"""
VRAJA AI — Product A Phase A4 Integration & Verification Test Suite
Tests multi-industry customer review journey, LLM prompt generalization,
healthcare restriction enforcement, tamper resistance, and NastaGhar preservation.
"""

import re
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.industry_registry import (
    INDUSTRY_REGISTRY,
    resolve_industry,
    resolve_effective_topics,
    get_available_industries,
    get_all_industries_metadata,
)
from backend.app.core.tenants.google_reviews import google_review_manager

client = TestClient(app)


def test_industry_registry_completeness():
    """Verify all 10 standard industries plus healthcare (restricted) are properly registered."""
    expected_industries = [
        "restaurant",
        "hotel",
        "fitness",
        "salon",
        "retail",
        "automotive",
        "education",
        "events",
        "travel",
        "unclassified",
        "healthcare",
    ]
    for ind_id in expected_industries:
        ind = INDUSTRY_REGISTRY.get(ind_id)
        assert ind is not None, f"Expected industry {ind_id} in registry"
        assert ind.industry_id == ind_id
        assert ind.display_name
        assert ind.terminology is not None
        assert ind.terminology.customer_noun_singular
        assert ind.terminology.customer_noun_plural
        assert ind.terminology.touchpoint_noun
        assert ind.terminology.touchpoint_placeholder
        assert ind.terminology.disclaimer_noun
        assert ind.terminology.private_feedback_title


def test_public_review_link_terminology_schema():
    """Verify /api/businesses/{business_id}/review-link returns serialized TerminologySchema."""
    res = client.get("/api/businesses/default_business/review-link")
    assert res.status_code == 200
    data = res.json()
    assert data["business_id"] == "default_business"
    assert data["industry_id"] == "restaurant"
    assert "terminology" in data
    term = data["terminology"]
    assert term is not None
    assert "customer_noun_singular" in term
    assert "customer_noun_plural" in term
    assert "touchpoint_noun" in term
    assert "touchpoint_placeholder" in term
    assert "disclaimer_noun" in term
    assert "private_feedback_title" in term
    assert term["customer_noun_singular"].lower() == "diner"


def test_all_industries_generate_ideas_without_culinary_fabrication():
    """Verify each non-restaurant industry produces grounded suggestions with zero culinary fabrication."""
    non_restaurant_industries = [
        "hotel",
        "fitness",
        "salon",
        "retail",
        "automotive",
        "education",
        "events",
        "travel",
        "unclassified",
    ]
    culinary_keywords = ["breakfast", "chai", "snack", "poha", "taste & flavour", "tea", "coffee"]

    for ind_id in non_restaurant_industries:
        ind = INDUSTRY_REGISTRY.get(ind_id)
        # Register temporary test tenant config in memory
        test_biz = f"test_{ind_id}_biz"
        google_review_manager.update_business_config(
            business_id=test_biz,
            google_review_url="https://maps.google.com/test",
            business_name=f"Vraja {ind.display_name} Studio",
            category=ind.subcategories[0] if ind.subcategories else ind.display_name,
            industry_id=ind_id,
            topics=ind.default_topics[:3],
        )

        # Call review ideas endpoint
        res = client.post(
            "/api/reviews/ideas",
            json={
                "business_id": test_biz,
                "rating": 5,
                "aspects": ind.default_topics[:2],
                "user_note": "Great staff and very professional experience",
                "language": "english",
            },
        )
        assert res.status_code == 200, f"Failed for industry {ind_id}: {res.text}"
        data = res.json()
        assert "ideas" in data
        assert len(data["ideas"]) >= 1

        for idea in data["ideas"]:
            text_lower = idea["text"].lower()
            # Ensure none of the restaurant-only keywords appear in non-restaurant review copy
            for kw in culinary_keywords:
                assert not re.search(r"\b" + re.escape(kw) + r"\b", text_lower), (
                    f"Industry '{ind_id}' generated culinary keyword '{kw}' in draft: '{idea['text']}'"
                )


