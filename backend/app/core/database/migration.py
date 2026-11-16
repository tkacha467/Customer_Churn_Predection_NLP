"""
Idempotent Database Migration for ChurnLens / NastaGhar Multi-Tenant Architecture.
Supports Phase 1 legacy JSON migration as well as Phase 2 Subpart 2B Shared Profile
Schema Migration, Data Reconciliation, Conflict Auditing, and Transaction Guarantees.
"""

import hashlib
import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.tenants.google_reviews import SOURCE_CONFIG_FILE, CONFIG_FILE, DEFAULT_TOPICS

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Raised when a database migration fails or must be rolled back."""
    pass


class InvariantViolationError(MigrationError):
    """Raised when a critical database invariant (e.g. journal_mode) is violated."""
    pass


# ---------------------------------------------------------------------------
# Phase 2 Subpart 2B: Normalization & Field Mapping
# ---------------------------------------------------------------------------

SHARED_FIELD_PAIRS: List[Tuple[str, str]] = [
    ("display_name", "business_name"),
    ("category", "category"),
    ("branch_name", "branch"),
    ("description", "description"),
    ("timezone", "timezone"),
]


def normalize_field_value(val: Optional[str]) -> str:
    """Normalizes None, empty string, and whitespace-only strings to empty string ('')."""
    if val is None:
        return ""
    return str(val).strip()


def ensure_column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str, col_type_sql: str) -> bool:
    """
    Checks table columns using PRAGMA table_info.
    Adds the column using ALTER TABLE ADD COLUMN only if not already present.
    Returns True if added, False if already existed.
    """
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if column_name not in existing_cols:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type_sql};")
        return True
    return False


# ---------------------------------------------------------------------------
# Phase 2 Subpart 2B: Schema Alterations & Partial Unique Index
# ---------------------------------------------------------------------------

def apply_phase2_schema_alterations(db: sqlite3.Connection) -> Dict[str, Any]:
    """
    Applies guarded column additions to business_profiles and tenants,
    and creates the migration_conflicts table with partial unique index.
    """
    cursor = db.cursor()
    added_columns: List[str] = []

    # 1. business_profiles columns
    if ensure_column_exists(cursor, "business_profiles", "branch_name", "TEXT DEFAULT ''"):
        added_columns.append("business_profiles.branch_name")
    if ensure_column_exists(cursor, "business_profiles", "description", "TEXT DEFAULT ''"):
        added_columns.append("business_profiles.description")
    if ensure_column_exists(cursor, "business_profiles", "brand_accent", "TEXT DEFAULT NULL"):
        added_columns.append("business_profiles.brand_accent")
    if ensure_column_exists(cursor, "business_profiles", "timezone", "TEXT DEFAULT 'Asia/Kolkata'"):
        added_columns.append("business_profiles.timezone")

    # 2. tenants column
    if ensure_column_exists(cursor, "tenants", "timezone", "TEXT DEFAULT 'Asia/Kolkata'"):
        added_columns.append("tenants.timezone")

    # 3. migration_conflicts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            field_name TEXT NOT NULL,
            tenants_value TEXT,
            profile_value TEXT,
            proposed_canonical TEXT NOT NULL,
            conflict_type TEXT NOT NULL DEFAULT 'SUBSTANTIVE',
            status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
            conflict_fingerprint TEXT NOT NULL,
            resolved_value TEXT,
            resolved_by TEXT,
            resolution_notes TEXT DEFAULT '',
            detected_at REAL NOT NULL,
            resolved_at REAL
        );
    """)

    # 4. Partial Unique Index: Exactly one pending conflict allowed per (tenant_id, field_name)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_active_pending_conflicts 
        ON migration_conflicts(tenant_id, field_name) 
        WHERE status = 'PENDING_REVIEW';
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_migration_conflicts_lookup 
        ON migration_conflicts(tenant_id, status);
    """)

    return {"added_columns": added_columns}


# ---------------------------------------------------------------------------
# Phase 2 Subpart 2B: Provision Missing business_profiles Rows
# ---------------------------------------------------------------------------

def provision_unprovisioned_tenants(db: sqlite3.Connection) -> Dict[str, Any]:
    """
    Identifies tenants registered in tenants that lack an entry in business_profiles.
    Dynamically counts and provisions exactly one initial profile row for each unprovisioned tenant.
    """
    now = time.time()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, business_name, category, branch, description 
        FROM tenants 
        WHERE id NOT IN (SELECT tenant_id FROM business_profiles);
    """)
    unprovisioned = cursor.fetchall()

    provisioned_tenants = []
    for row in unprovisioned:
        t_id = row["id"] if isinstance(row, sqlite3.Row) else row[0]
        b_name = row["business_name"] if isinstance(row, sqlite3.Row) else row[1]
        cat = row["category"] if isinstance(row, sqlite3.Row) else row[2]
        branch = row["branch"] if isinstance(row, sqlite3.Row) else row[3]
        desc = row["description"] if isinstance(row, sqlite3.Row) else row[4]

        cursor.execute("""
            INSERT INTO business_profiles (
                tenant_id, display_name, category, branch_name, description,
                brand_accent, timezone, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, NULL, 'Asia/Kolkata', ?, ?);
        """, (t_id, b_name or "", cat or "", branch or "", desc or "", now, now))
        provisioned_tenants.append(t_id)

    return {
        "unprovisioned_count": len(unprovisioned),
        "provisioned_count": len(provisioned_tenants),
        "provisioned_tenant_ids": provisioned_tenants
    }


