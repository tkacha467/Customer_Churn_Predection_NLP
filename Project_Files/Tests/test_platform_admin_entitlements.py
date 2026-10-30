"""
Unit & Integration Tests for Vraja Phase 8.4:
Platform Admin, Product Packaging & Entitlement Management:
- Platform Admin Authorization & RBAC enforcement on all /api/platform/ endpoints
- Anonymous, staff, and regular owner rejection (401 / 403)
- Owner self-assignment denial (cannot escalate entitlements via /businesses/{id}/config)
- Platform onboarding with each product package (Reviews only, Card only, Both)
- Validation of entitlement choices during onboarding and updating
- Immediate real-time enforcement of runtime entitlement switching
- Immediate real-time enforcement of tenant suspension and reactivation
- User session context reporting is_platform_admin flag correctly
"""

import os
import time
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


@pytest.fixture
def admin_test_setup(tmp_path, monkeypatch):
    """Sets up an isolated SQLite database and clears caches for clean testing."""
    db_path = tmp_path / "test_admin_reviews.sqlite3"
    docs_path = tmp_path / "test_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))

    # 1. Seed Platform Superadmin
    admin_user = store.create_user(
        email="superadmin@vraja.test",
        password_hash=hash_password("SuperSecretAdminPass123!"),
        display_name="Vraja Superadmin",
        is_active=1,
        is_platform_admin=1,
    )

    # 2. Seed Regular Tenant and Owner
    owner_user = store.create_user(
        email="owner@bistrot.test",
        password_hash=hash_password("OwnerPassword123!"),
        display_name="Bistrot Owner",
        is_active=1,
        is_platform_admin=0,
    )

    tenant_record = store.upsert_tenant({
        "id": "le_bistrot",
        "business_name": "Le Bistrot Parisien",
        "status": "active",
        "platform": "google",
        "review_url": "https://g.page/r/lebistrot",
        "category": "Restaurant",
        "entitlements": ["review_manager", "digital_card"],
    })
    store.add_membership(owner_user["id"], "le_bistrot", role="owner")

    # Seed published profile for le_bistrot so public card is available
    store.upsert_business_profile("le_bistrot", {
        "tagline": "Authentic French Cuisine",
        "phone_number": "+1234567890",
        "is_published": 1,
    })

    def create_session(user_id: str, tenant_id: str) -> str:
        raw_token = generate_session_token()
        hashed = hash_token(raw_token)
        now = time.time()
        with store._connect() as db:
            db.execute(
                "INSERT INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (hashed, user_id, tenant_id, now, now + SESSION_TTL_SECONDS)
            )
        return raw_token

    admin_token = create_session(admin_user["id"], "default_business")
    owner_token = create_session(owner_user["id"], "le_bistrot")

    return {
        "store": store,
        "admin_user": admin_user,
        "owner_user": owner_user,
        "admin_token": admin_token,
        "owner_token": owner_token,
        "tenant": tenant_record,
    }


def test_anonymous_rejected_from_platform_endpoints(admin_test_setup):
    """Anonymous requests to all platform admin endpoints must return 401 or 403."""
    with TestClient(app) as client:
        # GET /platform/tenants
        res = client.get("/api/platform/tenants")
        assert res.status_code in (401, 403)

        # POST /platform/tenants
        res = client.post("/api/platform/tenants", json={
            "tenant_id": "test_anon",
            "business_name": "Anon Business",
            "owner_email": "anon@test.com",
            "owner_password": "password123456",
        })
        assert res.status_code in (401, 403)

        # GET /platform/tenants/{id}
        res = client.get("/api/platform/tenants/le_bistrot")
        assert res.status_code in (401, 403)

        # PATCH /platform/tenants/{id}/status
        res = client.patch("/api/platform/tenants/le_bistrot/status", json={"status": "suspended"})
        assert res.status_code in (401, 403)

        # PATCH /platform/tenants/{id}/entitlements
        res = client.patch("/api/platform/tenants/le_bistrot/entitlements", json={"entitlements": ["review_manager"]})
        assert res.status_code in (401, 403)


def test_regular_owner_forbidden_from_platform_endpoints(admin_test_setup):
    """Authenticated business owners without platform admin privileges must receive 403 Forbidden."""
    owner_token = admin_test_setup["owner_token"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, owner_token)

        # List tenants
        res = client.get("/api/platform/tenants")
        assert res.status_code == 403
        assert "Platform administrator" in res.json().get("detail", "")

        # Onboard tenant
        res = client.post("/api/platform/tenants", json={
            "tenant_id": "hacker_tenant",
            "business_name": "Hacker Business",
            "owner_email": "hacker@test.com",
            "owner_password": "password123456",
        })
        assert res.status_code == 403

        # Get tenant details
        res = client.get("/api/platform/tenants/le_bistrot")
        assert res.status_code == 403

        # Status update
        res = client.patch("/api/platform/tenants/le_bistrot/status", json={"status": "suspended"})
        assert res.status_code == 403

        # Entitlements update
        res = client.patch("/api/platform/tenants/le_bistrot/entitlements", json={"entitlements": ["review_manager"]})
        assert res.status_code == 403


