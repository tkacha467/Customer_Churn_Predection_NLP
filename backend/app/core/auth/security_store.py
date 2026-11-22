import hashlib
import hmac
import ipaddress
import logging
import os
import time
import uuid
from typing import Optional, Tuple, Dict, Any, List

import httpx

try:
    import redis
    import redis.asyncio as aioredis
    from redis.exceptions import (
        RedisError,
        ConnectionError as RedisConnectionError,
        TimeoutError as RedisTimeoutError,
    )
except ImportError:
    redis = None
    aioredis = None
    RedisError = Exception
    RedisConnectionError = Exception
    RedisTimeoutError = Exception

logger = logging.getLogger("auth.security_store")

def _sanitize_credential_log(msg: Any) -> str:
    """Removes sensitive passwords, tokens, or credentials from log messages."""
    import re
    text = str(msg)
    # Redact passwords in redis/valkey URLs: redis://user:password@host or redis://:password@host
    redacted = re.sub(r"://([^:@]+)?:([^@]+)@", r"://\1:***@", text)
    # Redact raw query param secrets if present
    redacted = re.sub(r"(token|secret|password)=([^\s&]+)", r"\1=***", redacted, flags=re.IGNORECASE)
    return redacted

# Operational Limits
MAX_GLOBAL_IPS = 30000
MAX_GLOBAL_ACCOUNTS = 50000
MAX_GLOBAL_PAIRS = 75000
IP_RATE_LIMIT_WINDOW = 60.0
IP_MAX_ATTEMPTS = 10
ACCOUNT_ATTEMPT_WINDOW = 300.0
ACCOUNT_DISTRIBUTED_THRESHOLD = 20
PAIR_FAILURE_THRESHOLD = 5

# Cloudflare Turnstile Official Test Keys
CF_DUMMY_PASS_SITEKEY = "1x00000000000000000000AA"
CF_DUMMY_PASS_SECRET = "1x0000000000000000000000000000000AA"
CF_DUMMY_FAIL_SITEKEY = "2x00000000000000000000AB"
CF_DUMMY_FAIL_SECRET = "2x0000000000000000000000000000000AB"

# Ephemeral secret for development / test fallback
_EPHEMERAL_HMAC_SECRET = None

# Global Redis Client / Pool cache
_redis_client = None
_client_loop = None


def get_hmac_secrets() -> Tuple[bytes, str, Optional[bytes], Optional[str]]:
    """
    Returns (primary_secret, primary_key_id, prev_secret, prev_key_id).
    Validates minimum 32-character secret in production and staging.
    """
    global _EPHEMERAL_HMAC_SECRET
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    raw_primary = os.getenv("SECURITY_HMAC_SECRET", "").strip()

    if not raw_primary:
        if env in ("production", "staging"):
            raise RuntimeError(
                f"SECURITY_HMAC_SECRET must be configured with at least 32 characters in '{env}'."
            )
        if _EPHEMERAL_HMAC_SECRET is None:
            _EPHEMERAL_HMAC_SECRET = "dev-ephemeral-hmac-secret-at-least-32-chars-key-0001"
        raw_primary = _EPHEMERAL_HMAC_SECRET

    if len(raw_primary) < 32 and env in ("production", "staging"):
        raise RuntimeError("SECURITY_HMAC_SECRET must be at least 32 characters long.")

    primary_id = os.getenv("SECURITY_HMAC_KEY_ID", "k1").strip() or "k1"
    raw_prev = os.getenv("SECURITY_HMAC_SECRET_PREVIOUS", "").strip()
    prev_id = os.getenv("SECURITY_HMAC_KEY_ID_PREVIOUS", "").strip() or "k0"

    prev_secret = raw_prev.encode("utf-8") if raw_prev else None
    prev_key_id = prev_id if raw_prev else None

    return raw_primary.encode("utf-8"), primary_id, prev_secret, prev_key_id


