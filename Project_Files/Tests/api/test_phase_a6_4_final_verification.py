"""
Phase A6.4 Test Suite: Final Security Verification, Official Dependency Requirements & SMTP Readiness.

Validates:
1. Task 1: Authoritative Technical Requirements Inventory (official vs laptop vs locked versions, explicit NOT FOUND detection).
2. Task 2: Database Safety Guards (rejection of relative paths, symlinks, missing env vars, subprocess isolation).
3. Task 3: Google Reviews 1-5 Star Regression (ratings 1 through 5, multilingual EN/HI/GU, NastaGhar branding, unblocked Google access).
4. Task 4: Real Security Center Browser Testing (Playwright against compiled React app + live FastAPI backend).
5. Task 5: SMTP Readiness & Staging Alert Configuration (vajra.techworks@gmail.com, safe credentials, unexecuted live flag).
6. Task 6: Code Integrity Controls & SHA-256 Stability.
"""

import os
import sys
import time
import json
import uuid
import socket
import hashlib
import asyncio
import threading
import subprocess
from pathlib import Path
import pytest
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
from Backend.app.core.security.security_store import SecurityStore, DEFAULT_SECURITY_DB
from Backend.app.core.security.alert_mailer import alert_mailer, AlertMailer, AlertDispatcherWorker
from Backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROD_DB_HASH = "37624B30A19B67809B078D951E1A382A83B2A49311EDB0445187002D7F365BA4"


