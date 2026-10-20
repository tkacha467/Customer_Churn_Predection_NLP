"""
Hostile Security & Boundary Verification Suite for ChurnLens / Vraja SaaS Architecture.
Simulates attack scenarios:
- Ordinary owner arbitrary tenant creation attempts.
- Cross-tenant read, update, and deletion attacks.
- Role privilege escalation attacks.
- Tampered, expired, and revoked token injection.
- CSRF Origin manipulation.
- Tenant deactivation / suspension enforcement.
- Feature entitlement gating.
- Migration safety: proving stale JSON never overwrites newer SQLite data.
"""

import time
import tempfile
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
def setup_security_fixtures():
    """Sets up isolated hostile test fixtures."""
    with _login_lock:
        _login_attempts.clear()

    store = get_store()

    # Create Tenant Alpha (Active, all entitlements)
    store.upsert_tenant({
        "id": "sec_alpha",
        "business_name": "Secure Alpha Cafe",
        "status": "active",
        "review_url": "https://g.page/r/sec-alpha/review",
        "entitlements": ["review_manager", "digital_card"]
    })

    # Create Tenant Beta (Active, all entitlements)
    store.upsert_tenant({
        "id": "sec_beta",
        "business_name": "Secure Beta Bistro",
        "status": "active",
        "review_url": "https://g.page/r/sec-beta/review",
        "entitlements": ["review_manager", "digital_card"]
    })

    # Create Tenant Gamma (Suspended tenant)
    store.upsert_tenant({
        "id": "sec_gamma",
        "business_name": "Suspended Gamma Hotel",
        "status": "suspended",
        "review_url": "https://g.page/r/sec-gamma/review",
        "entitlements": ["review_manager", "digital_card"]
    })

    # Create Tenant Delta (Entitled only to digital_card, review_manager disabled)
    store.upsert_tenant({
        "id": "sec_delta",
        "business_name": "Delta Digital Card Only",
        "status": "active",
        "review_url": "https://g.page/r/sec-delta/review",
        "entitlements": ["digital_card"]
    })

    # Users
    # 1. Owner Alpha (strictly belongs to Alpha, is_platform_admin=0)
    if not store.get_user_by_email("sec_owner_alpha@test.com"):
        u_alpha = store.create_user("sec_owner_alpha@test.com", hash_password("AlphaPass123!"), "Owner Alpha", is_active=1, is_platform_admin=0)
        store.add_membership(u_alpha["id"], "sec_alpha", role="owner")

    # 2. Owner Beta (strictly belongs to Beta, is_platform_admin=0)
    if not store.get_user_by_email("sec_owner_beta@test.com"):
        u_beta = store.create_user("sec_owner_beta@test.com", hash_password("BetaPass123!"), "Owner Beta", is_active=1, is_platform_admin=0)
        store.add_membership(u_beta["id"], "sec_beta", role="owner")

    # 3. Staff Alpha (strictly staff in Alpha, is_platform_admin=0)
    if not store.get_user_by_email("sec_staff_alpha@test.com"):
        u_staff = store.create_user("sec_staff_alpha@test.com", hash_password("StaffPass123!"), "Staff Alpha", is_active=1, is_platform_admin=0)
        store.add_membership(u_staff["id"], "sec_alpha", role="staff")

    # 4. Owner Gamma (belongs to suspended Gamma)
    if not store.get_user_by_email("sec_owner_gamma@test.com"):
        u_gamma = store.create_user("sec_owner_gamma@test.com", hash_password("GammaPass123!"), "Owner Gamma", is_active=1, is_platform_admin=0)
        store.add_membership(u_gamma["id"], "sec_gamma", role="owner")


def login(email: str, password: str, tenant_id: str = None) -> TestClient:
    client = TestClient(app)
    payload = {"email": email, "password": password}
    if tenant_id:
        payload["tenant_id"] = tenant_id
    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return client


# ─── 1. TENANT BOUNDARY & OWNERSHIP HARDENING ─────────────────────────────────

def test_hostile_1_ordinary_owner_cannot_create_arbitrary_tenant():
    """Ordinary business owner cannot create arbitrary tenants or claim businesses via config endpoint."""
    client_alpha = login("sec_owner_alpha@test.com", "AlphaPass123!")

    # Attempt to provision a new business 'malicious_corp'
    res = client_alpha.post("/api/businesses/malicious_corp/config", json={
        "business_name": "Malicious Corp",
        "google_review_url": "https://attacker.com/review"
    })
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # Verify 'malicious_corp' was NOT created
    store = get_store()
    assert store.tenant_exists("malicious_corp") is False


