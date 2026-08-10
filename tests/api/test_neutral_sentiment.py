import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(scope="module")
def client():
    # Context manager triggers startup/shutdown events
    with TestClient(app) as c:
        yield c

def test_positive_reviews(client):
    pos_cases = [
        "Excellent product, I loved it.",
        "Very good quality."
    ]
    for review in pos_cases:
        response = client.post("/api/predict", json={"review": review, "rating": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "Positive"
        assert data["rating_review_consistency"] == "Match"
        assert data["integrity"] == "Genuine"

def test_negative_reviews(client):
    neg_cases = [
        "Terrible product, completely disappointed.",
        "Very poor quality."
    ]
    for review in neg_cases:
        response = client.post("/api/predict", json={"review": review, "rating": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "Negative"
        assert data["rating_review_consistency"] == "Match"
        assert data["integrity"] == "Genuine"

def test_neutral_reviews(client):
    neutral_cases = [
        "The package arrived yesterday.",
        "The product is blue and contains two pieces.",
        "Delivery was on Monday."
    ]
    for review in neutral_cases:
        # Check rating 3
        response = client.post("/api/predict", json={"review": review, "rating": 3})
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "Neutral"
        assert data["rating_review_consistency"] == "No Strong Sentiment"
        assert data["integrity"] == "No Clear Mismatch"
        
        # Check rating 5 (should not be marked suspicious/mismatch)
        response_high = client.post("/api/predict", json={"review": review, "rating": 5})
        data_high = response_high.json()
        assert data_high["sentiment"] == "Neutral"
        assert data_high["rating_review_consistency"] == "No Strong Sentiment"
        assert data_high["integrity"] == "No Clear Mismatch"

def test_mixed_review(client):
    review = "The product arrived on time but the packaging was average."
    response = client.post("/api/predict", json={"review": review, "rating": 3})
    assert response.status_code == 200
    data = response.json()
    # Confirm endpoint works and returns one of the 3 sentiment classes
    assert data["sentiment"] in ["Positive", "Negative", "Neutral"]
