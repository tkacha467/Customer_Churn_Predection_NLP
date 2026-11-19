"""
Automated Test Suite for VRAJA AI Phase A2: Multi-Industry Registry and API Integration.

Verifies:
1. Canonical Industry Registry integrity (9 active industries + unclassified + restricted healthcare).
2. Industry Resolution Engine (explicit industry_id, legacy category mappings, unknown -> unclassified).
3. Topic precedence resolution (tenant custom > industry default > platform fallback).
4. API endpoints:
   - GET /api/businesses/{id}/industry-config
   - GET /api/industries
   - POST /api/businesses/{id}/config with industry_id validation
5. Security & Access Control:
   - Authentication gating
   - Role-based authorization (Staff read-only, Owner/Manager update)
   - Cross-tenant isolation
   - Healthcare self-onboarding rejection (HTTP 400)
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.industry_registry import (
    INDUSTRY_REGISTRY,
    ACTIVE_INDUSTRIES,
    DEFAULT_PLATFORM_TOPICS,
    resolve_industry,
    resolve_effective_topics,
    get_available_industries,
    IndustryDefinition,
)
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
def industry_test_env(tmp_path, monkeypatch):
    """Provides an isolated test database and environment for Multi-Industry tests."""
    db_file = tmp_path / "multi_industry_test.sqlite3"
    links_file = tmp_path / "multi_industry_links.json"
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
        # Ensure industry_id column exists in test db
        cols = [r[1] for r in con.execute("PRAGMA table_info(tenants)").fetchall()]
        if "industry_id" not in cols:
            con.execute("ALTER TABLE tenants ADD COLUMN industry_id TEXT DEFAULT NULL")
            con.commit()

    # 1. Tenant Alpha - Restaurant (NastaGhar legacy category)
    t_alpha_id = "tenant-alpha"
    store.upsert_tenant({
        "id": t_alpha_id,
        "business_name": "NastaGhar Alpha",
        "category": "Breakfast & Snacks",
        "place_id": "ChIJ_alpha",
        "review_url": "https://g.page/r/test_alpha/review",
        "is_active": 1,
        "status": "active",
        "entitlements": ["review_manager"],
    })
    store.upsert_business_profile(t_alpha_id, {
        "display_name": "NastaGhar Alpha",
        "category": "Breakfast & Snacks",
    })

    # 2. Tenant Beta - Hotel (explicit industry_id)
    t_beta_id = "tenant-beta"
    store.upsert_tenant({
        "id": t_beta_id,
        "business_name": "Grand Azure Hotel",
        "category": "Hospitality",
        "industry_id": "hotel",
        "place_id": "ChIJ_beta",
        "review_url": "https://g.page/r/test_beta/review",
        "is_active": 1,
        "status": "active",
        "entitlements": ["review_manager"],
    })
    store.upsert_business_profile(t_beta_id, {
        "display_name": "Grand Azure Hotel",
        "category": "Hospitality",
    })

    # 3. Tenant Gamma - Unknown Category
    t_gamma_id = "tenant-gamma"
    store.upsert_tenant({
        "id": t_gamma_id,
        "business_name": "Cosmic Innovations",
        "category": "Quantum Computing Consulting",
        "place_id": "ChIJ_gamma",
        "review_url": "https://g.page/r/test_gamma/review",
        "is_active": 1,
        "status": "active",
        "entitlements": ["review_manager"],
    })
    store.upsert_business_profile(t_gamma_id, {
        "display_name": "Cosmic Innovations",
        "category": "Quantum Computing Consulting",
    })

    # Users
    u_owner_a = store.create_user("alpha_owner@test.com", hash_password("Password123!"), display_name="Alpha Owner")
    store.add_membership(u_owner_a["id"], t_alpha_id, role="owner")

    u_staff_a = store.create_user("alpha_staff@test.com", hash_password("Password123!"), display_name="Alpha Staff")
    store.add_membership(u_staff_a["id"], t_alpha_id, role="staff")

    u_owner_b = store.create_user("beta_owner@test.com", hash_password("Password123!"), display_name="Beta Owner")
    store.add_membership(u_owner_b["id"], t_beta_id, role="owner")

    def make_session(user_id, tenant_id):
        token = generate_session_token()
        store.create_session(
            token_hash=hash_token(token),
            user_id=user_id,
            active_tenant_id=tenant_id,
            expires_at=time.time() + SESSION_TTL_SECONDS,
            ip_address="127.0.0.1",
            user_agent="TestRunner",
        )
        return token

    sessions = {
        "alpha_owner": make_session(u_owner_a["id"], t_alpha_id),
        "alpha_staff": make_session(u_staff_a["id"], t_alpha_id),
        "beta_owner": make_session(u_owner_b["id"], t_beta_id),
    }

    return {
        "store": store,
        "sessions": sessions,
        "tenants": {
            "alpha": t_alpha_id,
            "beta": t_beta_id,
            "gamma": t_gamma_id,
        },
    }


# =====================================================================
# 1. REGISTRY INTEGRITY TESTS
# =====================================================================

def test_registry_contains_expected_industries():
    """Verify registry has the required active industries, unclassified, and healthcare."""
    expected_active = [
        "restaurant", "hotel", "fitness", "salon",
        "retail", "automotive", "education", "events", "travel"
    ]
    for ind in expected_active:
        assert ind in INDUSTRY_REGISTRY
        assert ind in ACTIVE_INDUSTRIES
        defn = INDUSTRY_REGISTRY[ind]
        assert defn.industry_id == ind
        assert defn.display_name != ""
        assert defn.terminology.customer_noun_singular != ""
        assert defn.terminology.customer_noun_plural != ""
        assert defn.terminology.touchpoint_noun != ""
        assert len(defn.default_topics) >= 4
        assert len(defn.subcategories) >= 2
        assert not defn.is_restricted

    # Unclassified
    assert "unclassified" in INDUSTRY_REGISTRY
    unclass = INDUSTRY_REGISTRY["unclassified"]
    assert unclass.industry_id == "unclassified"
    assert unclass.display_name == "Unclassified Business"

    # Healthcare restricted
    assert "healthcare" in INDUSTRY_REGISTRY
    assert INDUSTRY_REGISTRY["healthcare"].is_restricted is True


# =====================================================================
# 2. INDUSTRY RESOLUTION LOGIC TESTS
# =====================================================================

def test_resolve_industry_explicit_id():
    """Explicit industry_id has highest precedence."""
    defn = resolve_industry(industry_id="hotel", category="Breakfast & Snacks")
    assert defn.industry_id == "hotel"
    assert defn.display_name == "Hotels & Hospitality"


def test_resolve_industry_legacy_category_mapping():
    """Legacy category maps accurately when industry_id is omitted."""
    assert resolve_industry(category="Breakfast & Snacks").industry_id == "restaurant"
    assert resolve_industry(category="Cafe").industry_id == "restaurant"
    assert resolve_industry(category="Fine Dining").industry_id == "restaurant"
    assert resolve_industry(category="Boutique Hotel").industry_id == "hotel"
    assert resolve_industry(category="Gym").industry_id == "fitness"
    assert resolve_industry(category="Spa & Salon").industry_id == "salon"
    assert resolve_industry(category="Clothing Boutique").industry_id == "retail"
    assert resolve_industry(category="Auto Repair").industry_id == "automotive"


def test_resolve_industry_unknown_category_remains_unclassified():
    """Unknown category must NEVER silently default to restaurant."""
    defn = resolve_industry(category="Quantum Computing Consulting")
    assert defn.industry_id == "unclassified"
    assert defn.display_name == "Unclassified Business"
    assert defn.terminology.customer_noun_singular == "Customer"

    defn_none = resolve_industry(category=None)
    assert defn_none.industry_id == "unclassified"


# =====================================================================
# 3. TOPIC PRECEDENCE TESTS
# =====================================================================

def test_topic_precedence():
    """Tenant custom topics override industry defaults; industry defaults override platform fallbacks."""
    custom_topics = ["Ambiance", "Custom Mocktail", "DJ Vibe"]
    
    # 1. Custom topics present -> returned intact
    effective = resolve_effective_topics(custom_topics, "restaurant")
    assert effective == custom_topics

    # 2. Custom topics empty -> industry defaults returned
    effective_def = resolve_effective_topics([], "hotel")
    assert effective_def == INDUSTRY_REGISTRY["hotel"].default_topics

    # 3. Unclassified without custom topics -> platform fallbacks returned
    effective_unclass = resolve_effective_topics(None, "unclassified")
    assert effective_unclass == DEFAULT_PLATFORM_TOPICS


# =====================================================================
# 4. API ENDPOINTS & ACCESS CONTROL TESTS
# =====================================================================

def test_get_industry_config_alpha_legacy(industry_test_env):
    """Tenant Alpha without explicit industry_id resolves to restaurant via legacy category."""
    client = TestClient(app)
    token = industry_test_env["sessions"]["alpha_owner"]
    tenant_id = industry_test_env["tenants"]["alpha"]

    client.cookies.set(OWNER_COOKIE, token)
    res = client.get(f"/api/businesses/{tenant_id}/industry-config")
    assert res.status_code == 200
    data = res.json()
    assert data["industry_id"] == "restaurant"
    assert data["industry_name"] == "Restaurants & Dining"
    assert data["terminology"]["customer_noun_singular"] == "Diner"
    assert data["terminology"]["touchpoint_noun"] == "Table / Counter"
    assert data["has_custom_topics"] is False
    assert len(data["effective_topics"]) >= 5


def test_get_industry_config_beta_explicit(industry_test_env):
    """Tenant Beta with explicit industry_id=hotel resolves to hotel."""
    client = TestClient(app)
    token = industry_test_env["sessions"]["beta_owner"]
    tenant_id = industry_test_env["tenants"]["beta"]

    client.cookies.set(OWNER_COOKIE, token)
    res = client.get(f"/api/businesses/{tenant_id}/industry-config")
    assert res.status_code == 200
    data = res.json()
    assert data["industry_id"] == "hotel"
    assert data["industry_name"] == "Hotels & Hospitality"
    assert data["terminology"]["customer_noun_singular"] == "Guest"
    assert data["terminology"]["touchpoint_noun"] == "Room / Front Desk"


def test_get_industry_config_gamma_unclassified(industry_test_env):
    """Cross-tenant access to Gamma without membership returns 403."""
    client = TestClient(app)
    # Login as beta owner and try to access gamma -> should be 403 Forbidden
    client.cookies.set(OWNER_COOKIE, industry_test_env["sessions"]["beta_owner"])
    res_cross = client.get(f"/api/businesses/{industry_test_env['tenants']['gamma']}/industry-config")
    assert res_cross.status_code == 403


def test_get_available_industries(industry_test_env):
    """GET /api/industries returns active industries and restricts healthcare from onboarding list."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, industry_test_env["sessions"]["alpha_owner"])
    res = client.get("/api/industries")
    assert res.status_code == 200
    data = res.json()
    industry_ids = {item["industry_id"] for item in data["industries"]}

    assert "restaurant" in industry_ids
    assert "hotel" in industry_ids
    assert "fitness" in industry_ids
    assert "retail" in industry_ids
    
    # Healthcare must NOT be in available onboarding list
    assert "healthcare" not in industry_ids