def test_tenant_owner_cannot_self_assign_entitlements_via_business_config(admin_test_setup):
    """Regular tenant owners cannot elevate or alter their entitlements via POST /businesses/{id}/config."""
    store = admin_test_setup["store"]
    owner_token = admin_test_setup["owner_token"]

    # Start tenant with only review_manager
    tenant = store.get_tenant("le_bistrot")
    tenant["entitlements"] = ["review_manager"]
    store.upsert_tenant(tenant)

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, owner_token)

        # Owner tries to self-grant digital_card entitlement
        payload = {
            "business_name": "Le Bistrot Parisien Updated",
            "google_review_url": "https://g.page/r/lebistrot",
            "entitlements": ["review_manager", "digital_card"],
            "category": "Restaurant",
        }
        res = client.post("/api/businesses/le_bistrot/config", json=payload)
        assert res.status_code == 200

        # Verify in database that entitlements were NOT changed
        updated = store.get_tenant("le_bistrot")
        assert updated["entitlements"] == ["review_manager"]
        assert "digital_card" not in updated["entitlements"]


def test_platform_admin_can_list_tenants_with_metadata(admin_test_setup):
    """Platform superadmin can list all tenants, including owner email and metadata."""
    admin_token = admin_test_setup["admin_token"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, admin_token)

        res = client.get("/api/platform/tenants")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        bistrot = next((t for t in data if t["id"] == "le_bistrot"), None)
        assert bistrot is not None
        assert bistrot["business_name"] == "Le Bistrot Parisien"
        assert bistrot["owner_email"] == "owner@bistrot.test"
        assert "review_manager" in bistrot["entitlements"]
        assert "digital_card" in bistrot["entitlements"]


def test_platform_admin_can_onboard_tenants_with_each_package(admin_test_setup):
    """Platform admin can onboard new customer tenants with Reviews Only, Card Only, or Both."""
    admin_token = admin_test_setup["admin_token"]
    store = admin_test_setup["store"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, admin_token)

        # 1. Onboard Review System Only
        res1 = client.post("/api/platform/tenants", json={
            "tenant_id": "review_only_cafe",
            "business_name": "Review Only Cafe",
            "owner_email": "owner@reviewonly.test",
            "owner_password": "SecurePassword123!",
            "category": "Cafe",
            "review_url": "https://g.page/r/reviewonly",
            "entitlements": ["review_manager"],
        })
        assert res1.status_code == 201
        data1 = res1.json()
        assert data1["tenant_id"] == "review_only_cafe"
        assert data1["entitlements"] == ["review_manager"]
        assert store.get_tenant("review_only_cafe")["entitlements"] == ["review_manager"]

        # 2. Onboard Digital Card Only
        res2 = client.post("/api/platform/tenants", json={
            "tenant_id": "card_only_shop",
            "business_name": "Card Only Shop",
            "owner_email": "owner@cardonly.test",
            "owner_password": "SecurePassword123!",
            "category": "Boutique",
            "entitlements": ["digital_card"],
        })
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["tenant_id"] == "card_only_shop"
        assert data2["entitlements"] == ["digital_card"]
        assert store.get_tenant("card_only_shop")["entitlements"] == ["digital_card"]

        # 3. Onboard Combined Full Suite
        res3 = client.post("/api/platform/tenants", json={
            "tenant_id": "full_suite_hotel",
            "business_name": "Full Suite Grand Hotel",
            "owner_email": "owner@hotel.test",
            "owner_password": "SecurePassword123!",
            "category": "Hotel",
            "entitlements": ["review_manager", "digital_card"],
        })
        assert res3.status_code == 201
        data3 = res3.json()
        assert set(data3["entitlements"]) == {"review_manager", "digital_card"}

        # 4. Reject invalid entitlement
        res4 = client.post("/api/platform/tenants", json={
            "tenant_id": "invalid_ent_biz",
            "business_name": "Invalid Biz",
            "owner_email": "owner@invalid.test",
            "owner_password": "SecurePassword123!",
            "entitlements": ["unsupported_crm_module"],
        })
        assert res4.status_code == 422


def test_platform_admin_get_tenant_details(admin_test_setup):
    """GET /api/platform/tenants/{id} returns comprehensive tenant details or 404."""
    admin_token = admin_test_setup["admin_token"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, admin_token)

        # Existing tenant
        res = client.get("/api/platform/tenants/le_bistrot")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "le_bistrot"
        assert data["business_name"] == "Le Bistrot Parisien"
        assert data["owner_email"] == "owner@bistrot.test"
        assert "profile" in data

        # Nonexistent tenant
        res_404 = client.get("/api/platform/tenants/nonexistent_xyz")
        assert res_404.status_code == 404


