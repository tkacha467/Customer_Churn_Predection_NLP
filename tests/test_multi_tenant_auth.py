"""
Comprehensive Automated Test Suite for NastaGhar Multi-Tenant Architecture.
Tests authentication, tenant-bound authorization, role hierarchies, session lifecycle,
CSRF protection, concurrent isolation, and migration integrity.
"""

import os
import time
import tempfile
import threading
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.review_assistant.auth import (
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    _login_attempts,
    _login_lock,
    get_store,
)
from api.review_assistant.storage import ReviewStore
from api.review_assistant.migration import migrate_database


@pytest.fixture(autouse=True)
def setup_auth_environment():
    """Sets up synthetic isolated test users and tenants in the test SQLite database and resets rate limits."""
    with _login_lock:
        _login_attempts.clear()

    store = get_store()
    
    # 1. Create Tenant Alpha & Tenant Beta
    store.upsert_tenant({
        "id": "tenant_alpha",
        "business_name": "Cafe Alpha",
        "review_url": "https://g.page/r/alpha/review",
        "category": "Cafe",
        "description": "Artisan coffee in Alpha",
        "topics": ["Coffee", "Bakery"],
        "primary_accent": "#059669"
    })
    store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Restaurant Beta",
        "review_url": "https://g.page/r/beta/review",
        "category": "Restaurant",
        "description": "Italian dining in Beta",
        "topics": ["Pasta", "Wine"],
        "primary_accent": "#dc2626"
    })

    # 2. Create Users
    # Owner Alpha (only owns Alpha)
    if not store.get_user_by_email("owner_alpha@test.com"):
        owner_alpha = store.create_user("owner_alpha@test.com", hash_password("PasswordAlpha123!"), "Owner Alpha")
        store.add_membership(owner_alpha["id"], "tenant_alpha", role="owner")

    # Owner Beta (only owns Beta)
    if not store.get_user_by_email("owner_beta@test.com"):
        owner_beta = store.create_user("owner_beta@test.com", hash_password("PasswordBeta123!"), "Owner Beta")
        store.add_membership(owner_beta["id"], "tenant_beta", role="owner")

    # Multi-tenant User (manager in Alpha, staff in Beta)
    if not store.get_user_by_email("multi_user@test.com"):
        user_multi = store.create_user("multi_user@test.com", hash_password("PasswordMulti123!"), "Multi User")
        store.add_membership(user_multi["id"], "tenant_alpha", role="manager")
        store.add_membership(user_multi["id"], "tenant_beta", role="staff")

    # Staff Alpha (only staff in Alpha)
    if not store.get_user_by_email("staff_alpha@test.com"):
        staff_alpha = store.create_user("staff_alpha@test.com", hash_password("PasswordStaff123!"), "Staff Alpha")
        store.add_membership(staff_alpha["id"], "tenant_alpha", role="staff")


def login_client(email: str, password: str, tenant_id: str = None) -> TestClient:
    client = TestClient(app)
    payload = {"email": email, "password": password}
    if tenant_id:
        payload["tenant_id"] = tenant_id
    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return client


# ─── 1. OWNER ACCESS & AUTHORIZATION ──────────────────────────────────────────

def test_1_owner_alpha_can_access_authorized_alpha_data():
    client = login_client("owner_alpha@test.com", "PasswordAlpha123!")
    
    # Can read session
    sess_res = client.get("/api/auth/session")
    assert sess_res.status_code == 200
    sess_data = sess_res.json()
    assert sess_data["user"]["email"] == "owner_alpha@test.com"
    assert sess_data["active_tenant"]["id"] == "tenant_alpha"
    assert sess_data["active_tenant"]["role"] == "owner"

    # Can update Alpha config
    cfg_res = client.post("/api/businesses/tenant_alpha/config", json={
        "business_name": "Cafe Alpha Updated",
        "google_review_url": "https://g.page/r/alpha-updated/review",
        "primary_accent": "#00ff00"
    })
    assert cfg_res.status_code == 200
    assert cfg_res.json()["business_name"] == "Cafe Alpha Updated"

    # Can read Alpha analytics
    analytics_res = client.get("/api/reviews/analytics?business_id=tenant_alpha")
    assert analytics_res.status_code == 200
    assert "total_generations" in analytics_res.json()


def test_2_owner_alpha_cannot_read_or_modify_beta_configuration():
    client_alpha = login_client("owner_alpha@test.com", "PasswordAlpha123!")

    # Attempt to overwrite Beta config
    res = client_alpha.post("/api/businesses/tenant_beta/config", json={
        "business_name": "Hacked Beta",
        "google_review_url": "https://evil.com"
    })
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # Verify Beta config is completely untouched
    anon = TestClient(app)
    beta_info = anon.get("/api/businesses/tenant_beta/review-link").json()
    assert beta_info["business_name"] == "Restaurant Beta"
    assert "evil.com" not in beta_info["review_url"]


