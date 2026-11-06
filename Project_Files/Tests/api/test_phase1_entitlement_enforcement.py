"""
VRAJA AI — Phase 1 Entitlement & Authorization Foundation Tests.

Validates:
1. Product A-only tenants (['review_manager']) can access Product A APIs, but are blocked from Product B APIs.
2. Product B-only tenants (['digital_card']) can access Product B APIs, but are blocked from Product A APIs.
3. Both products tenants (['review_manager', 'digital_card']) can access both products without restriction.
4. Neither product tenants ([]) are rejected from both products' protected functionality.
5. Cross-tenant isolation: Tenant A cannot access Tenant B's data or configuration.
6. Platform-admin separation: Regular tenant owners cannot access /api/platform/* endpoints or self-assign entitlements.
"""

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
def phase1_setup(tmp_path, monkeypatch):
    """Sets up an isolated SQLite database and test tenants for all 4 combinations."""
    db_path = tmp_path / "test_phase1_entitlements.sqlite3"
    docs_path = tmp_path / "test_phase1_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))

    # Helper to create user + session token
    def make_user_and_session(email: str, tenant_id: str, role: str = "owner", is_admin: int = 0) -> str:
        user = store.create_user(
            email=email,
            password_hash=hash_password("SecurePass123!"),
            display_name=email.split("@")[0].title(),
            is_active=1,
            is_platform_admin=is_admin,
        )
        if tenant_id:
            store.add_membership(user["id"], tenant_id, role=role)
        raw_token = generate_session_token()
        hashed = hash_token(raw_token)
        now = time.time()
        with store._connect() as db:
            db.execute(
                "INSERT INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (hashed, user["id"], tenant_id or "default_business", now, now + SESSION_TTL_SECONDS)
            )
        return raw_token

    # 1. Platform Admin
    admin_token = make_user_and_session("superadmin@vraja.ai", "default_business", role="owner", is_admin=1)

    # 2. Combination 1: Product A Only ('review_manager')
    store.upsert_tenant({
        "id": "tenant_a_only",
        "business_name": "Review Assistant Only Cafe",
        "status": "active",
        "platform": "google",
        "review_url": "https://g.page/r/tenant_a_only",
        "category": "Cafe",
        "entitlements": ["review_manager"],
    })
    token_a_only = make_user_and_session("owner@tenant-a.com", "tenant_a_only", role="owner")

    # 3. Combination 2: Product B Only ('digital_card')
    store.upsert_tenant({
        "id": "tenant_b_only",
        "business_name": "Digital Card Only Boutique",
        "status": "active",
        "platform": "google",
        "review_url": "https://g.page/r/tenant_b_only",
        "category": "Boutique",
        "entitlements": ["digital_card"],
    })
    store.upsert_business_profile("tenant_b_only", {
        "tagline": "Exclusive Luxury Boutique",
        "phone_number": "+91 98765 00002",
        "is_published": 1,
    })
    token_b_only = make_user_and_session("owner@tenant-b.com", "tenant_b_only", role="owner")

    # 4. Combination 3: Both Products ('review_manager' and 'digital_card')
    store.upsert_tenant({
        "id": "tenant_both",
        "business_name": "Grand Palace Hotel (Both Products)",
        "status": "active",
        "platform": "google",
        "review_url": "https://g.page/r/tenant_both",
        "category": "Hotel",
        "entitlements": ["review_manager", "digital_card"],
    })
    store.upsert_business_profile("tenant_both", {
        "tagline": "Luxury Living & Fine Dining",
        "phone_number": "+91 98765 00003",
        "is_published": 1,
    })
    token_both = make_user_and_session("owner@tenant-both.com", "tenant_both", role="owner")

    # 5. Combination 4: Neither Product ([])
    store.upsert_tenant({
        "id": "tenant_neither",
        "business_name": "Unsubscribed Tenant (Neither Product)",
        "status": "active",
        "platform": "google",
        "review_url": "https://g.page/r/tenant_neither",
        "category": "General",
        "entitlements": [],
    })
    token_neither = make_user_and_session("owner@tenant-neither.com", "tenant_neither", role="owner")

    return {
        "store": store,
        "admin_token": admin_token,
        "token_a_only": token_a_only,
        "token_b_only": token_b_only,
        "token_both": token_both,
        "token_neither": token_neither,
    }


# ==============================================================================
# COMBINATION 1: PRODUCT A ONLY
# ==============================================================================

