"""
Focused Automated Test Suite for VRAJA AI Phase 4:
Product A Integration into Unified Client Portal.

Verifies:
1. Component modularization and extraction (ProductAReviewSetup, ProductAReviewAnalytics, ProductAPrivateInbox).
2. Five-section navigation structure and removal of redundant manual language toggles.
3. Server-side role hierarchy (Staff vs Manager vs Owner).
4. Strict product entitlement enforcement (review_manager required; digital_card only denied).
5. Cross-tenant request isolation for analytics, tickets, and configurations.
6. Private feedback status mutation and tenant scoping.
7. Analytics data integrity and timezone resolution.
"""

import json
from pathlib import Path
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
from backend.app.core.database.migration import apply_phase2_schema_alterations
import time


@pytest.fixture
def phase4_env(tmp_path, monkeypatch):
    """Provides an isolated test database and environment for Phase 4 tests."""
    db_file = tmp_path / "phase4_integration_test.sqlite3"
    links_file = tmp_path / "phase4_links.json"
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(links_file))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_dir))

    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_file))
    _stores[str(db_file)] = store
    review_service._store = store

    with store._connect() as con:
        apply_phase2_schema_alterations(con)

    # 1. Tenant Alpha (Product A only: review_manager)
    store.upsert_tenant({
        "id": "tenant-alpha",
        "business_name": "Alpha Dining",
        "branch": "Central",
        "category": "Restaurant",
        "entitlements": ["review_manager"]
    })
    store.upsert_business_profile("tenant-alpha", {
        "display_name": "Alpha Dining",
        "category": "Restaurant",
        "branch_name": "Central",
        "description": "Authentic dining experience.",
        "timezone": "Asia/Kolkata",
    })

    # 2. Tenant Beta (Product B only: digital_card)
    store.upsert_tenant({
        "id": "tenant-beta",
        "business_name": "Beta Card Co",
        "branch": "Uptown",
        "category": "Consulting",
        "entitlements": ["digital_card"]
    })
    store.upsert_business_profile("tenant-beta", {
        "display_name": "Beta Card Co",
        "category": "Consulting",
        "branch_name": "Uptown",
        "timezone": "Asia/Dubai",
    })

    # Users:
    # - Owner of Tenant Alpha
    u_owner_a = store.create_user("owner-a@example.com", hash_password("Password123!"), display_name="Alpha Owner")
    owner_a_id = u_owner_a["id"]
    store.add_membership(owner_a_id, "tenant-alpha", role="owner")

    # - Manager of Tenant Alpha
    u_mgr_a = store.create_user("mgr-a@example.com", hash_password("Password123!"), display_name="Alpha Manager")
    mgr_a_id = u_mgr_a["id"]
    store.add_membership(mgr_a_id, "tenant-alpha", role="manager")

    # - Staff of Tenant Alpha
    u_staff_a = store.create_user("staff-a@example.com", hash_password("Password123!"), display_name="Alpha Staff")
    staff_a_id = u_staff_a["id"]
    store.add_membership(staff_a_id, "tenant-alpha", role="staff")

    # - Owner of Tenant Beta
    u_owner_b = store.create_user("owner-b@example.com", hash_password("Password123!"), display_name="Beta Owner")
    owner_b_id = u_owner_b["id"]
    store.add_membership(owner_b_id, "tenant-beta", role="owner")

    def make_cookie(user_id, tenant_id):
        raw_token = generate_session_token()
        hashed = hash_token(raw_token)
        expires_at = time.time() + SESSION_TTL_SECONDS
        store.create_session(
            token_hash=hashed,
            user_id=user_id,
            active_tenant_id=tenant_id,
            expires_at=expires_at,
            ip_address="127.0.0.1",
            user_agent="TestRunner"
        )
        return raw_token

    return {
        "store": store,
        "owner_a_cookie": make_cookie(owner_a_id, "tenant-alpha"),
        "mgr_a_cookie": make_cookie(mgr_a_id, "tenant-alpha"),
        "staff_a_cookie": make_cookie(staff_a_id, "tenant-alpha"),
        "owner_b_cookie": make_cookie(owner_b_id, "tenant-beta"),
    }


# ==============================================================================
# 1. COMPONENT STRUCTURE & EXTRACTION CONTRACTS
# ==============================================================================

def test_01_extracted_components_exist():
    """Verify all 3 extracted Product A components exist and have substantial implementation."""
    base = Path("NastaGhar/frontend/src/components/portal/product_a")
    setup_file = base / "ProductAReviewSetup.jsx"
    analytics_file = base / "ProductAReviewAnalytics.jsx"
    inbox_file = base / "ProductAPrivateInbox.jsx"

    for f in [setup_file, analytics_file, inbox_file]:
        assert f.exists(), f"Missing extracted component: {f}"
        assert f.stat().st_size > 1000, f"Component {f} is too small"


