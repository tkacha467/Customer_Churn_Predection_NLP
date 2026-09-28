import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_review_ideas_generation_5_star():
    payload = {
        "business_id": "test_bistro",
        "rating": 5,
        "aspects": ["Food", "Atmosphere", "Friendly staff"],
        "user_note": "The margherita pizza was super fresh"
    }
    res = client.post("/api/reviews/ideas", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "ideas" in data
    assert len(data["ideas"]) >= 3
    # Check that ideas have distinct focus
    foci = [idea["focus"] for idea in data["ideas"]]
    assert len(set(foci)) >= 2
    # Check that user note is present in ideas
    texts = " ".join([idea["text"] for idea in data["ideas"]])
    assert "margherita pizza" in texts.lower()
    # Check that 5-star ideas contain warm positive sentiment
    assert any("really enjoyed" in t.lower() or "lovely" in t.lower() or "wonderful" in t.lower() or "delicious" in t.lower() or "best" in t.lower() for t in [i["text"] for i in data["ideas"]])

def test_review_ideas_generation_1_star():
    payload = {
        "business_id": "test_bistro",
        "rating": 1,
        "aspects": ["Service", "Wait Time"],
        "user_note": ""
    }
    res = client.post("/api/reviews/ideas", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["ideas"]) >= 3
    for idea in data["ideas"]:
        # 1-star reviews should not have emojis or positive exclamation
        assert "❤️" not in idea["text"]
        assert "😊" not in idea["text"]
        assert "loved" not in idea["text"].lower()
        assert "highly recommend" not in idea["text"].lower()

def test_generate_from_selected_idea():
    selected = "Really enjoyed the food and the friendly service. The place had a nice atmosphere too!"
    payload = {
        "business_id": "test_bistro",
        "rating": 5,
        "aspects": ["Food", "Service"],
        "selected_idea": selected,
        "user_note": "Tiramisu was delicious",
        "emoji_preference": "light"
    }
    res = client.post("/api/reviews/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "review" in data
    text = data["review"]
    # Check that note is incorporated without fabrication
    assert "tiramisu" in text.lower()
    # Check word count is compact and natural (15 to 45 words approx)
    word_count = len(text.split())
    assert 10 <= word_count <= 55
    # Rating consistency
    assert data["rating_consistent"] is True

def test_emoji_rule_enforcement():
    # 1-star review should have NO emojis
    res_1 = client.post("/api/reviews/generate", json={
        "rating": 1,
        "aspects": ["Wait Time"],
        "emoji_preference": "light"
    })
    assert res_1.status_code == 200
    text_1 = res_1.json()["review"]
    assert "😊" not in text_1 and "❤️" not in text_1 and "☕" not in text_1 and "✨" not in text_1

    # 5-star review should have at most 2 emojis
    res_5 = client.post("/api/reviews/generate", json={
        "rating": 5,
        "aspects": ["Coffee & Drinks"],
        "emoji_preference": "light"
    })
    assert res_5.status_code == 200
    text_5 = res_5.json()["review"]
    # Emojis count should be <= 2
    emojis = [c for c in text_5 if ord(c) > 127 and c in "☕😊❤️✨🍕😋🥐🍰🙂"]
    assert len(emojis) <= 2

def test_no_rating_gating_behavior():
    # Both 5-star and 1-star customer requests should successfully get review link and have valid flows
    link_res = client.get("/api/businesses/default_business/review-link")
    assert link_res.status_code == 200
    link_data = link_res.json()
    assert "review_url" in link_data

    # Log Google review opened event for 1-star customer
    ev_res = client.post("/api/reviews/events", json={
        "event_name": "google_review_link_opened",
        "metadata": {"rating": 1, "action": "copy_and_continue"}
    })
    assert ev_res.status_code == 200

def test_restaurant_config_and_topics():
    config_payload = {
        "business_name": "Cuore Downtown",
        "branch": "Central Mall",
        "category": "Italian Bistro & Espresso",
        "description": "Artisan coffee, fresh pasta, and stone-baked pizza.",
        "google_review_url": "https://g.page/r/cuore-downtown/review",
        "topics": ["Fresh Pasta", "Woodfire Pizza", "Espresso", "Staff", "Patio Vibe"],
        "primary_accent": "#d97706"
    }
    res = client.post("/api/businesses/cuore_bistro/config", json=config_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["business_name"] == "Cuore Downtown"
    assert data["branch"] == "Central Mall"
    assert "Fresh Pasta" in data["topics"]
    assert data["is_configured"] is True

    # Retrieve to confirm persistence
    get_res = client.get("/api/businesses/cuore_bistro/review-link")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["business_name"] == "Cuore Downtown"
    assert get_data["topics"] == ["Fresh Pasta", "Woodfire Pizza", "Espresso", "Staff", "Patio Vibe"]

def test_simplified_owner_analytics():
    # Log some events
    client.post("/api/reviews/events", json={"event_name": "review_generation_completed", "metadata": {"rating": 5, "aspects": ["Food", "Service"], "table_number": "Table 2"}})
    client.post("/api/reviews/events", json={"event_name": "review_copied", "metadata": {"rating": 5}})
    client.post("/api/reviews/events", json={"event_name": "google_review_link_opened", "metadata": {"rating": 5}})

    res = client.get("/api/reviews/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_generations" in data
    assert "google_clicks" in data
    assert "reviews_copied" in data
    assert "top_topics" in data
    assert "recent_activity" in data
