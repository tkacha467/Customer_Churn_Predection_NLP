#!/usr/bin/env python3
"""
VRAJA AI — Phase A5 Database Migration Script: review_sessions Table
Creates the persistent review_sessions table and composite indexes with
strict safety invariants:
1. Requires explicit absolute database path (rejects relative paths and missing targets).
2. Protects production database: refuses to modify production without explicit --confirm-production.
3. Never infers target path from current working directory; never silently falls back.
4. Supports --dry-run (executes schema check and rolls back completely).
5. Creates a hot SQLite online backup and verifies PRAGMA integrity_check before modifying target.
6. Uses SQLite transaction safety with automatic rollback on error.
7. Inspects existing table schema and rejects incompatible structures.
8. Verifies resulting schema and indexes post-migration.
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
from typing import Any, Dict, List, Optional

# Expected production database path
REPO_ROOT = Path(__file__).resolve().parent.parent
PROD_DB_PATH = (REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3").resolve()

EXPECTED_COLUMNS = {
    "session_id",
    "tenant_id",
    "traffic_source",
    "table_number",
    "dining_type",
    "created_at",
    "expires_at",
}

EXPECTED_INDEXES = {
    "idx_review_sessions_tenant_created",
    "idx_review_sessions_expiry",
}


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
    and collision-resistant exclusive creation.
    Never overwrites an existing backup file.
    """
    dest_dir = backup_dir or (target_path.parent / "backups")
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = custom_filename or generate_backup_filename(target_path)
    backup_file = dest_dir / filename

    created_by_us = False
    try:
        # Atomically create the backup file exclusively with mode 0600 on POSIX
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
            # Non-POSIX (e.g. Windows) exclusive file creation
            if backup_file.exists():
                raise FileExistsError(
                    f"Backup destination already exists: {backup_file}. Aborting to prevent overwrite."
                )
            backup_file.touch(exist_ok=False)
            created_by_us = True

        # Perform hot online SQLite backup (WAL-safe)
        with sqlite3.connect(str(target_path)) as src, sqlite3.connect(str(backup_file)) as dst:
            src.backup(dst)

        # Verify and enforce restrictive file permissions on POSIX systems
        if os.name == "posix":
            mode = stat.S_IMODE(os.stat(backup_file).st_mode)
            if (mode & 0o077) != 0:
                os.chmod(backup_file, 0o600)
                mode = stat.S_IMODE(os.stat(backup_file).st_mode)
                if (mode & 0o077) != 0:
                    raise PermissionError(
                        f"Insecure backup file permissions ({oct(mode)}). Expected 0600."
                    )

        # Verify backup database integrity
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


def validate_existing_schema(conn: sqlite3.Connection) -> bool:
    """
    Checks if review_sessions already exists and verifies its schema.
    Returns True if table exists and matches expected schema, False if table does not exist.
    Raises ValueError if table exists but has an incompatible schema.
    """
    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='review_sessions'"
        ).fetchall()
    ]
    if not tables:
        return False

    col_info = conn.execute("PRAGMA table_info(review_sessions)").fetchall()
    existing_cols = {row[1] for row in col_info}
    pk_cols = [row[1] for row in col_info if row[5] > 0]

    # Verify all expected columns are present and no unexpected columns exist
    missing_cols = EXPECTED_COLUMNS - existing_cols
    unexpected_cols = existing_cols - EXPECTED_COLUMNS
    if missing_cols or unexpected_cols:
        raise ValueError(
            f"Incompatible review_sessions table: expected exact columns {EXPECTED_COLUMNS}, "
            f"got {existing_cols} (missing: {missing_cols}, unexpected: {unexpected_cols})"
        )

    # Verify primary key
    if pk_cols != ["session_id"]:
        raise ValueError(
            f"Incompatible review_sessions table: expected PK ['session_id'], got {pk_cols}"
        )

    return True


