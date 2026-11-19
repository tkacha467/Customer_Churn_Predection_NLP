"""
Automated Test Suite for Server-Authenticated Preview Context & 3-Way Analytics Separation
(SPEC-03 / ISS-01 Verification).

Tests:
1. Customer traffic recorded into production analytics_events table.
2. Client-supplied unauthenticated ?preview=true is NOT trusted and treated as customer traffic.
3. Authenticated staff/owners receive cryptographically signed HMAC-SHA256 preview tokens.
4. Staff cannot request preview tokens for unrelated tenants.
5. Preview events are strictly segregated into preview_analytics_events and never written into analytics_events.
6. Owner analytics aggregations (/api/analytics) remain 100% clean and unpolluted by preview/admin events.
7. Platform admin sessions are dynamically classified as 'internal_admin'.
8. Basic idempotency / deduplication prevents redundant duplicate event writes.
9. Tampered or expired preview tokens fail safely and fall back to customer traffic.
10. Preview events endpoint returns segregated preview telemetry for authenticated staff.
"""

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.auth.auth import (
    get_store,
    hash_password,
    make_session,
    create_preview_token,
    verify_preview_token,
    OWNER_COOKIE,
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_preview_analytics.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(test_db))
    monkeypatch.setenv("OWNER_SESSION_SECRET", "test-secret-key-at-least-32-chars-long-security")
    
    # Reset store cache
    from backend.app.core.auth import auth as auth_mod
    auth_mod._stores.clear()
    
    store = get_store()

    # Re-link review_service to the test store and clear active session caches
    from backend.app.api.service import review_service
    review_service._store = store
    review_service._analytics_events = store.list_events()
    review_service._preview_events = store.list_preview_events()
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    
    # Provision test tenants
    store.upsert_tenant({
        "id": "tenant_cafe",
        "business_name": "Test Cafe",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"]
    })
    store.upsert_tenant({
        "id": "tenant_bistro",
        "business_name": "Test Bistro",
        "status": "active",
        "entitlements": ["review_manager"]
    })
    
    # Provision test users
    u_owner = store.create_user("owner@testcafe.com", hash_password("Password123!"), display_name="Cafe Owner")
    store.add_membership(u_owner["id"], "tenant_cafe", role="owner")
    
    u_admin = store.create_user("admin@vraja.ai", hash_password("AdminPass123!"), display_name="Vraja Admin", is_platform_admin=True)
    
    with TestClient(app) as test_client:
        test_client.u_owner = u_owner
        test_client.u_admin = u_admin
        test_client.store = store
        yield test_client


def test_01_customer_traffic_records_to_production_analytics_events(client):
    """Anonymous diner traffic must be recorded into analytics_events table and reflected in analytics."""
    res_sess = client.post("/api/reviews/session", json={"business_id": "tenant_cafe", "table_number": "Table 5"})
    assert res_sess.status_code == 200
    sess_data = res_sess.json()
    assert sess_data["traffic_source"] == "customer"
    assert sess_data["is_preview"] is False
    session_id = sess_data["session_id"]

    res_ev = client.post("/api/reviews/events", json={
        "session_id": session_id,
        "event_name": "rating_selected",
        "metadata": {"business_id": "tenant_cafe", "rating": 5}
    })
    assert res_ev.status_code == 200
    assert res_ev.json()["traffic_source"] == "customer"

    # Verify event exists in production analytics_events table
    events = client.store.list_events("tenant_cafe")
    assert any(e.get("event_name") == "rating_selected" for e in events)

    # Verify preview_analytics_events table has zero events
    preview_events = client.store.list_preview_events("tenant_cafe")
    assert len(preview_events) == 0


def test_02_client_spoofed_preview_flag_untrusted(client):
    """Client-supplied ?preview=true or is_preview: true without signed token is NOT trusted."""
    res_sess = client.post(
        "/api/reviews/session?preview=true",
        json={"business_id": "tenant_cafe", "table_number": "Table 1", "is_preview": True}
    )
    assert res_sess.status_code == 200
    sess_data = res_sess.json()
    # Server strictly resolves unauthenticated claims to customer traffic
    assert sess_data["traffic_source"] == "customer"
    assert sess_data["is_preview"] is False


