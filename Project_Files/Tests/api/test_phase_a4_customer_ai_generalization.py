"""
Phase A4 Test Suite: Multi-Industry Customer Experience & AI Generation.
Tests:
1. Mandatory healthcare 403 block on /reviews/ideas and /reviews/generate.
2. Suspended tenant 403 block on /reviews/ideas and /reviews/generate.
3. Server-side industry resolution (client cannot override canonical industry).
4. All 9 active industries produce grounded ideas and reviews.
5. Unclassified fallback produces neutral reviews.
6. Native script fidelity (Gujarati Unicode 0x0A80-0x0AFF, Hindi Devanagari 0x0900-0x097F).
7. Rating sentiment consistency (1-5 stars) and emoji rules.
8. Nasta Ghar (default_business) backward compatibility and preservation.
9. Public review-link and config DTOs return canonical industry terminology.
"""

import time
import json
import re
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import _stores
from Backend.app.api.service import review_service
from Backend.app.core.tenants.google_reviews import google_review_manager
from Backend.app.api.prompts import (
    generate_candidate_ideas,
    humanize_review_draft,
    resolve_industry_id,
    extract_aspect_summary,
    pick_tasteful_emojis
)
from Backend.app.core.industry_registry import IndustryRegistry, CANONICAL_INDUSTRIES

@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Isolated test environment with test database."""
    db_path = tmp_path / "test_a4.sqlite3"
    docs_path = tmp_path / "test_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))
    now = time.time()

    # Seed test tenants
    with store._connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES
            ('default_business', 'Nasta Ghar', 'active', 'google', 'https://maps.google.com/?cid=123', 'Main', 'Breakfast & Snacks', 'Homestyle breakfast', '[]', '#f97316', '', '["review_manager"]', ?, ?),
            ('biz_hotel_1', 'Grand Horizon Hotel', 'active', 'google', 'https://maps.google.com/?cid=456', 'Downtown', 'Hotel & Hospitality', 'Luxury Stay', '[]', '#2563eb', '', '["review_manager"]', ?, ?),
            ('biz_health_1', 'Apex Health Care', 'active', 'google', 'https://maps.google.com/?cid=789', 'City Wing', 'Healthcare & Clinics', 'Medical Care', '[]', '#0d9488', '', '["review_manager"]', ?, ?),
            ('biz_suspended_1', 'Old Cafe', 'suspended', 'google', 'https://maps.google.com/?cid=999', 'Closed', 'Cafe', 'Closed', '[]', '#f97316', '', '["review_manager"]', ?, ?)
        """, (now, now, now, now, now, now, now, now))

        db.execute("""
            CREATE TABLE IF NOT EXISTS industry_configs (
                business_id TEXT PRIMARY KEY,
                industry_id TEXT NOT NULL,
                subcategory TEXT,
                custom_terminology_json TEXT,
                custom_topics_json TEXT,
                updated_at REAL NOT NULL
            )
        """)
        db.execute("""
            INSERT OR REPLACE INTO industry_configs (business_id, industry_id, updated_at)
            VALUES
            ('default_business', 'restaurant', ?),
            ('biz_hotel_1', 'hotel', ?),
            ('biz_health_1', 'healthcare', ?)
        """, (now, now, now))

    old_store = review_service._store
    review_service._store = store

    client = TestClient(app)
    yield client, store

    review_service._store = old_store


# ─── 1. HEALTHCARE 403 RESTRICTION TESTS ──────────────────────────────────────

def test_healthcare_ai_ideas_blocked(test_env):
    client, store = test_env
    res = client.post("/api/reviews/ideas", json={
        "business_id": "biz_health_1",
        "rating": 5,
        "aspects": ["Doctor Care", "Hygiene"],
        "language": "english"
    })
    assert res.status_code == 403
    assert "healthcare" in res.json()["detail"].lower()


def test_healthcare_ai_generate_blocked(test_env):
    client, store = test_env
    res = client.post("/api/reviews/generate", json={
        "business_id": "biz_health_1",
        "rating": 5,
        "aspects": ["Doctor Care"],
        "language": "english"
    })
    assert res.status_code == 403
    assert "healthcare" in res.json()["detail"].lower()


# ─── 2. SUSPENDED TENANT 403 TESTS ───────────────────────────────────────────

def test_suspended_tenant_blocked(test_env):
    client, store = test_env
    res = client.post("/api/reviews/ideas", json={
        "business_id": "biz_suspended_1",
        "rating": 5,
        "aspects": ["Food Quality"],
        "language": "english"
    })
    assert res.status_code == 403
    assert "suspended" in res.json()["detail"].lower()


