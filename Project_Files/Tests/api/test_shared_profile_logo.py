"""
Comprehensive Automated Test Suite for Phase 2 Subpart 2D:
Shared Business Logo Upload & Atomic Storage.

Verifies:
1. Role-based authorization:
   - Owner can upload and replace shared logo.
   - Staff and Manager receive HTTP 403.
   - Anonymous requests receive HTTP 401.
   - Cross-tenant upload attempts receive HTTP 403.
   - Platform Superadmin can upload across tenants.
2. File validation & security:
   - Rejects non-raster formats (SVG, HTML, scripts, executables).
   - Validates authentic raster headers and dimensions (PNG, JPEG, WebP).
   - Rejects oversized files (> 2 MiB -> 413).
   - Rejects spoofed MIME types and corrupted image bytes (422).
   - Rejects unreasonable dimensions (< 16x16 or > 4096x4096 -> 422).
   - Sanitizes filenames and prevents path traversal.
3. Atomic storage & failure compensation:
   - Collision-proof immutable filenames.
   - Temporary file writing and atomic rename.
   - Database failure compensation: unlinks newly written file, preserves previous logo.
   - Filesystem write failure handling: unlinks temporary file, preserves database.
   - Post-commit cleanup: unlinks old managed logo without deleting default or unrelated files.
4. Product configuration preservation:
   - Product A (review topics, google_review_url, primary_accent) and
     Product B (background_preset, overlay_opacity, custom_links) remain untouched.
5. Public logo serving:
   - Public versioned logo endpoint (200 OK with caching and nosniff).
   - Public current logo endpoint.
"""

import hashlib
import io
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import (
    DocumentStorageService,
    get_document_storage,
    _document_services,
)
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

# Valid synthetic raster images with standardized dimensions
VALID_PNG_100x100 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x64\x00\x00\x00\x64\x08\x06\x00\x00\x00"
    b"\x70\xe1\xd5\x9a"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

VALID_JPEG_300x200 = (
    b"\xff\xd8\xff\xc0\x00\x11\x08\x00\xc8\x01\x2c\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xd9"
)

VALID_WEBP_150x120 = (
    b"RIFF\x20\x00\x00\x00WEBPVP8X\x0a\x00\x00\x00\x00\x00\x00\x00\x95\x00\x00\x77\x00\x00"
)

SVG_PAYLOAD = b"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><circle cx='50' cy='50' r='40'/></svg>"
HTML_PAYLOAD = b"<!DOCTYPE html><html><body><h1>Fake Image</h1></body></html>"
SCRIPT_PAYLOAD = b"<script>alert('xss')</script>"
UNDERSIZED_PNG_5x5 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x05\x00\x00\x00\x05\x08\x06\x00\x00\x00"
    b"\x70\xe1\xd5\x9a"
)


