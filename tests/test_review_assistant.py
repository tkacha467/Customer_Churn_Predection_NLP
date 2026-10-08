import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
login = client.post("/api/auth/login", json={"password": "test-only-owner-password"})
assert login.status_code == 200

def test_owner_data_and_mutations_require_authentication():
    anonymous = TestClient(app)
    assert anonymous.get("/api/reviews/analytics").status_code == 401
    assert anonymous.get("/api/reviews/private-tickets").status_code == 401
    assert anonymous.post("/api/businesses/test_cafe/config", json={
        "google_review_url": "https://g.page/r/test/review"
    }).status_code == 401

def test_owner_session_is_signed_http_only_and_logout_works():
    cookie = login.cookies.get("nasta_owner_session")
    assert cookie
    assert "httponly" in login.headers.get("set-cookie", "").lower()
    assert client.get("/api/auth/session").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/session").status_code == 401
    assert client.post("/api/auth/login", json={"password": "test-only-owner-password"}).status_code == 200

def test_health_and_cors_allowlist():
    assert client.get("/healthz").json() == {"status": "ok"}
    response = client.options(
        "/api/auth/session",
        headers={"Origin": "https://attacker.invalid", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers

def test_review_store_persists_events_and_private_tickets(tmp_path):
    from api.review_assistant.storage import ReviewStore

    path = tmp_path / "reviews.sqlite3"
    first = ReviewStore(str(path))
    first.add_event({"event_id": "event-1", "timestamp": 1, "event_name": "review_selected"})
    first.add_ticket({"ticket_id": "ticket-1", "timestamp": 1, "diner_note": "private note"})

    restarted = ReviewStore(str(path))
    assert restarted.list_events()[0]["event_id"] == "event-1"
    assert restarted.list_tickets()[0]["diner_note"] == "private note"

def test_business_configuration_persists_atomically():
    from api.review_assistant.google_reviews import GoogleReviewManager

    manager = GoogleReviewManager()
    manager.update_business_config(
        "persistence-check",
        "https://g.page/r/persistence-check/review",
        business_name="Persistence Check",
    )
    reloaded = GoogleReviewManager().get_review_url("persistence-check")
    assert reloaded["business_name"] == "Persistence Check"
    assert reloaded["review_url"] == "https://g.page/r/persistence-check/review"

def test_get_business_review_link():
    res = client.get("/api/businesses/test_cafe/review-link")
    assert res.status_code == 200
    data = res.json()
    assert data["business_id"] == "test_cafe"
    assert "review_url" in data

def test_update_business_config():
    payload = {
        "business_name": "Artisan Coffee Roasters",
        "google_review_url": "https://g.page/r/artisan-coffee/review"
    }
    res = client.post("/api/businesses/artisan_coffee/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["review_url"] == "https://g.page/r/artisan-coffee/review"
    assert data["is_configured"] is True

def test_generate_review_5_star():
    payload = {
        "business_id": "artisan_coffee",
        "rating": 5,
        "aspects": ["food", "service"],
        "user_note": "The espresso and pastry were wonderful, staff was super friendly.",
        "tone": "natural",
        "length": "medium"
    }
    res = client.post("/api/reviews/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "review" in data
    assert len(data["review"]) > 10
    assert "espresso" in data["review"].lower() or "pastry" in data["review"].lower()
    assert data["rating_consistent"] is True
    assert data["sentiment"] in ["Positive", "Neutral"]

def test_generate_review_3_star():
    payload = {
        "business_id": "artisan_coffee",
        "rating": 3,
        "aspects": ["service"],
        "user_note": "Service took longer than expected but coffee was okay.",
        "tone": "professional",
        "length": "short"
    }
    res = client.post("/api/reviews/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "review" in data
    assert data["rating_consistent"] is True

def test_validate_review_consistency():
    # Valid positive review for 5 stars
    res = client.post("/api/reviews/validate", json={
        "rating": 5,
        "review": "Absolutely wonderful atmosphere, fantastic coffee, and welcoming staff!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["rating_consistent"] is True
    assert data["sentiment"] == "Positive"

    # Inconsistent negative review for 5 stars
    res_inconsistent = client.post("/api/reviews/validate", json={
        "rating": 5,
        "review": "Horrible experience, rude staff, cold coffee, never returning!"
    })
    assert res_inconsistent.status_code == 200
    data_inc = res_inconsistent.json()
    assert data_inc["rating_consistent"] is False
    assert len(data_inc["warnings"]) > 0

def test_analytics_and_session():
    # Create session
    sess_res = client.post("/api/reviews/session", json={"business_id": "test_cafe"})
    assert sess_res.status_code == 200
    sess_id = sess_res.json()["session_id"]

    # Log event
    ev_res = client.post("/api/reviews/events", json={
        "session_id": sess_id,
        "event_name": "google_review_link_clicked",
        "metadata": {"source": "continue_button"}
    })
    assert ev_res.status_code == 200

    # Get analytics summary
    analytics_res = client.get("/api/reviews/analytics")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert "total_generations" in analytics_data
    assert "google_clicks" in analytics_data

def test_manager_reply_generation():
    payload = {
        "guest_review": "The iced matcha latte was incredible and staff was so welcoming!",
        "rating": 5,
        "guest_name": "Samantha",
        "manager_name": "Chef Marco",
        "tone": "gracious"
    }
    res = client.post("/api/reviews/manager-reply", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "Samantha" in data["reply"]
    assert "Chef Marco" in data["reply"]

def test_private_feedback_escalation():
    payload = {
        "business_id": "test_cafe",
        "table_number": "Table 7",
        "rating": 1,
        "diner_note": "Waited 40 minutes for coffee and it was cold.",
        "aspects": ["Wait Time", "Coffee"],
        "guest_contact": "guest@example.com"
    }
    res = client.post("/api/reviews/private-feedback", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "escalated"
    assert "ticket_id" in data

def test_frontend_analytics_events_accepted():
    """Regression: all event names emitted by CustomerReview.jsx must be accepted.

    Previously these returned 422 because ALLOWED_ANALYTICS_EVENTS only
    contained server-side event names.
    """
    sess = client.post("/api/reviews/session", json={"business_id": "test_cafe"})
    sess_id = sess.json()["session_id"]

    frontend_events = [
        ("rating_selected", {"rating": 5}),
        ("aspects_selected", {"aspects": ["Breakfast", "Chai & Tea"]}),
        ("review_selected", {"review_id": "opt1"}),
        ("idea_selected", {"idea_id": "opt1"}),
        ("review_approved", {"length": 120, "direct_post": True}),
        ("google_review_handoff_started", {"review_id": "opt1"}),
        ("review_clipboard_success", {"review_id": "opt1"}),
        ("review_clipboard_failed", {"review_id": "opt1"}),
        ("google_maps_redirect", {"destination": "https://maps.google.com"}),
        ("google_review_link_opened", {}),
        ("private_feedback_sent", {}),
        ("language_selected", {"language": "gujarati"}),
    ]

    for event_name, metadata in frontend_events:
        res = client.post("/api/reviews/events", json={
            "session_id": sess_id,
            "event_name": event_name,
            "metadata": metadata,
        })
        assert res.status_code == 200, (
            f"Event '{event_name}' returned {res.status_code}: {res.text}"
        )
        assert res.json()["status"] == "recorded"

def test_unknown_analytics_event_rejected():
    """Unknown event names must still be rejected with 422."""
    res = client.post("/api/reviews/events", json={
        "event_name": "totally_made_up_event",
        "metadata": {},
    })
    assert res.status_code == 422

def test_generate_review_hindi_hinglish():
    """Roman-script Hindi (Hinglish) review generation with zero fabrication and no Devanagari script."""
    payload = {
        "business_id": "default_business",
        "rating": 5,
        "aspects": ["Breakfast", "Chai & Tea"],
        "user_note": "Poha was fresh and tasty",
        "language": "hindi",
    }
    res = client.post("/api/reviews/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "review" in data
    review = data["review"]
    # Check that it's in Roman script (Latin) and not Devanagari script
    assert not any(0x0900 <= ord(c) <= 0x097F for c in review), "Should not contain Devanagari script"
    # User note should be incorporated
    assert "poha" in review.lower()
    # Consistent with 5 stars
    assert data["rating_consistent"] is True

def test_generate_review_gujarati_gujlish():
    """Roman-script Gujarati (Gujlish) review generation with zero fabrication and no Gujarati script."""
    payload = {
        "business_id": "default_business",
        "rating": 5,
        "aspects": ["Breakfast", "Chai & Tea"],
        "user_note": "Fafda jalebi bahu saras hatu",
        "language": "gujarati",
    }
    res = client.post("/api/reviews/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "review" in data
    review = data["review"]
    # Check that it's in Roman script (Latin) and not Gujarati native script
    assert not any(0x0A80 <= ord(c) <= 0x0AFF for c in review), "Should not contain Gujarati script"
    # User note incorporated
    assert "fafda" in review.lower()
    # Rating consistency
    assert data["rating_consistent"] is True

def test_multilingual_candidate_ideas():
    """Review candidate ideas generated directly in English, Roman Hindi, and Roman Gujarati."""
    # 1. Hindi candidate ideas
    res_hi = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Taste", "Staff"],
        "user_note": "Special chai",
        "language": "hindi",
    })
    assert res_hi.status_code == 200
    ideas_hi = res_hi.json()["ideas"]
    assert len(ideas_hi) >= 3
    hi_text = " ".join([i["text"] for i in ideas_hi])
    assert not any(0x0900 <= ord(c) <= 0x097F for c in hi_text), "No Devanagari in Hinglish ideas"
    assert "chai" in hi_text.lower() or "khana" in hi_text.lower()

    # 2. Gujarati candidate ideas
    res_gu = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Breakfast", "Cleanliness"],
        "user_note": "Saras breakfast",
        "language": "gujarati",
    })
    assert res_gu.status_code == 200
    ideas_gu = res_gu.json()["ideas"]
    assert len(ideas_gu) >= 3
    gu_text = " ".join([i["text"] for i in ideas_gu])
    assert not any(0x0A80 <= ord(c) <= 0x0AFF for c in gu_text), "No Gujarati script in Gujlish ideas"
    assert "food" in gu_text.lower() or "saras" in gu_text.lower() or "chhe" in gu_text.lower()

    # 3. English candidate ideas
    res_en = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Breakfast", "Staff"],
        "language": "english",
    })
    assert res_en.status_code == 200
    ideas_en = res_en.json()["ideas"]
    assert len(ideas_en) >= 3
    en_text = " ".join([i["text"] for i in ideas_en])
    assert "breakfast" in en_text.lower() or "chai" in en_text.lower()

def test_backward_compatibility_omitted_language():
    """When language is omitted, system gracefully defaults to English without breaking clients."""
    # Ideas endpoint without language
    res_ideas = client.post("/api/reviews/ideas", json={
        "rating": 4,
        "aspects": ["Breakfast"],
    })
    assert res_ideas.status_code == 200
    assert len(res_ideas.json()["ideas"]) >= 3

    # Generate endpoint without language
    res_gen = client.post("/api/reviews/generate", json={
        "rating": 4,
        "aspects": ["Breakfast"],
    })
    assert res_gen.status_code == 200
    assert "review" in res_gen.json()

def test_unknown_or_invalid_language_handling():
    """Unknown language inputs smoothly fall back to English without throwing errors."""
    res = client.post("/api/reviews/generate", json={
        "rating": 5,
        "aspects": ["Food"],
        "language": "esperanto_unsupported",
    })
    assert res.status_code == 200
    assert "review" in res.json()
    assert len(res.json()["review"]) > 10

def test_hospitality_specific_topics_configuration():
    """Hospitality categories (Cafe, Restaurant, Hotel, Salon) have tailored topic presets."""
    # Artisan Coffee has category "Cafe" without explicit topics override
    res = client.get("/api/businesses/artisan_coffee/review-link")
    assert res.status_code == 200
    topics = res.json()["topics"]
    assert "Chai / Coffee" in topics or "Food & Taste" in topics or "Cleanliness" in topics
