"""
Multi-Tenant Authentication & Role-Based Authorization for ChurnLens / NastaGhar.
Implements scrypt password hashing, cryptographically random server-side sessions,
tenant-membership binding, and role-based access control.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, Any

from fastapi import HTTPException, Request

from backend.app.core.database.storage import ReviewStore

OWNER_COOKIE = "nasta_owner_session"
SESSION_TTL_SECONDS = 8 * 60 * 60

# Ephemeral secret for development and testing (generated once, stable for process lifetime)
_EPHEMERAL_DEV_SECRET: Optional[str] = None
_secret_lock = threading.Lock()

# Bounded in-memory rate limiting and account abuse tracking (SEC-04)
MAX_TRACKED_IPS = 10000
MAX_TRACKED_ACCOUNTS = 10000
MAX_TRACKED_PAIRS = 20000
IP_RATE_LIMIT_WINDOW = 60.0       # 1 minute window for per-IP limit
IP_MAX_ATTEMPTS = 10              # max 10 attempts per minute per IP
ACCOUNT_ATTEMPT_WINDOW = 300.0    # 5 minute window for failed attempts
ACCOUNT_FAILURE_THRESHOLD = 5     # 5 failed attempts before cooldown initiates
ACCOUNT_DISTRIBUTED_THRESHOLD = 20 # 20 failures across all IPs triggers stricter untrusted-IP defenses

_ip_attempts: Dict[str, deque] = defaultdict(deque)
_account_failures: Dict[str, deque] = defaultdict(deque)
_account_lockout_until: Dict[str, float] = {}
_account_lockout_step: Dict[str, int] = {}

# Composite (client_ip, normalized_email) tracking (SEC-04 DoS remediation)
_ip_account_failures: Dict[tuple[str, str], deque] = defaultdict(deque)
_ip_account_lockout_until: Dict[tuple[str, str], float] = {}
_ip_account_lockout_step: Dict[tuple[str, str], int] = {}
_trusted_account_ips: Dict[str, set[str]] = defaultdict(set)
_login_lock = threading.Lock()

# Compatibility alias for existing tests referencing _login_attempts
_login_attempts = _ip_attempts

_stores: dict[str, ReviewStore] = {}

def get_store() -> ReviewStore:
    db_path = os.getenv("REVIEW_DB_PATH", "")
    if db_path not in _stores:
        _stores[db_path] = ReviewStore()
    return _stores[db_path]


# ---------------------------------------------------------
# Password Hashing & Verification (scrypt - RFC 7914)
# ---------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes password using Python's standard library scrypt with OWASP-recommended parameters."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        maxmem=32 * 1024 * 1024
    )
    return f"scrypt$16384$8$1${salt.hex()}${key.hex()}"


# Precomputed dummy scrypt hash for constant-time authentication and zero user enumeration
DUMMY_SCRYPT_HASH = hash_password("dummy-password-for-timing-defense")


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies password against stored scrypt hash in constant time."""
    if not password or not stored_hash or not isinstance(stored_hash, str):
        return False
    parts = stored_hash.split("$")
    if len(parts) == 6 and parts[0] == "scrypt":
        try:
            n = int(parts[1])
            r = int(parts[2])
            p = int(parts[3])
            salt = bytes.fromhex(parts[4])
            expected_key = bytes.fromhex(parts[5])
            computed_key = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=n,
                r=r,
                p=p,
                maxmem=32 * 1024 * 1024
            )
            return hmac.compare_digest(computed_key, expected_key)
        except Exception:
            return False
    return False


# ---------------------------------------------------------
# Session Token Generation & Hashing
# ---------------------------------------------------------
def generate_session_token() -> str:
    """Generates a cryptographically secure 256-bit URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Hashes the raw session token with SHA-256 before database lookup/storage."""
    return hashlib.sha256(raw_token.encode("ascii")).hexdigest()


def _sign(val: str) -> str:
    """Compatibility signing helper."""
    return hashlib.sha256(val.encode("ascii")).hexdigest()


