"""
Phase A6.1 Test Suite: Security Shield Reliability, Concurrency & Live Alert Readiness.

Validates:
1. Multi-dimensional incident fingerprinting (endpoint/tenant/actor isolation).
2. Resolved incidents never swallow new attacks.
3. Concurrent outbox claiming (zero duplicate deliveries across workers).
4. Concurrent incident creation with BEGIN IMMEDIATE (zero duplicate incidents).
5. Retention pruning safety (open/investigating incidents are NEVER deleted).
6. Request execution decoupling (zero synchronous SMTP blocking in request thread).
7. AlertDispatcherWorker background worker lifecycle and dispatching.
8. Outbox retry backoff and dead-lettering after 3 failed attempts.
9. Platform admin rate limiting on manual outbox retry and export.
10. Incident status mutation audit trail emission.
11. Analytics idempotency validation (short sliding window vs flawed static index).
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
def a6_1_env(tmp_path, monkeypatch):
    """Isolated environment for Phase A6.1 reliability testing."""
    main_db_path = tmp_path / "test_a6_1_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_1_security.sqlite3"
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

    # Seed main database tenant, users and sessions
    with main_store._connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES (
                'tenant_alpha', 'Alpha Dining', 'active', 'google', 'https://maps.google.com/?cid=111',
                'Main', 'Restaurant & Dining', 'Fine dining', '[]', '#f97316', '', '["review_manager"]', ?, ?
            )
        """, (now, now))

        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES
            ('usr_admin_61', 'admin61@vajra.techworks', ?, 'Admin A61', 1, 1, ?, ?)
        """, (hash_password("AdminPass123!"), now, now))

        token_admin = "token_admin_61"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_admin_61', 'tenant_alpha', ?, ?, NULL)
        """, (hash_token(token_admin), now, now + 3600))

    return {
        "sec_store": sec_store,
        "main_store": main_store,
        "token_admin": token_admin,
    }


def test_multidimensional_incident_fingerprinting(a6_1_env):
    """
    Events with the same event_type but different endpoints or tenants
    must generate distinct incidents and not collide.
    """
    store = a6_1_env["sec_store"]

    # Attack on login endpoint
    inc_id1, is_new1 = store.aggregate_event_into_incident(
        event_type="AUTH_BRUTE_FORCE_LOCKOUT",
        severity="HIGH",
        affected_tenant="tenant_alpha",
        actor_id="ip_1.1.1.1",
        title="Brute Force Login",
        description="Login attack",
        details={"endpoint": "/api/auth/login"}
    )
    assert is_new1 is True

    # Same event type, same tenant, but different endpoint
    inc_id2, is_new2 = store.aggregate_event_into_incident(
        event_type="AUTH_BRUTE_FORCE_LOCKOUT",
        severity="HIGH",
        affected_tenant="tenant_alpha",
        actor_id="ip_1.1.1.1",
        title="Brute Force API",
        description="API attack",
        details={"endpoint": "/api/reviews/generate"}
    )
    assert is_new2 is True
    assert inc_id1 != inc_id2, "Different endpoints must create separate incidents"

    # Repeat on first endpoint -> groups into inc_id1
    inc_id3, is_new3 = store.aggregate_event_into_incident(
        event_type="AUTH_BRUTE_FORCE_LOCKOUT",
        severity="HIGH",
        affected_tenant="tenant_alpha",
        actor_id="ip_1.1.1.1",
        title="Brute Force Login Repeat",
        description="Login attack repeat",
        details={"endpoint": "/api/auth/login"}
    )
    assert is_new3 is False
    assert inc_id3 == inc_id1

    inc1 = store.get_incident(inc_id1)
    assert inc1["event_count"] == 2


def test_resolved_incidents_never_swallow_new_attacks(a6_1_env):
    """
    Once an incident is resolved, subsequent attacks must open a brand new incident.
    """
    store = a6_1_env["sec_store"]

    inc_id1, is_new1 = store.aggregate_event_into_incident(
        event_type="AI_INJECTION_NEUTRALIZED",
        severity="HIGH",
        affected_tenant="tenant_alpha",
        actor_id="ip_attacker",
        title="Prompt Injection",
        description="Attempt 1",
        details={"endpoint": "/api/reviews/generate"}
    )
    assert is_new1 is True

    # Mark as resolved
    store.update_incident(inc_id1, status="resolved", resolution_note="Firewall rule deployed")
    resolved_inc = store.get_incident(inc_id1)
    assert resolved_inc["status"] == "resolved"

    # New attack with identical fingerprint
    inc_id2, is_new2 = store.aggregate_event_into_incident(
        event_type="AI_INJECTION_NEUTRALIZED",
        severity="HIGH",
        affected_tenant="tenant_alpha",
        actor_id="ip_attacker",
        title="Prompt Injection Re-attempt",
        description="Attempt 2",
        details={"endpoint": "/api/reviews/generate"}
    )
    assert is_new2 is True, "New attack after resolution must open a new incident"
    assert inc_id2 != inc_id1