def test_03_issue_preview_token_for_tenant_staff(client):
    """Authenticated tenant owner/staff can request a cryptographically signed preview token."""
    raw_token = make_session(user_id=client.u_owner["id"], tenant_id="tenant_cafe")
    client.cookies.set(OWNER_COOKIE, raw_token)

    res = client.post("/api/reviews/preview-token", json={"business_id": "tenant_cafe"})
    assert res.status_code == 200
    data = res.json()
    assert "preview_token" in data
    assert data["traffic_source"] == "preview"
    assert data["tenant_id"] == "tenant_cafe"

    # Verify token payload using server helper
    payload = verify_preview_token(data["preview_token"])
    assert payload is not None
    assert payload["tenant_id"] == "tenant_cafe"
    assert payload["traffic_source"] == "preview"


def test_04_issue_preview_token_forbidden_for_unrelated_tenant(client):
    """Staff of tenant_cafe cannot request preview tokens for tenant_bistro."""
    raw_token = make_session(user_id=client.u_owner["id"], tenant_id="tenant_cafe")
    client.cookies.set(OWNER_COOKIE, raw_token)

    res = client.post("/api/reviews/preview-token", json={"business_id": "tenant_bistro"})
    assert res.status_code == 403


def test_05_preview_session_and_events_segregated_to_preview_table(client):
    """Preview session and events must be written exclusively to preview_analytics_events."""
    # Obtain signed preview token
    token = create_preview_token(tenant_id="tenant_cafe", user_id=client.u_owner["id"], role="owner")

    # Start session with preview token
    res_sess = client.post(
        "/api/reviews/session",
        json={"business_id": "tenant_cafe", "preview_token": token}
    )
    assert res_sess.status_code == 200
    sess_data = res_sess.json()
    assert sess_data["traffic_source"] == "preview"
    assert sess_data["is_preview"] is True
    session_id = sess_data["session_id"]

    # Record review event under preview session
    res_ev = client.post(
        "/api/reviews/events",
        json={
            "session_id": session_id,
            "event_name": "rating_selected",
            "metadata": {"business_id": "tenant_cafe", "rating": 1}
        }
    )
    assert res_ev.status_code == 200
    assert res_ev.json()["traffic_source"] == "preview"

    # Verify event was written to preview_analytics_events table
    preview_events = client.store.list_preview_events("tenant_cafe")
    assert any(e.get("event_name") == "rating_selected" for e in preview_events)

    # Verify event was NEVER written to production analytics_events table
    prod_events = client.store.list_events("tenant_cafe")
    assert not any(e.get("session_id") == session_id for e in prod_events)


def test_06_owner_analytics_summary_never_polluted_by_preview_events(client):
    """Owner analytics endpoint (/api/analytics) must reflect ONLY customer traffic."""
    # 1. Record 1 customer 5-star rating
    s1 = client.post("/api/reviews/session", json={"business_id": "tenant_cafe"}).json()["session_id"]
    client.post("/api/reviews/events", json={
        "session_id": s1,
        "event_name": "rating_selected",
        "metadata": {"business_id": "tenant_cafe", "rating": 5}
    })

    # 2. Record 10 preview 1-star ratings
    token = create_preview_token(tenant_id="tenant_cafe", user_id=client.u_owner["id"], role="owner")
    s2 = client.post("/api/reviews/session", json={"business_id": "tenant_cafe", "preview_token": token}).json()["session_id"]
    for _ in range(10):
        client.post("/api/reviews/events", json={
            "session_id": s2,
            "event_name": "rating_selected",
            "metadata": {"business_id": "tenant_cafe", "rating": 1}
        })

    # 3. Query owner analytics as authenticated owner
    raw_token = make_session(user_id=client.u_owner["id"], tenant_id="tenant_cafe")
    client.cookies.set(OWNER_COOKIE, raw_token)

    analytics_res = client.get("/api/reviews/analytics?business_id=tenant_cafe")
    assert analytics_res.status_code == 200
    summary = analytics_res.json()

    # The 10 preview 1-star ratings must NOT appear in rating_distribution or event_counts
    ratings_dist = summary.get("rating_distribution", {})
    assert ratings_dist.get("5", 0) == 1
    assert ratings_dist.get("1", 0) == 0  # 1-star count is 0 because preview was completely isolated!


