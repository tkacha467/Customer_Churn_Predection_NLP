"""
Comprehensive Automated Test Suite for Phase 2 Subpart 2C:
Canonical Shared Business Profile API (GET & PUT /api/businesses/{business_id}/shared-profile).

Verifies:
1. Role-based authorization matrix:
   - Staff: GET 200, PUT 403.
   - Manager: GET 200, PUT 403.
   - Owner: GET 200, PUT 200.
   - Platform Admin: GET 200, PUT 200 across tenants.
2. Tenant boundary and isolation:
   - Cross-tenant access denied with HTTP 403.
   - Missing / invalid business IDs safely return HTTP 404 / 422 without data leakage.
3. Common Identity Contract:
   - Returns strictly common shared identity fields.
   - Zero Product A settings leakage (no topics, place_id, google_review_url).
   - Zero Product B settings leakage (no background_preset, overlay_opacity, custom_links).
4. Pydantic field-set tracking and brand accent states:
   - Omitted fields remain completely unchanged in storage.
   - Explicit null clears brand_accent to NULL.
   - Valid hex updates brand_accent.
   - Original business-name casing is preserved verbatim.
5. Strong validation:
   - Invalid / malformed / whitespace URLs rejected with HTTP 422.
   - Non-HTTP(S) schemes (e.g. javascript:) rejected with HTTP 422.
   - Invalid IANA timezones rejected with HTTP 422.
   - Invalid hex colors rejected with HTTP 422.
   - Unsupported / product-specific configuration rejected with HTTP 422 (extra="forbid").
6. Transactional integrity and rollback on failure.
"""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database.storage import ReviewStore
from backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    _login_attempts,
    _login_lock,
)
from backend.app.api.service import review_service


@pytest.fixture
def api_setup(tmp_path, monkeypatch):
    """Sets up an isolated SQLite test database with provisioned shared profiles."""
    db_path = tmp_path / "test_shared_profile.sqlite3"
    docs_path = tmp_path / "documents"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))
    _stores[str(db_path)] = store

    # Apply schema additions so columns like branch_name, description, brand_accent, timezone exist
    from backend.app.core.database.migration import apply_phase2_schema_alterations
    with store._connect() as con:
        apply_phase2_schema_alterations(con)

    # 1. Seed Platform Admin
    admin_user = store.create_user(
        email="superadmin@vraja.test",
        password_hash=hash_password("SuperSecretAdmin123!"),
        display_name="Platform Superadmin",
        is_active=1,
        is_platform_admin=1,
    )

    # 2. Seed Tenant Alpha (Review Manager + Digital Card)
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
    # Provision canonical business_profiles record
    now = time.time()
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
                '#174D3A', 'Asia/Kolkata', '/logos/alpha.png', ?, ?
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

    # 3. Seed Tenant Beta (Review Manager only)
    store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Cuore Bistro",
        "category": "Italian Bistro",
        "branch": "West End",
        "description": "Authentic wood-fired pizza and handmade pasta.",
        "primary_accent": "#ef4444",
        "status": "active",
        "entitlements": ["review_manager"],
    })
    with store._connect() as con:
        con.execute("""
            INSERT OR REPLACE INTO business_profiles (
                tenant_id, display_name, category, branch_name, description,
                tagline, phone_number, email, address, website_url, opening_hours,
                map_url, brand_accent, timezone, logo_path, created_at, updated_at
            ) VALUES (
                'tenant_beta', 'Cuore Bistro', 'Italian Bistro', 'West End',
                'Authentic wood-fired pizza and handmade pasta.', 'Taste of Napoli',
                '+91 98765 22222', 'ciao@beta.test', '202 River Road, Surat',
                'https://cuore-bistro.test', '12:00 PM - 11:00 PM', 'https://maps.google.com/beta',
                '#B91C1C', 'Asia/Kolkata', '/logos/beta.png', ?, ?
            );
        """, (now, now))

    owner_beta = store.create_user(
        email="owner@beta.test",
        password_hash=hash_password("OwnerBeta123!"),
        display_name="Beta Owner",
        is_active=1,
    )
    store.add_membership(owner_beta["id"], "tenant_beta", role="owner")

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
        "admin_client": make_client(admin_user["id"], "default_business"),
        "owner_alpha_client": make_client(owner_alpha["id"], "tenant_alpha"),
        "manager_alpha_client": make_client(manager_alpha["id"], "tenant_alpha"),
        "staff_alpha_client": make_client(staff_alpha["id"], "tenant_alpha"),
        "owner_beta_client": make_client(owner_beta["id"], "tenant_beta"),
        "unauth_client": TestClient(app),
    }