def test_concurrent_outbox_claiming_zero_duplicates(a6_1_env):
    """
    Multiple workers concurrently claiming outbox items must never double-claim
    the same item. Each item must be leased exactly once.
    """
    store = a6_1_env["sec_store"]

    # Queue 20 alerts
    item_ids = []
    for i in range(20):
        o_id = store.queue_alert(
            incident_id=f"inc_{i}",
            recipient="vajra.techworks@gmail.com",
            subject=f"Alert {i}",
            body_text=f"Body {i}",
            body_html=f"<p>{i}</p>",
            severity="HIGH"
        )
        item_ids.append(o_id)

    claimed_by_worker = {}
    lock = threading.Lock()

    def worker_claim_task(worker_name: str):
        claims = store.claim_outbox_items(worker_id=worker_name, limit=10, lease_seconds=300.0)
        with lock:
            claimed_by_worker[worker_name] = [item["id"] for item in claims]

    threads = []
    for w in range(5):
        t = threading.Thread(target=worker_claim_task, args=(f"worker_{w}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Aggregate all claimed IDs
    all_claimed = []
    for worker_name, ids in claimed_by_worker.items():
        all_claimed.extend(ids)

    # Verify zero duplicates across workers
    assert len(all_claimed) == len(set(all_claimed)), "Outbox items were double-claimed across workers!"
    assert len(all_claimed) == 20, f"Expected 20 claimed items, got {len(all_claimed)}"


def test_concurrent_incident_creation_begin_immediate(a6_1_env):
    """
    Concurrent event aggregation with BEGIN IMMEDIATE must never create duplicate
    open incidents for the same attack fingerprint.
    """
    store = a6_1_env["sec_store"]

    created_ids = []
    lock = threading.Lock()

    def burst_task():
        inc_id, _ = store.aggregate_event_into_incident(
            event_type="ABUSE_RATE_LIMIT_EXCEEDED",
            severity="MEDIUM",
            affected_tenant="tenant_concurrent",
            actor_id="ip_spammer",
            title="Spam Burst",
            description="Concurrent flood",
            details={"endpoint": "/api/predict"}
        )
        with lock:
            created_ids.append(inc_id)

    threads = [threading.Thread(target=burst_task) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one incident should be created, all threads returning the same ID
    unique_inc_ids = set(created_ids)
    assert len(unique_inc_ids) == 1, f"Concurrent race created multiple incidents: {unique_inc_ids}"

    single_id = created_ids[0]
    inc = store.get_incident(single_id)
    assert inc["event_count"] == 10


def test_retention_pruning_safety_unresolved_never_deleted(a6_1_env):
    """
    prune_retention must NEVER delete open or investigating incidents,
    even if their first_observed_at is ancient. Only resolved incidents
    older than 180 days are pruned.
    """
    store = a6_1_env["sec_store"]
    now = time.time()
    ancient_ts = now - (365 * 86400.0)  # 1 year ago

    with store._connect() as conn:
        # 1. Ancient open incident
        conn.execute("""
            INSERT INTO security_incidents (
                incident_id, event_type, severity, title, description,
                affected_tenant, status, event_count, first_observed_at, last_observed_at
            ) VALUES ('inc_open_ancient', 'AUTH_FAILED', 'HIGH', 'Old Open', 'Desc', 't1', 'open', 5, ?, ?)
        """, (ancient_ts, ancient_ts))

        # 2. Ancient investigating incident
        conn.execute("""
            INSERT INTO security_incidents (
                incident_id, event_type, severity, title, description,
                affected_tenant, status, event_count, first_observed_at, last_observed_at
            ) VALUES ('inc_inv_ancient', 'AUTH_FAILED', 'HIGH', 'Old Inv', 'Desc', 't1', 'investigating', 5, ?, ?)
        """, (ancient_ts, ancient_ts))

        # 3. Ancient resolved incident (resolved 200 days ago)
        conn.execute("""
            INSERT INTO security_incidents (
                incident_id, event_type, severity, title, description,
                affected_tenant, status, event_count, first_observed_at, last_observed_at,
                resolved_at
            ) VALUES ('inc_res_ancient', 'AUTH_FAILED', 'LOW', 'Old Res', 'Desc', 't1', 'resolved', 1, ?, ?, ?)
        """, (ancient_ts, ancient_ts, now - (200 * 86400.0)))

        # 4. Recently resolved incident (resolved 10 days ago)
        conn.execute("""
            INSERT INTO security_incidents (
                incident_id, event_type, severity, title, description,
                affected_tenant, status, event_count, first_observed_at, last_observed_at,
                resolved_at
            ) VALUES ('inc_res_recent', 'AUTH_FAILED', 'LOW', 'Recent Res', 'Desc', 't1', 'resolved', 1, ?, ?, ?)
        """, (now - 86400.0, now - 86400.0, now - (10 * 86400.0)))

    # Run pruning
    stats = store.prune_retention(retention_days=30)
    assert stats["incidents_pruned"] == 1, "Only the 200-day-old resolved incident should be pruned"

    # Verify active incidents are preserved
    assert store.get_incident("inc_open_ancient") is not None, "Open incident must NOT be pruned"
    assert store.get_incident("inc_inv_ancient") is not None, "Investigating incident must NOT be pruned"
    assert store.get_incident("inc_res_recent") is not None, "Recent resolved incident must NOT be pruned"
    assert store.get_incident("inc_res_ancient") is None, "Ancient resolved incident must be pruned"


def test_request_execution_decoupling_from_smtp(a6_1_env):
    """
    Emitting a critical security event must queue the email into the SQLite outbox
    without executing synchronous SMTP calls during the request thread.
    """
    store = a6_1_env["sec_store"]

    rec = emit_security_event(
        event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL,
        severity=SecuritySeverity.CRITICAL,
        actor_id="ip_blocked_request",
        tenant_id="tenant_alpha",
        action_taken="BLOCKED",
        outcome="ATTACK_PREVENTED",
        details={"endpoint": "/api/businesses/tenant_beta/reviews"}
    )

    # Event is durably stored
    events, total = store.list_events(event_type=SecurityEventType.ACCESS_CROSS_TENANT_DENIAL.value)
    assert total >= 1

    # Outbox item is queued with status 'pending' (decoupled from SMTP network call)
    outbox_items, out_total = store.list_outbox(status="pending")
    assert out_total >= 1
    assert any(item["recipient"] == "vajra.techworks@gmail.com" for item in outbox_items)


def test_alert_dispatcher_worker_lifecycle_and_dispatch(a6_1_env):
    """
    AlertDispatcherWorker background daemon polls and delivers outbox alerts,
    marking items as mock_sent (or sent).
    """
    store = a6_1_env["sec_store"]

    # Queue an alert
    store.queue_alert(
        incident_id="inc_worker_test",
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI SECURITY] Worker Test",
        body_text="Worker body",
        body_html="<p>Worker</p>",
        severity="HIGH"
    )

    # Start background dispatcher worker
    worker = AlertDispatcherWorker(store=store, mailer=alert_mailer, poll_interval=0.1)
    worker.start()
    assert worker.is_running() is True

    # Allow worker to process
    time.sleep(0.4)
    worker.stop(timeout=1.0)
    assert worker.is_running() is False

    # Under MOCK_EMAIL_TRANSPORT=true, status is updated to 'mock_sent'
    mock_sent_items, _ = store.list_outbox(status="mock_sent")
    assert len(mock_sent_items) >= 1
    assert mock_sent_items[0]["status"] == "mock_sent"


def test_outbox_retry_backoff_and_dead_lettering(a6_1_env):
    """
    Outbox retries failed items with exponential backoff and dead-letters after 3 attempts.
    """
    store = a6_1_env["sec_store"]

    out_id = store.queue_alert(
        incident_id="inc_fail_test",
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI SECURITY] Fail Test",
        body_text="Fail body",
        body_html="<p>Fail</p>",
        severity="HIGH"
    )

    class MockFailingTransport:
        def __init__(self):
            self.recipient = "vajra.techworks@gmail.com"
            self.is_mock_transport = False

        def send_email_sync(self, *args, **kwargs):
            return False, "Simulated SMTP timeout error"

    failing_mailer = alert_mailer
    original_send = failing_mailer.send_email_sync
    original_is_mock_prop = type(failing_mailer).is_mock_transport

    try:
        # Mock failure
        failing_mailer.send_email_sync = lambda *args, **kwargs: (False, "Simulated SMTP timeout error")
        type(failing_mailer).is_mock_transport = property(lambda self: False)

        # Attempt 1
        res1 = failing_mailer.process_outbox(store)
        assert res1["failed"] == 1
        items1, _ = store.list_outbox()
        item1 = next(i for i in items1 if i["id"] == out_id)
        assert item1["attempts"] == 1
        assert item1["status"] == "pending"
        assert item1["next_retry_at"] > time.time()

        # Advance next_retry_at for Attempt 2
        with store._connect() as conn:
            conn.execute("UPDATE security_alert_outbox SET next_retry_at = ? WHERE id = ?", (time.time() - 1, out_id))

        res2 = failing_mailer.process_outbox(store)
        assert res2["failed"] == 1

        # Advance next_retry_at for Attempt 3 (Final Attempt -> Dead Letter)
        with store._connect() as conn:
            conn.execute("UPDATE security_alert_outbox SET next_retry_at = ? WHERE id = ?", (time.time() - 1, out_id))

        res3 = failing_mailer.process_outbox(store)
        assert res3["dead_letter"] == 1

        items3, _ = store.list_outbox()
        item3 = next(i for i in items3 if i["id"] == out_id)
        assert item3["status"] == "dead_letter"
        assert "Simulated SMTP timeout error" in item3["last_error"]
        assert item3["attempts"] == 3

    finally:
        failing_mailer.send_email_sync = original_send
        type(failing_mailer).is_mock_transport = original_is_mock_prop


def test_platform_admin_rate_limiting_on_retry_and_export(a6_1_env):
    """
    Security Shield outbox retry and export endpoints are rate-limited to 5/minute.
    """
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a6_1_env["token_admin"])

    # 1. Test outbox retry rate limiting
    responses_retry = []
    for _ in range(6):
        r = client.post("/api/platform/security-shield/outbox/retry")
        responses_retry.append(r.status_code)

    assert responses_retry[0] == 200
    assert 429 in responses_retry, "Excessive outbox retries must return HTTP 429"

    # 2. Test export rate limiting
    responses_export = []
    for _ in range(6):
        r = client.post("/api/platform/security-shield/export")
        responses_export.append(r.status_code)

    assert responses_export[0] == 200
    assert 429 in responses_export, "Excessive export calls must return HTTP 429"


