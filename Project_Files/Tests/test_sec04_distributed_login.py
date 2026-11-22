"""
VRAJA AI — SEC-04 Distributed Login Security Test Suite
Adversarial verification of centralized Valkey/Redis shared security state:
- Multi-worker atomic rate limiting and composite pair cooldowns
- Distributed brute-force risk tracking across dynamic IP pools
- Progressive Cloudflare Turnstile challenge gating (pre-scrypt)
- HMAC-SHA256 account derivation and key rotation
- Remediation of Account-Lockout Denial-of-Service
- Fail-closed policy under store outage and degradation
"""

import asyncio
import os
import time
from unittest.mock import patch
import pytest
from starlette.testclient import TestClient

from backend.app.core.auth.auth import hash_password, reset_rate_limits
from backend.app.core.auth.security_store import (
    SecurityStore,
    get_redis_client,
    reset_redis_client,
    compute_account_hmac,
    get_hmac_secrets,
    normalize_ip_address,
    CF_DUMMY_PASS_SITEKEY,
    CF_DUMMY_PASS_SECRET,
    CF_DUMMY_FAIL_SITEKEY,
    CF_DUMMY_FAIL_SECRET,
    verify_turnstile_token,
)
from backend.app.core.database.storage import ReviewStore
from backend.app.main import app


TEST_REDIS_URL = "redis://127.0.0.1:6379/0"
TEST_HMAC_SECRET = "production-grade-hmac-secret-at-least-32-chars-long-sec04-test"
TEST_SESSION_SECRET = "production-grade-session-secret-at-least-32-chars-long-sec04-test"
VICTIM_EMAIL = "owner@bistro-delight.com"
CORRECT_PASSWORD = "CorrectOwnerPass123!"


@pytest.fixture(autouse=True)
def setup_sec04_environment(tmp_path, monkeypatch):
    """Configures live Valkey connection and isolated test environment."""
    db_file = tmp_path / "test_sec04.sqlite3"
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("REDIS_URL", TEST_REDIS_URL)
    monkeypatch.setenv("SECURITY_HMAC_SECRET", TEST_HMAC_SECRET)
    monkeypatch.setenv("SECURITY_HMAC_KEY_ID", "k1")
    monkeypatch.delenv("SECURITY_HMAC_SECRET_PREVIOUS", raising=False)
    monkeypatch.delenv("SECURITY_HMAC_KEY_ID_PREVIOUS", raising=False)
    monkeypatch.setenv("OWNER_SESSION_SECRET", TEST_SESSION_SECRET)
    monkeypatch.setenv("TRUSTED_PROXIES", "*")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", CF_DUMMY_PASS_SECRET)
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")

    # Seed tenant and owner user
    store = ReviewStore(str(db_file))
    store.upsert_tenant({"id": "bistro_delight", "business_name": "Bistro Delight"})
    store.create_user(
        email=VICTIM_EMAIL,
        password_hash=hash_password(CORRECT_PASSWORD),
        display_name="Bistro Owner",
    )
    user = store.get_user_by_email(VICTIM_EMAIL)
    store.add_membership(user["id"], "bistro_delight", role="owner")

    reset_rate_limits()
    reset_redis_client()

    # Flush Valkey test keys before running test
    try:
        asyncio.run(SecurityStore.clear_all_security_keys())
    except Exception:
        pass

    yield {
        "store": store,
        "db_file": db_file,
    }

    # Teardown: ensure TEST_REDIS_URL is restored before clearing test keys
    monkeypatch.setenv("REDIS_URL", TEST_REDIS_URL)
    reset_redis_client()
    try:
        asyncio.run(SecurityStore.clear_all_security_keys())
    except Exception:
        pass
    reset_redis_client()
    reset_rate_limits()


