#!/usr/bin/env python3
"""
Enterprise Database & Configuration Backup and Recovery Utility for NastaGhar SaaS Platform.
Safely creates hot SQLite online snapshots (WAL-safe) and isolated restore verifications.
"""

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "nasta-ghar" / "reviews.sqlite3"
DEFAULT_CONFIG_PATH = ROOT_DIR / "api" / "review_assistant" / "business_links.json"
BACKUP_BASE_DIR = ROOT_DIR / "data" / "backups"


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_table_counts(db_path: Path) -> dict[str, int]:
    """Retrieves record counts across all relational tables."""
    counts = {}
    with sqlite3.connect(db_path) as db:
        tables = [
            "tenants", "users", "tenant_memberships",
            "sessions", "analytics_events", "private_tickets"
        ]
        for t in tables:
            try:
                row = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
                counts[t] = int(row[0]) if row else 0
            except sqlite3.OperationalError:
                counts[t] = 0
    return counts


def create_backup(dest_dir: Path | None = None) -> Path:
    """Creates a consistent, hot SQLite backup and metadata manifest."""
    source_db = Path(os.getenv("REVIEW_DB_PATH", str(DEFAULT_DB_PATH))).resolve()
    source_cfg = Path(os.getenv("BUSINESS_LINKS_PATH", str(DEFAULT_CONFIG_PATH))).resolve()

    if not source_db.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    target = (dest_dir or (BACKUP_BASE_DIR / f"snapshot_{timestamp}")).resolve()
    target.mkdir(parents=True, exist_ok=True)

    backup_db_path = target / "reviews.sqlite3"
    print(f"[*] Creating hot SQLite snapshot from {source_db}...")
    # Use SQLite Online Backup API for hot, transactionally consistent snapshot
    with sqlite3.connect(source_db) as src, sqlite3.connect(backup_db_path) as dst:
        src.backup(dst)

    # Checkpoint and verify backup integrity
    with sqlite3.connect(backup_db_path) as chk:
        integrity = chk.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")

    # Copy config JSON if present
    backup_cfg_path = None
    if source_cfg.exists():
        backup_cfg_path = target / "business_links.json"
        shutil.copy2(source_cfg, backup_cfg_path)

    # Build manifest
    counts = get_table_counts(backup_db_path)
    manifest = {
        "timestamp": timestamp,
        "created_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_db": str(source_db),
        "source_db_sha256": compute_sha256(backup_db_path),
        "source_cfg": str(source_cfg) if source_cfg.exists() else None,
        "source_cfg_sha256": compute_sha256(backup_cfg_path) if backup_cfg_path else None,
        "table_counts": counts,
        "sqlite_integrity": integrity
    }

    manifest_path = target / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Backup successfully created at: {target}")
    print(f"    Table Counts: {counts}")
    print(f"    Integrity: {integrity}")
    return target


def verify_backup(backup_dir: Path) -> bool:
    """Verifies checksums and integrity of a backup archive."""
    manifest_path = backup_dir / "manifest.json"
    db_path = backup_dir / "reviews.sqlite3"

    if not manifest_path.exists() or not db_path.exists():
        print(f"[-] Invalid backup archive in {backup_dir}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Check hash
    current_hash = compute_sha256(db_path)
    if current_hash != manifest.get("source_db_sha256"):
        print(f"[-] Checksum mismatch for database file!")
        return False

    # Check SQLite integrity
    with sqlite3.connect(db_path) as db:
        res = db.execute("PRAGMA integrity_check").fetchone()[0]
        if res != "ok":
            print(f"[-] PRAGMA integrity_check failed: {res}")
            return False

    counts = get_table_counts(db_path)
    print(f"[+] Backup verification PASSED for {backup_dir}")
    print(f"    Manifest Counts: {manifest.get('table_counts')}")
    print(f"    Verified Counts: {counts}")
    return True


def restore_backup(backup_dir: Path, restore_dir: Path, allow_overwrite: bool = False) -> bool:
    """Safely restores a backup into an isolated target location."""
    db_path = backup_dir / "reviews.sqlite3"
    cfg_path = backup_dir / "business_links.json"

    if not db_path.exists():
        print(f"[-] Backup database does not exist: {db_path}")
        return False

    active_db = DEFAULT_DB_PATH.resolve()
    target_db = (restore_dir / "reviews.sqlite3").resolve()

    if target_db == active_db and not allow_overwrite:
        print("[-] Refusing to overwrite active production/working database directly.")
        print("    Specify an isolated restore directory (e.g. /tmp/restore_test/) or pass --allow-overwrite.")
        return False

    restore_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, target_db)
    if cfg_path.exists():
        shutil.copy2(cfg_path, restore_dir / "business_links.json")

    # Verify restored database
    with sqlite3.connect(target_db) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            print(f"[-] Restored database integrity failed: {integrity}")
            return False

    counts = get_table_counts(target_db)
    print(f"[+] Backup successfully restored to: {restore_dir}")
    print(f"    Restored Integrity: {integrity}")
    print(f"    Restored Table Counts: {counts}")
    return True


def main():
    parser = argparse.ArgumentParser(description="NastaGhar Backup and Restore Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a hot online backup")
    backup_parser.add_argument("--out", type=Path, default=None, help="Output directory")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a backup archive")
    verify_parser.add_argument("backup_dir", type=Path, help="Path to backup directory")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore backup to a target directory")
    restore_parser.add_argument("backup_dir", type=Path, help="Path to backup directory")
    restore_parser.add_argument("--dest", type=Path, required=True, help="Isolated target directory")
    restore_parser.add_argument("--allow-overwrite", action="store_true", help="Permit writing over working db")

    args = parser.parse_args()

    if args.command == "backup":
        create_backup(args.out)
    elif args.command == "verify":
        success = verify_backup(args.backup_dir)
        sys.exit(0 if success else 1)
    elif args.command == "restore":
        success = restore_backup(args.backup_dir, args.dest, args.allow_overwrite)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
