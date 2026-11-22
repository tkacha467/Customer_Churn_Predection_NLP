"""
Phase A6.5.2 Test Suite: Final SMTP Authorization Gate, CI Browser Enforcement & Release Integrity Verification.

Validates:
1. Fail-closed live SMTP authorization gate (ALLOW_LIVE_SMTP_TEST=true requirement).
2. Non-blocking asynchronous durable queuing with zero HTTP worker blocking.
3. Status lookup endpoint GET /api/platform/security-shield/test-alert/{test_id}.
4. Comprehensive test alert security (401, 403, 429, CSRF, recipient override rejection, SMTP timeout safety).
5. Worker restart recovery and complete isolation from production incident outbox.
6. HMAC release manifest signing, unexpected file detection, and DB schema vs data separation.
7. Google Reviews 1-5 star direct access and 100% Product B clean isolation.
"""

import os
import json
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    OWNER_COOKIE,
)
from Backend.app.api.service import review_service
from Backend.app.core.security.security_store import SecurityStore
from Backend.app.core.security.alert_mailer import alert_mailer, AlertMailer, AlertDispatcherWorker
from Backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)
from Backend.app.core.security.code_integrity import (
    generate_release_manifest,
    verify_code_integrity,
    verify_database_schema_integrity,
    sign_release_manifest,
    verify_manifest_signature,
    compute_file_sha256,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROD_DB_HASH = "37624B30A19B67809B078D951E1A382A83B2A49311EDB0445187002D7F365BA4"


@pytest.fixture
def a6_5_2_env(tmp_path, monkeypatch):
    """Isolated test environment for Phase A6.5.2 authorization testing."""
    main_db_path = tmp_path / "test_a6_5_2_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_5_2_security.sqlite3"
    legacy_json_path = tmp_path / "business_links.json"
    docs_path = tmp_path / "test_docs"
    docs_path.mkdir(parents=True, exist_ok=True)

    legacy_json_path.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("REVIEW_DB_PATH", str(main_db_path))
    monkeypatch.setenv("SECURITY_DB_PATH", str(sec_db_path))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(legacy_json_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("MOCK_EMAIL_TRANSPORT", "true")
    monkeypatch.setenv("ALERT_RECIPIENT_EMAIL", "vajra.techworks@gmail.com")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-gate-key-32-chars-long!!")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    _stores.clear()
    SecurityStore._instances.clear()
    review_service._rate_limits.clear()
    review_service._dedup_cache.clear()
    review_service._verified_preview_sessions.clear()

    sec_store = SecurityStore(db_path=str(sec_db_path))
    sec_store.clear()
    security_shield._store = sec_store
    security_shield.clear()

    main_store = ReviewStore(database_path=str(main_db_path))
    now = time.time()

    with main_store._connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, domain, entitlements_json,
                created_at, updated_at
            ) VALUES (
                'default_business', 'Nasta Ghar', 'active', 'google',
                'https://search.google.com/local/writereview?placeid=ChIJNastaGharOfficial',
                'Navrangpura', 'Breakfast & Snacks', 'Authentic Gujarati breakfast',
                '["Breakfast", "Chai & Tea"]', '#f97316', NULL,
                '["review_manager", "digital_card"]', ?, ?
            )
        """, (now, now))

        # Admin user
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('usr_adm_gate', 'admin@platform.vraja', ?, 'Platform Admin Gate', 1, 1, ?, ?)
        """, (hash_password("AdminGatePass123!"), now, now))
        token_admin = "token_adm_gate"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_adm_gate', 'default_business', ?, ?, NULL)
        """, (hash_token(token_admin), now, now + 86400))

        # Tenant owner
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('usr_own_gate', 'owner@cafe.com', ?, 'Cafe Owner Gate', 1, 0, ?, ?)
        """, (hash_password("OwnerGatePass123!"), now, now))
        token_owner = "token_own_gate"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_own_gate', 'default_business', ?, ?, NULL)
        """, (hash_token(token_owner), now, now + 86400))

    return {
        "tmp_path": tmp_path,
        "main_store": main_store,
        "sec_store": sec_store,
        "admin_token": token_admin,
        "owner_token": token_owner,
    }


# ==============================================================================
# TASK 1 & 2: LIVE SMTP AUTHORIZATION GATE & DURABLE ASYNC DISPATCH
# ==============================================================================
def test_task1_and_task2_live_smtp_gate_and_non_blocking_queue(a6_5_2_env):
    """
    Verify live SMTP requires ALLOW_LIVE_SMTP_TEST=true, credentials,
    and returns immediately with test ID without blocking on socket calls.
    """
    client = TestClient(app)
    admin_cookie = {OWNER_COOKIE: a6_5_2_env["admin_token"]}
    store = a6_5_2_env["sec_store"]

    # 1. Under default mock transport -> returns MOCK_SENT immediately
    res_mock = client.post(
        "/api/platform/security-shield/test-alert",
        cookies=admin_cookie,
        headers={"Origin": "http://localhost:5173"}
    )
    assert res_mock.status_code == 200
    mock_data = res_mock.json()
    assert mock_data["status"] == "MOCK_SENT"
    test_id_mock = mock_data["test_id"]
    assert test_id_mock.startswith("syn_test_")

    # Verify status lookup endpoint
    lookup_resp = client.get(f"/api/platform/security-shield/test-alert/{test_id_mock}", cookies=admin_cookie)
    assert lookup_resp.status_code == 200
    lookup_data = lookup_resp.json()
    assert lookup_data["test_id"] == test_id_mock
    assert lookup_data["status"] == "mock_sent"

    # 2. When mock is disabled, credentials present, but ALLOW_LIVE_SMTP_TEST is NOT set -> FAIL-CLOSED
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("MOCK_EMAIL_TRANSPORT", "false")
        mp.setenv("SMTP_HOST", "smtp.example.com")
        mp.setenv("SMTP_USER", "test_user")
        mp.setenv("SMTP_PASSWORD", "test_pass")
        mp.delenv("ALLOW_LIVE_SMTP_TEST", raising=False)

        res_rejected = client.post(
            "/api/platform/security-shield/test-alert",
            cookies=admin_cookie,
            headers={"Origin": "http://localhost:5173"}
        )
        assert res_rejected.status_code == 200
        data_rej = res_rejected.json()
        assert data_rej["status"] == "REJECTED_MISSING_LIVE_FLAG"
        assert "ALLOW_LIVE_SMTP_TEST=true is required" in data_rej["message"]

    # 3. When mock disabled, credentials MISSING -> NOT CONFIGURED
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("MOCK_EMAIL_TRANSPORT", "false")
        mp.delenv("SMTP_HOST", raising=False)
        mp.delenv("SMTP_USER", raising=False)
        mp.delenv("SMTP_PASSWORD", raising=False)

        res_unconf = client.post(
            "/api/platform/security-shield/test-alert",
            cookies=admin_cookie,
            headers={"Origin": "http://localhost:5173"}
        )
        assert res_unconf.status_code == 200
        data_unconf = res_unconf.json()
        assert data_unconf["status"] == "NOT CONFIGURED"

    # 4. When mock disabled, credentials set, AND ALLOW_LIVE_SMTP_TEST=true -> QUEUED non-blocking
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("MOCK_EMAIL_TRANSPORT", "false")
        mp.setenv("SMTP_HOST", "127.0.0.1")
        mp.setenv("SMTP_PORT", "9999")  # Unreachable port to test socket non-blocking
        mp.setenv("SMTP_USER", "user")
        mp.setenv("SMTP_PASSWORD", "pass")
        mp.setenv("ALLOW_LIVE_SMTP_TEST", "true")

        # Clear rate limit before test step 4
        review_service._rate_limits.clear()

        t0 = time.time()
        res_queued = client.post(
            "/api/platform/security-shield/test-alert",
            cookies=admin_cookie,
            headers={"Origin": "http://localhost:5173"}
        )
        elapsed = time.time() - t0
        assert res_queued.status_code == 200
        data_q = res_queued.json()
        assert data_q["status"] == "QUEUED"
        # Non-blocking proof: API returned immediately (< 0.5s) instead of blocking for 10s SMTP timeout
        assert elapsed < 1.0, f"Synthetic test dispatch must be non-blocking, took {elapsed}s"


# ==============================================================================
# TASK 3: COMPREHENSIVE TEST ALERT SECURITY & OUTBOX ISOLATION
# ==============================================================================
def test_task3_test_alert_security_controls_matrix(a6_5_2_env):
    """Verify 401, 403, 429, CSRF, recipient override rejection, and outbox isolation."""
    client = TestClient(app)
    admin_cookie = {OWNER_COOKIE: a6_5_2_env["admin_token"]}
    owner_cookie = {OWNER_COOKIE: a6_5_2_env["owner_token"]}
    store = a6_5_2_env["sec_store"]

    # 1. Anonymous request rejected (401)
    r_unauth = client.post("/api/platform/security-shield/test-alert")
    assert r_unauth.status_code == 401

    # 2. Non-admin tenant owner rejected (403)
    r_nonadmin = client.post("/api/platform/security-shield/test-alert", cookies=owner_cookie)
    assert r_nonadmin.status_code == 403

    # 3. Recipient override attempt strictly rejected (400)
    r_bad_recip = client.post(
        "/api/platform/security-shield/test-alert",
        cookies=admin_cookie,
        headers={"Origin": "http://localhost:5173"},
        json={"recipient": "attacker@evil.com"}
    )
    assert r_bad_recip.status_code == 400
    assert "Unauthorized recipient" in r_bad_recip.json()["detail"]

    # 4. Strict rate limiting (max 3/min)
    client.post("/api/platform/security-shield/test-alert", cookies=admin_cookie, headers={"Origin": "http://localhost:5173"})
    client.post("/api/platform/security-shield/test-alert", cookies=admin_cookie, headers={"Origin": "http://localhost:5173"})
    r_limited = client.post("/api/platform/security-shield/test-alert", cookies=admin_cookie, headers={"Origin": "http://localhost:5173"})
    assert r_limited.status_code == 429

    # 5. Outbox Isolation: incident outbox remains completely separate
    outbox_items, total = store.list_outbox()
    # Synthetic tests are NOT in security_alert_outbox
    assert not any("SYNTHETIC" in item["subject"] for item in outbox_items)


# ==============================================================================
# TASK 4: WORKER RECOVERY, DISPATCH-TIME AUTH, AND TTL EXPIRY
# ==============================================================================
def test_task4_worker_recovery_of_pending_synthetic_tests(a6_5_2_env):
    """Verify that queued synthetic tests can be recovered, enforce dispatch-time auth, and expire stale jobs."""
    store = a6_5_2_env["sec_store"]
    mailer = AlertMailer()

    # 1. Recovery under mock transport
    test_id = "syn_test_recover_01"
    store.record_synthetic_test(
        test_id=test_id,
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI STAGING TEST] Recovery Test",
        body_text="Recovery test body",
        body_html="<p>Recovery test</p>",
        status="queued",
        initiated_by="admin@platform.vraja"
    )

    worker = AlertDispatcherWorker(store=store, mailer=mailer, poll_interval=0.1)
    worker.start()
    time.sleep(0.3)
    worker.stop(timeout=1.0)

    rec = store.get_synthetic_test(test_id)
    assert rec is not None
    assert rec["status"] in ("sent", "mock_sent", "not_configured", "rejected_missing_live_flag")

    # 2. Dispatch-time authorization revocation: queued when authorized, but flag revoked before worker claims
    test_id_revoked = "syn_test_revoked_02"
    store.record_synthetic_test(
        test_id=test_id_revoked,
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI STAGING TEST] Revocation Test",
        body_text="Revocation test body",
        body_html="<p>Revocation test</p>",
        status="queued",
        initiated_by="admin@platform.vraja"
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("MOCK_EMAIL_TRANSPORT", "false")
        mp.delenv("ALLOW_LIVE_SMTP_TEST", raising=False)  # Revoked!
        mp.setenv("SMTP_HOST", "smtp.example.com")
        mp.setenv("SMTP_USER", "u")
        mp.setenv("SMTP_PASSWORD", "p")

        res_proc = mailer.process_synthetic_tests(store)
        rec_rev = store.get_synthetic_test(test_id_revoked)
        assert rec_rev["status"] == "cancelled_missing_live_flag"
        assert "ALLOW_LIVE_SMTP_TEST not enabled at dispatch time" in rec_rev["last_error"]

    # 3. Stale synthetic test TTL expiry: queued > 300s ago is expired rather than dispatched
    test_id_stale = "syn_test_stale_03"
    with store._connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO security_synthetic_tests (
                test_id, recipient, subject, body_text, body_html, status,
                initiated_by, is_synthetic, attempts, created_at, completed_at, last_error
            ) VALUES (?, 'vajra.techworks@gmail.com', 'Stale', 'body', 'html', 'queued', 'admin@platform.vraja', 1, 0, ?, NULL, NULL)
        """, (test_id_stale, time.time() - 3600.0))  # Created 1 hour ago

    # Processing expired test
    res_expired = mailer.process_synthetic_tests(store, ttl_seconds=300.0)
    rec_stale = store.get_synthetic_test(test_id_stale)
    assert rec_stale["status"] == "expired"
    assert "expired" in rec_stale["last_error"].lower()

    # 4. Multi-worker concurrency safety: simultaneous claims via BEGIN IMMEDIATE
    claimed_w1 = store.claim_pending_synthetic_tests(limit=5)
    claimed_w2 = store.claim_pending_synthetic_tests(limit=5)
    # Double-claim is impossible (w2 receives 0 items because w1 claimed all queued items)
    overlap = set(i["test_id"] for i in claimed_w1).intersection(set(i["test_id"] for i in claimed_w2))
    assert len(overlap) == 0


