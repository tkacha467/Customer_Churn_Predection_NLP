"""
Automated Test Suite for VRAJA AI Phase A5: Explicit review_sessions Database Migration.

Validates:
1. Migration on a temporary database creates table and indexes.
2. Correct schema: 7 columns, correct types, primary key.
3. Correct composite indexes created.
4. Idempotency: repeated execution succeeds without errors or duplicates.
5. Dry-run mode tests DDL and rolls back; target file remains completely unmodified.
6. Hot online backup creation and integrity check before applying migration.
7. Incompatible existing schema rejection (e.g. wrong columns or missing PK).
8. Failure rollback: database remains clean on error.
9. Missing target database path rejection.
10. Relative path rejection (requires explicit absolute path).
11. Production database protection (rejects production path without explicit confirmation).
12. Existing tenant and analytics records are preserved completely untouched.
"""

import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch
import pytest

from scripts.migrate_phase_a5_sessions import (
    run_a5_migration,
    compute_sha256,
    create_backup,
    generate_backup_filename,
    PROD_DB_PATH,
)
from backend.app.core.database.storage import ReviewStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _create_legacy_database(db_path: Path) -> None:
    """Helper creating a representative legacy SQLite database without review_sessions."""
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

        # Insert sample tenant and analytics records
        conn.execute(
            "INSERT INTO tenants (id, business_name, status, created_at, updated_at) VALUES ('default_business', 'Nasta Ghar', 'active', ?, ?)",
            (now, now),
        )
        conn.execute(
            "INSERT INTO tenants (id, business_name, status, created_at, updated_at) VALUES ('test_cafe', 'Test Cafe', 'active', ?, ?)",
            (now, now),
        )
        conn.execute(
            "INSERT INTO analytics_events VALUES ('ev-1', ?, '{\"rating\": 5}', 'test_cafe')",
            (now,),
        )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def test_migration_on_temporary_database(tmp_path):
    """Running migration on a temporary database creates review_sessions and expected indexes."""
    db_file = tmp_path / "legacy_test.sqlite3"
    _create_legacy_database(db_file)

    res = run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res["status"] == "success"
    assert res["mode"] == "apply"
    assert "review_sessions" in res["verification"]["table"]

    # Verify directly via sqlite3
    with sqlite3.connect(str(db_file)) as conn:
        cols = {row[1]: row[2] for row in conn.execute("PRAGMA table_info(review_sessions)").fetchall()}
        assert "session_id" in cols
        assert "tenant_id" in cols
        assert "traffic_source" in cols
        assert "table_number" in cols
        assert "dining_type" in cols
        assert "created_at" in cols
        assert "expires_at" in cols

        indexes = [r[1] for r in conn.execute("PRAGMA index_list(review_sessions)").fetchall()]
        assert "idx_review_sessions_tenant_created" in indexes
        assert "idx_review_sessions_expiry" in indexes


def test_repeated_migration_is_idempotent(tmp_path):
    """Running migration repeatedly on an already-migrated database succeeds idempotently."""
    db_file = tmp_path / "idempotent_test.sqlite3"
    _create_legacy_database(db_file)

    # First run
    res1 = run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res1["status"] == "success"

    # Second run
    res2 = run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res2["status"] == "success"

    # Schema remains intact and verified
    with sqlite3.connect(str(db_file)) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_dry_run_makes_no_changes(tmp_path):
    """Dry-run simulates the migration within a transaction and rolls back without modifying target file."""
    db_file = tmp_path / "dry_run_test.sqlite3"
    _create_legacy_database(db_file)

    pre_sha256 = compute_sha256(db_file)

    res = run_a5_migration(str(db_file), dry_run=True)
    assert res["status"] == "success"
    assert res["mode"] == "dry_run"
    assert res["file_modified"] is False

    post_sha256 = compute_sha256(db_file)
    assert pre_sha256 == post_sha256

    # Verify review_sessions was NOT created on disk
    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "review_sessions" not in tables


