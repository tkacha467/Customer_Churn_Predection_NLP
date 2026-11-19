"""
Automated Test Suite for VRAJA AI Phase A5.0: Approved Corrections and Technical Verification.

Covers:
1. Industry Resolution Precedence and Invalid ID handling (Task 2).
2. GoogleReviewManager Cache Consistency & Worker Invalidation (Task 3).
3. Analytics Event Deduplication & Historical Compatibility (Task 4).
4. Unobstructed Google Access across All 5 Ratings (Task 1 & Task 5).
5. Private Feedback Optionality & Non-Gating Behavior (Task 1 & Task 5).
6. Multi-Tenant Analytics Isolation (Task 5).
"""

import os
import json
import time
import uuid
import zoneinfo
from datetime import datetime, date, time as dtime, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.industry_registry import (
    resolve_industry,
    CANONICAL_INDUSTRIES,
    UNCLASSIFIED_INDUSTRY,
)
from backend.app.core.tenants.google_reviews import GoogleReviewManager
import backend.app.core.tenants.google_reviews as gr_module
from backend.app.core.database.storage import ReviewStore
from backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    _login_attempts,
    _login_lock,
)
from backend.app.api.service import ReviewService

client = TestClient(app)


# =====================================================================
# 1. INDUSTRY RESOLUTION LOGIC & PRECEDENCE (TASK 2)
# =====================================================================

def test_resolve_industry_valid_explicit_id():
    """Valid explicit industry ID takes precedence over everything."""
    # Matches canonical industry
    ind = resolve_industry(industry_id="hotel", category="Breakfast & Snacks")
    assert ind.industry_id == "hotel"
    assert ind.display_name == "Hotels & Hospitality"

    ind_fit = resolve_industry(explicit_industry_id="fitness", category="Cafe")
    assert ind_fit.industry_id == "fitness"
    assert ind_fit.terminology.customer_noun_singular == "Member"


def test_resolve_industry_invalid_explicit_id_returns_unclassified():
    """
    Invalid non-empty explicit industry ID must return 'unclassified'.
    Crucially, it must NEVER fall through to legacy category mapping.
    """
    # Conflicting: invalid explicit ID + valid legacy category
    ind = resolve_industry(industry_id="crypto_mining_center", category="Breakfast & Snacks")
    assert ind.industry_id == "unclassified"
    assert ind.display_name == "Unclassified Business"

    ind2 = resolve_industry(explicit_industry_id="bogus_industry", category="Cafe & Dining")
    assert ind2.industry_id == "unclassified"


def test_resolve_industry_missing_explicit_id_uses_category():
    """Missing explicit industry ID falls back to legacy category mapping."""
    # None
    ind_none = resolve_industry(industry_id=None, category="Breakfast & Snacks")
    assert ind_none.industry_id == "restaurant"

    # Empty string
    ind_empty = resolve_industry(industry_id="", category="Fine Dining")
    assert ind_empty.industry_id == "restaurant"

    # Whitespace
    ind_ws = resolve_industry(explicit_industry_id="   ", category="Spa & Salon")
    assert ind_ws.industry_id == "salon"


def test_resolve_industry_unknown_category_returns_unclassified():
    """Unknown category with missing explicit industry ID returns unclassified."""
    ind = resolve_industry(industry_id=None, category="Aerospace Propulsion Lab")
    assert ind.industry_id == "unclassified"

    ind_blank = resolve_industry(industry_id=None, category="")
    assert ind_blank.industry_id == "unclassified"


# =====================================================================
# 2. CACHE CONSISTENCY & WORKER INVALIDATION (TASK 3)
# =====================================================================

def test_cache_consistency_across_workers(tmp_path, monkeypatch):
    """
    Simulate multi-worker environment:
    When an external worker updates business_links.json on disk,
    GoogleReviewManager automatically refreshes via mtime detection.
    """
    links_file = tmp_path / "shared_business_links.json"
    init_data = {
        "test_tenant": {
            "business_name": "Initial Name",
            "google_review_url": "https://maps.google.com/initial",
            "category": "Breakfast & Snacks",
            "industry_id": "restaurant"
        }
    }
    links_file.write_text(json.dumps(init_data), encoding="utf-8")

    monkeypatch.setattr(gr_module, "CONFIG_FILE", links_file)

    manager = GoogleReviewManager()
    info1 = manager.get_review_url("test_tenant")
    assert info1 is not None
    assert info1["business_name"] == "Initial Name"
    assert info1["industry_id"] == "restaurant"

    # Simulate Worker 2 updating the file on disk (bump mtime)
    time.sleep(0.05)  # Ensure mtime difference
    updated_data = {
        "test_tenant": {
            "business_name": "Updated Hotel Name",
            "google_review_url": "https://maps.google.com/updated",
            "category": "Luxury Stay",
            "industry_id": "hotel"
        }
    }
    links_file.write_text(json.dumps(updated_data), encoding="utf-8")
    os.utime(links_file, (time.time() + 1, time.time() + 1))

    # Worker 1 reads again -> detects new mtime -> reloads fresh configuration
    info2 = manager.get_review_url("test_tenant")
    assert info2 is not None
    assert info2["business_name"] == "Updated Hotel Name"
    assert info2["industry_id"] == "hotel"

    # Explicit cache invalidation
    manager.invalidate_cache()
    info3 = manager.get_review_url("test_tenant")
    assert info3["industry_id"] == "hotel"


# =====================================================================
# 3. ANALYTICS EVENT DEDUPLICATION (TASK 4)
# =====================================================================

def test_analytics_deduplication_historical_events(tmp_path, monkeypatch):
    """
    Verify that historical duplicate events (google_maps_redirect + google_review_link_opened)
    are not double-counted in google_clicks.
    """
    db_file = tmp_path / "dedup_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    tenant_id = "dedup_biz"
    now = time.time()

    # Session 1: Historical dual firing (both redirect and link_opened emitted)
    u1 = str(uuid.uuid4())
    store.add_event({
        "event_id": "ev-1a",
        "event_name": "google_maps_redirect",
        "session_id": u1,
        "timestamp": now - 100,
        "metadata": {"business_id": tenant_id}
    }, tenant_id=tenant_id)
    store.add_event({
        "event_id": "ev-1b",
        "event_name": "google_review_link_opened",
        "session_id": u1,
        "timestamp": now - 100,
        "metadata": {"business_id": tenant_id}
    }, tenant_id=tenant_id)

    # Session 2: Legacy single-event session (only google_review_link_opened)
    u2 = str(uuid.uuid4())
    store.add_event({
        "event_id": "ev-2",
        "event_name": "google_review_link_opened",
        "session_id": u2,
        "timestamp": now - 80,
        "metadata": {"business_id": tenant_id}
    }, tenant_id=tenant_id)

    # Session 3: Dual clipboard copy events (review_clipboard_success + review_copied)
    u3 = str(uuid.uuid4())
    store.add_event({
        "event_id": "ev-3a",
        "event_name": "review_clipboard_success",
        "session_id": u3,
        "timestamp": now - 60,
        "metadata": {"business_id": tenant_id}
    }, tenant_id=tenant_id)
    store.add_event({
        "event_id": "ev-3b",
        "event_name": "review_copied",
        "session_id": u3,
        "timestamp": now - 60,
        "metadata": {"business_id": tenant_id}
    }, tenant_id=tenant_id)

    # Session 4: Legacy single-event copy (only review_copied)
    u4 = str(uuid.uuid4())
    store.add_event({
        "event_id": "ev-4",
        "event_name": "review_copied",
        "session_id": u4,
        "timestamp": now - 40,
        "metadata": {"business_id": tenant_id}
    }, tenant_id=tenant_id)

    summary = service.get_analytics_summary(business_id=tenant_id)

    # Session 1 has both events -> must count as 1, Session 2 has 1 -> total 2 (NOT 3!)
    assert summary["google_clicks"] == 2

    # Session 3 has both events -> must count as 1, Session 4 has 1 -> total 2 (NOT 3!)
    assert summary["reviews_copied"] == 2