def test_hostile_2_cross_tenant_mutation_blocked():
    """Owner Alpha cannot update Beta's configuration under any circumstances."""
    client_alpha = login("sec_owner_alpha@test.com", "AlphaPass123!")

    res = client_alpha.post("/api/businesses/sec_beta/config", json={
        "business_name": "Hacked Beta",
        "google_review_url": "https://hacked.com"
    })
    assert res.status_code == 403

    # Verify Beta's config remains completely intact
    store = get_store()
    beta_info = store.get_tenant("sec_beta")
    assert beta_info["business_name"] == "Secure Beta Bistro"
    assert "hacked.com" not in beta_info["review_url"]


def test_hostile_3_cross_tenant_read_analytics_and_tickets_blocked():
    """Owner Alpha cannot eavesdrop on Beta's analytics or private tickets."""
    client_alpha = login("sec_owner_alpha@test.com", "AlphaPass123!")

    # Analytics query
    res_analytics = client_alpha.get("/api/reviews/analytics?business_id=sec_beta")
    assert res_analytics.status_code == 403

    # Private tickets query
    res_tickets = client_alpha.get("/api/reviews/private-tickets?business_id=sec_beta")
    assert res_tickets.status_code == 403


# ─── 2. ROLE ESCALATION ATTACKS ───────────────────────────────────────────────

def test_hostile_4_staff_role_escalation_blocked():
    """Staff member cannot perform owner or manager operations."""
    client_staff = login("sec_staff_alpha@test.com", "StaffPass123!")

    # Staff attempts owner operation (update config)
    res_cfg = client_staff.post("/api/businesses/sec_alpha/config", json={
        "google_review_url": "https://staff-tamper.com"
    })
    assert res_cfg.status_code == 403
    assert "Requires 'owner' role" in res_cfg.json()["detail"]

    # Staff attempts manager operation (view private tickets)
    res_tickets = client_staff.get("/api/reviews/private-tickets?business_id=sec_alpha")
    assert res_tickets.status_code == 403
    assert "Requires 'manager' role" in res_tickets.json()["detail"]


# ─── 3. SUSPENDED TENANT & DISABLED USER ──────────────────────────────────────

def test_hostile_5_suspended_tenant_access_blocked():
    """Users of an inactive or suspended tenant cannot access portal operations."""
    client = TestClient(app)
    
    # 1. Login attempt is blocked when tenant is suspended
    res_login = client.post("/api/auth/login", json={
        "email": "sec_owner_gamma@test.com",
        "password": "GammaPass123!"
    })
    assert res_login.status_code == 403
    assert "No business access" in res_login.json()["detail"]

    # 2. If a session existed before suspension, requests are blocked
    store = get_store()
    u_gamma = store.get_user_by_email("sec_owner_gamma@test.com")
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    store.create_session(
        token_hash=token_hash,
        user_id=u_gamma["id"],
        active_tenant_id="sec_gamma",
        expires_at=time.time() + 3600
    )
    client.cookies.set(OWNER_COOKIE, raw_token)
    res_req = client.get("/api/reviews/analytics?business_id=sec_gamma")
    assert res_req.status_code == 403
    assert "inactive or suspended" in res_req.json()["detail"].lower()


def test_hostile_6_disabled_user_session_immediately_revoked():
    """Disabling a user account immediately invalidates their active sessions."""
    store = get_store()
    user = store.get_user_by_email("sec_owner_alpha@test.com")
    client_alpha = login("sec_owner_alpha@test.com", "AlphaPass123!")

    assert client_alpha.get("/api/auth/session").status_code == 200

    # Deactivate user
    store.set_user_active(user["id"], is_active=False)

    # Immediate rejection
    assert client_alpha.get("/api/auth/session").status_code == 401
    assert client_alpha.get("/api/reviews/analytics").status_code == 401

    # Restore user
    store.set_user_active(user["id"], is_active=True)


# ─── 4. SESSION FORGERY & CSRF ────────────────────────────────────────────────

def test_hostile_7_tampered_token_injection_blocked():
    """Injecting random or forged token in cookie returns 401."""
    client = TestClient(app)
    client.cookies.set(OWNER_COOKIE, "forged_non_existent_token_12345")
    assert client.get("/api/auth/session").status_code == 401


def test_hostile_8_csrf_foreign_origin_blocked():
    """Mutating request with untrusted foreign origin header is rejected."""
    client_alpha = login("sec_owner_alpha@test.com", "AlphaPass123!")

    res = client_alpha.post(
        "/api/businesses/sec_alpha/config",
        headers={"Origin": "https://phishing-attacker.com"},
        json={"google_review_url": "https://test.com"}
    )
    assert res.status_code == 403
    assert "origin is not allowed" in res.json()["detail"].lower()