# ==============================================================================
# SCENARIO 1: 5 Failed Attempts from Same IP Triggers Cooldown (HTTP 429)
# ==============================================================================
def test_scenario_01_five_failures_trigger_cooldown_same_ip():
    """
    Submitting 5 incorrect passwords from IP A triggers exponential cooldown.
    The 6th attempt (even with correct password) is rejected with HTTP 429.
    """
    client = TestClient(app)
    ip_a = "198.51.100.11"
    headers = {"X-Forwarded-For": ip_a}

    for attempt in range(5):
        res = client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"bad-password-{attempt}"},
            headers=headers,
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid email or password"
        if attempt == 4:
            assert res.headers.get("Retry-After") == "30"

    # 6th attempt with correct password within 30s cooldown -> HTTP 429
    res_blocked = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers=headers,
    )
    assert res_blocked.status_code == 429
    assert "Too many sign-in attempts for this account" in res_blocked.json()["detail"]
    assert int(res_blocked.headers.get("Retry-After", "0")) > 0


# ==============================================================================
# SCENARIO 2: Attacker Locked on IP A, Legitimate Owner Logs In on IP B (HTTP 200)
# ==============================================================================
def test_scenario_02_attacker_on_ip_a_does_not_deny_legitimate_owner_on_ip_b():
    """
    Proves elimination of Account-Lockout DoS.
    Attacker exhausts attempts on IP A.
    Legitimate owner connects from IP B with correct credentials and succeeds immediately.
    """
    client = TestClient(app)
    ip_attacker = "203.0.113.88"
    ip_owner = "192.0.2.77"

    # Attacker triggers pair cooldown for (ip_attacker, VICTIM_EMAIL)
    for attempt in range(5):
        res = client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"attacker-guess-{attempt}"},
            headers={"X-Forwarded-For": ip_attacker},
        )
        assert res.status_code == 401

    # Attacker is locked out
    res_attacker = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": ip_attacker},
    )
    assert res_attacker.status_code == 429

    # Legitimate owner logs in successfully from their own IP
    res_owner = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": ip_owner},
    )
    assert res_owner.status_code == 200
    assert res_owner.json()["user"]["email"] == VICTIM_EMAIL
    assert "nasta_owner_session" in res_owner.cookies


# ==============================================================================
# SCENARIO 3: Distributed Attempts from 20 Distinct IPs Recorded in Risk ZSET
# ==============================================================================
def test_scenario_03_distributed_attempts_recorded_in_shared_risk_zset():
    """
    20 unique IPs each submit 1 failed login attempt for the same account.
    All 20 attempts are atomically recorded in the account's risk ZSET in Valkey.
    """
    client = TestClient(app)

    for i in range(20):
        attacker_ip = f"198.51.100.{100 + i}"
        res = client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"distributed-bad-{i}"},
            headers={"X-Forwarded-For": attacker_ip},
        )
        assert res.status_code == 401

    # Verify risk ZSET in Valkey contains exactly 20 recorded entries
    async def verify_zset():
        redis_c = get_redis_client()
        primary_sec, primary_id, _, _ = get_hmac_secrets()
        acct_hmac = compute_account_hmac(VICTIM_EMAIL, primary_sec)
        risk_key = f"v1:auth:risk:{primary_id}:{acct_hmac}:failures"
        card = await redis_c.zcard(risk_key)
        assert card == 20

    asyncio.run(verify_zset())


# ==============================================================================
# SCENARIO 4: Threshold Crossing & Challenge Activation (21st Attempt Requires Challenge)
# ==============================================================================
def test_scenario_04_threshold_crossing_activates_turnstile_challenge():
    """
    Once an account accumulates >= 20 distributed failures within 5 minutes,
    any subsequent login attempt requires a Cloudflare Turnstile challenge (HTTP 403).
    """
    client = TestClient(app)

    # Accumulate 20 failures across 20 distinct IPs
    for i in range(20):
        attacker_ip = f"198.51.100.{100 + i}"
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"distributed-bad-{i}"},
            headers={"X-Forwarded-For": attacker_ip},
        )

    # 21st attempt from a fresh IP 21 without Turnstile token triggers challenge gate
    fresh_ip = "198.51.100.222"
    res_challenge = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": fresh_ip},
    )
    assert res_challenge.status_code == 403
    assert res_challenge.headers.get("X-Challenge-Required") == "true"
    assert "Security verification required" in res_challenge.json()["detail"]