def test_combination_1_product_a_only_can_access_product_a_endpoints(phase1_setup):
    """Tenant with ['review_manager'] can successfully execute all Product A operations."""
    token = phase1_setup["token_a_only"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, token)

        # 1. Update Product A config (Fix 1 verification)
        res_cfg = client.post("/api/businesses/tenant_a_only/config", json={
            "business_name": "Review Assistant Only Cafe Updated",
            "google_review_url": "https://g.page/r/tenant_a_only/updated",
            "category": "Cafe & Bakery",
        })
        assert res_cfg.status_code == 200
        assert res_cfg.json()["business_name"] == "Review Assistant Only Cafe Updated"

        # 2. Get analytics
        res_ana = client.get("/api/reviews/analytics?business_id=tenant_a_only")
        assert res_ana.status_code == 200

        # 3. Get private tickets
        res_tix = client.get("/api/reviews/private-tickets?business_id=tenant_a_only")
        assert res_tix.status_code == 200
        assert isinstance(res_tix.json(), list)

        # 4. Public review link
        client.cookies.delete(OWNER_COOKIE)
        res_link = client.get("/api/businesses/tenant_a_only/review-link")
        assert res_link.status_code == 200
        assert res_link.json()["business_id"] == "tenant_a_only"

        # 5. Public review session creation
        res_sess = client.post("/api/reviews/session", json={
            "business_id": "tenant_a_only",
            "table_number": "Table 5",
        })
        assert res_sess.status_code == 200
        session_id = res_sess.json()["session_id"]

        # 6. Analytics event
        res_ev = client.post("/api/reviews/events", json={
            "session_id": session_id,
            "event_name": "google_review_link_clicked",
            "metadata": {"business_id": "tenant_a_only"},
        })
        assert res_ev.status_code == 200

        # 7. Review ideas generation
        res_ideas = client.post("/api/reviews/ideas", json={
            "business_id": "tenant_a_only",
            "rating": 5,
            "aspects": ["Food Quality", "Service"],
        })
        assert res_ideas.status_code == 200

        # 8. Private feedback submission
        res_fb = client.post("/api/reviews/private-feedback", json={
            "business_id": "tenant_a_only",
            "rating": 2,
            "diner_note": "Table was shaky.",
            "guest_contact": "+91 99999 11111",
        })
        assert res_fb.status_code == 200


def test_combination_1_product_a_only_cannot_access_product_b_endpoints(phase1_setup):
    """Tenant with ['review_manager'] is strictly rejected from all Product B endpoints."""
    token = phase1_setup["token_a_only"]

    with TestClient(app) as client:
        # Public Card check: suppressed (404)
        res_card = client.get("/api/businesses/tenant_a_only/card")
        assert res_card.status_code == 404

        # QR info: blocked (403)
        res_qr = client.get("/api/businesses/tenant_a_only/card/qr-info")
        assert res_qr.status_code == 403

        # Authenticated owner trying to view/edit Digital Card profile -> 403 Forbidden
        client.cookies.set(OWNER_COOKIE, token)

        res_prof = client.get("/api/businesses/tenant_a_only/profile")
        assert res_prof.status_code == 403
        assert "digital_card" in res_prof.json().get("detail", "")

        res_prof_edit = client.put("/api/businesses/tenant_a_only/profile", json={
            "tagline": "Attempting unauthorized card",
        })
        assert res_prof_edit.status_code == 403
        assert "digital_card" in res_prof_edit.json().get("detail", "")

        # Authenticated owner trying to list/upload documents -> 403 Forbidden
        res_docs = client.get("/api/businesses/tenant_a_only/documents")
        assert res_docs.status_code == 403
        assert "digital_card" in res_docs.json().get("detail", "")


# ==============================================================================
# COMBINATION 2: PRODUCT B ONLY
# ==============================================================================

def test_combination_2_product_b_only_can_access_product_b_endpoints(phase1_setup):
    """Tenant with ['digital_card'] can successfully execute all Product B operations."""
    token = phase1_setup["token_b_only"]

    with TestClient(app) as client:
        # 1. Public digital card view
        res_card = client.get("/api/businesses/tenant_b_only/card")
        assert res_card.status_code == 200
        assert res_card.json()["tenant_id"] == "tenant_b_only"

        # 2. Card QR info
        res_qr = client.get("/api/businesses/tenant_b_only/card/qr-info")
        assert res_qr.status_code == 200

        # 3. Authenticated profile view & update
        client.cookies.set(OWNER_COOKIE, token)
        res_prof = client.get("/api/businesses/tenant_b_only/profile")
        assert res_prof.status_code == 200

        res_prof_update = client.put("/api/businesses/tenant_b_only/profile", json={
            "tagline": "Exclusive Luxury Boutique - Updated",
            "phone_number": "+91 98765 00002",
        })
        assert res_prof_update.status_code == 200
        assert res_prof_update.json()["tagline"] == "Exclusive Luxury Boutique - Updated"

        # 4. List documents
        res_docs = client.get("/api/businesses/tenant_b_only/documents")
        assert res_docs.status_code == 200


