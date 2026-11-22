"""
VRAJA AI — PHASE A6.5.3: STAGING SAFETY GATE & NEGATIVE SAFETY MATRIX
Automated regression tests verifying:
1. Isolated staging database mock email test execution & outbox isolation.
2. The 8 mandatory negative safety edge cases.
"""

import os
import sys
import time
import pytest
from pathlib import Path
from starlette.testclient import TestClient

from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import hash_password, OWNER_COOKIE
from Backend.app.core.security.security_store import SecurityStore
from Backend.app.core.security.alert_mailer import AlertMailer, DEFAULT_ALERT_EMAIL
from Backend.app.main import app


@pytest.fixture
def staging_gate_env(tmp_path, monkeypatch):
    stag_rev = tmp_path / "reviews_staging.sqlite3"
    stag_sec = tmp_path / "security_staging.sqlite3"

    monkeypatch.setenv("REVIEW_DB_PATH", str(stag_rev))
    monkeypatch.setenv("SECURITY_DB_PATH", str(stag_sec))
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("MOCK_EMAIL_TRANSPORT", "true")
    monkeypatch.setenv("PAUSE_INCIDENT_DISPATCH", "true")
    monkeypatch.setenv("ALLOW_LIVE_SMTP_TEST", "false")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    rev_store = ReviewStore(str(stag_rev))
    sec_store = SecurityStore(str(stag_sec))
    now = time.time()

    with rev_store._connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO tenants (id, business_name, status, platform, entitlements_json, created_at, updated_at)
            VALUES ('default_business', 'Nasta Ghar Staging', 'active', 'google', '["review_manager", "digital_card"]', ?, ?)
        """, (now, now))
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('u_stag_adm', 'admin@platform.vraja', ?, 'Staging Admin', 1, 1, ?, ?)
        """, (hash_password("SecAdmGatePass987!"), now, now))
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('u_stag_own', 'owner@cafe.com', ?, 'Cafe Owner', 1, 0, ?, ?)
        """, (hash_password("SecOwnGatePass456!"), now, now))

    rev_store.add_membership("u_stag_adm", "default_business", role="owner")
    rev_store.add_membership("u_stag_own", "default_business", role="owner")

    return {
        "rev_store": rev_store,
        "sec_store": sec_store,
        "stag_rev": stag_rev,
        "stag_sec": stag_sec,
    }


def test_task4_mock_security_email_and_outbox_isolation(staging_gate_env):
    """
    Verifies admin auth, CSRF Origin protection, test alert creation, approved recipient,
    test ID, status endpoint, and that incident outbox remains untouched.
    """
    from Backend.app.api.service import review_service
    review_service._rate_limits.clear()
    client = TestClient(app)
    sec_store = staging_gate_env["sec_store"]

    # 1. Pre-queue a regular incident alert in outbox
    sec_store.queue_alert(
        incident_id="inc_preexisting",
        recipient="incident-team@vraja.ai",
        subject="[ALERT] Pre-existing Breach",
        body_text="Alert details",
        body_html="<p>Alert details</p>",
        severity="HIGH"
    )
    outbox_before, count_before = sec_store.list_outbox()
    assert count_before == 1

    # 2. Authenticate platform admin
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@platform.vraja", "password": "SecAdmGatePass987!", "tenant_id": "default_business"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert login_res.status_code == 200
    assert OWNER_COOKIE in login_res.cookies
    token = login_res.cookies[OWNER_COOKIE]

    # 3. Verify CSRF rejection on missing/untrusted origin
    bad_origin = client.post(
        "/api/platform/security-shield/test-alert",
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://untrusted-attacker.com"},
        json={"scenario": "csrf_probe"}
    )
    assert bad_origin.status_code == 403

    # 4. Trigger one authorized synthetic test alert
    alert_res = client.post(
        "/api/platform/security-shield/test-alert",
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"},
        json={"scenario": "staging_mock_run"}
    )
    assert alert_res.status_code == 200
    data = alert_res.json()
    assert data["status"] == "MOCK_SENT"
    assert data["recipient"] == DEFAULT_ALERT_EMAIL
    assert data["is_synthetic"] is True
    test_id = data["test_id"]
    assert test_id.startswith("syn_test_")

    # 5. Verify status endpoint
    status_res = client.get(
        f"/api/platform/security-shield/test-alert/{test_id}",
        cookies={OWNER_COOKIE: token}
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["test_id"] == test_id
    assert status_data["status"] == "mock_sent"
    assert status_data["recipient"] == DEFAULT_ALERT_EMAIL

    # 6. Verify incident outbox remained paused and completely untouched
    mailer = AlertMailer()
    res_worker = mailer.process_outbox(sec_store)
    assert res_worker.get("paused") is True
    outbox_after, count_after = sec_store.list_outbox()
    assert count_before == count_after
    assert outbox_before[0]["id"] == outbox_after[0]["id"]
    assert outbox_after[0]["status"] == "pending"


def test_negative_1_missing_pause_incident_dispatch_blocks_live_testing(staging_gate_env, monkeypatch):
    """Missing PAUSE_INCIDENT_DISPATCH in staging strictly blocks live synthetic test."""
    from Backend.app.api.service import review_service
    review_service._rate_limits.clear()
    client = TestClient(app)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@platform.vraja", "password": "SecAdmGatePass987!", "tenant_id": "default_business"},
        headers={"Origin": "http://localhost:5173"}
    )
    token = login_res.cookies[OWNER_COOKIE]

    monkeypatch.setenv("MOCK_EMAIL_TRANSPORT", "false")
    monkeypatch.setenv("ALLOW_LIVE_SMTP_TEST", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.delenv("PAUSE_INCIDENT_DISPATCH", raising=False)

    res = client.post(
        "/api/platform/security-shield/test-alert",
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"},
        json={"scenario": "test_unpaused"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REJECTED_INCIDENT_DISPATCH_NOT_PAUSED"
    assert "PAUSE_INCIDENT_DISPATCH=true" in data["message"]


def test_negative_2_missing_allow_live_smtp_test_blocks_sending(staging_gate_env, monkeypatch):
    """Missing ALLOW_LIVE_SMTP_TEST blocks live outbound transmission."""
    from Backend.app.api.service import review_service
    review_service._rate_limits.clear()
    client = TestClient(app)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@platform.vraja", "password": "SecAdmGatePass987!", "tenant_id": "default_business"},
        headers={"Origin": "http://localhost:5173"}
    )
    token = login_res.cookies[OWNER_COOKIE]

    monkeypatch.setenv("MOCK_EMAIL_TRANSPORT", "false")
    monkeypatch.setenv("PAUSE_INCIDENT_DISPATCH", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.delenv("ALLOW_LIVE_SMTP_TEST", raising=False)

    res = client.post(
        "/api/platform/security-shield/test-alert",
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"},
        json={"scenario": "test_no_flag"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REJECTED_MISSING_LIVE_FLAG"


def test_negative_3_missing_smtp_credentials_prevents_sending(staging_gate_env, monkeypatch):
    """Missing SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) prevents sending."""
    from Backend.app.api.service import review_service
    review_service._rate_limits.clear()
    client = TestClient(app)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@platform.vraja", "password": "SecAdmGatePass987!", "tenant_id": "default_business"},
        headers={"Origin": "http://localhost:5173"}
    )
    token = login_res.cookies[OWNER_COOKIE]

    monkeypatch.setenv("MOCK_EMAIL_TRANSPORT", "false")
    monkeypatch.setenv("PAUSE_INCIDENT_DISPATCH", "true")
    monkeypatch.setenv("ALLOW_LIVE_SMTP_TEST", "true")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    res = client.post(
        "/api/platform/security-shield/test-alert",
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"},
        json={"scenario": "test_no_creds"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "NOT CONFIGURED"


def test_negative_4_pending_regular_incident_emails_untouched(staging_gate_env):
    """Pending regular incident emails remain untouched when synthetic tests run."""
    sec_store = staging_gate_env["sec_store"]
    sec_store.queue_alert("inc_01", "dev@vraja.ai", "Subject 1", "Body", "<p>Body</p>", "HIGH")
    sec_store.queue_alert("inc_02", "dev@vraja.ai", "Subject 2", "Body", "<p>Body</p>", "LOW")
    before, count_before = sec_store.list_outbox()

    mailer = AlertMailer()
    res = mailer.send_synthetic_test_alert(initiated_by="admin@platform.vraja", store=sec_store)
    assert res["is_synthetic"] is True

    after, count_after = sec_store.list_outbox()
    assert count_before == count_after
    assert [x["id"] for x in before] == [x["id"] for x in after]
    assert [x["status"] for x in after] == ["pending", "pending"]


def test_negative_5_historical_synthetic_tests_cannot_unexpectedly_dispatch(staging_gate_env, monkeypatch):
    """Queued historical tests cannot dispatch when live authorization flag is not present."""
    sec_store = staging_gate_env["sec_store"]
    monkeypatch.delenv("ALLOW_LIVE_SMTP_TEST", raising=False)

    sec_store.record_synthetic_test(
        test_id="syn_old_01",
        recipient=DEFAULT_ALERT_EMAIL,
        subject="Old Test",
        body_text="Body",
        body_html="<p>Body</p>",
        status="queued",
        initiated_by="admin@platform.vraja"
    )

    mailer = AlertMailer()
    res = mailer.process_synthetic_tests(sec_store)
    rec = sec_store.get_synthetic_test("syn_old_01")
    assert rec["status"] in ("cancelled_missing_live_flag", "not_configured")


def test_negative_6_expired_synthetic_tests_remain_expired(staging_gate_env):
    """Expired synthetic tests (>300s TTL) cannot be resurrected or dispatched."""
    sec_store = staging_gate_env["sec_store"]
    now = time.time()
    sec_store.record_synthetic_test(
        test_id="syn_ttl_01",
        recipient=DEFAULT_ALERT_EMAIL,
        subject="Stale Test",
        body_text="Body",
        body_html="<p>Body</p>",
        status="queued",
        initiated_by="admin@platform.vraja"
    )
    with sec_store._connect() as conn:
        conn.execute("UPDATE security_synthetic_tests SET created_at = ? WHERE test_id = ?", (now - 350.0, "syn_ttl_01"))

    mailer = AlertMailer()
    mailer.process_synthetic_tests(sec_store, ttl_seconds=300.0)
    rec1 = sec_store.get_synthetic_test("syn_ttl_01")
    assert rec1["status"] == "expired"

    # Attempting worker pass again does not alter its expired status
    mailer.process_synthetic_tests(sec_store, ttl_seconds=300.0)
    rec2 = sec_store.get_synthetic_test("syn_ttl_01")
    assert rec2["status"] == "expired"


def test_negative_7_unauthenticated_and_tenant_owner_rejected(staging_gate_env):
    """Anonymous (401) and non-admin tenant owner (403) requests are strictly rejected."""
    from Backend.app.api.service import review_service
    review_service._rate_limits.clear()
    client = TestClient(app)

    # 1. Anonymous request
    r_anon = client.post("/api/platform/security-shield/test-alert")
    assert r_anon.status_code == 401

    # 2. Login as non-admin tenant owner
    login_own = client.post(
        "/api/auth/login",
        json={"email": "owner@cafe.com", "password": "SecOwnGatePass456!", "tenant_id": "default_business"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert login_own.status_code == 200
    token_own = login_own.cookies[OWNER_COOKIE]

    # 3. Non-admin request rejected
    r_own = client.post(
        "/api/platform/security-shield/test-alert",
        cookies={OWNER_COOKIE: token_own},
        headers={"Origin": "http://localhost:5173"}
    )
    assert r_own.status_code == 403


def test_negative_8_staging_databases_cannot_resolve_to_production():
    """Attempting to initialize ReviewStore or SecurityStore pointing to production in test mode raises RuntimeError."""
    from Backend.app.core.security.security_store import DEFAULT_SECURITY_DB

    relative_prod_path = Path("Project_Files/Data/nasta-ghar/reviews.sqlite3")
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        ReviewStore(database_path=str(relative_prod_path))

    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        SecurityStore(db_path=str(DEFAULT_SECURITY_DB))
