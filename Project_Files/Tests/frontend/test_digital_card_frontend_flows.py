"""
Automated Test Suite for Vraja Phase 8.3:
Digital Business Card Frontend Flows, Endpoints, Entitlements,
Asset Build Verification, and Review System Regression Behavior.
"""

import json
import os
import re
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import (
    DocumentStorageService,
    _document_services,
)
from Backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    _login_attempts,
    _login_lock,
)
from Backend.app.api.service import review_service

SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj "
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
    b"0000000052 00000 n \n0000000102 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF"
)


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Provides an isolated database and document storage root for frontend tests."""
    db_path = tmp_path / "frontend_flow_db.sqlite3"
    docs_path = tmp_path / "frontend_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    _document_services.clear()
    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))

    # 1. Combined Tenant (Cafe Alpha)
    store.upsert_tenant({
        "id": "cafe_alpha",
        "business_name": "Cafe Alpha",
        "category": "Artisanal Cafe",
        "description": "Specialty coffee in Ahmedabad.",
        "primary_accent": "#0ea5e9",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })
    owner_alpha = store.create_user(
        email="owner@alpha.test",
        password_hash=hash_password("AlphaPass123!"),
        display_name="Alpha Owner",
        is_active=1,
    )
    store.add_membership(owner_alpha["id"], "cafe_alpha", role="owner")

    # 2. Card-Only Tenant (Boutique Beta)
    store.upsert_tenant({
        "id": "boutique_beta",
        "business_name": "Boutique Beta",
        "category": "Fashion Boutique",
        "description": "Designer pret-a-porter and accessories.",
        "primary_accent": "#ec4899",
        "status": "active",
        "entitlements": ["digital_card"],
    })
    owner_beta = store.create_user(
        email="owner@beta.test",
        password_hash=hash_password("BetaPass123!"),
        display_name="Beta Owner",
        is_active=1,
    )
    store.add_membership(owner_beta["id"], "boutique_beta", role="owner")

    # 3. Review-Only Tenant (Diner Gamma)
    store.upsert_tenant({
        "id": "diner_gamma",
        "business_name": "Diner Gamma",
        "category": "American Diner",
        "status": "active",
        "entitlements": ["review_manager"],
    })
    owner_gamma = store.create_user(
        email="owner@gamma.test",
        password_hash=hash_password("GammaPass123!"),
        display_name="Gamma Owner",
        is_active=1,
    )
    store.add_membership(owner_gamma["id"], "diner_gamma", role="owner")

    client = TestClient(app)

    def login(user_id: str, tenant_id: str) -> TestClient:
        token = generate_session_token()
        token_hash = hash_token(token)
        store.create_session(
            token_hash=token_hash,
            user_id=user_id,
            active_tenant_id=tenant_id,
            expires_at=time.time() + SESSION_TTL_SECONDS,
        )
        c = TestClient(app)
        c.cookies.set(OWNER_COOKIE, token)
        return c

    return {
        "client": client,
        "login": login,
        "store": store,
        "docs_path": docs_path,
        "owner_alpha": owner_alpha,
        "owner_beta": owner_beta,
        "owner_gamma": owner_gamma,
    }


# ─── 1. Public Card Rendering & Missing Optional Fields ──────────────────────

def test_public_card_with_missing_optional_fields(test_env):
    """Tests that a card with only partial/minimal fields returns valid response without crashing."""
    store = test_env["store"]
    client = test_env["client"]

    # Minimal profile: no phone, no website, no socials, no custom links
    store.upsert_business_profile("cafe_alpha", {
        "tagline": "Minimalist coffee experience",
        "is_published": True,
        "show_review_button": True,
    })

    res = client.get("/api/businesses/cafe_alpha/card")
    assert res.status_code == 200
    card = res.json()

    assert card["business_name"] == "Cafe Alpha"
    assert card["tagline"] == "Minimalist coffee experience"
    # Graceful missing fields
    assert card["phone_number"] == ""
    assert card["website_url"] == ""
    assert card["address"] == ""
    assert card["map_url"] == ""
    assert card["whatsapp_url"] == ""
    assert card["instagram_url"] == ""
    assert card["custom_links"] == []
    assert card["documents"] == []
    assert card["show_review_button"] is True


def test_public_card_with_complete_fields(test_env):
    """Tests that a fully configured card returns all fields formatted and normalized."""
    store = test_env["store"]
    client = test_env["client"]
    docs_path = test_env["docs_path"]

    store.upsert_business_profile("cafe_alpha", {
        "tagline": "Artisanal pour-overs & fresh bakes",
        "phone_number": "+91 98765 43210",
        "website_url": "cafealpha.example.com",
        "address": "404 Cafe Street, Ahmedabad",
        "map_url": "maps.google.com/?q=23.0,72.5",
        "whatsapp_url": "919876543210",
        "instagram_url": "instagram.com/cafealpha",
        "facebook_url": "facebook.com/cafealpha",
        "youtube_url": "youtube.com/@cafealpha",
        "logo_path": "https://example.com/logo.png",
        "cover_image_path": "https://example.com/cover.jpg",
        "custom_links": [{"title": "Swiggy", "url": "swiggy.com/restaurants/alpha"}],
        "is_published": True,
        "show_review_button": True,
    })

    # Upload document
    doc_service = DocumentStorageService(storage_root=docs_path, store=store)
    doc = doc_service.save_document(
        tenant_id="cafe_alpha",
        content=SAMPLE_PDF_BYTES,
        original_filename="Main_Menu.pdf",
        document_type="food_menu",
        display_name="Food & Beverage Menu",
        is_published=True,
    )

    res = client.get("/api/businesses/cafe_alpha/card")
    assert res.status_code == 200
    card = res.json()

    assert card["tagline"] == "Artisanal pour-overs & fresh bakes"
    assert card["website_url"] == "https://cafealpha.example.com"
    assert card["map_url"] == "https://maps.google.com/?q=23.0,72.5"
    assert card["instagram_url"] == "https://instagram.com/cafealpha"
    assert len(card["custom_links"]) == 1
    assert card["custom_links"][0]["url"] == "https://swiggy.com/restaurants/alpha"

    assert len(card["documents"]) == 1
    assert card["documents"][0]["id"] == doc["id"]
    assert card["documents"][0]["display_name"] == "Food & Beverage Menu"
    assert card["documents"][0]["download_url"] == f"/api/businesses/cafe_alpha/documents/{doc['id']}/file"


# ─── 2. Draft vs Published Visibility ────────────────────────────────────────

def test_draft_versus_published_visibility(test_env):
    """Anonymous visitors receive 404 for unpublished cards, while owners can preview drafts."""
    store = test_env["store"]
    client = test_env["client"]
    login = test_env["login"]
    owner_alpha = test_env["owner_alpha"]

    # 1. Initially draft (is_published=False)
    store.upsert_business_profile("cafe_alpha", {
        "tagline": "Secret upcoming cafe",
        "is_published": False,
    })

    # Public request returns 404
    anon_res = client.get("/api/businesses/cafe_alpha/card")
    assert anon_res.status_code == 404
    assert "not found or not published" in anon_res.json()["detail"].lower()

    # Authenticated owner GET /profile returns the draft
    auth_client = login(owner_alpha["id"], "cafe_alpha")
    owner_res = auth_client.get("/api/businesses/cafe_alpha/profile")
    assert owner_res.status_code == 200
    assert owner_res.json()["tagline"] == "Secret upcoming cafe"
    assert owner_res.json()["is_published"] is False

    # 2. Owner publishes card
    publish_res = auth_client.put(
        "/api/businesses/cafe_alpha/profile",
        json={"is_published": True},
    )
    assert publish_res.status_code == 200
    assert publish_res.json()["is_published"] is True

    # Now public request succeeds
    anon_published_res = client.get("/api/businesses/cafe_alpha/card")
    assert anon_published_res.status_code == 200
    assert anon_published_res.json()["tagline"] == "Secret upcoming cafe"


# ─── 3. Card-Only, Review-Only & Combined Entitlement Scenarios ──────────────

def test_card_only_tenant_review_button_and_analytics_suppression(test_env):
    """Card-only tenants have show_review_button=False on card and cannot access review analytics."""
    store = test_env["store"]
    client = test_env["client"]
    login = test_env["login"]
    owner_beta = test_env["owner_beta"]

    # Boutique Beta attempts to set show_review_button=True
    auth_beta = login(owner_beta["id"], "boutique_beta")
    put_res = auth_beta.put(
        "/api/businesses/boutique_beta/profile",
        json={
            "tagline": "Luxury Designer Wear",
            "show_review_button": True,
            "is_published": True,
        },
    )
    assert put_res.status_code == 200

    # Public card: show_review_button MUST be False because tenant lacks review_manager entitlement
    public_res = client.get("/api/businesses/boutique_beta/card")
    assert public_res.status_code == 200
    assert public_res.json()["show_review_button"] is False

    # Boutique Beta owner CANNOT access review manager analytics
    analytics_res = auth_beta.get("/api/reviews/analytics")
    assert analytics_res.status_code == 403
    assert "review_manager" in analytics_res.json()["detail"]


def test_review_only_tenant_card_blocking(test_env):
    """Review-only tenants cannot publish cards, view cards, or upload documents."""
    client = test_env["client"]
    login = test_env["login"]
    owner_gamma = test_env["owner_gamma"]

    # Public card returns 404
    anon_res = client.get("/api/businesses/diner_gamma/card")
    assert anon_res.status_code == 404

    # Owner cannot edit card profile -> 403
    auth_gamma = login(owner_gamma["id"], "diner_gamma")
    edit_res = auth_gamma.put(
        "/api/businesses/diner_gamma/profile",
        json={"tagline": "Unauthorized card edit"},
    )
    assert edit_res.status_code == 403
    assert "digital_card" in edit_res.json()["detail"]

    # Owner cannot upload documents -> 403
    files = {"file": ("menu.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    upload_res = auth_gamma.post(
        "/api/businesses/diner_gamma/documents",
        files=files,
    )
    assert upload_res.status_code == 403
    assert "digital_card" in upload_res.json()["detail"]

    # But review link & review assistance work smoothly
    rev_link = client.get("/api/businesses/diner_gamma/review-link")
    assert rev_link.status_code == 200
    assert rev_link.json()["business_name"] == "Diner Gamma"


# ─── 4. Cross-Tenant Isolation ───────────────────────────────────────────────

def test_cross_tenant_mutation_and_document_protection(test_env):
    """Tenant A owner cannot edit Tenant B profile or delete Tenant B documents."""
    login = test_env["login"]
    owner_alpha = test_env["owner_alpha"]
    owner_beta = test_env["owner_beta"]

    auth_alpha = login(owner_alpha["id"], "cafe_alpha")
    auth_beta = login(owner_beta["id"], "boutique_beta")

    # Tenant B uploads a catalogue
    files = {"file": ("Winter_Collection.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    upload_res = auth_beta.post(
        "/api/businesses/boutique_beta/documents",
        files=files,
        data={"display_name": "Winter Collection", "document_type": "catalogue"},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Tenant A attempts to edit Tenant B's profile -> 403 Forbidden
    hack_res = auth_alpha.put(
        "/api/businesses/boutique_beta/profile",
        json={"tagline": "Hacked by Alpha"},
    )
    assert hack_res.status_code == 403

    # Tenant A attempts to delete Tenant B's document via Tenant A's endpoint -> 404
    del_res1 = auth_alpha.delete(f"/api/businesses/cafe_alpha/documents/{doc_id}")
    assert del_res1.status_code == 404

    # Tenant A attempts to delete Tenant B's document via Tenant B's endpoint -> 403
    del_res2 = auth_alpha.delete(f"/api/businesses/boutique_beta/documents/{doc_id}")
    assert del_res2.status_code == 403

    # Document remains intact for Tenant B
    verify_docs = auth_beta.get("/api/businesses/boutique_beta/documents")
    assert verify_docs.status_code == 200
    assert any(d["id"] == doc_id for d in verify_docs.json())


# ─── 5. QR Code and Sharing URL Correctness ───────────────────────────────────

def test_card_qr_destination_and_canonical_sharing_url(test_env):
    """QR destination info points strictly to /card/:tenant, NOT the review URL."""
    client = test_env["client"]
    store = test_env["store"]

    store.upsert_business_profile("cafe_alpha", {"is_published": True})

    # Fetch Card QR info
    qr_res = client.get("/api/businesses/cafe_alpha/card/qr-info")
    assert qr_res.status_code == 200
    qr_data = qr_res.json()

    assert qr_data["business_id"] == "cafe_alpha"
    assert qr_data["card_path"] == "/card/cafe_alpha"
    assert qr_data["is_published"] is True
    # Ensure it does NOT point to review URL
    assert "review" not in qr_data["card_path"]

    # Review link endpoint remains distinct
    rev_res = client.get("/api/businesses/cafe_alpha/review-link")
    assert rev_res.status_code == 200
    assert rev_res.json()["business_id"] == "cafe_alpha"


# ─── 6. Frontend Build & Bundle Contract Verification ────────────────────────

def test_frontend_production_build_contains_card_components():
    """Verifies that the compiled Vite production bundle includes DigitalCard & Editor components."""
    _repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists()), Path(__file__).resolve().parents[3])
    candidates = [
        _repo_root / "Digital_Card" / "frontend" / "dist",
        _repo_root / "product-b" / "frontend" / "dist",
        _repo_root / "NastaGhar" / "frontend" / "dist",
    ]
    dist_dir = next((p for p in candidates if (p / "index.html").exists()), candidates[0])
    index_html = dist_dir / "index.html"
    assert index_html.exists(), "Frontend production build (dist/index.html) must exist."

    html_content = index_html.read_text(encoding="utf-8")
    assert '<div id="root">' in html_content, "index.html must include root mount point."

    # Search compiled JS chunks for component strings
    js_files = list((dist_dir / "assets").glob("*.js"))
    assert len(js_files) > 0, "At least one JS bundle must exist in dist/assets."

    combined_js = "".join(f.read_text(encoding="utf-8") for f in js_files)

    # Assert critical Digital Card and Editor signatures are present in compiled bundle
    assert "Digital Business Card" in combined_js or "card-outer-wrap" in combined_js or "card-identity-block" in combined_js
    assert "uploadCategory" in combined_js or "food_menu" in combined_js
    assert "canonicalCardUrl" in combined_js or "/card" in combined_js


# ─── 7. Preservation of Review Assistant System ──────────────────────────────

def test_review_system_remains_unaffected(test_env):
    """Review ideas, review validation, and private feedback routing continue without gating."""
    client = test_env["client"]

    # 1. Review ideas generation
    ideas_res = client.post(
        "/api/reviews/ideas",
        json={
            "business_id": "cafe_alpha",
            "rating": 5,
            "aspects": ["food", "service", "vibe"],
            "user_note": "Great cappuccino and avocado toast",
        },
    )
    assert ideas_res.status_code == 200
    assert len(ideas_res.json()["ideas"]) > 0

    # 2. Private feedback submission
    fb_res = client.post(
        "/api/reviews/private-feedback",
        json={
            "business_id": "cafe_alpha",
            "rating": 5,
            "diner_note": "Exceptional hospitality!",
        },
    )
    assert fb_res.status_code == 200
    assert "ticket_id" in fb_res.json()