# =====================================================================
# 4. UNOBSTRUCTED GOOGLE ACCESS ACROSS ALL 5 RATINGS (TASKS 1 & 5)
# =====================================================================

@pytest.mark.parametrize("star", [1, 2, 3, 4, 5])
def test_google_access_all_ratings_unobstructed(star):
    """
    Every star rating (1 to 5) must have equal, unobstructed access to Google Review URLs.
    Ideas and draft generation must succeed without gating.
    """
    # 1. Verify config endpoint supplies review URL
    res_link = client.get("/api/businesses/default_business/review-link")
    assert res_link.status_code == 200
    review_url = res_link.json()["review_url"]
    assert bool(review_url)

    # 2. Ideas generation succeeds for rating
    res_ideas = client.post("/api/reviews/ideas", json={
        "business_id": "default_business",
        "rating": star,
        "language": "english"
    })
    assert res_ideas.status_code == 200
    assert len(res_ideas.json()["ideas"]) >= 1

    # 3. Review generation succeeds for rating
    res_gen = client.post("/api/reviews/generate", json={
        "business_id": "default_business",
        "rating": star,
        "language": "english"
    })
    assert res_gen.status_code == 200
    data = res_gen.json()
    assert bool(data["review"])
    assert data["rating_consistent"] is True


def test_private_feedback_optional_and_non_gating():
    """
    Private feedback is purely optional:
    1. Skipping private feedback allows immediate Google review handoff.
    2. Submitting private feedback does NOT prevent subsequent Google access.
    """
    # Customer with 1-star skips private feedback, generates review draft directly
    res_gen1 = client.post("/api/reviews/generate", json={
        "business_id": "default_business",
        "rating": 1,
        "user_note": "Service was very slow today"
    })
    assert res_gen1.status_code == 200
    assert len(res_gen1.json()["review"]) > 10

    # Customer submits private feedback
    res_fb = client.post("/api/reviews/private-feedback", json={
        "business_id": "default_business",
        "rating": 1,
        "diner_note": "Direct message to manager about cold food",
        "guest_contact": "diner@example.com"
    })
    assert res_fb.status_code == 200
    assert res_fb.json()["status"] == "escalated"

    # Customer can STILL proceed to Google review URL / generate draft after private submission
    res_link = client.get("/api/businesses/default_business/review-link")
    assert res_link.status_code == 200
    assert bool(res_link.json()["review_url"])

    res_gen2 = client.post("/api/reviews/generate", json={
        "business_id": "default_business",
        "rating": 1,
        "user_note": "Follow-up public review note"
    })
    assert res_gen2.status_code == 200


# =====================================================================
# 5. MULTI-TENANT ANALYTICS ISOLATION (TASK 5)
# =====================================================================

def test_tenant_analytics_isolation(tmp_path, monkeypatch):
    """Events for Tenant Alpha never pollute or appear in Tenant Beta analytics."""
    db_file = tmp_path / "tenant_isolation_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    now = time.time()
    # 5 events for tenant_a with valid UUIDv4 sessions
    for i in range(5):
        store.add_event({
            "event_id": f"ev-a-{i}",
            "event_name": "google_maps_redirect",
            "session_id": str(uuid.uuid4()),
            "timestamp": now - i * 10,
            "metadata": {"business_id": "tenant_a"}
        }, tenant_id="tenant_a")

    # 2 events for tenant_b with valid UUIDv4 sessions
    for i in range(2):
        store.add_event({
            "event_id": f"ev-b-{i}",
            "event_name": "google_maps_redirect",
            "session_id": str(uuid.uuid4()),
            "timestamp": now - i * 10,
            "metadata": {"business_id": "tenant_b"}
        }, tenant_id="tenant_b")

    sum_a = service.get_analytics_summary(business_id="tenant_a")
    sum_b = service.get_analytics_summary(business_id="tenant_b")

    assert sum_a["google_clicks"] == 5
    assert sum_b["google_clicks"] == 2


# =====================================================================
# 6. PHASE A5.0.1 FOCUSED HARDENING TESTS
# =====================================================================

def test_rapid_consecutive_configuration_updates(tmp_path, monkeypatch):
    """
    Rapid consecutive writes to business_links.json are reliably detected
    by independent manager instances using sub-second cache key (mtime_ns, size).
    """
    links_file = tmp_path / "rapid_links.json"
    init_data = {
        "tenant_rapid": {
            "business_name": "Version 1",
            "google_review_url": "https://maps.google.com/v1",
            "category": "Casual Dining",
            "industry_id": "restaurant"
        }
    }
    links_file.write_text(json.dumps(init_data), encoding="utf-8")
    monkeypatch.setattr(gr_module, "CONFIG_FILE", links_file)

    mgr1 = GoogleReviewManager()
    mgr2 = GoogleReviewManager()

    assert mgr1.get_review_url("tenant_rapid")["business_name"] == "Version 1"
    assert mgr2.get_review_url("tenant_rapid")["business_name"] == "Version 1"

    # Rapid update 1
    init_data["tenant_rapid"]["business_name"] = "Version 2 (Instant)"
    links_file.write_text(json.dumps(init_data), encoding="utf-8")

    assert mgr1.get_review_url("tenant_rapid")["business_name"] == "Version 2 (Instant)"
    assert mgr2.get_review_url("tenant_rapid")["business_name"] == "Version 2 (Instant)"

    # Rapid update 2 immediately following
    init_data["tenant_rapid"]["business_name"] = "Version 3 (Sub-millisecond)"
    init_data["tenant_rapid"]["industry_id"] = "hotel"
    links_file.write_text(json.dumps(init_data), encoding="utf-8")

    assert mgr1.get_review_url("tenant_rapid")["business_name"] == "Version 3 (Sub-millisecond)"
    assert mgr1.get_review_url("tenant_rapid")["industry_id"] == "hotel"
    assert mgr2.get_review_url("tenant_rapid")["business_name"] == "Version 3 (Sub-millisecond)"
    assert mgr2.get_review_url("tenant_rapid")["industry_id"] == "hotel"


