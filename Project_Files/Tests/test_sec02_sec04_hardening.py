"""
VRAJA AI — Product A Security Hardening Test Suite (Phase A5.0.31)

Validates complete remediation of:
- SEC-02: Predictable fallback signing secret elimination & fail-closed enforcement
- SEC-04: Process-local bounded login rate limiting and account-level abuse protection
"""

import os
import time
from typing import Dict, Any
import pytest
from starlette.testclient import TestClient

from backend.app.core.auth.auth import (
    get_signing_secret,
    create_preview_token,
    verify_preview_token,
    check_login_rate_limit,
    check_account_login_rate_limit,
    record_login_failure,
    record_login_success,
    reset_rate_limits,
    normalize_account_identity,
    MAX_TRACKED_IPS,
    MAX_TRACKED_ACCOUNTS,
    _prune_expired_entries,
    _ip_attempts,
    _account_failures,
    _account_lockout_until,
    _account_lockout_step,
)
from backend.app.core.database.storage import ReviewStore
from backend.app.main import app


# ─────────────────────────────────────────────────────────────────────────────
# SEC-02 TESTS: SIGNING SECRET HARDENING & FAIL-CLOSED ENFORCEMENT
# ─────────────────────────────────────────────────────────────────────────────

class TestSec02SigningSecretHardening:
    """Comprehensive test cases for SEC-02 remediation."""

    def test_production_fails_closed_when_secret_missing(self, monkeypatch):
        """In production, missing OWNER_SESSION_SECRET raises RuntimeError."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="Missing or insecure OWNER_SESSION_SECRET in environment 'production'"):
            get_signing_secret()

    def test_production_fails_closed_when_secret_too_short(self, monkeypatch):
        """In production, secret < 32 characters raises RuntimeError."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("OWNER_SESSION_SECRET", "short-secret-under-32-chars")
        with pytest.raises(RuntimeError, match="Must be configured with at least 32 characters"):
            get_signing_secret()

    def test_staging_fails_closed_when_secret_missing(self, monkeypatch):
        """In staging, missing OWNER_SESSION_SECRET raises RuntimeError."""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="Missing or insecure OWNER_SESSION_SECRET in environment 'staging'"):
            get_signing_secret()

    def test_staging_fails_closed_when_secret_too_short(self, monkeypatch):
        """In staging, secret < 32 characters raises RuntimeError."""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("OWNER_SESSION_SECRET", "short-staging-secret")
        with pytest.raises(RuntimeError, match="Must be configured with at least 32 characters"):
            get_signing_secret()

    def test_unconfigured_env_fails_closed(self, monkeypatch):
        """Ambiguous/unset ENVIRONMENT fails closed if secret is missing."""
        monkeypatch.setenv("ENVIRONMENT", "")
        monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="Missing or insecure OWNER_SESSION_SECRET"):
            get_signing_secret()

    def test_production_and_staging_succeed_with_valid_configured_secret(self, monkeypatch):
        """Valid configured secret (>= 32 chars) is accepted in production and staging."""
        valid_secret = "a-very-long-production-grade-signing-secret-64-bytes-entropy-here!!"
        for env in ("production", "staging"):
            monkeypatch.setenv("ENVIRONMENT", env)
            monkeypatch.setenv("OWNER_SESSION_SECRET", valid_secret)
            assert get_signing_secret() == valid_secret

    def test_dev_test_uses_configured_secret_when_present(self, monkeypatch):
        """Development and test environments use configured secret if >= 32 chars."""
        dev_secret = "developer-configured-session-secret-32-bytes!!"
        for env in ("dev", "development", "test", "testing"):
            monkeypatch.setenv("ENVIRONMENT", env)
            monkeypatch.setenv("OWNER_SESSION_SECRET", dev_secret)
            assert get_signing_secret() == dev_secret

    def test_dev_test_generates_stable_ephemeral_secret_when_unset(self, monkeypatch):
        """When unset in dev/test, a stable ephemeral secret is generated once and retained."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)

        # Clear cached dev secret for isolated test
        import backend.app.core.auth.auth as auth_mod
        auth_mod._EPHEMERAL_DEV_SECRET = None

        secret_1 = get_signing_secret()
        assert len(secret_1) == 64  # secrets.token_hex(32) produces 64 hex chars
        assert isinstance(secret_1, str)

        # Second call within same process returns the EXACT same stable secret
        secret_2 = get_signing_secret()
        assert secret_1 == secret_2

    def test_preview_token_lifecycle_with_hardened_secret(self, monkeypatch):
        """Preview token generation and signature verification succeed with hardened secret."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("OWNER_SESSION_SECRET", "custom-token-signing-secret-key-at-least-32-chars")

        token = create_preview_token(tenant_id="test_cafe", user_id="user_123", role="owner")
        assert token is not None
        assert "." in token

        verified = verify_preview_token(token)
        assert verified is not None
        assert verified["tenant_id"] == "test_cafe"
        assert verified["user_id"] == "user_123"

        # Tampered signature fails verification
        payload_b64, sig = token.split(".", 1)
        tampered_token = f"{payload_b64}.tampered_signature"
        assert verify_preview_token(tampered_token) is None


