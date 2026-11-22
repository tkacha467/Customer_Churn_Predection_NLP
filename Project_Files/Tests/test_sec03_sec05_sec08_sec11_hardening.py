import json
import os
import stat
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.testclient import TestClient

from backend.app.core.database.storage import ReviewStore, set_secure_file_permissions
from backend.app.main import (
    GENERIC_500_DETAIL,
    app,
    get_allowed_hosts,
)
from Project_Files.Scripts.backup_restore import (
    create_backup,
    get_table_counts,
    restore_backup,
    set_secure_file_permissions as backup_set_secure_permissions,
    verify_backup,
)
from backend.app.core.auth.auth import (
    check_account_login_rate_limit,
    record_login_failure,
    record_login_success,
    reset_rate_limits,
)


# =====================================================================
# SEC-03: SQLite Database File Permissions
# =====================================================================
class TestSec03FilePermissions:
    """Verifies filesystem permission enforcement for SQLite database and backup files."""

    def test_new_database_receives_restrictive_permissions(self, tmp_path, monkeypatch):
        """Newly created SQLite database files in dev/test get restrictive 0600 permissions on POSIX."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        db_file = tmp_path / "new_test.sqlite3"
        assert not db_file.exists()

        store = ReviewStore(database_path=str(db_file))
        assert db_file.exists()

        if os.name == "posix":
            file_stat = db_file.stat()
            file_mode = stat.S_IMODE(file_stat.st_mode)
            # Must be 0600 (read/write by owner only; zero access to group/others)
            assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"

    def test_existing_production_database_not_modified_by_storage_init(self, tmp_path, monkeypatch):
        """Existing database files in staging/production must not have permissions mutated."""
        db_file = tmp_path / "prod_existing.sqlite3"

        # 1. Pre-create database with full schema in test environment
        monkeypatch.setenv("ENVIRONMENT", "test")
        store_init = ReviewStore(database_path=str(db_file))
        assert db_file.exists()

        if os.name == "posix":
            # Set to 0644
            os.chmod(db_file, 0o644)
            assert stat.S_IMODE(db_file.stat().st_mode) == 0o644

        # 2. Switch to production environment and open the existing database
        monkeypatch.setenv("ENVIRONMENT", "production")
        store_prod = ReviewStore(database_path=str(db_file))
        if os.name == "posix":
            # Must remain 0644, proving ReviewStore does not mutate existing production permissions
            assert stat.S_IMODE(db_file.stat().st_mode) == 0o644

    def test_set_secure_file_permissions_handles_non_posix_and_oserror_gracefully(self, tmp_path):
        """Non-POSIX platforms and OS errors are gracefully handled without crashing."""
        test_file = tmp_path / "dummy.txt"
        test_file.write_text("hello")

        # Mock os.name to nt (Windows)
        with patch("os.name", "nt"):
            with patch("os.chmod") as mock_chmod:
                set_secure_file_permissions(test_file)
                mock_chmod.assert_not_called()

        # Mock chmod raising OSError
        if os.name == "posix":
            with patch("os.chmod", side_effect=OSError("Read-only filesystem")):
                # Should not raise
                set_secure_file_permissions(test_file)


# =====================================================================
# SEC-05: TrustedHostMiddleware Configuration
# =====================================================================
class TestSec05TrustedHostValidation:
    """Verifies host validation middleware configuration and enforcement."""

    def test_production_fails_closed_when_allowed_hosts_missing(self, monkeypatch):
        """Production startup fails closed if ALLOWED_HOSTS is missing or empty."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
        with pytest.raises(RuntimeError, match="ALLOWED_HOSTS must be explicitly configured in 'production'"):
            get_allowed_hosts()

    def test_production_fails_closed_when_allowed_hosts_contains_wildcard(self, monkeypatch):
        """Production startup fails closed if ALLOWED_HOSTS contains wildcard '*'."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com,*")
        with pytest.raises(RuntimeError, match="Wildcard '\\*' is strictly prohibited"):
            get_allowed_hosts()

    def test_staging_fails_closed_when_allowed_hosts_missing(self, monkeypatch):
        """Staging startup fails closed if ALLOWED_HOSTS is missing or empty."""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
        with pytest.raises(RuntimeError, match="ALLOWED_HOSTS must be explicitly configured in 'staging'"):
            get_allowed_hosts()

    def test_staging_and_production_accept_configured_hosts(self, monkeypatch):
        """Production and staging accept valid comma-separated lists of hostnames."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ALLOWED_HOSTS", "api.vraja.ai, app.vraja.ai")
        hosts = get_allowed_hosts()
        assert hosts == ["api.vraja.ai", "app.vraja.ai"]

    def test_dev_test_defaults_to_safe_local_hosts(self, monkeypatch):
        """Development and test environments default to safe local/test hostnames."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
        hosts = get_allowed_hosts()
        assert "localhost" in hosts
        assert "127.0.0.1" in hosts
        assert "testserver" in hosts

    def test_runtime_trusted_host_allows_valid_host(self):
        """Requests with trusted host headers pass through successfully."""
        client = TestClient(app)
        # TestClient uses 'testserver' by default
        resp = client.get("/healthz", headers={"Host": "testserver"})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_runtime_untrusted_host_rejected(self):
        """Requests with untrusted or spoofed host headers are rejected with HTTP 400."""
        # Create an isolated test app with strict trusted host middleware
        test_app = FastAPI()
        test_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["trusted.example.com"])

        @test_app.get("/test")
        def endpoint():
            return {"status": "ok"}

        test_client = TestClient(test_app)
        # Untrusted host header
        resp = test_client.get("/test", headers={"Host": "attacker.com"})
        assert resp.status_code == 400
        assert "Invalid host header" in resp.text

        # Trusted host header
        resp_ok = test_client.get("/test", headers={"Host": "trusted.example.com"})
        assert resp_ok.status_code == 200


# =====================================================================
# SEC-08: Safe HTTP 500 Responses (No Exception/Path/SQL Leaks)
# =====================================================================
class TestSec08Safe500Responses:
    """Verifies that internal exceptions, file paths, and SQL queries do not leak in HTTP 500 responses."""

    def test_unhandled_exception_returns_generic_500(self):
        """Unhandled Python exceptions return a stable, generic message without tracebacks."""
        test_app = FastAPI()
        test_app.add_exception_handler(Exception, app.exception_handlers[Exception])

        @test_app.get("/fail-unhandled")
        def fail():
            # Deliberate division by zero with internal details
            x = 1 / 0
            return {"x": x}

        client = TestClient(test_app, raise_server_exceptions=False)
        resp = client.get("/fail-unhandled")
        assert resp.status_code == 500
        data = resp.json()
        assert data["detail"] == GENERIC_500_DETAIL
        # Ensure no traceback or internal keywords leaked
        assert "ZeroDivisionError" not in resp.text
        assert "Traceback" not in resp.text
        assert "line " not in resp.text

    def test_http_exception_with_leaky_detail_sanitized(self):
        """HTTPException(500) containing SQL queries or filesystem paths is sanitized."""
        test_app = FastAPI()
        test_app.add_exception_handler(HTTPException, app.exception_handlers[HTTPException])

        @test_app.get("/fail-leaky-500")
        def fail_leaky():
            raise HTTPException(
                status_code=500,
                detail="OperationalError: no such table: /var/secrets/db.sqlite3 SELECT * FROM users;"
            )

        client = TestClient(test_app, raise_server_exceptions=False)
        resp = client.get("/fail-leaky-500")
        assert resp.status_code == 500
        data = resp.json()
        assert data["detail"] == GENERIC_500_DETAIL
        assert "/var/secrets" not in resp.text
        assert "SELECT" not in resp.text
        assert "OperationalError" not in resp.text

    def test_client_safe_4xx_errors_preserved_without_alteration(self):
        """Standard 4xx errors (e.g. 400, 401, 403, 404, 422, 429) pass through with original detail."""
        test_app = FastAPI()
        test_app.add_exception_handler(HTTPException, app.exception_handlers[HTTPException])

        @test_app.get("/client-404")
        def client_err():
            raise HTTPException(status_code=404, detail="Specific item not found.")

        client = TestClient(test_app)
        resp = client.get("/client-404")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Specific item not found."


# =====================================================================
# SEC-11: Backup Manifest Table Count & Restore Compatibility
# =====================================================================
class TestSec11BackupManifestTableCount:
    """Verifies that database table count is accurately recorded and verified in backup manifests."""

    def test_backup_manifest_records_table_count(self, tmp_path, monkeypatch):
        """create_backup writes table_count and database_table_count in manifest.json."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        db_file = tmp_path / "reviews.sqlite3"
        store = ReviewStore(database_path=str(db_file))

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        backup_dir = tmp_path / "backup_out"

        created = create_backup(dest_dir=backup_dir)
        manifest_path = created / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert "table_count" in manifest
        assert "database_table_count" in manifest
        assert isinstance(manifest["table_count"], int)
        assert manifest["table_count"] > 0
        assert manifest["table_count"] == len(manifest["table_counts"])
        assert manifest["database_table_count"] == manifest["table_count"]

        # Verify permissions on backup files (SEC-03 check)
        if os.name == "posix":
            backup_db = created / "reviews.sqlite3"
            assert stat.S_IMODE(backup_db.stat().st_mode) == 0o600
            assert stat.S_IMODE(manifest_path.stat().st_mode) == 0o600

    def test_verify_backup_with_matching_table_count(self, tmp_path, monkeypatch):
        """verify_backup passes when manifest table_count matches the database."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        db_file = tmp_path / "reviews.sqlite3"
        store = ReviewStore(database_path=str(db_file))

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        backup_dir = tmp_path / "backup_out"
        create_backup(dest_dir=backup_dir)

        assert verify_backup(backup_dir) is True

    def test_verify_backup_handles_legacy_manifest_without_table_count(self, tmp_path, monkeypatch):
        """verify_backup gracefully accepts legacy manifests that omit table_count."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        db_file = tmp_path / "reviews.sqlite3"
        store = ReviewStore(database_path=str(db_file))

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        backup_dir = tmp_path / "backup_out"
        create_backup(dest_dir=backup_dir)

        # Simulate legacy manifest by deleting table_count and database_table_count
        manifest_path = backup_dir / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        m.pop("table_count", None)
        m.pop("database_table_count", None)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)

        # Must still pass verification
        assert verify_backup(backup_dir) is True

    def test_verify_backup_fails_when_table_count_mismatched(self, tmp_path, monkeypatch):
        """verify_backup fails if the manifest table_count differs from actual tables."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        db_file = tmp_path / "reviews.sqlite3"
        store = ReviewStore(database_path=str(db_file))

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        backup_dir = tmp_path / "backup_out"
        create_backup(dest_dir=backup_dir)

        # Tamper with table_count in manifest
        manifest_path = backup_dir / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        m["table_count"] = 9999
        m["database_table_count"] = 9999
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)

        assert verify_backup(backup_dir) is False

    def test_restore_backup_restores_and_applies_secure_permissions(self, tmp_path, monkeypatch):
        """restore_backup restores data and ensures restrictive 0600 permissions on restored files."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        db_file = tmp_path / "reviews.sqlite3"
        store = ReviewStore(database_path=str(db_file))

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        backup_dir = tmp_path / "backup_out"
        create_backup(dest_dir=backup_dir)

        restore_dest = tmp_path / "restored_isolated"
        ok = restore_backup(backup_dir, restore_dest)
        assert ok is True

        restored_db = restore_dest / "reviews.sqlite3"
        assert restored_db.exists()
        if os.name == "posix":
            assert stat.S_IMODE(restored_db.stat().st_mode) == 0o600