def test_missing_configuration_file_handling(tmp_path, monkeypatch):
    """Missing configuration file is handled safely without deadlock or exception."""
    missing_file = tmp_path / "does_not_exist_links.json"
    monkeypatch.setattr(gr_module, "CONFIG_FILE", missing_file)

    manager = GoogleReviewManager()
    res = manager.get_review_url("non_existent_tenant", allow_default_fallback=False)
    assert res is None

    res_default = manager.get_review_url("default_business", allow_default_fallback=True)
    assert res_default is not None
    assert res_default["business_name"] == "Nasta Ghar"


def test_multiple_canonical_redirects_one_session(tmp_path, monkeypatch):
    """Multiple google_maps_redirect events in the same session must count as exactly 1 handoff."""
    db_file = tmp_path / "multi_redirect_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    now = time.time()
    sess_single = str(uuid.uuid4())
    # 5 clicks within the same user session
    for i in range(5):
        store.add_event({
            "event_id": f"ev-multi-{i}",
            "event_name": "google_maps_redirect",
            "session_id": sess_single,
            "timestamp": now - (10 - i),
            "metadata": {"business_id": "multi_biz"}
        }, tenant_id="multi_biz")

    summary = service.get_analytics_summary(business_id="multi_biz")
    assert summary["google_clicks"] == 1


def test_canonical_and_legacy_events_same_session(tmp_path, monkeypatch):
    """Canonical google_maps_redirect and legacy aliases in the same session count as 1."""
    db_file = tmp_path / "canonical_legacy_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    now = time.time()
    sess_mixed = str(uuid.uuid4())
    store.add_event({
        "event_id": "ev-can-1",
        "event_name": "google_maps_redirect",
        "session_id": sess_mixed,
        "timestamp": now - 30,
        "metadata": {"business_id": "mix_biz"}
    }, tenant_id="mix_biz")
    store.add_event({
        "event_id": "ev-leg-1",
        "event_name": "google_review_link_opened",
        "session_id": sess_mixed,
        "timestamp": now - 30,
        "metadata": {"business_id": "mix_biz"}
    }, tenant_id="mix_biz")
    store.add_event({
        "event_id": "ev-leg-2",
        "event_name": "google_review_link_clicked",
        "session_id": sess_mixed,
        "timestamp": now - 29,
        "metadata": {"business_id": "mix_biz"}
    }, tenant_id="mix_biz")

    summary = service.get_analytics_summary(business_id="mix_biz")
    assert summary["google_clicks"] == 1


def test_anonymous_events_excluded_from_conversions(tmp_path, monkeypatch):
    """Anonymous events without valid session_id are not counted as valid session handoffs."""
    db_file = tmp_path / "anon_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    now = time.time()
    # Anonymous & malformed events
    store.add_event({
        "event_id": "ev-anon-1",
        "event_name": "google_maps_redirect",
        "session_id": "anonymous",
        "timestamp": now - 25,
        "metadata": {"business_id": "anon_biz"}
    }, tenant_id="anon_biz")
    store.add_event({
        "event_id": "ev-anon-2",
        "event_name": "google_maps_redirect",
        "session_id": None,
        "timestamp": now - 20,
        "metadata": {"business_id": "anon_biz"}
    }, tenant_id="anon_biz")
    store.add_event({
        "event_id": "ev-anon-3",
        "event_name": "google_maps_redirect",
        "session_id": "",
        "timestamp": now - 15,
        "metadata": {"business_id": "anon_biz"}
    }, tenant_id="anon_biz")
    store.add_event({
        "event_id": "ev-anon-4",
        "event_name": "google_maps_redirect",
        "session_id": f"local-{int(time.time()*1000)}",
        "timestamp": now - 10,
        "metadata": {"business_id": "anon_biz"}
    }, tenant_id="anon_biz")
    store.add_event({
        "event_id": "ev-anon-5",
        "event_name": "google_maps_redirect",
        "session_id": "not-a-valid-uuid-1234",
        "timestamp": now - 8,
        "metadata": {"business_id": "anon_biz"}
    }, tenant_id="anon_biz")

    # One genuine UUIDv4 session
    genuine_uuid = str(uuid.uuid4())
    store.add_event({
        "event_id": "ev-real-1",
        "event_name": "google_maps_redirect",
        "session_id": genuine_uuid,
        "timestamp": now - 5,
        "metadata": {"business_id": "anon_biz"}
    }, tenant_id="anon_biz")

    summary = service.get_analytics_summary(business_id="anon_biz")
    # Only the genuine UUIDv4 session is counted
    assert summary["google_clicks"] == 1


def test_two_tenants_similar_event_histories(tmp_path, monkeypatch):
    """Two tenants with multiple distinct sessions remain strictly isolated."""
    db_file = tmp_path / "two_tenants_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    now = time.time()
    # Tenant Alpha: 3 unique sessions
    for i in range(3):
        store.add_event({
            "event_id": f"ev-alpha-{i}",
            "event_name": "google_maps_redirect",
            "session_id": str(uuid.uuid4()),
            "timestamp": now - i * 10,
            "metadata": {"business_id": "alpha_tenant"}
        }, tenant_id="alpha_tenant")

    # Tenant Beta: 2 unique sessions
    for i in range(2):
        store.add_event({
            "event_id": f"ev-beta-{i}",
            "event_name": "google_maps_redirect",
            "session_id": str(uuid.uuid4()),
            "timestamp": now - i * 10,
            "metadata": {"business_id": "beta_tenant"}
        }, tenant_id="beta_tenant")

    sum_alpha = service.get_analytics_summary(business_id="alpha_tenant")
    sum_beta = service.get_analytics_summary(business_id="beta_tenant")

    assert sum_alpha["google_clicks"] == 3
    assert sum_beta["google_clicks"] == 2


def test_reporting_period_boundaries(tmp_path, monkeypatch):
    """Events outside the requested reporting period are strictly excluded."""
    db_file = tmp_path / "boundary_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    service = ReviewService()
    service._store = store

    t_center = 1700000000.0  # reference time

    # Event 1: Before window (excluded)
    store.add_event({
        "event_id": "ev-before",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": t_center - 200,
        "metadata": {"business_id": "bound_biz"}
    }, tenant_id="bound_biz")

    # Event 2: Inside window
    store.add_event({
        "event_id": "ev-in-1",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": t_center - 50,
        "metadata": {"business_id": "bound_biz"}
    }, tenant_id="bound_biz")

    # Event 3: Inside window
    store.add_event({
        "event_id": "ev-in-2",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": t_center + 50,
        "metadata": {"business_id": "bound_biz"}
    }, tenant_id="bound_biz")

    # Event 4: After window (excluded)
    store.add_event({
        "event_id": "ev-after",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": t_center + 200,
        "metadata": {"business_id": "bound_biz"}
    }, tenant_id="bound_biz")

    # Query with window [t_center - 100, t_center + 100]
    summary_window = service.get_analytics_summary(
        business_id="bound_biz",
        start_timestamp=t_center - 100,
        end_timestamp=t_center + 100
    )
    assert summary_window["google_clicks"] == 2