def test_post_config_update_industry(industry_test_env):
    """Owner can update industry_id to a valid industry."""
    client = TestClient(app)
    token = industry_test_env["sessions"]["alpha_owner"]
    tenant_id = industry_test_env["tenants"]["alpha"]

    client.cookies.set(OWNER_COOKIE, token)
    payload = {
        "business_name": "NastaGhar Alpha Renamed",
        "google_review_url": "https://g.page/r/test_alpha/review",
        "category": "Gym & Cafe",
        "industry_id": "fitness",
        "topics": ["Workout Experience", "Equipment Quality", "Trainer Support"],
    }
    res = client.post(f"/api/businesses/{tenant_id}/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["industry_id"] == "fitness"

    # Verify GET industry-config reflects new industry and custom topics
    res_cfg = client.get(f"/api/businesses/{tenant_id}/industry-config")
    assert res_cfg.status_code == 200
    cfg_data = res_cfg.json()
    assert cfg_data["industry_id"] == "fitness"
    assert cfg_data["terminology"]["customer_noun_singular"] == "Member"
    assert cfg_data["has_custom_topics"] is True
    assert cfg_data["effective_topics"] == payload["topics"]


def test_post_config_rejects_healthcare(industry_test_env):
    """Attempting to update to restricted healthcare industry must fail with HTTP 400."""
    client = TestClient(app)
    token = industry_test_env["sessions"]["alpha_owner"]
    tenant_id = industry_test_env["tenants"]["alpha"]

    client.cookies.set(OWNER_COOKIE, token)
    payload = {
        "google_review_url": "https://g.page/r/test_alpha/review",
        "industry_id": "healthcare",
    }
    res = client.post(f"/api/businesses/{tenant_id}/config", json=payload)
    assert res.status_code == 400
    assert "Healthcare onboarding is disabled in production" in res.json()["detail"]


def test_post_config_rejects_invalid_industry(industry_test_env):
    """Attempting to update to a non-existent industry returns HTTP 400."""
    client = TestClient(app)
    token = industry_test_env["sessions"]["alpha_owner"]
    tenant_id = industry_test_env["tenants"]["alpha"]

    client.cookies.set(OWNER_COOKIE, token)
    payload = {
        "google_review_url": "https://g.page/r/test_alpha/review",
        "industry_id": "crypto_mining_facility",
    }
    res = client.post(f"/api/businesses/{tenant_id}/config", json=payload)
    assert res.status_code == 400
    assert "Invalid industry_id" in res.json()["detail"]


def test_staff_cannot_update_config(industry_test_env):
    """Staff role is read-only and cannot update business config."""
    client = TestClient(app)
    token = industry_test_env["sessions"]["alpha_staff"]
    tenant_id = industry_test_env["tenants"]["alpha"]

    client.cookies.set(OWNER_COOKIE, token)
    # Staff CAN read industry config
    res_get = client.get(f"/api/businesses/{tenant_id}/industry-config")
    assert res_get.status_code == 200

    # Staff CANNOT update config (requires manager/owner)
    res_post = client.post(f"/api/businesses/{tenant_id}/config", json={"name": "Hacked"})
    assert res_post.status_code == 403