# ==============================================================================
# 1. Successful GET /shared-profile & Common Identity Verification
# ==============================================================================

def test_01_get_shared_profile_success(api_setup):
    """Staff, Manager, and Owner can all read the Shared Business Profile."""
    for client, role in [
        (api_setup["owner_alpha_client"], "owner"),
        (api_setup["manager_alpha_client"], "manager"),
        (api_setup["staff_alpha_client"], "staff"),
    ]:
        resp = client.get("/api/businesses/tenant_alpha/shared-profile")
        assert resp.status_code == 200, f"Role {role} failed to get shared profile: {resp.text}"
        data = resp.json()
        assert data["tenant_id"] == "tenant_alpha"
        assert data["display_name"] == "Artisanal Coffee & Roastery"
        assert data["category"] == "Cafe & Roastery"
        assert data["branch_name"] == "Downtown Flagship"
        assert data["description"] == "Artisanal single-origin espresso and sourdough."
        assert data["brand_accent"] == "#174D3A"
        assert data["timezone"] == "Asia/Kolkata"
        assert set(data["entitlements"]) == {"review_manager", "digital_card"}

        # Strict common identity assertion: zero Product A/B configuration returned
        for forbidden in (
            "topics", "topics_json", "google_review_url", "place_id",
            "background_preset", "overlay_opacity", "custom_links", "custom_links_json",
            "is_published", "show_review_button", "welcome_message",
        ):
            assert forbidden not in data, f"Data leakage: '{forbidden}' present in shared profile response"