# ─── 3. SERVER-SIDE INDUSTRY RESOLUTION & CLIENT TAMPERING IMMUNITY ──────────

def test_client_cannot_override_industry(test_env):
    client, store = test_env
    # Client sends request for biz_hotel_1 claiming it is a 'restaurant'
    res = client.post("/api/reviews/ideas", json={
        "business_id": "biz_hotel_1",
        "category": "restaurant",  # Client tries to spoof restaurant
        "rating": 5,
        "aspects": ["Room Cleanliness", "Staff Hospitality"],
        "language": "english"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["ideas"]) >= 3
    # Verify ideas talk about hotel stay/room, not food/dishes
    hotel_texts = " ".join([i["text"] for i in data["ideas"]]).lower()
    assert any(w in hotel_texts for w in ["room", "cleanliness", "hospitality", "stay", "comfort"])
    assert "breakfast and chai" not in hotel_texts


# ─── 4. ALL 9 ACTIVE INDUSTRIES PRODUCE GROUNDED IDEAS & REVIEWS ─────────────

ACTIVE_INDUSTRIES = [
    ("restaurant", ["Food Quality", "Quick Service"], "Cafe Bistro"),
    ("hotel", ["Room Cleanliness", "Staff Hospitality"], "Grand Hotel"),
    ("fitness", ["Trainer Guidance", "Equipment Quality"], "Iron Gym"),
    ("salon", ["Service Precision", "Hygiene & Sanitation"], "Style Studio"),
    ("retail", ["Collection Variety", "Fabric & Quality"], "Vogue Boutique"),
    ("automotive", ["Service Quality", "Timely Delivery"], "Speed Motors"),
    ("education", ["Teacher Dedication", "Clear Explanations"], "Bright Academy"),
    ("events", ["Venue Ambience", "Sound & Lighting"], "Celebration Hall"),
    ("travel", ["Trip Planning", "Vehicle Comfort"], "Wanderlust Tours"),
]

@pytest.mark.parametrize("ind_id, aspects, bname", ACTIVE_INDUSTRIES)
def test_active_industries_ideas_and_reviews(ind_id, aspects, bname):
    # Test Ideas
    ideas = generate_candidate_ideas(
        rating=5,
        aspects=aspects,
        user_note="Enjoyed it thoroughly",
        business_name=bname,
        language="english",
        category=ind_id
    )
    assert len(ideas) == 3
    for idea in ideas:
        assert idea["id"] in ("idea_1", "idea_2", "idea_3")
        assert len(idea["text"].split()) >= 6
        assert bname in idea["text"]

    # Test Draft Review
    draft = humanize_review_draft(
        rating=5,
        aspects=aspects,
        user_note="Will visit again",
        business_name=bname,
        language="english",
        category=ind_id
    )
    assert bname in draft
    assert len(draft.split()) >= 8


# ─── 5. UNCLASSIFIED FALLBACK TEST ───────────────────────────────────────────

def test_unclassified_fallback():
    ideas = generate_candidate_ideas(
        rating=4,
        aspects=["Service Quality", "Communication"],
        business_name="Acme Solutions",
        language="english",
        category="unknown_random_industry"
    )
    assert len(ideas) == 3
    texts = " ".join([i["text"] for i in ideas])
    assert "Acme Solutions" in texts
    assert "dishes" not in texts.lower()
    assert "room" not in texts.lower()


# ─── 6. NATIVE SCRIPT FIDELITY (GUJARATI & HINDI) ─────────────────────────────

def test_native_script_fidelity_gujarati():
    ideas = generate_candidate_ideas(
        rating=5,
        aspects=["નાસ્તો", "ચા"],
        business_name="Nasta Ghar",
        language="gujarati",
        category="restaurant"
    )
    for idea in ideas:
        text = idea["text"]
        # Must contain Gujarati Unicode characters (\u0A80-\u0AFF)
        assert re.search(r'[\u0A80-\u0AFF]', text), f"Expected Gujarati script, got: {text}"
        # Verify focus is in Gujarati
        assert any(k in idea["focus"] for k in ["સ્વાભાવિક", "અભિવ્યક્તિપૂર્ણ", "વ્યક્તિગત"])

    draft = humanize_review_draft(
        rating=5,
        aspects=["નાસ્તો", "ચા"],
        user_note="ખૂબ સ્વાદિષ્ટ",
        business_name="Nasta Ghar",
        language="gujarati",
        category="restaurant"
    )
    assert re.search(r'[\u0A80-\u0AFF]', draft)


def test_native_script_fidelity_hindi():
    ideas = generate_candidate_ideas(
        rating=5,
        aspects=["कमरे की सफ़ाई", "स्टाफ"],
        business_name="Grand Stay",
        language="hindi",
        category="hotel"
    )
    for idea in ideas:
        text = idea["text"]
        # Must contain Devanagari Unicode characters (\u0900-\u097F)
        assert re.search(r'[\u0900-\u097F]', text), f"Expected Devanagari script, got: {text}"
        # Verify focus is in Hindi
        assert any(k in idea["focus"] for k in ["स्वाभाविक", "स्पष्ट", "व्यक्तिगत"])

    draft = humanize_review_draft(
        rating=5,
        aspects=["कमरे की सफ़ाई"],
        business_name="Grand Stay",
        language="hindi",
        category="hotel"
    )
    assert re.search(r'[\u0900-\u097F]', draft)


# ─── 7. RATING CALIBRATION & EMOJI RULES ──────────────────────────────────────

def test_rating_calibration_and_emojis():
    # 5 stars has positive sentiment and tasteful emojis
    draft_5 = humanize_review_draft(
        rating=5, aspects=["Service"], business_name="Test Store", language="english", category="retail"
    )
    assert any(c in draft_5 for c in ["😊", "✨", "🛍️", "👍", "❤️"])

    # 1 star has dissatisfaction sentiment and ZERO emojis
    draft_1 = humanize_review_draft(
        rating=1, aspects=["Service"], business_name="Test Store", language="english", category="retail"
    )
    assert not any(c in draft_1 for c in ["😊", "✨", "🛍️", "👍", "❤️", "😋"])
    assert any(w in draft_1.lower() for w in ["disappointing", "below", "standards", "improvement", "unsatisfied"])


# ─── 8. NASTA GHAR PRESERVATION ───────────────────────────────────────────────

def test_nasta_ghar_preservation():
    ideas_gu = generate_candidate_ideas(
        rating=5, aspects=["Breakfast"], business_name="default_business", language="gujarati"
    )
    assert "નાસ્તા ઘર" in ideas_gu[0]["text"]

    ideas_hi = generate_candidate_ideas(
        rating=5, aspects=["Breakfast"], business_name="default_business", language="hindi"
    )
    assert "नाश्ता घर" in ideas_hi[0]["text"]

    ideas_en = generate_candidate_ideas(
        rating=5, aspects=["Breakfast"], business_name="default_business", language="english"
    )
    assert "Nasta Ghar" in ideas_en[0]["text"]


# ─── 9. PUBLIC DTO & TERMINOLOGY RESOLUTION ───────────────────────────────────

def test_public_review_link_terminology(test_env):
    client, store = test_env
    # Hotel tenant
    res = client.get("/api/businesses/biz_hotel_1/review-link")
    assert res.status_code == 200
    data = res.json()
    assert data["industry_id"] == "hotel"
    assert data["touchpoint_label"] == "Room / Suite Number"
    assert data["touchpoint_placeholder"] == "e.g. Room 302"
    assert data["allow_ai_ideas"] is True

    # Nasta Ghar (Restaurant)
    res2 = client.get("/api/businesses/default_business/review-link")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["industry_id"] == "restaurant"
    assert data2["touchpoint_label"] == "Table Number"
    assert data2["touchpoint_placeholder"] == "e.g. Table 4"


def test_iso_language_codes_hi_and_gu_produce_native_script_without_culinary_emojis():
    """Verify 'hi', 'hi-IN', 'gu', and 'gu-IN' produce Devanagari/Gujarati output without culinary emojis for gyms."""
    ideas_hi = generate_candidate_ideas(
        rating=5, aspects=["Equipment Quality"], business_name="Pulse Fitness", language="hi", category="fitness"
    )
    assert re.search(r"[\u0900-\u097F]", ideas_hi[0]["text"])
    assert "🍳" not in ideas_hi[0]["text"] and "☕" not in ideas_hi[0]["text"]

    ideas_gu = generate_candidate_ideas(
        rating=5, aspects=["Equipment Quality"], business_name="Pulse Fitness", language="gu", category="fitness"
    )
    assert re.search(r"[\u0A80-\u0AFF]", ideas_gu[0]["text"])
    assert "🍳" not in ideas_gu[0]["text"] and "☕" not in ideas_gu[0]["text"]

    draft_hi = humanize_review_draft(
        rating=5, aspects=["Equipment Quality"], business_name="Pulse Fitness", language="hi-IN", category="fitness"
    )
    assert re.search(r"[\u0900-\u097F]", draft_hi)

    draft_gu = humanize_review_draft(
        rating=5, aspects=["Equipment Quality"], business_name="Pulse Fitness", language="gu-IN", category="fitness"
    )
    assert re.search(r"[\u0A80-\u0AFF]", draft_gu)