# =====================================================================
# 7. PHASE A5.0.3 ANALYTICS API & SESSION VALIDATION TESTS
# =====================================================================

def _setup_test_tenant(store, tenant_id: str, email: str = None, role: str = "staff", entitlements: list = None, timezone: str = None):
    entitlements = entitlements or ["review_manager"]
    store.upsert_tenant({
        "id": tenant_id,
        "business_name": f"{tenant_id.title()} Business",
        "status": "active",
        "category": "Restaurant",
        "entitlements": entitlements,
    })
    store.upsert_business_profile(tenant_id, {"display_name": f"{tenant_id.title()} Business"})
    if timezone:
        store.update_shared_business_profile(tenant_id, {"timezone": timezone})
    if email:
        user = store.create_user(
            email=email,
            password_hash=hash_password("pass123"),
            display_name=email.split("@")[0].title(),
            is_active=1,
        )
        store.add_membership(user["id"], tenant_id, role=role)
        raw_token = generate_session_token()
        hashed = hash_token(raw_token)
        now = time.time()
        with store._connect() as db:
            db.execute(
                "INSERT INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (hashed, user["id"], tenant_id, now, now + SESSION_TTL_SECONDS)
            )
        return raw_token
    return None


def test_event_ingestion_valid_uuidv4(tmp_path, monkeypatch):
    """A valid UUIDv4 session belonging to the tenant is ingested and marked verified."""
    db_file = tmp_path / "valid_uuid_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "valid_tenant")
    
    sess_id = str(uuid.uuid4())
    review_service.record_session(
        session_id=sess_id,
        business_id="valid_tenant",
        traffic_source="customer"
    )
    
    res = client.post("/api/reviews/events", json={
        "session_id": sess_id,
        "event_name": "google_maps_redirect",
        "metadata": {"business_id": "valid_tenant"}
    })
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "recorded"
    assert body["session_verified"] is True
    assert body["traffic_source"] == "customer"


def test_event_ingestion_malformed_uuid_marked_unverified(tmp_path, monkeypatch):
    """Malformed session IDs (e.g. frontend fallback local-...) are ingested as unverified telemetry and excluded from conversion metrics."""
    db_file = tmp_path / "malformed_uuid_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "fallback_tenant")
    
    # Send event with fallback ID
    res = client.post("/api/reviews/events", json={
        "session_id": f"local-{int(time.time()*1000)}",
        "event_name": "google_maps_redirect",
        "metadata": {"business_id": "fallback_tenant"}
    })
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "recorded"
    assert body["session_verified"] is False
    
    # Verify in analytics that fallback session is not counted as a conversion
    summary = review_service.get_analytics_summary(business_id="fallback_tenant")
    assert summary["google_clicks"] == 0


def test_event_ingestion_cross_tenant_uuid_rejected(tmp_path, monkeypatch):
    """Events attempting cross-tenant session borrowing are rejected with HTTP 403 Forbidden."""
    db_file = tmp_path / "cross_tenant_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "tenant_victim")
    _setup_test_tenant(store, "tenant_attacker")
    
    # Session legitimately created for Victim
    victim_session = str(uuid.uuid4())
    review_service.record_session(
        session_id=victim_session,
        business_id="tenant_victim",
        traffic_source="customer"
    )
    
    # Attacker tries to submit events using Victim's session ID
    res = client.post("/api/reviews/events", json={
        "session_id": victim_session,
        "event_name": "google_maps_redirect",
        "metadata": {"business_id": "tenant_attacker"}
    })
    assert res.status_code == 403
    assert "Cross-tenant session borrowing detected" in res.json().get("detail", "")


def test_event_ingestion_unknown_uuid(tmp_path, monkeypatch):
    """Unknown UUIDv4 (not in server active sessions) is ingested as unverified customer telemetry without cross-tenant conflict."""
    db_file = tmp_path / "unknown_uuid_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "unknown_tenant")
    
    random_uuid = str(uuid.uuid4())
    res = client.post("/api/reviews/events", json={
        "session_id": random_uuid,
        "event_name": "review_ideas_generated",
        "metadata": {"business_id": "unknown_tenant", "rating": 5}
    })
    assert res.status_code == 200
    assert res.json()["status"] == "recorded"
    assert res.json()["session_verified"] is False


def test_event_ingestion_anonymous_event(tmp_path, monkeypatch):
    """Anonymous events are accepted, preserving diagnostic telemetry without counting toward conversion metrics."""
    db_file = tmp_path / "anon_ingest_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "anon_ingest_biz")
    
    res = client.post("/api/reviews/events", json={
        "session_id": "anonymous",
        "event_name": "google_maps_redirect",
        "metadata": {"business_id": "anon_ingest_biz"}
    })
    assert res.status_code == 200
    assert res.json()["session_verified"] is False
    
    summary = review_service.get_analytics_summary(business_id="anon_ingest_biz")
    assert summary["google_clicks"] == 0


