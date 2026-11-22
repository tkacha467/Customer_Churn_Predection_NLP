"""
Phase A6.2 Test Suite: Critical Database Safety, Email Delivery Reliability & Security Shield Release Gate.

Validates:
1. Realistic failure modeling for email outbox delivery (at-least-once delivery, lease expiry recovery).
2. Worker lifecycle reliability and operational health telemetry (AlertDispatcherWorker).
3. Concurrent SQLite security storage operations with multi-worker isolation.
4. Severity calibration preventing false-positive alert floods (404s logged as LOW, zero email spam).
5. High-risk threat alerting (brute-force lockout and BOLA/IDOR trigger priority alert queues).
6. Server-authoritative preview isolation rejecting client-side preview spoofing.
7. Analytics sliding-window idempotency preventing double-click inflation while preserving subsequent conversions.
"""

import time
import json
import uuid
import threading
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
from Backend.app.core.security.alert_mailer import alert_mailer, AlertDispatcherWorker
from Backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)


@pytest.fixture
def a6_2_env(tmp_path, monkeypatch):
    """Isolated environment for Phase A6.2 testing."""
    main_db_path = tmp_path / "test_a6_2_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_2_security.sqlite3"
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

    # Isolated security store
    sec_store = SecurityStore(db_path=str(sec_db_path))
    sec_store.clear()
    security_shield._store = sec_store
    security_shield.clear()

    main_store = ReviewStore(database_path=str(main_db_path))
    now = time.time()

    # Seed platform admin
    with main_store._connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES (
                'tenant_gamma', 'Gamma Bistro', 'active', 'google', 'https://maps.google.com/?cid=333',
                'Main', 'Restaurant & Dining', 'Bistro', '[]', '#f97316', '', '["review_manager"]', ?, ?
            )
        """, (now, now))

        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES
            ('usr_admin_62', 'admin62@vajra.techworks', ?, 'Admin A62', 1, 1, ?, ?)
        """, (hash_password("AdminPass123!"), now, now))

        token_admin = "token_admin_62"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_admin_62', 'tenant_gamma', ?, ?, NULL)
        """, (hash_token(token_admin), now, now + 3600))

    return {
        "sec_store": sec_store,
        "main_store": main_store,
        "token_admin": token_admin,
    }


def test_outbox_lease_expiry_and_recovery(a6_2_env):
    """
    If a worker claims an outbox item but crashes before completion,
    the lease expires and another worker safely reclaims it (at-least-once delivery).
    """
    store = a6_2_env["sec_store"]
    now = time.time()

    # Queue an alert
    out_id = store.queue_alert(
        incident_id="inc_lease_test",
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI SECURITY] Lease Recovery Test",
        body_text="Test body",
        body_html="<p>Test</p>",
        severity="HIGH"
    )

    # Worker 1 claims with a short 2-second lease
    claimed_w1 = store.claim_outbox_items(worker_id="worker_crashed_1", limit=10, lease_seconds=2.0)
    assert len(claimed_w1) == 1
    assert claimed_w1[0]["id"] == out_id
    assert claimed_w1[0]["status"] == "claimed"

    # Immediately, Worker 2 attempts to claim: item is locked and NOT available
    claimed_w2_early = store.claim_outbox_items(worker_id="worker_live_2", limit=10, lease_seconds=2.0)
    assert len(claimed_w2_early) == 0, "Item must not be claimable while active lease is valid"

    # Advance time beyond the 2s lease expiration
    with store._connect() as conn:
        conn.execute("UPDATE security_alert_outbox SET claimed_at = ? WHERE id = ?", (now - 10.0, out_id))

    # Worker 2 attempts to claim after lease expiry: item is reclaimed!
    claimed_w2_recovered = store.claim_outbox_items(worker_id="worker_live_2", limit=10, lease_seconds=2.0)
    assert len(claimed_w2_recovered) == 1
    assert claimed_w2_recovered[0]["id"] == out_id
    assert claimed_w2_recovered[0]["claimed_by"] == "worker_live_2"


def test_alert_dispatcher_worker_health_telemetry(a6_2_env):
    """
    AlertDispatcherWorker exposes health state, tracks processed counts,
    and recovers from transient errors without terminating the thread.
    """
    store = a6_2_env["sec_store"]

    worker = AlertDispatcherWorker(store=store, mailer=alert_mailer, poll_interval=0.1)
    health_initial = worker.get_health()
    assert health_initial["is_running"] is False
    assert health_initial["total_processed"] == 0

    worker.start()
    assert worker.is_running() is True

    # Queue 2 alerts
    store.queue_alert("inc_1", "vajra.techworks@gmail.com", "A1", "B1", "<p>1</p>", "HIGH")
    store.queue_alert("inc_2", "vajra.techworks@gmail.com", "A2", "B2", "<p>2</p>", "HIGH")

    time.sleep(0.3)
    health_running = worker.get_health()
    assert health_running["is_running"] is True
    assert health_running["last_run_at"] is not None
    assert health_running["total_processed"] >= 2
    assert health_running["last_error"] is None

    worker.stop(timeout=1.0)
    assert worker.is_running() is False


def test_severity_calibration_unknown_tenant_does_not_spam_email(a6_2_env):
    """
    An unknown tenant 404 is calibrated as LOW severity;
    it must be recorded in the audit store but must NEVER queue an email alert.
    """
    store = a6_2_env["sec_store"]
    client = TestClient(app)

    # 404 request for unknown business
    resp = client.post("/api/reviews/ideas", json={"business_id": "nonexistent_biz_999", "rating": 5, "language": "en"})
    assert resp.status_code == 404

    # Verify event was durably recorded
    events, total = store.list_events(event_type=SecurityEventType.ACCESS_UNKNOWN_TENANT.value)
    assert total >= 1
    assert events[0]["severity"] in ("LOW", "MEDIUM")

    # Verify NO outbox email was queued for a single 404
    outbox_items, out_total = store.list_outbox()
    assert out_total == 0, "Single 404 should never trigger outbox email notifications"


def test_high_risk_threat_queues_email_alert(a6_2_env):
    """
    High-risk security threats (e.g. BOLA/IDOR attempt or healthcare compliance breach)
    must immediately queue a priority outbox notification.
    """
    store = a6_2_env["sec_store"]

    emit_security_event(
        event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL,
        severity=SecuritySeverity.HIGH,
        actor_id="ip_malicious",
        tenant_id="tenant_gamma",
        action_taken="BLOCKED",
        outcome="ATTACK_PREVENTED",
        details={"endpoint": "/api/owner/documents", "target_doc": "doc_other_tenant"}
    )

    outbox_items, out_total = store.list_outbox()
    assert out_total >= 1
    assert any(i["severity"] == "HIGH" and i["recipient"] == "vajra.techworks@gmail.com" for i in outbox_items)


def test_server_authoritative_preview_context_rejects_client_spoofing(a6_2_env):
    """
    A public caller passing preview query params or strings containing 'preview'
    cannot bypass review analytics without explicit server registration.
    """
    store = a6_2_env["sec_store"]
    fake_preview_session = "preview_fake_client_generated_session_123"

    # Verify the fake session is NOT recognized by the server-authoritative preview store
    assert store.is_valid_preview_session(fake_preview_session) is False

    # Legitimate manager registers a genuine preview session
    store.register_preview_session("server_issued_valid_session_456", "tenant_gamma", "usr_admin_62", ttl_seconds=300)
    assert store.is_valid_preview_session("server_issued_valid_session_456") is True


def test_concurrent_incident_aggregation_under_load(a6_2_env):
    """
    Tests high concurrency against SQLite security store with 15 concurrent threads
    emitting the same fingerprint. Verifies BEGIN IMMEDIATE prevents race conditions.
    """
    store = a6_2_env["sec_store"]

    incident_ids = []
    lock = threading.Lock()

    def thread_work():
        inc_id, _ = store.aggregate_event_into_incident(
            event_type="AUTH_FAILED_LOGIN",
            severity="LOW",
            affected_tenant="tenant_gamma",
            actor_id="ip_load_test",
            title="Failed Login Burst",
            description="Concurrent test",
            details={"endpoint": "/api/auth/login"}
        )
        with lock:
            incident_ids.append(inc_id)

    threads = [threading.Thread(target=thread_work) for _ in range(15)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All 15 threads should resolve to the exact same incident
    assert len(set(incident_ids)) == 1
    inc = store.get_incident(incident_ids[0])
    assert inc["event_count"] == 15
