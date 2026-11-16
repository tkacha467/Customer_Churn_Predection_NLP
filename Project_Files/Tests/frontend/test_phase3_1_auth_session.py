"""
Focused Automated Test Suite for VRAJA AI Phase 3.1:
Unified Client Portal Session Initialization, Entitlement Resolution,
Tenant Switching, and Auth Gate Contracts.
"""

import json
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    _login_attempts,
    _login_lock,
)
from Backend.app.api.service import review_service
from Backend.app.core.database.migration import apply_phase2_schema_alterations
import time


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Provides an isolated database for Phase 3.1 auth session tests."""
    db_file = tmp_path / "phase3_1_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_file))
    _stores[str(db_file)] = store

    with store._connect() as con:
        apply_phase2_schema_alterations(con)

    # Provision multi-product test tenants:
    # 1. Tenant A (Product A only)
    store.upsert_tenant({
        "id": "tenant-alpha",
        "business_name": "Alpha Cafe",
        "branch": "Main Branch",
        "category": "Cafe",
        "entitlements": ["review_manager"]
    })
    store.upsert_business_profile("tenant-alpha", {
        "display_name": "Alpha Cafe",
        "category": "Cafe",
        "branch_name": "Main Branch",
        "description": "Artisanal coffee and breakfast.",
    })
    store.update_shared_business_profile("tenant-alpha", {"brand_accent": "#174D3A"})

    # 2. Tenant B (Product B only)
    store.upsert_tenant({
        "id": "tenant-beta",
        "business_name": "Beta Studio",
        "branch": "Design Studio",
        "category": "Creative Studio",
        "entitlements": ["digital_card"]
    })
    store.upsert_business_profile("tenant-beta", {
        "display_name": "Beta Studio",
        "category": "Creative Studio",
        "branch_name": "Design Studio",
        "description": "Digital branding and cards.",
    })
    store.update_shared_business_profile("tenant-beta", {"brand_accent": "#078BFF"})

    # 3. Tenant Dual (Both products)
    store.upsert_tenant({
        "id": "tenant-dual",
        "business_name": "Dual Enterprises",
        "branch": "Headquarters",
        "category": "Hospitality",
        "entitlements": ["review_manager", "digital_card"]
    })
    store.upsert_business_profile("tenant-dual", {
        "display_name": "Dual Enterprises",
        "category": "Hospitality",
        "branch_name": "Headquarters",
        "description": "Full-service hospitality group.",
        "brand_accent": "#C6A66B"
    })

    # 4. Tenant None (Neither product)
    store.upsert_tenant({
        "id": "tenant-none",
        "business_name": "Zero Modules Ltd",
        "branch": "Pending Activation",
        "category": "Retail",
        "entitlements": []
    })
    store.upsert_business_profile("tenant-none", {
        "display_name": "Zero Modules Ltd",
        "category": "Retail",
        "branch_name": "Pending Activation",
        "description": "Awaiting module licensing.",
        "brand_accent": None
    })

    # Provision Users:
    # Multi-tenant Owner: has membership in tenant-alpha (owner) and tenant-beta (manager)
    multi_user = store.create_user(
        email="multi@vraja.ai",
        password_hash=hash_password("Password123!"),
        display_name="Multi Owner"
    )
    multi_user_id = multi_user["id"]
    store.add_membership(multi_user_id, "tenant-alpha", "owner")
    store.add_membership(multi_user_id, "tenant-beta", "manager")

    # Single Tenant Staff: member of tenant-dual (staff)
    staff_user = store.create_user(
        email="staff@vraja.ai",
        password_hash=hash_password("Password123!"),
        display_name="Dual Staff"
    )
    staff_user_id = staff_user["id"]
    store.add_membership(staff_user_id, "tenant-dual", "staff")

    return {
        "store": store,
        "db_path": str(db_file),
        "multi_user_id": multi_user_id,
        "staff_user_id": staff_user_id
    }


def create_authenticated_client(user_id: str, tenant_id: str, store: ReviewStore):
    """Helper to issue a session token and return a TestClient with cookie set."""
    client = TestClient(app)
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    expires_at = time.time() + SESSION_TTL_SECONDS
    store.create_session(
        token_hash=token_hash,
        user_id=user_id,
        active_tenant_id=tenant_id,
        expires_at=expires_at,
        ip_address="127.0.0.1",
        user_agent="TestRunner"
    )
    client.cookies.set(OWNER_COOKIE, raw_token)
    return client


def test_01_session_unauthenticated_returns_401():
    """Unauthenticated GET /api/auth/session returns 401 Unauthorized."""
    client = TestClient(app)
    resp = client.get("/api/auth/session")
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_02_session_authenticated_returns_active_and_available_tenants(test_db):
    """Authenticated GET /api/auth/session returns active_tenant and available_tenants."""
    client = create_authenticated_client(test_db["multi_user_id"], "tenant-alpha", test_db["store"])
    resp = client.get("/api/auth/session")
    assert resp.status_code == 200
    data = resp.json()

    assert data["authenticated"] is True
    assert data["user"]["email"] == "multi@vraja.ai"
    assert data["active_tenant"]["id"] == "tenant-alpha"
    assert data["active_tenant"]["role"] == "owner"
    assert len(data["available_tenants"]) == 2

    tenant_ids = [t["id"] for t in data["available_tenants"]]
    assert "tenant-alpha" in tenant_ids
    assert "tenant-beta" in tenant_ids


def test_03_stage2_shared_profile_returns_authoritative_entitlements_product_a(test_db):
    """GET /shared-profile for tenant-alpha returns ['review_manager'] entitlements."""
    client = create_authenticated_client(test_db["multi_user_id"], "tenant-alpha", test_db["store"])
    resp = client.get("/api/businesses/tenant-alpha/shared-profile")
    assert resp.status_code == 200
    data = resp.json()

    assert data["tenant_id"] == "tenant-alpha"
    assert data["display_name"] == "Alpha Cafe"
    assert data["entitlements"] == ["review_manager"]
    assert data["brand_accent"] == "#174D3A"


def test_04_stage2_shared_profile_returns_authoritative_entitlements_product_b(test_db):
    """GET /shared-profile for tenant-beta returns ['digital_card'] entitlements."""
    client = create_authenticated_client(test_db["multi_user_id"], "tenant-beta", test_db["store"])
    resp = client.get("/api/businesses/tenant-beta/shared-profile")
    assert resp.status_code == 200
    data = resp.json()

    assert data["tenant_id"] == "tenant-beta"
    assert data["display_name"] == "Beta Studio"
    assert data["entitlements"] == ["digital_card"]
    assert data["brand_accent"] == "#078BFF"


def test_05_stage2_shared_profile_returns_both_entitlements(test_db):
    """GET /shared-profile for tenant-dual returns both entitlements."""
    client = create_authenticated_client(test_db["staff_user_id"], "tenant-dual", test_db["store"])
    resp = client.get("/api/businesses/tenant-dual/shared-profile")
    assert resp.status_code == 200
    data = resp.json()

    assert data["tenant_id"] == "tenant-dual"
    assert set(data["entitlements"]) == {"review_manager", "digital_card"}
    assert data["branch_name"] == "Headquarters"


def test_06_stage2_shared_profile_returns_empty_entitlements_when_none(test_db):
    """GET /shared-profile for tenant-none returns empty entitlements list."""
    store = test_db["store"]
    # Add membership for multi_user in tenant-none
    store.add_membership(test_db["multi_user_id"], "tenant-none", "owner")

    client = create_authenticated_client(test_db["multi_user_id"], "tenant-none", store)
    resp = client.get("/api/businesses/tenant-none/shared-profile")
    assert resp.status_code == 200
    data = resp.json()

    assert data["tenant_id"] == "tenant-none"
    assert data["entitlements"] == []


def test_07_tenant_switching_updates_active_tenant_and_entitlements(test_db):
    """POST /api/auth/switch-tenant updates session and reloads distinct tenant context."""
    client = create_authenticated_client(test_db["multi_user_id"], "tenant-alpha", test_db["store"])

    # Verify initial active tenant is Alpha (Product A)
    s1 = client.get("/api/auth/session").json()
    assert s1["active_tenant"]["id"] == "tenant-alpha"
    p1 = client.get("/api/businesses/tenant-alpha/shared-profile").json()
    assert p1["entitlements"] == ["review_manager"]

    # Switch to Beta (Product B)
    switch_resp = client.post("/api/auth/switch-tenant", json={"tenant_id": "tenant-beta"})
    assert switch_resp.status_code == 200
    s2 = switch_resp.json()
    assert s2["active_tenant"]["id"] == "tenant-beta"
    assert s2["active_tenant"]["role"] == "manager"

    # Verify new shared profile reflects Beta's digital_card entitlement
    p2 = client.get("/api/businesses/tenant-beta/shared-profile").json()
    assert p2["entitlements"] == ["digital_card"]
    assert p2["display_name"] == "Beta Studio"


def test_08_staff_can_read_shared_profile_but_cannot_update(test_db):
    """Staff can GET shared-profile, but PUT returns 403 Forbidden."""
    client = create_authenticated_client(test_db["staff_user_id"], "tenant-dual", test_db["store"])

    # Read succeeds
    get_resp = client.get("/api/businesses/tenant-dual/shared-profile")
    assert get_resp.status_code == 200

    # Write is forbidden for staff
    put_resp = client.put(
        "/api/businesses/tenant-dual/shared-profile",
        json={"display_name": "Hacked Display Name"}
    )
    assert put_resp.status_code == 403


def test_09_cross_tenant_access_strictly_rejected(test_db):
    """User in tenant-alpha cannot read tenant-dual shared profile."""
    client = create_authenticated_client(test_db["multi_user_id"], "tenant-alpha", test_db["store"])

    # Attempt cross-tenant access to tenant-dual
    resp = client.get("/api/businesses/tenant-dual/shared-profile")
    assert resp.status_code == 403


def test_10_logout_clears_session_cookie(test_db):
    """POST /api/auth/logout invalidates session and subsequent session check returns 401."""
    client = create_authenticated_client(test_db["multi_user_id"], "tenant-alpha", test_db["store"])

    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    # Next session check must be 401
    session_resp = client.get("/api/auth/session")
    assert session_resp.status_code == 401