# ─── 5. PUBLIC ENDPOINT DATA LEAKAGE & RESOURCE EXHAUSTION ────────────────────

def test_hostile_9_public_endpoint_cannot_leak_private_tickets():
    """Anonymous callers cannot read private tickets or customer contact details."""
    anon = TestClient(app)
    assert anon.get("/api/reviews/private-tickets").status_code == 401
    assert anon.get("/api/reviews/private-tickets?business_id=sec_alpha").status_code == 401


def test_hostile_10_public_event_poisoning_blocked():
    """Posting events or private feedback for non-existent tenant returns 404."""
    anon = TestClient(app)

    # Event for non-existent tenant
    ev_res = anon.post("/api/reviews/events", json={
        "event_name": "google_review_link_opened",
        "metadata": {"business_id": "non_existent_fake_tenant_999"}
    })
    assert ev_res.status_code == 404

    # Feedback for non-existent tenant
    fb_res = anon.post("/api/reviews/private-feedback", json={
        "business_id": "non_existent_fake_tenant_999",
        "rating": 1,
        "diner_note": "Spam attack note"
    })
    assert fb_res.status_code == 404


# ─── 6. FEATURE ENTITLEMENT ENFORCEMENT ────────────────────────────────────────

def test_hostile_11_disabled_feature_entitlement_blocked():
    """Tenant Delta (entitled only to digital_card) cannot invoke review_manager features."""
    anon = TestClient(app)

    # Verify review ideas blocked for sec_delta
    ideas_res = anon.post("/api/reviews/ideas", json={
        "business_id": "sec_delta",
        "rating": 5,
        "aspects": ["Hospitality"]
    })
    assert ideas_res.status_code == 403
    assert "review_manager" in ideas_res.json()["detail"]


# ─── 7. MIGRATION SAFETY: NEVER OVERWRITE NEWER SQLITE DATA ───────────────────

def test_hostile_12_migration_does_not_overwrite_newer_sqlite_data():
    """Re-running migrations preserves user changes in SQLite without reversion to stale JSON."""
    temp_db = str(Path(tempfile.gettempdir()) / f"nasta-safety-mig-{time.time_ns()}.sqlite3")
    
    # 1. Run initial migration
    report1 = migrate_database(database_path=temp_db)
    assert report1["success"] is True

    # 2. Owner updates configuration in SQLite
    store = ReviewStore(database_path=temp_db)
    store.upsert_tenant({
        "id": "default_business",
        "business_name": "Nasta Ghar - Customized In Production",
        "review_url": "https://custom.live/review"
    })
    updated = store.get_tenant("default_business")
    assert updated["business_name"] == "Nasta Ghar - Customized In Production"

    # 3. Run migration again (simulating application restart or redeploy)
    report2 = migrate_database(database_path=temp_db)
    assert report2["success"] is True

    # 4. Verify the updated name in SQLite was NOT overwritten by stale JSON!
    final_tenant = store.get_tenant("default_business")
    assert final_tenant["business_name"] == "Nasta Ghar - Customized In Production"
    assert final_tenant["review_url"] == "https://custom.live/review"


# ─── 8. REVERSE PROXY SPOOFING PREVENTION ─────────────────────────────────────

def test_hostile_13_trusted_proxy_client_ip_spoofing_prevention(monkeypatch):
    """
    Ensures that X-Forwarded-For is only trusted when the peer matches TRUSTED_PROXIES.
    Direct clients attempting to spoof X-Forwarded-For are denied spoofing.
    """
    from starlette.requests import Request
    from api.review_assistant.routes import get_client_ip

    def make_request(client_host: str, headers: dict) -> Request:
        scope = {
            "type": "http",
            "client": (client_host, 50000),
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }
        return Request(scope)

    # 1. Untrusted environment (TRUSTED_PROXIES unset)
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    req1 = make_request("198.51.100.2", {"x-forwarded-for": "10.0.0.1, 198.51.100.2"})
    assert get_client_ip(req1) == "198.51.100.2"  # Spoofed header ignored!

    # 2. Trusted proxy configured (e.g. internal reverse proxy 10.0.0.254)
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.254, 127.0.0.1")
    
    # Request from trusted proxy forwards real client IP
    req2 = make_request("10.0.0.254", {"x-forwarded-for": "203.0.113.195, 10.0.0.254"})
    assert get_client_ip(req2) == "203.0.113.195"

    # Request directly from untrusted external IP trying to claim it's someone else
    req3 = make_request("198.51.100.2", {"x-forwarded-for": "1.2.3.4"})
    assert get_client_ip(req3) == "198.51.100.2"  # Rejected spoofing

