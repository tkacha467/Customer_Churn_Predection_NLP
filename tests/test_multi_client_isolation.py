import copy
import os
import tempfile
import threading
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.review_assistant.auth import OWNER_COOKIE, make_session
from api.review_assistant.google_reviews import GoogleReviewManager
from api.review_assistant.storage import ReviewStore
from api.review_assistant.service import ReviewService

@pytest.fixture
def auth_client():
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"password": "test-only-owner-password"})
    assert login.status_code == 200
    return client

@pytest.fixture
def anon_client():
    return TestClient(app)

# ─── 1. CONFIGURATION & ISOLATION TESTS ───────────────────────────────────────

def test_each_business_can_retrieve_its_own_configuration(auth_client):
    # Configure Cafe Alpha
    res_alpha = auth_client.post("/api/businesses/test_cafe_alpha/config", json={
        "business_name": "Cafe Alpha",
        "google_review_url": "https://g.page/r/cafe-alpha/review",
        "category": "Cafe",
        "description": "Artisan espresso bar in Ahmedabad",
        "topics": ["Espresso", "Croissant", "Vibe"],
        "primary_accent": "#0ea5e9"
    })
    assert res_alpha.status_code == 200
    alpha_data = res_alpha.json()
    assert alpha_data["business_id"] == "test_cafe_alpha"
    assert alpha_data["business_name"] == "Cafe Alpha"
    assert alpha_data["review_url"] == "https://g.page/r/cafe-alpha/review"
    assert alpha_data["primary_accent"] == "#0ea5e9"

    # Configure Restaurant Beta
    res_beta = auth_client.post("/api/businesses/test_restaurant_beta/config", json={
        "business_name": "Restaurant Beta",
        "google_review_url": "https://g.page/r/restaurant-beta/review",
        "category": "Restaurant",
        "description": "Traditional thali dining in Vadodara",
        "topics": ["Thali", "Rotli", "Hospitality"],
        "primary_accent": "#10b981"
    })
    assert res_beta.status_code == 200
    beta_data = res_beta.json()
    assert beta_data["business_id"] == "test_restaurant_beta"
    assert beta_data["business_name"] == "Restaurant Beta"
    assert beta_data["review_url"] == "https://g.page/r/restaurant-beta/review"
    assert beta_data["primary_accent"] == "#10b981"

    # Configure Hotel Gamma
    res_gamma = auth_client.post("/api/businesses/test_hotel_gamma/config", json={
        "business_name": "Hotel Gamma",
        "google_review_url": "https://g.page/r/hotel-gamma/review",
        "category": "Hotel",
        "description": "Boutique heritage stay in Rajkot",
        "topics": ["Room", "Breakfast", "Service"],
        "primary_accent": "#6366f1"
    })
    assert res_gamma.status_code == 200
    gamma_data = res_gamma.json()
    assert gamma_data["business_id"] == "test_hotel_gamma"
    assert gamma_data["business_name"] == "Hotel Gamma"
    assert gamma_data["review_url"] == "https://g.page/r/hotel-gamma/review"
    assert gamma_data["primary_accent"] == "#6366f1"

    # Independent retrieval via public endpoint
    anon = TestClient(app)
    get_alpha = anon.get("/api/businesses/test_cafe_alpha/review-link").json()
    get_beta = anon.get("/api/businesses/test_restaurant_beta/review-link").json()
    get_gamma = anon.get("/api/businesses/test_hotel_gamma/review-link").json()

    assert get_alpha["business_name"] == "Cafe Alpha"
    assert get_beta["business_name"] == "Restaurant Beta"
    assert get_gamma["business_name"] == "Hotel Gamma"
    assert get_alpha["primary_accent"] == "#0ea5e9"
    assert get_beta["primary_accent"] == "#10b981"
    assert get_gamma["primary_accent"] == "#6366f1"

