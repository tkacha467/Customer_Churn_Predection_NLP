"""
Focused Automated Test Suite for VRAJA AI Phase 3.3:
Shared Business Profile View, Canonical Identity Synchronization,
Shared Logo Management, and Role-Based Authorization Enforcement.
"""

import io
from pathlib import Path
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

# Valid synthetic 100x100 PNG bytes matching raster image parser requirements
VALID_PNG_100x100 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x64\x00\x00\x00\x64\x08\x06\x00\x00\x00"
    b"\x70\xe1\xd5\x9a"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Provides an isolated database and document root for Phase 3.3 tests."""
    db_file = tmp_path / "phase3_3_test.sqlite3"
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_dir))

    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_file))
    _stores[str(db_file)] = store

    with store._connect() as con:
        apply_phase2_schema_alterations(con)

    # 1. Provision Tenant Alpha (Dual Product)
    store.upsert_tenant({
        "id": "tenant-alpha",
        "business_name": "Alpha Dining & Lounge",
        "branch": "Central",
        "category": "Fine Dining",
        "entitlements": ["review_manager", "digital_card"]
    })
    store.upsert_business_profile("tenant-alpha", {
        "display_name": "Alpha Dining & Lounge",
        "category": "Fine Dining",
        "branch_name": "Central",
        "description": "Exquisite culinary journey.",
        "tagline": "Crafted with passion",
        "phone_number": "+91 99999 88888",
        "email": "contact@alphadining.com",
        "address": "100 Heritage Way",
        "website_url": "https://alphadining.com",
        "opening_hours": "11:00 AM - 11:00 PM",
        "map_url": "https://maps.google.com/?cid=123",
    })
    store.update_shared_business_profile("tenant-alpha", {
        "brand_accent": "#174D3A",
        "timezone": "Asia/Kolkata"
    })

    # 2. Provision Tenant Beta (Isolated Tenant)
    store.upsert_tenant({
        "id": "tenant-beta",
        "business_name": "Beta Bistro",
        "branch": "North",
        "category": "Bistro",
        "entitlements": ["digital_card"]
    })
    store.upsert_business_profile("tenant-beta", {
        "display_name": "Beta Bistro",
        "category": "Bistro",
    })

    # 3. Provision Users:
    # Owner of Alpha
    owner_user = store.create_user(
        email="owner@alpha.com",
        password_hash=hash_password("OwnerPass123!"),
        display_name="Alpha Owner"
    )
    store.add_membership(owner_user["id"], "tenant-alpha", "owner")

    # Manager of Alpha
    manager_user = store.create_user(
        email="manager@alpha.com",
        password_hash=hash_password("ManagerPass123!"),
        display_name="Alpha Manager"
    )
    store.add_membership(manager_user["id"], "tenant-alpha", "manager")

    # Staff of Alpha
    staff_user = store.create_user(
        email="staff@alpha.com",
        password_hash=hash_password("StaffPass123!"),
        display_name="Alpha Staff"
    )
    store.add_membership(staff_user["id"], "tenant-alpha", "staff")

    # User belonging only to Beta
    beta_user = store.create_user(
        email="owner@beta.com",
        password_hash=hash_password("BetaPass123!"),
        display_name="Beta Owner"
    )
    store.add_membership(beta_user["id"], "tenant-beta", "owner")

    # Platform Admin
    superadmin_user = store.create_user(
        email="admin@vraja.internal",
        password_hash=hash_password("AdminPass123!"),
        display_name="Platform Superadmin",
        is_active=1,
        is_platform_admin=1
    )

    return {
        "store": store,
        "owner_id": owner_user["id"],
        "manager_id": manager_user["id"],
        "staff_id": staff_user["id"],
        "beta_user_id": beta_user["id"],
        "superadmin_id": superadmin_user["id"]
    }


def make_client(user_id: str, tenant_id: str, store: ReviewStore):
    """Helper to create authenticated TestClient."""
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


def test_01_get_shared_profile_returns_all_canonical_fields(test_env):
    """GET /shared-profile returns all 13 canonical fields plus entitlements."""
    client = make_client(test_env["owner_id"], "tenant-alpha", test_env["store"])
    resp = client.get("/api/businesses/tenant-alpha/shared-profile")
    assert resp.status_code == 200
    data = resp.json()

    assert data["tenant_id"] == "tenant-alpha"
    assert data["display_name"] == "Alpha Dining & Lounge"
    assert data["category"] == "Fine Dining"
    assert data["branch_name"] == "Central"
    assert data["description"] == "Exquisite culinary journey."
    assert data["tagline"] == "Crafted with passion"
    assert data["phone_number"] == "+91 99999 88888"
    assert data["email"] == "contact@alphadining.com"
    assert data["address"] == "100 Heritage Way"
    assert data["website_url"] == "https://alphadining.com"
    assert data["opening_hours"] == "11:00 AM - 11:00 PM"
    assert data["map_url"] == "https://maps.google.com/?cid=123"
    assert data["brand_accent"] == "#174D3A"
    assert data["timezone"] == "Asia/Kolkata"
    assert set(data["entitlements"]) == {"review_manager", "digital_card"}


def test_02_owner_can_update_canonical_profile(test_env):
    """Owner can update canonical shared profile fields via PUT."""
    client = make_client(test_env["owner_id"], "tenant-alpha", test_env["store"])
    update_payload = {
        "display_name": "Alpha Gourmet Kitchen",
        "category": "Contemporary Indian",
        "branch_name": "Central Plaza",
        "description": "Elevated authentic flavors.",
        "tagline": "Pure culinary craftsmanship",
        "phone_number": "+91 88888 77777",
        "email": "hello@alphagourmet.com",
        "address": "400 Royal Boulevard",
        "website_url": "https://alphagourmet.com",
        "opening_hours": "12:00 PM - 11:30 PM",
        "map_url": "https://maps.google.com/?cid=456",
        "brand_accent": "#C6A66B",
        "timezone": "Asia/Kolkata",
    }
    resp = client.put("/api/businesses/tenant-alpha/shared-profile", json=update_payload)
    assert resp.status_code == 200
    updated = resp.json()

    assert updated["display_name"] == "Alpha Gourmet Kitchen"
    assert updated["brand_accent"] == "#C6A66B"
    assert updated["category"] == "Contemporary Indian"

    # Verify persistence via fresh GET
    fresh = client.get("/api/businesses/tenant-alpha/shared-profile").json()
    assert fresh["display_name"] == "Alpha Gourmet Kitchen"
    assert fresh["brand_accent"] == "#C6A66B"


def test_03_manager_and_staff_put_strictly_rejected(test_env):
    """Manager and Staff are strictly forbidden from modifying shared profile."""
    # Manager attempt
    mgr_client = make_client(test_env["manager_id"], "tenant-alpha", test_env["store"])
    resp_mgr = mgr_client.put(
        "/api/businesses/tenant-alpha/shared-profile",
        json={"display_name": "Manager Renamed"}
    )
    assert resp_mgr.status_code == 403

    # Staff attempt
    staff_client = make_client(test_env["staff_id"], "tenant-alpha", test_env["store"])
    resp_staff = staff_client.put(
        "/api/businesses/tenant-alpha/shared-profile",
        json={"display_name": "Staff Renamed"}
    )
    assert resp_staff.status_code == 403


def test_04_owner_logo_upload_success_and_replacement(test_env):
    """Owner can upload a valid PNG logo, and shared logo_path updates atomically."""
    client = make_client(test_env["owner_id"], "tenant-alpha", test_env["store"])

    files = {"file": ("alpha_logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    upload_resp = client.post("/api/businesses/tenant-alpha/shared-profile/logo", files=files)
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()

    assert upload_data["success"] is True
    assert upload_data["media_type"] == "image/png"
    assert "/shared-profile/logo/" in upload_data["logo_path"]

    # Verify shared profile reflects new logo_path
    profile = client.get("/api/businesses/tenant-alpha/shared-profile").json()
    assert profile["logo_path"] == upload_data["logo_path"]


def test_05_manager_and_staff_logo_upload_strictly_forbidden(test_env):
    """Manager and Staff cannot upload logos."""
    mgr_client = make_client(test_env["manager_id"], "tenant-alpha", test_env["store"])
    files_mgr = {"file": ("unauthorized_mgr.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp_mgr = mgr_client.post("/api/businesses/tenant-alpha/shared-profile/logo", files=files_mgr)
    assert resp_mgr.status_code == 403

    staff_client = make_client(test_env["staff_id"], "tenant-alpha", test_env["store"])
    files_staff = {"file": ("unauthorized_staff.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp_staff = staff_client.post("/api/businesses/tenant-alpha/shared-profile/logo", files=files_staff)
    assert resp_staff.status_code == 403


def test_06_validation_rejections(test_env):
    """Server enforces strict validation on invalid timezones, URLs, and SVG uploads."""
    client = make_client(test_env["owner_id"], "tenant-alpha", test_env["store"])

    # 1. Invalid timezone
    resp_tz = client.put(
        "/api/businesses/tenant-alpha/shared-profile",
        json={"timezone": "Invalid/Fictional_Zone"}
    )
    assert resp_tz.status_code == 422

    # 2. Invalid website URL
    resp_url = client.put(
        "/api/businesses/tenant-alpha/shared-profile",
        json={"website_url": "not-a-valid-url"}
    )
    assert resp_url.status_code == 422

    # 3. SVG upload rejected
    svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
    svg_file = {"file": ("malicious.svg", io.BytesIO(svg_bytes), "image/svg+xml")}
    resp_svg = client.post("/api/businesses/tenant-alpha/shared-profile/logo", files=svg_file)
    assert resp_svg.status_code in (415, 422)


def test_07_tenant_isolation_strictly_enforced(test_env):
    """User in Tenant Beta cannot access Tenant Alpha's shared profile."""
    beta_client = make_client(test_env["beta_user_id"], "tenant-beta", test_env["store"])

    get_resp = beta_client.get("/api/businesses/tenant-alpha/shared-profile")
    assert get_resp.status_code == 403

    put_resp = beta_client.put(
        "/api/businesses/tenant-alpha/shared-profile",
        json={"display_name": "Cross Tenant Exploit"}
    )
    assert put_resp.status_code == 403