def test_02_platform_admin_can_read_and_update_any_tenant(api_setup):
    """Platform Superadmin can read and update shared profile across tenant boundaries."""
    client = api_setup["admin_client"]
    resp = client.get("/api/businesses/tenant_alpha/shared-profile")
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == "tenant_alpha"

    put_resp = client.put(
        "/api/businesses/tenant_alpha/shared-profile",
        json={"tagline": "Updated by Superadmin"}
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["tagline"] == "Updated by Superadmin"


# ==============================================================================
# 2. Authorization Hierarchy & Tenant Isolation
# ==============================================================================

def test_03_staff_and_manager_put_forbidden(api_setup):
    """Staff and Manager are rejected with HTTP 403 when attempting to update shared profile."""
    for client, role in [
        (api_setup["staff_alpha_client"], "staff"),
        (api_setup["manager_alpha_client"], "manager"),
    ]:
        resp = client.put(
            "/api/businesses/tenant_alpha/shared-profile",
            json={"display_name": "Hacked Name"}
        )
        assert resp.status_code == 403, f"Expected 403 for {role}, got {resp.status_code}"
        assert "Insufficient permissions" in resp.json()["detail"] or "owner" in resp.json()["detail"]


def test_04_cross_tenant_isolation_enforced(api_setup):
    """Tenant Alpha owner cannot read or update Tenant Beta shared profile."""
    alpha_owner = api_setup["owner_alpha_client"]

    # Attempt cross-tenant GET
    get_resp = alpha_owner.get("/api/businesses/tenant_beta/shared-profile")
    assert get_resp.status_code == 403
    assert "Access denied" in get_resp.json()["detail"]

    # Attempt cross-tenant PUT
    put_resp = alpha_owner.put(
        "/api/businesses/tenant_beta/shared-profile",
        json={"display_name": "Malicious Overwrite"}
    )
    assert put_resp.status_code == 403
    assert "Access denied" in put_resp.json()["detail"]

    # Verify Beta was not mutated
    beta_resp = api_setup["owner_beta_client"].get("/api/businesses/tenant_beta/shared-profile")
    assert beta_resp.json()["display_name"] == "Cuore Bistro"


def test_05_unauthenticated_request_rejected(api_setup):
    """Unauthenticated requests return HTTP 401."""
    client = api_setup["unauth_client"]
    assert client.get("/api/businesses/tenant_alpha/shared-profile").status_code == 401
    assert client.put("/api/businesses/tenant_alpha/shared-profile", json={"tagline": "x"}).status_code == 401


def test_06_non_existent_business_returns_404_or_403_safely(api_setup):
    """Requests for nonexistent tenants return 404/403 without data leakage."""
    # Admin requesting non-existent tenant gets 404
    resp = api_setup["admin_client"].get("/api/businesses/non_existent_tenant/shared-profile")
    assert resp.status_code == 404

    # Tenant owner requesting non-existent tenant gets 403 (membership check fails first)
    resp2 = api_setup["owner_alpha_client"].get("/api/businesses/non_existent_tenant/shared-profile")
    assert resp2.status_code == 403


# ==============================================================================
# 3. Owner PUT & Pydantic Set-Tracking (Omitted vs Explicit Null vs Hex)
# ==============================================================================

def test_07_owner_put_success_and_preservation_of_omitted_fields(api_setup):
    """Owner updating a single field preserves all omitted fields."""
    client = api_setup["owner_alpha_client"]

    # Update only tagline and phone number
    resp = client.put(
        "/api/businesses/tenant_alpha/shared-profile",
        json={"tagline": "Rajkot Premier Coffee House", "phone_number": "+91 99999 88888"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tagline"] == "Rajkot Premier Coffee House"
    assert data["phone_number"] == "+91 99999 88888"

    # Verify omitted fields preserved
    assert data["display_name"] == "Artisanal Coffee & Roastery"
    assert data["category"] == "Cafe & Roastery"
    assert data["branch_name"] == "Downtown Flagship"
    assert data["description"] == "Artisanal single-origin espresso and sourdough."
    assert data["brand_accent"] == "#174D3A"
    assert data["timezone"] == "Asia/Kolkata"


def test_08_brand_accent_three_state_transitions(api_setup):
    """
    Verifies all three brand_accent Pydantic set-tracking states:
    1. Omitted field -> preserves existing value.
    2. Explicit null -> clears brand_accent to NULL.
    3. Valid hex -> sets new brand_accent.
    """
    client = api_setup["owner_alpha_client"]

    # State 1: Omitted -> remains '#174D3A'
    r1 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"branch_name": "Updated Branch"})
    assert r1.status_code == 200
    assert r1.json()["brand_accent"] == "#174D3A"

    # State 2: Explicit null -> clears to None
    r2 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"brand_accent": None})
    assert r2.status_code == 200
    assert r2.json()["brand_accent"] is None

    # Verify directly in SQLite storage
    store = api_setup["store"]
    with store._connect() as con:
        val = con.execute("SELECT brand_accent FROM business_profiles WHERE tenant_id = 'tenant_alpha';").fetchone()[0]
        assert val is None

    # State 3: Valid hex -> updates to '#2563EB'
    r3 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"brand_accent": "#2563EB"})
    assert r3.status_code == 200
    assert r3.json()["brand_accent"] == "#2563EB"

    with store._connect() as con:
        val2 = con.execute("SELECT brand_accent FROM business_profiles WHERE tenant_id = 'tenant_alpha';").fetchone()[0]
        assert val2 == "#2563EB"


def test_09_business_name_casing_preserved(api_setup):
    """Business name casing (e.g. mixed/special casing) is preserved verbatim."""
    client = api_setup["owner_alpha_client"]
    for raw_name in ("iPhone Repair Co.", "eBay Store", "diptyque Paris", "McDonald's Express"):
        resp = client.put("/api/businesses/tenant_alpha/shared-profile", json={"display_name": raw_name})
        assert resp.status_code == 200
        assert resp.json()["display_name"] == raw_name