def resolve_obsolete_pending_conflict(
    cursor: sqlite3.Cursor,
    tenant_id: str,
    field_name: str,
    reconciled_value: Optional[str],
    now: float,
) -> bool:
    """
    If an active PENDING_REVIEW conflict exists for this tenant and field,
    transitions it to RESOLVED because the underlying discrepancy has been eliminated.
    Preserves historical records and returns True if a pending conflict was resolved.
    """
    cursor.execute("""
        SELECT id FROM migration_conflicts 
        WHERE tenant_id = ? AND field_name = ? AND status = 'PENDING_REVIEW';
    """, (tenant_id, field_name))
    row = cursor.fetchone()
    if row:
        conflict_id = row["id"] if isinstance(row, sqlite3.Row) else row[0]
        cursor.execute("""
            UPDATE migration_conflicts 
            SET status = 'RESOLVED',
                resolved_value = ?,
                resolved_by = 'SYSTEM_RECONCILIATION',
                resolution_notes = 'Auto-resolved: underlying discrepancy eliminated.',
                resolved_at = ?
            WHERE id = ?;
        """, (reconciled_value, now, conflict_id))
        return True
    return False


# ---------------------------------------------------------------------------
# Phase 2 Subpart 2B: Existing Data Reconciliation & Conflict Detection
# ---------------------------------------------------------------------------

def reconcile_and_audit_existing_records(db: sqlite3.Connection) -> Dict[str, int]:
    """
    Field-by-field reconciliation and conflict auditing between tenants and business_profiles.
    Guarantees zero silent overwrites, idempotency, exact casing preservation, and
    whitespace-equivalent normalized comparisons.
    """
    now = time.time()
    cursor = db.cursor()
    stats = {
        "backfilled_canonical": 0,
        "mirrored_legacy": 0,
        "substantive_conflicts": 0,
        "case_conflicts": 0,
        "matching_fields": 0,
        "pending_skipped": 0,
        "pending_mutated": 0,
        "new_conflicts": 0,
        "auto_resolved": 0,
    }

    cursor.execute("""
        SELECT 
            t.id AS tenant_id,
            t.business_name AS t_business_name,
            t.category AS t_category,
            t.branch AS t_branch,
            t.description AS t_description,
            t.timezone AS t_timezone,
            p.display_name AS p_display_name,
            p.category AS p_category,
            p.branch_name AS p_branch_name,
            p.description AS p_description,
            p.timezone AS p_timezone
        FROM tenants t
        INNER JOIN business_profiles p ON t.id = p.tenant_id;
    """)
    rows = cursor.fetchall()

    for row in rows:
        tenant_id = row["tenant_id"]

        for p_col, t_col in SHARED_FIELD_PAIRS:
            raw_t = row[f"t_{t_col}"]
            raw_p = row[f"p_{p_col}"]

            norm_t = normalize_field_value(raw_t)
            norm_p = normalize_field_value(raw_p)

            # Case 1: Both empty
            if norm_p == "" and norm_t == "":
                if resolve_obsolete_pending_conflict(cursor, tenant_id, p_col, "", now):
                    stats["auto_resolved"] += 1
                stats["matching_fields"] += 1
                continue

            # Case 2: Canonical empty, legacy tenant populated -> Backfill canonical
            if norm_p == "" and norm_t != "":
                cursor.execute(
                    f"UPDATE business_profiles SET {p_col} = ?, updated_at = ? WHERE tenant_id = ?",
                    (raw_t, now, tenant_id)
                )
                if resolve_obsolete_pending_conflict(cursor, tenant_id, p_col, raw_t, now):
                    stats["auto_resolved"] += 1
                stats["backfilled_canonical"] += 1
                continue

            # Case 3: Canonical populated, legacy tenant empty -> Mirror to legacy
            if norm_p != "" and norm_t == "":
                cursor.execute(
                    f"UPDATE tenants SET {t_col} = ?, updated_at = ? WHERE id = ?",
                    (raw_p, now, tenant_id)
                )
                if resolve_obsolete_pending_conflict(cursor, tenant_id, p_col, raw_p, now):
                    stats["auto_resolved"] += 1
                stats["mirrored_legacy"] += 1
                continue

            # Case 4: Both populated and normalized match (exact match or whitespace equivalence)
            # Must execute BEFORE case-difference detection!
            if norm_p == norm_t:
                if resolve_obsolete_pending_conflict(cursor, tenant_id, p_col, raw_p, now):
                    stats["auto_resolved"] += 1
                stats["matching_fields"] += 1
                continue

            # Case 5 & 6: Divergence detected
            is_case_diff = (norm_p.lower() == norm_t.lower())
            conflict_type = "CASE_DIFFERENCE" if is_case_diff else "SUBSTANTIVE"
            proposed_canonical = raw_p  # Canonical profile proposed for review

            if is_case_diff:
                stats["case_conflicts"] += 1
            else:
                stats["substantive_conflicts"] += 1

            fingerprint_src = f"{tenant_id}:{p_col}:{norm_t}:{norm_p}".encode("utf-8")
            fingerprint = hashlib.sha256(fingerprint_src).hexdigest()

            cursor.execute("""
                SELECT id, conflict_fingerprint 
                FROM migration_conflicts 
                WHERE tenant_id = ? AND field_name = ? AND status = 'PENDING_REVIEW';
            """, (tenant_id, p_col))
            existing_pending = cursor.fetchone()

            if existing_pending:
                stored_fp = existing_pending["conflict_fingerprint"] if isinstance(existing_pending, sqlite3.Row) else existing_pending[1]
                c_id = existing_pending["id"] if isinstance(existing_pending, sqlite3.Row) else existing_pending[0]
                if stored_fp == fingerprint:
                    stats["pending_skipped"] += 1
                else:
                    cursor.execute("""
                        UPDATE migration_conflicts 
                        SET tenants_value = ?,
                            profile_value = ?,
                            proposed_canonical = ?,
                            conflict_type = ?,
                            conflict_fingerprint = ?,
                            detected_at = ?
                        WHERE id = ?;
                    """, (raw_t, raw_p, proposed_canonical, conflict_type, fingerprint, now, c_id))
                    stats["pending_mutated"] += 1
            else:
                cursor.execute("""
                    INSERT INTO migration_conflicts (
                        tenant_id, field_name, tenants_value, profile_value,
                        proposed_canonical, conflict_type, status,
                        conflict_fingerprint, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', ?, ?);
                """, (tenant_id, p_col, raw_t, raw_p, proposed_canonical, conflict_type, fingerprint, now))
                stats["new_conflicts"] += 1

    return stats