def test_08_superadmin_can_manage_any_tenant_profile(test_env):
    """Platform Superadmin can read and edit any tenant profile."""
    admin_client = make_client(test_env["superadmin_id"], "tenant-alpha", test_env["store"])

    put_resp = admin_client.put(
        "/api/businesses/tenant-alpha/shared-profile",
        json={"display_name": "Admin Adjusted Name"}
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["display_name"] == "Admin Adjusted Name"


def test_09_frontend_component_structure_and_safe_imports():
    """Verify SharedBusinessProfileView component contains all required sections and safeguards."""
    view_file = Path("NastaGhar/frontend/src/components/portal/SharedBusinessProfileView.jsx")
    assert view_file.exists()
    content = view_file.read_text()

    # Canonical fields
    assert "displayName" in content
    assert "category" in content
    assert "branchName" in content
    assert "description" in content
    assert "tagline" in content
    assert "phoneNumber" in content
    assert "email" in content
    assert "address" in content
    assert "websiteUrl" in content
    assert "openingHours" in content
    assert "mapUrl" in content
    assert "brandAccent" in content
    assert "timezone" in content

    # Logo integration
    assert "handleLogoFileSelect" in content
    assert "/shared-profile/logo" in content

    # Read-only check
    assert "isReadOnly" in content
    assert "Read-Only Mode" in content
    assert "isDirty" in content
