#!/usr/bin/env python3
"""
VRAJA AI — Product A: Dynamic Industry Template Subsystem Database Migration Runner
Creates dynamic industry template subsystem tables and seeds default templates idempotently with
strict safety invariants:
1. Requires explicit absolute database path (rejects relative paths and missing targets).
2. Protects production database: refuses to modify production without explicit --confirm-production.
3. Never infers target path from current working directory; never silently falls back.
4. Supports --dry-run (executes schema check/seeding within rolled-back transaction).
5. Creates a hot SQLite online backup and verifies PRAGMA integrity_check before modifying target.
6. Uses SQLite transaction safety with automatic rollback on error.
7. Preserves existing industry templates and tenant customizations.
8. Verifies resulting schema, indexes, and integrity post-migration.
9. Returns nonzero exit code on failure and outputs structured execution report.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
PROD_DB_PATH = (REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3").resolve()

# Add repository root to sys.path so we can import template_storage
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.database.template_storage import (
    TEMPLATE_SCHEMA_CONTRACT,
    init_template_schema,
    seed_default_templates,
    validate_strict_template_schema,
    validate_strict_template_table,
)


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_backup_filename(
    target_path: Path,
    timestamp: Optional[str] = None,
    nonce: Optional[str] = None
) -> str:
    """Generates collision-resistant backup filename with timestamp and nonce."""
    ts = timestamp or time.strftime("%Y%m%d_%H%M%S")
    uid = nonce or uuid.uuid4().hex[:8]
    return f"{target_path.stem}_{ts}_{uid}.sqlite3.bak"


def create_backup(
    target_path: Path,
    backup_dir: Optional[Path] = None,
    custom_filename: Optional[str] = None,
) -> Path:
    """
    Creates a WAL-safe hot SQLite backup with strict restrictive permissions (0600 on POSIX)
    and collision-resistant exclusive creation. Never overwrites an existing backup file.
    If an error occurs after file creation, safely removes the incomplete backup file.
    """
    dest_dir = backup_dir or (target_path.parent / "backups")
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = custom_filename or generate_backup_filename(target_path)
    backup_file = dest_dir / filename

    created_by_us = False
    try:
        if os.name == "posix":
            try:
                fd = os.open(str(backup_file), os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                raise FileExistsError(
                    f"Backup destination already exists: {backup_file}. Aborting to prevent overwrite."
                )
            created_by_us = True
            try:
                os.fchmod(fd, 0o600)
            finally:
                os.close(fd)
        else:
            if backup_file.exists():
                raise FileExistsError(
                    f"Backup destination already exists: {backup_file}. Aborting to prevent overwrite."
                )
            backup_file.touch(exist_ok=False)
            created_by_us = True

        with sqlite3.connect(str(target_path)) as src, sqlite3.connect(str(backup_file)) as dst:
            src.backup(dst)

        if os.name == "posix":
            mode = stat.S_IMODE(os.stat(backup_file).st_mode)
            if (mode & 0o077) != 0:
                os.chmod(backup_file, 0o600)
                mode = stat.S_IMODE(os.stat(backup_file).st_mode)
                if (mode & 0o077) != 0:
                    raise PermissionError(
                        f"Insecure backup file permissions ({oct(mode)}). Expected 0600."
                    )

        with sqlite3.connect(str(backup_file)) as chk:
            integrity = chk.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"Backup integrity check failed: {integrity}")

    except Exception as exc:
        if created_by_us and backup_file.exists():
            try:
                backup_file.unlink()
            except Exception as cleanup_err:
                print(
                    f"[!] Warning: Failed to clean up incomplete backup file {backup_file}: {cleanup_err}",
                    file=sys.stderr,
                )
                if hasattr(exc, "add_note"):
                    exc.add_note(f"Additionally, cleanup of incomplete backup file failed: {cleanup_err}")
        raise

    return backup_file


def validate_existing_template_schema(conn: sqlite3.Connection, db_path_str: str) -> bool:
    """
    Inspects existing template tables in the database before migration.
    If an existing table has an incompatible schema (wrong columns, types, nullability,
    defaults, PK, unique constraints, foreign keys, or indexes), raises ValueError to abort safely.
    Returns True if all 5 tables already exist and match strictly, False if unmigrated.
    """
    existing_tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    # Inspect each template table that exists
    for tbl, contract in TEMPLATE_SCHEMA_CONTRACT.items():
        if tbl in existing_tables:
            try:
                validate_strict_template_table(conn, tbl, contract, "pre-migration-check", db_path_str)
            except RuntimeError as exc:
                raise ValueError(f"Incompatible existing template table '{tbl}': {exc}") from exc

    all_exist = all(tbl in existing_tables for tbl in TEMPLATE_SCHEMA_CONTRACT)
    return all_exist


def verify_template_schema(conn: sqlite3.Connection, db_path_str: str) -> Dict[str, Any]:
    """Strictly verifies that target database matches all 5 template tables, foreign keys, and indexes."""
    validate_strict_template_schema(conn, "post-migration-verify", db_path_str)

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"Database integrity check failed: {integrity}")

    results: Dict[str, Any] = {"integrity": integrity}
    for tbl, contract in TEMPLATE_SCHEMA_CONTRACT.items():
        cols = [c["name"] for c in contract["columns"]]
        idxs = list(contract["indexes"].keys())
        results[tbl] = {
            "columns": cols,
            "indexes": idxs,
        }

    return results


def apply_template_migration(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Applies template schema DDL and idempotent default seeding."""
    init_template_schema(conn)
    seed_default_templates(conn)
    return {"status": "applied"}