def test_analytics_api_lifetime_aggregation(tmp_path, monkeypatch):
    """GET /api/reviews/analytics without start_date and end_date preserves lifetime aggregation."""
    db_file = tmp_path / "lifetime_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "lifetime_biz", email="lifetime_owner@example.com")
    
    # Seed events across wide time range
    t_now = time.time()
    store.add_event({
        "event_id": "ev-old",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": t_now - (365 * 86400),
        "metadata": {"business_id": "lifetime_biz"}
    }, tenant_id="lifetime_biz")
    store.add_event({
        "event_id": "ev-recent",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": t_now - 100,
        "metadata": {"business_id": "lifetime_biz"}
    }, tenant_id="lifetime_biz")
    
    # Query without date filters
    res = client.get("/api/reviews/analytics?business_id=lifetime_biz", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["google_clicks"] == 2


def test_analytics_api_single_day_range(tmp_path, monkeypatch):
    """GET /api/reviews/analytics with start_date == end_date queries exactly that local day."""
    db_file = tmp_path / "single_day_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "singleday_biz", email="singleday@example.com")
    
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    d = date(2026, 5, 10)
    ts_target_day_noon = datetime.combine(d, dtime(12, 0), tzinfo=tz).timestamp()
    ts_prev_day_night = datetime.combine(d - timedelta(days=1), dtime(23, 30), tzinfo=tz).timestamp()
    ts_next_day_morning = datetime.combine(d + timedelta(days=1), dtime(8, 0), tzinfo=tz).timestamp()
    
    store.add_event({
        "event_id": "ev-prev",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_prev_day_night,
        "metadata": {"business_id": "singleday_biz"}
    }, tenant_id="singleday_biz")
    store.add_event({
        "event_id": "ev-target",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_target_day_noon,
        "metadata": {"business_id": "singleday_biz"}
    }, tenant_id="singleday_biz")
    store.add_event({
        "event_id": "ev-next",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_next_day_morning,
        "metadata": {"business_id": "singleday_biz"}
    }, tenant_id="singleday_biz")
    
    res = client.get(
        "/api/reviews/analytics?business_id=singleday_biz&start_date=2026-05-10&end_date=2026-05-10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["google_clicks"] == 1


def test_analytics_api_multi_day_range(tmp_path, monkeypatch):
    """GET /api/reviews/analytics with multi-day range covers the full interval."""
    db_file = tmp_path / "multi_day_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "multiday_biz", email="multiday@example.com")
    
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    ts_may1 = datetime.combine(date(2026, 5, 1), dtime(10, 0), tzinfo=tz).timestamp()
    ts_may5 = datetime.combine(date(2026, 5, 5), dtime(14, 0), tzinfo=tz).timestamp()
    ts_may10 = datetime.combine(date(2026, 5, 10), dtime(16, 0), tzinfo=tz).timestamp()
    
    store.add_event({
        "event_id": "ev-1",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_may1,
        "metadata": {"business_id": "multiday_biz"}
    }, tenant_id="multiday_biz")
    store.add_event({
        "event_id": "ev-2",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_may5,
        "metadata": {"business_id": "multiday_biz"}
    }, tenant_id="multiday_biz")
    store.add_event({
        "event_id": "ev-3",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_may10,
        "metadata": {"business_id": "multiday_biz"}
    }, tenant_id="multiday_biz")
    
    # Window 2026-05-01 to 2026-05-07 should capture May 1 and May 5, but exclude May 10
    res = client.get(
        "/api/reviews/analytics?business_id=multiday_biz&start_date=2026-05-01&end_date=2026-05-07",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["google_clicks"] == 2


def test_analytics_api_end_date_before_start_date_rejected(tmp_path, monkeypatch):
    """end_date earlier than start_date is rejected with HTTP 422."""
    db_file = tmp_path / "order_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "order_biz", email="order@example.com")
    
    res = client.get(
        "/api/reviews/analytics?business_id=order_biz&start_date=2026-05-10&end_date=2026-05-05",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 422
    assert "cannot be earlier than start_date" in res.json().get("detail", "")


def test_analytics_api_malformed_date_format_rejected(tmp_path, monkeypatch):
    """Malformed date formats or impossible dates are rejected with HTTP 422."""
    db_file = tmp_path / "malformed_date_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "date_biz", email="date@example.com")
    
    # Slash format
    assert client.get("/api/reviews/analytics?business_id=date_biz&start_date=2026/05/01", headers={"Authorization": f"Bearer {token}"}).status_code == 422
    # Non-date string
    assert client.get("/api/reviews/analytics?business_id=date_biz&start_date=invalid-date", headers={"Authorization": f"Bearer {token}"}).status_code == 422
    # Invalid calendar date (Feb 31)
    assert client.get("/api/reviews/analytics?business_id=date_biz&start_date=2026-02-31", headers={"Authorization": f"Bearer {token}"}).status_code == 422


def test_analytics_api_timezone_utc_conversion(tmp_path, monkeypatch):
    """Tenant configured timezone correctly shifts UTC boundary timestamps."""
    db_file = tmp_path / "tz_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "ny_biz", email="ny@example.com", timezone="America/New_York")
    
    # An event at 2026-05-01 02:00:00 UTC
    # In America/New_York (EDT, UTC-4), this is 2026-04-30 22:00:00 (April 30, NOT May 1!)
    # In Asia/Kolkata (IST, UTC+5:30), this is 2026-05-01 07:30:00 (May 1)
    dt_utc = datetime(2026, 5, 1, 2, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    store.add_event({
        "event_id": "ev-tz-edge",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": dt_utc.timestamp(),
        "metadata": {"business_id": "ny_biz"}
    }, tenant_id="ny_biz")
    
    # Query for May 1 local NY time (2026-05-01): event at 02:00 UTC was on April 30 NY time, so should be 0!
    res_may1 = client.get(
        "/api/reviews/analytics?business_id=ny_biz&start_date=2026-05-01&end_date=2026-05-01",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_may1.status_code == 200
    assert res_may1.json()["google_clicks"] == 0
    
    # Query for April 30 local NY time (2026-04-30): event SHOULD be captured!
    res_apr30 = client.get(
        "/api/reviews/analytics?business_id=ny_biz&start_date=2026-04-30&end_date=2026-04-30",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_apr30.status_code == 200
    assert res_apr30.json()["google_clicks"] == 1


def test_analytics_api_inclusive_start_exclusive_end(tmp_path, monkeypatch):
    """Start boundary is strictly inclusive (00:00:00) and end boundary is strictly exclusive (start of next day 00:00:00)."""
    db_file = tmp_path / "boundary_exact_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "boundary_tenant", email="boundary@example.com")
    
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    d_start = date(2026, 6, 1)
    d_end = date(2026, 6, 2)
    
    # Exact start midnight (inclusive -> MUST be included)
    ts_start_exact = datetime.combine(d_start, dtime.min, tzinfo=tz).timestamp()
    
    # 1 second before next day midnight (MUST be included)
    ts_end_inclusive = datetime.combine(d_end + timedelta(days=1), dtime.min, tzinfo=tz).timestamp() - 1.0
    
    # Exact start of day 3 midnight (exclusive boundary -> MUST be excluded)
    ts_end_exclusive = datetime.combine(d_end + timedelta(days=1), dtime.min, tzinfo=tz).timestamp()
    
    store.add_event({
        "event_id": "ev-start-exact",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_start_exact,
        "metadata": {"business_id": "boundary_tenant"}
    }, tenant_id="boundary_tenant")
    store.add_event({
        "event_id": "ev-end-in",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_end_inclusive,
        "metadata": {"business_id": "boundary_tenant"}
    }, tenant_id="boundary_tenant")
    store.add_event({
        "event_id": "ev-end-excl",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_end_exclusive,
        "metadata": {"business_id": "boundary_tenant"}
    }, tenant_id="boundary_tenant")
    
    res = client.get(
        "/api/reviews/analytics?business_id=boundary_tenant&start_date=2026-06-01&end_date=2026-06-02",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    # Exactly 2 events included: ev-start-exact and ev-end-in. ev-end-excl must be excluded!
    assert res.json()["google_clicks"] == 2


def test_analytics_api_tenant_isolation_with_date_filters(tmp_path, monkeypatch):
    """Tenant A date-filtered analytics query never leaks Tenant B events with identical timestamps."""
    db_file = tmp_path / "date_iso_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store
    
    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "iso_biz_a", email="user_a@example.com")
    _setup_test_tenant(store, "iso_biz_b")
    
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    ts_event = datetime.combine(date(2026, 7, 1), dtime(15, 0), tzinfo=tz).timestamp()
    
    store.add_event({
        "event_id": "ev-a",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_event,
        "metadata": {"business_id": "iso_biz_a"}
    }, tenant_id="iso_biz_a")
    store.add_event({
        "event_id": "ev-b",
        "event_name": "google_maps_redirect",
        "session_id": str(uuid.uuid4()),
        "timestamp": ts_event,
        "metadata": {"business_id": "iso_biz_b"}
    }, tenant_id="iso_biz_b")
    
    res_a = client.get(
        "/api/reviews/analytics?business_id=iso_biz_a&start_date=2026-07-01&end_date=2026-07-01",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_a.status_code == 200
    assert res_a.json()["google_clicks"] == 1
    
    # User A attempting to query Tenant B -> 403 Forbidden
    res_forbidden = client.get(
        "/api/reviews/analytics?business_id=iso_biz_b&start_date=2026-07-01&end_date=2026-07-01",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_forbidden.status_code == 403


# =====================================================================
# 9. PHASE A5.0.5 — PERSISTENT SESSIONS, CONVERSION FUNNEL & OWNER UI
# =====================================================================

def test_persistent_session_creation_and_cross_worker_lookup(tmp_path, monkeypatch):
    """
    Persistent sessions stored in SQLite review_sessions are visible across separate
    worker/process instances with disjoint in-memory state.
    """
    db_file = tmp_path / "cross_worker_session.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()

    # Worker 1 creates review session
    store_worker1 = ReviewStore()
    _setup_test_tenant(store_worker1, "worker_cafe")
    service_worker1 = ReviewService()
    service_worker1._store = store_worker1

    sid = str(uuid.uuid4())
    service_worker1.record_session(
        session_id=sid,
        business_id="worker_cafe",
        traffic_source="customer",
        table_number="T12",
        dining_type="dine_in",
        ttl_seconds=3600.0,
    )

    # Verify Worker 1 has it
    info1 = service_worker1.get_session_info(sid)
    assert info1 is not None
    assert info1["business_id"] == "worker_cafe"
    assert info1["table_number"] == "T12"

    # Worker 2: Fresh instance, empty in-memory cache, shares SQLite database
    store_worker2 = ReviewStore()
    service_worker2 = ReviewService()
    service_worker2._store = store_worker2
    assert sid not in service_worker2._active_sessions

    # Worker 2 looks up session -> must query SQLite and populate cache
    info2 = service_worker2.get_session_info(sid)
    assert info2 is not None
    assert info2["session_id"] == sid
    assert info2["business_id"] == "worker_cafe"
    assert info2["traffic_source"] == "customer"
    assert info2["table_number"] == "T12"
    assert info2["dining_type"] == "dine_in"
    assert info2["expires_at"] > time.time()
    assert sid in service_worker2._active_sessions


def test_cross_tenant_session_borrowing_rejection(tmp_path, monkeypatch):
    """
    Attempting to ingest analytics events using a valid session ID belonging to another
    tenant must be rejected with HTTP 403 Forbidden.
    """
    db_file = tmp_path / "cross_tenant_borrow.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()

    _setup_test_tenant(store, "tenant_alpha")
    _setup_test_tenant(store, "tenant_beta")

    # Session created for Tenant Alpha
    sid_alpha = str(uuid.uuid4())
    review_service.record_session(
        session_id=sid_alpha,
        business_id="tenant_alpha",
        traffic_source="customer",
        table_number="T1",
    )

    # Event sent claiming to be for Tenant Beta with Alpha's session ID -> 403 Forbidden
    res = client.post(
        "/api/reviews/events",
        json={
            "event_name": "review_generation_completed",
            "session_id": sid_alpha,
            "metadata": {
                "business_id": "tenant_beta",
                "rating": 5,
            }
        }
    )
    assert res.status_code == 403
    assert "Cross-tenant session borrowing detected" in res.json()["detail"]


def test_unknown_uuid_accepted_for_raw_telemetry_but_excluded_from_conversion(tmp_path, monkeypatch):
    """
    An unknown random UUIDv4 (not registered via server session) is ingested as unverified
    telemetry, but is strictly excluded from conversion rate calculation.
    """
    db_file = tmp_path / "unknown_uuid_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "telemetry_biz")

    unknown_sid = str(uuid.uuid4())

    # Raw telemetry event ingestion succeeds
    res_gen = client.post(
        "/api/reviews/events",
        json={
            "event_name": "review_generation_completed",
            "session_id": unknown_sid,
            "metadata": {"business_id": "telemetry_biz", "rating": 5}
        }
    )
    assert res_gen.status_code == 200

    res_redir = client.post(
        "/api/reviews/events",
        json={
            "event_name": "google_maps_redirect",
            "session_id": unknown_sid,
            "metadata": {"business_id": "telemetry_biz"}
        }
    )
    assert res_redir.status_code == 200

    # Analytics calculation: unknown UUID is excluded from conversion denominator & numerator
    summary = review_service.get_analytics_summary(business_id="telemetry_biz")
    assert summary["total_generations"] == 1
    assert summary["conversion_rate_percent"] == 0.0
    assert summary.get("eligible_generation_sessions", 0) == 0


def test_anonymous_and_unverified_sessions_excluded_from_conversion(tmp_path, monkeypatch):
    """
    Events with 'anonymous' or 'unverified' session IDs are excluded from conversion.
    """
    db_file = tmp_path / "anon_unverified_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "anon_biz")

    client.post("/api/reviews/events", json={
        "event_name": "review_generation_completed",
        "session_id": "anonymous",
        "metadata": {"business_id": "anon_biz", "rating": 5}
    })
    client.post("/api/reviews/events", json={
        "event_name": "google_maps_redirect",
        "session_id": "anonymous",
        "metadata": {"business_id": "anon_biz"}
    })
    client.post("/api/reviews/events", json={
        "event_name": "review_generation_completed",
        "session_id": "unverified",
        "metadata": {"business_id": "anon_biz", "rating": 4}
    })
    client.post("/api/reviews/events", json={
        "event_name": "google_maps_redirect",
        "session_id": "unverified",
        "metadata": {"business_id": "anon_biz"}
    })

    summary = review_service.get_analytics_summary(business_id="anon_biz")
    assert summary["conversion_rate_percent"] == 0.0
    assert summary.get("eligible_generation_sessions", 0) == 0


def test_expired_session_handling(tmp_path, monkeypatch):
    """
    Expired review sessions return None on lookup and are excluded from conversion funnel.
    """
    db_file = tmp_path / "expired_session_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "expired_biz")

    # Session created with past expiry (-10 seconds)
    sid = str(uuid.uuid4())
    store.create_review_session(
        session_id=sid,
        tenant_id="expired_biz",
        ttl_seconds=-10.0,
    )

    # get_session_info with expiry check returns None
    assert review_service.get_session_info(sid, check_expiry=True) is None

    # Ingestion treats it as unverified
    res = client.post(
        "/api/reviews/events",
        json={
            "event_name": "review_generation_completed",
            "session_id": sid,
            "metadata": {"business_id": "expired_biz", "rating": 5}
        }
    )
    assert res.status_code == 200

    # Analytics calculation excludes expired session from conversion
    summary = review_service.get_analytics_summary(business_id="expired_biz")
    assert summary["conversion_rate_percent"] == 0.0
    assert summary.get("eligible_generation_sessions", 0) == 0


def test_conversion_funnel_generation_followed_by_handoff(tmp_path, monkeypatch):
    """
    Valid session where generation is followed by a Google handoff (handoff_ts >= gen_ts)
    correctly yields a 100.0% conversion rate.
    """
    db_file = tmp_path / "conv_success_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "conv_biz")

    sid = str(uuid.uuid4())
    review_service.record_session(session_id=sid, business_id="conv_biz")

    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid,
        "timestamp": t0,
        "metadata": {"business_id": "conv_biz"}
    }, tenant_id="conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid,
        "timestamp": t0 + 10.0,
        "metadata": {"business_id": "conv_biz"}
    }, tenant_id="conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid,
        "timestamp": t0 + 20.0,
        "metadata": {"business_id": "conv_biz"}
    }, tenant_id="conv_biz")

    summary = review_service.get_analytics_summary(business_id="conv_biz")
    assert summary["conversion_rate_percent"] == 100.0
    assert summary.get("eligible_generation_sessions") == 1
    assert summary.get("eligible_handoff_sessions") == 1


def test_conversion_funnel_handoff_before_generation_excluded(tmp_path, monkeypatch):
    """
    Google handoff occurring BEFORE review generation in the same session does not
    count as a successful completion of the review generation funnel.
    """
    db_file = tmp_path / "conv_premature_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "premature_biz")

    sid = str(uuid.uuid4())
    review_service.record_session(session_id=sid, business_id="premature_biz")

    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid,
        "timestamp": t0,
        "metadata": {"business_id": "premature_biz"}
    }, tenant_id="premature_biz")
    # Redirect at t0 + 5s (BEFORE generation)
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid,
        "timestamp": t0 + 5.0,
        "metadata": {"business_id": "premature_biz"}
    }, tenant_id="premature_biz")
    # Generation at t0 + 20s
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid,
        "timestamp": t0 + 20.0,
        "metadata": {"business_id": "premature_biz"}
    }, tenant_id="premature_biz")

    summary = review_service.get_analytics_summary(business_id="premature_biz")
    assert summary["eligible_generation_sessions"] == 1
    assert summary["eligible_handoff_sessions"] == 0
    assert summary["conversion_rate_percent"] == 0.0


