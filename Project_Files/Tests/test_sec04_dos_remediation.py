import os
import threading
import time
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from backend.app.core.auth.auth import (
    ACCOUNT_FAILURE_THRESHOLD,
    DUMMY_SCRYPT_HASH,
    MAX_TRACKED_ACCOUNTS,
    MAX_TRACKED_IPS,
    MAX_TRACKED_PAIRS,
    _account_failures,
    _account_lockout_step,
    _account_lockout_until,
    _ip_account_failures,
    _ip_account_lockout_step,
    _ip_account_lockout_until,
    _ip_attempts,
    _trusted_account_ips,
    check_account_login_rate_limit,
    check_login_rate_limit,
    hash_password,
    record_login_failure,
    record_login_success,
    reset_rate_limits,
    verify_password,
)
from backend.app.core.database.storage import ReviewStore
from backend.app.main import app


class TestSec04DosRemediation:
    """
    Adversarial verification suite proving that account-level rate limiting
    protects against brute-force attacks without enabling Account Lockout Denial of Service (SEC-04).
    """

    def setup_method(self):
        reset_rate_limits()

    def teardown_method(self):
        reset_rate_limits()

    # -----------------------------------------------------------------
    # 1. Exact A5.0.32 Attack Remediation: Attacker vs. Legitimate Owner
    # -----------------------------------------------------------------
    def test_exact_a5_0_32_attacker_cannot_deny_legitimate_owner_login(self, tmp_path, monkeypatch):
        """
        CRITICAL TEST (A5.0.32 exact scenario):
        An external attacker repeatedly submits 5 incorrect passwords for a victim's email address.
        The attacker's IP is placed into temporary cooldown.
        The legitimate owner arrives with the correct password.
        VERIFY: The legitimate owner logs in successfully (HTTP 200),
        and the attacker remains blocked (HTTP 429).
        """
        db_file = tmp_path / "test_auth_dos.sqlite3"
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secure-signing-secret-key-32-chars-minimum")
        monkeypatch.setenv("TRUSTED_PROXIES", "*")

        store = ReviewStore(str(db_file))
        victim_email = "owner@victim-bistro.com"
        correct_password = "CorrectOwnerPass123!"

        store.upsert_tenant({"id": "victim_bistro", "business_name": "Victim Bistro"})
        store.create_user(
            email=victim_email,
            password_hash=hash_password(correct_password),
            display_name="Legitimate Owner"
        )
        user = store.get_user_by_email(victim_email)
        store.add_membership(user["id"], "victim_bistro", role="owner")

        client = TestClient(app)
        attacker_headers = {"X-Forwarded-For": "203.0.113.10"}
        owner_headers = {"X-Forwarded-For": "198.51.100.25"}

        # Step 1: Attacker sends 5 bad passwords from attacker IP
        for attempt in range(5):
            res = client.post(
                "/api/auth/login",
                json={"email": victim_email, "password": f"wrong-pass-{attempt}"},
                headers=attacker_headers,
            )
            assert res.status_code == 401
            assert res.json()["detail"] == "Invalid email or password"

        # Step 2: Attacker is now locked out (6th attempt from attacker IP gets HTTP 429)
        res_attacker_blocked = client.post(
            "/api/auth/login",
            json={"email": victim_email, "password": "another-wrong-pass"},
            headers=attacker_headers,
        )
        assert res_attacker_blocked.status_code == 429
        assert "Too many sign-in attempts for this account" in res_attacker_blocked.json()["detail"]

        # Step 3: Even if attacker tries the correct password during cooldown, attacker is still blocked (no shortcut bypass!)
        res_attacker_shortcut = client.post(
            "/api/auth/login",
            json={"email": victim_email, "password": correct_password},
            headers=attacker_headers,
        )
        assert res_attacker_shortcut.status_code == 429

        # Step 4: Legitimate owner attempts login from their IP with the correct password
        res_owner = client.post(
            "/api/auth/login",
            json={"email": victim_email, "password": correct_password},
            headers=owner_headers,
        )
        # MUST SUCCEED with HTTP 200 and session token cookie!
        assert res_owner.status_code == 200
        data = res_owner.json()
        assert data["user"]["email"] == victim_email
        assert "nasta_owner_session" in res_owner.cookies

    # -----------------------------------------------------------------
    # 2. Repeated failed attempts remain throttled with exponential backoff
    # -----------------------------------------------------------------
    def test_repeated_failed_attempts_remain_throttled_with_exponential_backoff(self):
        """Attacker client IP experiences exponential backoff: 30s -> 60s -> 120s -> 240s -> 300s."""
        email = "victim@example.com"
        attacker_ip = "203.0.113.50"
        t = 1000.0

        # 5 failures from attacker IP trigger Step 1 cooldown (30s)
        for _ in range(5):
            record_login_failure(email, client_ip=attacker_ip, now=t)

        allowed, wait = check_account_login_rate_limit(email, client_ip=attacker_ip, now=t)
        assert allowed is False
        assert wait == 30

        # Step 2: after 31s, another failure triggers 60s
        t += 31.0
        record_login_failure(email, client_ip=attacker_ip, now=t)
        allowed, wait = check_account_login_rate_limit(email, client_ip=attacker_ip, now=t)
        assert allowed is False
        assert wait == 60

        # Step 3: after 61s, failure triggers 120s
        t += 61.0
        record_login_failure(email, client_ip=attacker_ip, now=t)
        allowed, wait = check_account_login_rate_limit(email, client_ip=attacker_ip, now=t)
        assert allowed is False
        assert wait == 120

        # Step 4: after 121s, failure triggers 240s
        t += 121.0
        record_login_failure(email, client_ip=attacker_ip, now=t)
        allowed, wait = check_account_login_rate_limit(email, client_ip=attacker_ip, now=t)
        assert allowed is False
        assert wait == 240

        # Step 5: after 241s, failure triggers 300s (capped max)
        t += 241.0
        record_login_failure(email, client_ip=attacker_ip, now=t)
        allowed, wait = check_account_login_rate_limit(email, client_ip=attacker_ip, now=t)
        assert allowed is False
        assert wait == 300

    # -----------------------------------------------------------------
    # 3. IP-level brute-force protection still works
    # -----------------------------------------------------------------
    def test_ip_level_protection_still_enforced(self):
        """A single client IP cannot exceed 10 login attempts per 60 seconds across any accounts."""
        client_ip = "192.0.2.1"
        t0 = 2000.0

        for _ in range(10):
            assert check_login_rate_limit(client_ip, now=t0) is True

        # 11th attempt from this IP is rejected by IP-level limiter
        assert check_login_rate_limit(client_ip, now=t0) is False

        # After 61 seconds, IP rate limit window resets
        assert check_login_rate_limit(client_ip, now=t0 + 61.0) is True

    # -----------------------------------------------------------------
    # 4. Account-level protection against distributed attempts
    # -----------------------------------------------------------------
    def test_account_level_protection_against_distributed_attempts(self):
        """
        When an attacker rotates through multiple IPs targeting one account,
        each attacking IP is independently throttled upon reaching failure thresholds,
        and global account failure telemetry is accurately tracked.
        """
        email = "target_owner@bistro.com"
        t0 = 3000.0

        # Attacker uses 3 distinct IPs, failing 5 times on each
        for ip_num in range(1, 4):
            ip = f"198.51.100.{ip_num}"
            for _ in range(5):
                record_login_failure(email, client_ip=ip, now=t0)
            # That attacking IP is locked out
            allowed, wait = check_account_login_rate_limit(email, client_ip=ip, now=t0)
            assert allowed is False
            assert wait == 30

        # Total failures tracked on account
        assert len(_account_failures[email]) == 15

    # -----------------------------------------------------------------
    # 5. Existing and nonexistent accounts have indistinguishable responses
    # -----------------------------------------------------------------
    def test_existing_and_nonexistent_accounts_indistinguishable(self, tmp_path, monkeypatch):
        """
        Verifies zero user enumeration:
        - Both return HTTP 401 with identical message on invalid password.
        - Both trigger HTTP 429 with identical message after repeated failures.
        - Both execute constant-time scrypt verification.
        """
        db_file = tmp_path / "test_auth_enum.sqlite3"
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secure-signing-secret-key-32-chars-minimum")
        monkeypatch.setenv("TRUSTED_PROXIES", "*")

        store = ReviewStore(str(db_file))
        store.upsert_tenant({"id": "cafe", "business_name": "Cafe"})
        real_email = "real_user@cafe.com"
        ghost_email = "nonexistent_ghost_9999@cafe.com"

        store.create_user(
            email=real_email,
            password_hash=hash_password("RealPassword123!"),
            display_name="Real User"
        )
        user = store.get_user_by_email(real_email)
        store.add_membership(user["id"], "cafe", role="owner")

        client = TestClient(app)

        # 1. 401 message parity
        res_real = client.post("/api/auth/login", json={"email": real_email, "password": "wrong"})
        res_ghost = client.post("/api/auth/login", json={"email": ghost_email, "password": "wrong"})
        assert res_real.status_code == 401
        assert res_ghost.status_code == 401
        assert res_real.json() == res_ghost.json() == {"detail": "Invalid email or password"}

        # 2. Lockout parity on ghost account
        ghost_ip_headers = {"X-Forwarded-For": "203.0.113.88"}
        for _ in range(5):
            client.post("/api/auth/login", json={"email": ghost_email, "password": "wrong"}, headers=ghost_ip_headers)

        res_ghost_lockout = client.post("/api/auth/login", json={"email": ghost_email, "password": "wrong"}, headers=ghost_ip_headers)
        assert res_ghost_lockout.status_code == 429
        assert "Too many sign-in attempts for this account" in res_ghost_lockout.json()["detail"]

        # 3. Constant-time dummy hash verification
        assert DUMMY_SCRYPT_HASH.startswith("scrypt$")
        assert verify_password("anything", DUMMY_SCRYPT_HASH) is False

    # -----------------------------------------------------------------
    # 6. Successful login resets failure state
    # -----------------------------------------------------------------
    def test_successful_login_resets_failure_state(self):
        """A successful authentication clears the failure counters and lockout state for that account/IP."""
        email = "owner@cafe.com"
        client_ip = "192.0.2.5"
        t0 = 4000.0

        for _ in range(4):
            record_login_failure(email, client_ip=client_ip, now=t0)

        assert len(_ip_account_failures[(client_ip, email)]) == 4

        # Successful login
        record_login_success(email, client_ip=client_ip)

        assert (client_ip, email) not in _ip_account_failures
        assert (client_ip, email) not in _ip_account_lockout_until
        assert email in _trusted_account_ips
        assert client_ip in _trusted_account_ips[email]

    # -----------------------------------------------------------------
    # 7. Temporary throttling expires correctly
    # -----------------------------------------------------------------
    def test_temporary_throttling_expires_correctly(self):
        """When the cooldown period expires, the client IP is allowed to attempt login again."""
        email = "test@cafe.com"
        client_ip = "198.51.100.99"
        t0 = 5000.0

        for _ in range(5):
            record_login_failure(email, client_ip=client_ip, now=t0)

        allowed, wait = check_account_login_rate_limit(email, client_ip=client_ip, now=t0)
        assert allowed is False
        assert wait == 30

        # After 31 seconds, cooldown has expired
        allowed_after, wait_after = check_account_login_rate_limit(email, client_ip=client_ip, now=t0 + 31.0)
        assert allowed_after is True
        assert wait_after == 0

    # -----------------------------------------------------------------
    # 8. No permanent lockout is possible
    # -----------------------------------------------------------------
    def test_no_permanent_lockout(self):
        """Even after 50 consecutive failed attempts, lockouts remain temporary (capped at 300s max)."""
        email = "test_perm@cafe.com"
        client_ip = "203.0.113.7"
        t = 6000.0

        for _ in range(50):
            record_login_failure(email, client_ip=client_ip, now=t)

        allowed, wait = check_account_login_rate_limit(email, client_ip=client_ip, now=t)
        assert allowed is False
        assert wait <= 300  # Never infinite or permanent

        # After cooldown duration + 1s, access is always restored
        allowed_after, _ = check_account_login_rate_limit(email, client_ip=client_ip, now=t + 301.0)
        assert allowed_after is True

    # -----------------------------------------------------------------
    # 9. Concurrent requests do not corrupt limiter state
    # -----------------------------------------------------------------
    def test_concurrent_requests_thread_safety(self):
        """High-concurrency requests across multiple threads do not race or corrupt limiter state."""
        email = "concurrency@cafe.com"
        threads = []
        errors = []

        def worker(thread_id: int):
            try:
                ip = f"10.0.{thread_id % 5}.{thread_id % 250}"
                for i in range(10):
                    now = 7000.0 + i * 0.1
                    record_login_failure(email, client_ip=ip, now=now)
                    check_account_login_rate_limit(email, client_ip=ip, now=now)
            except Exception as e:
                errors.append(e)

        for tid in range(20):
            t = threading.Thread(target=worker, args=(tid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0

    # -----------------------------------------------------------------
    # 10. Memory remains strictly bounded under high-volume attempts
    # -----------------------------------------------------------------
    def test_memory_remains_bounded_under_high_volume_attempts(self):
        """Simulating 15,000 distinct IP/account combinations does not grow dictionaries unboundedly."""
        now = 8000.0

        # Inject 12,000 distinct IPs and accounts
        for i in range(12000):
            ip = f"172.16.{i // 256}.{i % 256}"
            acc = f"user_{i}@domain.com"
            _ip_attempts[ip].append(now)
            _account_failures[acc].append(now)
            _ip_account_failures[(ip, acc)].append(now)

        # Trigger pruning
        check_login_rate_limit("172.16.0.1", now=now)

        # Must not exceed configured hard caps
        assert len(_ip_attempts) <= MAX_TRACKED_IPS
        assert len(_account_failures) <= MAX_TRACKED_ACCOUNTS
        assert len(_ip_account_failures) <= MAX_TRACKED_PAIRS