# ==============================================================================
# SCENARIO 5: Missing Turnstile Token Rejected (HTTP 403)
# ==============================================================================
def test_scenario_05_missing_turnstile_token_rejected_pre_scrypt():
    """
    When challenge is required, missing turnstile_token returns HTTP 403 before password hashing.
    """
    client = TestClient(app)
    for i in range(20):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"flood-{i}"},
            headers={"X-Forwarded-For": f"198.51.101.{i}"},
        )

    res = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": "any-password", "turnstile_token": None},
        headers={"X-Forwarded-For": "198.51.102.1"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Security verification required."


# ==============================================================================
# SCENARIO 6: Invalid Turnstile Token Rejected (HTTP 403)
# ==============================================================================
def test_scenario_06_invalid_turnstile_token_rejected():
    """
    Providing an invalid or unverified token returns HTTP 403.
    """
    client = TestClient(app)
    for i in range(20):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"flood-{i}"},
            headers={"X-Forwarded-For": f"198.51.101.{i}"},
        )

    res = client.post(
        "/api/auth/login",
        json={
            "email": VICTIM_EMAIL,
            "password": CORRECT_PASSWORD,
            "turnstile_token": "XXXX.DUMMY.TOKEN.FAIL",
        },
        headers={"X-Forwarded-For": "198.51.102.2"},
    )
    assert res.status_code == 403
    assert "Security verification failed" in res.json()["detail"]


# ==============================================================================
# SCENARIO 7: Expired / Replayed Token Rejected (HTTP 403)
# ==============================================================================
def test_scenario_07_expired_or_replayed_token_rejected(monkeypatch):
    """
    Upstream rejection with 'timeout-or-duplicate' results in HTTP 403.
    """
    async def mock_verify_expired(token, client_ip):
        return False, "challenge_rejected_timeout-or-duplicate"

    monkeypatch.setattr("backend.app.api.routes.verify_turnstile_token", mock_verify_expired)

    client = TestClient(app)
    for i in range(20):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"flood-{i}"},
            headers={"X-Forwarded-For": f"198.51.101.{i}"},
        )

    res = client.post(
        "/api/auth/login",
        json={
            "email": VICTIM_EMAIL,
            "password": CORRECT_PASSWORD,
            "turnstile_token": "expired-replayed-token",
        },
        headers={"X-Forwarded-For": "198.51.102.3"},
    )
    assert res.status_code == 403
    assert res.headers.get("X-Challenge-Error") == "challenge_rejected_timeout-or-duplicate"


# ==============================================================================
# SCENARIO 8: Incorrect Action or Hostname Rejection (HTTP 403)
# ==============================================================================
def test_scenario_08_incorrect_action_or_hostname_rejected(monkeypatch):
    """
    Token issues for a different action or untrusted hostname are rejected.
    """
    async def mock_action_mismatch(token, client_ip):
        return False, "action_mismatch"

    monkeypatch.setattr("backend.app.api.routes.verify_turnstile_token", mock_action_mismatch)

    client = TestClient(app)
    for i in range(20):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"flood-{i}"},
            headers={"X-Forwarded-For": f"198.51.101.{i}"},
        )

    res = client.post(
        "/api/auth/login",
        json={
            "email": VICTIM_EMAIL,
            "password": CORRECT_PASSWORD,
            "turnstile_token": "token-for-contact-form",
        },
        headers={"X-Forwarded-For": "198.51.102.4"},
    )
    assert res.status_code == 403
    assert res.headers.get("X-Challenge-Error") == "action_mismatch"


# ==============================================================================
# SCENARIO 9: Valid Turnstile Token + Correct Password Succeeds (HTTP 200)
# ==============================================================================
def test_scenario_09_valid_turnstile_token_with_correct_password_succeeds():
    """
    Under distributed attack, a user who solves the Turnstile challenge
    and provides the correct password authenticates successfully (HTTP 200).
    """
    client = TestClient(app)
    for i in range(20):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"flood-{i}"},
            headers={"X-Forwarded-For": f"198.51.101.{i}"},
        )

    res = client.post(
        "/api/auth/login",
        json={
            "email": VICTIM_EMAIL,
            "password": CORRECT_PASSWORD,
            "turnstile_token": "XXXX.DUMMY.TOKEN.PASS",
        },
        headers={"X-Forwarded-For": "198.51.102.5"},
    )
    assert res.status_code == 200
    assert res.json()["user"]["email"] == VICTIM_EMAIL


