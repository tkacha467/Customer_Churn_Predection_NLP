"""
Automated unit and integration tests for SQLite hot backup, manifest verification,
and isolated restore recovery.
"""

import json
import os
import sqlite3
import time
from pathlib import Path
import pytest

from api.review_assistant.storage import ReviewStore
from scripts.backup_restore import (
    compute_sha256,
    get_table_counts,
    create_backup,
    verify_backup,
    restore_backup,
)


@pytest.fixture
def multi_tenant_db(tmp_path):
    """Creates an isolated test database with rich multi-tenant state."""
    db_file = tmp_path / "source" / "reviews.sqlite3"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file = tmp_path / "source" / "business_links.json"

    with open(cfg_file, "w") as f:
        json.dump({"test": "config"}, f)

    store = ReviewStore(database_path=str(db_file))

    # 1. Tenants (in addition to seeded default_business)
    t1 = store.upsert_tenant({
        "id": "tenant_alpha",
        "business_name": "Tenant Alpha Bistro",
        "platform": "google",
        "review_url": "https://g.page/r/alpha/review",
        "branch": "Downtown",
        "category": "Cafe",
        "description": "Artisan espresso and pastries",
        "topics": ["coffee", "bakery"],
        "primary_accent": "#10b981",
        "domain": "alpha.example.com",
        "entitlements": ["review_manager", "digital_card"]
    })
    t2 = store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Tenant Beta Grill",
        "platform": "google",
        "review_url": "https://g.page/r/beta/review",
        "branch": "Uptown",
        "category": "Steakhouse",
        "description": "Wood-fired dining",
        "topics": ["steaks", "wine"],
        "primary_accent": "#ef4444",
        "domain": "beta.example.com",
        "entitlements": ["review_manager"]
    })

    # 2. Users
    u1 = store.create_user("owner_alpha@example.com", "argon2_dummy_hash_1", "Owner Alpha", is_platform_admin=False)
    u2 = store.create_user("owner_beta@example.com", "argon2_dummy_hash_2", "Owner Beta", is_platform_admin=False)
    u_admin = store.create_user("super@platform.example.com", "argon2_dummy_hash_3", "Super Admin", is_platform_admin=True)

    # 3. Memberships
    store.add_membership(u1["id"], "tenant_alpha", role="owner")
    store.add_membership(u2["id"], "tenant_beta", role="owner")
    store.add_membership(u_admin["id"], "tenant_alpha", role="admin")

    # 4. Sessions
    store.create_session("token_hash_alpha", u1["id"], "tenant_alpha", time.time() + 86400, "127.0.0.1", "Chrome")
    store.create_session("token_hash_beta", u2["id"], "tenant_beta", time.time() + 86400, "127.0.0.1", "Firefox")

    # 5. Analytics events
    store.add_event({
        "event_id": "evt_1",
        "timestamp": time.time(),
        "event_name": "review_started",
        "metadata": {"business_id": "tenant_alpha"},
    })
    store.add_event({
        "event_id": "evt_2",
        "timestamp": time.time(),
        "event_name": "review_submitted",
        "metadata": {"business_id": "tenant_beta"},
    })

    # 6. Private tickets
    store.add_ticket({
        "ticket_id": "tkt_1",
        "timestamp": time.time(),
        "business_id": "tenant_alpha",
        "customer_name": "Charlie",
        "customer_phone": "+1234567890",
        "feedback_text": "Espresso was lukewarm",
        "status": "new",
    })
    store.add_ticket({
        "ticket_id": "tkt_2",
        "timestamp": time.time(),
        "business_id": "tenant_beta",
        "customer_name": "Dana",
        "customer_phone": "+1987654321",
        "feedback_text": "Steak was slightly overcooked",
        "status": "in_progress",
    })

    return {
        "db_file": db_file,
        "cfg_file": cfg_file,
        "store": store,
        "tmp_path": tmp_path
    }