def test_conversion_funnel_multiple_generations_and_redirects_deduplicated(tmp_path, monkeypatch):
    """
    Multiple generations and multiple redirects within the same session count exactly once
    in the denominator and numerator.
    """
    db_file = tmp_path / "conv_multi_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "multi_biz")

    sid = str(uuid.uuid4())
    review_service.record_session(session_id=sid, business_id="multi_biz")

    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid,
        "timestamp": t0,
        "metadata": {"business_id": "multi_biz"}
    }, tenant_id="multi_biz")
    # Two completed generations
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid,
        "timestamp": t0 + 10.0,
        "metadata": {"business_id": "multi_biz"}
    }, tenant_id="multi_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid,
        "timestamp": t0 + 15.0,
        "metadata": {"business_id": "multi_biz"}
    }, tenant_id="multi_biz")
    # Three redirects
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid,
        "timestamp": t0 + 20.0,
        "metadata": {"business_id": "multi_biz"}
    }, tenant_id="multi_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_review_link_opened",
        "session_id": sid,
        "timestamp": t0 + 25.0,
        "metadata": {"business_id": "multi_biz"}
    }, tenant_id="multi_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_review_link_clicked",
        "session_id": sid,
        "timestamp": t0 + 30.0,
        "metadata": {"business_id": "multi_biz"}
    }, tenant_id="multi_biz")

    summary = review_service.get_analytics_summary(business_id="multi_biz")
    assert summary["eligible_generation_sessions"] == 1
    assert summary["eligible_handoff_sessions"] == 1
    assert summary["conversion_rate_percent"] == 100.0


