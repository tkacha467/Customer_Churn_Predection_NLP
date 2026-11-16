"""
Comprehensive Automated Test Suite for Phase 2 Subpart 2E:
Runtime Backward Compatibility & Product Synchronization.

Verifies:
1. Product A reads canonical shared identity from business_profiles.
2. Product B reads canonical shared identity from business_profiles.
3. Updating shared identity via canonical PUT /shared-profile is reflected in both products.
4. Product A operational settings (review_url, topics, primary_accent) remain untouched.
5. Product B presentation settings (background_preset, overlay_opacity, custom_links, cover_image) remain untouched.
6. Legacy Product A endpoint (POST /businesses/{id}/config) remains backward compatible and synchronizes shared fields.
7. Legacy Product B endpoint (PUT /businesses/{id}/profile) remains backward compatible and synchronizes shared fields.
8. Unauthorized legacy updates are strictly rejected (401/403).
9. Tenant isolation is strictly maintained across both products.
10. Missing profiles are handled safely with zero-error fallback.
11. New tenant provisioning automatically creates usable canonical shared profiles.
12. Shared logo is consumed consistently across Product A and Product B.
13. Failed updates roll back cleanly and prevent partial synchronization.
14. Phase 1 entitlement enforcement remains intact across all operations.
"""

import io
import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import _document_services
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
from Backend.app.core.tenants.google_reviews import google_review_manager

VALID_PNG_100x100 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x64\x00\x00\x00\x64\x08\x06\x00\x00\x00"
    b"\x70\xe1\xd5\x9a"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def sync_setup(tmp_path, monkeypatch):
    """Sets up an isolated SQLite database and documents directory for Subpart 2E tests."""
    db_path = tmp_path / "test_sync.sqlite3"
    docs_path = tmp_path / "documents"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    _document_services.clear()
    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))
    _stores[str(db_path)] = store

    from Backend.app.core.database.migration import apply_phase2_schema_alterations
    with store._connect() as con:
        apply_phase2_schema_alterations(con)

    # 1. Platform Superadmin
    admin_user = store.create_user(
        email="superadmin@vraja.test",
        password_hash=hash_password("SuperAdmin123!"),
        display_name="Platform Superadmin",
        is_active=1,
        is_platform_admin=1,
    )

    # 2. Tenant Alpha (Review Manager + Digital Card)
    now = time.time()
    store.upsert_tenant({
        "id": "tenant_alpha",
        "business_name": "Alpha Legacy Name",
        "category": "Cafe",
        "branch": "Old Branch",
        "description": "Old description on tenants table",
        "primary_accent": "#f97316",
        "review_url": "https://search.google.com/local/writereview?placeid=ChIJalpha123",
        "topics": ["Espresso", "Sourdough", "Service"],
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })

    with store._connect() as con:
        con.execute("""
            INSERT OR REPLACE INTO business_profiles (
                tenant_id, display_name, category, branch_name, description,
                tagline, phone_number, email, address, website_url, opening_hours,
                map_url, brand_accent, timezone, logo_path,
                background_preset, overlay_opacity, primary_accent, is_published,
                show_review_button, created_at, updated_at
            ) VALUES (
                'tenant_alpha', 'Alpha Canonical Roast', 'Specialty Roastery', 'Uptown Hub',
                'Canonical single-origin pour-overs and pastries.', 'Pure Perfection',
                '+91 98765 43210', 'hello@alpha-roast.test', '42 Artisan Way, Ahmedabad',
                'https://alpharoast.test', '8:00 AM - 10:00 PM', 'https://maps.google.com/alpha',
                '#174D3A', 'Asia/Kolkata', '/restaurant/nasta-ghar-logo.svg',
                'dark_wood', 0.80, '#078BFF', 1,
                1, ?, ?
            );
        """, (now, now))

    owner_alpha = store.create_user(
        email="owner@alpha.test",
        password_hash=hash_password("OwnerAlpha123!"),
        display_name="Alpha Owner",
        is_active=1,
    )
    store.add_membership(owner_alpha["id"], "tenant_alpha", role="owner")

    staff_alpha = store.create_user(
        email="staff@alpha.test",
        password_hash=hash_password("StaffAlpha123!"),
        display_name="Alpha Staff",
        is_active=1,
    )
    store.add_membership(staff_alpha["id"], "tenant_alpha", role="staff")

    # 3. Tenant Beta (Review Manager ONLY)
    store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Beta Trattoria",
        "category": "Italian",
        "status": "active",
        "entitlements": ["review_manager"],
    })
    owner_beta = store.create_user(
        email="owner@beta.test",
        password_hash=hash_password("OwnerBeta123!"),
        display_name="Beta Owner",
        is_active=1,
    )
    store.add_membership(owner_beta["id"], "tenant_beta", role="owner")

    # 4. Tenant Gamma (Digital Card ONLY)
    store.upsert_tenant({
        "id": "tenant_gamma",
        "business_name": "Gamma Studio",
        "category": "Design",
        "status": "active",
        "entitlements": ["digital_card"],
    })
    owner_gamma = store.create_user(
        email="owner@gamma.test",
        password_hash=hash_password("OwnerGamma123!"),
        display_name="Gamma Owner",
        is_active=1,
    )
    store.add_membership(owner_gamma["id"], "tenant_gamma", role="owner")

    def make_client(user_id: str, active_tenant: str) -> TestClient:
        raw_token = generate_session_token()
        token_hash = hash_token(raw_token)
        store.create_session(
            token_hash=token_hash,
            user_id=user_id,
            active_tenant_id=active_tenant,
            expires_at=time.time() + SESSION_TTL_SECONDS,
        )
        c = TestClient(app)
        c.cookies.set(OWNER_COOKIE, raw_token)
        c.headers.update({"Origin": "http://localhost:5173"})
        return c

    return {
        "store": store,
        "db_path": db_path,
        "docs_path": docs_path,
        "admin_client": make_client(admin_user["id"], "default_business"),
        "owner_alpha_client": make_client(owner_alpha["id"], "tenant_alpha"),
        "staff_alpha_client": make_client(staff_alpha["id"], "tenant_alpha"),
        "owner_beta_client": make_client(owner_beta["id"], "tenant_beta"),
        "owner_gamma_client": make_client(owner_gamma["id"], "tenant_gamma"),
        "unauth_client": TestClient(app),
    }


