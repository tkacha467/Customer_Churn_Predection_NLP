#!/usr/bin/env python3
"""
VRAJA AI — Phase 2 Subpart 2B CLI Migration Runner
Executes guarded column additions, tenant provisioning, reconciliation,
and conflict auditing against an isolated or specified SQLite database.

Safety Invariants:
1. Refuses to run against production database unless explicitly confirmed.
2. Supports --dry-run (always rolls back at the end).
3. Supports --isolated-copy (runs exclusively on a temporary database snapshot).
4. Enforces PRAGMA foreign_keys = ON and verifies journal mode is preserved.
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Backend.app.core.database.migration import (
    run_subpart_2b_migration,
    MigrationError,
    InvariantViolationError,
)

PROD_DB_PATH = REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"


def execute_migration_runner(
    db_path: Path,
    dry_run: bool = False,
    isolated_copy: bool = False,
    confirm_production: bool = False,
) -> Dict[str, Any]:
    """
    Executes Subpart 2B migration with complete safety checks.
    """
    resolved_path = db_path.resolve()
    resolved_prod = PROD_DB_PATH.resolve()

    # Safety Barrier: Protect production database
    if resolved_path == resolved_prod and not confirm_production:
        raise PermissionError(
            f"REFUSED: Target database '{resolved_path}' matches the active production database! "
            "Running migrations against production is strictly prohibited without explicit authorization "
            "and --confirm-production flag."
        )

    working_path = resolved_path
    temp_dir = None

    if isolated_copy:
        temp_dir = tempfile.mkdtemp(prefix="vraja_phase2_migration_")
        working_path = Path(temp_dir) / resolved_path.name
        shutil.copy2(resolved_path, working_path)
        # Also copy WAL/SHM if they exist
        wal = resolved_path.with_name(resolved_path.name + "-wal")
        shm = resolved_path.with_name(resolved_path.name + "-shm")
        if wal.exists():
            shutil.copy2(wal, Path(temp_dir) / wal.name)
        if shm.exists():
            shutil.copy2(shm, Path(temp_dir) / shm.name)

    if not working_path.exists():
        raise FileNotFoundError(f"Database file not found: {working_path}")

    # Connect with isolation_level=None to allow explicit transaction management
    con = sqlite3.connect(str(working_path), timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row

    try:
        if dry_run:
            # In dry-run mode, we test running migration and immediately roll back
            initial_journal = con.execute("PRAGMA journal_mode;").fetchone()[0]
            con.execute("PRAGMA foreign_keys = ON;")
            fk_ok = con.execute("PRAGMA foreign_keys;").fetchone()[0]
            if fk_ok != 1:
                raise MigrationError("foreign_keys = ON could not be enabled.")

            con.execute("BEGIN IMMEDIATE TRANSACTION;")
            from Backend.app.core.database.migration import (
                apply_phase2_schema_alterations,
                provision_unprovisioned_tenants,
                reconcile_and_audit_existing_records,
            )
            schema_stats = apply_phase2_schema_alterations(con)
            prov_stats = provision_unprovisioned_tenants(con)
            rec_stats = reconcile_and_audit_existing_records(con)
            con.execute("ROLLBACK;")

            return {
                "mode": "DRY_RUN (Rolled Back)",
                "target_database": str(working_path),
                "isolated_copy": isolated_copy,
                "initial_journal_mode": initial_journal,
                "schema_alterations": schema_stats,
                "provisioning": prov_stats,
                "reconciliation": rec_stats,
            }
        else:
            result = run_subpart_2b_migration(con)
            result["mode"] = "EXECUTED"
            result["target_database"] = str(working_path)
            result["isolated_copy"] = isolated_copy
            return result
    finally:
        con.close()
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="VRAJA AI Phase 2 Subpart 2B Migration Tool")
    parser.add_argument("--db-path", type=Path, required=True, help="Path to target SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration and roll back")
    parser.add_argument("--isolated-copy", action="store_true", help="Run on a temporary clone of the database")
    parser.add_argument("--confirm-production", action="store_true", help="Required only for production database")

    args = parser.parse_args()

    try:
        report = execute_migration_runner(
            db_path=args.db_path,
            dry_run=args.dry_run,
            isolated_copy=args.isolated_copy,
            confirm_production=args.confirm_production,
        )
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(f"Migration Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