def test_3_owner_alpha_cannot_read_beta_analytics_or_tickets():
    client_alpha = login_client("owner_alpha@test.com", "PasswordAlpha123!")

    # Attempt to read Beta analytics
    analytics_res = client_alpha.get("/api/reviews/analytics?business_id=tenant_beta")
    assert analytics_res.status_code == 403

    # Attempt to read Beta private tickets
    tickets_res = client_alpha.get("/api/reviews/private-tickets?business_id=tenant_beta")
    assert tickets_res.status_code == 403


def test_4_changing_path_or_query_tenant_id_does_not_bypass_authorization():
    client_alpha = login_client("owner_alpha@test.com", "PasswordAlpha123!")

    # Forged query parameter
    res = client_alpha.get("/api/reviews/private-tickets?business_id=tenant_beta")
    assert res.status_code == 403

    # Forged path parameter
    res = client_alpha.post("/api/businesses/tenant_beta/config", json={
        "google_review_url": "https://attacker.com"
    })
    assert res.status_code == 403


# ─── 2. SESSION LIFECYCLE & TAMPERING ──────────────────────────────────────────

def test_5_requests_without_authentication_rejected():
    anon = TestClient(app)
    assert anon.get("/api/auth/session").status_code == 401
    assert anon.post("/api/businesses/tenant_alpha/config", json={"google_review_url": "https://test.com"}).status_code == 401
    assert anon.get("/api/reviews/analytics").status_code == 401
    assert anon.get("/api/reviews/private-tickets").status_code == 401


def test_6_expired_revoked_or_tampered_sessions_rejected():
    store = get_store()
    user = store.get_user_by_email("owner_alpha@test.com")
    client = TestClient(app)

    # 1. Tampered / non-existent token
    client.cookies.set(OWNER_COOKIE, "completely_fake_tampered_token_xyz")
    assert client.get("/api/auth/session").status_code == 401

    # 2. Expired session
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    store.create_session(
        token_hash=token_hash,
        user_id=user["id"],
        active_tenant_id="tenant_alpha",
        expires_at=time.time() - 3600  # 1 hour ago
    )
    client.cookies.set(OWNER_COOKIE, raw_token)
    assert client.get("/api/auth/session").status_code == 401

    # 3. Explicitly revoked session
    valid_raw_token = generate_session_token()
    valid_hash = hash_token(valid_raw_token)
    store.create_session(
        token_hash=valid_hash,
        user_id=user["id"],
        active_tenant_id="tenant_alpha",
        expires_at=time.time() + 3600
    )
    store.revoke_session(valid_hash)
    client.cookies.set(OWNER_COOKIE, valid_raw_token)
    assert client.get("/api/auth/session").status_code == 401


def test_7_disabled_user_cannot_continue_using_session():
    store = get_store()
    user = store.create_user("disabled_user@test.com", hash_password("ValidPassword123!"), "Disabled User", is_active=1)
    store.add_membership(user["id"], "tenant_alpha", role="owner")

    client = login_client("disabled_user@test.com", "ValidPassword123!")
    assert client.get("/api/auth/session").status_code == 200

    # Deactivate user
    store.set_user_active(user["id"], is_active=False)

    # Subsequent request fails
    assert client.get("/api/auth/session").status_code == 401


def test_8_multi_tenant_user_can_switch_authorized_tenants():
    # multi_user belongs to both tenant_alpha (manager) and tenant_beta (staff)
    client = login_client("multi_user@test.com", "PasswordMulti123!", tenant_id="tenant_alpha")
    
    sess = client.get("/api/auth/session").json()
    assert sess["active_tenant"]["id"] == "tenant_alpha"
    assert sess["active_tenant"]["role"] == "manager"

    # Switch to tenant_beta
    switch_res = client.post("/api/auth/switch-tenant", json={"tenant_id": "tenant_beta"})
    assert switch_res.status_code == 200
    switch_data = switch_res.json()
    assert switch_data["active_tenant"]["id"] == "tenant_beta"
    assert switch_data["active_tenant"]["role"] == "staff"

    # Switching to unauthorized tenant fails with 403
    unauth_switch = client.post("/api/auth/switch-tenant", json={"tenant_id": "unauthorized_tenant_xyz"})
    assert unauth_switch.status_code == 403


# ─── 3. ROLE HIERARCHY PERMISSIONS ───────────────────────────────────────────