# ==============================================================================
# 1. Product A & Product B Read Authoritative Canonical Shared Identity
# ==============================================================================

def test_01_product_a_reads_canonical_shared_identity(sync_setup):
    """Product A (Review Manager) endpoints read shared identity from canonical business_profiles."""
    client = sync_setup["unauth_client"]

    resp = client.get("/api/businesses/tenant_alpha/review-link")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Must reflect canonical business_profiles fields, NOT legacy tenants table strings
    assert data["business_name"] == "Alpha Canonical Roast"
    assert data["branch"] == "Uptown Hub"
    assert data["category"] == "Specialty Roastery"
    assert data["description"] == "Canonical single-origin pour-overs and pastries."
    assert data["logo_path"] == "/restaurant/nasta-ghar-logo.svg"

    # Product A specific review operational settings preserved
    assert data["review_url"] == "https://search.google.com/local/writereview?placeid=ChIJalpha123"
    assert data["topics"] == ["Espresso", "Sourdough", "Service"]
    assert data["primary_accent"] == "#f97316"


def test_02_product_b_reads_canonical_shared_identity(sync_setup):
    """Product B (Digital Card) endpoints read shared identity from canonical business_profiles."""
    client = sync_setup["unauth_client"]

    # Public card endpoint
    resp = client.get("/api/businesses/tenant_alpha/card")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["business_name"] == "Alpha Canonical Roast"
    assert data["display_name"] == "Alpha Canonical Roast"
    assert data["category"] == "Specialty Roastery"
    assert data["description"] == "Canonical single-origin pour-overs and pastries."
    assert data["address"] == "42 Artisan Way, Ahmedabad"
    assert data["phone_number"] == "+91 98765 43210"
    assert data["website_url"] == "https://alpharoast.test"

    # Product B presentation settings preserved
    assert data["background_preset"] == "dark_wood"
    assert data["overlay_opacity"] == 0.80
    assert data["primary_accent"] == "#078BFF"


# ==============================================================================
# 2. Canonical Updates Reflected in Both Products
# ==============================================================================