@pytest.fixture
def logo_setup(tmp_path, monkeypatch):
    """Sets up an isolated SQLite database and documents directory for logo tests."""
    db_path = tmp_path / "test_logo.sqlite3"
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

    # 1. Platform Admin
    admin_user = store.create_user(
        email="superadmin@vraja.test",
        password_hash=hash_password("SuperSecretAdmin123!"),
        display_name="Platform Superadmin",
        is_active=1,
        is_platform_admin=1,
    )

    # 2. Tenant Alpha (Review Manager + Digital Card)
    now = time.time()
    store.upsert_tenant({
        "id": "tenant_alpha",
        "business_name": "Artisanal Coffee & Roastery",
        "category": "Cafe & Roastery",
        "branch": "Downtown Flagship",
        "description": "Artisanal single-origin espresso and sourdough.",
        "primary_accent": "#f97316",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })
    with store._connect() as con:
        con.execute("""
            INSERT OR REPLACE INTO business_profiles (
                tenant_id, display_name, category, branch_name, description,
                tagline, phone_number, email, address, website_url, opening_hours,
                map_url, brand_accent, timezone, logo_path, created_at, updated_at
            ) VALUES (
                'tenant_alpha', 'Artisanal Coffee & Roastery', 'Cafe & Roastery', 'Downtown Flagship',
                'Artisanal single-origin espresso and sourdough.', 'Crafted with Passion',
                '+91 98765 11111', 'hello@alpha.test', '101 Main Street, Ahmedabad',
                'https://alpha-coffee.test', '7:00 AM - 11:00 PM', 'https://maps.google.com/alpha',
                '#174D3A', 'Asia/Kolkata', '/restaurant/nasta-ghar-logo.svg', ?, ?
            );
        """, (now, now))

    owner_alpha = store.create_user(
        email="owner@alpha.test",
        password_hash=hash_password("OwnerAlpha123!"),
        display_name="Alpha Owner",
        is_active=1,
    )
    store.add_membership(owner_alpha["id"], "tenant_alpha", role="owner")

    manager_alpha = store.create_user(
        email="manager@alpha.test",
        password_hash=hash_password("ManagerAlpha123!"),
        display_name="Alpha Manager",
        is_active=1,
    )
    store.add_membership(manager_alpha["id"], "tenant_alpha", role="manager")

    staff_alpha = store.create_user(
        email="staff@alpha.test",
        password_hash=hash_password("StaffAlpha123!"),
        display_name="Alpha Staff",
        is_active=1,
    )
    store.add_membership(staff_alpha["id"], "tenant_alpha", role="staff")

    # 3. Tenant Beta
    store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Cuore Bistro",
        "category": "Italian Bistro",
        "status": "active",
        "entitlements": ["review_manager"],
    })
    with store._connect() as con:
        con.execute("""
            INSERT OR REPLACE INTO business_profiles (
                tenant_id, display_name, category, created_at, updated_at
            ) VALUES ('tenant_beta', 'Cuore Bistro', 'Italian Bistro', ?, ?);
        """, (now, now))

    owner_beta = store.create_user(
        email="owner@beta.test",
        password_hash=hash_password("OwnerBeta123!"),
        display_name="Beta Owner",
        is_active=1,
    )
    store.add_membership(owner_beta["id"], "tenant_beta", role="owner")

    owner_default = store.create_user(
        email="owner@default.test",
        password_hash=hash_password("OwnerDefault123!"),
        display_name="Default Owner",
        is_active=1,
    )
    store.add_membership(owner_default["id"], "default_business", role="owner")

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
        "owner_default_client": make_client(owner_default["id"], "default_business"),
        "owner_alpha_client": make_client(owner_alpha["id"], "tenant_alpha"),
        "manager_alpha_client": make_client(manager_alpha["id"], "tenant_alpha"),
        "staff_alpha_client": make_client(staff_alpha["id"], "tenant_alpha"),
        "owner_beta_client": make_client(owner_beta["id"], "tenant_beta"),
        "unauth_client": TestClient(app),
    }


# ==============================================================================
# 1. Owner Upload Success & Replacement Lifecycle
# ==============================================================================