def test_9_staff_and_manager_role_hierarchy_enforced():
    # 1. Staff cannot modify config or view private tickets
    client_staff = login_client("staff_alpha@test.com", "PasswordStaff123!")
    
    cfg_res = client_staff.post("/api/businesses/tenant_alpha/config", json={"google_review_url": "https://test.com"})
    assert cfg_res.status_code == 403
    assert "Requires 'owner' role" in cfg_res.json()["detail"]

    ticket_res = client_staff.get("/api/reviews/private-tickets?business_id=tenant_alpha")
    assert ticket_res.status_code == 403
    assert "Requires 'manager' role" in ticket_res.json()["detail"]

    # Staff CAN view analytics
    assert client_staff.get("/api/reviews/analytics?business_id=tenant_alpha").status_code == 200

    # 2. Manager CAN view tickets & generate reply, but CANNOT modify config
    client_mgr = login_client("multi_user@test.com", "PasswordMulti123!", tenant_id="tenant_alpha")
    assert client_mgr.get("/api/reviews/private-tickets?business_id=tenant_alpha").status_code == 200
    assert client_mgr.post("/api/businesses/tenant_alpha/config", json={"google_review_url": "https://test.com"}).status_code == 403


def test_10_logout_invalidates_current_session():
    client = login_client("owner_alpha@test.com", "PasswordAlpha123!")
    assert client.get("/api/auth/session").status_code == 200

    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["authenticated"] is False

    # Calling session again fails
    assert client.get("/api/auth/session").status_code == 401


def test_11_csrf_protection_on_authenticated_mutations():
    client = login_client("owner_alpha@test.com", "PasswordAlpha123!")

    # Attempt mutation with untrusted origin
    bad_origin_res = client.post(
        "/api/businesses/tenant_alpha/config",
        headers={"Origin": "https://malicious-attacker-site.com"},
        json={"google_review_url": "https://test.com"}
    )
    assert bad_origin_res.status_code == 403
    assert "origin is not allowed" in bad_origin_res.json()["detail"].lower()


# ─── 4. PUBLIC FLOW & BACKWARD COMPATIBILITY ──────────────────────────────────

def test_12_unknown_tenant_returns_404_without_leaking_data():
    anon = TestClient(app)
    res = anon.get("/api/businesses/non_existent_cafe_999/review-link")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
    assert "Nasta Ghar" not in res.text


def test_13_existing_public_nastaghar_review_urls_compatible():
    anon = TestClient(app)
    
    # 1. Default business review link
    res_def = anon.get("/api/businesses/default_business/review-link")
    assert res_def.status_code == 200
    assert res_def.json()["business_name"] == "Nasta Ghar"

    # 2. nasta_ghar alias
    res_alias = anon.get("/api/businesses/nasta_ghar/review-link")
    assert res_alias.status_code == 200
    assert res_alias.json()["business_name"] == "Nasta Ghar"

    # 3. Public review generation without auth
    gen_res = anon.post("/api/reviews/generate", json={
        "business_id": "default_business",
        "rating": 5,
        "aspects": ["Breakfast", "Chai & Beverages"]
    })
    assert gen_res.status_code == 200
    assert "review" in gen_res.json()


def test_14_existing_qr_destinations_compatible():
    anon = TestClient(app)
    sess_res = anon.post("/api/reviews/session", json={
        "business_id": "tenant_alpha",
        "table_number": "Table 12"
    })
    assert sess_res.status_code == 200
    assert sess_res.json()["business_id"] == "tenant_alpha"
    assert sess_res.json()["table_number"] == "Table 12"


# ─── 5. MIGRATION & REPEATABILITY ─────────────────────────────────────────────

def test_15_database_migration_preserves_records_and_configs():
    temp_db = str(Path(tempfile.gettempdir()) / f"nasta-mig-test-{time.time_ns()}.sqlite3")
    report = migrate_database(database_path=temp_db)
    assert report["success"] is True
    assert report["total_tenants_in_db"] >= 3

    store = ReviewStore(database_path=temp_db)
    assert store.tenant_exists("default_business") is True
    assert store.tenant_exists("test_cafe") is True


def test_16_rerunning_migration_is_idempotent():
    temp_db = str(Path(tempfile.gettempdir()) / f"nasta-idem-test-{time.time_ns()}.sqlite3")
    
    r1 = migrate_database(database_path=temp_db)
    r2 = migrate_database(database_path=temp_db)
    r3 = migrate_database(database_path=temp_db)

    assert r1["total_tenants_in_db"] == r2["total_tenants_in_db"] == r3["total_tenants_in_db"]


# ─── 6. CONCURRENT SESSION ISOLATION ──────────────────────────────────────────

def test_17_concurrent_sessions_and_requests_no_leakage():
    results = []

    def run_worker(user_idx):
        # Reset IP rate limit per worker thread simulation
        with _login_lock:
            _login_attempts.clear()
        client = login_client("owner_alpha@test.com", "PasswordAlpha123!")
        sess = client.get("/api/auth/session")
        if sess.status_code == 200 and sess.json()["active_tenant"]["id"] == "tenant_alpha":
            results.append(True)
        else:
            results.append(False)

    threads = [threading.Thread(target=run_worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 5
    assert all(results)