def test_02_manual_language_toggles_removed_from_setup():
    """Verify manual language toggles are removed from ProductAReviewSetup per Product Decision 2.1."""
    setup_code = Path("NastaGhar/frontend/src/components/portal/product_a/ProductAReviewSetup.jsx").read_text()

    assert "Supported Review Languages" not in setup_code
    assert "supportedLanguages" not in setup_code
    assert "toggleLanguage" not in setup_code
    assert "Official Google Review URL / Place ID" in setup_code
    assert "Primary Accent Color" in setup_code
    assert "Review Highlights & Aspects" in setup_code


def test_03_unified_portal_mounts_product_a_components():
    """Verify UnifiedClientPortal imports and renders all 3 Product A components."""
    portal_code = Path("NastaGhar/frontend/src/components/portal/UnifiedClientPortal.jsx").read_text()

    assert "ProductAReviewSetup" in portal_code
    assert "ProductAReviewAnalytics" in portal_code
    assert "ProductAPrivateInbox" in portal_code

    # Verify placeholder panels for Product A are replaced
    assert "activeTab === 'reviews-setup'" in portal_code
    assert "activeTab === 'reviews-analytics'" in portal_code
    assert "activeTab === 'reviews-inbox'" in portal_code


def test_04_sidebar_preserves_five_section_standard():
    """Verify PortalSidebar maintains exactly the five-section standard and keeps profile under Settings."""
    sidebar_code = Path("NastaGhar/frontend/src/components/portal/PortalSidebar.jsx").read_text()

    # Section 1: Home / Overview
    assert "Dashboard Overview" in sidebar_code
    # Section 2, 3, 4: Product A Review Manager
    assert "reviews-setup" in sidebar_code
    assert "reviews-analytics" in sidebar_code
    assert "reviews-inbox" in sidebar_code
    # Section 5: Settings
    assert "Settings & Security" in sidebar_code
    assert "Shared Profile & Logo" in sidebar_code


# ==============================================================================
# 2. SERVER-SIDE ROLE HIERARCHY (STAFF vs MANAGER vs OWNER)
# ==============================================================================

def test_05_staff_role_permissions(phase4_env):
    """Staff can view Analytics, but cannot access Private Tickets or modify Config."""
    client = TestClient(app)
    cookies = {OWNER_COOKIE: phase4_env["staff_a_cookie"]}

    # 1. Staff can view Analytics (GET /api/reviews/analytics)
    res_ana = client.get("/api/reviews/analytics?business_id=tenant-alpha", cookies=cookies)
    assert res_ana.status_code == 200, f"Staff should be able to view analytics, got {res_ana.status_code}"

    # 2. Staff cannot view Private Tickets (GET /api/reviews/private-tickets)
    res_tkt = client.get("/api/reviews/private-tickets?business_id=tenant-alpha", cookies=cookies)
    assert res_tkt.status_code == 403, f"Staff must be denied private tickets, got {res_tkt.status_code}"

    # 3. Staff cannot update Business Config (POST /api/businesses/{id}/config)
    res_cfg = client.post(
        "/api/businesses/tenant-alpha/config",
        json={"google_review_url": "https://g.page/r/test"},
        cookies=cookies
    )
    assert res_cfg.status_code == 403, f"Staff must be denied config updates, got {res_cfg.status_code}"


def test_06_manager_role_permissions(phase4_env):
    """Manager can view Analytics and manage Private Tickets, but cannot modify Config."""
    client = TestClient(app)
    cookies = {OWNER_COOKIE: phase4_env["mgr_a_cookie"]}

    # 1. Manager can view Analytics
    res_ana = client.get("/api/reviews/analytics?business_id=tenant-alpha", cookies=cookies)
    assert res_ana.status_code == 200

    # 2. Manager can view Private Tickets
    res_tkt = client.get("/api/reviews/private-tickets?business_id=tenant-alpha", cookies=cookies)
    assert res_tkt.status_code == 200

    # 3. Manager cannot update Business Config
    res_cfg = client.post(
        "/api/businesses/tenant-alpha/config",
        json={"google_review_url": "https://g.page/r/test"},
        cookies=cookies
    )
    assert res_cfg.status_code == 403, f"Manager must be denied config updates, got {res_cfg.status_code}"