def test_conversion_funnel_zero_generation_safe(tmp_path, monkeypatch):
    """
    Zero review generations returns 0.0% conversion rate without division by zero.
    """
    db_file = tmp_path / "conv_zero_gen.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "zero_biz")

    summary = review_service.get_analytics_summary(business_id="zero_biz")
    assert summary["eligible_generation_sessions"] == 0
    assert summary["eligible_handoff_sessions"] == 0
    assert summary["conversion_rate_percent"] == 0.0


def test_conversion_funnel_with_date_range_filtering(tmp_path, monkeypatch):
    """
    Conversion rate calculation correctly respects date range filters.
    """
    db_file = tmp_path / "conv_date_range.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    token = _setup_test_tenant(store, "date_conv_biz", email="conv_owner@example.com")

    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    # Day 1: 2026-08-01
    d1_noon = datetime.combine(date(2026, 8, 1), dtime(12, 0), tzinfo=tz).timestamp()
    sid1 = str(uuid.uuid4())
    store.create_review_session(session_id=sid1, tenant_id="date_conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid1,
        "timestamp": d1_noon,
        "metadata": {"business_id": "date_conv_biz"}
    }, tenant_id="date_conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid1,
        "timestamp": d1_noon + 10.0,
        "metadata": {"business_id": "date_conv_biz"}
    }, tenant_id="date_conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid1,
        "timestamp": d1_noon + 20.0,
        "metadata": {"business_id": "date_conv_biz"}
    }, tenant_id="date_conv_biz")

    # Day 3: 2026-08-03 (Generation only, no redirect)
    d3_noon = datetime.combine(date(2026, 8, 3), dtime(12, 0), tzinfo=tz).timestamp()
    sid3 = str(uuid.uuid4())
    store.create_review_session(session_id=sid3, tenant_id="date_conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid3,
        "timestamp": d3_noon,
        "metadata": {"business_id": "date_conv_biz"}
    }, tenant_id="date_conv_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid3,
        "timestamp": d3_noon + 10.0,
        "metadata": {"business_id": "date_conv_biz"}
    }, tenant_id="date_conv_biz")

    # Query Day 1 only (2026-08-01): 1 generation, 1 handoff -> 100.0%
    res1 = client.get(
        "/api/reviews/analytics?business_id=date_conv_biz&start_date=2026-08-01&end_date=2026-08-01",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["conversion_rate_percent"] == 100.0

    # Query Day 3 only (2026-08-03): 1 generation, 0 handoffs -> 0.0%
    res3 = client.get(
        "/api/reviews/analytics?business_id=date_conv_biz&start_date=2026-08-03&end_date=2026-08-03",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["conversion_rate_percent"] == 0.0

    # Query Day 1 to Day 3: 2 generations, 1 handoff -> 50.0%
    res_all = client.get(
        "/api/reviews/analytics?business_id=date_conv_biz&start_date=2026-08-01&end_date=2026-08-03",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["conversion_rate_percent"] == 50.0


def test_multi_tenant_conversion_funnel_isolation(tmp_path, monkeypatch):
    """
    Tenant A's conversion sessions never leak into or influence Tenant B's conversion funnel.
    """
    db_file = tmp_path / "conv_isolation_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()

    token_a = _setup_test_tenant(store, "conv_iso_a", email="iso_a@example.com")
    token_b = _setup_test_tenant(store, "conv_iso_b", email="iso_b@example.com")

    # Tenant A: 1 full conversion
    sid_a = str(uuid.uuid4())
    store.create_review_session(session_id=sid_a, tenant_id="conv_iso_a")
    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid_a,
        "timestamp": t0,
        "metadata": {"business_id": "conv_iso_a"}
    }, tenant_id="conv_iso_a")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid_a,
        "timestamp": t0 + 10.0,
        "metadata": {"business_id": "conv_iso_a"}
    }, tenant_id="conv_iso_a")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid_a,
        "timestamp": t0 + 20.0,
        "metadata": {"business_id": "conv_iso_a"}
    }, tenant_id="conv_iso_a")

    # Tenant B: No activity
    res_a = client.get(
        "/api/reviews/analytics?business_id=conv_iso_a",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200
    assert res_a.json()["conversion_rate_percent"] == 100.0

    res_b = client.get(
        "/api/reviews/analytics?business_id=conv_iso_b",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b.status_code == 200
    assert res_b.json()["conversion_rate_percent"] == 0.0


# =====================================================================
# 10. PHASE A5.0.7 — FUNNEL DEFINITION & EVENT ORDERING CORRECTIONS
# =====================================================================

def test_ideas_generated_excluded_from_funnel_denominator(tmp_path, monkeypatch):
    """
    A session where the user only views/generates suggestion ideas (review_ideas_generated)
    without completing a full draft (review_generation_completed) is NOT included in the
    conversion funnel denominator.
    """
    db_file = tmp_path / "ideas_excluded_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "ideas_only_biz")

    sid = str(uuid.uuid4())
    store.create_review_session(session_id=sid, tenant_id="ideas_only_biz")

    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid,
        "timestamp": t0,
        "metadata": {"business_id": "ideas_only_biz"}
    }, tenant_id="ideas_only_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_ideas_generated",
        "session_id": sid,
        "timestamp": t0 + 10.0,
        "metadata": {"business_id": "ideas_only_biz"}
    }, tenant_id="ideas_only_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid,
        "timestamp": t0 + 20.0,
        "metadata": {"business_id": "ideas_only_biz"}
    }, tenant_id="ideas_only_biz")

    summary = review_service.get_analytics_summary(business_id="ideas_only_biz")
    # review_ideas_generated does NOT qualify as completed generation
    assert summary["eligible_generation_sessions"] == 0
    assert summary["eligible_handoff_sessions"] == 0
    assert summary["conversion_rate_percent"] == 0.0