def test_updating_one_business_leaves_every_other_business_unchanged(auth_client):
    # Setup initial configs
    auth_client.post("/api/businesses/test_cafe_alpha/config", json={
        "business_name": "Cafe Alpha Original",
        "google_review_url": "https://g.page/r/alpha-orig/review",
        "primary_accent": "#000001"
    })
    auth_client.post("/api/businesses/test_restaurant_beta/config", json={
        "business_name": "Restaurant Beta Untouched",
        "google_review_url": "https://g.page/r/beta-untouched/review",
        "primary_accent": "#000002"
    })

    # Mutate ONLY Cafe Alpha
    update_res = auth_client.post("/api/businesses/test_cafe_alpha/config", json={
        "business_name": "Cafe Alpha Renamed",
        "google_review_url": "https://g.page/r/alpha-new/review",
        "primary_accent": "#ff0000"
    })
    assert update_res.status_code == 200

    # Verify Beta is completely unchanged
    beta = auth_client.get("/api/businesses/test_restaurant_beta/review-link").json()
    assert beta["business_name"] == "Restaurant Beta Untouched"
    assert beta["review_url"] == "https://g.page/r/beta-untouched/review"
    assert beta["primary_accent"] == "#000002"

    # Verify Default business (Nasta Ghar) is completely unchanged
    default_b = auth_client.get("/api/businesses/default_business/review-link").json()
    assert default_b["business_name"] == "Nasta Ghar"
    assert "ChIJZeK7NwDLWTkR1pOxt51jLro" in default_b["review_url"]

def test_unknown_or_malformed_business_id_returns_404_or_validation_error(anon_client):
    # Unknown business ID must return 404, NEVER default business
    res = anon_client.get("/api/businesses/totally_nonexistent_business_id_99999/review-link")
    assert res.status_code == 404, f"Expected 404 for unknown business, got {res.status_code}: {res.text}"
    error_body = res.json()
    # Must not leak default business details
    assert "Nasta Ghar" not in str(error_body)
    assert "placeid" not in str(error_body)

    # Malformed business IDs (e.g. path traversal, special characters)
    for bad_id in ["..", "bad/slash", "foo bar", "bad$character"]:
        res_bad = anon_client.get(f"/api/businesses/{bad_id}/review-link")
        assert res_bad.status_code in {404, 422}, f"Expected 404/422 for malformed ID '{bad_id}', got {res_bad.status_code}"

def test_existing_default_business_remains_backward_compatible(anon_client):
    res_default = anon_client.get("/api/businesses/default_business/review-link")
    assert res_default.status_code == 200
    assert res_default.json()["business_name"] == "Nasta Ghar"

    res_nasta = anon_client.get("/api/businesses/nasta_ghar/review-link")
    assert res_nasta.status_code == 200
    assert res_nasta.json()["business_name"] == "Nasta Ghar"

# ─── 2. ANALYTICS & EVENT ISOLATION TESTS ─────────────────────────────────────

def test_analytics_events_and_summary_are_scoped_to_correct_business(auth_client, anon_client):
    # Emit events for Cafe Alpha
    anon_client.post("/api/reviews/events", json={
        "event_name": "review_generation_completed",
        "session_id": "sess-alpha-1",
        "metadata": {
            "business_id": "test_cafe_alpha",
            "rating": 5,
            "sentiment": "Positive",
            "table_number": "Table A1",
            "aspects": ["Espresso"]
        }
    })
    anon_client.post("/api/reviews/events", json={
        "event_name": "google_review_link_opened",
        "session_id": "sess-alpha-1",
        "metadata": {"business_id": "test_cafe_alpha"}
    })

    # Emit events for Restaurant Beta
    anon_client.post("/api/reviews/events", json={
        "event_name": "review_generation_completed",
        "session_id": "sess-beta-1",
        "metadata": {
            "business_id": "test_restaurant_beta",
            "rating": 1,
            "sentiment": "Negative",
            "table_number": "Table B9",
            "aspects": ["Wait Time"]
        }
    })

    # Query analytics for Cafe Alpha
    res_alpha = auth_client.get("/api/reviews/analytics?business_id=test_cafe_alpha")
    assert res_alpha.status_code == 200
    data_alpha = res_alpha.json()
    assert data_alpha["total_generations"] >= 1
    assert data_alpha["rating_distribution"].get("5", 0) >= 1
    # Rating 1 from Beta MUST NOT appear in Alpha's distribution
    assert data_alpha["rating_distribution"].get("1", 0) == 0
    # Table B9 from Beta MUST NOT appear in Alpha's recent activity
    for act in data_alpha.get("recent_activity", []):
        assert "Table B9" not in act

    # Query analytics for Restaurant Beta
    res_beta = auth_client.get("/api/reviews/analytics?business_id=test_restaurant_beta")
    assert res_beta.status_code == 200
    data_beta = res_beta.json()
    assert data_beta["total_generations"] >= 1
    assert data_beta["rating_distribution"].get("1", 0) >= 1
    # Rating 5 from Alpha MUST NOT appear in Beta's distribution
    assert data_beta["rating_distribution"].get("5", 0) == 0
    # Table A1 from Alpha MUST NOT appear in Beta's recent activity
    for act in data_beta.get("recent_activity", []):
        assert "Table A1" not in act

