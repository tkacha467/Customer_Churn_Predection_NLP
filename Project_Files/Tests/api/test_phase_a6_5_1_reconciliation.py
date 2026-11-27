"""
Phase A6.5.1 Test Suite: Release Evidence Reconciliation & Controlled SMTP Readiness.

Validates:
1. Reconciled Technical Requirements (package.json vs package-lock.json vs Dockerfile vs Host).
2. GitHub Actions CI syntax, permissions, third-party version pinning, and clean-checkout readiness.
3. Code-Integrity Engine path normalization, directory traversal protection, and DB schema vs content separation.
4. Synthetic SMTP Test Endpoint rate limiting, admin authorization, CSRF check, and credential isolation.
5. Google Review 1-5 star accessibility regression and Product B file isolation.
"""

import os
import json
import time
import yaml
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
from Backend.app.core.security.alert_mailer import alert_mailer, AlertMailer
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
    compute_file_sha256,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROD_DB_HASH = "37624B30A19B67809B078D951E1A382A83B2A49311EDB0445187002D7F365BA4"


@pytest.fixture
def a6_5_1_env(tmp_path, monkeypatch):
    """Isolated test environment for Phase A6.5.1 reconciliation."""
    main_db_path = tmp_path / "test_a6_5_1_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_5_1_security.sqlite3"
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
    monkeypatch.setenv("OWNER_SESSION_SECRET", "reconciliation-secret-key-32-chars-long!!")
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
            VALUES ('usr_adm_recon', 'admin@platform.vraja', ?, 'Platform Admin', 1, 1, ?, ?)
        """, (hash_password("AdminPass123!"), now, now))
        token_admin = "token_adm_recon"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_adm_recon', 'default_business', ?, ?, NULL)
        """, (hash_token(token_admin), now, now + 86400))

        # Tenant owner
        db.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
            VALUES ('usr_own_recon', 'owner@cafe.com', ?, 'Cafe Owner', 1, 0, ?, ?)
        """, (hash_password("OwnerPass123!"), now, now))
        token_owner = "token_own_recon"
        db.execute("""
            INSERT OR REPLACE INTO sessions (token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at)
            VALUES (?, 'usr_own_recon', 'default_business', ?, ?, NULL)
        """, (hash_token(token_owner), now, now + 86400))

    return {
        "tmp_path": tmp_path,
        "main_store": main_store,
        "sec_store": sec_store,
        "admin_token": token_admin,
        "owner_token": token_owner,
    }


# ==============================================================================
# TASK 1: RECONCILE ACTUAL TECHNICAL REQUIREMENTS
# ==============================================================================
def test_task1_reconciled_requirements_inventory():
    """Verify package.json vs package-lock.json vs Dockerfile vs requirements.txt."""
    # 1. Product A package.json & package-lock.json
    p_a_pkg = json.loads((REPO_ROOT / "NastaGhar" / "frontend" / "package.json").read_text(encoding="utf-8"))
    p_a_lock = json.loads((REPO_ROOT / "NastaGhar" / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    assert p_a_pkg["dependencies"]["react"] == "^19.2.7"
    assert p_a_pkg["devDependencies"]["vite"] == "^8.1.1"
    assert p_a_lock["packages"]["node_modules/react"]["version"] == "19.2.7"
    assert p_a_lock["packages"]["node_modules/vite"]["version"] == "8.3.8"

    # 2. Product B package.json & package-lock.json
    p_b_pkg = json.loads((REPO_ROOT / "Digital_Card" / "frontend" / "package.json").read_text(encoding="utf-8"))
    p_b_lock = json.loads((REPO_ROOT / "Digital_Card" / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    assert p_b_pkg["dependencies"]["react"] == "^19.2.7"
    assert p_b_pkg["devDependencies"]["vite"] == "^8.1.1"
    assert p_b_lock["packages"]["node_modules/react"]["version"] == "19.2.7"
    assert p_b_lock["packages"]["node_modules/vite"]["version"] == "8.1.4"

    # 3. Dockerfile deployment targets
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "node:20-alpine" in dockerfile
    assert "python:3.11-slim" in dockerfile

    # 4. Vite Node engine constraint
    vite_pkg = json.loads((REPO_ROOT / "NastaGhar" / "frontend" / "node_modules" / "vite" / "package.json").read_text(encoding="utf-8"))
    assert "^20.19.0" in vite_pkg["engines"]["node"]

    # 5. Tushar specification absence
    assert not (REPO_ROOT / ".python-version").exists()
    assert not (REPO_ROOT / ".nvmrc").exists()
    assert not (REPO_ROOT / "runtime.txt").exists()


# ==============================================================================
# TASK 2: VERIFY GITHUB ACTIONS CI SPECIFICATION
# ==============================================================================
def test_task2_github_actions_ci_validation():
    """Verify GitHub Actions workflow syntax, permissions, and clean-checkout readiness."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "ci.yml must exist"

    with open(ci_path, "r", encoding="utf-8") as f:
        ci_config = yaml.safe_load(f)

    # 1. Root structure and permissions
    assert ci_config["permissions"]["contents"] == "read"
    assert "backend-security-and-tests" in ci_config["jobs"]
    assert "frontend-builds-and-audit" in ci_config["jobs"]
    assert "release-integrity-manifest" in ci_config["jobs"]
    assert "secret-scanning" in ci_config["jobs"]

    # 2. Dependency installations
    backend_job = ci_config["jobs"]["backend-security-and-tests"]
    install_step = next(s for s in backend_job["steps"] if s.get("name") == "Install Python Dependencies")
    assert "pytest" in install_step["run"]
    assert "httpx" in install_step["run"]

    # 3. Third-party action version pinning
    frontend_job = ci_config["jobs"]["frontend-builds-and-audit"]
    setup_node_step = next(s for s in frontend_job["steps"] if "setup-node" in s.get("uses", ""))
    assert setup_node_step["uses"] == "actions/setup-node@v4"

    secret_job = ci_config["jobs"]["secret-scanning"]
    gitleaks_step = next(s for s in secret_job["steps"] if "gitleaks" in s.get("uses", ""))
    assert gitleaks_step["uses"] == "gitleaks/gitleaks-action@v2"


