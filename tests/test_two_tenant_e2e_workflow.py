"""
End-to-End Two-Tenant SaaS Workflow Tests for NastaGhar & Multi-Client Hospitality Platform.
Validates controlled platform admin onboarding, isolated customer experiences,
cross-tenant boundary enforcement, entitlement suspension, and session persistence.
"""

import time
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.review_assistant.auth import (
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    _login_attempts,
    _login_lock,
    get_store,
)


@pytest.fixture(autouse=True)
def setup_two_tenant_environment():
    """Sets up an isolated platform admin, Nasta Ghar tenant, and resets rate limits."""
    with _login_lock:
        _login_attempts.clear()

    from api.review_assistant.service import review_service
    review_service._rate_limits.clear()

    store = get_store()

    # 1. Ensure Platform Administrator exists
    admin = store.get_user_by_email("superadmin@platform.test")
    if not admin:
        admin = store.create_user(
            email="superadmin@platform.test",
            password_hash=hash_password("SuperSecurePlatformAdmin99!"),
            display_name="Global Administrator",
            is_active=1,
            is_platform_admin=1
        )
    else:
        with store._connect() as db:
            db.execute("UPDATE users SET is_platform_admin = 1 WHERE id = ?", (admin["id"],))
    store.add_membership(admin["id"], "default_business", role="owner")

    # 2. Ensure Nasta Ghar (default_business) tenant exists
    store.upsert_tenant({
        "id": "default_business",
        "business_name": "Nasta Ghar",
        "review_url": "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro",
        "category": "Breakfast & Snacks",
        "description": "Authentic homestyle breakfast, chai, and snacks in Rajkot.",
        "topics": ["Breakfast", "Chai", "Snacks"],
        "primary_accent": "#f97316",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"]
    })

    # Ensure Owner 1 exists for Nasta Ghar
    owner1 = store.get_user_by_email("owner1@nastaghar.test")
    if not owner1:
        owner1 = store.create_user(
            email="owner1@nastaghar.test",
            password_hash=hash_password("NastaGharPass123!"),
            display_name="Nasta Ghar Owner",
            is_active=1,
            is_platform_admin=0
        )
    store.add_membership(owner1["id"], "default_business", role="owner")


def _ensure_vraja_cafe():
    """Helper to ensure Vraja Cafe tenant and owner exist for isolated tests."""
    store = get_store()
    store.upsert_tenant({
        "id": "vraja_cafe",
        "business_name": "Vraja Artisanal Cafe",
        "review_url": "https://g.page/r/vraja-cafe/review",
        "category": "Cafe & Roastery",
        "branch": "Main Street",
        "description": "Specialty pour-overs and artisanal sourdough.",
        "primary_accent": "#0ea5e9",
        "topics": ["Artisan Coffee", "Cold Brew", "Sourdough", "Vibe"],
        "entitlements": ["review_manager", "digital_card"],
        "status": "active"
    })
    owner2 = store.get_user_by_email("owner@vrajacafe.test")
    if not owner2:
        owner2 = store.create_user(
            email="owner@vrajacafe.test",
            password_hash=hash_password("VrajaOwnerPassword123!"),
            display_name="Vraja Patel",
            is_active=1,
            is_platform_admin=0
        )
    store.add_membership(owner2["id"], "vraja_cafe", role="owner")
    return owner2


def _create_session_for_user(user_id: str, tenant_id: str) -> str:
    """Helper to issue a valid authenticated cookie for tests."""
    store = get_store()
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    store.create_session(
        token_hash=token_hash,
        user_id=user_id,
        active_tenant_id=tenant_id,
        expires_at=time.time() + SESSION_TTL_SECONDS
    )
    return raw_token