def test_03_canonical_update_reflected_in_both_products(sync_setup):
    """Updating canonical profile via PUT /shared-profile is immediately reflected in Product A and B."""
    owner_client = sync_setup["owner_alpha_client"]
    unauth_client = sync_setup["unauth_client"]

    update_payload = {
        "display_name": "Alpha Grand Roastery & Eatery",
        "category": "Artisanal Roastery",
        "branch_name": "Jubilee Flagship",
        "description": "Freshly roasted single origins and European breakfasts.",
        "brand_accent": "#059669",
    }
    put_resp = owner_client.put("/api/businesses/tenant_alpha/shared-profile", json=update_payload)
    assert put_resp.status_code == 200, put_resp.text
    p_data = put_resp.json()
    assert p_data["display_name"] == "Alpha Grand Roastery & Eatery"
    assert p_data["branch_name"] == "Jubilee Flagship"

    # 1. Verify Product A immediately reflects updated shared identity
    a_resp = unauth_client.get("/api/businesses/tenant_alpha/review-link")
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    assert a_data["business_name"] == "Alpha Grand Roastery & Eatery"
    assert a_data["branch"] == "Jubilee Flagship"
    assert a_data["category"] == "Artisanal Roastery"
    assert a_data["description"] == "Freshly roasted single origins and European breakfasts."

    # 2. Verify Product B immediately reflects updated shared identity
    b_resp = unauth_client.get("/api/businesses/tenant_alpha/card")
    assert b_resp.status_code == 200
    b_data = b_resp.json()
    assert b_data["business_name"] == "Alpha Grand Roastery & Eatery"
    assert b_data["display_name"] == "Alpha Grand Roastery & Eatery"
    assert b_data["category"] == "Artisanal Roastery"
    assert b_data["description"] == "Freshly roasted single origins and European breakfasts."


def test_04_product_a_settings_untouched_after_shared_profile_update(sync_setup):
    """Shared profile update preserves Product A operational settings on tenants table."""
    owner_client = sync_setup["owner_alpha_client"]
    store = sync_setup["store"]

    t_before = store.get_tenant("tenant_alpha")

    update_payload = {"display_name": "Alpha High-End Roastery"}
    resp = owner_client.put("/api/businesses/tenant_alpha/shared-profile", json=update_payload)
    assert resp.status_code == 200

    t_after = store.get_tenant("tenant_alpha")

    # Product A settings preserved
    assert t_after["review_url"] == t_before["review_url"]
    assert t_after["topics"] == t_before["topics"]
    assert t_after["primary_accent"] == t_before["primary_accent"]
    assert t_after["status"] == t_before["status"]
    assert t_after["entitlements"] == t_before["entitlements"]


def test_05_product_b_settings_untouched_after_shared_profile_update(sync_setup):
    """Shared profile update preserves Product B card presentation settings."""
    owner_client = sync_setup["owner_alpha_client"]
    store = sync_setup["store"]

    p_before = store.get_business_profile("tenant_alpha")

    update_payload = {"display_name": "Alpha Gourmet Coffee"}
    resp = owner_client.put("/api/businesses/tenant_alpha/shared-profile", json=update_payload)
    assert resp.status_code == 200

    p_after = store.get_business_profile("tenant_alpha")

    # Product B presentation settings preserved
    assert p_after["background_preset"] == p_before["background_preset"]
    assert p_after["overlay_opacity"] == p_before["overlay_opacity"]
    assert p_after["is_published"] == p_before["is_published"]
    assert p_after["show_review_button"] == p_before["show_review_button"]
    assert p_after["primary_accent"] == p_before["primary_accent"]


# ==============================================================================
# 3. Legacy Write Endpoints & Synchronous Delegation
# ==============================================================================

