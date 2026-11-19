#!/usr/bin/env python3
"""
VRAJA AI — Phase A2 Additive Industry Migration Script
Adds optional `industry_id` column to `tenants` table idempotently.

SAFETY DIRECTIVE:
Per Section 3.2, this script is provided for staging/deployment environments
and is NOT executed automatically against the production database without separate approval.
"""

import sys
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"


def migrate_industry_column(db_path: Path) -> bool:
    if not db_path.exists():
        print(f"[Error] Database file not found at: {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(tenants)")
        columns = [row[1] for row in cur.fetchall()]

        if "industry_id" in columns:
            print("[Info] Column `industry_id` already exists in `tenants`. Migration already applied.")
            return True

        print("[Info] Adding `industry_id TEXT DEFAULT NULL` column to `tenants` table...")
        cur.execute("ALTER TABLE tenants ADD COLUMN industry_id TEXT DEFAULT NULL")
        conn.commit()
        print("[Success] Column `industry_id` added successfully.")
        return True
    except Exception as e:
        print(f"[Error] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def rollback_industry_column(db_path: Path) -> bool:
    """
    Rollback strategy:
    In SQLite 3.35.0+, columns can be dropped via `ALTER TABLE tenants DROP COLUMN industry_id`.
    Alternatively, setting `UPDATE tenants SET industry_id = NULL` neutralizes values safely.
    """
    if not db_path.exists():
        print(f"[Error] Database file not found at: {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(tenants)")
        columns = [row[1] for row in cur.fetchall()]

        if "industry_id" not in columns:
            print("[Info] Column `industry_id` does not exist in `tenants`. Nothing to rollback.")
            return True

        try:
            print("[Info] Attempting ALTER TABLE DROP COLUMN...")
            cur.execute("ALTER TABLE tenants DROP COLUMN industry_id")
            conn.commit()
            print("[Success] Column `industry_id` dropped successfully.")
            return True
        except sqlite3.OperationalError:
            print("[Notice] SQLite engine does not support DROP COLUMN. Neutralizing column values...")
            cur.execute("UPDATE tenants SET industry_id = NULL")
            conn.commit()
            print("[Success] All `industry_id` values set to NULL.")
            return True
    except Exception as e:
        print(f"[Error] Rollback failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    db_target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    action = sys.argv[2] if len(sys.argv) > 2 else "migrate"

    print(f"Target Database: {db_target}")
    if action == "rollback":
        success = rollback_industry_column(db_target)
    else:
        success = migrate_industry_column(db_target)
    sys.exit(0 if success else 1)