def apply_review_sessions_ddl(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Applies review_sessions table and index creation within a transaction."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS review_sessions (
            session_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            traffic_source TEXT NOT NULL DEFAULT 'customer',
            table_number TEXT DEFAULT '',
            dining_type TEXT DEFAULT '',
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_sessions_tenant_created ON review_sessions(tenant_id, created_at DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_sessions_expiry ON review_sessions(expires_at)"
    )
    return {"status": "applied"}


def verify_migrated_schema(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Verifies that the target database contains review_sessions and expected indexes."""
    # 1. Table existence & columns
    col_info = conn.execute("PRAGMA table_info(review_sessions)").fetchall()
    if not col_info:
        raise RuntimeError("Verification failed: review_sessions table not found.")
    cols = {row[1] for row in col_info}
    missing = EXPECTED_COLUMNS - cols
    unexpected = cols - EXPECTED_COLUMNS
    if missing or unexpected:
        raise RuntimeError(
            f"Verification failed: expected exact columns {EXPECTED_COLUMNS}, "
            f"got {cols} (missing: {missing}, unexpected: {unexpected})"
        )

    # 2. Indexes
    idx_info = conn.execute("PRAGMA index_list(review_sessions)").fetchall()
    indexes = {row[1] for row in idx_info}
    missing_idx = EXPECTED_INDEXES - indexes
    if missing_idx:
        raise RuntimeError(f"Verification failed: missing indexes {missing_idx}")

    # 3. Overall database integrity
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"Database integrity check failed: {integrity}")

    return {
        "table": "review_sessions",
        "columns": sorted(list(cols)),
        "indexes": sorted(list(indexes)),
        "integrity": integrity,
    }


def run_a5_migration(
    database_path_str: str,
    dry_run: bool = False,
    confirm_production: bool = False,
    backup_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes Phase A5 migration with complete safety controls.
    """
    if not database_path_str:
        raise ValueError("Missing required database path. Pass an explicit absolute path.")

    raw_path = Path(database_path_str)

    # Invariant 1: Reject relative paths
    if not raw_path.is_absolute():
        raise ValueError(
            f"Relative database path '{database_path_str}' rejected. You must provide an explicit absolute path."
        )

    resolved_path = raw_path.resolve()

    # Invariant 2: Reject missing targets
    if not resolved_path.exists():
        raise FileNotFoundError(f"Target database not found: {resolved_path}")

    # Invariant 3: Reject non-file paths
    if not resolved_path.is_file():
        raise ValueError(f"Target path is not a file: {resolved_path}")

    # Invariant 4: Production protection
    is_prod = (resolved_path == PROD_DB_PATH)
    if is_prod and not confirm_production:
        raise PermissionError(
            f"REFUSED: Target database '{resolved_path}' matches production database! "
            "Running migrations against production is strictly prohibited without explicit --confirm-production flag."
        )

    print(f"[*] Targeting database: {resolved_path}")
    print(f"[*] Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    initial_sha256 = compute_sha256(resolved_path)
    backup_file = None
    backup_sha256 = None

    if dry_run:
        # In dry-run mode, run inside an IMMEDIATE transaction and always roll back
        conn = sqlite3.connect(str(resolved_path), timeout=30, isolation_level=None)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN IMMEDIATE TRANSACTION")
            is_already_migrated = validate_existing_schema(conn)
            if is_already_migrated:
                schema_state = "already_migrated"
            else:
                apply_review_sessions_ddl(conn)
                verify_migrated_schema(conn)
                schema_state = "compatible_dry_run_success"
            conn.execute("ROLLBACK")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

        post_dry_run_sha = compute_sha256(resolved_path)
        if post_dry_run_sha != initial_sha256:
            raise RuntimeError("Dry-run violated invariant: target file was modified!")

        return {
            "status": "success",
            "mode": "dry_run",
            "target_database": str(resolved_path),
            "schema_state": schema_state,
            "target_sha256": initial_sha256,
            "file_modified": False,
        }

    # Production / Apply Mode: Create and verify hot backup first
    print("[*] Creating verified hot backup before applying migration...")
    backup_file = create_backup(resolved_path, backup_dir=backup_dir)
    backup_sha256 = compute_sha256(backup_file)
    print(f"[+] Hot backup created and verified: {backup_file} (SHA256: {backup_sha256})")

    # Connect and execute within transaction
    conn = sqlite3.connect(str(resolved_path), timeout=30, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE TRANSACTION")
        is_already_migrated = validate_existing_schema(conn)
        if is_already_migrated:
            print("[*] review_sessions table already exists with compatible schema. Ensuring indexes...")
        apply_review_sessions_ddl(conn)
        verification_details = verify_migrated_schema(conn)
        conn.execute("COMMIT")
        print("[+] Migration successfully committed.")
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
        description="VRAJA AI — Phase A5 review_sessions Database Migration Runner"
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
        help="Explicit confirmation required when targeting the production database.",
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default=None,
        help="Optional custom directory for pre-migration backups.",
    )

    args = parser.parse_args()
    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else None

    try:
        result = run_a5_migration(
            database_path_str=args.database,
            dry_run=args.dry_run,
            confirm_production=args.confirm_production,
            backup_dir=backup_dir,
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