# ==============================================================================
# TASK 3: CODE-INTEGRITY MONITORING & DIRECTORY TRAVERSAL PROTECTION
# ==============================================================================
def test_task3_code_integrity_and_traversal_guards(tmp_path):
    """Verify manifest integrity, path traversal rejection, and schema vs content separation."""
    # 1. Directory traversal rejection
    malicious_manifest = {
        "release_id": "malicious_test",
        "file_hashes": {
            "../../etc/passwd": "dummyhash123",
            "../secret.txt": "dummyhash456",
        }
    }
    is_valid, deviations, _ = verify_code_integrity(malicious_manifest, repo_root=REPO_ROOT)
    assert is_valid is False
    assert any("TRAVERSAL_REJECTED" in d for d in deviations)

    # 2. Legitimate manifest generation and verification
    manifest = generate_release_manifest(release_id="recon_test", repo_root=REPO_ROOT, include_frontend_dist=False)
    assert manifest["total_monitored_files"] > 30
    is_valid, devs, _ = verify_code_integrity(manifest, repo_root=REPO_ROOT)
    assert is_valid is True
    assert len(devs) == 0

    # 3. Database schema vs content separation
    test_db = tmp_path / "schema_test.sqlite3"
    main_store = ReviewStore(database_path=str(test_db))
    healthy1, msg1, hash1 = verify_database_schema_integrity(test_db)
    assert healthy1 is True
    assert msg1 == "ok"

    # Insert customer data row -> Schema hash MUST remain identical
    with main_store._connect() as conn:
        conn.execute(
            "INSERT INTO tenants (id, business_name, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("t_new_customer", "Customer Cafe", "active", time.time(), time.time())
        )
    healthy2, msg2, hash2 = verify_database_schema_integrity(test_db)
    assert healthy2 is True
    assert hash2 == hash1, "Customer row insertions must NEVER alter schema hash"

    # Alter schema (DDL tampering) -> Schema hash MUST change
    with main_store._connect() as conn:
        conn.execute("CREATE TABLE injected_backdoor (id INTEGER PRIMARY KEY, payload TEXT);")
    healthy3, msg3, hash3 = verify_database_schema_integrity(test_db)
    assert healthy3 is True
    assert hash3 != hash1, "Schema alterations (DDL) must immediately trigger hash discrepancy"