def test_review_generation_completed_qualifies_for_denominator(tmp_path, monkeypatch):
    """
    Only review_generation_completed qualifies as a completed review draft in the
    conversion denominator.
    """
    db_file = tmp_path / "gen_completed_qualifies.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "completed_gen_biz")

    sid = str(uuid.uuid4())
    store.create_review_session(session_id=sid, tenant_id="completed_gen_biz")

    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid,
        "timestamp": t0,
        "metadata": {"business_id": "completed_gen_biz"}
    }, tenant_id="completed_gen_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid,
        "timestamp": t0 + 10.0,
        "metadata": {"business_id": "completed_gen_biz"}
    }, tenant_id="completed_gen_biz")

    summary = review_service.get_analytics_summary(business_id="completed_gen_biz")
    assert summary["eligible_generation_sessions"] == 1
    assert summary["eligible_handoff_sessions"] == 0
    assert summary["conversion_rate_percent"] == 0.0


def test_historical_aliases_do_not_inflate_canonical_conversions(tmp_path, monkeypatch):
    """
    1. A session with only historical aliases (e.g., google_review_link_opened) does not receive
       conversion attribution in the new canonical funnel.
    2. A session with canonical google_maps_redirect alongside legacy aliases counts exactly once.
    """
    db_file = tmp_path / "legacy_alias_conv_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()
    from backend.app.api.routes import review_service, get_store

    store = get_store()
    review_service._store = store
    review_service._active_sessions.clear()
    review_service._dedup_cache.clear()
    review_service._rate_limits.clear()
    _setup_test_tenant(store, "alias_biz")

    # Session 1: completed generation followed only by legacy alias -> 0 conversions in canonical funnel
    sid1 = str(uuid.uuid4())
    store.create_review_session(session_id=sid1, tenant_id="alias_biz")
    t0 = time.time()
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid1,
        "timestamp": t0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid1,
        "timestamp": t0 + 10.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_review_link_opened",
        "session_id": sid1,
        "timestamp": t0 + 20.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")

    summary1 = review_service.get_analytics_summary(business_id="alias_biz")
    assert summary1["eligible_generation_sessions"] == 1
    assert summary1["eligible_handoff_sessions"] == 0
    assert summary1["conversion_rate_percent"] == 0.0

    # Session 2: completed generation followed by canonical google_maps_redirect AND legacy aliases
    sid2 = str(uuid.uuid4())
    store.create_review_session(session_id=sid2, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "session_created",
        "session_id": sid2,
        "timestamp": t0 + 30.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "review_generation_completed",
        "session_id": sid2,
        "timestamp": t0 + 40.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_maps_redirect",
        "session_id": sid2,
        "timestamp": t0 + 50.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_review_link_opened",
        "session_id": sid2,
        "timestamp": t0 + 55.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")
    store.add_event({
        "event_id": f"ev-{uuid.uuid4().hex[:6]}",
        "event_name": "google_review_link_clicked",
        "session_id": sid2,
        "timestamp": t0 + 60.0,
        "metadata": {"business_id": "alias_biz"}
    }, tenant_id="alias_biz")

    summary2 = review_service.get_analytics_summary(business_id="alias_biz")
    # Denominator: 2 sessions (sid1 and sid2)
    assert summary2["eligible_generation_sessions"] == 2
    # Numerator: exactly 1 session (sid2 with canonical google_maps_redirect); sid1 has no canonical redirect
    assert summary2["eligible_handoff_sessions"] == 1
    # Conversion rate: 1 / 2 = 50.0%
    assert summary2["conversion_rate_percent"] == 50.0


def test_deterministic_event_ordering_same_timestamp(tmp_path, monkeypatch):
    """
    When multiple analytics events share the exact same created_at timestamp,
    secondary ordering by rowid DESC guarantees deterministic insertion-order retrieval.
    """
    db_file = tmp_path / "same_ts_order_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    _stores.clear()

    store = ReviewStore()
    _setup_test_tenant(store, "order_biz")

    fixed_ts = 1700000000.0

    # Insert 4 events in sequence with the EXACT same timestamp
    ev_ids = ["ev-first", "ev-second", "ev-third", "ev-fourth"]
    for eid in ev_ids:
        store.add_event({
            "event_id": eid,
            "event_name": "test_event",
            "session_id": "sess-order",
            "timestamp": fixed_ts,
            "metadata": {"business_id": "order_biz", "seq": eid}
        }, tenant_id="order_biz")

    # list_events returns reversed(rows) ordered by (created_at DESC, rowid DESC)
    # This means the returned list preserves exact chronological insertion order: first, second, third, fourth
    events = store.list_events(business_id="order_biz")
    retrieved_ids = [e["event_id"] for e in events]
    assert retrieved_ids == ev_ids, f"Expected {ev_ids}, got {retrieved_ids}"


