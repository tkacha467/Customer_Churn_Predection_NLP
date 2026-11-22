"""
Phase A5-S Enterprise API Security Hardening & Release Security Audit Test Suite.
Validates:
1. Strict unknown-tenant resolution (404 for unknown, 403 for suspended, revoked, and healthcare).
2. Authoritative SQLite override over legacy JSON configurations.
3. Legacy tenant credential quarantine (legacy tenants cannot authenticate or access owner APIs).
4. Multi-tenant BOLA/IDOR isolation (cross-tenant access strictly blocked with Security Shield logging).
5. CSRF origin verification on state-changing requests.
6. Unauthorized platform admin rejection and Security Shield audit logging.
7. Server-authoritative preview isolation (client spoofing prevented and logged).
8. Durable SQLite event deduplication across multi-worker operations.
9. Platform admin Security Shield audit log inspection.
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
    SESSION_TTL_SECONDS
)
from Backend.app.api.service import review_service
from Backend.app.core.tenants.google_reviews import google_review_manager
from Backend.app.core.security.security_shield import (
    security_shield,
    SecurityEventType,
    SecuritySeverity,
)


@pytest.fixture
def a5s_env(tmp_path, monkeypatch):
    """Isolated security testing sandbox."""
    db_path = tmp_path / "test_a5s_security.sqlite3"
    legacy_json_path = tmp_path / "business_links.json"
    docs_path = tmp_path / "test_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    # Legacy fallback JSON configuration
    legacy_data = {
        "legacy_only_biz": {
            "business_name": "Legacy Only Cafe",
            "google_review_url": "https://maps.google.com/?cid=111",
            "status": "active",
            "entitlements": ["review_manager"]
        },
        "conflicting_biz": {
            "business_name": "Conflicting Business",
            "google_review_url": "https://maps.google.com/?cid=222",
            "status": "active",
            "entitlements": ["review_manager"]
        },
        "legacy_healthcare": {
            "business_name": "Legacy Dental Clinic",
            "google_review_url": "https://maps.google.com/?cid=333",
            "category": "Healthcare & Clinics",
            "status": "active",
            "entitlements": ["review_manager"]
        }
    }
    legacy_json_path.write_text(json.dumps(legacy_data), encoding="utf-8")

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(legacy_json_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-key-for-test-32-chars!!")

    _stores.clear()
    review_service._rate_limits.clear()
    review_service._dedup_cache.clear()
    review_service._verified_preview_sessions.clear()
    security_shield.clear()

    # Re-init google review manager with isolated test file
    google_review_manager._file_path = str(legacy_json_path)
    google_review_manager._links.clear()
    google_review_manager._load_links()

    store = ReviewStore(database_path=str(db_path))
    now = time.time()

    # Seed test tenants, users, and credentials in SQLite
    with store._connect() as db:
        # 1. Active review tenant (Tenant A)
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('tenant_a', 'Tenant Alpha Dining', 'active', 'google', 'https://maps.google.com/?cid=aaa', 'Main', 'Restaurant & Dining', 'Fine dining', '[]', '#f97316', '', '["review_manager", "digital_card"]', ?, ?)
        """, (now, now))

        # 2. Active review tenant (Tenant B)
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('tenant_b', 'Tenant Beta Cafe', 'active', 'google', 'https://maps.google.com/?cid=bbb', 'East', 'Cafe & Bakery', 'Pastries', '[]', '#2563eb', '', '["review_manager"]', ?, ?)
        """, (now, now))

        # 3. Suspended tenant in SQLite (overriding legacy active status)
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('conflicting_biz', 'Conflicting Business (Suspended in DB)', 'suspended', 'google', 'https://maps.google.com/?cid=222', 'Central', 'Retail', 'Shop', '[]', '#10b981', '', '["review_manager"]', ?, ?)
        """, (now, now))

        # 4. Entitlement revoked tenant in SQLite
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('revoked_biz', 'Revoked Entitlement Biz', 'active', 'google', 'https://maps.google.com/?cid=444', 'West', 'Services', 'Services', '[]', '#6366f1', '', '["digital_card"]', ?, ?)
        """, (now, now))

        # 5. Healthcare tenant in SQLite
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('healthcare_biz', 'Apex Health Clinic', 'active', 'google', 'https://maps.google.com/?cid=555', 'City', 'Healthcare & Clinics', 'Medical', '[]', '#0d9488', '', '["review_manager"]', ?, ?)
        """, (now, now))

        # Seed Users
        # User 1: Owner of Tenant A
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('usr_owner_a', 'owner_a@test.com', ?, 'Owner A', 1, 0, ?, ?)
        """, (hash_password("OwnerPassword123!"), now, now))

        # User 2: Owner of Tenant B
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('usr_owner_b', 'owner_b@test.com', ?, 'Owner B', 1, 0, ?, ?)
        """, (hash_password("OwnerPassword123!"), now, now))

        # User 3: Platform Admin
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('usr_platform_admin', 'admin@vajra.techworks', ?, 'Admin', 1, 1, ?, ?)
        """, (hash_password("AdminMasterPassword123!"), now, now))

        # Seed Memberships
        db.execute("""
            INSERT OR REPLACE INTO tenant_memberships (id, user_id, tenant_id, role, created_at)
            VALUES
            ('mem_a', 'usr_owner_a', 'tenant_a', 'owner', ?),
            ('mem_b', 'usr_owner_b', 'tenant_b', 'owner', ?)
        """, (now, now))

        # Seed Active Sessions
        token_a = "token_owner_a_valid_session"
        token_b = "token_owner_b_valid_session"
        token_admin = "token_admin_valid_session"

        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES
            (?, 'usr_owner_a', 'tenant_a', ?, ?, NULL),
            (?, 'usr_owner_b', 'tenant_b', ?, ?, NULL),
            (?, 'usr_platform_admin', 'tenant_a', ?, ?, NULL)
        """, (hash_token(token_a), now, now + 3600, hash_token(token_b), now, now + 3600, hash_token(token_admin), now, now + 3600))

    return {
        "store": store,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


def test_unknown_tenant_resolution_rejection(a5s_env):
    """Unknown tenant identifier must strictly return HTTP 404 with Security Shield audit logging."""
    client = TestClient(app)
    unknown_id = "completely_unknown_vendor_999"

    # 1. Review ideas request
    resp = client.post("/api/reviews/ideas", json={
        "business_id": unknown_id,
        "rating": 5,
        "topics": ["Taste"],
        "language": "en"
    })
    assert resp.status_code == 404
    assert f"'{unknown_id}' not found" in resp.json()["detail"]

    # 2. Review generation request
    resp_gen = client.post("/api/reviews/generate", json={
        "business_id": unknown_id,
        "rating": 5,
        "selected_aspects": ["Taste"],
        "language": "en"
    })
    assert resp_gen.status_code == 404

    # 3. Public review link endpoint
    resp_link = client.get(f"/api/businesses/{unknown_id}/review-link")
    assert resp_link.status_code == 404

    # Verify Security Shield recorded the incident
    events = security_shield.list_events(tenant_filter=unknown_id)
    assert len(events) >= 1
    assert events[0]["event_type"] == SecurityEventType.ACCESS_UNKNOWN_TENANT.value
    assert events[0]["severity"] == SecuritySeverity.MEDIUM.value


def test_suspended_tenant_rejection(a5s_env):
    """Suspended tenant must return HTTP 403 and emit ACCESS_SUSPENDED_TENANT."""
    client = TestClient(app)

    # conflicting_biz is suspended in SQLite
    resp = client.post("/api/reviews/ideas", json={
        "business_id": "conflicting_biz",
        "rating": 5,
        "topics": ["Service"],
        "language": "en"
    })
    assert resp.status_code == 403
    assert "suspended" in resp.json()["detail"].lower()

    events = security_shield.list_events(tenant_filter="conflicting_biz")
    assert any(e["event_type"] == SecurityEventType.ACCESS_SUSPENDED_TENANT.value for e in events)


def test_revoked_entitlement_rejection(a5s_env):
    """Tenant without review_manager entitlement must return HTTP 403."""
    client = TestClient(app)

    # revoked_biz only has digital_card entitlement in SQLite
    resp = client.post("/api/reviews/generate", json={
        "business_id": "revoked_biz",
        "rating": 5,
        "selected_aspects": ["Speed"],
        "language": "en"
    })
    assert resp.status_code == 403
    assert "not enabled" in resp.json()["detail"].lower() or "review_manager" in resp.json()["detail"].lower()

    events = security_shield.list_events(tenant_filter="revoked_biz")
    assert any(e["event_type"] == SecurityEventType.TENANT_ENTITLEMENT_VIOLATION.value for e in events)


def test_restricted_healthcare_tenant_rejection(a5s_env):
    """Restricted healthcare tenant in SQLite and legacy JSON must return HTTP 403."""
    client = TestClient(app)

    # 1. SQLite healthcare tenant
    resp1 = client.post("/api/reviews/ideas", json={
        "business_id": "healthcare_biz",
        "rating": 5,
        "topics": ["Doctors"],
        "language": "en"
    })
    assert resp1.status_code == 403
    assert "healthcare" in resp1.json()["detail"].lower()

    # 2. Legacy JSON healthcare tenant
    resp2 = client.post("/api/reviews/generate", json={
        "business_id": "legacy_healthcare",
        "rating": 5,
        "selected_aspects": ["Treatment"],
        "language": "en"
    })
    assert resp2.status_code == 403
    assert "healthcare" in resp2.json()["detail"].lower()

    events = security_shield.list_events(tenant_filter="healthcare_biz")
    assert any(e["event_type"] == SecurityEventType.ACCESS_HEALTHCARE_RESTRICTION.value for e in events)


def test_legacy_tenant_cannot_login_or_access_owner_api(a5s_env):
    """Legacy JSON tenant has zero credentials in SQLite and cannot log in or access owner endpoints."""
    client = TestClient(app)

    # 1. Attempt login with legacy tenant ID
    login_resp = client.post("/api/auth/login", json={
        "email": "legacy_only_biz",
        "password": "AnyPassword123!"
    })
    assert login_resp.status_code == 401

    # 2. Attempt to update business profile without session
    profile_resp = client.put("/api/businesses/legacy_only_biz/profile", json={
        "name": "Hacked Profile"
    })
    assert profile_resp.status_code == 401


def test_cross_tenant_isolation_and_idor_protection(a5s_env):
    """Owner of Tenant A cannot modify or inspect Tenant B data (BOLA/IDOR prevention)."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a5s_env["token_a"])

    # Owner A attempts to update Tenant B's business profile
    resp = client.put(
        "/api/businesses/tenant_b/profile",
        json={"name": "Malicious Hijack"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

    # Verify Security Shield recorded cross-tenant denial
    events = security_shield.list_events(tenant_filter="tenant_b")
    assert any(e["event_type"] == SecurityEventType.ACCESS_CROSS_TENANT_DENIAL.value for e in events)


def test_csrf_origin_header_validation(a5s_env):
    """State-changing requests with invalid Origin header must be rejected with 403."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a5s_env["token_a"])

    # Attempt request from untrusted origin
    resp = client.put(
        "/api/businesses/tenant_a/profile",
        json={"name": "Cross-Site Attack"},
        headers={"Origin": "http://evil-phishing-attacker.com"}
    )
    assert resp.status_code == 403
    assert "origin" in resp.json()["detail"].lower()

    # Verify Security Shield emitted CSRF violation event
    events = security_shield.list_events()
    assert any(e["event_type"] == SecurityEventType.CSRF_ORIGIN_VIOLATION.value for e in events)


def test_unauthorized_platform_admin_access(a5s_env):
    """Non-platform-admin tenant owner cannot access platform admin endpoints."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a5s_env["token_a"])

    # Owner A attempts to access platform Security Shield endpoint
    resp = client.get("/api/platform/security-shield/events")
    assert resp.status_code == 403
    assert "Platform admin" in resp.json()["detail"]

    # Verify Security Shield recorded unauthorized admin access
    events = security_shield.list_events()
    assert any(e["event_type"] == SecurityEventType.ACCESS_UNAUTHORIZED_ADMIN.value for e in events)


def test_server_authoritative_preview_isolation(a5s_env):
    """Public unauthenticated client cannot spoof is_preview: true. Must be registered."""
    client = TestClient(app)

    # 1. Unregistered spoofed preview event
    resp_spoof = client.post("/api/reviews/events", json={
        "session_id": "spoofed_preview_sess_001",
        "event_name": "google_maps_direct_click",
        "metadata": {
            "business_id": "tenant_a",
            "is_preview": True
        }
    })
    assert resp_spoof.status_code == 200

    # Verify Security Shield logged the spoofing attempt
    events = security_shield.list_events(tenant_filter="tenant_a")
    assert any(e["event_type"] == SecurityEventType.ABUSE_PREVIEW_SPOOF_ATTEMPT.value for e in events)

    # 2. Legitimate preview session registered by authenticated owner
    client.cookies.set(OWNER_COOKIE, a5s_env["token_a"])
    resp_reg = client.post("/api/reviews/preview-session", json={
        "business_id": "tenant_a",
        "session_id": "legit_preview_sess_777"
    }, headers={"Origin": "http://localhost:5173"})
    assert resp_reg.status_code == 200
    assert resp_reg.json()["is_preview"] is True

    # Now public client sends event with registered preview session
    client.cookies.clear()
    resp_legit = client.post("/api/reviews/events", json={
        "session_id": "legit_preview_sess_777",
        "event_name": "google_maps_direct_click",
        "metadata": {
            "business_id": "tenant_a",
            "is_preview": True
        }
    })
    assert resp_legit.status_code == 200


def test_multi_worker_durable_sqlite_idempotency(a5s_env):
    """Durable SQLite deduplication prevents duplicate conversion events within 30 seconds."""
    store = a5s_env["store"]

    event_payload = {
        "business_id": "tenant_a",
        "session_id": "idempotency_sess_101",
        "event_name": "google_maps_direct_click",
        "client_timestamp": "2026-11-20T00:00:00Z",
        "meta": {"source": "button"}
    }

    # First event recorded successfully
    r1 = store.add_event(event_payload)
    assert r1.get("status") == "recorded"

    # Immediate second event within 30-second window is deduplicated
    r2 = store.add_event(event_payload)
    assert r2.get("status") == "deduplicated"
    assert r2.get("is_duplicate") is True

    # Check database event count is strictly 1
    with store._connect() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM analytics_events WHERE tenant_id = 'tenant_a' AND json_extract(payload, '$.session_id') = 'idempotency_sess_101'"
        ).fetchone()[0]
        assert count == 1


def test_platform_admin_security_shield_inspection(a5s_env):
    """Platform admin can inspect structured Security Shield events."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, a5s_env["token_admin"])

    # Emit a test security event
    security_shield.emit(
        event_type=SecurityEventType.ABUSE_RATE_LIMIT_EXCEEDED,
        severity=SecuritySeverity.HIGH,
        actor_id="test_actor",
        tenant_id="tenant_a",
        action_taken="RATE_LIMITED",
        details={"ip": "1.2.3.4", "endpoint": "/api/reviews/generate"}
    )

    resp = client.get("/api/platform/security-shield/events?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert data["target_email"] == "vajra.techworks@gmail.com"
    assert any(e["event_type"] == SecurityEventType.ABUSE_RATE_LIMIT_EXCEEDED.value for e in data["events"])