# ---------------------------------------------------------------------------
# Phase 2 Subpart 2B: Transaction Runner with Pre-Commit Verification
# ---------------------------------------------------------------------------

def run_subpart_2b_migration(db: sqlite3.Connection) -> Dict[str, Any]:
    """
    Executes Subpart 2B within an explicit immediate transaction.
    Preserves existing journal_mode without alteration, enables and verifies
    PRAGMA foreign_keys = ON before beginning the transaction, verifies journal_mode
    before COMMIT (triggering rollback on violation), and raises an explicit error
    if an invariant violation occurs during or after rollback.
    """
    # Safety Check: Verify connection is not already inside a transaction
    if getattr(db, "in_transaction", False):
        raise MigrationError("SQLite connection is already in an active transaction; cannot execute PRAGMA pre-checks.")

    # Ensure row_factory is sqlite3.Row for dictionary-like column access
    db.row_factory = sqlite3.Row

    # 1. Read and record existing journal mode (MUST NOT be altered)
    initial_journal_mode = db.execute("PRAGMA journal_mode;").fetchone()[0]

    # 2. Enable and verify foreign key constraint enforcement prior to transaction
    db.execute("PRAGMA foreign_keys = ON;")
    fk_status = db.execute("PRAGMA foreign_keys;").fetchone()[0]
    if fk_status != 1:
        raise MigrationError(
            f"SQLite foreign_keys constraint enforcement could not be enabled (returned {fk_status}). Migration aborted."
        )

    # 3. Begin immediate transaction
    db.execute("BEGIN IMMEDIATE TRANSACTION;")
    try:
        # Step 1: Guarded column additions (PRAGMA table_info inspection + ALTER TABLE)
        schema_stats = apply_phase2_schema_alterations(db)

        # Step 2: Provision unprovisioned tenants (INSERT INTO business_profiles)
        provision_stats = provision_unprovisioned_tenants(db)

        # Step 3: Reconcile existing records and audit conflicts
        reconciliation_stats = reconcile_and_audit_existing_records(db)

        # Step 4: PRE-COMMIT INVARIANT CHECK — Verify journal mode is unchanged WHILE TRANSACTION IS ACTIVE
        pre_commit_journal_mode = db.execute("PRAGMA journal_mode;").fetchone()[0]
        if pre_commit_journal_mode.lower() != initial_journal_mode.lower():
            raise InvariantViolationError(
                f"FATAL PRE-COMMIT VIOLATION: Database journal_mode changed from '{initial_journal_mode}' to '{pre_commit_journal_mode}'! Aborting transaction."
            )

        # Commit entire migration atomically ONLY AFTER all pre-commit checks pass
        db.execute("COMMIT;")

        # Step 5: Post-commit diagnostic assertion (Note: committed transaction cannot be undone by rollback)
        post_commit_journal_mode = db.execute("PRAGMA journal_mode;").fetchone()[0]
        if post_commit_journal_mode.lower() != initial_journal_mode.lower():
            logger.critical(
                f"DIAGNOSTIC ALERT: Database journal_mode changed from '{initial_journal_mode}' to '{post_commit_journal_mode}' post-commit."
            )

        return {
            "initial_journal_mode": initial_journal_mode,
            "foreign_keys_active": True,
            "schema_alterations": schema_stats,
            "provisioning": provision_stats,
            "reconciliation": reconciliation_stats
        }
    except Exception as exc:
        db.execute("ROLLBACK;")
        # Verify journal mode after rollback — NEVER silently ignore violations
        post_rollback_journal_mode = db.execute("PRAGMA journal_mode;").fetchone()[0]
        if post_rollback_journal_mode.lower() != initial_journal_mode.lower():
            raise InvariantViolationError(
                f"CRITICAL INVARIANT VIOLATION: Database journal_mode was corrupted from '{initial_journal_mode}' to '{post_rollback_journal_mode}' during migration failure/rollback! Original error: {exc}"
            ) from exc
        raise MigrationError(f"Subpart 2B migration failed and was rolled back: {exc}") from exc