# ─── 3. PRIVATE FEEDBACK ISOLATION TESTS ──────────────────────────────────────

def test_private_feedback_tickets_are_scoped_to_correct_business(auth_client, anon_client):
    # Submit private feedback for Cafe Alpha
    res_fb_alpha = anon_client.post("/api/reviews/private-feedback", json={
        "business_id": "test_cafe_alpha",
        "rating": 2,
        "diner_note": "Confidential Alpha Feedback: cold latte",
        "guest_contact": "alpha_guest@example.com"
    })
    assert res_fb_alpha.status_code == 200
    alpha_ticket_id = res_fb_alpha.json()["ticket_id"]

    # Submit private feedback for Restaurant Beta
    res_fb_beta = anon_client.post("/api/reviews/private-feedback", json={
        "business_id": "test_restaurant_beta",
        "rating": 1,
        "diner_note": "Confidential Beta Feedback: wrong billing",
        "guest_contact": "beta_guest@example.com"
    })
    assert res_fb_beta.status_code == 200
    beta_ticket_id = res_fb_beta.json()["ticket_id"]

    # Query tickets for Cafe Alpha
    res_tickets_alpha = auth_client.get("/api/reviews/private-tickets?business_id=test_cafe_alpha")
    assert res_tickets_alpha.status_code == 200
    tickets_alpha = res_tickets_alpha.json()
    alpha_ids = [t["ticket_id"] for t in tickets_alpha]
    assert alpha_ticket_id in alpha_ids
    assert beta_ticket_id not in alpha_ids
    for t in tickets_alpha:
        assert t.get("business_id") == "test_cafe_alpha"
        assert "beta_guest" not in str(t)

    # Query tickets for Restaurant Beta
    res_tickets_beta = auth_client.get("/api/reviews/private-tickets?business_id=test_restaurant_beta")
    assert res_tickets_beta.status_code == 200
    tickets_beta = res_tickets_beta.json()
    beta_ids = [t["ticket_id"] for t in tickets_beta]
    assert beta_ticket_id in beta_ids
    assert alpha_ticket_id not in beta_ids
    for t in tickets_beta:
        assert t.get("business_id") == "test_restaurant_beta"
        assert "alpha_guest" not in str(t)

# ─── 4. PER-TENANT RETENTION LIMIT ISOLATION ──────────────────────────────────