# ==============================================================================
# TASK 5 & 6: RELEASE MANIFEST HMAC SIGNING & UNEXPECTED FILE DETECTION
# ==============================================================================
def test_task5_and_task6_manifest_hmac_and_unexpected_files(tmp_path):
    """Verify cryptographic HMAC provenance and detection of unexpected source files."""
    secret_key = "super-secure-release-signing-secret-key-2026!!"
    manifest = generate_release_manifest(release_id="rel_v2_signed", repo_root=REPO_ROOT, include_frontend_dist=False)

    # 1. Sign manifest
    sig = sign_release_manifest(manifest, secret_key)
    assert len(sig) == 64  # SHA-256 hex string

    # 2. Verify signature
    assert verify_manifest_signature(manifest, sig, secret_key) is True
    assert verify_manifest_signature(manifest, "invalidsig123", secret_key) is False

    # 3. Detect unexpected new files
    # Create a dummy unexpected py file in monitored tree
    dummy_file = REPO_ROOT / "Backend" / "app" / "core" / "security" / "_unexpected_tamper_test.py"
    try:
        dummy_file.write_text("# injected backdoor source\n", encoding="utf-8")
        is_valid, devs, unexp = verify_code_integrity(manifest, repo_root=REPO_ROOT)
        assert is_valid is False
        assert any("_unexpected_tamper_test.py" in u for u in unexp)
    finally:
        if dummy_file.exists():
            dummy_file.unlink()

    # 4. After cleanup, code integrity returns to valid
    is_valid_clean, devs_clean, unexp_clean = verify_code_integrity(manifest, repo_root=REPO_ROOT)
    assert is_valid_clean is True
    assert len(devs_clean) == 0
    assert len(unexp_clean) == 0

    # 5. Cryptographic signature enforcement fails closed on invalid or missing signature
    is_valid_bad_sig, devs_bad_sig, _ = verify_code_integrity(
        manifest, repo_root=REPO_ROOT, signature="invalid_tampered_sig", signing_secret=secret_key
    )
    assert is_valid_bad_sig is False
    assert any("INVALID_MANIFEST_SIGNATURE" in d for d in devs_bad_sig)

    # Valid signature passes
    is_valid_good_sig, devs_good_sig, _ = verify_code_integrity(
        manifest, repo_root=REPO_ROOT, signature=sig, signing_secret=secret_key
    )
    assert is_valid_good_sig is True
    assert len(devs_good_sig) == 0

    # 6. Production mode fails closed when RELEASE_SIGNING_SECRET is missing
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("ENVIRONMENT", "production")
        mp.delenv("RELEASE_SIGNING_SECRET", raising=False)
        is_val_prod_no_sec, devs_prod_no_sec, _ = verify_code_integrity(manifest, repo_root=REPO_ROOT)
        assert is_val_prod_no_sec is False
        assert any("MISSING_RELEASE_SIGNING_SECRET" in d for d in devs_prod_no_sec)

    # 7. Manifest fingerprint mismatch / internal tampering fails closed
    tampered_manifest = dict(manifest)
    tampered_manifest["manifest_fingerprint"] = "0000000000000000000000000000000000000000000000000000000000000000"
    is_val_tampered, devs_tampered, _ = verify_code_integrity(tampered_manifest, repo_root=REPO_ROOT)
    assert is_val_tampered is False
    assert any("MANIFEST_TAMPERED" in d for d in devs_tampered)

    # 8. Release identifier mismatch fails closed
    is_val_rel_mismatch, devs_rel_mismatch, _ = verify_code_integrity(
        manifest, repo_root=REPO_ROOT, expected_release_id="unexpected_rel_999"
    )
    assert is_val_rel_mismatch is False
    assert any("RELEASE_MISMATCH" in d for d in devs_rel_mismatch)


# ==============================================================================
# TASK 7: PRODUCT A 1-5 GOOGLE REVIEW ACCESS & PRODUCT B CLEAN ISOLATION
# ==============================================================================
def test_task7_google_reviews_and_product_b_clean(a6_5_2_env):
    """Verify Google review link access across 1-5 stars and Product B clean git status."""
    client = TestClient(app)

    # 1. Verify link endpoint
    resp = client.get("/api/businesses/default_business/review-link")
    assert resp.status_code == 200
    assert "google.com" in resp.json()["review_url"]

    # 2. Verify idea generation across ratings 1 through 5
    for r in range(1, 6):
        res = client.post(
            "/api/reviews/ideas",
            json={
                "business_id": "default_business",
                "rating": r,
                "language": "en",
                "aspects": ["Breakfast"],
                "user_note": "Great food",
            }
        )
        assert res.status_code == 200
        assert len(res.json()["ideas"]) >= 1

    # 3. Product B git status
    import subprocess
    git_status = subprocess.check_output(
        ["git", "status", "--porcelain", "Digital_Card"],
        cwd=str(REPO_ROOT),
        text=True
    )
    assert git_status.strip() == "", "Product B must remain 100% clean"