# =====================================================================
# Additional SEC-04 Regression & DoS Risk Analysis Check
# =====================================================================
class TestSec04DosRiskRegressionCheck:
    """
    Tests whether an unauthenticated external attacker can deliberately trigger
    repeated temporary lockouts for a legitimate user identity (account lockout DoS).
    """

    def setup_method(self):
        reset_rate_limits()

    def teardown_method(self):
        reset_rate_limits()

    def test_attacker_can_trigger_temporary_account_lockout_for_victim(self):
        """
        Demonstrates the account-lockout DoS vector:
        An attacker knowing only victim's email can send 5 bad passwords,
        causing a temporary 30-second lockout that also blocks the legitimate user.
        """
        victim_email = "owner@victim-bistro.com"
        t0 = 1000.0

        # Legitimate user is initially allowed
        allowed, wait = check_account_login_rate_limit(victim_email, now=t0)
        assert allowed is True
        assert wait == 0

        # Attacker sends 5 bad passwords
        for _ in range(5):
            record_login_failure(victim_email, now=t0)

        # Account is now locked out for 30s
        allowed, wait = check_account_login_rate_limit(victim_email, now=t0)
        assert allowed is False
        assert wait == 30

        # Even with correct password, legitimate user would be blocked during the 30s
        allowed_victim, _ = check_account_login_rate_limit(victim_email, now=t0 + 10.0)
        assert allowed_victim is False

        # After cooldown expires (31s later), legitimate user can attempt login
        t_after = t0 + 31.0
        allowed_after, wait_after = check_account_login_rate_limit(victim_email, now=t_after)
        assert allowed_after is True
        assert wait_after == 0

        # Legitimate user logs in successfully -> clears all failure history
        record_login_success(victim_email)

        # Account remains cleanly unlocked
        allowed_clean, _ = check_account_login_rate_limit(victim_email, now=t_after + 1.0)
        assert allowed_clean is True