def test_combination_2_product_b_only_cannot_access_product_a_endpoints(phase1_setup):
    """Tenant with ['digital_card'] is strictly rejected from all Product A endpoints."""
    token = phase1_setup["token_b_only"]

    with TestClient(app) as client:
        # Public review link -> 403 Forbidden
        res_link = client.get("/api/businesses/tenant_b_only/review-link")
        assert res_link.status_code == 403
        assert "review_manager" in res_link.json().get("detail", "")

        # Public review session -> 403 Forbidden
        res_sess = client.post("/api/reviews/session", json={
            "business_id": "tenant_b_only",
            "table_number": "Table 1",
        })
        assert res_sess.status_code == 403
        assert "review_manager" in res_sess.json().get("detail", "")

        # Public review ideas -> 403 Forbidden
        res_ideas = client.post("/api/reviews/ideas", json={
            "business_id": "tenant_b_only",
            "rating": 5,
            "aspects": ["Quality"],
        })
        assert res_ideas.status_code == 403
        assert "review_manager" in res_ideas.json().get("detail", "")

        # Public events recording -> 403 Forbidden
        res_ev = client.post("/api/reviews/events", json={
            "session_id": "dummy-session",
            "event_name": "google_review_link_clicked",
            "metadata": {"business_id": "tenant_b_only"},
        })
        assert res_ev.status_code == 403
        assert "review_manager" in res_ev.json().get("detail", "")

        # Public private feedback -> 403 Forbidden
        res_fb = client.post("/api/reviews/private-feedback", json={
            "business_id": "tenant_b_only",
            "rating": 1,
            "diner_note": "Not satisfied.",
        })
        assert res_fb.status_code == 403
        assert "review_manager" in res_fb.json().get("detail", "")

        # Authenticated owner trying to configure Product A -> 403 Forbidden
        client.cookies.set(OWNER_COOKIE, token)
        res_cfg = client.post("/api/businesses/tenant_b_only/config", json={
            "google_review_url": "https://g.page/r/hacked",
        })
        assert res_cfg.status_code == 403
        assert "review_manager" in res_cfg.json().get("detail", "")

        # Authenticated owner trying to view analytics -> 403 Forbidden
        res_ana = client.get("/api/reviews/analytics?business_id=tenant_b_only")
        assert res_ana.status_code == 403
        assert "review_manager" in res_ana.json().get("detail", "")

        # Authenticated owner trying to view private tickets -> 403 Forbidden
        res_tix = client.get("/api/reviews/private-tickets?business_id=tenant_b_only")
        assert res_tix.status_code == 403
        assert "review_manager" in res_tix.json().get("detail", "")


# ==============================================================================
# COMBINATION 3: BOTH PRODUCTS
# ==============================================================================

def test_combination_3_both_products_can_access_both_suites(phase1_setup):
    """Tenant with ['review_manager', 'digital_card'] has full access to both products."""
    token = phase1_setup["token_both"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, token)

        # Product A: Config & Analytics
        res_cfg = client.post("/api/businesses/tenant_both/config", json={
            "business_name": "Grand Palace Hotel (Configured)",
            "google_review_url": "https://g.page/r/tenant_both/reviews",
        })
        assert res_cfg.status_code == 200

        res_ana = client.get("/api/reviews/analytics?business_id=tenant_both")
        assert res_ana.status_code == 200

        res_tix = client.get("/api/reviews/private-tickets?business_id=tenant_both")
        assert res_tix.status_code == 200

        # Product B: Profile & Documents
        res_prof = client.put("/api/businesses/tenant_both/profile", json={
            "tagline": "Grand Palace - Unrivaled Luxury",
        })
        assert res_prof.status_code == 200

        res_docs = client.get("/api/businesses/tenant_both/documents")
        assert res_docs.status_code == 200

        # Public endpoints for both products
        client.cookies.delete(OWNER_COOKIE)

        # Product A public review link
        res_link = client.get("/api/businesses/tenant_both/review-link")
        assert res_link.status_code == 200

        # Product B public digital card
        res_card = client.get("/api/businesses/tenant_both/card")
        assert res_card.status_code == 200


# ==============================================================================
# COMBINATION 4: NEITHER PRODUCT
# ==============================================================================