def test_07_platform_admin_session_classified_as_internal_admin(client):
    """Platform admin session context dynamically resolves to 'internal_admin'."""
    raw_token = make_session(user_id=client.u_admin["id"], tenant_id="tenant_cafe")
    client.cookies.set(OWNER_COOKIE, raw_token)

    # Calling session while signed in as platform admin
    res_sess = client.post("/api/reviews/session", json={"business_id": "tenant_cafe"})
    assert res_sess.status_code == 200
    sess_data = res_sess.json()
    assert sess_data["traffic_source"] == "internal_admin"
    assert sess_data["is_preview"] is True

    # Events sent under this session are tagged internal_admin
    res_ev = client.post("/api/reviews/events", json={
        "session_id": sess_data["session_id"],
        "event_name": "review_selected",
        "metadata": {"business_id": "tenant_cafe"}
    })
    assert res_ev.status_code == 200
    assert res_ev.json()["traffic_source"] == "internal_admin"

    # Confirmed segregated in preview table
    preview_events = client.store.list_preview_events("tenant_cafe")
    assert any(e.get("traffic_source") == "internal_admin" for e in preview_events)


def test_08_analytics_event_deduplication(client):
    """Duplicate event submissions with identical idempotency_key within sliding window are deduplicated."""
    sess_id = client.post("/api/reviews/session", json={"business_id": "tenant_cafe"}).json()["session_id"]

    # First event submission
    res1 = client.post("/api/reviews/events", json={
        "session_id": sess_id,
        "event_name": "review_copied",
        "idempotency_key": f"{sess_id}-copy-1",
        "metadata": {"business_id": "tenant_cafe"}
    })
    assert res1.status_code == 200
    assert res1.json()["deduplicated"] is False

    # Second immediate submission with identical idempotency_key
    res2 = client.post("/api/reviews/events", json={
        "session_id": sess_id,
        "event_name": "review_copied",
        "idempotency_key": f"{sess_id}-copy-1",
        "metadata": {"business_id": "tenant_cafe"}
    })
    assert res2.status_code == 200
    assert res2.json()["deduplicated"] is True


def test_09_tampered_preview_token_falls_back_to_customer(client):
    """Tampered or invalid preview tokens safely fall back to customer traffic."""
    tampered_token = "eyJ0ZW5hbnRfaWQiOiJ0ZW5hbnRfY2FmZSJ9.invalidhash12345"

    res_sess = client.post(
        "/api/reviews/session",
        json={"business_id": "tenant_cafe", "preview_token": tampered_token}
    )
    assert res_sess.status_code == 200
    # Must NOT error out with 500, must safely treat as customer
    assert res_sess.json()["traffic_source"] == "customer"
    assert res_sess.json()["is_preview"] is False


def test_10_preview_events_query_endpoint(client):
    """Authenticated staff can inspect segregated preview events via /api/reviews/preview-events."""
    token = create_preview_token(tenant_id="tenant_cafe", user_id=client.u_owner["id"], role="owner")
    sess = client.post("/api/reviews/session", json={"business_id": "tenant_cafe", "preview_token": token}).json()

    client.post("/api/reviews/events", json={
        "session_id": sess["session_id"],
        "event_name": "language_selected",
        "metadata": {"business_id": "tenant_cafe", "language": "hindi"}
    })

    # Query preview events as authenticated owner
    raw_token = make_session(user_id=client.u_owner["id"], tenant_id="tenant_cafe")
    client.cookies.set(OWNER_COOKIE, raw_token)

    res = client.get("/api/reviews/preview-events?business_id=tenant_cafe")
    assert res.status_code == 200
    events = res.json().get("events", [])
    assert any(e.get("event_name") == "language_selected" for e in events)