def test_platform_admin_onboarding_workflow():
    """Verify authorized platform administrator can onboard a second tenant with initial owner."""
    client = TestClient(app)
    store = get_store()
    admin = store.get_user_by_email("superadmin@platform.test")
    token = _create_session_for_user(admin["id"], "default_business")

    # Clean up prior test run tenant if any
    with store._connect() as db:
        db.execute("DELETE FROM tenant_memberships WHERE tenant_id = 'vraja_cafe'")
        db.execute("DELETE FROM tenants WHERE id = 'vraja_cafe'")
        db.execute("DELETE FROM users WHERE email = 'owner@vrajacafe.test'")

    onboard_payload = {
        "tenant_id": "vraja_cafe",
        "business_name": "Vraja Artisanal Cafe",
        "owner_email": "owner@vrajacafe.test",
        "owner_password": "VrajaOwnerPassword123!",
        "owner_name": "Vraja Patel",
        "category": "Cafe & Roastery",
        "review_url": "https://g.page/r/vraja-cafe/review",
        "branch": "Main Street",
        "description": "Specialty pour-overs and artisanal sourdough.",
        "primary_accent": "#0ea5e9",
        "topics": ["Artisan Coffee", "Cold Brew", "Sourdough", "Vibe"],
        "entitlements": ["review_manager", "digital_card"],
        "status": "active"
    }

    # Execute onboarding request
    response = client.post(
        "/api/platform/tenants",
        json=onboard_payload,
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["tenant_id"] == "vraja_cafe"
    assert data["business_name"] == "Vraja Artisanal Cafe"
    assert data["owner_email"] == "owner@vrajacafe.test"
    assert data["status"] == "active"
    assert "review_manager" in data["entitlements"]

    # Verify database persistence
    tenant = store.get_tenant("vraja_cafe")
    assert tenant is not None
    assert tenant["business_name"] == "Vraja Artisanal Cafe"
    assert tenant["primary_accent"] == "#0ea5e9"

    # Verify owner membership was created
    owner_user = store.get_user_by_email("owner@vrajacafe.test")
    assert owner_user is not None
    membership = store.get_membership(owner_user["id"], "vraja_cafe")
    assert membership is not None
    assert membership["role"] == "owner"


def test_platform_admin_duplicate_tenant_rejected():
    """Verify platform admin cannot overwrite or claim an existing tenant ID."""
    client = TestClient(app)
    store = get_store()
    admin = store.get_user_by_email("superadmin@platform.test")
    token = _create_session_for_user(admin["id"], "default_business")

    # Attempt to onboard default_business again
    response = client.post(
        "/api/platform/tenants",
        json={
            "tenant_id": "default_business",
            "business_name": "Malicious Claim",
            "owner_email": "intruder@evil.test",
            "owner_password": "IntruderPassword123!",
        },
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_ordinary_owner_cannot_access_platform_onboarding():
    """Ensure ordinary business owner cannot call platform onboarding API."""
    client = TestClient(app)
    store = get_store()
    owner1 = store.get_user_by_email("owner1@nastaghar.test")
    token = _create_session_for_user(owner1["id"], "default_business")

    response = client.post(
        "/api/platform/tenants",
        json={
            "tenant_id": "unauthorized_tenant",
            "business_name": "Unauthorized Cafe",
            "owner_email": "intruder@test.com",
            "owner_password": "IntruderPassword123!",
        },
        cookies={OWNER_COOKIE: token},
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 403
    assert "Platform administrator privileges required" in response.json()["detail"]


def test_two_tenant_independent_authentication_and_branding():
    """Verify that Owner 1 and Owner 2 log into their respective accounts and receive correct brand configs."""
    _ensure_vraja_cafe()
    client = TestClient(app)
    store = get_store()

    # 1. Public config resolution for Nasta Ghar
    res1 = client.get("/api/businesses/default_business/review-link")
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["business_name"] == "Nasta Ghar"
    assert d1["primary_accent"] == "#f97316"

    # 2. Public config resolution for Vraja Cafe
    res2 = client.get("/api/businesses/vraja_cafe/review-link")
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["business_name"] == "Vraja Artisanal Cafe"
    assert d2["primary_accent"] == "#0ea5e9"
    assert "Artisan Coffee" in d2["topics"]

    # 3. Owner 2 signs in via /api/auth/login
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "owner@vrajacafe.test",
            "password": "VrajaOwnerPassword123!",
            "tenant_id": "vraja_cafe"
        },
        headers={"Origin": "http://localhost:5173"}
    )
    assert login_res.status_code == 200
    auth_data = login_res.json()
    assert auth_data["authenticated"] is True
    assert auth_data["user"]["email"] == "owner@vrajacafe.test"
    assert auth_data["active_tenant"]["id"] == "vraja_cafe"
    assert auth_data["active_tenant"]["role"] == "owner"


def test_two_tenant_isolated_analytics_and_tickets():
    """Verify strict tenant isolation across analytics events and private customer tickets."""
    _ensure_vraja_cafe()
    client = TestClient(app)
    store = get_store()
    owner1 = store.get_user_by_email("owner1@nastaghar.test")
    owner2 = store.get_user_by_email("owner@vrajacafe.test")

    token_owner1 = _create_session_for_user(owner1["id"], "default_business")
    token_owner2 = _create_session_for_user(owner2["id"], "vraja_cafe")

    # Customer 1 submits private feedback for Nasta Ghar
    res_ticket1 = client.post(
        "/api/reviews/private-feedback",
        json={
            "business_id": "default_business",
            "rating": 2,
            "diner_note": "Chai was a bit cold this morning.",
            "aspects": ["Chai"],
            "guest_contact": "guest1@test.com"
        }
    )
    assert res_ticket1.status_code == 200

    # Customer 2 submits private feedback for Vraja Cafe
    res_ticket2 = client.post(
        "/api/reviews/private-feedback",
        json={
            "business_id": "vraja_cafe",
            "rating": 2,
            "diner_note": "Cold brew was too acidic today.",
            "aspects": ["Cold Brew"],
            "guest_contact": "guest2@test.com"
        }
    )
    assert res_ticket2.status_code == 200

    # Owner 1 fetches private tickets -> must only see ticket for Nasta Ghar
    tickets1 = client.get("/api/reviews/private-tickets", cookies={OWNER_COOKIE: token_owner1})
    assert tickets1.status_code == 200
    items1 = tickets1.json()
    assert any("Chai was a bit cold" in t.get("diner_note", "") for t in items1)
    assert not any("Cold brew was too acidic" in t.get("diner_note", "") for t in items1)

    # Owner 2 fetches private tickets -> must only see ticket for Vraja Cafe
    tickets2 = client.get("/api/reviews/private-tickets", cookies={OWNER_COOKIE: token_owner2})
    assert tickets2.status_code == 200
    items2 = tickets2.json()
    assert any("Cold brew was too acidic" in t.get("diner_note", "") for t in items2)
    assert not any("Chai was a bit cold" in t.get("diner_note", "") for t in items2)


def test_cross_tenant_tampering_blocked():
    """Verify that attempting to read or update another tenant's data via query/path parameters is blocked."""
    _ensure_vraja_cafe()
    client = TestClient(app)
    store = get_store()
    owner2 = store.get_user_by_email("owner@vrajacafe.test")
    token_owner2 = _create_session_for_user(owner2["id"], "vraja_cafe")

    # 1. Owner 2 attempts to query analytics for default_business
    res_analytics = client.get(
        "/api/reviews/analytics?business_id=default_business",
        cookies={OWNER_COOKIE: token_owner2}
    )
    assert res_analytics.status_code == 403
    assert "Access denied" in res_analytics.json()["detail"]

    # 2. Owner 2 attempts to query private tickets for default_business
    res_tickets = client.get(
        "/api/reviews/private-tickets?business_id=default_business",
        cookies={OWNER_COOKIE: token_owner2}
    )
    assert res_tickets.status_code == 403
    assert "Access denied" in res_tickets.json()["detail"]

    # 3. Owner 2 attempts to update config of default_business
    res_config = client.post(
        "/api/businesses/default_business/config",
        json={"google_review_url": "https://attacker.com/review"},
        cookies={OWNER_COOKIE: token_owner2},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res_config.status_code == 403
    assert "Access denied" in res_config.json()["detail"]


def test_tenant_suspension_and_entitlement_enforcement():
    """Verify platform admin can suspend a tenant, immediately disabling review generation and owner operations."""
    _ensure_vraja_cafe()
    client = TestClient(app)
    store = get_store()
    admin = store.get_user_by_email("superadmin@platform.test")
    token_admin = _create_session_for_user(admin["id"], "default_business")

    owner2 = store.get_user_by_email("owner@vrajacafe.test")
    token_owner2 = _create_session_for_user(owner2["id"], "vraja_cafe")

    # Step 1: Active tenant generates review ideas successfully
    res_ideas = client.post(
        "/api/reviews/ideas",
        json={"business_id": "vraja_cafe", "rating": 5, "aspects": ["Artisan Coffee"]}
    )
    assert res_ideas.status_code == 200

    # Step 2: Platform Admin suspends Vraja Cafe
    res_suspend = client.patch(
        "/api/platform/tenants/vraja_cafe/status",
        json={"status": "suspended"},
        cookies={OWNER_COOKIE: token_admin},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res_suspend.status_code == 200
    assert res_suspend.json()["status"] == "suspended"

    # Step 3: Customer generation attempt on suspended tenant returns 403 Forbidden
    res_ideas_suspended = client.post(
        "/api/reviews/ideas",
        json={"business_id": "vraja_cafe", "rating": 5, "aspects": ["Artisan Coffee"]}
    )
    assert res_ideas_suspended.status_code == 403
    assert "not enabled" in res_ideas_suspended.json()["detail"].lower() or "suspended" in res_ideas_suspended.json()["detail"].lower()

    # Step 4: Owner 2 attempting to view analytics on suspended tenant returns 403 Forbidden
    res_owner_analytics = client.get(
        "/api/reviews/analytics",
        cookies={OWNER_COOKIE: token_owner2}
    )
    assert res_owner_analytics.status_code == 403
    assert "suspended" in res_owner_analytics.json()["detail"].lower()

    # Step 5: Platform Admin reactivates Vraja Cafe
    res_reactivate = client.patch(
        "/api/platform/tenants/vraja_cafe/status",
        json={"status": "active"},
        cookies={OWNER_COOKIE: token_admin},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res_reactivate.status_code == 200

    # Step 6: Customer generation succeeds again
    res_ideas_reactivated = client.post(
        "/api/reviews/ideas",
        json={"business_id": "vraja_cafe", "rating": 5, "aspects": ["Artisan Coffee"]}
    )
    assert res_ideas_reactivated.status_code == 200


def test_unknown_tenant_not_found():
    """Ensure non-existent tenant returns 404 rather than defaulting or leaking data."""
    client = TestClient(app)
    response = client.get("/api/businesses/non_existent_bistro_404/review-link")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
