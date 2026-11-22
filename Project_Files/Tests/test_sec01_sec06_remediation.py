"""
VRAJA AI — Product A Security Remediation Test Suite (Phase A5.0.29)

Validates complete remediation of:
- SEC-01: Strict Google Review URL validation (Open Redirect / Stored XSS prevention)
- SEC-06: Elimination of unconditional legacy database DDL during staging/production application startup
"""

import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlsplit
import pytest

from backend.app.core.database.storage import ReviewStore
from backend.app.core.tenants.google_reviews import (
    validate_google_review_url,
    is_safe_google_review_url,
    ALLOWED_GOOGLE_REVIEW_HOSTS,
    google_review_manager,
)
from backend.app.schemas import (
    BusinessConfigUpdateRequest,
    TenantOnboardingRequest,
)
from backend.app.api.template_schemas import UpdateBusinessConfigRequest
from scripts.migrate_phase_a5_sessions import apply_review_sessions_ddl
from scripts.migrate_template_subsystem import apply_template_migration, compute_sha256


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Create fully-migrated representative SQLite database
# ─────────────────────────────────────────────────────────────────────────────

def _create_full_migrated_db(db_path: Path) -> None:
    """Creates a temporary SQLite database with all 15 tables and indexes matching production contract."""
    now = time.time()
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("""
            CREATE TABLE tenants (
                id TEXT PRIMARY KEY,
                business_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                platform TEXT NOT NULL DEFAULT 'google',
                review_url TEXT NOT NULL DEFAULT '',
                branch TEXT DEFAULT '',
                category TEXT DEFAULT 'Breakfast & Snacks',
                description TEXT DEFAULT '',
                topics_json TEXT DEFAULT '[]',
                primary_accent TEXT DEFAULT '#f97316',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                domain TEXT DEFAULT '',
                entitlements_json TEXT DEFAULT '["review_manager"]'
            )
        """)
        conn.execute("""
            CREATE TABLE analytics_events (
                event_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload TEXT NOT NULL,
                tenant_id TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE private_tickets (
                ticket_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload TEXT NOT NULL,
                tenant_id TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE preview_analytics_events (
                event_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload TEXT NOT NULL,
                tenant_id TEXT,
                traffic_source TEXT NOT NULL DEFAULT 'preview'
            )
        """)
        conn.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                is_platform_admin INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE tenant_memberships (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'manager',
                created_at REAL NOT NULL,
                UNIQUE(user_id, tenant_id)
            )
        """)
        conn.execute("""
            CREATE TABLE sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                active_tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                revoked_at REAL,
                ip_address TEXT DEFAULT '',
                user_agent TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE business_profiles (
                tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                tagline TEXT DEFAULT '',
                phone_number TEXT DEFAULT '',
                website_url TEXT DEFAULT '',
                address TEXT DEFAULT '',
                map_url TEXT DEFAULT '',
                whatsapp_url TEXT DEFAULT '',
                instagram_url TEXT DEFAULT '',
                facebook_url TEXT DEFAULT '',
                youtube_url TEXT DEFAULT '',
                logo_path TEXT DEFAULT '',
                cover_image_path TEXT DEFAULT '',
                custom_links_json TEXT DEFAULT '[]',
                is_published INTEGER NOT NULL DEFAULT 0,
                show_review_button INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                display_name TEXT DEFAULT '',
                category TEXT DEFAULT '',
                opening_hours TEXT DEFAULT '',
                welcome_message TEXT DEFAULT '',
                email TEXT DEFAULT '',
                whatsapp_group_url TEXT DEFAULT '',
                background_preset TEXT DEFAULT '',
                overlay_opacity REAL DEFAULT 0.75,
                primary_accent TEXT DEFAULT '#078BFF',
                branch_name TEXT DEFAULT '',
                description TEXT DEFAULT '',
                brand_accent TEXT DEFAULT NULL,
                timezone TEXT DEFAULT 'Asia/Kolkata'
            )
        """)
        conn.execute("""
            CREATE TABLE tenant_documents (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                document_type TEXT NOT NULL DEFAULT 'food_menu',
                display_name TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                mime_type TEXT NOT NULL DEFAULT 'application/pdf',
                sha256_hash TEXT NOT NULL,
                is_published INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memberships_user ON tenant_memberships(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON tenant_memberships(tenant_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_business_profiles_published ON business_profiles(is_published)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_documents_tenant ON tenant_documents(tenant_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_documents_published ON tenant_documents(is_published)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_tenant_created ON analytics_events(tenant_id, created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_tenant_created ON private_tickets(tenant_id, created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_preview_events_tenant_created ON preview_analytics_events(tenant_id, created_at DESC)")

        # Seed sample tenant
        conn.execute(
            "INSERT INTO tenants (id, business_name, status, review_url, created_at, updated_at) "
            "VALUES ('default_business', 'Nasta Ghar', 'active', 'https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro', ?, ?)",
            (now, now)
        )
        conn.execute(
            "INSERT INTO tenants (id, business_name, status, review_url, created_at, updated_at) "
            "VALUES ('test_cafe', 'Test Cafe', 'active', 'https://g.page/r/test-cafe/review', ?, ?)",
            (now, now)
        )
        # Apply review_sessions table and indexes
        apply_review_sessions_ddl(conn)
        # Apply 5 template tables and indexes
        apply_template_migration(conn)
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# SEC-01 TESTS: STRICT GOOGLE REVIEW URL VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

class TestSec01GoogleReviewUrlValidation:
    """Comprehensive test cases for SEC-01 remediation."""

    def test_valid_https_google_review_urls_accepted(self):
        """Standard legitimate Google review destinations are accepted."""
        valid_urls = [
            "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro",
            "https://g.page/r/test-cafe/review",
            "https://maps.google.com/?cid=123456789",
            "https://www.google.com/maps/place/Nasta+Ghar",
            "https://google.com/maps/reviews",
            "https://maps.app.goo.gl/abc123xyz",
            "https://goo.gl/maps/123",
        ]
        for url in valid_urls:
            assert validate_google_review_url(url) == url
            assert is_safe_google_review_url(url) is True

    def test_nastaghar_actual_url_format_preserved(self):
        """The authoritative NastaGhar Google Review URL format is accepted."""
        nastaghar_url = "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro"
        assert validate_google_review_url(nastaghar_url) == nastaghar_url
        assert is_safe_google_review_url(nastaghar_url) is True

    def test_javascript_scheme_rejected(self):
        """XSS attempt via javascript: URI is strictly rejected."""
        malicious = [
            "javascript:alert(1)",
            "JAVASCRIPT:alert(document.cookie)",
            "javascript://search.google.com/local/%0Aalert(1)",
            " javascript:void(0) ",
        ]
        for url in malicious:
            with pytest.raises(ValueError, match="Google review URL must use HTTPS scheme"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_data_scheme_rejected(self):
        """XSS attempt via data: URI is strictly rejected."""
        malicious = [
            "data:text/html,<script>alert(1)</script>",
            "DATA:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        ]
        for url in malicious:
            with pytest.raises(ValueError, match="Google review URL must use HTTPS scheme"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_http_scheme_rejected(self):
        """Insecure plain HTTP is strictly rejected."""
        http_urls = [
            "http://search.google.com/local/writereview?placeid=ChIJ123",
            "http://g.page/r/test-cafe/review",
            "http://maps.google.com",
        ]
        for url in http_urls:
            with pytest.raises(ValueError, match="Google review URL must use HTTPS scheme"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_external_attacker_domains_rejected(self):
        """External non-Google domains are rejected (Open Redirect prevention)."""
        attacker_urls = [
            "https://attacker.com/review",
            "https://evil.com/phishing",
            "https://facebook.com/reviews",
            "https://example.com/fake-google",
            "https://bing.com/maps",
        ]
        for url in attacker_urls:
            with pytest.raises(ValueError, match="Invalid Google review URL domain"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_lookalike_and_deceptive_domains_rejected(self):
        """Subdomain bypasses and typo-squatted lookalike domains are rejected."""
        deceptive_urls = [
            "https://search.google.com.attacker.com/review",
            "https://g.page.evil.com/r/test",
            "https://evil-google.com/maps",
            "https://google.com.fakedomain.org",
            "https://attacker.com/search.google.com",
            "https://g-page.com/review",
        ]
        for url in deceptive_urls:
            with pytest.raises(ValueError, match="Invalid Google review URL domain"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_credentials_in_url_rejected(self):
        """URLs containing embedded user credentials are rejected."""
        credential_urls = [
            "https://user:pass@search.google.com/local",
            "https://admin@g.page/r/test",
            "https://victim:secret@maps.google.com/",
        ]
        for url in credential_urls:
            with pytest.raises(ValueError, match="must not contain user credentials"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_custom_ports_rejected(self):
        """Non-standard ports on legitimate hostnames are rejected."""
        custom_port_urls = [
            "https://search.google.com:8080/review",
            "https://g.page:444/r/test",
            "https://maps.google.com:9000/",
        ]
        for url in custom_port_urls:
            with pytest.raises(ValueError, match="must not use custom port"):
                validate_google_review_url(url)
            assert is_safe_google_review_url(url) is False

    def test_malformed_urls_and_empty_values_rejected(self):
        """Empty or invalid inputs are rejected when required."""
        for val in ["", "   ", None, "not_a_url", "https://", "://invalid"]:
            with pytest.raises(ValueError):
                validate_google_review_url(val, allow_empty=False)

    def test_pydantic_schema_ingress_rejection(self):
        """Pydantic schemas enforce SEC-01 validation at API ingress."""
        # 1. BusinessConfigUpdateRequest (strict required)
        with pytest.raises(ValueError):
            BusinessConfigUpdateRequest(google_review_url="javascript:alert(1)")
        with pytest.raises(ValueError):
            BusinessConfigUpdateRequest(google_review_url="https://attacker.com")
        with pytest.raises(ValueError):
            BusinessConfigUpdateRequest(google_review_url="")

        valid_req = BusinessConfigUpdateRequest(
            google_review_url="https://search.google.com/local/writereview?placeid=ChIJ123"
        )
        assert valid_req.google_review_url == "https://search.google.com/local/writereview?placeid=ChIJ123"

        # 2. TenantOnboardingRequest (optional review_url)
        with pytest.raises(ValueError):
            TenantOnboardingRequest(
                tenant_id="new_cafe",
                business_name="New Cafe",
                owner_email="owner@newcafe.com",
                owner_password="SuperSecretPassword123!",
                review_url="https://evil.com"
            )
        valid_onb = TenantOnboardingRequest(
            tenant_id="new_cafe",
            business_name="New Cafe",
            owner_email="owner@newcafe.com",
            owner_password="SuperSecretPassword123!",
            review_url="https://g.page/r/new-cafe/review"
        )
        assert valid_onb.review_url == "https://g.page/r/new-cafe/review"

        # 3. UpdateBusinessConfigRequest
        with pytest.raises(ValueError):
            UpdateBusinessConfigRequest(google_review_url="javascript:alert(1)")
        valid_tpl = UpdateBusinessConfigRequest(
            google_review_url="https://maps.google.com/test"
        )
        assert valid_tpl.google_review_url == "https://maps.google.com/test"

    def test_invalid_stored_url_neutralized_in_egress(self, tmp_path, monkeypatch):
        """When an invalid legacy URL exists in the database, egress neutralizes it to safe default."""
        db_file = tmp_path / "unsafe_db.sqlite3"
        _create_full_migrated_db(db_file)

        # Injected legacy malicious URL directly into SQLite
        with sqlite3.connect(str(db_file)) as conn:
            conn.execute(
                "UPDATE tenants SET review_url = 'javascript:alert(document.domain)' WHERE id = 'test_cafe'"
            )
            conn.commit()

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        monkeypatch.setenv("ENVIRONMENT", "test")

        info = google_review_manager.get_review_url("test_cafe")
        assert info is not None
        # Neutralized to safe default Google Maps URL, not the stored javascript payload
        assert info["review_url"] == "https://maps.google.com"
        assert info["is_configured"] is False

    def test_valid_url_preserves_customer_journey(self, tmp_path, monkeypatch):
        """Valid Google review URL is preserved unchanged across full resolution path."""
        db_file = tmp_path / "valid_db.sqlite3"
        _create_full_migrated_db(db_file)

        monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
        monkeypatch.setenv("ENVIRONMENT", "test")

        info = google_review_manager.get_review_url("default_business")
        assert info is not None
        assert info["review_url"] == "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro"
        assert info["is_configured"] is True


# ─────────────────────────────────────────────────────────────────────────────
# SEC-06 TESTS: ELIMINATE PRODUCTION / STAGING STARTUP DDL
# ─────────────────────────────────────────────────────────────────────────────

class TestSec06StartupDdlElimination:
    """Comprehensive test cases for SEC-06 remediation."""

    def test_dev_test_initialization_still_works(self, tmp_path, monkeypatch):
        """Development and test initialization auto-creates database schema for ephemeral test DBs."""
        db_file = tmp_path / "test_ephemeral.sqlite3"
        monkeypatch.setenv("ENVIRONMENT", "test")

        store = ReviewStore(database_path=str(db_file))
        assert store is not None

        # Verify all 15 tables were initialized
        with sqlite3.connect(str(db_file)) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            assert "tenants" in tables
            assert "analytics_events" in tables
            assert "private_tickets" in tables
            assert "preview_analytics_events" in tables
            assert "review_sessions" in tables
            assert "business_profiles" in tables
            assert "tenant_documents" in tables
            assert "industries" in tables
            assert "templates" in tables
            assert "template_versions" in tables
            assert "business_configurations" in tables
            assert "business_template_assignments" in tables

    def test_staging_initialization_performs_no_ddl(self, tmp_path, monkeypatch):
        """Staging startup against a fully migrated database executes zero DDL and produces zero file mutations."""
        db_file = tmp_path / "staging_zero_ddl.sqlite3"
        _create_full_migrated_db(db_file)

        # Checkpoint WAL to flush all transactions to the main DB file
        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        pre_sha = compute_sha256(db_file)
        pre_size = db_file.stat().st_size

        monkeypatch.setenv("ENVIRONMENT", "staging")
        store = ReviewStore(database_path=str(db_file))
        assert store is not None

        post_sha = compute_sha256(db_file)
        post_size = db_file.stat().st_size

        assert pre_sha == post_sha, "Staging startup modified database file! Startup DDL must be strictly zero."
        assert pre_size == post_size

    def test_production_initialization_performs_no_ddl(self, tmp_path, monkeypatch):
        """Production startup against a fully migrated database executes zero DDL and produces zero file mutations."""
        db_file = tmp_path / "prod_zero_ddl.sqlite3"
        _create_full_migrated_db(db_file)

        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        pre_sha = compute_sha256(db_file)
        pre_size = db_file.stat().st_size

        monkeypatch.setenv("ENVIRONMENT", "production")
        store = ReviewStore(database_path=str(db_file))
        assert store is not None

        post_sha = compute_sha256(db_file)
        post_size = db_file.stat().st_size

        assert pre_sha == post_sha, "Production startup modified database file! Startup DDL must be strictly zero."
        assert pre_size == post_size

    def test_staging_missing_table_fails_closed_without_ddl(self, tmp_path, monkeypatch):
        """When any contractual table is missing in staging, startup fails closed and creates nothing."""
        db_file = tmp_path / "staging_missing_tbl.sqlite3"
        _create_full_migrated_db(db_file)

        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("DROP TABLE private_tickets")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        pre_sha = compute_sha256(db_file)

        monkeypatch.setenv("ENVIRONMENT", "staging")
        with pytest.raises(RuntimeError, match="missing required table 'private_tickets'"):
            ReviewStore(database_path=str(db_file))

        # Assert no table was recreated and file is unmodified
        post_sha = compute_sha256(db_file)
        assert pre_sha == post_sha

    def test_production_missing_table_fails_closed_without_ddl(self, tmp_path, monkeypatch):
        """When any contractual table is missing in production, startup fails closed and creates nothing."""
        db_file = tmp_path / "prod_missing_tbl.sqlite3"
        _create_full_migrated_db(db_file)

        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("DROP TABLE business_profiles")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        pre_sha = compute_sha256(db_file)

        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(RuntimeError, match="missing required table 'business_profiles'"):
            ReviewStore(database_path=str(db_file))

        post_sha = compute_sha256(db_file)
        assert pre_sha == post_sha

    def test_production_missing_column_fails_closed(self, tmp_path, monkeypatch):
        """When a required column is missing from a contractual table, production startup fails closed."""
        db_file = tmp_path / "prod_missing_col.sqlite3"
        _create_full_migrated_db(db_file)

        with sqlite3.connect(str(db_file)) as conn:
            # Recreate users table missing is_platform_admin column
            conn.execute("DROP TABLE users")
            conn.execute("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(RuntimeError, match=r"Incompatible 'users' table schema .*missing: \{'is_platform_admin'\}"):
            ReviewStore(database_path=str(db_file))

    def test_production_unexpected_column_fails_closed(self, tmp_path, monkeypatch):
        """When an unexpected extra column exists on a contractual table, production startup fails closed."""
        db_file = tmp_path / "prod_extra_col.sqlite3"
        _create_full_migrated_db(db_file)

        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("ALTER TABLE tenants ADD COLUMN rogue_column TEXT DEFAULT ''")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(RuntimeError, match=r"Incompatible 'tenants' table schema .*unexpected: \{'rogue_column'\}"):
            ReviewStore(database_path=str(db_file))

    def test_production_missing_index_fails_closed(self, tmp_path, monkeypatch):
        """When a required composite or lookup index is missing, production startup fails closed."""
        db_file = tmp_path / "prod_missing_idx.sqlite3"
        _create_full_migrated_db(db_file)

        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("DROP INDEX idx_analytics_tenant_created")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(RuntimeError, match="missing required base indexes .*idx_analytics_tenant_created"):
            ReviewStore(database_path=str(db_file))

    def test_direct_reviewstore_construction_enforces_restrictions(self, tmp_path, monkeypatch):
        """Direct ReviewStore(path) instantiation without API framework enforces environment restrictions."""
        db_file = tmp_path / "direct_unmigrated.sqlite3"
        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("CREATE TABLE dummy (id INT)")
            conn.commit()

        monkeypatch.setenv("ENVIRONMENT", "production")
        # Direct construction must raise RuntimeError, NOT create tables
        with pytest.raises(RuntimeError):
            ReviewStore(database_path=str(db_file))

        with sqlite3.connect(str(db_file)) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            assert tables == {"dummy"}
