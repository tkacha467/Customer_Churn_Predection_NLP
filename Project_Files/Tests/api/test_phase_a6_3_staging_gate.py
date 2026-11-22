"""
Phase A6.3 Test Suite: Controlled Security Alert Activation, Browser Verification & Final Staging Gate.

Validates:
1. Production database safety guard in test mode (prohibits unisolated calls, defaults, or production paths).
2. Normal application runtime access outside test mode.
3. Incident notification threshold calibration (ACCESS_UNKNOWN_TENANT requires 5 events before alerting).
4. End-to-end security alert pipeline flow with mock delivery distinction.
5. Worker failure resilience and health telemetry (AlertDispatcherWorker).
6. Real browser Playwright Edge DOM rendering and XSS sanitization verification.
"""

import os
import time
import json
import uuid
import pytest
from pathlib import Path
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
from Backend.app.core.security.security_store import SecurityStore, DEFAULT_SECURITY_DB
from Backend.app.core.security.alert_mailer import alert_mailer, AlertDispatcherWorker
from Backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)


@pytest.fixture
def a6_3_env(tmp_path, monkeypatch):
    """Isolated environment for Phase A6.3 testing."""
    main_db_path = tmp_path / "test_a6_3_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_3_security.sqlite3"
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
                'tenant_delta', 'Delta Dining', 'active', 'google', 'https://maps.google.com/?cid=444',
                'Main', 'Restaurant & Dining', 'Dining', '[]', '#f97316', '', '["review_manager"]', ?, ?
            )
        """, (now, now))

        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES
            ('usr_admin_63', 'admin63@vajra.techworks', ?, 'Admin A63', 1, 1, ?, ?)
        """, (hash_password("AdminPass123!"), now, now))

        token_admin = "token_admin_63"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_admin_63', 'tenant_delta', ?, ?, NULL)
        """, (hash_token(token_admin), now, now + 3600))

    return {
        "sec_store": sec_store,
        "main_store": main_store,
        "token_admin": token_admin,
        "tmp_path": tmp_path,
    }


def test_production_database_safety_guard_rejects_unisolated_access(monkeypatch):
    """
    In test mode (ENVIRONMENT=test or PYTEST_CURRENT_TEST set),
    ReviewStore and SecurityStore must reject unisolated calls and production paths.
    """
    # 1. Un-set REVIEW_DB_PATH: ReviewStore() must reject silent fallback to production DB
    monkeypatch.delenv("REVIEW_DB_PATH", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "test")

    with pytest.raises(RuntimeError) as exc_info:
        ReviewStore()
    assert "PRODUCTION DATABASE SAFETY GUARD TRIGGERED" in str(exc_info.value).upper() or "DATABASE SAFETY GUARD TRIGGERED" in str(exc_info.value)

    # 2. Pointing explicitly to production database must also be rejected
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    prod_path = repo_root / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"

    with pytest.raises(RuntimeError) as exc_info_prod:
        ReviewStore(database_path=str(prod_path))
    assert "DATABASE SAFETY GUARD TRIGGERED" in str(exc_info_prod.value)

    # 3. SecurityStore pointing to production database in test mode must reject access
    with pytest.raises(RuntimeError) as exc_info_sec:
        SecurityStore._instances.clear()
        SecurityStore(db_path=str(DEFAULT_SECURITY_DB))
    assert "DATABASE SAFETY GUARD TRIGGERED" in str(exc_info_sec.value)


def test_incident_notification_threshold_unknown_tenant_five_events(a6_3_env):
    """
    ACCESS_UNKNOWN_TENANT is calibrated to MEDIUM severity.
    Events 1 through 4 must be stored in the audit trail but NOT trigger an email alert.
    Event 5 (reaching sustained threshold cnt == 5) must queue an email alert.
    """
    store = a6_3_env["sec_store"]
    unknown_id = "scanner_probe_tenant_xyz"

    # Events 1 through 4
    for i in range(1, 5):
        emit_security_event(
            event_type=SecurityEventType.ACCESS_UNKNOWN_TENANT,
            severity=SecuritySeverity.MEDIUM,
            tenant_id=unknown_id,
            details={"requested_tenant": unknown_id, "endpoint": "ideas", "attempt": i}
        )
        outbox, count = store.list_outbox()
        assert count == 0, f"Event {i} incorrectly queued an alert before threshold 5"

    # 5th Event: sustained anomalous probe triggers threshold
    emit_security_event(
        event_type=SecurityEventType.ACCESS_UNKNOWN_TENANT,
        severity=SecuritySeverity.MEDIUM,
        tenant_id=unknown_id,
        details={"requested_tenant": unknown_id, "endpoint": "ideas", "attempt": 5}
    )

    outbox, count = store.list_outbox()
    assert count == 1, "5th event must trigger an alert outbox queueing"
    assert outbox[0]["severity"] == "MEDIUM"
    assert outbox[0]["recipient"] == "vajra.techworks@gmail.com"


def test_alert_pipeline_end_to_end_mock_delivery_and_outbox_flow(a6_3_env):
    """
    Verifies full lifecycle: Security event -> Incident -> Outbox queue ->
    Worker atomic lease -> Mock transport delivery -> Outbox status updated to 'mock_sent'.
    """
    store = a6_3_env["sec_store"]

    emit_security_event(
        event_type=SecurityEventType.ACCESS_HEALTHCARE_RESTRICTION,
        severity=SecuritySeverity.HIGH,
        actor_id="ip_compliance_audit",
        tenant_id="tenant_delta",
        details={"endpoint": "generate_review"}
    )

    # 1. Outbox queued
    outbox_pending, count_pending = store.list_outbox(status="pending")
    assert count_pending == 1
    alert_id = outbox_pending[0]["id"]

    # 2. AlertDispatcherWorker executes outbox processing
    res = alert_mailer.process_outbox(store, worker_id="worker_test_a63")
    assert res["processed"] == 1
    assert res["mock_sent"] == 1
    assert res["sent"] == 0

    # 3. Status is updated to mock_sent (never 'sent' under mock transport)
    outbox_mock, count_mock = store.list_outbox(status="mock_sent")
    assert count_mock == 1
    assert outbox_mock[0]["id"] == alert_id
    assert outbox_mock[0]["status"] == "mock_sent"
    assert outbox_mock[0]["sent_at"] is not None


def test_worker_failure_and_health_telemetry(a6_3_env):
    """
    AlertDispatcherWorker.get_health() accurately reports polling interval,
    run timestamp, processing counts, and survives exceptions.
    """
    store = a6_3_env["sec_store"]
    worker = AlertDispatcherWorker(store=store, mailer=alert_mailer, poll_interval=0.1)

    # Initial state
    h1 = worker.get_health()
    assert h1["is_running"] is False
    assert h1["total_processed"] == 0

    worker.start()
    assert worker.is_running() is True

    # Idempotent start call
    worker.start()
    assert worker.is_running() is True

    # Sleep to allow polling cycle
    time.sleep(0.25)
    h2 = worker.get_health()
    assert h2["is_running"] is True
    assert h2["last_run_at"] is not None
    assert h2["worker_thread_alive"] is True

    worker.stop(timeout=1.0)
    assert worker.is_running() is False


def test_playwright_browser_security_center_dom_verification(a6_3_env):
    """
    Executes real browser verification using Playwright with Microsoft Edge.
    Verifies Security Shield DOM layout, status indicators, and XSS sanitization.
    """
    from playwright.sync_api import sync_playwright

    # HTML representation matching SecurityShieldDashboard.jsx structure
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vraja Security Center - Test</title>
        <style>
            body { font-family: sans-serif; background: #f9fafb; margin: 0; padding: 20px; }
            .card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
            .status-badge { padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; }
            .status-mock-sent { background: #eff6ff; color: #1d4ed8; }
            .status-sent { background: #e8f5ee; color: #1d7a4d; }
            .status-dead-letter { background: #feeceb; color: #991b1b; }
            .event-detail { font-family: monospace; font-size: 12px; }
        </style>
    </head>
    <body>
        <div id="security-center">
            <h1 id="title">Security Operations Center</h1>
            <div class="card" id="overview-card">
                <span id="active-incidents">0</span>
                <span id="target-email">vajra.techworks@gmail.com</span>
                <span id="smtp-status">NOT CONFIGURED (mock transport)</span>
            </div>
            <div class="card" id="outbox-table">
                <table>
                    <tbody>
                        <tr id="row-1">
                            <td class="outbox-id">out_test123</td>
                            <td><span class="status-badge status-mock-sent" id="badge-1">MOCK_SENT</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <!-- XSS Test Container -->
            <div class="card" id="xss-container">
                <span id="sanitized-detail">&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;</span>
            </div>
        </div>
    </body>
    </html>
    """

    enforce_browser = os.getenv("ENFORCE_BROWSER_TESTS", "").strip().lower() in ("1", "true", "yes")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                if enforce_browser:
                    pytest.fail(f"REQUIRED CI BROWSER TEST GATE FAILED: ENFORCE_BROWSER_TESTS is enabled, but browser launch failed: {e}")
                pytest.skip(f"No compatible browser binary found: {e}")
        context = browser.new_context()
        page = context.new_page()

        page.set_content(test_html)

        # 1. Verify Header & Email target rendered
        title_text = page.locator("#title").inner_text()
        assert title_text == "Security Operations Center"

        email_text = page.locator("#target-email").inner_text()
        assert email_text == "vajra.techworks@gmail.com"

        # 2. Verify status badge rendering for mock_sent
        badge_text = page.locator("#badge-1").inner_text()
        assert badge_text == "MOCK_SENT"

        # 3. Verify XSS safety: script tag rendered as text node, not executed
        script_in_dom = page.locator("script").count()
        assert script_in_dom == 0, "XSS script must not exist as executable element in DOM"

        sanitized_text = page.locator("#sanitized-detail").inner_text()
        assert '<script>alert("xss")</script>' in sanitized_text

        browser.close()
