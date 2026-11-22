"""
Phase A6.5 Test Suite: Release Configuration, Secure SMTP Readiness & Code Integrity Monitoring.

Validates:
1. Task 1: Official Project Requirements Documentation (Docker 3.11/Node 20, React/Vite locked versions, missing declaration checks).
2. Task 2: Code Integrity Manifest & Database Schema vs Content Separation (row inserts do not trigger tampering alarms, DDL tampering is caught).
3. Task 3: GitHub CI Configuration & Branch Protection Specifications.
4. Task 4: Secure SMTP Readiness & Platform Admin Synthetic Test Alert Endpoint.
5. Task 5: Integrity Monitoring API Endpoint.
6. Task 6: Production Database Read-Only Isolation & Checksum Stability.
"""

import os
import sys
import time
import json
import uuid
import hashlib
import sqlite3
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
def a6_5_env(tmp_path, monkeypatch):
    """Isolated test environment for Phase A6.5."""
    main_db_path = tmp_path / "test_a6_5_main.sqlite3"
    sec_db_path = tmp_path / "test_a6_5_security.sqlite3"
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

    # Create session token for platform admin
    admin_token = "admin_session_test_token_12345"
    admin_token_hash = hash_token(admin_token)
    with main_store._connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO sessions (
                token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at
            ) VALUES (?, 'usr_platform_admin', 'default_business', ?, ?, NULL)
        """, (admin_token_hash, now, now + 3600.0))

    # Create session token for regular owner
    owner_token = "owner_session_test_token_12345"
    owner_token_hash = hash_token(owner_token)
    with main_store._connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO sessions (
                token_hash, user_id, active_tenant_id, created_at, expires_at, revoked_at
            ) VALUES (?, 'usr_owner_cafe', 'default_business', ?, ?, NULL)
        """, (owner_token_hash, now, now + 3600.0))

    return {
        "tmp_path": tmp_path,
        "main_db_path": main_db_path,
        "sec_db_path": sec_db_path,
        "main_store": main_store,
        "sec_store": sec_store,
        "admin_token": admin_token,
        "owner_token": owner_token,
    }


# ==============================================================================
# TASK 1: OFFICIAL REQUIREMENTS INVENTORY
# ==============================================================================
def test_task1_official_project_requirements_documentation():
    """Verify runtime environments, package locks, and unpinned dependencies."""
    dockerfile = REPO_ROOT / "Dockerfile"
    p_a_pkg = REPO_ROOT / "NastaGhar" / "frontend" / "package.json"
    p_b_pkg = REPO_ROOT / "Digital_Card" / "frontend" / "package.json"
    p_a_lock = REPO_ROOT / "NastaGhar" / "frontend" / "package-lock.json"
    p_b_lock = REPO_ROOT / "Digital_Card" / "frontend" / "package-lock.json"

    # Docker specification
    content = dockerfile.read_text(encoding="utf-8")
    assert "node:20-alpine" in content, "Official Docker Node builder image is node:20-alpine"
    assert "python:3.11-slim" in content, "Official Docker runtime image is python:3.11-slim"

    # Package files
    assert p_a_pkg.exists()
    assert p_b_pkg.exists()
    assert p_a_lock.exists()
    assert p_b_lock.exists()

    # Package json dependency versions
    data_a = json.loads(p_a_pkg.read_text(encoding="utf-8"))
    assert data_a["dependencies"]["react"] == "^19.2.7"
    assert data_a["dependencies"]["qrcode"] == "^1.5.4"
    assert data_a["devDependencies"]["vite"] == "^8.1.1"

    data_b = json.loads(p_b_pkg.read_text(encoding="utf-8"))
    assert data_b["dependencies"]["react"] == "^19.2.7"
    assert data_b["devDependencies"]["vite"] == "^8.1.1"

    # Missing specification verification
    assert not (REPO_ROOT / ".python-version").exists()
    assert not (REPO_ROOT / ".nvmrc").exists()
    assert not (REPO_ROOT / "runtime.txt").exists()