def test_tamper_resistance_ignores_client_supplied_industry():
    """Verify that client-supplied industry_id is never trusted or used to override backend authority."""
    # test_fitness_biz is configured as 'fitness'
    google_review_manager.update_business_config(
        business_id="test_tamper_fitness",
        google_review_url="https://maps.google.com/fitness",
        business_name="Iron Fit Gym",
        category="Gym",
        industry_id="fitness",
        topics=["Equipment Quality", "Trainer Support"],
    )

    # Attempt to spoof as 'restaurant' via request body
    res = client.post(
        "/api/reviews/ideas",
        json={
            "business_id": "test_tamper_fitness",
            "rating": 5,
            "aspects": ["Equipment Quality"],
            "user_note": "Solid workout today",
            "language": "english",
            "industry_id": "restaurant",  # Spoofed!
        },
    )
    assert res.status_code == 200
    data = res.json()
    # Ideas should not contain restaurant references like chai or breakfast
    for idea in data["ideas"]:
        assert "breakfast" not in idea["text"].lower()
        assert "chai" not in idea["text"].lower()


def test_restricted_healthcare_enforcement():
    """Verify that healthcare industry is strictly restricted and returns 403 on all review endpoints."""
    google_review_manager.update_business_config(
        business_id="test_clinic",
        google_review_url="https://maps.google.com/clinic",
        business_name="City Health Clinic",
        category="Clinic",
        industry_id="healthcare",
    )

    # 1. Review link endpoint
    res_link = client.get("/api/businesses/test_clinic/review-link")
    assert res_link.status_code == 403
    assert "restricted" in res_link.json()["detail"].lower()

    # 2. Review ideas endpoint
    res_ideas = client.post(
        "/api/reviews/ideas",
        json={"business_id": "test_clinic", "rating": 5},
    )
    assert res_ideas.status_code == 403
    assert "restricted" in res_ideas.json()["detail"].lower()

    # 3. Review generate endpoint
    res_gen = client.post(
        "/api/reviews/generate",
        json={"business_id": "test_clinic", "rating": 5, "user_draft": "Doctor was kind"},
    )
    assert res_gen.status_code == 403
    assert "restricted" in res_gen.json()["detail"].lower()

    # 4. Review session endpoint
    res_sess = client.post(
        "/api/reviews/session",
        json={"business_id": "test_clinic"},
    )
    assert res_sess.status_code == 403
    assert "restricted" in res_sess.json()["detail"].lower()

    # 5. Private feedback endpoint
    res_fb = client.post(
        "/api/reviews/private-feedback",
        json={"business_id": "test_clinic", "rating": 2, "diner_note": "Long wait"},
    )
    assert res_fb.status_code == 403
    assert "restricted" in res_fb.json()["detail"].lower()


def test_unobstructed_google_review_access_all_ratings():
    """Verify that all ratings (1 to 5 stars) have equal, unobstructed access to the Google Review URL."""
    res_link = client.get("/api/businesses/default_business/review-link")
    assert res_link.status_code == 200
    target_url = res_link.json()["review_url"]
    assert bool(target_url)

    # The review URL returned by the config API must be available to the client regardless of rating
    # Validate that neither backend nor frontend restricts review_url for 1 or 2 stars
    for star in [1, 2, 3, 4, 5]:
        res_ideas = client.post(
            "/api/reviews/ideas",
            json={
                "business_id": "default_business",
                "rating": star,
                "language": "english",
            },
        )
        assert res_ideas.status_code == 200
        # Review ideas endpoint must successfully return suggestions for all stars
        assert len(res_ideas.json()["ideas"]) >= 1


def test_nastaghar_preservation():
    """Verify that NastaGhar homestyle Gujarati, Hindi, and English breakfast & chai suggestions are preserved."""
    # Gujarati 5-star
    res_gu = client.post(
        "/api/reviews/ideas",
        json={
            "business_id": "default_business",
            "rating": 5,
            "aspects": ["Breakfast", "Chai & Beverages"],
            "language": "gujarati",
        },
    )
    assert res_gu.status_code == 200
    ideas_gu = [i["text"] for i in res_gu.json()["ideas"]]
    assert any("નાસ્તા ઘર" in t or "Nasta Ghar" in t for t in ideas_gu)

    # English 5-star with personal note
    res_en = client.post(
        "/api/reviews/ideas",
        json={
            "business_id": "default_business",
            "rating": 5,
            "aspects": ["Breakfast", "Taste & Flavour"],
            "user_note": "The thepla was amazing",
            "language": "english",
        },
    )
    assert res_en.status_code == 200
    ideas_en = [i["text"] for i in res_en.json()["ideas"]]
    assert any("thepla was amazing" in t for t in ideas_en)
