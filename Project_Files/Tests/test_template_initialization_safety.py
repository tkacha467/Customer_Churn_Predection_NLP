"""
Automated Test Suite for Product A: Strict Template Subsystem Schema Validation & Migration Safety.
Verifies:
1. Exact valid schema acceptance in production/staging.
2. Wrong declared type rejection (fail closed).
3. Wrong nullability/default rejection (fail closed).
4. Wrong primary key rejection (fail closed).
5. Missing unique constraint rejection (fail closed).
6. Missing or incorrect foreign key rejection (fail closed).
7. Missing index rejection (fail closed).
8. Incorrect index column order or sort direction rejection (fail closed).
9. Unexpected column rejection (fail closed).
10. Incompatible existing partial schema rejection before migration.
11. Dry-run checksum invariance.
12. Transaction rollback after injected failure.
13. Backup cleanup and collision preservation.
14. Idempotent migration on compatible schema.
15. Preservation of custom configurations and assignments.
"""

import json
import os
import sqlite3
import stat
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.core.database.storage import ReviewStore
from backend.app.core.database.template_storage import (
    TEMPLATE_SCHEMA_CONTRACT,
    init_template_schema,
    validate_strict_template_schema,
    validate_strict_template_table,
)
from scripts.migrate_phase_a5_sessions import apply_review_sessions_ddl
from scripts.migrate_template_subsystem import (
    PROD_DB_PATH,
    apply_template_migration,
    compute_sha256,
    create_backup,
    run_template_migration,
    validate_existing_template_schema,
    verify_template_schema,
)


def _create_minimal_db(db_path: Path) -> None:
    """Helper creating a minimal SQLite database with default_business tenant and base schema."""
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

        conn.execute("""
            INSERT INTO tenants (id, business_name, status, created_at, updated_at)
            VALUES ('default_business', 'Nasta Ghar', 'active', ?, ?)
        """, (now, now))
        apply_review_sessions_ddl(conn)
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME STRICT VALIDATOR TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_template_initialization_in_test_env(tmp_path, monkeypatch):
    """In test environment, ReviewStore startup auto-creates template schema and default seeds."""
    db_file = tmp_path / "test_env.sqlite3"
    _create_minimal_db(db_file)

    monkeypatch.setenv("ENVIRONMENT", "test")
    store = ReviewStore(database_path=str(db_file))

    with sqlite3.connect(str(db_file)) as conn:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for expected_tbl in TEMPLATE_SCHEMA_CONTRACT.keys():
            assert expected_tbl in tables

        ind_count = conn.execute("SELECT COUNT(*) FROM industries").fetchone()[0]
        assert ind_count >= 4


def test_template_initialization_in_dev_env(tmp_path, monkeypatch):
    """In dev environment, ReviewStore startup auto-creates template schema and default seeds."""
    db_file = tmp_path / "dev_env.sqlite3"
    _create_minimal_db(db_file)

    monkeypatch.setenv("ENVIRONMENT", "dev")
    store = ReviewStore(database_path=str(db_file))

    with sqlite3.connect(str(db_file)) as conn:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for expected_tbl in TEMPLATE_SCHEMA_CONTRACT.keys():
            assert expected_tbl in tables


def test_staging_fails_closed_when_template_tables_missing(tmp_path, monkeypatch):
    """In staging environment, missing template tables cause startup to fail closed."""
    db_file = tmp_path / "staging_missing.sqlite3"
    _create_minimal_db(db_file)

    monkeypatch.setenv("ENVIRONMENT", "staging")
    with pytest.raises(RuntimeError, match="missing required template table 'industries'"):
        ReviewStore(database_path=str(db_file))


def test_production_fails_closed_when_template_tables_missing(tmp_path, monkeypatch):
    """In production environment, missing template tables cause startup to fail closed."""
    db_file = tmp_path / "prod_missing.sqlite3"
    _create_minimal_db(db_file)

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="missing required template table 'industries'"):
        ReviewStore(database_path=str(db_file))


def test_production_startup_read_only_passes_when_migrated(tmp_path, monkeypatch):
    """In production, when database is properly migrated, startup succeeds and performs NO writes."""
    db_file = tmp_path / "prod_valid.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.commit()

    pre_sha = compute_sha256(db_file)

    monkeypatch.setenv("ENVIRONMENT", "production")
    store = ReviewStore(database_path=str(db_file))
    assert store is not None

    post_sha = compute_sha256(db_file)
    assert pre_sha == post_sha, "Production startup modified target database unexpectedly!"