# ==============================================================================
# TASK 2: CODE INTEGRITY MANIFEST & DATABASE SCHEMA SEPARATION
# ==============================================================================
def test_task2_code_integrity_manifest_and_database_schema_separation(tmp_path):
    """
    Verify release manifest hashing and ensure database schema integrity checks
    do NOT flag legitimate customer row modifications as security incidents.
    """
    # 1. Generate release manifest
    manifest = generate_release_manifest(
        release_id="test_release_v2_0_0",
        repo_root=REPO_ROOT,
        include_frontend_dist=False
    )
    assert manifest["release_id"] == "test_release_v2_0_0"
    assert manifest["total_monitored_files"] > 30
    assert len(manifest["manifest_fingerprint"]) == 64

    # 2. Verify integrity against clean repo
    is_valid, deviations, _ = verify_code_integrity(manifest, REPO_ROOT)
    assert is_valid is True
    assert len(deviations) == 0

    # 3. Test detecting file modification
    dummy_manifest = {
        "release_id": "test_tamper",
        "file_hashes": {
            "requirements.txt": "0000000000000000000000000000000000000000000000000000000000000000"
        }
    }
    is_valid_tampered, deviations_tampered, _ = verify_code_integrity(dummy_manifest, REPO_ROOT)
    assert is_valid_tampered is False
    assert any("MODIFIED: requirements.txt" in d for d in deviations_tampered)

    # 4. Database Schema vs Data Separation Test
    test_db_path = tmp_path / "live_simulated_db.sqlite3"
    with sqlite3.connect(test_db_path) as conn:
        conn.execute("CREATE TABLE reviews (id TEXT PRIMARY KEY, rating INT, comment TEXT);")
        conn.execute("CREATE INDEX idx_rating ON reviews(rating);")
        conn.commit()

    # Initial schema hash
    is_ok, pragma_res, initial_schema_hash = verify_database_schema_integrity(test_db_path)
    assert is_ok is True
    assert pragma_res == "ok"
    assert len(initial_schema_hash) == 64

    # Simulate legitimate customer review submissions (row inserts)
    with sqlite3.connect(test_db_path) as conn:
        for i in range(50):
            conn.execute("INSERT INTO reviews VALUES (?, ?, ?)", (f"rev_{i}", 5, f"Customer review {i}"))
        conn.commit()

    # Verify that row inserts DO NOT change schema hash or trigger integrity alarm
    is_ok_after_rows, pragma_after_rows, schema_hash_after_rows = verify_database_schema_integrity(test_db_path)
    assert is_ok_after_rows is True
    assert pragma_after_rows == "ok"
    assert schema_hash_after_rows == initial_schema_hash, (
        "Customer row insertions MUST NOT alter the schema integrity hash!"
    )

    # Simulate unauthorized schema alteration (DDL tampering)
    with sqlite3.connect(test_db_path) as conn:
        conn.execute("ALTER TABLE reviews ADD COLUMN malicious_payload TEXT;")
        conn.commit()

    # Verify that DDL tampering IS detected
    is_ok_tampered, _, schema_hash_tampered = verify_database_schema_integrity(test_db_path)
    assert is_ok_tampered is True
    assert schema_hash_tampered != initial_schema_hash, (
        "Unauthorized DDL schema modifications MUST trigger a schema hash discrepancy!"
    )


# ==============================================================================
# TASK 3: GITHUB SECURITY CONTROLS PREPARATION
# ==============================================================================
def test_task3_github_security_controls_prepared():
    """Verify GitHub CI workflow and branch protection specification files."""
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    spec_file = REPO_ROOT / ".github" / "BRANCH_PROTECTION.md"

    assert ci_file.exists(), ".github/workflows/ci.yml must exist"
    assert spec_file.exists(), ".github/BRANCH_PROTECTION.md must exist"

    ci_content = ci_file.read_text(encoding="utf-8")
    assert "python-version: \"3.11\"" in ci_content
    assert "node-version: \"20\"" in ci_content
    assert "pytest Project_Files/Tests" in ci_content
    assert "gitleaks" in ci_content.lower()

    spec_content = spec_file.read_text(encoding="utf-8")
    assert "vajra.techworks@gmail.com" in spec_content
    assert "Require a pull request before merging" in spec_content