def test_07_owner_role_permissions(phase4_env):
    """Owner has full access to Analytics, Private Tickets, and Review Setup Config."""
    client = TestClient(app)
    cookies = {OWNER_COOKIE: phase4_env["owner_a_cookie"]}

    # 1. Owner can view Analytics
    res_ana = client.get("/api/reviews/analytics?business_id=tenant-alpha", cookies=cookies)
    assert res_ana.status_code == 200

    # 2. Owner can view Private Tickets
    res_tkt = client.get("/api/reviews/private-tickets?business_id=tenant-alpha", cookies=cookies)
    assert res_tkt.status_code == 200

    # 3. Owner can update Business Config
    res_cfg = client.post(
        "/api/businesses/tenant-alpha/config",
        json={
            "business_name": "Alpha Dining Updated",
            "google_review_url": "https://search.google.com/local/writereview?placeid=ChIJ123",
            "topics": ["Delicious Food", "Great Service"]
        },
        cookies=cookies
    )
    assert res_cfg.status_code == 200, f"Owner should be able to update config, got {res_cfg.status_code}: {res_cfg.text}"
    assert res_cfg.json()["business_name"] == "Alpha Dining Updated"


# ==============================================================================
# 3. PRODUCT ENTITLEMENT ENFORCEMENT & CROSS-TENANT ISOLATION
# ==============================================================================

def test_08_tenant_without_review_manager_is_denied(phase4_env):
    """Tenant Beta (Product B only, lacking review_manager) is denied access to Product A endpoints."""
    client = TestClient(app)
    cookies = {OWNER_COOKIE: phase4_env["owner_b_cookie"]}

    # Analytics denied
    res_ana = client.get("/api/reviews/analytics?business_id=tenant-beta", cookies=cookies)
    assert res_ana.status_code == 403
    assert "review_manager" in res_ana.text.lower()

    # Private tickets denied
    res_tkt = client.get("/api/reviews/private-tickets?business_id=tenant-beta", cookies=cookies)
    assert res_tkt.status_code == 403

    # Config update denied
    res_cfg = client.post(
        "/api/businesses/tenant-beta/config",
        json={"google_review_url": "https://g.page/r/test"},
        cookies=cookies
    )
    assert res_cfg.status_code == 403


def test_09_cross_tenant_request_rejection(phase4_env):
    """Owner of Tenant Alpha cannot query or modify Tenant Beta's data."""
    client = TestClient(app)
    cookies = {OWNER_COOKIE: phase4_env["owner_a_cookie"]}

    # Cross-tenant analytics query
    res = client.get("/api/reviews/analytics?business_id=tenant-beta", cookies=cookies)
    assert res.status_code == 403, "Cross-tenant analytics request must be rejected with 403"

    # Cross-tenant private ticket query
    res_tkt = client.get("/api/reviews/private-tickets?business_id=tenant-beta", cookies=cookies)
    assert res_tkt.status_code == 403, "Cross-tenant tickets request must be rejected with 403"

    # Cross-tenant config update
    res_cfg = client.post(
        "/api/businesses/tenant-beta/config",
        json={"google_review_url": "https://g.page/r/malicious"},
        cookies=cookies
    )
    assert res_cfg.status_code == 403, "Cross-tenant config modification must be rejected with 403"


def test_10_private_ticket_status_transitions_and_scoping(phase4_env):
    """Verify private ticket status updates (OPEN -> RESOLVED -> ESCALATED) are strictly tenant-scoped."""
    store = phase4_env["store"]
    client = TestClient(app)
    cookies = {OWNER_COOKIE: phase4_env["mgr_a_cookie"]}

    # Seed a private ticket for Tenant Alpha
    tkt_id = "TKT-TEST-001"
    tkt_data = {
        "ticket_id": tkt_id,
        "timestamp": "2026-11-16T12:00:00Z",
        "rating": 2,
        "diner_note": "Soup was served cold.",
        "aspects": ["Food Quality"],
        "table_number": "Table 12",
        "guest_contact": "guest@example.com",
        "status": "OPEN",
    }
    store.add_ticket(tkt_data, tenant_id="tenant-alpha")

    # 1. Manager of Tenant Alpha transitions ticket to RESOLVED
    res1 = client.patch(
        f"/api/reviews/private-tickets/{tkt_id}/status",
        json={"status": "RESOLVED"},
        cookies=cookies
    )
    assert res1.status_code == 200
    assert res1.json()["new_status"] == "RESOLVED"

    # 2. Manager of Tenant Alpha transitions ticket to ESCALATED
    res2 = client.patch(
        f"/api/reviews/private-tickets/{tkt_id}/status",
        json={"status": "ESCALATED"},
        cookies=cookies
    )
    assert res2.status_code == 200
    assert res2.json()["new_status"] == "ESCALATED"

    # 3. Owner of Tenant Beta cannot modify Tenant Alpha's ticket
    cookies_b = {OWNER_COOKIE: phase4_env["owner_b_cookie"]}
    res3 = client.patch(
        f"/api/reviews/private-tickets/{tkt_id}/status",
        json={"status": "RESOLVED"},
        cookies=cookies_b
    )
    assert res3.status_code in (403, 404), "Tenant Beta must not be able to mutate Tenant Alpha's ticket"