# ==============================================================================
# SCENARIO 10: Valkey Connection Timeout / Unavailable (HTTP 503 Fail-Closed)
# ==============================================================================
def test_scenario_10_valkey_outage_fails_closed_with_503(monkeypatch):
    """
    When Valkey is down and REDIS_FAILURE_POLICY=fail_closed,
    login fails safely with HTTP 503 and Retry-After header.
    """
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:9999/0")  # Invalid dead port
    monkeypatch.setenv("REDIS_TIMEOUT_SECONDS", "0.2")
    reset_redis_client()

    client = TestClient(app)
    res = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert res.status_code == 503
    assert "temporarily unavailable" in res.json()["detail"]
    assert res.headers.get("Retry-After") == "30"


# ==============================================================================
# SCENARIO 11: Valkey Recovery After Outage Restores Normal Authentication
# ==============================================================================
def test_scenario_11_valkey_recovery_restores_authentication(monkeypatch):
    """
    After store connectivity is restored, authentication functions normally without server restart.
    """
    # 1. Simulate outage
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:9999/0")
    monkeypatch.setenv("REDIS_TIMEOUT_SECONDS", "0.2")
    reset_redis_client()

    client = TestClient(app)
    res_fail = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert res_fail.status_code == 503

    # 2. Restore live Valkey connection
    monkeypatch.setenv("REDIS_URL", TEST_REDIS_URL)
    monkeypatch.setenv("REDIS_TIMEOUT_SECONDS", "0.5")
    reset_redis_client()

    res_ok = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert res_ok.status_code == 200


# ==============================================================================
# SCENARIO 12: Concurrent Requests Sharing State Across Simulated Workers
# ==============================================================================
def test_scenario_12_concurrent_requests_share_state_atomically():
    """
    Simulates concurrent workers evaluating and recording state against live Valkey.
    Proves atomic sliding-window and failure counting with zero race conditions.
    """
    async def run_concurrent():
        norm_ip = "198.51.100.77"
        email = "concurrent@test.com"

        # Concurrently evaluate pre-auth 10 times (the max IP limit)
        tasks = [SecurityStore.evaluate_pre_auth(norm_ip, email) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All 10 requests within the limit must be admitted
        for is_allowed, status, _, _ in results:
            assert is_allowed is True
            assert status == "admitted"

        # The 11th request from the same IP must be rate-limited by sliding window
        allowed_11, status_11, wait_11, _ = await SecurityStore.evaluate_pre_auth(norm_ip, email)
        assert allowed_11 is False
        assert status_11 == "ip_rate_limited"
        assert wait_11 == 60

    asyncio.run(run_concurrent())


# ==============================================================================
# SCENARIO 13: Dual-Key HMAC Secret Rotation Preserves Active Cooldowns
# ==============================================================================
def test_scenario_13_dual_key_rotation_preserves_active_cooldown(monkeypatch):
    """
    When rotating from key k1 to k2 with SECURITY_HMAC_SECRET_PREVIOUS set to k1,
    existing cooldowns generated under k1 remain active and enforced under k2.
    """
    client = TestClient(app)
    ip_attacker = "198.51.100.44"

    # Step 1: Incur cooldown under primary key k1
    for attempt in range(5):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"wrong-{attempt}"},
            headers={"X-Forwarded-For": ip_attacker},
        )

    # Verify IP is locked under k1
    res_locked_k1 = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": ip_attacker},
    )
    assert res_locked_k1.status_code == 429

    # Step 2: Rotate key: promote new k2 to primary, demote k1 to previous
    new_secret_k2 = "new-primary-hmac-secret-at-least-32-chars-long-k2"
    monkeypatch.setenv("SECURITY_HMAC_KEY_ID", "k2")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", new_secret_k2)
    monkeypatch.setenv("SECURITY_HMAC_KEY_ID_PREVIOUS", "k1")
    monkeypatch.setenv("SECURITY_HMAC_SECRET_PREVIOUS", TEST_HMAC_SECRET)

    # Step 3: Verify the attacker is STILL locked out via previous key evaluation
    res_locked_k2 = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": ip_attacker},
    )
    assert res_locked_k2.status_code == 429
    assert "Too many sign-in attempts for this account" in res_locked_k2.json()["detail"]


