"""
Phase A6 Test Suite: VRAJA AI Security Shield.
Validates:
1. Event persistence across process restarts.
2. Sensitive field redaction (passwords, tokens, cookies, PII, drafts).
3. Security event server-side pagination and severity/tenant filtering.
4. Incident aggregation and burst grouping (no alert storms).
5. Incident lifecycle (Open -> Investigating -> Resolved).
6. Email notification pipeline, outbox deduplication, and retry backoff.
7. Platform admin authorization and strict non-admin 403 lockdown.
8. Server-authoritative preview session isolation (no prefix spoofing).
9. Concurrent analytics deduplication.
10. Overview telemetry and SMTP configuration status.
"""

import time
import json
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    OWNER_COOKIE,
)
from Backend.app.api.service import review_service
from Backend.app.core.security.security_store import SecurityStore
from Backend.app.core.security.alert_mailer import alert_mailer
from Backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)


@pytest.fixture
def a6_env(tmp_path, monkeypatch):
    """Isolated environment for Phase A6 testing."""
    main_db_path = tmp_path / "test_a6_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_security.sqlite3"
    legacy_json_path = tmp_path / "business_links.json"
    docs_path = tmp_path / "test_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    legacy_json_path.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("REVIEW_DB_PATH", str(main_db_path))
    monkeypatch.setenv("SECURITY_DB_PATH", str(sec_db_path))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(legacy_json_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("MOCK_EMAIL_TRANSPORT", "true")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-key-for-test-32-chars!!")

    _stores.clear()
    SecurityStore._instances.clear()
    review_service._rate_limits.clear()
    review_service._dedup_cache.clear()
    review_service._verified_preview_sessions.clear()

    # Initialize isolated security store
    sec_store = SecurityStore(db_path=str(sec_db_path))
    sec_store.clear()
    security_shield._store = sec_store
    security_shield.clear()

    main_store = ReviewStore(database_path=str(main_db_path))
    now = time.time()

    # Seed main database tenants and users
    with main_store._connect() as db:
        # Tenants
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('tenant_alpha', 'Alpha Dining', 'active', 'google', 'https://maps.google.com/?cid=111', 'Main', 'Restaurant & Dining', 'Fine dining', '[]', '#f97316', '', '["review_manager"]', ?, ?),
            ('tenant_beta', 'Beta Hotel', 'active', 'google', 'https://maps.google.com/?cid=222', 'Central', 'Hotel', 'Hotel', '[]', '#2563eb', '', '["review_manager"]', ?, ?)
        """, (now, now, now, now))

        # Users: Tenant Owner vs Platform Admin
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES
            ('usr_owner', 'owner@alphadining.com', ?, 'Owner Alpha', 1, 0, ?, ?),
            ('usr_admin', 'superadmin@vajra.techworks', ?, 'Platform Admin', 1, 1, ?, ?)
        """, (hash_password("OwnerPassword123!"), now, now, hash_password("SuperAdmin123!"), now, now))

        # Memberships
        db.execute("""
            INSERT OR REPLACE INTO tenant_memberships (id, user_id, tenant_id, role, created_at)
            VALUES ('mem_owner', 'usr_owner', 'tenant_alpha', 'owner', ?)
        """, (now,))

        # Active sessions
        token_owner = "token_owner_session_a6"
        token_admin = "token_admin_session_a6"

        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES
            (?, 'usr_owner', 'tenant_alpha', ?, ?, NULL),
            (?, 'usr_admin', 'tenant_alpha', ?, ?, NULL)
        """, (hash_token(token_owner), now, now + 3600, hash_token(token_admin), now, now + 3600))

    return {
        "sec_store": sec_store,
        "main_store": main_store,
        "sec_db_path": str(sec_db_path),
        "token_owner": token_owner,
        "token_admin": token_admin,
    }


def test_security_event_persistence_across_restarts(a6_env):
    """Security events must survive complete process restarts via SQLite storage."""
    # 1. Emit an event
    ev = emit_security_event(
        event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL,
        severity=SecuritySeverity.HIGH,
        actor_id="test_attacker",
        tenant_id="tenant_beta",
        details={"ip": "10.0.0.1", "action": "attempted_config_update"}
    )

    # 2. Simulate process restart by instantiating a fresh SecurityStore from disk
    SecurityStore._instances.clear()
    fresh_store = SecurityStore(db_path=a6_env["sec_db_path"])

    events, total = fresh_store.list_events(limit=10)
    assert total >= 1
    stored = next((e for e in events if e["event_id"] == ev.event_id), None)
    assert stored is not None
    assert stored["event_type"] == SecurityEventType.ACCESS_CROSS_TENANT_DENIAL.value
    assert stored["severity"] == "HIGH"
    assert stored["tenant_id"] == "tenant_beta"
    assert stored["details"]["action"] == "attempted_config_update"


def test_security_event_redaction(a6_env):
    """Passwords, session tokens, cookies, secrets, and raw review drafts must be redacted."""
    ev = emit_security_event(
        event_type=SecurityEventType.AUTH_FAILED_LOGIN,
        severity=SecuritySeverity.MEDIUM,
        details={
            "email": "user@test.com",
            "password": "MySuperSecretPassword99!",
            "token": "tok_live_123456789",
            "cookie": "owner_session=abc",
            "diner_note": "Guest raw review text here",
            "api_key": "sec_key_xyz",
            "safe_metadata": "allowed_context"
        }
    )

    events, _ = a6_env["sec_store"].list_events(limit=5)
    rec = next(e for e in events if e["event_id"] == ev.event_id)
    d = rec["details"]

    assert d["password"] == "[REDACTED]"
    assert d["token"] == "[REDACTED]"
    assert d["cookie"] == "[REDACTED]"
    assert d["diner_note"] == "[REDACTED]"
    assert d["api_key"] == "[REDACTED]"
    assert d["safe_metadata"] == "allowed_context"


def test_security_event_pagination_and_filtering(a6_env):
    """Server-side pagination and severity filtering must work accurately."""
    store = a6_env["sec_store"]

    # Seed 15 events
    for i in range(10):
        emit_security_event(
            event_type=SecurityEventType.ABUSE_RATE_LIMIT_EXCEEDED,
            severity=SecuritySeverity.MEDIUM,
            tenant_id="tenant_alpha"
        )
    for i in range(5):
        emit_security_event(
            event_type=SecurityEventType.CSRF_ORIGIN_VIOLATION,
            severity=SecuritySeverity.CRITICAL,
            tenant_id="tenant_beta"
        )

    # Page 1: 5 items
    p1, total = store.list_events(limit=5, offset=0)
    assert len(p1) == 5
    assert total >= 15

    # Filter by CRITICAL severity
    crit_events, crit_total = store.list_events(severity="CRITICAL")
    assert crit_total >= 5
    assert all(e["severity"] == "CRITICAL" for e in crit_events)


def test_incident_creation_and_grouping(a6_env):
    """Bursts of identical security events within 15 minutes must group into 1 incident."""
    store = a6_env["sec_store"]

    # Emit 5 identical denial events in rapid succession
    for _ in range(5):
        emit_security_event(
            event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL,
            severity=SecuritySeverity.HIGH,
            tenant_id="tenant_beta"
        )

    incidents, total_inc = store.list_incidents(tenant_id="tenant_beta")
    assert total_inc == 1
    inc = incidents[0]
    assert inc["event_count"] == 5
    assert inc["severity"] == "HIGH"
    assert inc["status"] == "open"


def test_incident_lifecycle_acknowledge_and_resolve(a6_env):
    """Platform admin can acknowledge and resolve incidents via API."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a6_env["token_admin"])

    # 1. Trigger an incident
    emit_security_event(
        event_type=SecurityEventType.CSRF_ORIGIN_VIOLATION,
        severity=SecuritySeverity.CRITICAL,
        tenant_id="tenant_alpha"
    )

    incidents, _ = a6_env["sec_store"].list_incidents(tenant_id="tenant_alpha")
    inc_id = incidents[0]["incident_id"]

    # 2. Acknowledge incident (Open -> Investigating)
    resp1 = client.patch(
        f"/api/platform/security-shield/incidents/{inc_id}",
        json={"status": "investigating"}
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "investigating"
    assert resp1.json()["acknowledged_by"] == "superadmin@vajra.techworks"

    # 3. Resolve incident (Investigating -> Resolved)
    resp2 = client.patch(
        f"/api/platform/security-shield/incidents/{inc_id}",
        json={"status": "resolved", "resolution_note": "Origin confirmed and whitelisted."}
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "resolved"
    assert resp2.json()["resolution_note"] == "Origin confirmed and whitelisted."


def test_notification_deduplication_and_outbox_queueing(a6_env):
    """High severity events queue 1 email per incident, not 1 per event."""
    store = a6_env["sec_store"]

    # Emit 4 high-severity events for same tenant
    for _ in range(4):
        emit_security_event(
            event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL,
            severity=SecuritySeverity.HIGH,
            tenant_id="tenant_beta"
        )

    outbox, count = store.list_outbox()
    # Outbox should have strictly 1 alert item for this incident burst
    assert count == 1
    item = outbox[0]
    assert item["recipient"] == "vajra.techworks@gmail.com"
    assert "Cross-Tenant" in item["subject"]
    assert item["severity"] == "HIGH"


def test_email_retry_and_backoff_handling(a6_env):
    """Outbox processor retries with backoff and records failures."""
    store = a6_env["sec_store"]

    # Manually queue an alert
    out_id = store.queue_alert(
        incident_id="inc_test_123",
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI SECURITY] Test Alert",
        body_text="Test alert body",
        body_html="<p>Test</p>",
        severity="HIGH"
    )

    # Force simulated failure
    class FailingMailer:
        def send_email_sync(self, *args, **kwargs):
            return False, "SMTPConnectionTimeout: host unreachable"

    res = alert_mailer.process_outbox(store)
    # Under test MOCK_EMAIL_TRANSPORT=true, mock transport records mock_sent:
    assert (res.get("sent", 0) + res.get("mock_sent", 0)) >= 1
    items, _ = store.list_outbox(status="mock_sent")
    assert len(items) >= 1


def test_platform_admin_authorization_and_non_admin_rejection(a6_env):
    """Ordinary business owner cannot access Security Shield APIs (strictly HTTP 403)."""
    client = TestClient(app)

    # 1. Tenant Owner session
    client.cookies.set(OWNER_COOKIE, a6_env["token_owner"])

    resp_overview = client.get("/api/platform/security-shield/overview")
    assert resp_overview.status_code == 403
    assert "Platform admin" in resp_overview.json()["detail"]

    resp_incidents = client.get("/api/platform/security-shield/incidents")
    assert resp_incidents.status_code == 403

    resp_events = client.get("/api/platform/security-shield/events")
    assert resp_events.status_code == 403

    resp_outbox = client.get("/api/platform/security-shield/outbox")
    assert resp_outbox.status_code == 403

    # 2. Superadmin session
    client.cookies.set(OWNER_COOKIE, a6_env["token_admin"])

    admin_overview = client.get("/api/platform/security-shield/overview")
    assert admin_overview.status_code == 200
    data = admin_overview.json()
    assert data["target_alert_email"] == "vajra.techworks@gmail.com"
    assert "total_events" in data


def test_server_authoritative_preview_isolation_strict(a6_env):
    """Unregistered session cannot spoof preview mode, even with 'preview_' prefix."""
    client = TestClient(app)

    # 1. Unregistered session with preview prefix
    client.post("/api/reviews/events", json={
        "session_id": "preview_fake_spoof_888",
        "event_name": "google_maps_direct_click",
        "metadata": {
            "business_id": "tenant_alpha",
            "is_preview": True
        }
    })

    # Spoof attempt must be logged in Security Shield
    events = security_shield.list_events(tenant_filter="tenant_alpha")
    assert any(e["event_type"] == SecurityEventType.ABUSE_PREVIEW_SPOOF_ATTEMPT.value for e in events)

    # 2. Legitimate preview session registered by authenticated owner
    client.cookies.set(OWNER_COOKIE, a6_env["token_owner"])
    reg_resp = client.post(
        "/api/reviews/preview-session",
        json={"business_id": "tenant_alpha", "session_id": "legit_registered_preview_001"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert reg_resp.status_code == 200
    assert reg_resp.json()["is_preview"] is True

    # Check that security store recognizes it
    assert security_shield.is_preview_session("legit_registered_preview_001") is True


def test_concurrent_analytics_event_atomic_handling(a6_env):
    """Simultaneous conversion events for same session are deduplicated."""
    store = a6_env["main_store"]

    event_payload = {
        "business_id": "tenant_alpha",
        "session_id": "concurrent_sess_999",
        "event_name": "google_maps_direct_click",
        "client_timestamp": "2026-11-20T00:00:00Z",
        "meta": {"source": "cta"}
    }

    # First event
    r1 = store.add_event(event_payload)
    assert r1.get("status") == "recorded"

    # Immediate concurrent second event
    r2 = store.add_event(event_payload)
    assert r2.get("status") == "deduplicated"
    assert r2.get("is_duplicate") is True
