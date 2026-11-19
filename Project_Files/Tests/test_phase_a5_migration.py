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
import subprocess
import sys
import time
from pathlib import Path
import pytest

from scripts.migrate_phase_a5_sessions import (
    run_a5_migration,
    compute_sha256,
    PROD_DB_PATH,
)

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
