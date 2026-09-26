import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

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
