"""
Automated Safety and Verification Suite for Vraja Phase 8.7.
Verifies clean database initialization, profile/document storage security,
backup/restore integrity with document checksums, accidental overwrite defenses,
and release package composition.
"""

import hashlib
import json
import os
import sqlite3
import tarfile
import pytest
from pathlib import Path

from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import DocumentStorageService
from Backend.app.core.entitlements.entitlements import check_tenant_entitlement
from scripts.backup_restore import create_backup, verify_backup, restore_backup, compute_sha256
from scripts.package_release import build_release_package, verify_release_package


def test_clean_database_initialization(tmp_path, monkeypatch):
    """Verifies that an empty database is safely initialized with all required schemas."""
    db_file = tmp_path / "staging_fresh.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    assert db_file.exists()

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "tenants", "users", "tenant_memberships", "sessions",
        "business_profiles", "tenant_documents", "analytics_events", "private_tickets"
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    # Verify default tenant seeding
    default_tenant = store.get_tenant("default_business")
    assert default_tenant is not None
    assert default_tenant["business_name"] == "Nasta Ghar"
    assert check_tenant_entitlement("default_business", "review_manager") is True


def test_profile_and_entitlement_schema(tmp_path, monkeypatch):
    """Verifies profile CRUD and entitlement check behavior on an isolated database."""
    db_file = tmp_path / "staging_profile.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    store.upsert_tenant({"id": "staging_inn", "business_name": "Staging Inn"})

    # Entitlement default is review_manager only
    assert check_tenant_entitlement("staging_inn", "review_manager") is True
    assert check_tenant_entitlement("staging_inn", "digital_card") is False

    # Upgrade to digital_card
    with store._connect() as db:
        db.execute("UPDATE tenants SET entitlements_json = ? WHERE id = ?", (json.dumps(["review_manager", "digital_card"]), "staging_inn"))

    assert check_tenant_entitlement("staging_inn", "digital_card") is True

    # Save business profile
    profile_data = {
        "tagline": "Staging Elegance",
        "phone_number": "+1 555-0100",
        "website_url": "staginginn.local",
        "address": "100 Staging Way",
        "custom_links": [{"title": "Specials", "url": "https://staginginn.local/specials"}],
        "is_published": 1
    }
    saved_profile = store.upsert_business_profile("staging_inn", profile_data)
    assert saved_profile["tagline"] == "Staging Elegance"
    assert saved_profile["is_published"] == 1

    fetched = store.get_business_profile("staging_inn")
    assert fetched["phone_number"] == "+1 555-0100"
    assert len(fetched["custom_links"]) == 1


def test_document_storage_directory_and_traversal_defense(tmp_path, monkeypatch):
    """Verifies document storage initialization, restricted permissions, and path traversal defense."""
    doc_root = tmp_path / "staging_documents"
    db_file = tmp_path / "doc_test.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("DOCUMENTS_PATH", str(doc_root))

    store = ReviewStore(database_path=str(db_file))
    store.upsert_tenant({"id": "staging_inn", "business_name": "Staging Inn"})
    doc_service = DocumentStorageService(storage_root=doc_root, store=store)

    assert doc_root.exists()
    assert doc_root.is_dir()

    # Save a valid PDF document
    pdf_bytes = b"%PDF-1.4 test document payload for safety verification"
    saved = doc_service.save_document(
        tenant_id="staging_inn",
        content=pdf_bytes,
        original_filename="StagingMenu.pdf",
        document_type="menu",
        display_name="StagingMenu.pdf",
        is_published=True
    )
    assert saved["id"] is not None
    assert saved["display_name"] == "StagingMenu.pdf"

    # Verify file stored on disk
    doc_file = doc_root / "staging_inn" / f"{saved['id']}.pdf"
    assert doc_file.exists()
    assert doc_file.read_bytes() == pdf_bytes

    # Verify path traversal defenses
    with pytest.raises((ValueError, PermissionError)):
        doc_service.save_document(
            tenant_id="../../etc",
            content=pdf_bytes,
            original_filename="malicious.pdf",
            document_type="menu"
        )

    with pytest.raises((ValueError, PermissionError)):
        doc_service._resolve_tenant_dir("../../etc")


