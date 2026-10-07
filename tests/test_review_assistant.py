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
        ("language_selected", {"language": "gujarati"}),
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

def test_trilingual_ideas_generation():
    """Verify English, Roman Hinglish, and Roman Gujlish review ideas."""
    import re
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    gujarati_script_pattern = re.compile(r'[\u0A80-\u0AFF]')

    # 1. English
    res_en = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Food", "Staff"],
        "language": "english"
    })
    assert res_en.status_code == 200
    ideas_en = res_en.json()["ideas"]
    assert len(ideas_en) >= 3
    assert any("loved" in i["text"].lower() or "amazing" in i["text"].lower() or "great" in i["text"].lower() for i in ideas_en)

    # 2. Hindi (Roman Hinglish)
    res_hi = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Food", "Service"],
        "language": "hindi"
    })
    assert res_hi.status_code == 200
    ideas_hi = res_hi.json()["ideas"]
    assert len(ideas_hi) >= 3
    hi_text = " ".join(i["text"] for i in ideas_hi)
    # Strictly NO Devanagari
    assert not devanagari_pattern.search(hi_text), "Hindi ideas must NOT contain Devanagari script"
    # Contains natural Hinglish
    assert any("khana" in t.lower() or "bahut" in t.lower() or "accha" in t.lower() or "badhiya" in t.lower() for t in [i["text"] for i in ideas_hi])

    # 3. Gujarati (Roman Gujlish)
    res_gu = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Breakfast", "Chai"],
        "language": "gujarati"
    })
    assert res_gu.status_code == 200
    ideas_gu = res_gu.json()["ideas"]
    assert len(ideas_gu) >= 3
    gu_text = " ".join(i["text"] for i in ideas_gu)
    # Strictly NO Gujarati native script
    assert not gujarati_script_pattern.search(gu_text), "Gujarati ideas must NOT contain Gujarati native script"
    # Contains natural Gujlish
    assert any("ahiya" in t.lower() or "mast" in t.lower() or "saras" in t.lower() or "maza" in t.lower() for t in [i["text"] for i in ideas_gu])

def test_trilingual_review_generation():
    """Verify direct review generation in English, Roman Hinglish, and Roman Gujlish."""
    import re
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    gujarati_script_pattern = re.compile(r'[\u0A80-\u0AFF]')

    # 1. Hindi (Roman Hinglish)
    res_hi = client.post("/api/reviews/generate", json={
        "rating": 5,
        "aspects": ["food", "service"],
        "user_note": "Garam samosa",
        "language": "hindi"
    })
    assert res_hi.status_code == 200
    draft_hi = res_hi.json()["review"]
    assert not devanagari_pattern.search(draft_hi), "Generated Hindi review must be Roman script, not Devanagari"
    assert "samosa" in draft_hi.lower()
    assert res_hi.json()["language"] == "hindi"

    # 2. Gujarati (Roman Gujlish)
    res_gu = client.post("/api/reviews/generate", json={
        "rating": 5,
        "aspects": ["food", "staff"],
        "user_note": "Fafda jalebi",
        "language": "gujarati"
    })
    assert res_gu.status_code == 200
    draft_gu = res_gu.json()["review"]
    assert not gujarati_script_pattern.search(draft_gu), "Generated Gujarati review must be Roman script, not Gujarati script"
    assert "fafda" in draft_gu.lower()
    assert res_gu.json()["language"] == "gujarati"

def test_backward_compatibility_defaults():
    """Verify legacy requests without language default safely to English and invalid language handled gracefully."""
    # Omitted language
    res_no_lang = client.post("/api/reviews/ideas", json={
        "rating": 5,
        "aspects": ["Food"]
    })
    assert res_no_lang.status_code == 200
    assert len(res_no_lang.json()["ideas"]) >= 3

    # Unknown language string falls back to English
    res_unknown = client.post("/api/reviews/generate", json={
        "rating": 4,
        "aspects": ["Food"],
        "language": "esperanto_dialect_xyz"
    })
    assert res_unknown.status_code == 200
    assert res_unknown.json()["rating_consistent"] is True

def test_hospitality_category_topics():
    """Verify hospitality category topic mapping and resolution."""
    from api.review_assistant.prompts import get_category_topics

    cafe_topics = get_category_topics("Café & Bakery")
    assert "Chai / Coffee" in cafe_topics or "Food & Taste" in cafe_topics

    hotel_topics = get_category_topics("Boutique Hotel")
    assert "Room" in hotel_topics
    assert "Cleanliness" in hotel_topics

    salon_topics = get_category_topics("Hair Salon & Spa")
    assert "Results" in salon_topics or "Service" in salon_topics