# ─────────────────────────────────────────────────────────────────────────────
# SEC-04 TESTS: LOGIN ABUSE PROTECTION & BOUNDED RATE LIMITING
# ─────────────────────────────────────────────────────────────────────────────

class TestSec04LoginAbuseProtection:
    """Comprehensive test cases for SEC-04 remediation."""

    @pytest.fixture(autouse=True)
    def clean_limits(self):
        """Reset rate limit state before and after each test."""
        reset_rate_limits()
        yield
        reset_rate_limits()

    def test_per_ip_rate_limit_allows_under_threshold(self):
        """Allows up to 10 attempts per minute from one IP."""
        client_ip = "192.168.1.100"
        t0 = 1000.0
        for _ in range(10):
            assert check_login_rate_limit(client_ip, now=t0) is True

        # 11th attempt is blocked
        assert check_login_rate_limit(client_ip, now=t0) is False

        # Attempt after 61 seconds is allowed
        assert check_login_rate_limit(client_ip, now=t0 + 61.0) is True

    def test_account_level_temporary_restriction_after_consecutive_failures(self):
        """Repeated failed attempts for an account trigger temporary restriction (not permanent)."""
        email = "Owner@TestCafe.com"
        t0 = 2000.0

        # First 4 failures do not lock out
        for _ in range(4):
            record_login_failure(email, now=t0)
            allowed, _ = check_account_login_rate_limit(email, now=t0)
            assert allowed is True

        # 5th failure triggers 30-second initial cooldown
        record_login_failure(email, now=t0)
        allowed, wait_secs = check_account_login_rate_limit(email, now=t0)
        assert allowed is False
        assert wait_secs == 30

        # After 31 seconds, restriction has expired
        allowed_after, wait_after = check_account_login_rate_limit(email, now=t0 + 31.0)
        assert allowed_after is True
        assert wait_after == 0

    def test_account_exponential_backoff_steps(self):
        """Subsequent failure bursts trigger exponential backoff: 30s -> 60s -> 120s -> 300s max."""
        email = "victim@example.com"
        t = 3000.0

        # Step 1: 5 failures -> 30s
        for _ in range(5):
            record_login_failure(email, now=t)
        allowed, wait = check_account_login_rate_limit(email, now=t)
        assert allowed is False
        assert wait == 30

        # Step 2: after 31s, another failure triggers step 2 (60s)
        t += 31.0
        record_login_failure(email, now=t)
        allowed, wait = check_account_login_rate_limit(email, now=t)
        assert allowed is False
        assert wait == 60

        # Step 3: after 61s, failure triggers step 3 (120s)
        t += 61.0
        record_login_failure(email, now=t)
        allowed, wait = check_account_login_rate_limit(email, now=t)
        assert allowed is False
        assert wait == 120

        # Step 4: after 121s, failure triggers step 4 (capped at 300s)
        t += 121.0
        record_login_failure(email, now=t)
        allowed, wait = check_account_login_rate_limit(email, now=t)
        assert allowed is False
        assert wait == 240

        t += 241.0
        record_login_failure(email, now=t)
        allowed, wait = check_account_login_rate_limit(email, now=t)
        assert allowed is False
        assert wait == 300  # Capped at 300s max

    def test_multi_ip_attack_against_single_account_is_blocked(self):
        """Attacker rotating through multiple client IPs targeting one account is blocked by account protection."""
        email = "target_owner@cafe.com"
        t0 = 4000.0

        # 5 requests from 5 completely different IP addresses
        attacker_ips = [f"203.0.113.{i}" for i in range(1, 6)]
        for ip in attacker_ips:
            # Each IP has made only 1 attempt, so IP check passes
            assert check_login_rate_limit(ip, now=t0) is True
            # Account records the failed password attempt
            record_login_failure(email, now=t0)

        # 6th attempt from a brand-new 6th IP address targeting the same account is BLOCKED
        new_ip = "203.0.113.99"
        assert check_login_rate_limit(new_ip, now=t0) is True
        allowed, wait = check_account_login_rate_limit(email, now=t0)
        assert allowed is False
        assert wait > 0

    def test_multiple_accounts_from_one_ip_preserves_ip_rate_limit(self):
        """Multiple different accounts targeted from one IP are subject to the per-IP rate limit."""
        client_ip = "198.51.100.50"
        t0 = 5000.0

        # 10 different accounts attempted from one IP
        for i in range(10):
            acc = f"user_{i}@example.com"
            assert check_login_rate_limit(client_ip, now=t0) is True
            assert check_account_login_rate_limit(acc, now=t0)[0] is True

        # 11th account from the same IP is blocked by IP rate limit
        assert check_login_rate_limit(client_ip, now=t0) is False

    def test_nonexistent_user_behavior_identical_no_enumeration(self):
        """Nonexistent accounts exhibit identical rate limiting behavior without leaking user existence."""
        ghost_email = "nonexistent_ghost_999@domain.org"
        t0 = 6000.0

        for _ in range(5):
            record_login_failure(ghost_email, now=t0)

        # Nonexistent user is restricted identically
        allowed, wait = check_account_login_rate_limit(ghost_email, now=t0)
        assert allowed is False
        assert wait == 30

    def test_successful_login_resets_failed_attempts(self):
        """A successful authentication immediately clears failure counts and backoff state."""
        email = "legit_owner@testcafe.com"
        t0 = 7000.0

        # 4 failed attempts
        for _ in range(4):
            record_login_failure(email, now=t0)

        # Successful login resets the account
        record_login_success(email)

        # Next 4 failed attempts do not trigger lockout because counter was reset
        for _ in range(4):
            record_login_failure(email, now=t0)
            assert check_account_login_rate_limit(email, now=t0)[0] is True

    def test_bounded_memory_pruning(self):
        """Pruning maintains bounded dictionaries and evicts expired records."""
        t0 = 8000.0
        # Populate 50 IP entries and 50 account entries
        for i in range(50):
            _ip_attempts[f"ip_{i}"].append(t0)
            _account_failures[f"user_{i}@test.com"].append(t0)

        assert len(_ip_attempts) == 50
        assert len(_account_failures) == 50

        # Prune after window has elapsed (window is 300s for accounts, 60s for IPs)
        _prune_expired_entries(now=t0 + 400.0)

        assert len(_ip_attempts) == 0
        assert len(_account_failures) == 0

    def test_api_endpoint_login_lockout_integration(self, tmp_path, monkeypatch):
        """FastAPI /api/auth/login integration verifies HTTP 429 when account is restricted."""
        from backend.app.core.database.storage import ReviewStore

        db_file = tmp_path / "test_auth_api.sqlite3"
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        monkeypatch.setenv("OWNER_SESSION_SECRET", "test-api-session-secret-key-32-bytes!!")

        # Initialize test database and create a test user
        store = ReviewStore(str(db_file))
        from backend.app.core.auth.auth import hash_password
        store.upsert_tenant({"id": "cafe_test", "business_name": "Cafe Test"})
        store.create_user(
            email="owner@testlockout.com",
            password_hash=hash_password("ValidPassword123!"),
            display_name="Test Owner"
        )
        user = store.get_user_by_email("owner@testlockout.com")
        store.add_membership(user["id"], "cafe_test", role="owner")

        client = TestClient(app)

        # Submit 5 failed password attempts
        for i in range(5):
            res = client.post("/api/auth/login", json={
                "email": "owner@testlockout.com",
                "password": "WrongPassword999!"
            })
            assert res.status_code == 401
            assert res.json()["detail"] == "Invalid email or password"

        # 6th attempt is blocked by account-level rate limiter with HTTP 429
        res_blocked = client.post("/api/auth/login", json={
            "email": "owner@testlockout.com",
            "password": "ValidPassword123!"  # Even with correct password, blocked during restriction window
        })
        assert res_blocked.status_code == 429
        assert "Too many sign-in attempts for this account" in res_blocked.json()["detail"]