def test_strict_validator_wrong_declared_type_rejection(tmp_path, monkeypatch):
    """Declared column type mismatch (e.g. INTEGER instead of TEXT for id) fails closed."""
    db_file = tmp_path / "wrong_type.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE industries")
        # Incompatible declared type: id INTEGER instead of TEXT
        conn.execute("""
            CREATE TABLE industries (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🏢',
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'industries.id' declared type .* expected 'TEXT', got 'INTEGER'"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_wrong_nullability_rejection(tmp_path, monkeypatch):
    """Wrong NOT NULL constraint (e.g. nullable name) fails closed."""
    db_file = tmp_path / "wrong_notnull.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE industries")
        # Incompatible: name lacks NOT NULL
        conn.execute("""
            CREATE TABLE industries (
                id TEXT PRIMARY KEY,
                name TEXT,
                slug TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🏢',
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'industries.name' NOT NULL constraint .* expected notnull=1, got 0"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_wrong_default_rejection(tmp_path, monkeypatch):
    """Wrong default value (e.g. status default 'pending' instead of 'active') fails closed."""
    db_file = tmp_path / "wrong_default.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE industries")
        # Incompatible default: 'pending' instead of 'active'
        conn.execute("""
            CREATE TABLE industries (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🏢',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'industries.status' default value"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_wrong_pk_rejection(tmp_path, monkeypatch):
    """Wrong primary key fails closed."""
    db_file = tmp_path / "wrong_pk.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE industries")
        # Incompatible PK: slug is PK instead of id
        conn.execute("""
            CREATE TABLE industries (
                id TEXT,
                name TEXT NOT NULL,
                slug TEXT PRIMARY KEY,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🏢',
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'industries.id' primary key flag .* expected pk=1, got 0"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_missing_unique_constraint_rejection(tmp_path, monkeypatch):
    """Missing unique constraint fails closed."""
    db_file = tmp_path / "missing_unique.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE industries")
        # Incompatible: slug lacks UNIQUE constraint
        conn.execute("""
            CREATE TABLE industries (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🏢',
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'industries' unique constraints .* expected unique constraints on .*slug"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_missing_or_incorrect_foreign_key_rejection(tmp_path, monkeypatch):
    """Missing or incorrect foreign key action fails closed."""
    db_file = tmp_path / "wrong_fk.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE templates")
        # Incompatible FK: ON DELETE SET NULL instead of CASCADE
        conn.execute("""
            CREATE TABLE templates (
                id TEXT PRIMARY KEY,
                industry_id TEXT NOT NULL REFERENCES industries(id) ON DELETE SET NULL,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_templates_industry ON templates(industry_id)")
        conn.execute("CREATE INDEX idx_templates_slug ON templates(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'templates' foreign keys"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_missing_index_rejection(tmp_path, monkeypatch):
    """Missing user index fails closed."""
    db_file = tmp_path / "missing_idx.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP INDEX idx_industries_slug")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="missing required index 'idx_industries_slug' on 'industries'"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_incorrect_index_columns_or_direction_rejection(tmp_path, monkeypatch):
    """Index with wrong column or sort direction (DESC instead of ASC) fails closed."""
    db_file = tmp_path / "wrong_idx_dir.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP INDEX idx_industries_slug")
        # Incompatible direction: DESC (1) instead of ASC (0)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug DESC)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible index 'idx_industries_slug' on 'industries'"):
        ReviewStore(database_path=str(db_file))


def test_strict_validator_unexpected_column_rejection(tmp_path, monkeypatch):
    """Table containing unexpected extra columns fails closed."""
    db_file = tmp_path / "unexpected_col.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        apply_template_migration(conn)
        conn.execute("DROP TABLE industries")
        conn.execute("""
            CREATE TABLE industries (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🏢',
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                extra_bogus_col TEXT DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX idx_industries_slug ON industries(slug)")
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'industries' table schema .* expected 8 columns, got 9"):
        ReviewStore(database_path=str(db_file))


# ─────────────────────────────────────────────────────────────────────────────
# MIGRATION RUNNER SAFETY & PRE-CHECK TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_migration_runner_incompatible_existing_schema_abort(tmp_path):
    """Existing table with incompatible schema causes migration runner to abort with ValueError before mutation."""
    db_file = tmp_path / "incompatible_runner.sqlite3"
    _create_minimal_db(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        # Create incompatible industries table
        conn.execute("""
            CREATE TABLE industries (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()

    pre_sha = compute_sha256(db_file)

    with pytest.raises(ValueError, match="Incompatible existing template table 'industries'"):
        run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")

    # Target database was NOT modified and no backup was created
    assert compute_sha256(db_file) == pre_sha
    assert list((tmp_path / "backups").glob("*.bak")) == []


def test_template_migration_runner_fresh_db(tmp_path):
    """Dedicated template migration script creates tables, indexes, and seeds defaults on fresh DB."""
    db_file = tmp_path / "fresh_migrate.sqlite3"
    _create_minimal_db(db_file)

    res = run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res["status"] == "success"
    assert res["mode"] == "apply"
    assert Path(res["backup_path"]).exists()

    with sqlite3.connect(str(db_file)) as conn:
        verification = verify_template_schema(conn, str(db_file))
        assert verification["integrity"] == "ok"


def test_template_migration_runner_idempotent(tmp_path):
    """Running template migration multiple times is completely idempotent."""
    db_file = tmp_path / "idempotent_migrate.sqlite3"
    _create_minimal_db(db_file)

    res1 = run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res1["status"] == "success"

    res2 = run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res2["status"] == "success"


def test_template_migration_runner_dry_run(tmp_path):
    """Template migration dry-run verifies schema and rolls back without touching database file."""
    db_file = tmp_path / "dry_run_migrate.sqlite3"
    _create_minimal_db(db_file)

    pre_sha = compute_sha256(db_file)
    res = run_template_migration(str(db_file), dry_run=True)
    assert res["status"] == "success"
    assert res["mode"] == "dry_run"
    assert res["file_modified"] is False
    assert compute_sha256(db_file) == pre_sha


def test_template_migration_production_protection():
    """Targeting the production database without --confirm-production raises PermissionError."""
    with pytest.raises(PermissionError, match="PROTECTED PRODUCTION DATABASE DETECTED"):
        run_template_migration(str(PROD_DB_PATH), dry_run=False, confirm_production=False)


def test_template_migration_preserves_customizations(tmp_path):
    """Template migration does not overwrite existing custom business configurations or assignments."""
    db_file = tmp_path / "custom_preserve.sqlite3"
    _create_minimal_db(db_file)

    # First run to set up base tables
    run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")

    # Insert customized configuration
    custom_accent = "#FF00FF"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute(
            "UPDATE business_configurations SET primary_accent = ? WHERE business_id = 'default_business'",
            (custom_accent,),
        )
        conn.commit()

    # Re-run migration
    run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")

    with sqlite3.connect(str(db_file)) as conn:
        row = conn.execute(
            "SELECT primary_accent FROM business_configurations WHERE business_id = 'default_business'"
        ).fetchone()
        assert row[0] == custom_accent, "Migration overwrote custom business configuration!"


def test_template_migration_rollback_on_injected_failure(tmp_path):
    """If an error occurs during apply_template_migration, the transaction rolls back cleanly."""
    db_file = tmp_path / "rollback_test.sqlite3"
    _create_minimal_db(db_file)
    pre_sha = compute_sha256(db_file)

    def broken_apply(conn):
        conn.execute("CREATE TABLE industries (id TEXT PRIMARY KEY)")
        raise RuntimeError("Injected migration failure midway through apply")

    with patch("scripts.migrate_template_subsystem.apply_template_migration", side_effect=broken_apply):
        with pytest.raises(RuntimeError, match="Injected migration failure midway through apply"):
            run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")

    # Database file did not retain partial table
    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "industries" not in tables


def test_template_migration_backup_failure_cleans_up_incomplete_file(tmp_path):
    """If an error occurs during backup, the incomplete backup file is removed."""
    db_file = tmp_path / "backup_fail.sqlite3"
    _create_minimal_db(db_file)
    bdir = tmp_path / "backups"

    orig_connect = sqlite3.connect
    def mock_connect(path_str, *args, **kwargs):
        conn = orig_connect(path_str, *args, **kwargs)
        if str(path_str) == str(db_file):
            class BrokenConn:
                def __init__(self, c): self._c = c
                def __enter__(self): return self
                def __exit__(self, *a): return self._c.__exit__(*a)
                def backup(self, dst, **k): raise OSError("Simulated disk full during backup")
                def __getattr__(self, name): return getattr(self._c, name)
            return BrokenConn(conn)
        return conn

    with patch("sqlite3.connect", side_effect=mock_connect):
        with pytest.raises(OSError, match="Simulated disk full during backup"):
            run_template_migration(str(db_file), dry_run=False, backup_dir=bdir)

    assert list(bdir.glob("*.bak")) == []