def test_backup_restore_and_accidental_overwrite_protection(tmp_path, monkeypatch):
    """
    Verifies full backup creation, SHA-256 document checksum generation,
    protection against accidental database overwrite, and exact restoration.
    """
    db_file = tmp_path / "live_data" / "reviews.sqlite3"
    doc_dir = tmp_path / "live_docs"
    backup_target = tmp_path / "backups" / "snap_1"
    restore_target = tmp_path / "restore_test"

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))
    monkeypatch.setenv("DOCUMENTS_PATH", str(doc_dir))

    store = ReviewStore(database_path=str(db_file))
    store.upsert_tenant({"id": "backup_cafe", "business_name": "Backup Cafe"})
    doc_service = DocumentStorageService(storage_root=doc_dir, store=store)
    pdf_content = b"%PDF-1.4 backup sample document"
    saved_doc = doc_service.save_document(
        tenant_id="backup_cafe",
        content=pdf_content,
        original_filename="Menu.pdf",
        document_type="menu",
        display_name="Menu",
        is_published=True
    )

    # 1. Create backup
    created = create_backup(dest_dir=backup_target)
    assert created.exists()
    assert (created / "manifest.json").exists()

    # 2. Verify backup integrity
    assert verify_backup(backup_target) is True

    manifest_data = json.loads((created / "manifest.json").read_text())
    assert manifest_data["source_db_sha256"] == compute_sha256(created / "reviews.sqlite3")
    assert len(manifest_data["documents"]) == 1
    doc_entry = manifest_data["documents"][0]
    expected_doc_hash = hashlib.sha256(pdf_content).hexdigest()
    assert doc_entry["sha256"] == expected_doc_hash

    # 3. Accidental Overwrite Defense:
    # If the destination already contains reviews.sqlite3, restore_backup MUST refuse without allow_overwrite=True
    restore_target.mkdir(parents=True)
    existing_file = restore_target / "reviews.sqlite3"
    existing_file.write_text("pre-existing data")

    refused = restore_backup(backup_target, restore_target, allow_overwrite=False)
    assert refused is False, "restore_backup MUST fail when destination file exists and allow_overwrite is False"
    assert existing_file.read_text() == "pre-existing data", "Existing file must not be modified when refused"

    # 4. Intentional restore with allow_overwrite=True succeeds
    success = restore_backup(backup_target, restore_target, allow_overwrite=True)
    assert success is True
    assert (restore_target / "reviews.sqlite3").exists()
    restored_doc = restore_target / "documents" / "backup_cafe" / f"{saved_doc['id']}.pdf"
    assert restored_doc.exists()
    assert compute_sha256(restored_doc) == expected_doc_hash


def test_release_package_generation_and_purity(tmp_path):
    """
    Verifies that the release packaging utility generates a valid archive
    and strictly excludes sensitive files, databases, .env files, and caches.
    """
    tar_path = tmp_path / "test-release.tar.gz"
    build_release_package(output_tar=tar_path)
    assert tar_path.exists()

    # Verify package passes internal checksum & structure verification
    assert verify_release_package(tar_path) is True

    # Direct tar examination for forbidden file extensions
    with tarfile.open(tar_path, "r:gz") as tar:
        names = tar.getnames()

    for name in names:
        lower = name.lower()
        # Must not contain databases
        assert not lower.endswith((".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".db")), f"Database file leaked: {name}"
        # Must not contain bytecode
        assert not lower.endswith((".pyc", ".pyo")), f"Compiled Python bytecode leaked: {name}"
        # Must not contain real .env files
        if "/.env" in lower or lower.endswith("/.env"):
            assert lower.endswith(".example"), f"Environment file leaked: {name}"
        # Must not contain test mocks or user data
        assert "tests/" not in lower, f"Tests directory leaked: {name}"
        assert "data/nasta-ghar" not in lower, f"Local data directory leaked: {name}"

    # Verify essential artifacts exist in the tarball
    assert any(n.endswith("RELEASE_MANIFEST.json") for n in names)
    assert any(n.endswith("RELEASE_MANIFEST.md") for n in names)
    assert any(n.endswith("staging.env.example") for n in names)
    assert any(n.endswith("Backend/app/main.py") for n in names)
    assert any(n.lower().endswith("nastaghar/frontend/dist/index.html") for n in names)
    assert any(n.lower().endswith("digital_card/frontend/dist/index.html") or n.lower().endswith("product-b/frontend/dist/index.html") for n in names)