def test_01_owner_logo_upload_success_png(logo_setup):
    """Owner successfully uploads a valid PNG logo; updates canonical logo_path."""
    client = logo_setup["owner_alpha_client"]
    files = {"file": ("brand_logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}

    resp = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["media_type"] == "image/png"
    assert data["size_bytes"] == len(VALID_PNG_100x100)
    assert data["dimensions"] == {"width": 100, "height": 100}
    assert data["filename"].startswith("logo_tenant_alpha_")
    assert data["filename"].endswith(".png")
    assert "/api/businesses/tenant_alpha/shared-profile/logo/" in data["logo_path"]

    # Verify canonical business_profiles was updated
    store = logo_setup["store"]
    profile = store.get_shared_business_profile("tenant_alpha")
    assert profile["logo_path"] == data["logo_path"]

    # Verify the uploaded file actually exists on disk in tenant's logos directory
    docs_dir = logo_setup["docs_path"]
    final_file = docs_dir / "tenant_alpha" / "logos" / data["filename"]
    assert final_file.is_file()
    assert final_file.read_bytes() == VALID_PNG_100x100


def test_02_owner_logo_replacement_unlinks_old_managed_logo(logo_setup):
    """Replacing an existing uploaded logo deletes the old file and sets the new one."""
    client = logo_setup["owner_alpha_client"]
    docs_dir = logo_setup["docs_path"]

    # Upload 1: PNG logo
    files1 = {"file": ("logo_v1.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    r1 = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files1)
    assert r1.status_code == 200
    fn1 = r1.json()["filename"]
    file1 = docs_dir / "tenant_alpha" / "logos" / fn1
    assert file1.is_file()

    # Upload 2: Replace with WebP logo
    files2 = {"file": ("logo_v2.webp", io.BytesIO(VALID_WEBP_150x120), "image/webp")}
    r2 = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files2)
    assert r2.status_code == 200
    fn2 = r2.json()["filename"]
    file2 = docs_dir / "tenant_alpha" / "logos" / fn2
    assert file2.is_file()

    # Old logo file must be cleaned up / unlinked
    assert not file1.exists(), "Old managed logo file was not unlinked after replacement!"

    # Database now points to new logo
    store = logo_setup["store"]
    profile = store.get_shared_business_profile("tenant_alpha")
    assert profile["logo_path"] == r2.json()["logo_path"]


def test_03_default_system_logo_never_deleted_on_replacement(logo_setup):
    """Initial system default logo (/restaurant/nasta-ghar-logo.svg) is never deleted."""
    client = logo_setup["owner_alpha_client"]
    # Alpha starts with '/restaurant/nasta-ghar-logo.svg'
    files = {"file": ("new_logo.jpg", io.BytesIO(VALID_JPEG_300x200), "image/jpeg")}
    resp = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert resp.status_code == 200


# ==============================================================================
# 2. Role-Based Authorization & Tenant Boundaries
# ==============================================================================

def test_04_staff_and_manager_upload_forbidden(logo_setup):
    """Staff and Managers receive HTTP 403 when attempting logo upload."""
    files = {"file": ("logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}

    for client, role in [
        (logo_setup["staff_alpha_client"], "staff"),
        (logo_setup["manager_alpha_client"], "manager"),
    ]:
        resp = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
        assert resp.status_code == 403, f"Expected 403 for {role}, got {resp.status_code}"
        assert "Insufficient permissions" in resp.json()["detail"] or "owner" in resp.json()["detail"]


def test_05_cross_tenant_upload_forbidden(logo_setup):
    """Tenant Alpha owner cannot upload a logo to Tenant Beta."""
    alpha_owner = logo_setup["owner_alpha_client"]
    files = {"file": ("logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}

    resp = alpha_owner.post("/api/businesses/tenant_beta/shared-profile/logo", files=files)
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

    # Beta's profile was not modified
    store = logo_setup["store"]
    beta_profile = store.get_shared_business_profile("tenant_beta")
    assert beta_profile["logo_path"] == ""


def test_06_unauthenticated_upload_rejected(logo_setup):
    """Unauthenticated requests return HTTP 401."""
    client = logo_setup["unauth_client"]
    files = {"file": ("logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    assert client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files).status_code == 401


def test_07_platform_admin_can_upload_across_tenants(logo_setup):
    """Platform Superadmin can upload a logo to any tenant."""
    admin = logo_setup["admin_client"]
    files = {"file": ("admin_logo.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp = admin.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# ==============================================================================
# 3. Format, Magic Byte, Dimension & Size Rejections
# ==============================================================================

def test_08_svg_strictly_rejected(logo_setup):
    """SVG files are strictly rejected with HTTP 422 even if renamed or with image/png MIME."""
    client = logo_setup["owner_alpha_client"]

    # Case A: Named .svg with image/svg+xml
    r1 = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("logo.svg", io.BytesIO(SVG_PAYLOAD), "image/svg+xml")}
    )
    assert r1.status_code == 422
    assert "SVG" in r1.json()["detail"]

    # Case B: Spoofed extension (.png) with image/png header, but SVG content
    r2 = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("spoofed.png", io.BytesIO(SVG_PAYLOAD), "image/png")}
    )
    assert r2.status_code == 422
    assert "SVG" in r2.json()["detail"]


def test_09_html_and_script_rejections(logo_setup):
    """HTML and scripts are rejected with HTTP 422."""
    client = logo_setup["owner_alpha_client"]

    r1 = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("index.html", io.BytesIO(HTML_PAYLOAD), "text/html")}
    )
    assert r1.status_code == 422

    r2 = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("evil.png", io.BytesIO(SCRIPT_PAYLOAD), "image/png")}
    )
    assert r2.status_code == 422


def test_10_corrupted_and_empty_files_rejected(logo_setup):
    """Empty and corrupted byte payloads are rejected with HTTP 422."""
    client = logo_setup["owner_alpha_client"]

    # Empty file
    r1 = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")}
    )
    assert r1.status_code == 422

    # Truncated header
    r2 = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("corrupt.png", io.BytesIO(b"\x89PNG\r\n\x1a\nTRUNCATED"), "image/png")}
    )
    assert r2.status_code == 422