def test_hot_backup_and_restore_fidelity(monkeypatch, multi_tenant_db):
    """Tests creating a hot backup, verifying manifest, and restoring to an isolated directory."""
    db_file = multi_tenant_db["db_file"]
    cfg_file = multi_tenant_db["cfg_file"]
    tmp_path = multi_tenant_db["tmp_path"]

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(cfg_file))

    # Initial table counts
    source_counts = get_table_counts(db_file)
    assert source_counts["tenants"] >= 3  # default + alpha + beta
    assert source_counts["users"] >= 3
    assert source_counts["tenant_memberships"] >= 3
    assert source_counts["sessions"] >= 2
    assert source_counts["analytics_events"] >= 2
    assert source_counts["private_tickets"] >= 2

    # 1. Create backup
    backup_dest = tmp_path / "backup_archive"
    backup_result_dir = create_backup(dest_dir=backup_dest)
    assert backup_result_dir.exists()

    manifest_path = backup_result_dir / "manifest.json"
    backup_db_path = backup_result_dir / "reviews.sqlite3"
    assert manifest_path.exists()
    assert backup_db_path.exists()

    # 2. Verify backup
    is_valid = verify_backup(backup_result_dir)
    assert is_valid is True

    # 3. Verify manifest contents
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["sqlite_integrity"] == "ok"
    assert manifest["table_counts"] == source_counts
    assert manifest["source_db_sha256"] == compute_sha256(backup_db_path)

    # 4. Restore to an isolated directory
    restore_dir = tmp_path / "restored_isolated"
    restore_ok = restore_backup(backup_result_dir, restore_dir)
    assert restore_ok is True

    restored_db_path = restore_dir / "reviews.sqlite3"
    assert restored_db_path.exists()

    # 5. Verify restored database fidelity
    restored_counts = get_table_counts(restored_db_path)
    assert restored_counts == source_counts

    restored_store = ReviewStore(database_path=str(restored_db_path))
    alpha_tenant = restored_store.get_tenant("tenant_alpha")
    assert alpha_tenant is not None
    assert alpha_tenant["business_name"] == "Tenant Alpha Bistro"
    assert alpha_tenant["domain"] == "alpha.example.com"

    beta_tenant = restored_store.get_tenant("tenant_beta")
    assert beta_tenant is not None
    assert beta_tenant["business_name"] == "Tenant Beta Grill"

    # Verify tickets in restored DB
    alpha_tickets = restored_store.list_tickets("tenant_alpha")
    assert len(alpha_tickets) == 1
    assert alpha_tickets[0]["customer_name"] == "Charlie"
    assert alpha_tickets[0]["feedback_text"] == "Espresso was lukewarm"

    beta_tickets = restored_store.list_tickets("tenant_beta")
    assert len(beta_tickets) == 1
    assert beta_tickets[0]["customer_name"] == "Dana"


def test_backup_tamper_detection(monkeypatch, multi_tenant_db):
    """Ensures tampering with backup SQLite file causes verification failure."""
    db_file = multi_tenant_db["db_file"]
    cfg_file = multi_tenant_db["cfg_file"]
    tmp_path = multi_tenant_db["tmp_path"]

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(cfg_file))

    backup_dest = tmp_path / "tamper_backup"
    create_backup(dest_dir=backup_dest)

    backup_db = backup_dest / "reviews.sqlite3"
    # Tamper with one byte near the end
    with open(backup_db, "r+b") as f:
        f.seek(100)
        f.write(b"\xff")

    # Verification must fail due to checksum mismatch
    assert verify_backup(backup_dest) is False


def test_restore_protection_against_overwriting_active_db(monkeypatch, tmp_path):
    """Ensures restore refuses to overwrite default active db unless allow_overwrite is True."""
    dummy_backup = tmp_path / "dummy_backup"
    dummy_backup.mkdir()
    (dummy_backup / "reviews.sqlite3").write_text("dummy")

    from scripts.backup_restore import DEFAULT_DB_PATH
    active_parent = DEFAULT_DB_PATH.parent

    # Attempt to restore directly to DEFAULT_DB_PATH without allow_overwrite
    success = restore_backup(dummy_backup, active_parent, allow_overwrite=False)
    assert success is False


def test_wal_transactions_hot_backup(monkeypatch, multi_tenant_db):
    """Verifies that hot SQLite backup captures uncheckpointed WAL transactions safely."""
    db_file = multi_tenant_db["db_file"]
    cfg_file = multi_tenant_db["cfg_file"]
    tmp_path = multi_tenant_db["tmp_path"]
    store = multi_tenant_db["store"]

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("BUSINESS_LINKS_PATH", str(cfg_file))

    # Add new tenant while DB is active in WAL mode
    store.upsert_tenant({
        "id": "tenant_gamma",
        "business_name": "Tenant Gamma Lounge",
        "platform": "google",
        "review_url": "https://g.page/r/gamma/review",
    })

    # Backup without manual checkpointing
    backup_dest = tmp_path / "wal_backup"
    create_backup(dest_dir=backup_dest)

    # Verify backup archive
    assert verify_backup(backup_dest) is True

    # Restore to isolated location
    restored_dir = tmp_path / "wal_restored"
    assert restore_backup(backup_dest, restored_dir) is True

    # Check that tenant_gamma is fully intact in the restored standalone DB
    restored_store = ReviewStore(database_path=str(restored_dir / "reviews.sqlite3"))
    gamma = restored_store.get_tenant("tenant_gamma")
    assert gamma is not None
    assert gamma["business_name"] == "Tenant Gamma Lounge"