def get_signing_secret() -> str:
    """
    Retrieves the session signing secret key.
    
    Security Contract (SEC-02):
    - Production and staging MUST configure OWNER_SESSION_SECRET with at least 32 characters.
      If missing or shorter than 32 characters, fails closed immediately with RuntimeError.
    - Unconfigured/unknown environments default to strict fail-closed behavior.
    - Development and test environments (ENVIRONMENT in ('test', 'testing', 'dev', 'development'))
      use OWNER_SESSION_SECRET if configured (>= 32 characters); otherwise, a cryptographically
      secure 32-byte secret is generated ONCE and retained stably for the process lifetime.
    - Hardcoded predictable fallback keys are strictly prohibited.
    - Never logs or prints the secret value.
    
    Notice:
    - Rotating OWNER_SESSION_SECRET invalidates all existing HMAC-signed preview tokens.
    """
    global _EPHEMERAL_DEV_SECRET
    env = os.getenv("ENVIRONMENT", "").strip().lower()
    secret = os.getenv("OWNER_SESSION_SECRET", "").strip()

    if env in ("test", "testing", "dev", "development"):
        if secret and len(secret) >= 32:
            return secret
        if _EPHEMERAL_DEV_SECRET is None:
            with _secret_lock:
                if _EPHEMERAL_DEV_SECRET is None:
                    _EPHEMERAL_DEV_SECRET = secrets.token_hex(32)
        return _EPHEMERAL_DEV_SECRET

    # Staging, production, and unconfigured/ambiguous environments: strictly fail closed
    if not secret or len(secret) < 32:
        raise RuntimeError(
            f"Missing or insecure OWNER_SESSION_SECRET in environment '{env or 'unconfigured'}'. "
            f"Must be configured with at least 32 characters. "
            f"Application execution halted to prevent forged session tokens."
        )
    return secret


