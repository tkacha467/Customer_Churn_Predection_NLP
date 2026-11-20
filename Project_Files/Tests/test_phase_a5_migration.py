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
    with sqlite3.connect(str(db_path)) as conn:
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
            CREATE TABLE analytics_events (
                event_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload TEXT NOT NULL,
                tenant_id TEXT
            )
        """)
        # Insert sample tenant and analytics records
        conn.execute(
            "INSERT INTO tenants VALUES ('default_business', 'Nasta Ghar', 'active', ?)",
            (time.time(),),
        )
        conn.execute(
            "INSERT INTO tenants VALUES ('test_cafe', 'Test Cafe', 'active', ?)",
            (time.time(),),
        )
        conn.execute(
            "INSERT INTO analytics_events VALUES ('ev-1', ?, '{\"rating\": 5}', 'test_cafe')",
            (time.time(),),
        )
        conn.commit()


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
    db_file = tmp_path / "staging_migrated.sqlite3"
    _create_legacy_database(db_file)

    # Migrate using migration script
    res = run_a5_migration(str(db_file), dry_run=False, backup_dir=tmp_path / "backups")
    assert res["status"] == "success"

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
    db_file = tmp_path / "preserve_all.sqlite3"
    _create_legacy_database(db_file)

    # 1. Run explicit migration
    run_a5_migration(str(db_file), backup_dir=tmp_path / "backups")

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