# ---------------------------------------------------------------------------
# Phase 1 Legacy Migration Function (Preserved 100% Intact)
# ---------------------------------------------------------------------------

def migrate_database(
    database_path: Optional[str] = None,
    json_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Executes a non-destructive, idempotent migration:
    1. Ensures all tables (tenants, users, tenant_memberships, sessions) exist.
    2. Imports all businesses from business_links.json into SQLite tenants.
    3. Verifies counts and data equivalence.
    4. Does not delete or rewrite original files.
    """
    store = ReviewStore(database_path=database_path)
    source = json_path or (CONFIG_FILE if CONFIG_FILE.exists() else SOURCE_CONFIG_FILE)
    
    migrated_count = 0
    errors = []

    if source.exists():
        try:
            with open(source, "r", encoding="utf-8") as f:
                links_data = json.load(f)
        except Exception as e:
            links_data = {}
            errors.append(f"Failed to read source json: {e}")
    else:
        links_data = {}

    # Always ensure default_business is present
    if "default_business" not in links_data:
        links_data["default_business"] = {
            "business_name": "Nasta Ghar",
            "branch": "",
            "category": "Breakfast & Snacks",
            "description": "Authentic homestyle breakfast, chai, and snacks in Rajkot.",
            "google_review_url": os.getenv("GOOGLE_REVIEW_URL", "https://maps.google.com"),
            "platform": "google",
            "topics": DEFAULT_TOPICS,
            "primary_accent": "#f97316"
        }

    for b_id, info in links_data.items():
        try:
            # SAFETY CHECK: Do not overwrite newer SQLite data with stale JSON configuration
            existing = store.get_tenant(b_id)
            if existing:
                # Tenant already exists in SQLite; preserve SQLite as the active source of truth
                continue

            category = info.get("category", "Breakfast & Snacks")
            topics = info.get("topics") or DEFAULT_TOPICS
            tenant_payload = {
                "id": b_id,
                "business_name": info.get("business_name", "Nasta Ghar"),
                "status": "active",
                "platform": info.get("platform", "google"),
                "review_url": info.get("google_review_url") or info.get("review_url", ""),
                "branch": info.get("branch", ""),
                "category": category,
                "description": info.get("description", ""),
                "topics": topics,
                "primary_accent": info.get("primary_accent", "#f97316")
            }
            store.upsert_tenant(tenant_payload)
            migrated_count += 1
        except Exception as e:
            errors.append(f"Error migrating business '{b_id}': {e}")

    # Ensure legacy owner user exists for backward compatibility
    store.get_or_create_legacy_owner()
    total_tenants = len(store.list_tenants())
    
    return {
        "success": len(errors) == 0,
        "source_file": str(source),
        "source_entries": len(links_data),
        "migrated_entries": migrated_count,
        "total_tenants_in_db": total_tenants,
        "errors": errors,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    result = migrate_database()
    print("Migration Result:", json.dumps(result, indent=2))