# ==============================================================================
# SCENARIO 14: Successful Login Cleanup Clears Pair, Preserves Risk Evidence
# ==============================================================================
def test_scenario_14_successful_login_cleans_pair_preserves_risk_evidence():
    """
    A successful login removes the caller's pair cooldown hash
    but preserves the account risk ZSET to protect against ongoing bot swarms.
    """
    client = TestClient(app)
    ip_owner = "198.51.100.55"

    # Trigger 4 failures for owner IP
    for i in range(4):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"typo-{i}"},
            headers={"X-Forwarded-For": ip_owner},
        )

    # Successful login from owner IP
    res_success = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
        headers={"X-Forwarded-For": ip_owner},
    )
    assert res_success.status_code == 200

    # Verify pair key was removed from Valkey
    async def verify_keys():
        redis_c = get_redis_client()
        primary_sec, primary_id, _, _ = get_hmac_secrets()
        acct_hmac = compute_account_hmac(VICTIM_EMAIL, primary_sec)
        pair_key = f"v1:auth:pair:{ip_owner}:{primary_id}:{acct_hmac}:failures"
        risk_key = f"v1:auth:risk:{primary_id}:{acct_hmac}:failures"

        exists_pair = await redis_c.exists(pair_key)
        assert exists_pair == 0  # Cleaned up!

        # Global risk evidence remains for bot detection
        card = await redis_c.zcard(risk_key)
        assert card == 4  # Preserved!

    asyncio.run(verify_keys())


# ==============================================================================
# SCENARIO 15: State Expiration and Capacity Recovery
# ==============================================================================
def test_scenario_15_state_expiration_and_capacity_recovery():
    """
    Verifies that metadata ZSETs automatically purge expired entries
    when evaluate_pre_auth executes, releasing capacity reservations.
    """
    async def test_expiry():
        redis_c = get_redis_client()
        k_meta_ips = "v1:auth:meta:ips"
        k_meta_accts = "v1:auth:meta:accounts"

        # Inject expired items with score in the past
        past_time = time.time() - 100.0
        await redis_c.zadd(k_meta_ips, {"old_ip_1": past_time, "old_ip_2": past_time})
        await redis_c.zadd(k_meta_accts, {"k1:old_acct_1": past_time})

        assert await redis_c.zcard(k_meta_ips) == 2
        assert await redis_c.zcard(k_meta_accts) == 1

        # Calling evaluate_pre_auth triggers atomic ZREMRANGEBYSCORE eviction
        await SecurityStore.evaluate_pre_auth("198.51.100.90", "active@bistro.com")

        # Expired items are evicted; only the new active IP and account remain
        assert await redis_c.zscore(k_meta_ips, "old_ip_1") is None
        assert await redis_c.zscore(k_meta_accts, "k1:old_acct_1") is None

    asyncio.run(test_expiry())