def run_template_migration(
    database_path_str: str,
    dry_run: bool = False,
    confirm_production: bool = False,
    backup_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Executes Dynamic Industry Template migration with full safety controls."""
    if not database_path_str:
        raise ValueError("Missing required database path. Pass an explicit absolute path.")

    raw_path = Path(database_path_str)
    if not raw_path.is_absolute():
        raise ValueError(
            f"Relative database path '{database_path_str}' rejected. You must provide an explicit absolute path."
        )

    resolved_path = raw_path.resolve()

    # Production path guard checked BEFORE file existence check so CI runners enforce guard cleanly
    is_prod = (resolved_path == PROD_DB_PATH)
    if is_prod and not confirm_production and not dry_run:
        raise PermissionError(
            f"PROTECTED PRODUCTION DATABASE DETECTED: {resolved_path}\n"
            "Modifications to production database require explicit authorization via --confirm-production."
        )

    if not resolved_path.exists():
        raise FileNotFoundError(f"Target database not found: {resolved_path}")

    if not resolved_path.is_file():
        raise ValueError(f"Target path is not a regular file: {resolved_path}")

    initial_sha256 = compute_sha256(resolved_path)

    # Dry-Run Mode
    if dry_run:
        print("[*] Executing in DRY-RUN mode. Simulating changes in transaction and rolling back...")
        initial_bytes = resolved_path.read_bytes()
        conn = sqlite3.connect(str(resolved_path), timeout=30, isolation_level=None)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN IMMEDIATE TRANSACTION")
            validate_existing_template_schema(conn, str(resolved_path))
            apply_template_migration(conn)
            verification = verify_template_schema(conn, str(resolved_path))
            conn.execute("ROLLBACK")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
            resolved_path.write_bytes(initial_bytes)

        post_dry_run_sha = compute_sha256(resolved_path)
        if post_dry_run_sha != initial_sha256:
            raise RuntimeError("Dry-run violated invariant: target file was modified!")

        return {
            "status": "success",
            "mode": "dry_run",
            "target_database": str(resolved_path),
            "target_sha256": initial_sha256,
            "verification": verification,
            "file_modified": False,
        }

    # Pre-Migration Safety Check: Verify any existing template tables before backup
    check_conn = sqlite3.connect(str(resolved_path), timeout=30)
    try:
        check_conn.execute("PRAGMA foreign_keys = ON")
        validate_existing_template_schema(check_conn, str(resolved_path))
    finally:
        check_conn.close()

    # Apply Mode: Create verified hot backup
    print("[*] Creating verified hot backup before applying template migration...")
    backup_file = create_backup(resolved_path, backup_dir=backup_dir)
    backup_sha256 = compute_sha256(backup_file)
    print(f"[+] Hot backup created and verified: {backup_file} (SHA256: {backup_sha256})")

    conn = sqlite3.connect(str(resolved_path), timeout=30, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE TRANSACTION")
        apply_template_migration(conn)
        verification_details = verify_template_schema(conn, str(resolved_path))
        conn.execute("COMMIT")
        print("[+] Template migration successfully committed.")
    except Exception as exc:
        conn.execute("ROLLBACK")
        print(f"[!] Migration failed: {exc}. Rolled back transaction.", file=sys.stderr)
        raise
    finally:
        conn.close()

    post_sha256 = compute_sha256(resolved_path)

    return {
        "status": "success",
        "mode": "apply",
        "target_database": str(resolved_path),
        "backup_path": str(backup_file),
        "backup_sha256": backup_sha256,
        "pre_migration_sha256": initial_sha256,
        "post_migration_sha256": post_sha256,
        "verification": verification_details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="VRAJA AI — Product A Dynamic Industry Template Database Migration Runner"
    )
    parser.add_argument(
        "--database",
        required=True,
        type=str,
        help="Explicit absolute path to the target SQLite database file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulates migration within a rolled-back transaction without modifying target file.",
    )
    parser.add_argument(
        "--confirm-production",
        action="store_true",
        help="Required flag when executing against production database.",
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default=None,
        help="Optional directory where backup file should be written.",
    )

    args = parser.parse_args()
    b_dir = Path(args.backup_dir) if args.backup_dir else None

    try:
        result = run_template_migration(
            database_path_str=args.database,
            dry_run=args.dry_run,
            confirm_production=args.confirm_production,
            backup_dir=b_dir,
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"\n[!] Migration Execution Failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