def create_preview_token(
    tenant_id: str,
    user_id: str,
    role: str = "owner",
    is_admin: bool = False,
    ttl_seconds: int = 7200
) -> str:
    """
    Creates a cryptographically signed HMAC-SHA256 preview token.
    Enforces server-authenticated preview session context without trusting client flags.
    """
    traffic_source = "internal_admin" if is_admin else "preview"
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "role": role,
        "is_admin": is_admin,
        "traffic_source": traffic_source,
        "exp": int(time.time() + ttl_seconds),
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('ascii').rstrip('=')
    sig = hmac.new(get_signing_secret().encode('utf-8'), payload_b64.encode('ascii'), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_preview_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Verifies HMAC-SHA256 signature, expiry, and payload on a server-issued preview token.
    Returns decoded token dictionary if valid, None if invalid, tampered, or expired.
    """
    if not token or not isinstance(token, str) or "." not in token:
        return None
    try:
        payload_b64, sig = token.strip().split(".", 1)
        expected_sig = hmac.new(get_signing_secret().encode('utf-8'), payload_b64.encode('ascii'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        rem = len(payload_b64) % 4
        padded = payload_b64 + ('=' * (4 - rem) if rem else '')
        payload = json.loads(base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8'))
        if float(payload.get("exp", 0)) < time.time():
            return None
        return payload
    except Exception:
        return None


def make_session(user_id: Optional[str] = None, tenant_id: str = "default_business") -> str:
    """Creates a valid server-side session token (used for backward compatibility and testing)."""
    store = get_store()
    if not user_id:
        user = store.get_or_create_legacy_owner()
        user_id = user["id"]
    # Ensure tenant exists and user has membership
    if not store.tenant_exists(tenant_id):
        store.upsert_tenant({"id": tenant_id, "business_name": tenant_id})
    if not store.get_membership(user_id, tenant_id):
        store.add_membership(user_id, tenant_id, role="owner")

    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    store.create_session(
        token_hash=token_hash,
        user_id=user_id,
        active_tenant_id=tenant_id,
        expires_at=time.time() + SESSION_TTL_SECONDS
    )
    return raw_token


# ---------------------------------------------------------
# Bounded Rate Limiting & Account Abuse Protection (SEC-04)
# ---------------------------------------------------------

def _prune_expired_entries(now: float) -> None:
    """Internal helper to prune expired rate limiting records and maintain strictly bounded memory."""
    # Prune expired IP attempts
    expired_ips = [ip for ip, deq in _ip_attempts.items() if not deq or deq[-1] <= now - IP_RATE_LIMIT_WINDOW]
    for ip in expired_ips:
        _ip_attempts.pop(ip, None)

    # Prune expired account failures where lockout has also ended
    expired_accs = [
        acc for acc, deq in _account_failures.items()
        if (not deq or deq[-1] <= now - ACCOUNT_ATTEMPT_WINDOW) and _account_lockout_until.get(acc, 0.0) <= now
    ]
    for acc in expired_accs:
        _account_failures.pop(acc, None)
        _account_lockout_until.pop(acc, None)
        _account_lockout_step.pop(acc, None)

    # Prune expired (client_ip, account) pair failures where lockout has also ended
    expired_pairs = [
        pair for pair, deq in _ip_account_failures.items()
        if (not deq or deq[-1] <= now - ACCOUNT_ATTEMPT_WINDOW) and _ip_account_lockout_until.get(pair, 0.0) <= now
    ]
    for pair in expired_pairs:
        _ip_account_failures.pop(pair, None)
        _ip_account_lockout_until.pop(pair, None)
        _ip_account_lockout_step.pop(pair, None)

    # Hard cap safeguards to guarantee bounded memory under massive volumetric scans
    if len(_ip_attempts) > MAX_TRACKED_IPS:
        excess = len(_ip_attempts) - int(MAX_TRACKED_IPS * 0.8)
        for ip in list(_ip_attempts.keys())[:excess]:
            _ip_attempts.pop(ip, None)

    if len(_account_failures) > MAX_TRACKED_ACCOUNTS:
        excess = len(_account_failures) - int(MAX_TRACKED_ACCOUNTS * 0.8)
        for acc in list(_account_failures.keys())[:excess]:
            _account_failures.pop(acc, None)
            _account_lockout_until.pop(acc, None)
            _account_lockout_step.pop(acc, None)

    if len(_ip_account_failures) > MAX_TRACKED_PAIRS:
        excess = len(_ip_account_failures) - int(MAX_TRACKED_PAIRS * 0.8)
        for pair in list(_ip_account_failures.keys())[:excess]:
            _ip_account_failures.pop(pair, None)
            _ip_account_lockout_until.pop(pair, None)
            _ip_account_lockout_step.pop(pair, None)

    if len(_trusted_account_ips) > MAX_TRACKED_ACCOUNTS:
        excess = len(_trusted_account_ips) - int(MAX_TRACKED_ACCOUNTS * 0.8)
        for acc in list(_trusted_account_ips.keys())[:excess]:
            _trusted_account_ips.pop(acc, None)


def check_login_rate_limit(client_ip: str, now: float | None = None) -> bool:
    """Allow at most 10 login attempts per IP per 60 seconds (thread-safe and memory-bounded)."""
    now = time.time() if now is None else now
    with _login_lock:
        _prune_expired_entries(now)
        attempts = _ip_attempts[client_ip]
        while attempts and attempts[0] <= now - IP_RATE_LIMIT_WINDOW:
            attempts.popleft()
        if len(attempts) >= IP_MAX_ATTEMPTS:
            return False
        attempts.append(now)
        return True


def normalize_account_identity(email: Optional[str]) -> str:
    """Normalizes email identity for consistent account rate limiting and enumeration defense."""
    if not email or not isinstance(email, str):
        return ""
    return email.strip().lower()


def check_account_login_rate_limit(
    email: str,
    client_ip: Optional[str] = None,
    now: float | None = None
) -> tuple[bool, int]:
    """
    Enforces account-level abuse protection without creating an Account Lockout Denial-of-Service.
    Returns (is_allowed, wait_seconds).
    
    If client_ip is provided:
      Checks whether (client_ip, account) pair is in temporary exponential cooldown due to repeated failures.
      A malicious client IP cannot lock out legitimate users connecting from other IP addresses.
    
    If client_ip is omitted (e.g. standalone test calls):
      Evaluates account-level lockout state directly.
    """
    norm_email = normalize_account_identity(email)
    if not norm_email:
        return True, 0

    now = time.time() if now is None else now
    with _login_lock:
        _prune_expired_entries(now)

        if client_ip:
            pair = (client_ip.strip(), norm_email)
            lock_until = _ip_account_lockout_until.get(pair, 0.0)
            if now < lock_until:
                wait_seconds = max(1, int(lock_until - now + 0.999))
                return False, wait_seconds
            if pair in _ip_account_lockout_until:
                del _ip_account_lockout_until[pair]
            return True, 0

        # Standalone account-level evaluation (when client_ip is not supplied)
        lock_until = _account_lockout_until.get(norm_email, 0.0)
        if now < lock_until:
            wait_seconds = max(1, int(lock_until - now + 0.999))
            return False, wait_seconds

        if norm_email in _account_lockout_until:
            del _account_lockout_until[norm_email]

        return True, 0


def record_login_failure(
    email: str,
    client_ip: Optional[str] = None,
    now: float | None = None
) -> None:
    """
    Records a failed login attempt for an account identity and client IP.
    Applies exponential temporary cooldown when failure threshold is reached.
    If client_ip is provided, isolates the cooldown to the offending (client_ip, account) pair.
    Cooldown intervals:
      - 5 failures: 30 seconds
      - 6 failures: 60 seconds
      - 7 failures: 120 seconds
      - 8+ failures: 300 seconds (capped at 5 minutes)
    """
    norm_email = normalize_account_identity(email)
    if not norm_email:
        return

    now = time.time() if now is None else now
    with _login_lock:
        # Always track global account failures
        failures = _account_failures[norm_email]
        while failures and failures[0] <= now - ACCOUNT_ATTEMPT_WINDOW:
            failures.popleft()
        failures.append(now)

        if len(failures) >= ACCOUNT_FAILURE_THRESHOLD or _account_lockout_step.get(norm_email, 0) > 0:
            current_step = _account_lockout_step.get(norm_email, 0) + 1
            _account_lockout_step[norm_email] = current_step
            cooldown_seconds = min(300.0, 30.0 * (2 ** (current_step - 1)))
            _account_lockout_until[norm_email] = now + cooldown_seconds

        # Track (client_ip, account) pair failure and cooldown
        if client_ip:
            pair = (client_ip.strip(), norm_email)
            pair_failures = _ip_account_failures[pair]
            while pair_failures and pair_failures[0] <= now - ACCOUNT_ATTEMPT_WINDOW:
                pair_failures.popleft()
            pair_failures.append(now)

            if len(pair_failures) >= ACCOUNT_FAILURE_THRESHOLD or _ip_account_lockout_step.get(pair, 0) > 0:
                current_step = _ip_account_lockout_step.get(pair, 0) + 1
                _ip_account_lockout_step[pair] = current_step
                cooldown_seconds = min(300.0, 30.0 * (2 ** (current_step - 1)))
                _ip_account_lockout_until[pair] = now + cooldown_seconds


def record_login_success(
    email: str,
    client_ip: Optional[str] = None
) -> None:
    """
    Clears failed attempt history and backoff state on successful authentication.
    Marks client_ip as a trusted IP for this account.
    """
    norm_email = normalize_account_identity(email)
    if not norm_email:
        return

    with _login_lock:
        _account_failures.pop(norm_email, None)
        _account_lockout_until.pop(norm_email, None)
        _account_lockout_step.pop(norm_email, None)

        if client_ip:
            pair = (client_ip.strip(), norm_email)
            _ip_account_failures.pop(pair, None)
            _ip_account_lockout_until.pop(pair, None)
            _ip_account_lockout_step.pop(pair, None)
            _trusted_account_ips[norm_email].add(client_ip.strip())


def reset_rate_limits() -> None:
    """Helper for testing to reset all rate limit state."""
    with _login_lock:
        _ip_attempts.clear()
        _account_failures.clear()
        _account_lockout_until.clear()
        _account_lockout_step.clear()
        _ip_account_failures.clear()
        _ip_account_lockout_until.clear()
        _ip_account_lockout_step.clear()
        _trusted_account_ips.clear()


# ---------------------------------------------------------
# Tenant Authorization Context
# ---------------------------------------------------------
@dataclass
class TenantContext:
    user_id: str
    email: str
    display_name: str
    tenant_id: str
    role: str  # 'owner', 'manager', 'staff'
    is_platform_admin: bool = False


def is_cookie_secure() -> bool:
    """Returns True if session cookies should be marked Secure (HTTPS)."""
    explicit = os.getenv("COOKIE_SECURE", "").strip().lower()
    if explicit in ("true", "1", "yes"):
        return True
    if explicit in ("false", "0", "no"):
        return False
    return os.getenv("ENVIRONMENT", "development").strip().lower() == "production"


def check_csrf_origin(request: Request) -> None:
    """Validates request origin on mutating HTTP methods against allowed CORS origins."""
    if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
        origin = request.headers.get("origin")
        if not origin:
            ref = request.headers.get("referer", "")
            match = re.match(r"^(https?://[^/]+)", ref)
            if match:
                origin = match.group(1)

        allowed = {
            value.strip().rstrip("/")
            for value in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:5176,http://127.0.0.1:5176",
            ).split(",")
            if value.strip()
        }

        if origin:
            if origin.rstrip("/") not in allowed:
                from backend.app.core.security.security_shield import emit_security_event, SecurityEventType, SecuritySeverity
                emit_security_event(
                    event_type=SecurityEventType.CSRF_ORIGIN_VIOLATION,
                    severity=SecuritySeverity.HIGH,
                    details={"origin": origin, "path": request.url.path, "method": request.method}
                )
                raise HTTPException(status_code=403, detail="Request origin is not allowed")
        elif OWNER_COOKIE in request.cookies and os.getenv("ENVIRONMENT", "development").lower() == "production":
            from backend.app.core.security.security_shield import emit_security_event, SecurityEventType, SecuritySeverity
            emit_security_event(
                event_type=SecurityEventType.CSRF_ORIGIN_VIOLATION,
                severity=SecuritySeverity.HIGH,
                details={"reason": "Missing origin header on authenticated mutation", "path": request.url.path, "method": request.method}
            )
            raise HTTPException(status_code=403, detail="Missing origin header on authenticated mutation")


async def require_auth_context(request: Request) -> TenantContext:
    """
    Extracts and validates the server-side session from cookie or Authorization header.
    Verifies user status, active tenant membership, and CSRF origin.
    """
    # 1. Extract raw token
    token = request.cookies.get(OWNER_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 2. Lookup session by SHA-256 hash
    store = get_store()
    token_hash = hash_token(token)
    session = store.get_session(token_hash)
    now = time.time()

    if not session or session.get("revoked_at") is not None or session.get("expires_at", 0) < now:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in again.")

    # 3. Lookup user & verify active status
    user = store.get_user_by_id(session["user_id"])
    if not user or user.get("is_active") != 1:
        raise HTTPException(status_code=401, detail="User account is deactivated or not found.")

    # 4. Verify membership in active tenant
    active_tenant_id = session["active_tenant_id"]
    is_admin = bool(user.get("is_platform_admin", 0))
    membership = store.get_membership(user["id"], active_tenant_id)
    if not membership and not is_admin:
        raise HTTPException(status_code=403, detail="Active tenant access is revoked.")

    # Immediately invalidate sessions for suspended tenants (unless platform admin)
    active_tenant = store.get_tenant(active_tenant_id)
    if not is_admin and active_tenant and active_tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Business '{active_tenant_id}' is inactive or suspended.")

    effective_role = membership["role"] if membership else ("owner" if is_admin else "staff")

    # 5. Check CSRF Origin
    check_csrf_origin(request)

    return TenantContext(
        user_id=user["id"],
        email=user["email"],
        display_name=user.get("display_name", ""),
        tenant_id=active_tenant_id,
        role=effective_role,
        is_platform_admin=is_admin
    )


def get_optional_auth_context(request: Request) -> Optional[TenantContext]:
    """
    Safely resolves TenantContext from cookie or Authorization header without raising 401.
    Used for dynamic traffic_source detection on endpoints that allow both anonymous and authenticated traffic.
    Returns None if unauthenticated, session expired, or invalid.
    """
    token = request.cookies.get(OWNER_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    if not token:
        return None
    try:
        store = get_store()
        token_hash = hash_token(token)
        session = store.get_session(token_hash)
        now = time.time()
        if not session or session.get("revoked_at") is not None or session.get("expires_at", 0) < now:
            return None
        user = store.get_user_by_id(session["user_id"])
        if not user or user.get("is_active") != 1:
            return None
        active_tenant_id = session["active_tenant_id"]
        is_admin = bool(user.get("is_platform_admin", 0))
        membership = store.get_membership(user["id"], active_tenant_id)
        if not membership and not is_admin:
            return None
        active_tenant = store.get_tenant(active_tenant_id)
        if not is_admin and active_tenant and active_tenant.get("status") != "active":
            return None
        effective_role = membership["role"] if membership else ("owner" if is_admin else "staff")
        return TenantContext(
            user_id=user["id"],
            email=user["email"],
            display_name=user.get("display_name", ""),
            tenant_id=active_tenant_id,
            role=effective_role,
            is_platform_admin=is_admin
        )
    except Exception:
        return None


ROLE_RANKS = {
    "staff": 1,
    "manager": 2,
    "owner": 3
}


def require_tenant_access(required_role: str = "manager", required_entitlement: Optional[str] = None):
    """
    FastAPI dependency factory enforcing tenant boundaries and role levels.
    If the endpoint receives a specific business_id (in path or query parameters),
    this dependency asserts that the authenticated user has an active membership
    in that specific business_id with the required role.
    """
    async def dependency(request: Request) -> TenantContext:
        ctx = await require_auth_context(request)
        store = get_store()

        # Check for requested tenant from path or query params
        target_id = request.path_params.get("business_id") or request.query_params.get("business_id")

        if target_id in ("default_business", "nasta_ghar", "nasta-ghar"):
            target_id = "default_business"

        effective_tenant = ctx.tenant_id
        effective_role = ctx.role

        if target_id and target_id != ctx.tenant_id:
            # Caller explicitly requested a business different from session active tenant
            if ctx.is_platform_admin:
                # Platform administrator can manage any tenant or onboard new tenants
                target_tenant = store.get_tenant(target_id)
                if not target_tenant and request.method in {"POST", "PUT"} and "config" in request.url.path:
                    store.upsert_tenant({"id": target_id, "business_name": target_id})
                    store.add_membership(ctx.user_id, target_id, role="owner")
                elif not target_tenant:
                    raise HTTPException(status_code=404, detail=f"Business '{target_id}' not found.")
                effective_tenant = target_id
                effective_role = "owner"
            else:
                # Ordinary owner or staff MUST have an existing membership in target_id
                target_membership = store.get_membership(ctx.user_id, target_id)
                if not target_membership:
                    from backend.app.core.security.security_shield import emit_security_event, SecurityEventType, SecuritySeverity
                    emit_security_event(
                        event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL,
                        severity=SecuritySeverity.HIGH,
                        actor_id=ctx.user_id,
                        tenant_id=target_id,
                        details={"requested_tenant": target_id, "active_tenant": ctx.tenant_id, "required_role": required_role}
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied: You do not have an authorized membership for business '{target_id}'."
                    )
                # Verify tenant is active
                target_tenant = store.get_tenant(target_id)
                if not target_tenant or target_tenant.get("status") != "active":
                    raise HTTPException(
                        status_code=403,
                        detail=f"Business '{target_id}' is inactive or suspended."
                    )
                effective_tenant = target_id
                effective_role = target_membership["role"]

        # Validate role hierarchy
        if ROLE_RANKS.get(effective_role, 0) < ROLE_RANKS.get(required_role, 2):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for this operation. Requires '{required_role}' role (current role: '{effective_role}')."
            )

        # Verify that the effective tenant is active
        effective_record = store.get_tenant(effective_tenant)
        if not effective_record or effective_record.get("status") != "active":
            raise HTTPException(
                status_code=403,
                detail=f"Business '{effective_tenant}' is inactive or suspended."
            )

        if required_entitlement:
            from backend.app.core.entitlements.entitlements import check_tenant_entitlement
            if not check_tenant_entitlement(effective_tenant, required_entitlement):
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature module '{required_entitlement}' is not enabled for business '{effective_tenant}'."
                )

        return TenantContext(
            user_id=ctx.user_id,
            email=ctx.email,
            display_name=ctx.display_name,
            tenant_id=effective_tenant,
            role=effective_role,
            is_platform_admin=ctx.is_platform_admin
        )

    return dependency


async def require_platform_admin(request: Request) -> TenantContext:
    """FastAPI dependency requiring an active platform administrator session."""
    ctx = await require_auth_context(request)
    if not ctx.is_platform_admin:
        from backend.app.core.security.security_shield import emit_security_event, SecurityEventType, SecuritySeverity
        emit_security_event(
            event_type=SecurityEventType.ACCESS_UNAUTHORIZED_ADMIN,
            severity=SecuritySeverity.HIGH,
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            details={"email": ctx.email, "path": request.url.path}
        )
        raise HTTPException(
            status_code=403,
            detail="Platform administrator privileges required."
        )
    return ctx


# Backward-compatible alias for owner operations
require_owner = require_tenant_access("owner")