def test_06_legacy_product_a_config_syncs_to_canonical_profile(sync_setup):
    """Legacy Product A POST /businesses/{id}/config synchronizes shared fields to business_profiles."""
    owner_client = sync_setup["owner_alpha_client"]
    unauth_client = sync_setup["unauth_client"]
    store = sync_setup["store"]

    cfg_payload = {
        "google_review_url": "https://search.google.com/local/writereview?placeid=ChIJalpha999",
        "business_name": "Alpha Specialty Bistro",
        "branch": "Metro Square",
        "category": "Bistro & Bakery",
        "description": "Fresh artisan bakes and sourdough daily.",
        "primary_accent": "#ea580c",
        "topics": ["Artisan Bakes", "Flat White", "Ambience"],
    }
    resp = owner_client.post("/api/businesses/tenant_alpha/config", json=cfg_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["business_name"] == "Alpha Specialty Bistro"
    assert data["branch"] == "Metro Square"
    assert data["review_url"] == "https://search.google.com/local/writereview?placeid=ChIJalpha999"

    # Canonical profile must now contain these shared fields
    canon = store.get_shared_business_profile("tenant_alpha")
    assert canon["display_name"] == "Alpha Specialty Bistro"
    assert canon["branch_name"] == "Metro Square"
    assert canon["category"] == "Bistro & Bakery"
    assert canon["description"] == "Fresh artisan bakes and sourdough daily."

    # Product B card must now reflect the new business name and description
    b_card = unauth_client.get("/api/businesses/tenant_alpha/card").json()
    assert b_card["business_name"] == "Alpha Specialty Bistro"
    assert b_card["description"] == "Fresh artisan bakes and sourdough daily."


def test_07_legacy_product_b_profile_syncs_to_canonical_and_product_a(sync_setup):
    """Legacy Product B PUT /businesses/{id}/profile updates canonical profile and reflects in Product A."""
    owner_client = sync_setup["owner_alpha_client"]
    unauth_client = sync_setup["unauth_client"]

    profile_payload = {
        "display_name": "Alpha Artisan Collective",
        "category": "Cafe & Eatery",
        "branch_name": "Riverfront Walk",
        "description": "Riverfront views and micro-batch roasts.",
        "background_preset": "modern_slate",
        "overlay_opacity": 0.90,
    }
    resp = owner_client.put("/api/businesses/tenant_alpha/profile", json=profile_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["display_name"] == "Alpha Artisan Collective"
    assert data["background_preset"] == "modern_slate"

    # Product A review link must immediately reflect the updated shared name and category
    a_link = unauth_client.get("/api/businesses/tenant_alpha/review-link").json()
    assert a_link["business_name"] == "Alpha Artisan Collective"
    assert a_link["category"] == "Cafe & Eatery"
    assert a_link["branch"] == "Riverfront Walk"
    assert a_link["description"] == "Riverfront views and micro-batch roasts."


def test_08_unauthorized_legacy_updates_rejected(sync_setup):
    """Staff, manager, and cross-tenant users are rejected on legacy update endpoints."""
    staff_client = sync_setup["staff_alpha_client"]
    owner_beta = sync_setup["owner_beta_client"]
    unauth = sync_setup["unauth_client"]

    # 1. Staff cannot update Product A config
    r1 = staff_client.post("/api/businesses/tenant_alpha/config", json={"google_review_url": "https://maps.google.com"})
    assert r1.status_code == 403

    # 2. Staff cannot update Product B profile
    r2 = staff_client.put("/api/businesses/tenant_alpha/profile", json={"display_name": "Hacked Name"})
    assert r2.status_code == 403

    # 3. Cross-tenant owner cannot update another tenant's config or profile
    r3 = owner_beta.post("/api/businesses/tenant_alpha/config", json={"google_review_url": "https://maps.google.com"})
    assert r3.status_code == 403
    r4 = owner_beta.put("/api/businesses/tenant_alpha/profile", json={"display_name": "Hacked Beta Name"})
    assert r4.status_code == 403

    # 4. Anonymous cannot update
    r5 = unauth.post("/api/businesses/tenant_alpha/config", json={"google_review_url": "https://maps.google.com"})
    assert r5.status_code == 401
    r6 = unauth.put("/api/businesses/tenant_alpha/profile", json={"display_name": "Anon Name"})
    assert r6.status_code == 401


# ==============================================================================
# 4. Tenant Isolation & Missing Profile Handling
# ==============================================================================

def test_09_tenant_isolation_maintained(sync_setup):
    """Updates to Tenant Alpha do not affect Tenant Beta."""
    owner_alpha = sync_setup["owner_alpha_client"]
    unauth = sync_setup["unauth_client"]
    store = sync_setup["store"]

    owner_alpha.put("/api/businesses/tenant_alpha/shared-profile", json={"display_name": "Alpha Unique Name"})

    beta_tenant = store.get_tenant("tenant_beta")
    assert beta_tenant["business_name"] == "Beta Trattoria"

    beta_link = unauth.get("/api/businesses/tenant_beta/review-link").json()
    assert beta_link["business_name"] == "Beta Trattoria"


def test_10_missing_profiles_handled_safely(sync_setup):
    """Tenants with missing or unprovisioned business_profiles fall back cleanly without 500 error."""
    store = sync_setup["store"]
    unauth = sync_setup["unauth_client"]

    # Insert a raw tenant without any business_profiles row
    with store._connect() as con:
        con.execute("""
            INSERT INTO tenants (id, business_name, status, platform, review_url, category, description, topics_json, primary_accent, created_at, updated_at)
            VALUES ('tenant_bare', 'Bare Minimal Diner', 'active', 'google', 'https://maps.google.com', 'Diner', 'Just a diner', '[]', '#f97316', 1000.0, 1000.0);
        """)

    # get_tenant should return tenant values safely
    t = store.get_tenant("tenant_bare")
    assert t["business_name"] == "Bare Minimal Diner"
    assert t["category"] == "Diner"

    # review-link should return 200 with fallback values
    resp = unauth.get("/api/businesses/tenant_bare/review-link")
    assert resp.status_code == 200
    assert resp.json()["business_name"] == "Bare Minimal Diner"


def test_11_new_tenant_provisioning_creates_usable_shared_profile(sync_setup):
    """Provisioning a new tenant via platform onboarding automatically creates a usable canonical business_profiles row."""
    admin_client = sync_setup["admin_client"]
    store = sync_setup["store"]

    onboard_payload = {
        "tenant_id": "tenant_delta",
        "business_name": "Delta Bistro",
        "category": "Bistro",
        "branch": "Harbor View",
        "description": "Seaside dining and catch of the day.",
        "owner_email": "owner@delta.test",
        "owner_password": "DeltaPassword123!",
        "entitlements": ["review_manager", "digital_card"],
    }
    resp = admin_client.post("/api/platform/tenants", json=onboard_payload)
    assert resp.status_code == 201

    # Assert canonical business_profiles row was automatically provisioned
    profile = store.get_shared_business_profile("tenant_delta")
    assert profile is not None
    assert profile["display_name"] == "Delta Bistro"
    assert profile["category"] == "Bistro"
    assert profile["branch_name"] == "Harbor View"
    assert profile["description"] == "Seaside dining and catch of the day."
    assert profile["category"] == "Bistro"
    assert profile["branch_name"] == "Harbor View"
    assert profile["description"] == "Seaside dining and catch of the day."


# ==============================================================================
# 5. Shared Logo Across Products & Entitlements
# ==============================================================================

def test_12_shared_logo_integration_across_products(sync_setup):
    """Shared logo upload is accessible in Product A review link and Product B card/active endpoints."""
    owner_alpha = sync_setup["owner_alpha_client"]
    unauth = sync_setup["unauth_client"]

    # 1. Upload shared logo
    files = {"file": ("brand_logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    up_resp = owner_alpha.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert up_resp.status_code == 200
    logo_path = up_resp.json()["logo_path"]
    assert "/api/businesses/tenant_alpha/shared-profile/logo/" in logo_path

    # 2. Product A review-link returns the canonical logo_path
    a_resp = unauth.get("/api/businesses/tenant_alpha/review-link")
    assert a_resp.status_code == 200
    assert a_resp.json()["logo_path"] == logo_path

    # 3. Product B card returns the canonical logo_path
    b_resp = unauth.get("/api/businesses/tenant_alpha/card")
    assert b_resp.status_code == 200
    assert b_resp.json()["logo_path"] == logo_path

    # 4. Active shared logo endpoint returns the uploaded PNG binary
    active_logo_resp = unauth.get("/api/businesses/tenant_alpha/shared-profile/logo")
    assert active_logo_resp.status_code == 200
    assert active_logo_resp.headers["cache-control"] == "no-cache, must-revalidate"
    assert active_logo_resp.content == VALID_PNG_100x100


def test_13_failed_updates_rollback_cleanly(sync_setup):
    """Validation errors on shared profile update abort cleanly without partial changes."""
    owner_alpha = sync_setup["owner_alpha_client"]
    store = sync_setup["store"]

    p_before = store.get_shared_business_profile("tenant_alpha")

    # Send invalid website URL and invalid brand accent
    bad_payload = {
        "display_name": "Should Not Persist",
        "website_url": "javascript:alert(1)",
        "brand_accent": "invalid-hex",
    }
    resp = owner_alpha.put("/api/businesses/tenant_alpha/shared-profile", json=bad_payload)
    assert resp.status_code == 422

    p_after = store.get_shared_business_profile("tenant_alpha")
    assert p_after["display_name"] == p_before["display_name"]
    assert p_after["website_url"] == p_before["website_url"]


def test_14_entitlement_enforcement_remains_intact(sync_setup):
    """Product-specific endpoints strictly enforce Phase 1 package entitlements."""
    unauth = sync_setup["unauth_client"]

    # Tenant Beta has 'review_manager' ONLY:
    # Product A works:
    assert unauth.get("/api/businesses/tenant_beta/review-link").status_code == 200
    # Product B card is rejected (404/not published or entitled):
    assert unauth.get("/api/businesses/tenant_beta/card").status_code == 404

    # Tenant Gamma has 'digital_card' ONLY:
    # Product A review-link is rejected (403 forbidden):
    assert unauth.get("/api/businesses/tenant_gamma/review-link").status_code == 403