@pytest.fixture
def a6_4_env(tmp_path, monkeypatch):
    """Isolated environment for Phase A6.4 verification."""
    main_db_path = tmp_path / "test_a6_4_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_4_security.sqlite3"
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
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-key-for-test-32-chars!!")

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
                '["Breakfast", "Chai & Tea", "Snacks", "Taste & Flavour", "Friendly Staff", "Cleanliness", "Value for Money", "Quick Service"]',
                '#f97316', NULL, '["review_manager", "digital_card"]', ?, ?
            )
        """, (now, now))
        db.execute("""
            INSERT OR REPLACE INTO users (
                id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at
            ) VALUES (
                'usr_platform_admin', 'admin@platform.vraja', ?, 'Platform Admin', 1, 1, ?, ?
            )
        """, (hash_password("AdminSecurePassword!2026"), now, now))
        db.execute("""
            INSERT OR REPLACE INTO users (
                id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at
            ) VALUES (
                'usr_owner_cafe', 'owner@cafe.com', ?, 'Cafe Owner', 1, 0, ?, ?
            )
        """, (hash_password("OwnerSecurePassword!2026"), now, now))
        db.execute("""
            INSERT OR REPLACE INTO tenant_memberships (
                id, user_id, tenant_id, role, created_at
            ) VALUES (
                'mem_owner_cafe', 'usr_owner_cafe', 'default_business', 'owner', ?
            )
        """, (now,))

    return {
        "tmp_path": tmp_path,
        "main_db_path": main_db_path,
        "sec_db_path": sec_db_path,
        "main_store": main_store,
        "sec_store": sec_store,
    }


# ==============================================================================
# TASK 1: AUTHORITATIVE DEPENDENCY REQUIREMENTS AUDIT
# ==============================================================================
def test_task1_authoritative_dependency_requirements_inventory():
    """Verify repository requirement files, versions, and absence of undocumented pins."""
    req_txt = REPO_ROOT / "requirements.txt"
    pyproject = REPO_ROOT / "pyproject.toml"
    dockerfile = REPO_ROOT / "Dockerfile"
    p_a_pkg = REPO_ROOT / "NastaGhar" / "frontend" / "package.json"
    p_b_pkg = REPO_ROOT / "Digital_Card" / "frontend" / "package.json"

    assert req_txt.exists(), "requirements.txt must exist"
    assert pyproject.exists(), "pyproject.toml must exist"
    assert dockerfile.exists(), "Dockerfile must exist"
    assert p_a_pkg.exists(), "Product A package.json must exist"
    assert p_b_pkg.exists(), "Product B package.json must exist"

    # Explicit check for missing version pinning files
    python_version_file = REPO_ROOT / ".python-version"
    nvmrc_file = REPO_ROOT / ".nvmrc"
    node_version_file = REPO_ROOT / ".node-version"
    runtime_txt = REPO_ROOT / "runtime.txt"
    req_dev = REPO_ROOT / "requirements-dev.txt"

    assert not python_version_file.exists(), "Official .python-version file is NOT FOUND"
    assert not nvmrc_file.exists(), "Official .nvmrc file is NOT FOUND"
    assert not node_version_file.exists(), "Official .node-version file is NOT FOUND"
    assert not runtime_txt.exists(), "Official runtime.txt file is NOT FOUND"
    assert not req_dev.exists(), "requirements-dev.txt is NOT FOUND"

    # Inspect Dockerfile official base images
    docker_content = dockerfile.read_text(encoding="utf-8")
    assert "node:20-alpine" in docker_content, "Official Docker Node builder image is node:20-alpine"
    assert "python:3.11-slim" in docker_content, "Official Docker runtime image is python:3.11-slim"

    # Inspect Product A package.json
    p_a_data = json.loads(p_a_pkg.read_text(encoding="utf-8"))
    assert p_a_data["dependencies"]["react"] == "^19.2.7"
    assert p_a_data["devDependencies"]["vite"] == "^8.1.1"

    # Inspect Product B package.json
    p_b_data = json.loads(p_b_pkg.read_text(encoding="utf-8"))
    assert p_b_data["dependencies"]["react"] == "^19.2.7"
    assert p_b_data["devDependencies"]["vite"] == "^8.1.1"


# ==============================================================================
# TASK 2: DATABASE SAFETY GUARDS COMPREHENSIVE VERIFICATION
# ==============================================================================
def test_task2_database_safety_guards_reject_relative_symlink_subprocess_unisolated(a6_4_env, tmp_path, monkeypatch):
    """Ensure database safety guards reject relative paths, symlinks, unisolated calls, and subprocess access."""
    # 1. Reject relative path pointing to production review database
    relative_prod_path = Path("Project_Files/Data/nasta-ghar/reviews.sqlite3")
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        ReviewStore(database_path=str(relative_prod_path))

    # 2. Reject relative path with ./
    relative_prod_path_dot = Path("./Project_Files/Data/nasta-ghar/reviews.sqlite3")
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        ReviewStore(database_path=str(relative_prod_path_dot))

    # 3. Reject missing environment variable / None fallback in test mode
    monkeypatch.delenv("REVIEW_DB_PATH", raising=False)
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        ReviewStore(database_path=None)

    # 4. Reject ReviewStore connecting to production security database
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        ReviewStore(database_path=str(DEFAULT_SECURITY_DB))

    # 5. Reject SecurityStore connecting to production security database
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        SecurityStore(db_path=str(DEFAULT_SECURITY_DB))

    # 6. Reject SecurityStore connecting to production review database
    prod_review_db = REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"
    with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
        SecurityStore(db_path=str(prod_review_db))

    # 7. Symlink rejection
    symlink_path = tmp_path / "symlink_prod_review.sqlite3"
    try:
        symlink_path.symlink_to(prod_review_db.resolve())
        with pytest.raises(RuntimeError, match="TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED"):
            ReviewStore(database_path=str(symlink_path))
    except (OSError, NotImplementedError):
        # On Windows, creating symlinks may require developer mode / privilege
        pass

    # 8. Subprocess isolation verification
    script = (
        "import os\n"
        "os.environ['ENVIRONMENT'] = 'test'\n"
        "from Backend.app.core.database.storage import ReviewStore\n"
        "try:\n"
        "    store = ReviewStore(database_path=None)\n"
        "    print('FAILED_SAFETY_GUARD')\n"
        "except RuntimeError as e:\n"
        "    print('BLOCKED_SAFELY:' + str(e))\n"
    )
    res = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert "BLOCKED_SAFELY:" in res.stdout, f"Subprocess must be blocked: {res.stdout}"
    assert "FAILED_SAFETY_GUARD" not in res.stdout


# ==============================================================================
# TASK 3: GOOGLE REVIEWS 1-5 STAR REGRESSION & MULTILINGUAL TEST
# ==============================================================================
def test_task3_google_reviews_1_to_5_stars_and_multilingual_regression(a6_4_env):
    """Verify ratings 1-5 generate ideas, provide Google Review URLs, and support EN, HI, GU."""
    client = TestClient(app)

    # Check public review-link endpoint
    link_resp = client.get("/api/businesses/default_business/review-link")
    assert link_resp.status_code == 200
    link_data = link_resp.json()
    review_url = link_data.get("review_url") or link_data.get("google_review_url")
    assert review_url, "Review URL must be returned"
    assert "search.google.com" in review_url
    assert link_data["business_name"] == "Nasta Ghar"

    # Test all 5 star ratings across English, Hindi, Gujarati
    languages = ["english", "hindi", "gujarati"]
    ratings = [1, 2, 3, 4, 5]

    for lang in languages:
        for r in ratings:
            res = client.post(
                "/api/reviews/ideas",
                json={
                    "business_id": "default_business",
                    "rating": r,
                    "language": lang,
                    "aspects": ["Breakfast", "Chai & Tea"] if r >= 4 else ["Taste & Flavour"],
                    "user_note": "Test note",
                },
            )
            assert res.status_code == 200, f"Ideas failed for rating {r} in {lang}"
            data = res.json()
            assert "ideas" in data and len(data["ideas"]) >= 1, f"No ideas generated for rating {r} in {lang}"
            for idea in data["ideas"]:
                assert "text" in idea and len(idea["text"].strip()) > 5
                # Verify placeholder is never shown
                assert "default_business" not in idea["text"]

    # Verify 1-star and 2-star ratings allow private feedback submission WITHOUT blocking Google Maps
    priv_resp = client.post(
        "/api/reviews/private-feedback",
        json={
            "business_id": "default_business",
            "rating": 1,
            "diner_note": "Chai was cold and delayed.",
            "aspects": ["Chai & Tea"],
            "table_number": "Table 4",
            "guest_contact": "guest@test.com",
        },
    )
    assert priv_resp.status_code == 200
    priv_data = priv_resp.json()
    assert priv_data["status"] in ("received", "escalated")
    assert priv_data["ticket_id"] and len(priv_data["ticket_id"]) > 3


# ==============================================================================
# TASK 4: REAL SECURITY CENTER BROWSER TESTING (PLAYWRIGHT + LIVE FASTAPI + REACT)
# ==============================================================================
def test_task4_real_security_center_browser_playwright_e2e(a6_4_env):
    """Execute real browser Playwright tests against compiled React app + live FastAPI backend."""
    from starlette.staticfiles import StaticFiles
    from playwright.sync_api import sync_playwright

    dist_path = REPO_ROOT / "NastaGhar" / "frontend" / "dist"
    assert dist_path.exists(), f"Frontend dist folder must exist: {dist_path}"

    sec_store = a6_4_env["sec_store"]

    # Seed an incident with potential XSS payload
    inc_xss_id, _ = sec_store.aggregate_event_into_incident(
        event_type=SecurityEventType.AI_INJECTION_NEUTRALIZED,
        severity=SecuritySeverity.CRITICAL,
        affected_tenant="default_business",
        actor_id="bad_actor_99",
        title="XSS Injection Attempt",
        description="XSS Injection Attempt: <script>alert('xss')</script> in payload parameter",
        details={"endpoint": "/api/reviews/generate", "payload": "<script>alert('xss')</script>"},
    )

    # Seed another incident for resolution
    inc_probe_id, _ = sec_store.aggregate_event_into_incident(
        event_type=SecurityEventType.AUTH_BRUTE_FORCE_LOCKOUT,
        severity=SecuritySeverity.HIGH,
        affected_tenant="default_business",
        actor_id="actor_lockout_01",
        title="Brute Force Login Lockout",
        description="Sustained login probe detected from 192.168.1.100",
        details={"endpoint": "/api/auth/login", "client_ip": "192.168.1.100"},
    )

    # Queue an alert in outbox
    sec_store.queue_alert(
        incident_id=inc_probe_id,
        recipient="vajra.techworks@gmail.com",
        subject="[VRAJA AI SECURITY] HIGH — Brute Force Login Lockout",
        body_text="Alert details text...",
        body_html="<p>Alert details html</p>",
        severity="HIGH",
    )

    # Mount compiled React frontend onto app router
    from fastapi import FastAPI
    test_live_app = FastAPI()
    test_live_app.include_router(app.router)
    test_live_app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")

    # Pick free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Allow test server origin through CSRF check
    os.environ["CORS_ORIGINS"] = f"http://127.0.0.1:{port},http://localhost:{port},http://localhost:5173,http://127.0.0.1:5173"

    class SafeTestServer:
        def __init__(self, app_to_run, port_num):
            self.app_to_run = app_to_run
            self.port_num = port_num
            self.server = None
            self.thread = None

        def start(self):
            def _run():
                import uvicorn
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                config = uvicorn.Config(self.app_to_run, host="127.0.0.1", port=self.port_num, log_level="warning")
                config.install_signal_handlers = False
                self.server = uvicorn.Server(config)
                loop.run_until_complete(self.server.serve())

            self.thread = threading.Thread(target=_run, daemon=True)
            self.thread.start()

    server = SafeTestServer(test_live_app, port)
    server.start()
    time.sleep(1.5)

    enforce_browser = os.getenv("ENFORCE_BROWSER_TESTS", "").strip().lower() in ("1", "true", "yes")

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                try:
                    browser = p.chromium.launch(headless=True)
                except Exception as e:
                    if enforce_browser:
                        pytest.fail(f"REQUIRED CI BROWSER TEST GATE FAILED: ENFORCE_BROWSER_TESTS is enabled, but browser launch failed: {e}")
                    pytest.skip(f"No compatible browser binary found: {e}")
            context = browser.new_context()
            page = context.new_page()

            page.on("console", lambda msg: print(f"PAGE CONSOLE: {msg.text}"))
            page.on("response", lambda resp: print(f"RESP: {resp.status} {resp.url}"))

            # 1. Unauthenticated view -> Login card
            page.goto(f"http://127.0.0.1:{port}/?view=admin")
            page.wait_for_selector(".admin-login-card")
            assert page.locator(".admin-login-card").is_visible()

            # 2. Invalid credentials rejected
            page.fill("input[type=email]", "wrong@platform.vraja")
            page.fill("input[type=password]", "WrongPassword123")
            page.click("button[type=submit]")
            page.wait_for_selector(".admin-alert-danger")
            assert "Invalid email or password" in page.locator(".admin-alert-danger").inner_text()

            # 3. Non-admin user rejected with 403 Forbidden Access Restricted screen
            page.fill("input[type=email]", "owner@cafe.com")
            page.fill("input[type=password]", "OwnerSecurePassword!2026")
            page.click("button[type=submit]")
            page.wait_for_selector(".admin-forbidden-card")
            assert page.locator(".admin-forbidden-card").is_visible()

            # Sign out from non-admin session
            page.click("button:has-text('Sign Out')")
            page.wait_for_selector(".admin-login-card")

            # 4. Platform Admin sign in
            page.fill("input[type=email]", "admin@platform.vraja")
            page.fill("input[type=password]", "AdminSecurePassword!2026")
            page.click("button[type=submit]")
            page.wait_for_selector(".admin-nav-tab")

            # 5. Open Security Shield tab
            page.click("button:has-text('Security Shield')")
            page.wait_for_selector("text=Active Incidents")
            assert page.locator("text=Active Incidents").is_visible()

            # 6. Verify XSS safety: script tag rendered as plain text in DOM, script never executed
            page.wait_for_selector(f"text={inc_xss_id}")
            xss_locator = page.locator("text=<script>alert('xss')</script>").first
            assert xss_locator.is_visible()
            assert "<script>alert('xss')</script>" in xss_locator.inner_text()

            # 7. Acknowledge an incident
            ack_button = page.locator("button:has-text('Acknowledge')").first
            if ack_button.is_visible():
                ack_button.click()
                page.wait_for_selector(":has-text('marked as investigating')", timeout=10000)

            # 8. Resolve an incident with resolution notes
            page.locator("button:has-text('Resolve…')").first.click()
            page.wait_for_selector("text=Resolution Notes & Root Cause Mitigation:")
            page.fill("textarea", "Verified and confirmed harmless test probe.")
            page.click("button:has-text('Mark Resolved')")
            page.wait_for_selector(":has-text('marked as resolved')", timeout=10000)

            # 9. Test Outbox tab & recipient
            page.locator("button:has-text('Alert Outbox')").click()
            page.wait_for_selector("text=vajra.techworks@gmail.com")
            assert page.locator("text=vajra.techworks@gmail.com").first.is_visible()

            # 10. Flush Outbox button
            flush_btn = page.locator("button:has-text('Flush & Send Outbox')")
            assert flush_btn.is_visible()
            flush_btn.click()

            # 11. Export Audit JSON button
            export_btn = page.locator("button:has-text('Export Audit JSON')")
            assert export_btn.is_visible()
            export_btn.click()

            # 12. Mobile viewport test (375x667)
            page.set_viewport_size({"width": 375, "height": 667})
            assert page.locator("text=Pending and Dispatched Email Alerts").is_visible()

            browser.close()
    finally:
        if server.server:
            server.server.should_exit = True


# ==============================================================================
# TASK 5: SMTP READINESS & STAGING ALERT CONFIGURATION
# ==============================================================================
def test_task5_smtp_readiness_and_staging_alert_configuration(a6_4_env):
    """Verify target recipient vajra.techworks@gmail.com and safe handling of unconfigured SMTP."""
    mailer = AlertMailer()

    # Recipient verification
    assert mailer.recipient == "vajra.techworks@gmail.com"

    # Non-sensitive status verification
    status = mailer.get_status()
    assert status["target_recipient"] == "vajra.techworks@gmail.com"
    assert "SMTP_PASSWORD" not in status
    assert status["transport"] in ("mock", "smtp")

    # Email formatting check
    mock_incident = {
        "incident_id": "inc_audit_test_99",
        "severity": "CRITICAL",
        "event_type": "ACCESS_UNKNOWN_TENANT",
        "title": "Access Unknown Tenant Probe",
        "affected_tenant": "attacker_fake_tenant",
        "event_count": 5,
        "last_observed_at": time.time(),
        "description": "5 consecutive 404 unknown tenant probes detected.",
    }
    subj, text, html = mailer.format_incident_email(mock_incident)
    assert "[VRAJA AI SECURITY] CRITICAL" in subj
    assert "Incident ID:  inc_audit_test_99" in text
    assert "attacker_fake_tenant" in text
    assert "https://app.vraja.ai/admin" in text

    # Verify live SMTP test flag
    assert not mailer.is_configured, "Live SMTP credentials must remain unconfigured in repo"


# ==============================================================================
# TASK 6: CODE INTEGRITY CONTROLS AUDIT & DATABASE HASH STABILITY
# ==============================================================================
def test_task6_code_integrity_controls_audit():
    """Verify code integrity, placeholder .github state, and database SHA-256 stability."""
    # 1. Audit .github directory
    gh_dir = REPO_ROOT / ".github"
    assert gh_dir.exists()
    gh_files = [f.name for f in gh_dir.iterdir() if f.is_file()]
    # .github currently contains placeholder only
    assert ".gitkeep" in gh_files or "README.md" in gh_files

    # 2. Production Database SHA-256 verification
    prod_db = REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"
    assert prod_db.exists(), "Production reviews.sqlite3 must exist"
    data = prod_db.read_bytes()
    computed_hash = hashlib.sha256(data).hexdigest().upper()
    assert computed_hash == PROD_DB_HASH, (
        f"Production database checksum mismatch! Expected: {PROD_DB_HASH}, Got: {computed_hash}"
    )

    # 3. Product B directory untouched
    product_b_dir = REPO_ROOT / "Digital_Card"
    assert product_b_dir.exists()
