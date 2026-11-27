"""
Comprehensive Automated Test Suite for Phase 2 Subpart 2B
Schema Migration, Data Reconciliation, Conflict Auditing, and Transaction Invariants.

Fulfills all 15 test scenarios specified in VRAJA AI Phase 2 Specification Revision 2.7.
All tests operate strictly against temporary isolated SQLite databases.
"""

import hashlib
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest

from backend.app.core.database.migration import (
    run_subpart_2b_migration,
    apply_phase2_schema_alterations,
    provision_unprovisioned_tenants,
    reconcile_and_audit_existing_records,
    normalize_field_value,
    MigrationError,
    InvariantViolationError,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROD_DB_PATH = REPO_ROOT / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3"


def _get_prod_db_hash() -> Optional[str]:
    """Capture the baseline SHA-256 hash of the production database at session start."""
    if not PROD_DB_PATH.exists():
        return None
    with open(PROD_DB_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


INITIAL_PROD_HASH = _get_prod_db_hash()


@pytest.fixture
def isolated_db_copy(tmp_path):
    """
    Creates an isolated pre-migration SQLite database in a temporary directory.
    Uses a temporary clone when local developer DB is present, or builds a
    deterministic WAL-mode pre-migration fixture when running in clean CI checkouts.
    """
    temp_db = tmp_path / "test_reviews.sqlite3"
    if PROD_DB_PATH.exists():
        shutil.copy2(PROD_DB_PATH, temp_db)

        prod_wal = PROD_DB_PATH.with_name(PROD_DB_PATH.name + "-wal")
        if prod_wal.exists():
            shutil.copy2(prod_wal, tmp_path / prod_wal.name)
        prod_shm = PROD_DB_PATH.with_name(PROD_DB_PATH.name + "-shm")
        if prod_shm.exists():
            shutil.copy2(prod_shm, tmp_path / prod_shm.name)

        con = sqlite3.connect(str(temp_db), timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
    else:
        con = sqlite3.connect(str(temp_db), timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("""
            CREATE TABLE tenants (
                id TEXT PRIMARY KEY,
                business_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                platform TEXT DEFAULT 'google',
                review_url TEXT,
                branch TEXT DEFAULT '',
                category TEXT DEFAULT '',
                description TEXT DEFAULT '',
                topics_json TEXT DEFAULT '[]',
                primary_accent TEXT DEFAULT '#f97316',
                entitlements_json TEXT DEFAULT '["review_manager"]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)
        con.execute("""
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
                primary_accent TEXT DEFAULT '#078BFF'
            );
        """)
        now = time.time()
        con.execute("""
            INSERT INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, entitlements_json, created_at, updated_at
            ) VALUES (
                'default_business', 'Nasta Ghar', 'active', 'google',
                'https://search.google.com/local/writereview?placeid=ChIJTestDefault',
                'Main Branch', 'Breakfast & Snacks', 'Authentic breakfast',
                '["Breakfast","Chai"]', '#f97316', '["review_manager","digital_card"]', ?, ?
            );
        """, (now, now))
        con.execute("""
            INSERT INTO business_profiles (
                tenant_id, display_name, category, background_preset, overlay_opacity,
                custom_links_json, primary_accent, created_at, updated_at
            ) VALUES (
                'default_business', 'Nasta Ghar', 'Breakfast & Snacks', 'default_navy', 0.75,
                '[]', '#078BFF', ?, ?
            );
        """, (now, now))
        con.execute("""
            INSERT INTO tenants (
                id, business_name, status, platform, review_url, branch, category,
                description, topics_json, primary_accent, entitlements_json, created_at, updated_at
            ) VALUES (
                'ci_unprovisioned_cafe', 'CI Unprovisioned Cafe', 'active', 'google',
                'https://search.google.com/local/writereview?placeid=ChIJTestCI',
                'Downtown', 'Cafe', 'Synthetic CI test tenant',
                '["Coffee"]', '#10b981', '["review_manager"]', ?, ?
            );
        """, (now, now))

    yield con, temp_db
    con.close()


@pytest.fixture
def fresh_synthetic_db(tmp_path):
    """
    Creates a fresh minimal database with standard pre-migration schema and WAL mode
    for controlled synthetic testing of edge cases.
    """
    temp_db = tmp_path / "synthetic_reviews.sqlite3"
    con = sqlite3.connect(str(temp_db), timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row

    # Match production WAL mode
    con.execute("PRAGMA journal_mode = WAL;")

    # Pre-migration tables (matching exact live schema)
    con.execute("""
        CREATE TABLE tenants (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            platform TEXT DEFAULT 'google',
            review_url TEXT,
            branch TEXT DEFAULT '',
            category TEXT DEFAULT '',
            description TEXT DEFAULT '',
            topics_json TEXT DEFAULT '[]',
            primary_accent TEXT DEFAULT '#f97316',
            entitlements_json TEXT DEFAULT '["review_manager"]',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
    """)

    con.execute("""
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
            primary_accent TEXT DEFAULT '#078BFF'
        );
    """)

    yield con, temp_db
    con.close()


# ==============================================================================
# Scenario 1: Column Existence Verification
# ==============================================================================

def test_01_column_existence_verification(isolated_db_copy):
    con, _ = isolated_db_copy
    result = run_subpart_2b_migration(con)
    assert result["foreign_keys_active"] is True

    # Check business_profiles columns
    bp_cols = {row["name"]: row["type"] for row in con.execute("PRAGMA table_info(business_profiles);").fetchall()}
    assert "branch_name" in bp_cols
    assert "description" in bp_cols
    assert "brand_accent" in bp_cols
    assert "timezone" in bp_cols

    # Check tenants columns
    t_cols = {row["name"]: row["type"] for row in con.execute("PRAGMA table_info(tenants);").fetchall()}
    assert "timezone" in t_cols

    # Check migration_conflicts table exists
    assert con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migration_conflicts';").fetchone() is not None


# ==============================================================================
# Scenario 2: Preservation of Existing Data & Product Settings
# ==============================================================================

def test_02_preservation_of_existing_data(isolated_db_copy):
    con, _ = isolated_db_copy
    # Snapshot existing default_business before migration
    t_before = dict(con.execute("SELECT * FROM tenants WHERE id = 'default_business';").fetchone())
    bp_before = dict(con.execute("SELECT * FROM business_profiles WHERE tenant_id = 'default_business';").fetchone())

    run_subpart_2b_migration(con)

    t_after = dict(con.execute("SELECT * FROM tenants WHERE id = 'default_business';").fetchone())
    bp_after = dict(con.execute("SELECT * FROM business_profiles WHERE tenant_id = 'default_business';").fetchone())

    # Product A settings preserved
    assert t_after["business_name"] == t_before["business_name"]
    assert t_after["review_url"] == t_before["review_url"]
    assert t_after["primary_accent"] == t_before["primary_accent"]
    assert t_after["topics_json"] == t_before["topics_json"]

    # Product B settings preserved
    assert bp_after["background_preset"] == bp_before["background_preset"]
    assert bp_after["overlay_opacity"] == bp_before["overlay_opacity"]
    assert bp_after["custom_links_json"] == bp_before["custom_links_json"]
    assert bp_after["primary_accent"] == bp_before["primary_accent"]


# ==============================================================================
# Scenario 3: Exact Provisioning Count (Dynamic Check)
# ==============================================================================

def test_03_exact_provisioning_count(isolated_db_copy):
    con, _ = isolated_db_copy
    # Dynamically find unprovisioned tenants before migration
    unprovisioned_before = [dict(r) for r in con.execute("""
        SELECT id, business_name, category, branch, description 
        FROM tenants 
        WHERE id NOT IN (SELECT tenant_id FROM business_profiles);
    """).fetchall()]
    expected_count = len(unprovisioned_before)
    assert expected_count > 0, "Expected at least one unprovisioned tenant in live snapshot"

    result = run_subpart_2b_migration(con)
    assert result["provisioning"]["provisioned_count"] == expected_count

    # Verify each now has exactly one profile with initialized values
    for t in unprovisioned_before:
        t_id = t["id"]
        rows = con.execute("SELECT * FROM business_profiles WHERE tenant_id = ?;", (t_id,)).fetchall()
        assert len(rows) == 1
        p = dict(rows[0])
        assert p["display_name"] == t["business_name"]
        assert p["category"] == t["category"]
        assert p["branch_name"] == t["branch"]
        assert p["description"] == t["description"]
        assert p["timezone"] == "Asia/Kolkata"
        assert p["brand_accent"] is None


# ==============================================================================
# Scenario 4: Whitespace Equivalence & Normalization Test
# ==============================================================================

def test_04_whitespace_equivalence_and_normalization(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    # Insert tenant with leading/trailing whitespace and NULL description
    con.execute("""
        INSERT INTO tenants (id, business_name, category, branch, description, created_at, updated_at)
        VALUES ('ws_test', '  VRAJA AI  ', '   ', 'Downtown', NULL, ?, ?);
    """, (now, now))

    # Insert pre-migration profile with trimmed name and empty category
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, category, created_at, updated_at)
        VALUES ('ws_test', 'VRAJA AI', '', ?, ?);
    """, (now, now))

    run_subpart_2b_migration(con)

    # Assert 0 conflicts created between "  VRAJA AI  " and "VRAJA AI", or whitespace and empty
    conflicts = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'ws_test';").fetchall()
    assert len(conflicts) == 0, f"Expected 0 conflicts for whitespace-equivalent records, got: {conflicts}"


# ==============================================================================
# Scenario 5: Canonical Backfill Test
# ==============================================================================

def test_05_canonical_backfill_test(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, category, branch, description, created_at, updated_at)
        VALUES ('bf_test', 'Chai Point', 'Beverages', 'Central Mall', 'Fresh hot chai', ?, ?);
    """, (now, now))

    # Pre-migration profile (branch_name and description do not exist yet; added during migration)
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, category, created_at, updated_at)
        VALUES ('bf_test', 'Chai Point', 'Beverages', ?, ?);
    """, (now, now))

    result = run_subpart_2b_migration(con)
    assert result["reconciliation"]["backfilled_canonical"] >= 1

    row = con.execute("SELECT branch_name, description FROM business_profiles WHERE tenant_id = 'bf_test';").fetchone()
    assert row["branch_name"] == "Central Mall"
    assert row["description"] == "Fresh hot chai"

    # No conflict should be logged
    assert len(con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'bf_test';").fetchall()) == 0


# ==============================================================================
# Scenario 6: Substantive Conflict Test
# ==============================================================================

def test_06_substantive_conflict_test(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, category, created_at, updated_at)
        VALUES ('sub_test', 'Artisan Cafe', 'Cafe', ?, ?);
    """, (now, now))

    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, category, created_at, updated_at)
        VALUES ('sub_test', 'Artisan Roasters', 'Cafe', ?, ?);
    """, (now, now))

    result = run_subpart_2b_migration(con)
    assert result["reconciliation"]["substantive_conflicts"] == 1

    # Check neither value was overwritten
    assert con.execute("SELECT business_name FROM tenants WHERE id = 'sub_test';").fetchone()["business_name"] == "Artisan Cafe"
    assert con.execute("SELECT display_name FROM business_profiles WHERE tenant_id = 'sub_test';").fetchone()["display_name"] == "Artisan Roasters"

    # Check conflict entry
    conflict = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'sub_test' AND field_name = 'display_name';").fetchone()
    assert conflict is not None
    assert conflict["conflict_type"] == "SUBSTANTIVE"
    assert conflict["status"] == "PENDING_REVIEW"
    assert conflict["tenants_value"] == "Artisan Cafe"
    assert conflict["profile_value"] == "Artisan Roasters"
    assert conflict["proposed_canonical"] == "Artisan Roasters"

    # Check fingerprint calculation
    expected_fp = hashlib.sha256("sub_test:display_name:Artisan Cafe:Artisan Roasters".encode("utf-8")).hexdigest()
    assert conflict["conflict_fingerprint"] == expected_fp


# ==============================================================================
# Scenario 7: Case-Only Difference Test
# ==============================================================================

def test_07_case_only_difference_test(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('case_test', 'eBay', ?, ?);
    """, (now, now))

    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
        VALUES ('case_test', 'Ebay', ?, ?);
    """, (now, now))

    result = run_subpart_2b_migration(con)
    assert result["reconciliation"]["case_conflicts"] == 1

    # Original casing preserved in both tables (zero auto-title-casing)
    assert con.execute("SELECT business_name FROM tenants WHERE id = 'case_test';").fetchone()["business_name"] == "eBay"
    assert con.execute("SELECT display_name FROM business_profiles WHERE tenant_id = 'case_test';").fetchone()["display_name"] == "Ebay"

    conflict = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'case_test' AND field_name = 'display_name';").fetchone()
    assert conflict is not None
    assert conflict["conflict_type"] == "CASE_DIFFERENCE"
    assert conflict["status"] == "PENDING_REVIEW"
    assert conflict["tenants_value"] == "eBay"
    assert conflict["profile_value"] == "Ebay"


# ==============================================================================
# Scenario 8: Rerun Idempotency Test
# ==============================================================================

def test_08_rerun_idempotency_test(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('idem_test', 'Original Name', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
        VALUES ('idem_test', 'Divergent Name', ?, ?);
    """, (now, now))

    # Run 1
    r1 = run_subpart_2b_migration(con)
    assert r1["reconciliation"]["substantive_conflicts"] == 1
    assert r1["reconciliation"]["new_conflicts"] == 1

    initial_conflict_count = con.execute("SELECT COUNT(*) FROM migration_conflicts;").fetchone()[0]

    # Run 2
    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["pending_skipped"] >= 1
    assert r2["reconciliation"]["new_conflicts"] == 0

    # Run 3
    r3 = run_subpart_2b_migration(con)
    assert r3["reconciliation"]["pending_skipped"] >= 1
    assert r3["reconciliation"]["new_conflicts"] == 0

    # Assert 0 duplicate conflict rows inserted
    assert con.execute("SELECT COUNT(*) FROM migration_conflicts;").fetchone()[0] == initial_conflict_count


# ==============================================================================
# Scenario 9: Pending Conflict Mutation Test
# ==============================================================================

def test_09_pending_conflict_mutation_test(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('mut_test', 'Initial Name', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
        VALUES ('mut_test', 'Divergent Name', ?, ?);
    """, (now, now))

    run_subpart_2b_migration(con)

    c_before = con.execute("SELECT id, conflict_fingerprint FROM migration_conflicts WHERE tenant_id = 'mut_test';").fetchone()
    old_id = c_before["id"]
    old_fp = c_before["conflict_fingerprint"]

    # Update tenant value while conflict is pending
    con.execute("UPDATE tenants SET business_name = 'Changed While Pending' WHERE id = 'mut_test';")

    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["pending_mutated"] == 1

    c_after = con.execute("SELECT id, tenants_value, conflict_fingerprint FROM migration_conflicts WHERE tenant_id = 'mut_test';").fetchone()
    assert c_after["id"] == old_id  # Mutated in-place, zero duplicate row
    assert c_after["tenants_value"] == "Changed While Pending"
    assert c_after["conflict_fingerprint"] != old_fp


# ==============================================================================
# Scenario 10: Database-Level Conflict Resolution Invariant Test
# ==============================================================================

def test_10_database_level_conflict_resolution_invariant(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('res_test', 'Name A', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
        VALUES ('res_test', 'Name B', ?, ?);
    """, (now, now))

    run_subpart_2b_migration(con)

    # Directly resolve the conflict in the database
    con.execute("""
        UPDATE migration_conflicts 
        SET status = 'RESOLVED',
            resolved_value = 'Resolved Canonical Name',
            resolved_by = 'owner@test.com',
            resolved_at = ?
        WHERE tenant_id = 'res_test';
    """, (time.time(),))

    # Synchronize both tables to the resolved value
    con.execute("UPDATE business_profiles SET display_name = 'Resolved Canonical Name' WHERE tenant_id = 'res_test';")
    con.execute("UPDATE tenants SET business_name = 'Resolved Canonical Name' WHERE id = 'res_test';")

    # Rerun migration
    r_after = run_subpart_2b_migration(con)
    assert r_after["reconciliation"]["new_conflicts"] == 0

    # Verify the resolved record is preserved
    resolved_rec = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'res_test';").fetchone()
    assert resolved_rec["status"] == "RESOLVED"
    assert resolved_rec["resolved_value"] == "Resolved Canonical Name"

    # Both tables retain the resolved canonical name
    assert con.execute("SELECT display_name FROM business_profiles WHERE tenant_id = 'res_test';").fetchone()["display_name"] == "Resolved Canonical Name"
    assert con.execute("SELECT business_name FROM tenants WHERE id = 'res_test';").fetchone()["business_name"] == "Resolved Canonical Name"


# ==============================================================================
# Scenario 11: Transaction Rollback & Failure-Injection Test (Revision 2.7)
# ==============================================================================

def test_11_transaction_rollback_and_failure_injection(fresh_synthetic_db, monkeypatch):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, branch, category, description, created_at, updated_at)
        VALUES ('fail_test', 'Pre-Migration Name', 'Main', 'Bakery', 'Fresh Bread', ?, ?);
    """, (now, now))

    # Record pre-migration schema and rows
    bp_cols_pre = [dict(r) for r in con.execute("PRAGMA table_info(business_profiles);").fetchall()]
    t_cols_pre = [dict(r) for r in con.execute("PRAGMA table_info(tenants);").fetchall()]
    bp_count_pre = con.execute("SELECT COUNT(*) FROM business_profiles;").fetchone()[0]

    # Inject failure during reconciliation (after alterations and provisioning)
    import backend.app.core.database.migration as mig_mod

    def failing_reconcile(db):
        raise RuntimeError("Synthetic failure injected to verify transaction rollback!")

    monkeypatch.setattr(mig_mod, "reconcile_and_audit_existing_records", failing_reconcile)

    with pytest.raises(MigrationError) as exc_info:
        run_subpart_2b_migration(con)
    assert "Synthetic failure injected" in str(exc_info.value)

    # Post-rollback structural and logical verification (Revision 2.7 criteria)
    bp_cols_post = [dict(r) for r in con.execute("PRAGMA table_info(business_profiles);").fetchall()]
    assert bp_cols_post == bp_cols_pre, "Columns on business_profiles must match pre-migration schema"

    t_cols_post = [dict(r) for r in con.execute("PRAGMA table_info(tenants);").fetchall()]
    assert t_cols_post == t_cols_pre, "Columns on tenants must match pre-migration schema"

    assert con.execute("SELECT COUNT(*) FROM business_profiles;").fetchone()[0] == bp_count_pre, "No new profile rows should remain"

    # Verify migration_conflicts was rolled back
    assert con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migration_conflicts';").fetchone() is None, "migration_conflicts table must be completely rolled back"

    # Integrity check
    assert con.execute("PRAGMA integrity_check;").fetchone()[0] == "ok"


# ==============================================================================
# Scenario 12: Foreign-Key Enforcement Verification Test
# ==============================================================================

def test_12_foreign_key_enforcement_verification(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    # Verify foreign_keys is active during migration run
    run_subpart_2b_migration(con)

    assert con.execute("PRAGMA foreign_keys;").fetchone()[0] == 1

    # Attempt to insert an orphan business_profile referencing non-existent tenant
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("""
            INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
            VALUES ('non_existent_tenant_xyz', 'Orphan Profile', ?, ?);
        """, (now, now))

    # Attempt to insert an orphan conflict record referencing non-existent tenant
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("""
            INSERT INTO migration_conflicts (tenant_id, field_name, proposed_canonical, conflict_fingerprint, detected_at)
            VALUES ('non_existent_tenant_xyz', 'display_name', 'Orphan', 'fp123', ?);
        """, (now,))


# ==============================================================================
# Scenario 13: Pre-Commit Journal Mode Verification on Success
# ==============================================================================

def test_13_pre_commit_journal_mode_verification_on_success(isolated_db_copy):
    con, _ = isolated_db_copy
    initial_mode = con.execute("PRAGMA journal_mode;").fetchone()[0]

    result = run_subpart_2b_migration(con)
    assert result["initial_journal_mode"].lower() == initial_mode.lower()

    # Verify journal mode after commit is completely unchanged
    current_mode = con.execute("PRAGMA journal_mode;").fetchone()[0]
    assert current_mode.lower() == initial_mode.lower()


# ==============================================================================
# Scenario 14: Journal Mode Preservation on Rollback Test
# ==============================================================================

def test_14_journal_mode_preservation_on_rollback(fresh_synthetic_db, monkeypatch):
    con, _ = fresh_synthetic_db
    initial_mode = con.execute("PRAGMA journal_mode;").fetchone()[0]

    import backend.app.core.database.migration as mig_mod
    def failing_reconcile(db):
        raise ValueError("Triggering rollback")

    monkeypatch.setattr(mig_mod, "reconcile_and_audit_existing_records", failing_reconcile)

    with pytest.raises(MigrationError):
        run_subpart_2b_migration(con)

    post_rollback_mode = con.execute("PRAGMA journal_mode;").fetchone()[0]
    assert post_rollback_mode.lower() == initial_mode.lower()


# ==============================================================================
# Scenario 15: Journal-Mode Transactional Rejection & Invariant Test (Revision 2.7)
# ==============================================================================

def test_15_journal_mode_transactional_rejection_and_invariant(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()
    initial_mode = con.execute("PRAGMA journal_mode;").fetchone()[0]

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('j_test', 'Journal Test', ?, ?);
    """, (now, now))

    # 1. Verify that attempting to change journal_mode during an active write transaction is rejected by SQLite
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("BEGIN IMMEDIATE TRANSACTION;")
    con.execute("UPDATE tenants SET business_name = 'Updated Name' WHERE id = 'j_test';")
    
    # In SQLite WAL mode with an active write, PRAGMA journal_mode returns the current mode (refuses change)
    res = con.execute("PRAGMA journal_mode = DELETE;").fetchone()[0]
    assert res.lower() == initial_mode.lower(), "SQLite must reject journal_mode changes inside an active write transaction"

    con.execute("ROLLBACK;")
    assert con.execute("PRAGMA journal_mode;").fetchone()[0].lower() == initial_mode.lower()

    # 2. Verify that if a journal-mode mismatch is detected pre-commit, InvariantViolationError is raised and rolls back
    class InvariantProxy:
        def __init__(self, target):
            self._target = target
            self.corrupt_pre_commit = False

        def __getattr__(self, name):
            return getattr(self._target, name)

        def cursor(self):
            return self._target.cursor()

        def execute(self, sql, *args, **kwargs):
            if self.corrupt_pre_commit and "PRAGMA journal_mode" in sql:
                class MockCursor:
                    def fetchone(inner_self):
                        return ("CORRUPTED_JOURNAL_MODE",)
                return MockCursor()
            return self._target.execute(sql, *args, **kwargs)

    proxy = InvariantProxy(con)

    # Monkeypatch apply_phase2_schema_alterations to trigger the proxy corruption right before pre-commit check
    import backend.app.core.database.migration as mig_mod
    orig_reconcile = mig_mod.reconcile_and_audit_existing_records

    def corrupt_before_precommit(db):
        res = orig_reconcile(db)
        proxy.corrupt_pre_commit = True
        return res

    import pytest
    from pytest import MonkeyPatch
    mp = MonkeyPatch()
    try:
        mp.setattr(mig_mod, "reconcile_and_audit_existing_records", corrupt_before_precommit)

        with pytest.raises(InvariantViolationError) as exc_info:
            run_subpart_2b_migration(proxy)
        assert "FATAL PRE-COMMIT VIOLATION" in str(exc_info.value) or "Database journal_mode changed" in str(exc_info.value)

        # Verify transaction was rolled back cleanly
        assert con.execute("SELECT COUNT(*) FROM business_profiles WHERE tenant_id = 'j_test';").fetchone()[0] == 0
        assert con.execute("PRAGMA integrity_check;").fetchone()[0] == "ok"
    finally:
        mp.undo()

    # 3. Verify that post-rollback journal mode violation is reported explicitly (never silently ignored)
    def test_post_rollback_violation_reporting():
        class PostRollbackProxy:
            def __init__(self, target):
                self._target = target
                self.rollback_called = False

            def __getattr__(self, name):
                return getattr(self._target, name)

            def cursor(self):
                return self._target.cursor()

            def execute(self, sql, *args, **kwargs):
                if "ROLLBACK" in sql:
                    self.rollback_called = True
                if self.rollback_called and "PRAGMA journal_mode" in sql:
                    class MockCursor:
                        def fetchone(inner_self):
                            return ("POST_ROLLBACK_CORRUPTED",)
                    return MockCursor()
                return self._target.execute(sql, *args, **kwargs)

        pr_proxy = PostRollbackProxy(con)
        
        def failing_step(db):
            raise RuntimeError("Trigger failure to test post-rollback invariant check")

        mp2 = MonkeyPatch()
        try:
            mp2.setattr(mig_mod, "reconcile_and_audit_existing_records", failing_step)
            with pytest.raises(InvariantViolationError) as exc_info2:
                run_subpart_2b_migration(pr_proxy)
            assert "CRITICAL INVARIANT VIOLATION" in str(exc_info2.value)
            assert exc_info2.value.__cause__ is not None  # Explicitly chained exception!
        finally:
            mp2.undo()

    test_post_rollback_violation_reporting()


# ==============================================================================
# Absolute Safety Assertion: Production Database Non-Modification Check
# ==============================================================================

def test_16_production_database_unmodified():
    """
    Asserts that the production database SHA-256 hash has not changed at all,
    confirming zero mutation to the live customer database during test suite execution.
    """
    if INITIAL_PROD_HASH is None:
        pytest.skip("Production database does not exist in this environment.")
    assert PROD_DB_PATH.exists()
    with open(PROD_DB_PATH, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    assert current_hash == INITIAL_PROD_HASH, (
        f"CRITICAL SAFETY VIOLATION: Production database was modified during test execution! "
        f"Initial: {INITIAL_PROD_HASH}, Current: {current_hash}"
    )


# ==============================================================================
# Scenario 17: Obsolete Pending Conflict Auto-Resolved When Identical
# ==============================================================================

def test_17_obsolete_pending_conflict_auto_resolved_when_identical(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('auto_res_test', 'Tenant Name', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
        VALUES ('auto_res_test', 'Profile Name', ?, ?);
    """, (now, now))

    # Run 1: Detects substantive conflict
    r1 = run_subpart_2b_migration(con)
    assert r1["reconciliation"]["new_conflicts"] == 1
    conf1 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'auto_res_test' AND field_name = 'display_name';").fetchone()
    assert conf1["status"] == "PENDING_REVIEW"
    assert conf1["resolved_at"] is None

    # Update both sides to become identical (discrepancy eliminated)
    con.execute("UPDATE tenants SET business_name = 'Profile Name' WHERE id = 'auto_res_test';")

    # Run 2: Reconciles and auto-resolves obsolete pending conflict
    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["auto_resolved"] == 1
    assert r2["reconciliation"]["new_conflicts"] == 0

    conf2 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'auto_res_test' AND field_name = 'display_name';").fetchone()
    assert conf2["status"] == "RESOLVED"
    assert conf2["resolved_by"] == "SYSTEM_RECONCILIATION"
    assert conf2["resolved_value"] == "Profile Name"
    assert conf2["resolution_notes"] == "Auto-resolved: underlying discrepancy eliminated."
    assert conf2["resolved_at"] is not None
    resolved_time = conf2["resolved_at"]

    # Run 3: Idempotency check - repeated run must not duplicate or alter resolved conflict
    r3 = run_subpart_2b_migration(con)
    assert r3["reconciliation"]["auto_resolved"] == 0
    assert r3["reconciliation"]["new_conflicts"] == 0
    all_confs = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'auto_res_test';").fetchall()
    assert len(all_confs) == 1
    assert all_confs[0]["status"] == "RESOLVED"
    assert all_confs[0]["resolved_at"] == resolved_time


# ==============================================================================
# Scenario 18: Obsolete Pending Conflict Auto-Resolved on Canonical Backfill
# ==============================================================================

def test_18_obsolete_pending_conflict_auto_resolved_on_canonical_backfill(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, category, created_at, updated_at)
        VALUES ('backfill_res_test', 'Backfill Tenant', 'Fast Food', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, category, created_at, updated_at)
        VALUES ('backfill_res_test', 'Backfill Tenant', 'Fine Dining', ?, ?);
    """, (now, now))

    # Run 1: Divergence detected in category
    run_subpart_2b_migration(con)
    conf1 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'backfill_res_test' AND field_name = 'category';").fetchone()
    assert conf1["status"] == "PENDING_REVIEW"

    # Profile category cleared to empty string
    con.execute("UPDATE business_profiles SET category = '' WHERE tenant_id = 'backfill_res_test';")

    # Run 2: Triggers canonical backfill and auto-resolves pending conflict
    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["backfilled_canonical"] >= 1
    assert r2["reconciliation"]["auto_resolved"] == 1

    # Verify canonical profile was backfilled from tenant
    p_cat = con.execute("SELECT category FROM business_profiles WHERE tenant_id = 'backfill_res_test';").fetchone()["category"]
    assert p_cat == "Fast Food"

    # Verify conflict auto-resolved with backfilled value
    conf2 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'backfill_res_test' AND field_name = 'category';").fetchone()
    assert conf2["status"] == "RESOLVED"
    assert conf2["resolved_by"] == "SYSTEM_RECONCILIATION"
    assert conf2["resolved_value"] == "Fast Food"
    assert conf2["resolution_notes"] == "Auto-resolved: underlying discrepancy eliminated."


# ==============================================================================
# Scenario 19: Obsolete Pending Conflict Auto-Resolved on Legacy Mirror
# ==============================================================================

def test_19_obsolete_pending_conflict_auto_resolved_on_legacy_mirror(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    # Apply schema additions first so branch_name column exists
    apply_phase2_schema_alterations(con)

    con.execute("""
        INSERT INTO tenants (id, business_name, branch, created_at, updated_at)
        VALUES ('mirror_res_test', 'Mirror Tenant', 'Branch T', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, branch_name, created_at, updated_at)
        VALUES ('mirror_res_test', 'Mirror Tenant', 'Branch P', ?, ?);
    """, (now, now))

    # Run 1: Divergence in branch
    run_subpart_2b_migration(con)
    conf1 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'mirror_res_test' AND field_name = 'branch_name';").fetchone()
    assert conf1["status"] == "PENDING_REVIEW"

    # Tenant branch cleared to empty string
    con.execute("UPDATE tenants SET branch = '' WHERE id = 'mirror_res_test';")

    # Run 2: Triggers legacy mirror and auto-resolves pending conflict
    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["mirrored_legacy"] >= 1
    assert r2["reconciliation"]["auto_resolved"] == 1

    # Verify legacy tenant branch mirrored canonical profile
    t_branch = con.execute("SELECT branch FROM tenants WHERE id = 'mirror_res_test';").fetchone()["branch"]
    assert t_branch == "Branch P"

    # Verify conflict auto-resolved
    conf2 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'mirror_res_test' AND field_name = 'branch_name';").fetchone()
    assert conf2["status"] == "RESOLVED"
    assert conf2["resolved_by"] == "SYSTEM_RECONCILIATION"
    assert conf2["resolved_value"] == "Branch P"
    assert conf2["resolution_notes"] == "Auto-resolved: underlying discrepancy eliminated."


# ==============================================================================
# Scenario 20: Resolved Historical Records Preserved and Never Overwritten
# ==============================================================================

def test_20_historical_resolved_conflicts_preserved_and_idempotent(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    # Apply schema additions first so description column exists in business_profiles
    apply_phase2_schema_alterations(con)

    con.execute("""
        INSERT INTO tenants (id, business_name, description, created_at, updated_at)
        VALUES ('hist_test', 'Hist Tenant', 'Desc Tenant', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, description, created_at, updated_at)
        VALUES ('hist_test', 'Hist Tenant', 'Desc Profile', ?, ?);
    """, (now, now))

    # Run 1: Divergence logged
    run_subpart_2b_migration(con)

    # Resolve conflict and synchronize tables to the chosen canonical value (Section 8.5 pattern)
    con.execute("""
        UPDATE migration_conflicts
        SET status = 'RESOLVED',
            resolved_value = 'Admin Chosen Canonical',
            resolved_by = 'owner@restaurant.com',
            resolution_notes = 'Manual admin decision after review',
            resolved_at = 1700000000.0
        WHERE tenant_id = 'hist_test' AND field_name = 'description';
    """)
    con.execute("UPDATE business_profiles SET description = 'Admin Chosen Canonical' WHERE tenant_id = 'hist_test';")
    con.execute("UPDATE tenants SET description = 'Admin Chosen Canonical' WHERE id = 'hist_test';")

    # Rerun migration while tables are aligned to the resolved value
    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["new_conflicts"] == 0
    assert r2["reconciliation"]["auto_resolved"] == 0  # Already resolved, not touched

    # Verify historical resolved row was NOT modified, overwritten, or duplicated
    h_recs = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'hist_test' AND field_name = 'description';").fetchall()
    assert len(h_recs) == 1
    h_rec = h_recs[0]
    assert h_rec["status"] == "RESOLVED"
    assert h_rec["resolved_value"] == "Admin Chosen Canonical"
    assert h_rec["resolved_by"] == "owner@restaurant.com"
    assert h_rec["resolution_notes"] == "Manual admin decision after review"
    assert h_rec["resolved_at"] == 1700000000.0

    # Introduce a new divergence on a different field: timezone
    con.execute("UPDATE tenants SET timezone = 'UTC' WHERE id = 'hist_test';")
    con.execute("UPDATE business_profiles SET timezone = 'Asia/Kolkata' WHERE tenant_id = 'hist_test';")

    run_subpart_2b_migration(con)

    # Verify both records exist: original resolved description AND new pending timezone
    all_recs = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'hist_test' ORDER BY id ASC;").fetchall()
    assert len(all_recs) == 2
    assert all_recs[0]["field_name"] == "description" and all_recs[0]["status"] == "RESOLVED"
    assert all_recs[1]["field_name"] == "timezone" and all_recs[1]["status"] == "PENDING_REVIEW"


# ==============================================================================
# Scenario 21: Genuine Pending Conflicts Remain Pending
# ==============================================================================

def test_21_genuine_pending_conflicts_remain_pending(fresh_synthetic_db):
    con, _ = fresh_synthetic_db
    now = time.time()

    con.execute("""
        INSERT INTO tenants (id, business_name, created_at, updated_at)
        VALUES ('genuine_test', 'Name Tenant', ?, ?);
    """, (now, now))
    con.execute("""
        INSERT INTO business_profiles (tenant_id, display_name, created_at, updated_at)
        VALUES ('genuine_test', 'Name Profile', ?, ?);
    """, (now, now))

    # Run 1
    r1 = run_subpart_2b_migration(con)
    assert r1["reconciliation"]["new_conflicts"] == 1

    conf1 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'genuine_test' AND field_name = 'display_name';").fetchone()
    assert conf1["status"] == "PENDING_REVIEW"
    initial_id = conf1["id"]
    initial_fp = conf1["conflict_fingerprint"]

    # Run 2: No data change -> remains pending, pending_skipped incremented
    r2 = run_subpart_2b_migration(con)
    assert r2["reconciliation"]["pending_skipped"] >= 1
    assert r2["reconciliation"]["auto_resolved"] == 0

    conf2 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'genuine_test' AND field_name = 'display_name';").fetchone()
    assert conf2["status"] == "PENDING_REVIEW"
    assert conf2["id"] == initial_id
    assert conf2["conflict_fingerprint"] == initial_fp

    # Mutate to a different divergence
    con.execute("UPDATE tenants SET business_name = 'Name Tenant Mutated' WHERE id = 'genuine_test';")

    # Run 3: Mutated in place, STILL PENDING_REVIEW
    r3 = run_subpart_2b_migration(con)
    assert r3["reconciliation"]["pending_mutated"] == 1
    assert r3["reconciliation"]["auto_resolved"] == 0

    conf3 = con.execute("SELECT * FROM migration_conflicts WHERE tenant_id = 'genuine_test' AND field_name = 'display_name';").fetchone()
    assert conf3["status"] == "PENDING_REVIEW"
    assert conf3["id"] == initial_id
    assert conf3["tenants_value"] == "Name Tenant Mutated"
    assert conf3["conflict_fingerprint"] != initial_fp