def compute_account_hmac(normalized_email: str, secret: bytes) -> str:
    """Computes HMAC-SHA256 account identifier truncated to 32 hex chars (128 bits)."""
    return hmac.new(secret, normalized_email.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def normalize_ip_address(ip_str: str) -> str:
    """
    Normalizes IPv4 (compressed) and IPv6 (standard /64 subnet prefix) to prevent
    subnet hopping attacks.
    """
    if not ip_str or not isinstance(ip_str, str):
        return "127.0.0.1"
    clean = ip_str.strip()
    try:
        addr = ipaddress.ip_address(clean)
        if addr.version == 6:
            prefix_len = int(os.getenv("IPV6_SUBNET_PREFIX_LENGTH", "64"))
            net = ipaddress.IPv6Network(f"{clean}/{prefix_len}", strict=False)
            return f"{net.network_address.compressed}/{prefix_len}"
        return addr.compressed
    except ValueError:
        return clean


def get_redis_client():
    """Returns singleton async Redis client instance configured with timeouts and active event-loop affinity."""
    import asyncio
    global _redis_client, _client_loop
    if aioredis is None:
        return None

    redis_url = os.getenv("REDIS_URL", "").strip() or os.getenv("VALKEY_URL", "").strip()
    if not redis_url:
        env = os.getenv("ENVIRONMENT", "development").strip().lower()
        if env in ("production", "staging"):
            raise RuntimeError(
                f"REDIS_URL must be configured in '{env}' environment for distributed security state."
            )
        return None

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _redis_client is not None:
        if _client_loop is not None and (_client_loop.is_closed() or (current_loop is not None and current_loop != _client_loop)):
            _redis_client = None

    if _redis_client is None:
        timeout = float(os.getenv("REDIS_TIMEOUT_SECONDS", "0.5"))
        extra_kwargs = {}
        ssl_ca = os.getenv("REDIS_SSL_CA_CERTS", "").strip()
        if ssl_ca:
            extra_kwargs["ssl_ca_certs"] = ssl_ca
        _redis_client = aioredis.from_url(
            redis_url,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            decode_responses=True,
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            **extra_kwargs,
        )
        _client_loop = current_loop
    return _redis_client


def reset_redis_client():
    """Resets cached client instance (useful for test isolation)."""
    global _redis_client, _client_loop
    _redis_client = None
    _client_loop = None


async def close_redis_client():
    """Closes Redis connection pool cleanly during application shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None


async def check_redis_health() -> bool:
    """Pings Redis to verify connection health."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        return await client.ping() is True
    except Exception as e:
        logger.warning(_sanitize_credential_log(f"Valkey/Redis health check failed: {e}"))
        return False


# --------------------------------------------------------------------------
# ATOMIC LUA SCRIPTS
# --------------------------------------------------------------------------

# Lua Script 1: Pre-Verification Gate & Multi-Tier Admission
# Enforces IP rate limiting, pair cooldowns, and evaluates whether Turnstile challenge is mandatory
# Returns: {allowed (1 or 0), status_code, wait_seconds, challenge_required (1 or 0)}
LUA_PRE_VERIFICATION_GATE = """
local redis_time = redis.call('TIME')
local now = tonumber(redis_time[1]) + (tonumber(redis_time[2]) / 1000000.0)

local max_ips = tonumber(ARGV[1])
local max_accounts = tonumber(ARGV[2])
local ip_limit = tonumber(ARGV[3])
local risk_threshold = tonumber(ARGV[4])
local norm_ip = ARGV[5]
local versioned_acct = ARGV[6]
local request_uuid = ARGV[7]
local has_prev = tonumber(ARGV[8])
local prev_versioned_acct = ARGV[9]

-- 1. EVICT EXPIRED ENTRIES FROM METADATA INDEXES
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)

-- 2. TIER 1: CLIENT IP ADMISSION & VELOCITY CHECK
local ip_score = redis.call('ZSCORE', KEYS[1], norm_ip)
if not ip_score then
    if redis.call('ZCARD', KEYS[1]) >= max_ips then
        return {0, "ip_capacity_exhausted", 0, 0}
    end
    redis.call('ZADD', KEYS[1], now + 60.0, norm_ip)
else
    redis.call('ZADD', KEYS[1], now + 60.0, norm_ip)
end

-- Sliding window for IP requests
redis.call('ZREMRANGEBYSCORE', KEYS[3], '-inf', now - 60.0)
local ip_count = redis.call('ZCARD', KEYS[3])
if ip_count >= ip_limit then
    local oldest = redis.call('ZRANGE', KEYS[3], 0, 0, 'WITHSCORES')
    local wait_time = 60
    if oldest and #oldest >= 2 then
        wait_time = math.max(1, math.ceil(60.0 - (now - tonumber(oldest[2]))))
    end
    return {0, "ip_rate_limited", wait_time, 0}
end
redis.call('ZADD', KEYS[3], now, request_uuid)
redis.call('EXPIRE', KEYS[3], 60)

-- 3. TIER 2: COMPOSITE PAIR COOLDOWN EVALUATION
local lock_until_primary = tonumber(redis.call('HGET', KEYS[4], 'lock_until') or '0')
local lock_until_prev = 0
if has_prev == 1 and KEYS[6] ~= '' then
    lock_until_prev = tonumber(redis.call('HGET', KEYS[6], 'lock_until') or '0')
end
local effective_lock = math.max(lock_until_primary, lock_until_prev)

if now < effective_lock then
    local wait_seconds = math.ceil(effective_lock - now)
    return {0, "pair_cooldown_active", wait_seconds, 0}
end

-- 4. TIER 3: ACCOUNT RISK & CAPACITY ADMISSION CHECK
local acct_score = redis.call('ZSCORE', KEYS[2], versioned_acct)
local challenge_required = 0

-- If account is actively tracked, measure sliding window failures across primary and prev
redis.call('ZREMRANGEBYSCORE', KEYS[5], '-inf', now - 300.0)
local risk_count = redis.call('ZCARD', KEYS[5])

if has_prev == 1 and KEYS[7] ~= '' then
    redis.call('ZREMRANGEBYSCORE', KEYS[7], '-inf', now - 300.0)
    risk_count = risk_count + redis.call('ZCARD', KEYS[7])
end

if risk_count >= risk_threshold then
    challenge_required = 1
end

if acct_score then
    redis.call('ZADD', KEYS[2], now + 300.0, versioned_acct)
else
    -- Untracked account: check if capacity is exhausted
    if redis.call('ZCARD', KEYS[2]) >= max_accounts then
        challenge_required = 1 -- Mandatory Turnstile challenge upfront for unadmitted accounts!
    else
        redis.call('ZADD', KEYS[2], now + 300.0, versioned_acct)
    end
end

return {1, "admitted", 0, challenge_required}
"""

# Lua Script 2: Record Login Failure with Safe Rollback
# Atomically records failure in pair hash and global risk ZSET
# Returns: {cooldown_wait_seconds, backoff_step}
LUA_RECORD_FAILURE = """
local redis_time = redis.call('TIME')
local now = tonumber(redis_time[1]) + (tonumber(redis_time[2]) / 1000000.0)

local max_pairs = tonumber(ARGV[1])
local versioned_pair = ARGV[2]
local request_uuid = ARGV[3]
local failure_threshold = tonumber(ARGV[4])

-- 1. RECORD ACCOUNT RISK ZSET (Protected Write)
local ok_risk = pcall(function()
    redis.call('ZREMRANGEBYSCORE', KEYS[3], '-inf', now - 300.0)
    redis.call('ZADD', KEYS[3], now, request_uuid)
    redis.call('EXPIRE', KEYS[3], 300)
end)

-- 2. PAIR CAPACITY ADMISSION
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
local pair_score = redis.call('ZSCORE', KEYS[1], versioned_pair)
local pair_admitted = 1
if not pair_score then
    if redis.call('ZCARD', KEYS[1]) >= max_pairs then
        pair_admitted = 0
    else
        local ok_pair_meta = pcall(redis.call, 'ZADD', KEYS[1], now + 300.0, versioned_pair)
        if not ok_pair_meta then pair_admitted = 0 end
    end
else
    redis.call('ZADD', KEYS[1], now + 300.0, versioned_pair)
end

-- 3. RECORD PAIR COOLDOWN (Protected Write with Explicit Rollback)
local cooldown = 0
local new_step = 0
if pair_admitted == 1 then
    local ok_pair_write = pcall(function()
        local failures = tonumber(redis.call('HGET', KEYS[2], 'failures') or '0') + 1
        local step = tonumber(redis.call('HGET', KEYS[2], 'step') or '0')
        if failures >= failure_threshold or step > 0 then
            step = step + 1
            cooldown = math.min(300, 30 * math.pow(2, step - 1))
            redis.call('HSET', KEYS[2], 'failures', failures, 'step', step, 'lock_until', now + cooldown)
            redis.call('EXPIRE', KEYS[2], math.ceil(cooldown + 300))
        else
            redis.call('HSET', KEYS[2], 'failures', failures, 'step', step, 'lock_until', 0)
            redis.call('EXPIRE', KEYS[2], 300)
        end
        new_step = step
    end)

    if not ok_pair_write then
        -- Rollback pair metadata on error
        redis.call('ZREM', KEYS[1], versioned_pair)
    end
end

return {cooldown, new_step}
"""

# Lua Script 3: Successful Login Cleanup
# Atomically removes composite pair for the authenticated IP without clearing risk evidence for other IPs
LUA_RECORD_SUCCESS = """
-- KEYS[1]: v1:auth:pair:{ip}:{key_id}:{account_hmac}:failures
-- KEYS[2]: v1:auth:meta:pairs
-- ARGV[1]: versioned_pair (string)
-- ARGV[2]: has_prev (1 or 0)
-- KEYS[3]: v1:auth:pair:{ip}:{prev_key_id}:{prev_account_hmac}:failures (optional)
-- ARGV[3]: prev_versioned_pair (string)

redis.call('DEL', KEYS[1])
redis.call('ZREM', KEYS[2], ARGV[1])

if tonumber(ARGV[2]) == 1 and KEYS[3] ~= '' then
    redis.call('DEL', KEYS[3])
    if ARGV[3] ~= '' then
        redis.call('ZREM', KEYS[2], ARGV[3])
    end
end

return 1
"""


# --------------------------------------------------------------------------
# HIGH-LEVEL SECURITY STORE API
# --------------------------------------------------------------------------

class SecurityStore:
    """
    Centralized security store orchestrating Redis/Valkey rate limiting,
    cooldown management, and Cloudflare Turnstile token validation.
    """

    @staticmethod
    async def evaluate_pre_auth(
        client_ip: str,
        normalized_email: str
    ) -> Tuple[bool, str, int, bool]:
        """
        Evaluates pre-authentication status before password hashing.
        Returns: (is_allowed, status_detail, wait_seconds, challenge_required)
        """
        norm_ip = normalize_ip_address(client_ip)
        primary_sec, primary_id, prev_sec, prev_id = get_hmac_secrets()
        acct_hmac_primary = compute_account_hmac(normalized_email, primary_sec)
        versioned_acct_primary = f"{primary_id}:{acct_hmac_primary}"
        req_uuid = uuid.uuid4().hex

        has_prev = 1 if prev_sec else 0
        versioned_acct_prev = f"{prev_id}:{compute_account_hmac(normalized_email, prev_sec)}" if prev_sec else ""

        client = get_redis_client()
        if client is None:
            # Fallback to local auth check if Redis is not configured in dev/test
            from backend.app.core.auth.auth import check_account_login_rate_limit, check_login_rate_limit
            if not check_login_rate_limit(client_ip):
                return False, "ip_rate_limited", 60, False
            allowed, wait = check_account_login_rate_limit(normalized_email, client_ip=client_ip)
            if not allowed:
                return False, "pair_cooldown_active", wait, False
            return True, "admitted", 0, False

        # Key definitions
        k_meta_ips = "v1:auth:meta:ips"
        k_meta_accts = "v1:auth:meta:accounts"
        k_ip_reqs = f"v1:auth:ip:{norm_ip}:reqs"
        k_pair_primary = f"v1:auth:pair:{norm_ip}:{primary_id}:{acct_hmac_primary}:failures"
        k_risk_primary = f"v1:auth:risk:{primary_id}:{acct_hmac_primary}:failures"

        k_pair_prev = f"v1:auth:pair:{norm_ip}:{prev_id}:{compute_account_hmac(normalized_email, prev_sec)}:failures" if prev_sec else ""
        k_risk_prev = f"v1:auth:risk:{prev_id}:{compute_account_hmac(normalized_email, prev_sec)}:failures" if prev_sec else ""

        try:
            keys = [k_meta_ips, k_meta_accts, k_ip_reqs, k_pair_primary, k_risk_primary, k_pair_prev, k_risk_prev]
            args = [
                MAX_GLOBAL_IPS,
                MAX_GLOBAL_ACCOUNTS,
                IP_MAX_ATTEMPTS,
                ACCOUNT_DISTRIBUTED_THRESHOLD,
                norm_ip,
                versioned_acct_primary,
                req_uuid,
                has_prev,
                versioned_acct_prev,
            ]
            res = await client.eval(LUA_PRE_VERIFICATION_GATE, len(keys), *keys, *args)
            allowed, status_code, wait_sec, challenge_req = res
            return bool(allowed), str(status_code), int(wait_sec), bool(challenge_req)
        except (RedisError, Exception) as exc:
            policy = os.getenv("REDIS_FAILURE_POLICY", "fail_closed").strip().lower()
            logger.warning(_sanitize_credential_log(f"Valkey/Redis communication error during pre-auth: {exc}"))
            if policy == "fail_closed":
                return False, "valkey_unavailable", 30, False
            # Dev fallback
            return True, "admitted_degraded", 0, False

    @staticmethod
    async def record_login_failure(client_ip: str, normalized_email: str) -> Tuple[int, int]:
        """
        Atomically records failed password attempt in pair hash and global risk ZSET.
        Returns: (cooldown_seconds, step)
        """
        norm_ip = normalize_ip_address(client_ip)
        primary_sec, primary_id, _, _ = get_hmac_secrets()
        acct_hmac = compute_account_hmac(normalized_email, primary_sec)
        versioned_acct = f"{primary_id}:{acct_hmac}"
        versioned_pair = f"{norm_ip}:{primary_id}:{acct_hmac}"
        req_uuid = uuid.uuid4().hex

        client = get_redis_client()
        if client is None:
            from backend.app.core.auth.auth import record_login_failure as local_fail
            local_fail(normalized_email, client_ip=client_ip)
            return 0, 0

        k_meta_pairs = "v1:auth:meta:pairs"
        k_pair = f"v1:auth:pair:{norm_ip}:{primary_id}:{acct_hmac}:failures"
        k_risk = f"v1:auth:risk:{primary_id}:{acct_hmac}:failures"

        try:
            keys = [k_meta_pairs, k_pair, k_risk]
            args = [
                MAX_GLOBAL_PAIRS,
                versioned_pair,
                req_uuid,
                PAIR_FAILURE_THRESHOLD,
            ]
            res = await client.eval(LUA_RECORD_FAILURE, len(keys), *keys, *args)
            cooldown, step = res
            return int(cooldown), int(step)
        except Exception as exc:
            logger.warning(_sanitize_credential_log(f"Failed to record login failure in Valkey: {exc}"))
            return 0, 0

    @staticmethod
    async def record_login_success(client_ip: str, normalized_email: str) -> None:
        """
        Atomically clears the calling client IP's pair cooldown upon successful login.
        Leaves the global risk ZSET intact to preserve evidence of ongoing bot attacks.
        """
        norm_ip = normalize_ip_address(client_ip)
        primary_sec, primary_id, prev_sec, prev_id = get_hmac_secrets()
        acct_hmac_primary = compute_account_hmac(normalized_email, primary_sec)
        versioned_pair_primary = f"{norm_ip}:{primary_id}:{acct_hmac_primary}"

        client = get_redis_client()
        if client is None:
            from backend.app.core.auth.auth import record_login_success as local_success
            local_success(normalized_email, client_ip=client_ip)
            return

        k_pair_primary = f"v1:auth:pair:{norm_ip}:{primary_id}:{acct_hmac_primary}:failures"
        k_meta_pairs = "v1:auth:meta:pairs"

        has_prev = 1 if prev_sec else 0
        k_pair_prev = f"v1:auth:pair:{norm_ip}:{prev_id}:{compute_account_hmac(normalized_email, prev_sec)}:failures" if prev_sec else ""
        versioned_pair_prev = f"{norm_ip}:{prev_id}:{compute_account_hmac(normalized_email, prev_sec)}" if prev_sec else ""

        try:
            keys = [k_pair_primary, k_meta_pairs, k_pair_prev]
            args = [versioned_pair_primary, has_prev, versioned_pair_prev]
            await client.eval(LUA_RECORD_SUCCESS, len(keys), *keys, *args)
        except Exception as exc:
            logger.warning(_sanitize_credential_log(f"Failed to clean up successful login state in Valkey: {exc}"))

    @staticmethod
    async def clear_all_security_keys() -> None:
        """Helper for test suites to completely flush security state from Valkey/Redis."""
        client = get_redis_client()
        if client is not None:
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match="v1:auth:*", count=100)
                if keys:
                    await client.delete(*keys)
                if cursor == 0:
                    break