def test_incident_mutation_audit_trail_emission(a6_1_env):
    """
    Updating an incident via platform admin endpoint emits a SECURITY_INCIDENT_MUTATED event.
    """
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a6_1_env["token_admin"])
    store = a6_1_env["sec_store"]

    inc_id, _ = store.aggregate_event_into_incident(
        event_type="ACCESS_UNAUTHORIZED_ADMIN",
        severity="HIGH",
        affected_tenant="tenant_audit",
        actor_id="ip_intruder",
        title="Unauthorized Admin Access",
        description="Attempted to breach admin"
    )

    resp = client.patch(
        f"/api/platform/security-shield/incidents/{inc_id}",
        json={"status": "investigating", "resolution_note": "Investigating intruder IP"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"

    # Verify audit event was emitted
    events, total = store.list_events(event_type="SECURITY_INCIDENT_MUTATED")
    assert total >= 1
    assert events[0]["details"]["incident_id"] == inc_id
    assert events[0]["details"]["status"] == "investigating"


def test_analytics_idempotency_safe_window_vs_flawed_index(a6_1_env):
    """
    Validates why a static UNIQUE index on (tenant_id, session_id, event_name) was flawed:
    it blocks legitimate later customer conversions in the same session.
    The correct design uses a 30s sliding window or explicit idempotency_key.
    """
    main_store = a6_1_env["main_store"]

    session_id = "customer_session_456"
    event_data = {
        "event_name": "google_maps_redirect",
        "session_id": session_id,
        "business_id": "tenant_alpha",
        "timestamp": 1000.0,
    }

    # 1. First click at t=1000s -> Recorded
    res1 = main_store.add_event(event_data, tenant_id="tenant_alpha")
    assert res1.get("status") != "deduplicated"

    # 2. Duplicate click 5s later at t=1005s (e.g. double-click retry) -> Safely Deduplicated
    event_retry = {**event_data, "timestamp": 1005.0}
    res2 = main_store.add_event(event_retry, tenant_id="tenant_alpha")
    assert res2.get("status") == "deduplicated"
    assert res2.get("is_duplicate") is True

    # 3. Legitimate second click 60s later at t=1065s -> Recorded successfully!
    # Under the flawed static UNIQUE index, this would have been rejected/failed.
    event_later = {**event_data, "timestamp": 1065.0}
    res3 = main_store.add_event(event_later, tenant_id="tenant_alpha")
    assert res3.get("status") != "deduplicated", "Legitimate later conversion was incorrectly blocked!"