def test_combination_4_neither_product_completely_rejected(phase1_setup):
    """Tenant with [] entitlements cannot access any Product A or Product B protected endpoints."""
    token = phase1_setup["token_neither"]

    with TestClient(app) as client:
        # Public calls rejected
        assert client.get("/api/businesses/tenant_neither/review-link").status_code == 403
        assert client.post("/api/reviews/session", json={"business_id": "tenant_neither"}).status_code == 403
        assert client.post("/api/reviews/events", json={"session_id": "s", "event_name": "session_created", "metadata": {"business_id": "tenant_neither"}}).status_code == 403
        assert client.post("/api/reviews/ideas", json={"business_id": "tenant_neither", "rating": 5}).status_code == 403
        assert client.post("/api/reviews/private-feedback", json={"business_id": "tenant_neither", "rating": 3, "diner_note": "None"}).status_code == 403

        # Public Product B card suppressed
        assert client.get("/api/businesses/tenant_neither/card").status_code == 404

        # Authenticated owner calls rejected
        client.cookies.set(OWNER_COOKIE, token)
        assert client.post("/api/businesses/tenant_neither/config", json={"google_review_url": "https://test.com"}).status_code == 403
        assert client.get("/api/reviews/analytics?business_id=tenant_neither").status_code == 403
        assert client.get("/api/reviews/private-tickets?business_id=tenant_neither").status_code == 403
        assert client.get("/api/businesses/tenant_neither/profile").status_code == 403
        assert client.put("/api/businesses/tenant_neither/profile", json={"tagline": "test"}).status_code == 403
        assert client.get("/api/businesses/tenant_neither/documents").status_code == 403


# ==============================================================================
# CROSS-TENANT ISOLATION & RBAC BOUNDARIES
# ==============================================================================

def test_cross_tenant_access_strictly_rejected(phase1_setup):
    """Authenticated owner of Tenant A cannot query or mutate Tenant B."""
    token_a = phase1_setup["token_a_only"]

    with TestClient(app) as client:
        client.cookies.set(OWNER_COOKIE, token_a)

        # Tenant A trying to mutate Tenant B's Product A config
        res_cfg = client.post("/api/businesses/tenant_b_only/config", json={
            "google_review_url": "https://hacked.com",
        })
        assert res_cfg.status_code == 403
        assert "Access denied" in res_cfg.json().get("detail", "")

        # Tenant A trying to view Tenant Both's analytics
        res_ana = client.get("/api/reviews/analytics?business_id=tenant_both")
        assert res_ana.status_code == 403
        assert "Access denied" in res_ana.json().get("detail", "")

        # Tenant A trying to view Tenant Both's private tickets
        res_tix = client.get("/api/reviews/private-tickets?business_id=tenant_both")
        assert res_tix.status_code == 403
        assert "Access denied" in res_tix.json().get("detail", "")

        # Tenant A trying to mutate Tenant Both's profile
        res_prof = client.put("/api/businesses/tenant_both/profile", json={
            "tagline": "Hacked Profile",
        })
        assert res_prof.status_code == 403
        assert "Access denied" in res_prof.json().get("detail", "")


def test_platform_admin_vs_tenant_owner_separation(phase1_setup):
    """Platform admin endpoints cannot be reached by tenant owners, and owners cannot self-assign entitlements."""
    token_both = phase1_setup["token_both"]
    admin_token = phase1_setup["admin_token"]
    store = phase1_setup["store"]

    with TestClient(app) as client:
        # 1. Tenant Owner trying to access platform admin endpoints -> 403 Forbidden
        client.cookies.set(OWNER_COOKIE, token_both)

        res_list = client.get("/api/platform/tenants")
        assert res_list.status_code == 403
        assert "Platform administrator" in res_list.json().get("detail", "")

        res_onboard = client.post("/api/platform/tenants", json={
            "tenant_id": "malicious_tenant",
            "business_name": "Malicious",
            "owner_email": "attacker@evil.com",
            "owner_password": "Pass",
            "entitlements": ["review_manager", "digital_card"],
        })
        assert res_onboard.status_code == 403

        res_ent = client.patch("/api/platform/tenants/tenant_both/entitlements", json={
            "entitlements": ["review_manager"],
        })
        assert res_ent.status_code == 403

        # 2. Tenant Owner cannot escalate/change entitlements via /businesses/{id}/config
        cfg_res = client.post("/api/businesses/tenant_both/config", json={
            "business_name": "Grand Palace Hotel",
            "google_review_url": "https://g.page/r/test",
            "entitlements": ["review_manager"],  # Trying to change entitlements
        })
        assert cfg_res.status_code == 200
        # In the database, entitlements must remain unchanged (both products)
        db_tenant = store.get_tenant("tenant_both")
        assert set(db_tenant["entitlements"]) == {"review_manager", "digital_card"}

        # 3. Platform Admin CAN access platform admin endpoints
        client.cookies.set(OWNER_COOKIE, admin_token)

        res_admin_list = client.get("/api/platform/tenants")
        assert res_admin_list.status_code == 200
        assert any(t["id"] == "tenant_both" for t in res_admin_list.json())

        # Platform Admin can change entitlements
        res_admin_patch = client.patch("/api/platform/tenants/tenant_both/entitlements", json={
            "entitlements": ["review_manager"],
        })
        assert res_admin_patch.status_code == 200
        assert store.get_tenant("tenant_both")["entitlements"] == ["review_manager"]