# --------------------------------------------------------------------------
# CLOUDFLARE TURNSTILE VERIFICATION
# --------------------------------------------------------------------------

async def verify_turnstile_token(token: Optional[str], client_ip: str) -> Tuple[bool, str]:
    """
    Independently verifies Cloudflare Turnstile token using server-side secret.
    Validates token presence, success flag, action, and allowed hostnames.
    Returns: (is_valid, error_reason)
    """
    if not token or not isinstance(token, str) or not token.strip():
        return False, "missing_token"

    token_clean = token.strip()
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    is_dev_test = env in ("development", "test")
    secret_key = os.getenv("TURNSTILE_SECRET_KEY", "").strip()

    # SEC-GAP-01: In staging, production, or unknown environments, reject all dummy tokens and dummy secrets
    if not is_dev_test:
        if token_clean in (
            "XXXX.DUMMY.TOKEN.PASS",
            "XXXX.DUMMY.TOKEN.FAIL",
            CF_DUMMY_PASS_SITEKEY,
            CF_DUMMY_FAIL_SITEKEY,
            "test-token-valid",
        ) or token_clean.startswith("test_pass"):
            logger.warning("Cloudflare Turnstile test dummy token rejected in non-development environment.")
            return False, "dummy_token_forbidden_in_production"

        if secret_key in (CF_DUMMY_PASS_SECRET, CF_DUMMY_FAIL_SECRET):
            logger.error("Cloudflare Turnstile dummy secret key configured in non-development environment.")
            return False, "dummy_secret_forbidden_in_production"

        if not secret_key:
            logger.error("TURNSTILE_SECRET_KEY is missing in non-development environment.")
            return False, "secret_unconfigured"

    # Cloudflare standardized test dummy keys bypass (ALLOWED EXCLUSIVELY IN DEVELOPMENT/TEST)
    if is_dev_test:
        if token_clean in ("XXXX.DUMMY.TOKEN.FAIL", CF_DUMMY_FAIL_SITEKEY) or secret_key == CF_DUMMY_FAIL_SECRET:
            return False, "test_fail"
        if token_clean in ("XXXX.DUMMY.TOKEN.PASS", CF_DUMMY_PASS_SITEKEY):
            return True, "test_pass"
        if secret_key == CF_DUMMY_PASS_SECRET:
            # When dummy pass secret is used in tests, reject unknown/bogus tokens unless explicit test pass
            if token_clean.startswith("test_pass") or token_clean == "test-token-valid":
                return True, "test_pass"
            return False, "test_token_rejected"
        if not secret_key:
            return True, "dev_mock_pass"

    verify_url = os.getenv("TURNSTILE_VERIFY_URL", "https://challenges.cloudflare.com/turnstile/v0/siteverify").strip()
    allowed_hostnames = [h.strip().lower() for h in os.getenv("TURNSTILE_ALLOWED_HOSTNAMES", "localhost,127.0.0.1").split(",") if h.strip()]

    payload = {
        "secret": secret_key,
        "response": token_clean,
        "remoteip": client_ip,
        "idempotency_key": uuid.uuid4().hex,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=1.0, read=2.0, write=1.0, pool=3.0)) as client:
            resp = await client.post(verify_url, data=payload)
            if resp.status_code != 200:
                logger.warning(f"Turnstile upstream error status {resp.status_code}")
                return False, f"upstream_status_{resp.status_code}"
            data = resp.json()
    except Exception as exc:
        logger.warning(f"Turnstile verification request failed: {exc}")
        return False, "provider_timeout"

    if not data.get("success"):
        error_codes = data.get("error-codes", [])
        return False, f"challenge_rejected_{','.join(error_codes)}"

    # Validate action
    action = data.get("action", "")
    if action and action != "owner_login":
        return False, "action_mismatch"

    # Validate hostname against explicit allowlist
    hostname = (data.get("hostname") or "").strip().lower()
    if hostname and allowed_hostnames and hostname not in allowed_hostnames:
        return False, "hostname_unauthorized"

    return True, "ok"