# ==============================================================================
# 4. Strong Validation Rejections (URLs, Timezones, Accents, Extra Fields)
# ==============================================================================

def test_10_invalid_urls_rejected(api_setup):
    """Rejects malformed URLs, URLs with whitespace, and non-HTTP(S) schemes."""
    client = api_setup["owner_alpha_client"]

    # 1. Scheme other than http/https (e.g. javascript:)
    r1 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"website_url": "javascript:alert(1)"})
    assert r1.status_code == 422

    # 2. Whitespace in URL
    r2 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"website_url": "https://alpha coffee.com"})
    assert r2.status_code == 422

    # 3. Missing host
    r3 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"website_url": "https://"})
    assert r3.status_code == 422

    # 4. Map URL validation
    r4 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"map_url": "ftp://maps.google.com"})
    assert r4.status_code == 422


def test_11_invalid_timezone_rejected(api_setup):
    """Rejects invalid IANA timezone identifiers."""
    client = api_setup["owner_alpha_client"]

    r1 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"timezone": "Invalid/Timezone"})
    assert r1.status_code == 422
    assert "Invalid IANA timezone" in r1.text

    # Valid timezones accepted
    for valid_tz in ("Asia/Kolkata", "UTC", "America/New_York", "Europe/London"):
        r2 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"timezone": valid_tz})
        assert r2.status_code == 200
        assert r2.json()["timezone"] == valid_tz


def test_12_invalid_brand_accent_rejected(api_setup):
    """Rejects invalid hex color codes."""
    client = api_api_setup = api_setup["owner_alpha_client"]

    for bad_hex in ("red", "#12", "#12345", "#GGGGGG", "174D3A"):
        resp = client.put("/api/businesses/tenant_alpha/shared-profile", json={"brand_accent": bad_hex})
        assert resp.status_code == 422, f"Failed to reject invalid hex: {bad_hex}"


def test_13_product_specific_settings_rejected(api_setup):
    """
    Subpart 2C forbids unexpected or product-specific settings via extra='forbid'.
    Ensures zero product configuration leakage.
    """
    client = api_setup["owner_alpha_client"]

    # Product A settings attempt
    r1 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"topics": ["food", "service"]})
    assert r1.status_code == 422
    assert "extra_forbidden" in r1.text

    r2 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"google_review_url": "https://g.page/review"})
    assert r2.status_code == 422

    # Product B settings attempt
    r3 = client.put("/api/businesses/tenant_alpha/shared-profile", json={"background_preset": "dark_slate"})
    assert r3.status_code == 422


# ==============================================================================
# 5. Database Failure & Transaction Rollback
# ==============================================================================

def test_14_database_failure_rolls_back(api_setup, monkeypatch):
    """Simulates a database failure during update to assert transactional rollback."""
    client = api_setup["owner_alpha_client"]
    store = api_setup["store"]

    orig_execute = store._connect

    class FailingConnection:
        def __init__(self, real_con):
            self._real = real_con

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._real.rollback()
            return False

        def execute(self, sql, *args, **kwargs):
            if "UPDATE business_profiles" in sql:
                raise RuntimeError("Simulated Disk / Lock Failure")
            return self._real.execute(sql, *args, **kwargs)

    def failing_connect():
        return FailingConnection(orig_execute())

    monkeypatch.setattr(store, "_connect", failing_connect)

    with pytest.raises(RuntimeError):
        client.put(
            "/api/businesses/tenant_alpha/shared-profile",
            json={"display_name": "Should Be Rolled Back"}
        )

    # Restore original connection method and verify original name preserved
    monkeypatch.setattr(store, "_connect", orig_execute)
    resp = client.get("/api/businesses/tenant_alpha/shared-profile")
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Artisanal Coffee & Roastery"