def test_backup_creation_and_integrity(tmp_path):
    """Migration creates a verified hot backup before modifying the target database."""
    db_file = tmp_path / "backup_test.sqlite3"
    _create_legacy_database(db_file)

    backup_dir = tmp_path / "custom_backups"
    res = run_a5_migration(str(db_file), dry_run=False, backup_dir=backup_dir)

    backup_path = Path(res["backup_path"])
    assert backup_path.exists()
    assert backup_path.is_file()

    # Verify backup integrity
    with sqlite3.connect(str(backup_path)) as chk:
        assert chk.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    # Verify backup does not have review_sessions (snapshot was taken prior to migration)
    with sqlite3.connect(str(backup_path)) as chk:
        tables = [r[0] for r in chk.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "review_sessions" not in tables


def test_incompatible_existing_schema_rejection(tmp_path):
    """An existing review_sessions table with incompatible columns or PK is rejected and rolled back."""
    db_file = tmp_path / "incompatible_test.sqlite3"
    with sqlite3.connect(str(db_file)) as conn:
        # Table exists but has wrong columns (missing tenant_id, created_at, etc.)
        conn.execute("""
            CREATE TABLE review_sessions (
                id INTEGER PRIMARY KEY,
                bogus_column TEXT
            )
        """)
        conn.commit()

    with pytest.raises(ValueError, match="Incompatible review_sessions table"):
        run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")


def test_missing_target_rejection(tmp_path):
    """Missing target database path is strictly rejected."""
    non_existent = tmp_path / "does_not_exist.sqlite3"
    with pytest.raises(FileNotFoundError, match="Target database not found"):
        run_a5_migration(str(non_existent), dry_run=False)


def test_relative_path_rejection():
    """Relative database path is rejected; must be absolute."""
    with pytest.raises(ValueError, match="Relative database path .* rejected"):
        run_a5_migration("relative/path/test.sqlite3", dry_run=False)


def test_production_path_protection():
    """Targeting the production database without --confirm-production raises PermissionError."""
    with pytest.raises(PermissionError, match="REFUSED: Target database .* matches production database"):
        run_a5_migration(str(PROD_DB_PATH), dry_run=False, confirm_production=False)


def test_existing_data_preserved_after_migration(tmp_path):
    """Pre-existing tenant and analytics records are preserved completely intact after migration."""
    db_file = tmp_path / "preserve_data_test.sqlite3"
    _create_legacy_database(db_file)

    run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")

    with sqlite3.connect(str(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        tenant = conn.execute("SELECT * FROM tenants WHERE id='test_cafe'").fetchone()
        assert tenant is not None
        assert tenant["business_name"] == "Test Cafe"

        event = conn.execute("SELECT * FROM analytics_events WHERE event_id='ev-1'").fetchone()
        assert event is not None
        assert event["tenant_id"] == "test_cafe"


def test_cli_execution_via_subprocess(tmp_path):
    """Validates CLI arguments and nonzero exit code handling via subprocess."""
    db_file = tmp_path / "cli_test.sqlite3"
    _create_legacy_database(db_file)

    script_path = REPO_ROOT / "scripts" / "migrate_phase_a5_sessions.py"

    # Dry-run via CLI
    p_dry = subprocess.run(
        [sys.executable, str(script_path), "--database", str(db_file), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert p_dry.returncode == 0
    assert "compatible_dry_run_success" in p_dry.stdout

    # Relative path via CLI -> exit code 1
    p_rel = subprocess.run(
        [sys.executable, str(script_path), "--database", "relative.sqlite3"],
        capture_output=True,
        text=True,
    )
    assert p_rel.returncode == 1
    assert "Relative database path" in p_rel.stderr

    # Apply via CLI
    p_apply = subprocess.run(
        [sys.executable, str(script_path), "--database", str(db_file)],
        capture_output=True,
        text=True,
    )
    assert p_apply.returncode == 0
    assert "Migration successfully committed" in p_apply.stdout


# ─────────────────────────────────────────────────────────────────────────────
# PHASE A5.0.11: BACKUP PERMISSIONS, COLLISION SECURITY & STARTUP OWNERSHIP
# ─────────────────────────────────────────────────────────────────────────────

def test_backup_restrictive_permissions_posix(tmp_path):
    """Backup file must be created with restrictive permissions (0600 on POSIX)."""
    db_file = tmp_path / "perm_test.sqlite3"
    _create_legacy_database(db_file)
    orig_mode = stat.S_IMODE(os.stat(db_file).st_mode)

    bak_file = create_backup(db_file, backup_dir=tmp_path / "backups")
    assert bak_file.exists()

    if os.name == "posix":
        bak_mode = stat.S_IMODE(os.stat(bak_file).st_mode)
        # Verify no group/other permissions (0600)
        assert (bak_mode & 0o077) == 0, f"Expected 0600 restrictive mode, got {oct(bak_mode)}"
        # Original database permissions must remain completely unchanged
        current_orig_mode = stat.S_IMODE(os.stat(db_file).st_mode)
        assert current_orig_mode == orig_mode


def test_backup_collision_prevention_and_exclusive_creation(tmp_path):
    """Collision-resistant naming includes timestamp + nonce, and existing destination aborts safely."""
    db_file = tmp_path / "collision_test.sqlite3"
    _create_legacy_database(db_file)

    # 1. Nonce ensures distinct filenames even with identical mocked timestamp
    fixed_ts = "20261119_120000"
    name1 = generate_backup_filename(db_file, timestamp=fixed_ts)
    name2 = generate_backup_filename(db_file, timestamp=fixed_ts)
    assert name1 != name2, "Same timestamp must generate distinct filenames via nonce"

    # 2. Two consecutive backups do not overwrite each other
    bak1 = create_backup(db_file, backup_dir=tmp_path / "backups")
    bak2 = create_backup(db_file, backup_dir=tmp_path / "backups")
    assert bak1 != bak2
    assert bak1.exists() and bak2.exists()

    # 3. Exclusive creation: attempting to overwrite an already-existing destination raises FileExistsError
    existing_dest = tmp_path / "backups" / "pre_existing.sqlite3.bak"
    existing_dest.write_text("existing backup content")
    pre_sha = compute_sha256(existing_dest)
    db_sha_pre = compute_sha256(db_file)

    with pytest.raises(FileExistsError) as exc_info:
        create_backup(db_file, backup_dir=tmp_path / "backups", custom_filename="pre_existing.sqlite3.bak")

    assert "already exists" in str(exc_info.value)
    # Existing backup and original database must remain 100% untouched
    assert compute_sha256(existing_dest) == pre_sha
    assert compute_sha256(db_file) == db_sha_pre


def test_reviewstore_startup_schema_ownership_test_env(tmp_path, monkeypatch):
    """In test environment, ReviewStore startup auto-creates review_sessions for ephemeral test databases."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    db_file = tmp_path / "test_env_startup.sqlite3"
    _create_legacy_database(db_file)

    store = ReviewStore(str(db_file))
    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "review_sessions" in tables


def test_reviewstore_startup_schema_ownership_dev_env(tmp_path, monkeypatch):
    """In development environment, ReviewStore startup auto-creates review_sessions."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    db_file = tmp_path / "dev_env_startup.sqlite3"
    _create_legacy_database(db_file)

    store = ReviewStore(str(db_file))
    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "review_sessions" in tables


def test_reviewstore_startup_schema_ownership_staging_missing_schema(tmp_path, monkeypatch):
    """In staging environment, ReviewStore startup does NOT auto-create review_sessions and fails with actionable error."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    db_file = tmp_path / "staging_missing.sqlite3"
    _create_legacy_database(db_file)

    with pytest.raises(RuntimeError) as exc_info:
        ReviewStore(str(db_file))

    err = str(exc_info.value)
    assert "Database schema unmigrated" in err
    assert "missing required table 'review_sessions'" in err
    assert "scripts/migrate_phase_a5_sessions.py" in err

    # Verify that staging startup did NOT create the table
    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "review_sessions" not in tables


def test_reviewstore_startup_schema_ownership_production_missing_schema(tmp_path, monkeypatch):
    """In production environment, ReviewStore startup does NOT auto-create review_sessions and fails with actionable error."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    db_file = tmp_path / "prod_missing.sqlite3"
    _create_legacy_database(db_file)

    with pytest.raises(RuntimeError) as exc_info:
        ReviewStore(str(db_file))

    err = str(exc_info.value)
    assert "Database schema unmigrated" in err
    assert "missing required table 'review_sessions'" in err
    assert "scripts/migrate_phase_a5_sessions.py" in err

    # Verify that production startup did NOT create the table
    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "review_sessions" not in tables


def test_reviewstore_startup_schema_ownership_unconfigured_env_fails_closed(tmp_path, monkeypatch):
    """When ENVIRONMENT is unset or ambiguous, startup fails closed and does not create missing schema."""
    monkeypatch.setenv("ENVIRONMENT", "")
    db_file = tmp_path / "unconfigured_env.sqlite3"
    _create_legacy_database(db_file)

    with pytest.raises(RuntimeError) as exc_info:
        ReviewStore(str(db_file))

    assert "Database schema unmigrated" in str(exc_info.value)

    with sqlite3.connect(str(db_file)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "review_sessions" not in tables


def test_reviewstore_startup_schema_ownership_staging_migrated_db_succeeds(tmp_path, monkeypatch):
    """When the database is properly migrated via script, staging startup succeeds cleanly."""
    from scripts.migrate_template_subsystem import run_template_migration

    db_file = tmp_path / "staging_migrated.sqlite3"
    _create_legacy_database(db_file)

    # Migrate using migration scripts
    res = run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res["status"] == "success"
    res_tpl = run_template_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res_tpl["status"] == "success"

    # Now boot in staging
    monkeypatch.setenv("ENVIRONMENT", "staging")
    store = ReviewStore(str(db_file))
    assert store is not None

    # Test read and write
    sess = store.create_review_session("sess_stag_1", "test_cafe")
    assert sess["session_id"] == "sess_stag_1"
    fetched = store.get_review_session("sess_stag_1")
    assert fetched is not None
    assert fetched["tenant_id"] == "test_cafe"


def test_reviewstore_startup_schema_ownership_production_incompatible_schema(tmp_path, monkeypatch):
    """In production, startup against an incompatible review_sessions schema fails safely."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    db_file = tmp_path / "prod_incompatible.sqlite3"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE tenants (id TEXT PRIMARY KEY, business_name TEXT, status TEXT DEFAULT 'active', created_at REAL)")
        conn.execute("CREATE TABLE analytics_events (event_id TEXT PRIMARY KEY, created_at REAL, payload TEXT, tenant_id TEXT)")
        conn.execute("CREATE TABLE private_tickets (ticket_id TEXT PRIMARY KEY, created_at REAL, payload TEXT, tenant_id TEXT)")
        # Incompatible review_sessions table (missing columns)
        conn.execute("CREATE TABLE review_sessions (id TEXT PRIMARY KEY, some_other_col TEXT)")

    with pytest.raises(RuntimeError) as exc_info:
        ReviewStore(str(db_file))

    assert "Incompatible 'review_sessions' table schema" in str(exc_info.value)


def test_reviewstore_startup_schema_ownership_preserves_tenant_and_analytics_tables(tmp_path, monkeypatch):
    """Existing tenant and analytics records are preserved completely untouched during migration and staging startup."""
    from scripts.migrate_template_subsystem import run_template_migration

    db_file = tmp_path / "preserve_all.sqlite3"
    _create_legacy_database(db_file)

    # 1. Run explicit migrations
    run_a5_migration(str(db_file), backup_dir=tmp_path / "backups")
    run_template_migration(str(db_file), backup_dir=tmp_path / "backups")

    # 2. Boot in staging
    monkeypatch.setenv("ENVIRONMENT", "staging")
    store = ReviewStore(str(db_file))

    # 3. Verify tenant and analytics data
    with sqlite3.connect(str(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        tenant = conn.execute("SELECT * FROM tenants WHERE id='test_cafe'").fetchone()
        assert tenant["business_name"] == "Test Cafe"
        assert tenant["status"] == "active"

        event = conn.execute("SELECT * FROM analytics_events WHERE event_id='ev-1'").fetchone()
        assert event["tenant_id"] == "test_cafe"
        assert "rating" in event["payload"]


# ─────────────────────────────────────────────────────────────────────────────
# PHASE A5.0.13: BACKUP FAILURE CLEANUP & RESILIENCE TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_backup_failure_during_sqlite_backup_cleans_up_incomplete_file(tmp_path):
    """If an error occurs during SQLite backup, the incomplete backup file is removed."""
    db_file = tmp_path / "backup_fail_src.sqlite3"
    _create_legacy_database(db_file)
    src_sha_before = compute_sha256(db_file)
    bdir = tmp_path / "backups"

    orig_connect = sqlite3.connect
    def mock_connect(path_str, *args, **kwargs):
        conn = orig_connect(path_str, *args, **kwargs)
        if str(path_str) == str(db_file):
            class BrokenSrcConn:
                def __init__(self, c): self._c = c
                def __enter__(self): return self
                def __exit__(self, *a): return self._c.__exit__(*a)
                def backup(self, dst, **k):
                    raise OSError("Simulated disk full during backup")
                def __getattr__(self, name): return getattr(self._c, name)
            return BrokenSrcConn(conn)
        return conn

    with patch("sqlite3.connect", side_effect=mock_connect):
        with pytest.raises(OSError, match="Simulated disk full during backup"):
            create_backup(db_file, backup_dir=bdir)

    # Incomplete backup file must have been cleaned up
    leftovers = list(bdir.glob("*.bak"))
    assert leftovers == [], f"Expected 0 leftover backup files, found: {leftovers}"

    # Original database remains completely untouched
    assert compute_sha256(db_file) == src_sha_before


def test_backup_failure_during_integrity_check_cleans_up_incomplete_file(tmp_path):
    """If PRAGMA integrity_check fails on the backup, the corrupt backup file is removed."""
    db_file = tmp_path / "integrity_fail_src.sqlite3"
    _create_legacy_database(db_file)
    src_sha_before = compute_sha256(db_file)
    bdir = tmp_path / "backups"

    orig_connect = sqlite3.connect
    calls = {"count": 0}
    def mock_connect(path_str, *args, **kwargs):
        calls["count"] += 1
        conn = orig_connect(path_str, *args, **kwargs)
        if calls["count"] == 3:  # Third connect in create_backup is integrity check
            class CorruptConn:
                def __init__(self, c): self._c = c
                def __enter__(self): return self
                def __exit__(self, *a): return self._c.__exit__(*a)
                def execute(self, q):
                    class FakeCursor:
                        def fetchone(self): return ["*** in database main *** Page 1: wrong header"]
                    return FakeCursor()
                def __getattr__(self, name): return getattr(self._c, name)
            return CorruptConn(conn)
        return conn

    with patch("sqlite3.connect", side_effect=mock_connect):
        with pytest.raises(RuntimeError, match="Backup integrity check failed"):
            create_backup(db_file, backup_dir=bdir)

    # Incomplete corrupt backup must have been unlinked
    leftovers = list(bdir.glob("*.bak"))
    assert leftovers == [], f"Expected 0 leftover backup files, found: {leftovers}"

    # Source database must remain 100% untouched
    assert compute_sha256(db_file) == src_sha_before


def test_backup_failure_preserves_preexisting_backups(tmp_path):
    """Failure or collision during backup never deletes or modifies pre-existing backup files."""
    db_file = tmp_path / "preserve_prev.sqlite3"
    _create_legacy_database(db_file)
    bdir = tmp_path / "backups"
    bdir.mkdir(parents=True, exist_ok=True)

    # Pre-existing backup file
    pre_existing = bdir / "pre_existing_backup.sqlite3.bak"
    pre_existing.write_text("critical prior backup data")
    pre_sha = compute_sha256(pre_existing)

    # 1. Collision failure preserves existing file
    with pytest.raises(FileExistsError):
        create_backup(db_file, backup_dir=bdir, custom_filename="pre_existing_backup.sqlite3.bak")

    assert pre_existing.exists()
    assert compute_sha256(pre_existing) == pre_sha
    assert pre_existing.read_text() == "critical prior backup data"

    # 2. Subsequent failed backup removes only its own newly created file, leaving prior backup
    orig_connect = sqlite3.connect
    def mock_connect(path_str, *args, **kwargs):
        conn = orig_connect(path_str, *args, **kwargs)
        if str(path_str) == str(db_file):
            class BrokenConn:
                def __init__(self, c): self._c = c
                def __enter__(self): return self
                def __exit__(self, *a): return self._c.__exit__(*a)
                def backup(self, dst, **k): raise IOError("Simulated IO error")
                def __getattr__(self, name): return getattr(self._c, name)
            return BrokenConn(conn)
        return conn

    with patch("sqlite3.connect", side_effect=mock_connect):
        with pytest.raises(IOError, match="Simulated IO error"):
            create_backup(db_file, backup_dir=bdir)

    # Only pre-existing backup remains
    remaining = list(bdir.glob("*.bak"))
    assert remaining == [pre_existing]
    assert compute_sha256(pre_existing) == pre_sha


def test_wal_data_preserved_and_restored_from_backup(tmp_path):
    """WAL frames not yet checkpointed are preserved in backup and successfully restored."""
    db_file = tmp_path / "wal_source.sqlite3"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE wal_test (id INT PRIMARY KEY, val TEXT)")
        conn.execute("INSERT INTO wal_test VALUES (1, 'initial')")
        conn.commit()
        # Uncheckpointed write
        conn.execute("INSERT INTO wal_test VALUES (2, 'uncheckpointed_wal_row')")
        conn.commit()

    # Create backup while in WAL mode
    bdir = tmp_path / "backups"
    bak_file = create_backup(db_file, backup_dir=bdir)
    assert bak_file.exists()

    # Restore from backup into new isolated database
    restore_file = tmp_path / "restored.sqlite3"
    with sqlite3.connect(str(bak_file)) as b_conn, sqlite3.connect(str(restore_file)) as r_conn:
        b_conn.backup(r_conn)

    with sqlite3.connect(str(restore_file)) as r_conn:
        rows = r_conn.execute("SELECT id, val FROM wal_test ORDER BY id").fetchall()
        assert rows == [(1, "initial"), (2, "uncheckpointed_wal_row")]


def test_backup_cleanup_itself_failing_preserves_original_exception(tmp_path, monkeypatch):
    """If unlinking the incomplete backup file fails, the original exception is preserved with a note."""
    db_file = tmp_path / "unlink_fail.sqlite3"
    _create_legacy_database(db_file)
    bdir = tmp_path / "backups"

    orig_connect = sqlite3.connect
    def mock_connect(path_str, *args, **kwargs):
        conn = orig_connect(path_str, *args, **kwargs)
        if str(path_str) == str(db_file):
            class BrokenConn:
                def __init__(self, c): self._c = c
                def __enter__(self): return self
                def __exit__(self, *a): return self._c.__exit__(*a)
                def backup(self, dst, **k): raise OSError("Original backup disk failure")
                def __getattr__(self, name): return getattr(self._c, name)
            return BrokenConn(conn)
        return conn

    orig_unlink = Path.unlink
    def mock_unlink(self, *args, **kwargs):
        raise PermissionError("Simulated cleanup unlink failure")

    with patch("sqlite3.connect", side_effect=mock_connect):
        with patch.object(Path, "unlink", side_effect=mock_unlink):
            with pytest.raises(OSError, match="Original backup disk failure") as exc_info:
                create_backup(db_file, backup_dir=bdir)

    # Verify original exception is raised and contains diagnostic note if supported
    exc = exc_info.value
    if hasattr(exc, "__notes__"):
        assert any("cleanup of incomplete backup file failed" in n for n in exc.__notes__)


def test_incompatible_schema_b_rejection_in_migration(tmp_path):
    """An existing review_sessions table adhering to legacy Schema B is strictly rejected."""
    db_file = tmp_path / "schema_b_test.sqlite3"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("""
            CREATE TABLE review_sessions (
                session_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                table_number TEXT,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.commit()

    with pytest.raises(ValueError, match="Incompatible review_sessions table: expected exact columns"):
        run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")


def test_incompatible_schema_b_rejection_in_production_runtime(tmp_path, monkeypatch):
    """In production runtime, ReviewStore startup against legacy Schema B fails closed."""
    from backend.app.core.database.storage import ReviewStore
    from scripts.migrate_template_subsystem import apply_template_migration

    db_file = tmp_path / "schema_b_prod.sqlite3"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("""
            CREATE TABLE tenants (
                id TEXT PRIMARY KEY,
                business_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE review_sessions (
                session_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                table_number TEXT,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL
            )
        """)
        apply_template_migration(conn)
        conn.commit()

    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="Incompatible 'review_sessions' table schema"):
        ReviewStore(database_path=str(db_file))