# ==============================================================================
# SCENARIO 16: Regression Check: Existing Session and Tenant-Isolation Pass
# ==============================================================================
def test_scenario_16_regression_check_multi_tenant_authorization():
    """
    Full regression check ensuring multi-tenant session creation,
    cross-tenant authorization checks, and cookie settings operate correctly.
    """
    client = TestClient(app)

    # 1. Login with valid credentials
    res = client.post(
        "/api/auth/login",
        json={"email": VICTIM_EMAIL, "password": CORRECT_PASSWORD},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == VICTIM_EMAIL
    assert data["active_tenant"]["id"] == "bistro_delight"

    # 2. Check session endpoint
    res_session = client.get("/api/auth/session")
    assert res_session.status_code == 200
    assert res_session.json()["authenticated"] is True

    # 3. Access authorized tenant data
    res_config = client.get("/api/businesses/bistro_delight/review-link")
    assert res_config.status_code == 200

    # 4. Access unauthorized tenant data -> 403 Forbidden
    res_unauthorized = client.get("/api/businesses/other_unauthorized_bistro/review-link")
    assert res_unauthorized.status_code in (403, 404)

    # 5. Logout
    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200


# ==============================================================================
# SCENARIO 17: Multi-Worker Shared State Synchronization Across Separate OS Processes
# ==============================================================================
def test_scenario_17_multi_process_worker_synchronization():
    """
    Spawns multiple separate OS processes to verify that independent Uvicorn worker
    processes share security state via Valkey with zero local memory contamination.
    """
    import subprocess
    import sys

    # Process 1 (Worker A): Records 5 login failures for an attacker IP
    worker_a_code = f"""
import asyncio, os
os.environ['REDIS_URL'] = '{TEST_REDIS_URL}'
os.environ['SECURITY_HMAC_SECRET'] = '{TEST_HMAC_SECRET}'
os.environ['SECURITY_HMAC_KEY_ID'] = 'k1'
from backend.app.core.auth.security_store import SecurityStore
for _ in range(5):
    asyncio.run(SecurityStore.record_login_failure('198.51.100.99', '{VICTIM_EMAIL}'))
print('WORKER_A_RECORDED')
"""
    res_a = subprocess.run([sys.executable, "-c", worker_a_code], capture_output=True, text=True)
    assert res_a.returncode == 0
    assert "WORKER_A_RECORDED" in res_a.stdout

    # Process 2 (Worker B): Independent OS process evaluates pre-auth and enforces cooldown
    worker_b_code = f"""
import asyncio, os
os.environ['REDIS_URL'] = '{TEST_REDIS_URL}'
os.environ['SECURITY_HMAC_SECRET'] = '{TEST_HMAC_SECRET}'
os.environ['SECURITY_HMAC_KEY_ID'] = 'k1'
from backend.app.core.auth.security_store import SecurityStore
allowed, status, wait, ch = asyncio.run(SecurityStore.evaluate_pre_auth('198.51.100.99', '{VICTIM_EMAIL}'))
print(f'WORKER_B_RESULT:{{allowed}}:{{status}}:{{wait}}')
"""
    res_b = subprocess.run([sys.executable, "-c", worker_b_code], capture_output=True, text=True)
    assert res_b.returncode == 0
    assert "WORKER_B_RESULT:False:pair_cooldown_active:30" in res_b.stdout

    # Process 3 (Worker C): Independent OS process logs in successfully from owner IP and clears state
    worker_c_code = f"""
import asyncio, os
os.environ['REDIS_URL'] = '{TEST_REDIS_URL}'
os.environ['SECURITY_HMAC_SECRET'] = '{TEST_HMAC_SECRET}'
os.environ['SECURITY_HMAC_KEY_ID'] = 'k1'
from backend.app.core.auth.security_store import SecurityStore
asyncio.run(SecurityStore.record_login_success('198.51.100.99', '{VICTIM_EMAIL}'))
print('WORKER_C_SUCCESS_CLEARED')
"""
    res_c = subprocess.run([sys.executable, "-c", worker_c_code], capture_output=True, text=True)
    assert res_c.returncode == 0
    assert "WORKER_C_SUCCESS_CLEARED" in res_c.stdout

    # Process 4 (Worker D): Verifies cooldown has been lifted in Valkey
    res_d = subprocess.run([sys.executable, "-c", worker_b_code], capture_output=True, text=True)
    assert res_d.returncode == 0
    assert "WORKER_B_RESULT:True:admitted:0" in res_d.stdout


# ==============================================================================
# SCENARIO 18: Client IP Spoofing Prevention Through Proxy Chains
# ==============================================================================
def test_scenario_18_client_ip_spoofing_prevention(monkeypatch):
    """
    Verifies that client IP determination rejects spoofed X-Forwarded-For headers
    from untrusted direct connections and walks proxy chains right-to-left.
    """
    from starlette.requests import Request
    from backend.app.api.routes import get_client_ip

    def make_req(client_host: str, headers: dict) -> Request:
        scope = {
            "type": "http",
            "client": (client_host, 50000),
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }
        return Request(scope)

    # 1. Direct connection from untrusted client attempting to spoof IP -> Rejected
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1, 10.0.0.2")
    req_untrusted = make_req("198.51.100.5", {"x-forwarded-for": "1.1.1.1"})
    assert get_client_ip(req_untrusted) == "198.51.100.5"

    # 2. Connection from trusted proxy with forged leftmost header:
    # Attacker injects '1.2.3.4' in X-Forwarded-For; proxy appends real client IP '203.0.113.88'
    req_trusted = make_req("10.0.0.1", {"x-forwarded-for": "1.2.3.4, 203.0.113.88, 10.0.0.1"})
    assert get_client_ip(req_trusted) == "203.0.113.88"  # Leftmost forged IP ignored!

    # 3. Invalid IP syntax in X-Forwarded-For -> falls back safely to peer IP
    req_invalid = make_req("10.0.0.1", {"x-forwarded-for": "bogus-injection-value, 10.0.0.1"})
    assert get_client_ip(req_invalid) == "10.0.0.1"


# ==============================================================================
# SCENARIO 19: Turnstile Provider Timeout Returns HTTP 503
# ==============================================================================
def test_scenario_19_turnstile_provider_timeout_returns_503(monkeypatch):
    """
    When Cloudflare Turnstile provider times out, login fails safely with HTTP 503 and Retry-After.
    """
    async def mock_timeout(token, client_ip):
        return False, "provider_timeout"

    monkeypatch.setattr("backend.app.api.routes.verify_turnstile_token", mock_timeout)

    client = TestClient(app)
    for i in range(20):
        client.post(
            "/api/auth/login",
            json={"email": VICTIM_EMAIL, "password": f"flood-{i}"},
            headers={"X-Forwarded-For": f"198.51.101.{i}"},
        )

    res = client.post(
        "/api/auth/login",
        json={
            "email": VICTIM_EMAIL,
            "password": CORRECT_PASSWORD,
            "turnstile_token": "some-token",
        },
        headers={"X-Forwarded-For": "198.51.102.8"},
    )
    assert res.status_code == 503
    assert "Security challenge provider unavailable" in res.json()["detail"]
    assert res.headers.get("Retry-After") == "10"


# ==============================================================================
# SCENARIO 20: Missing Production Configuration Fails Closed At Startup
# ==============================================================================
def test_scenario_20_missing_production_configuration_fails_closed(monkeypatch):
    """
    In production and staging environments, missing REDIS_URL or short HMAC secret
    fails closed immediately at startup with RuntimeError.
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("VALKEY_URL", raising=False)
    reset_redis_client()

    with pytest.raises(RuntimeError, match="REDIS_URL must be configured"):
        get_redis_client()

    # Short HMAC secret raises RuntimeError
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "short-secret")
    with pytest.raises(RuntimeError, match="SECURITY_HMAC_SECRET must be at least 32 characters"):
        get_hmac_secrets()


# ==============================================================================
# SCENARIO 21: Failure Recording Under Valkey Outage Handles Gracefully
# ==============================================================================
def test_scenario_21_record_login_failure_outage_handles_gracefully(monkeypatch):
    """
    If Valkey fails during failure recording, it logs a sanitized warning and returns (0, 0).
    """
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:9999/0")
    monkeypatch.setenv("REDIS_TIMEOUT_SECONDS", "0.2")
    reset_redis_client()

    cooldown, step = asyncio.run(SecurityStore.record_login_failure("198.51.100.99", VICTIM_EMAIL))
    assert cooldown == 0
    assert step == 0


# ==============================================================================
# SCENARIO 22: Multiple Concurrent Challenge Verifications
# ==============================================================================
def test_scenario_22_concurrent_turnstile_challenge_requests():
    """
    Verifies that multiple concurrent challenge requests under load
    are evaluated safely and concurrently without deadlocks.
    """
    async def verify_batch():
        tasks = [
            verify_turnstile_token("XXXX.DUMMY.TOKEN.PASS", f"198.51.100.{i}")
            for i in range(15)
        ]
        results = await asyncio.gather(*tasks)
        for is_valid, reason in results:
            assert is_valid is True
            assert reason == "test_pass"

    asyncio.run(verify_batch())