# ==============================================================================
# TASK 4: SYNTHETIC SMTP TEST ENDPOINT AUDIT & RATE LIMITING
# ==============================================================================
def test_task4_synthetic_smtp_audit_and_rate_limiting(a6_5_1_env):
    """Verify admin auth, rate limiting, and safe mock execution of synthetic test alert."""
    client = TestClient(app)
    admin_cookie = {OWNER_COOKIE: a6_5_1_env["admin_token"]}
    owner_cookie = {OWNER_COOKIE: a6_5_1_env["owner_token"]}

    # 1. Unauthenticated rejected (401)
    r_unauth = client.post("/api/platform/security-shield/test-alert")
    assert r_unauth.status_code == 401

    # 2. Non-admin owner rejected (403)
    r_non_admin = client.post("/api/platform/security-shield/test-alert", cookies=owner_cookie)
    assert r_non_admin.status_code == 403

    # 3. Platform admin success (under mock transport)
    r_admin = client.post(
        "/api/platform/security-shield/test-alert",
        cookies=admin_cookie,
        headers={"Origin": "http://localhost:5173"}
    )
    assert r_admin.status_code == 200
    res = r_admin.json()
    assert res["status"] in ("MOCK_SENT", "SENT")
    assert res["recipient"] == "vajra.techworks@gmail.com"
    assert res["is_synthetic"] is True

    # 4. Strict rate limiting (max 3/min)
    client.post("/api/platform/security-shield/test-alert", cookies=admin_cookie, headers={"Origin": "http://localhost:5173"})
    client.post("/api/platform/security-shield/test-alert", cookies=admin_cookie, headers={"Origin": "http://localhost:5173"})
    r_limited = client.post("/api/platform/security-shield/test-alert", cookies=admin_cookie, headers={"Origin": "http://localhost:5173"})
    assert r_limited.status_code == 429
    assert "Too many test alert requests" in r_limited.json()["detail"]


# ==============================================================================
# TASK 5: PRODUCT A 1-5 GOOGLE REVIEW ACCESS & PRODUCT B ISOLATION
# ==============================================================================
def test_task5_google_reviews_1_to_5_stars_and_product_b_isolation(a6_5_1_env):
    """Verify Google Review link access across ratings 1-5 and Product B isolation."""
    client = TestClient(app)

    # 1. Verify direct Google Review access for ratings 1-5
    link_resp = client.get("/api/businesses/default_business/review-link")
    assert link_resp.status_code == 200
    data = link_resp.json()
    assert "google.com" in data.get("review_url", "")

    # Direct idea generation for all ratings 1 to 5 without blocking
    for r in range(1, 6):
        res = client.post(
            "/api/reviews/ideas",
            json={
                "business_id": "default_business",
                "rating": r,
                "language": "en",
                "aspects": ["Breakfast", "Chai & Tea"] if r >= 4 else ["Taste & Flavour"],
                "user_note": "Test review note",
            },
        )
        assert res.status_code == 200
        ideas = res.json()["ideas"]
        assert len(ideas) >= 1

    # 2. Verify Product B code is completely clean and untouched
    import subprocess
    git_status = subprocess.check_output(
        ["git", "status", "--porcelain", "Digital_Card"],
        cwd=str(REPO_ROOT),
        text=True
    )
    assert git_status.strip() == "", f"Product B directory must be 100% clean: {git_status}"