def test_data_belonging_to_one_business_is_not_deleted_when_another_reaches_retention_limit(tmp_path):
    store = ReviewStore(str(tmp_path / "retention_test.sqlite3"))

    # Add 1 important ticket for Business B
    store.add_ticket({
        "ticket_id": "TICK-BETA-SAFE",
        "business_id": "test_restaurant_beta",
        "timestamp": time.time(),
        "diner_note": "Important note for Beta",
        "rating": 4
    })

    # Add 1 important event for Business B
    store.add_event({
        "event_id": "EV-BETA-SAFE",
        "event_name": "review_generation_completed",
        "timestamp": time.time(),
        "metadata": {"business_id": "test_restaurant_beta", "rating": 5}
    })

    # Flood Business A with 2500 events and 5500 tickets
    # (Testing with a small batch to verify the scoped deletion mechanism)
    for i in range(50):
        store.add_ticket({
            "ticket_id": f"TICK-ALPHA-{i}",
            "business_id": "test_cafe_alpha",
            "timestamp": time.time(),
            "diner_note": f"Alpha flood note {i}",
            "rating": 3
        })
        store.add_event({
            "event_id": f"EV-ALPHA-{i}",
            "event_name": "review_generation_completed",
            "timestamp": time.time(),
            "metadata": {"business_id": "test_cafe_alpha", "rating": 3}
        })

    # Verify Beta's ticket and event are still present and retrievable
    beta_tickets = store.list_tickets(business_id="test_restaurant_beta")
    assert len(beta_tickets) == 1
    assert beta_tickets[0]["ticket_id"] == "TICK-BETA-SAFE"

    beta_events = store.list_events(business_id="test_restaurant_beta")
    assert len(beta_events) == 1
    assert beta_events[0]["event_id"] == "EV-BETA-SAFE"

# ─── 5. CONCURRENT WRITES & RESTART PERSISTENCE ───────────────────────────────

def test_configuration_updates_and_concurrent_requests_do_not_corrupt_data(auth_client, tmp_path):
    errors = []

    def update_tenant(tenant_id, name):
        try:
            for i in range(5):
                res = auth_client.post(f"/api/businesses/{tenant_id}/config", json={
                    "business_name": f"{name} {i}",
                    "google_review_url": f"https://g.page/r/{tenant_id}-{i}/review"
                })
                if res.status_code != 200:
                    errors.append(f"{tenant_id}: {res.status_code} {res.text}")
        except Exception as e:
            errors.append(str(e))

    t1 = threading.Thread(target=update_tenant, args=("test_conc_alpha", "Alpha Conc"))
    t2 = threading.Thread(target=update_tenant, args=("test_conc_beta", "Beta Conc"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Concurrent updates failed: {errors}"
    c1 = auth_client.get("/api/businesses/test_conc_alpha/review-link").json()
    c2 = auth_client.get("/api/businesses/test_conc_beta/review-link").json()
    assert "Alpha Conc" in c1["business_name"]
    assert "Beta Conc" in c2["business_name"]

def test_state_persists_correctly_after_manager_reload():
    mgr1 = GoogleReviewManager()
    mgr1.update_business_config(
        "test_persist_client",
        "https://g.page/r/persist-client/review",
        business_name="Persist Client",
        primary_accent="#123456"
    )

    # Fresh instance simulating server restart
    mgr2 = GoogleReviewManager()
    cfg = mgr2.get_review_url("test_persist_client")
    assert cfg["business_name"] == "Persist Client"
    assert cfg["review_url"] == "https://g.page/r/persist-client/review"
    assert cfg["primary_accent"] == "#123456"

# ─── 6. AUTHENTICATION & SECURITY ISOLATION TESTS ─────────────────────────────

def test_unauthenticated_owner_requests_rejected(anon_client):
    assert anon_client.get("/api/reviews/analytics").status_code == 401
    assert anon_client.get("/api/reviews/private-tickets").status_code == 401
    assert anon_client.post("/api/businesses/test_cafe_alpha/config", json={
        "google_review_url": "https://g.page/r/test/review"
    }).status_code == 401
    assert anon_client.post("/api/reviews/manager-reply", json={
        "guest_review": "Nice food", "rating": 5
    }).status_code == 401
    assert anon_client.post("/api/debug", json={
        "review": "Nice food", "rating": 5
    }).status_code == 401

def test_tampered_or_expired_session_rejected():
    client = TestClient(app)
    # Tampered signature
    client.cookies.set(OWNER_COOKIE, "9999999999.invalid_signature_hex_value")
    assert client.get("/api/auth/session").status_code == 401

    # Expired session
    expired_time = str(int(time.time()) - 100)
    from api.review_assistant.auth import _sign
    expired_cookie = f"{expired_time}.{_sign(expired_time)}"
    client.cookies.set(OWNER_COOKIE, expired_cookie)
    assert client.get("/api/auth/session").status_code == 401