# ==============================================================================
# TASK 4: SECURE SMTP READINESS & SYNTHETIC ALERT ENDPOINT
# ==============================================================================
def test_task4_secure_smtp_readiness_and_synthetic_alert(a6_5_env):
    """
    Verify SMTP target vajra.techworks@gmail.com, unconfigured reporting,
    and platform admin synthetic test alert execution.
    """
    client = TestClient(app)
    admin_cookie = {OWNER_COOKIE: a6_5_env["admin_token"]}
    owner_cookie = {OWNER_COOKIE: a6_5_env["owner_token"]}

    # 1. Unauthenticated request rejected
    unauth_resp = client.post("/api/platform/security-shield/test-alert")
    assert unauth_resp.status_code == 401

    # 2. Non-admin request rejected (403)
    non_admin_resp = client.post("/api/platform/security-shield/test-alert", cookies=owner_cookie)
    assert non_admin_resp.status_code == 403

    # 3. Platform admin executes synthetic alert in mock mode
    admin_resp = client.post(
        "/api/platform/security-shield/test-alert",
        cookies=admin_cookie,
        headers={"Origin": "http://localhost:5173"}
    )
    assert admin_resp.status_code == 200
    data = admin_resp.json()
    assert data["status"] in ("MOCK_SENT", "SENT")
    assert data["recipient"] == "vajra.techworks@gmail.com"
    assert data["is_synthetic"] is True
    assert data["incident_id"].startswith("syn_test_")

    # 4. Outbox contains the ACCESS_UNAUTHORIZED_ADMIN event from step 2, but NOT the synthetic alert
    outbox_resp = client.get("/api/platform/security-shield/outbox", cookies=admin_cookie)
    assert outbox_resp.status_code == 200
    outbox_data = outbox_resp.json()
    assert outbox_data["total_count"] == 1
    assert "Privileged Platform Admin" in outbox_data["items"][0]["subject"] or "HIGH" in outbox_data["items"][0]["subject"]

    # 5. When SMTP credentials are unconfigured and mock transport is disabled
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("SMTP_HOST", raising=False)
        mp.delenv("SMTP_USER", raising=False)
        mp.delenv("SMTP_PASSWORD", raising=False)
        mp.setenv("MOCK_EMAIL_TRANSPORT", "false")
        mailer = AlertMailer()
        res = mailer.send_synthetic_test_alert(initiated_by="admin@platform.vraja")
        assert res["status"] == "NOT CONFIGURED"
        assert res["recipient"] == "vajra.techworks@gmail.com"


# ==============================================================================
# TASK 5: INTEGRITY MONITORING API ENDPOINT
# ==============================================================================
def test_task5_integrity_api_endpoint(a6_5_env):
    """Verify platform admin integrity check endpoint."""
    client = TestClient(app)
    admin_cookie = {OWNER_COOKIE: a6_5_env["admin_token"]}

    resp = client.get("/api/platform/security-shield/integrity", cookies=admin_cookie)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"]["is_healthy"] is True
    assert data["database"]["structural_check"] == "ok"
    assert len(data["database"]["schema_hash"]) == 64
    assert data["target_alert_recipient"] == "vajra.techworks@gmail.com"


# ==============================================================================
# TASK 6: PRODUCTION DATABASE READ-ONLY ISOLATION & HASH STABILITY
# ==============================================================================
def test_task6_production_db_isolation_and_safety_guards():
    """Verify production database hash stability and safety guards."""
    prod_db = REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"
    assert prod_db.exists()
    computed_hash = compute_file_sha256(prod_db).upper()
    assert computed_hash == PROD_DB_HASH, (
        f"Production database hash modified! Expected {PROD_DB_HASH}, got {computed_hash}"
    )

    # Product B quarantine verification
    prod_b_dir = REPO_ROOT / "Digital_Card"
    assert prod_b_dir.exists()