def test_runtime_entitlement_switching_and_immediate_enforcement(admin_test_setup):
    """Platform admin updating entitlements immediately gates or grants module access."""
    admin_token = admin_test_setup["admin_token"]
    owner_token = admin_test_setup["owner_token"]

    with TestClient(app) as client:
        # Step 1: Currently tenant has both modules. Owner can access profile and review link.
        client.cookies.set(OWNER_COOKIE, owner_token)
        res_prof = client.get("/api/businesses/le_bistrot/profile")
        assert res_prof.status_code == 200
        res_rev = client.get("/api/businesses/le_bistrot/review-link")
        assert res_rev.status_code == 200

        # Step 2: Platform Admin switches package to Review Only
        client.cookies.set(OWNER_COOKIE, admin_token)
        patch_res = client.patch(
            "/api/platform/tenants/le_bistrot/entitlements",
            json={"entitlements": ["review_manager"]}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["entitlements"] == ["review_manager"]

        # Step 3: Owner immediate check - Digital Card profile must return 403 Forbidden
        client.cookies.set(OWNER_COOKIE, owner_token)
        res_prof_blocked = client.get("/api/businesses/le_bistrot/profile")
        assert res_prof_blocked.status_code == 403
        assert "digital_card" in res_prof_blocked.json().get("detail", "")

        # But Review Link is still 200 OK
        res_rev_ok = client.get("/api/businesses/le_bistrot/review-link")
        assert res_rev_ok.status_code == 200

        # Step 4: Platform Admin switches package to Digital Card Only
        client.cookies.set(OWNER_COOKIE, admin_token)
        patch_res2 = client.patch(
            "/api/platform/tenants/le_bistrot/entitlements",
            json={"entitlements": ["digital_card"]}
        )
        assert patch_res2.status_code == 200

        # Step 5: Owner immediate check - Digital Card profile now works (200 OK), but Review Link returns 403
        client.cookies.set(OWNER_COOKIE, owner_token)
        res_prof_ok = client.get("/api/businesses/le_bistrot/profile")
        assert res_prof_ok.status_code == 200

        res_rev_blocked = client.get("/api/businesses/le_bistrot/review-link")
        assert res_rev_blocked.status_code == 403
        assert "review_manager" in res_rev_blocked.json().get("detail", "")

        # Step 6: Platform Admin restores Full Suite
        client.cookies.set(OWNER_COOKIE, admin_token)
        client.patch(
            "/api/platform/tenants/le_bistrot/entitlements",
            json={"entitlements": ["review_manager", "digital_card"]}
        )

        # Both endpoints work again immediately
        client.cookies.set(OWNER_COOKIE, owner_token)
        assert client.get("/api/businesses/le_bistrot/profile").status_code == 200
        assert client.get("/api/businesses/le_bistrot/review-link").status_code == 200


def test_tenant_suspension_and_reactivation_immediate_enforcement(admin_test_setup):
    """Platform admin suspending a tenant immediately shuts down card, review, and owner access."""
    admin_token = admin_test_setup["admin_token"]
    owner_token = admin_test_setup["owner_token"]

    with TestClient(app) as client:
        # Step 1: Active tenant public card and review link are accessible
        res_card = client.get("/api/businesses/le_bistrot/card")
        assert res_card.status_code == 200
        assert client.get("/api/businesses/le_bistrot/review-link").status_code == 200

        # Step 2: Platform Admin suspends the tenant
        client.cookies.set(OWNER_COOKIE, admin_token)
        res_suspend = client.patch(
            "/api/platform/tenants/le_bistrot/status",
            json={"status": "suspended"}
        )
        assert res_suspend.status_code == 200
        assert res_suspend.json()["status"] == "suspended"

        # Step 3: Immediate check - Public card is 404 (suppressed when suspended)
        client.cookies.delete(OWNER_COOKIE)
        res_card_blocked = client.get("/api/businesses/le_bistrot/card")
        assert res_card_blocked.status_code == 404

        # Review link is 403 Forbidden
        res_rev_blocked = client.get("/api/businesses/le_bistrot/review-link")
        assert res_rev_blocked.status_code == 403
        assert "suspended" in res_rev_blocked.json().get("detail", "").lower()

        # Existing owner session accessing owner endpoints is 403 Forbidden
        client.cookies.set(OWNER_COOKIE, owner_token)
        res_owner_prof = client.put(
            "/api/businesses/le_bistrot/profile",
            json={"tagline": "Hacked Profile"}
        )
        assert res_owner_prof.status_code == 403
        assert "suspended" in res_owner_prof.json().get("detail", "").lower()

        # Owner attempting fresh login while tenant is suspended is rejected (403 Forbidden)
        client.cookies.delete(OWNER_COOKIE)
        login_res = client.post("/api/auth/login", json={
            "email": "owner@bistrot.test",
            "password": "OwnerPassword123!"
        })
        assert login_res.status_code == 403
        assert any(term in login_res.json().get("detail", "").lower() for term in ("suspended", "no business access"))

        # Step 4: Platform Admin reactivates the tenant
        client.cookies.set(OWNER_COOKIE, admin_token)
        res_reactivate = client.patch(
            "/api/platform/tenants/le_bistrot/status",
            json={"status": "active"}
        )
        assert res_reactivate.status_code == 200
        assert res_reactivate.json()["status"] == "active"

        # Step 5: Immediate recovery - Public card works again
        client.cookies.delete(OWNER_COOKIE)
        assert client.get("/api/businesses/le_bistrot/card").status_code == 200

        # Owner login succeeds
        login_after = client.post("/api/auth/login", json={
            "email": "owner@bistrot.test",
            "password": "OwnerPassword123!"
        })
        assert login_after.status_code == 200


def test_auth_session_reports_platform_admin_flag_accurately(admin_test_setup):
    """GET /api/auth/session accurately reflects is_platform_admin for superadmins and owners."""
    admin_token = admin_test_setup["admin_token"]
    owner_token = admin_test_setup["owner_token"]

    with TestClient(app) as client:
        # Regular owner session
        client.cookies.set(OWNER_COOKIE, owner_token)
        res_owner = client.get("/api/auth/session")
        assert res_owner.status_code == 200
        owner_data = res_owner.json()
        assert owner_data["authenticated"] is True
        assert owner_data["user"]["is_platform_admin"] is False

        # Platform superadmin session
        client.cookies.set(OWNER_COOKIE, admin_token)
        res_admin = client.get("/api/auth/session")
        assert res_admin.status_code == 200
        admin_data = res_admin.json()
        assert admin_data["authenticated"] is True
        assert admin_data["user"]["is_platform_admin"] is True


def test_legacy_tenant_without_explicit_entitlements_gets_only_review_manager(admin_test_setup):
    """
    Existing/legacy tenants created before Phase 8 (with NULL or missing entitlements_json)
    must receive ONLY review_manager and NOT accidentally receive premium digital_card.
    """
    store = admin_test_setup["store"]
    now = time.time()

    # Simulate raw legacy row with NULL entitlements_json
    with store._connect() as db:
        db.execute("""
            INSERT INTO tenants (
                id, business_name, status, platform, review_url, branch,
                category, description, topics_json, primary_accent, domain,
                entitlements_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
        """, (
            "legacy_pre_phase8_cafe", "Legacy Pre-Phase8 Cafe", "active", "google",
            "https://g.page/r/legacy", "", "Cafe", "Old Cafe", "[]", "#f97316", "", now, now
        ))

    # Create owner membership for the legacy tenant
    legacy_owner = store.create_user(
        email="legacy_owner@test.com",
        password_hash=hash_password("LegacyPassword123!"),
        display_name="Legacy Owner",
        is_active=1,
        is_platform_admin=0,
    )
    store.add_membership(legacy_owner["id"], "legacy_pre_phase8_cafe", role="owner")

    # 1. Verify storage layer resolves to ['review_manager'] only
    tenant = store.get_tenant("legacy_pre_phase8_cafe")
    assert tenant["entitlements"] == ["review_manager"]

    # 2. Verify entitlement engine gates
    from Backend.app.core.entitlements.entitlements import check_tenant_entitlement
    assert check_tenant_entitlement("legacy_pre_phase8_cafe", "review_manager") is True
    assert check_tenant_entitlement("legacy_pre_phase8_cafe", "digital_card") is False

    # 3. Verify API enforcement: review link is 200, card endpoints are 403 Forbidden
    raw_token = generate_session_token()
    hashed = hash_token(raw_token)
    with store._connect() as db:
        db.execute(
            "INSERT INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (hashed, legacy_owner["id"], "legacy_pre_phase8_cafe", now, now + SESSION_TTL_SECONDS)
        )

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, raw_token)

        # Review link succeeds
        rev_res = client.get("/api/businesses/legacy_pre_phase8_cafe/review-link")
        assert rev_res.status_code == 200

        # Protected Digital Card profile management fails with 403
        prof_res = client.put(
            "/api/businesses/legacy_pre_phase8_cafe/profile",
            json={"tagline": "Attempting Card"}
        )
        assert prof_res.status_code == 403
        assert "digital_card" in prof_res.json().get("detail", "")

        # Document listing fails with 403
        doc_res = client.get("/api/businesses/legacy_pre_phase8_cafe/documents")
        assert doc_res.status_code == 403
        assert "digital_card" in doc_res.json().get("detail", "")