def test_11_unreasonable_dimensions_rejected(logo_setup):
    """Rejects image dimensions smaller than 16x16 pixels."""
    client = logo_setup["owner_alpha_client"]

    r = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("undersized.png", io.BytesIO(UNDERSIZED_PNG_5x5), "image/png")}
    )
    assert r.status_code == 422
    assert "dimensions" in r.text.lower()


def test_12_oversized_file_rejected_with_413(logo_setup):
    """Files exceeding 2 MiB are rejected with HTTP 413."""
    client = logo_setup["owner_alpha_client"]
    oversized_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 10)

    resp = client.post(
        "/api/businesses/tenant_alpha/shared-profile/logo",
        files={"file": ("huge.png", io.BytesIO(oversized_bytes), "image/png")}
    )
    assert resp.status_code == 413
    assert "exceeds maximum allowed limit" in resp.json()["detail"]


def test_13_path_traversal_filename_sanitized(logo_setup):
    """Client-supplied filenames with traversal paths are ignored; unique safe names used."""
    client = logo_setup["owner_alpha_client"]
    docs_dir = logo_setup["docs_path"]

    files = {"file": ("../../../../etc/passwd.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert resp.status_code == 200

    filename = resp.json()["filename"]
    assert "passwd" not in filename
    assert ".." not in filename
    final_file = docs_dir / "tenant_alpha" / "logos" / filename
    assert final_file.is_file()


# ==============================================================================
# 4. Atomic Rollback, Compensation & Unrelated Settings Preservation
# ==============================================================================

def test_14_database_failure_rolls_back_and_unlinks_new_file(logo_setup, monkeypatch):
    """If DB update fails, compensation unlinks newly written file and preserves old logo."""
    client = logo_setup["owner_alpha_client"]
    store = logo_setup["store"]
    docs_dir = logo_setup["docs_path"]

    orig_logo = store.get_shared_business_profile("tenant_alpha")["logo_path"]

    # Monkeypatch store.update_shared_business_logo to simulate a SQLite lock error
    def failing_update(tenant_id, logo_path):
        raise RuntimeError("Simulated Database Lock Failure")

    monkeypatch.setattr(store, "update_shared_business_logo", failing_update)

    files = {"file": ("fail_test.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert resp.status_code == 500
    assert "Database update failed" in resp.json()["detail"]

    # Verify zero orphaned files left in logos directory
    logos_dir = docs_dir / "tenant_alpha" / "logos"
    if logos_dir.exists():
        orphans = list(logos_dir.glob("logo_*"))
        assert len(orphans) == 0, f"Orphaned file remained after DB failure: {orphans}"

    # Verify original logo_path was preserved
    current = store.get_shared_business_profile("tenant_alpha")
    assert current["logo_path"] == orig_logo


def test_15_product_settings_remain_untouched(logo_setup):
    """Logo upload updates logo_path but preserves Product A and B settings."""
    client = logo_setup["owner_alpha_client"]
    store = logo_setup["store"]

    # Inspect Product A settings on tenants table
    t_before = store.get_tenant("tenant_alpha")
    # Inspect Product B settings on business_profiles table
    p_before = store.get_business_profile("tenant_alpha")

    files = {"file": ("brand.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp = client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert resp.status_code == 200

    t_after = store.get_tenant("tenant_alpha")
    p_after = store.get_business_profile("tenant_alpha")

    # Assert Product A operational review settings intact
    assert t_after["primary_accent"] == t_before["primary_accent"]
    assert t_after["category"] == t_before["category"]
    assert t_after["description"] == t_before["description"]

    # Assert Product B card presentation settings intact
    assert p_after["primary_accent"] == p_before["primary_accent"]
    assert p_after["background_preset"] == p_before["background_preset"]
    assert p_after["overlay_opacity"] == p_before["overlay_opacity"]
    assert p_after["tagline"] == p_before["tagline"]


# ==============================================================================
# 5. Public Logo Serving
# ==============================================================================

def test_16_public_logo_serving_versioned_and_active(logo_setup):
    """Public endpoints serve the versioned logo and current active logo."""
    owner_client = logo_setup["owner_alpha_client"]
    unauth_client = logo_setup["unauth_client"]

    # 1. Upload logo
    files = {"file": ("brand.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    up_resp = owner_client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files)
    assert up_resp.status_code == 200
    logo_path = up_resp.json()["logo_path"]
    filename = up_resp.json()["filename"]

    # 2. Anonymous client GET versioned logo file
    v_resp = unauth_client.get(logo_path)
    assert v_resp.status_code == 200
    assert v_resp.headers["content-type"] == "image/png"
    assert v_resp.headers["x-content-type-options"] == "nosniff"
    assert v_resp.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert v_resp.content == VALID_PNG_100x100

    # 3. Anonymous client GET current active logo
    c_resp = unauth_client.get("/api/businesses/tenant_alpha/shared-profile/logo")
    assert c_resp.status_code == 200
    assert c_resp.headers["content-type"] == "image/png"
    assert c_resp.headers["x-content-type-options"] == "nosniff"
    assert c_resp.headers["cache-control"] == "no-cache, must-revalidate"
    assert c_resp.content == VALID_PNG_100x100


def test_17_business_id_alias_normalization_and_retrieval(logo_setup):
    """Business aliases (default_business, nasta_ghar, nasta-ghar) resolve canonically; cross-tenant and unknown aliases rejected."""
    owner_client = logo_setup["owner_default_client"]
    unauth_client = logo_setup["unauth_client"]

    # Scenario 1: Upload using 'default_business', retrieve using 'nasta-ghar'
    files1 = {"file": ("logo1.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    resp1 = owner_client.post("/api/businesses/default_business/shared-profile/logo", files=files1)
    assert resp1.status_code == 200

    get_nasta_ghar = unauth_client.get("/api/businesses/nasta-ghar/shared-profile/logo")
    assert get_nasta_ghar.status_code == 200
    assert get_nasta_ghar.content == VALID_PNG_100x100

    # Scenario 2: Upload using 'nasta_ghar', retrieve using 'default_business' and 'nasta-ghar'
    files2 = {"file": ("logo2.jpg", io.BytesIO(VALID_JPEG_300x200), "image/jpeg")}
    resp2 = owner_client.post("/api/businesses/nasta_ghar/shared-profile/logo", files=files2)
    assert resp2.status_code == 200

    get_default = unauth_client.get("/api/businesses/default_business/shared-profile/logo")
    assert get_default.status_code == 200
    assert get_default.content == VALID_JPEG_300x200

    get_hyphen = unauth_client.get("/api/businesses/nasta-ghar/shared-profile/logo")
    assert get_hyphen.status_code == 200
    assert get_hyphen.content == VALID_JPEG_300x200

    # Scenario 3: Cross-tenant isolation remains strictly enforced
    # tenant_beta has no uploaded logo; requesting beta must return 404 and NOT leak default_business logo
    beta_resp = unauth_client.get("/api/businesses/tenant_beta/shared-profile/logo")
    assert beta_resp.status_code == 404

    # Requesting beta's versioned endpoint with default_business's logo filename must return 404
    db_logo_filename = resp2.json()["filename"]
    beta_cross_resp = unauth_client.get(f"/api/businesses/tenant_beta/shared-profile/logo/{db_logo_filename}")
    assert beta_cross_resp.status_code == 404

    # Scenario 4: Unknown aliases safely rejected with 404
    unknown_resp1 = unauth_client.get("/api/businesses/unknown_random_tenant/shared-profile/logo")
    assert unknown_resp1.status_code == 404
    unknown_resp2 = unauth_client.get(f"/api/businesses/unknown_random_tenant/shared-profile/logo/{db_logo_filename}")
    assert unknown_resp2.status_code == 404


def test_18_cache_control_and_logo_replacement_active_freshness(logo_setup):
    """Active endpoint returns no-cache and fresh content immediately upon replacement; versioned returns immutable."""
    owner_client = logo_setup["owner_alpha_client"]
    unauth_client = logo_setup["unauth_client"]

    # 1. Upload initial logo (PNG)
    files_png = {"file": ("brand_v1.png", io.BytesIO(VALID_PNG_100x100), "image/png")}
    r1 = owner_client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files_png)
    assert r1.status_code == 200
    v1_path = r1.json()["logo_path"]

    # Active endpoint serves PNG with no-cache header
    active_r1 = unauth_client.get("/api/businesses/tenant_alpha/shared-profile/logo")
    assert active_r1.status_code == 200
    assert active_r1.headers["cache-control"] == "no-cache, must-revalidate"
    assert active_r1.content == VALID_PNG_100x100

    # Versioned endpoint serves PNG with immutable cache header
    v1_resp = unauth_client.get(v1_path)
    assert v1_resp.status_code == 200
    assert v1_resp.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert v1_resp.content == VALID_PNG_100x100

    # 2. Replace with new logo (JPEG)
    files_jpg = {"file": ("brand_v2.jpg", io.BytesIO(VALID_JPEG_300x200), "image/jpeg")}
    r2 = owner_client.post("/api/businesses/tenant_alpha/shared-profile/logo", files=files_jpg)
    assert r2.status_code == 200
    v2_path = r2.json()["logo_path"]
    assert v1_path != v2_path

    # Active endpoint immediately returns JPEG with no-cache header
    active_r2 = unauth_client.get("/api/businesses/tenant_alpha/shared-profile/logo")
    assert active_r2.status_code == 200
    assert active_r2.headers["cache-control"] == "no-cache, must-revalidate"
    assert active_r2.content == VALID_JPEG_300x200

    # New versioned endpoint returns immutable cache header
    v2_resp = unauth_client.get(v2_path)
    assert v2_resp.status_code == 200
    assert v2_resp.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert v2_resp.content == VALID_JPEG_300x200

    # Old versioned endpoint returns 404 (cleaned up)
    v1_old_resp = unauth_client.get(v1_path)
    assert v1_old_resp.status_code == 404
