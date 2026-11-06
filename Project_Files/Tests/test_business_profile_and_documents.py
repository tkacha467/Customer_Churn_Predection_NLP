"""
Automated unit & integration test suite for Vraja Phase 8.1:
- Shared business profile data layer
- Document storage service (PDF validation, path traversal prevention, atomic writes)
- Tenant isolation across profiles and documents
- Backup/restore compatibility with document assets
"""

import json
import os
import shutil
import sqlite3
import time
from pathlib import Path
import pytest
from pydantic import ValidationError

from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import (
    DocumentStorageService,
    compute_sha256_bytes,
    sanitize_filename,
    MAX_DOCUMENT_SIZE_BYTES,
)
from Backend.app.schemas import (
    BusinessProfileResponse,
    BusinessProfileUpdateRequest,
    CustomLinkItem,
    normalize_url,
)
from scripts.backup_restore import (
    create_backup,
    verify_backup,
    restore_backup,
    compute_sha256,
    get_table_counts,
)

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000102 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF"


@pytest.fixture
def isolated_env(tmp_path):
    """Sets up an isolated database and document storage environment."""
    db_path = tmp_path / "test_db.sqlite3"
    docs_path = tmp_path / "documents"
    docs_path.mkdir(parents=True, exist_ok=True)

    store = ReviewStore(database_path=str(db_path))
    # Seed two active test tenants
    store.upsert_tenant({
        "id": "tenant_card_a",
        "business_name": "Cafe Alpha",
        "category": "Artisanal Cafe",
        "primary_accent": "#0ea5e9"
    })
    store.upsert_tenant({
        "id": "tenant_card_b",
        "business_name": "Bistro Beta",
        "category": "Italian Bistro",
        "primary_accent": "#ef4444"
    })

    doc_service = DocumentStorageService(storage_root=docs_path, store=store)

    return {
        "db_path": db_path,
        "docs_path": docs_path,
        "store": store,
        "doc_service": doc_service,
        "tmp_path": tmp_path
    }


# ─── 1. Idempotent Schema Initialization & Tenant Compatibility ──────────────

def test_idempotent_schema_initialization(tmp_path):
    """Proves that initializing ReviewStore multiple times is safe and preserves data."""
    db_file = tmp_path / "idempotent.sqlite3"
    store1 = ReviewStore(database_path=str(db_file))
    store1.upsert_tenant({"id": "init_test", "business_name": "Init Test"})
    profile1 = store1.upsert_business_profile("init_test", {"tagline": "Initial Tagline"})
    assert profile1["tagline"] == "Initial Tagline"

    # Second initialization on same database file
    store2 = ReviewStore(database_path=str(db_file))
    profile2 = store2.get_business_profile("init_test")
    assert profile2 is not None
    assert profile2["tagline"] == "Initial Tagline"


def test_existing_tenant_compatibility(isolated_env):
    """Ensures existing tenants created without profiles continue to function smoothly."""
    store = isolated_env["store"]
    # Tenant Alpha has no profile initially
    assert store.get_business_profile("tenant_card_a") is None

    # Creating profile for non-existent tenant fails with KeyError
    with pytest.raises(KeyError):
        store.upsert_business_profile("non_existent_tenant", {"tagline": "Ghost"})


# ─── 2. Business Profile Creation & Partial Updates ───────────────────────────

def test_profile_creation_and_partial_updates(isolated_env):
    """Tests creating a full profile and partially updating fields while preserving omitted ones."""
    store = isolated_env["store"]

    # 1. Initial creation
    initial_data = {
        "tagline": "Artisan pour-overs and fresh bakes",
        "phone_number": "+91 98765 43210",
        "website_url": "https://alpha.example.com",
        "address": "123 High Street, Rajkot",
        "map_url": "https://maps.google.com/?q=22.3,70.8",
        "whatsapp_url": "https://wa.me/919876543210",
        "instagram_url": "https://instagram.com/cafealpha",
        "facebook_url": "https://facebook.com/cafealpha",
        "youtube_url": "https://youtube.com/@cafealpha",
        "logo_path": "logo_alpha.png",
        "cover_image_path": "cover_alpha.jpg",
        "custom_links": [{"title": "Zomato", "url": "https://zomato.com/alpha", "icon": "food"}],
        "is_published": False,
        "show_review_button": True
    }
    created = store.upsert_business_profile("tenant_card_a", initial_data)
    assert created["tenant_id"] == "tenant_card_a"
    assert created["tagline"] == "Artisan pour-overs and fresh bakes"
    assert created["phone_number"] == "+91 98765 43210"
    assert created["is_published"] is False
    assert len(created["custom_links"]) == 1

    # 2. Partial update: Only update tagline and publish status
    updated = store.upsert_business_profile("tenant_card_a", {
        "tagline": "Updated Signature Coffee",
        "is_published": True
    })

    assert updated["tagline"] == "Updated Signature Coffee"
    assert updated["is_published"] is True
    # Verify omitted fields were safely preserved
    assert updated["phone_number"] == "+91 98765 43210"
    assert updated["website_url"] == "https://alpha.example.com"
    assert updated["address"] == "123 High Street, Rajkot"
    assert updated["instagram_url"] == "https://instagram.com/cafealpha"
    assert len(updated["custom_links"]) == 1

    # 3. Test set_profile_published helper
    ok = store.set_profile_published("tenant_card_a", False)
    assert ok is True
    assert store.get_business_profile("tenant_card_a")["is_published"] is False


# ─── 3. URL Validation & Normalization ───────────────────────────────────────

def test_url_validation_and_normalization():
    """Tests URL normalization and schema validators for business profiles."""
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("  http://mycafe.com/menu  ") == "http://mycafe.com/menu"
    assert normalize_url("") == ""
    assert normalize_url(None) == ""

    # Test BusinessProfileUpdateRequest validators
    req = BusinessProfileUpdateRequest(
        website_url="cafe.local",
        map_url="goo.gl/maps/123",
        instagram_url="instagram.com/cafe",
        phone_number="+91 98765 43210"
    )
    assert req.website_url == "https://cafe.local"
    assert req.map_url == "https://goo.gl/maps/123"
    assert req.instagram_url == "https://instagram.com/cafe"
    assert req.phone_number == "+91 98765 43210"

    # Test invalid phone number
    with pytest.raises(ValidationError):
        BusinessProfileUpdateRequest(phone_number="not-a-phone-number-at-all-xyz")

    # Test CustomLinkItem
    link = CustomLinkItem(title="Order Online", url="order.cafe.com")
    assert link.url == "https://order.cafe.com"

    with pytest.raises(ValidationError):
        CustomLinkItem(title="", url="https://example.com")


# ─── 4. Document Storage & Multiple Categories ────────────────────────────────

def test_multiple_documents_per_tenant(isolated_env):
    """Proves that a tenant can store multiple categorized documents."""
    doc_service = isolated_env["doc_service"]

    doc1 = doc_service.save_document(
        tenant_id="tenant_card_a",
        content=SAMPLE_PDF_BYTES,
        original_filename="Main Menu 2026.pdf",
        document_type="food_menu",
        display_name="Dinner Menu"
    )
    doc2 = doc_service.save_document(
        tenant_id="tenant_card_a",
        content=SAMPLE_PDF_BYTES,
        original_filename="Drinks & Cocktails.pdf",
        document_type="drinks_menu",
        display_name="Bar Menu"
    )
    doc3 = doc_service.save_document(
        tenant_id="tenant_card_a",
        content=SAMPLE_PDF_BYTES,
        original_filename="Desserts.pdf",
        document_type="dessert_menu",
        display_name="Dessert Menu"
    )

    docs = doc_service.list_documents("tenant_card_a")
    assert len(docs) == 3
    types = {d["document_type"] for d in docs}
    assert types == {"food_menu", "drinks_menu", "dessert_menu"}


def test_valid_pdf_storage_and_integrity_hashes(isolated_env):
    """Verifies atomic write, SHA-256 calculation, and server-generated filename."""
    doc_service = isolated_env["doc_service"]
    record = doc_service.save_document(
        tenant_id="tenant_card_a",
        content=SAMPLE_PDF_BYTES,
        original_filename="Chef's Special!.pdf",
        document_type="food_menu"
    )

    expected_hash = compute_sha256_bytes(SAMPLE_PDF_BYTES)
    assert record["sha256_hash"] == expected_hash
    assert record["file_size_bytes"] == len(SAMPLE_PDF_BYTES)
    assert record["stored_filename"].endswith(".pdf")
    # Verify original filename never used as disk filename
    assert "Chef's Special" not in record["stored_filename"]

    # Verify physical file on disk
    file_path = doc_service.get_document_path("tenant_card_a", record["id"])
    assert file_path is not None
    assert file_path.is_file()
    assert file_path.read_bytes() == SAMPLE_PDF_BYTES


# ─── 5. Document Validation & Attack Prevention ──────────────────────────────

def test_invalid_empty_and_oversized_pdfs(isolated_env):
    """Ensures empty, non-PDF, and oversized files are strictly rejected."""
    doc_service = isolated_env["doc_service"]

    # 1. Empty file
    with pytest.raises(ValueError, match="empty or corrupted"):
        doc_service.save_document("tenant_card_a", b"", "empty.pdf")

    # 2. Corrupt / Non-PDF file
    with pytest.raises(ValueError, match="Invalid document signature"):
        doc_service.save_document("tenant_card_a", b"<html><body>Not a PDF</body></html>", "fake.pdf")

    # 3. Oversized file (>10 MiB)
    oversized = b"%PDF-1.4 " + (b"0" * (MAX_DOCUMENT_SIZE_BYTES + 100))
    with pytest.raises(ValueError, match="exceeds the maximum allowed limit"):
        doc_service.save_document("tenant_card_a", oversized, "large.pdf")


def test_filename_and_path_traversal_attempts(isolated_env):
    """Ensures malicious filenames or tenant identifiers cannot escape the storage root."""
    doc_service = isolated_env["doc_service"]
    storage_root = isolated_env["docs_path"]

    # 1. Path traversal in original filename
    record = doc_service.save_document(
        tenant_id="tenant_card_a",
        content=SAMPLE_PDF_BYTES,
        original_filename="../../etc/passwd.pdf"
    )
    # Stored safely inside tenant directory
    file_path = doc_service.get_document_path("tenant_card_a", record["id"])
    assert file_path.is_relative_to(storage_root)
    assert ".." not in str(file_path)

    # 2. Path traversal in tenant_id
    with pytest.raises(ValueError, match="Invalid tenant identifier"):
        doc_service.save_document(
            tenant_id="../../escaped_tenant",
            content=SAMPLE_PDF_BYTES,
            original_filename="menu.pdf"
        )


# ─── 6. Tenant Isolation & Access Scoping ────────────────────────────────────

def test_cross_tenant_document_access_prevention(isolated_env):
    """Proves Tenant A cannot view, retrieve, or delete Tenant B's documents."""
    doc_service = isolated_env["doc_service"]

    # Tenant A uploads document
    doc_a = doc_service.save_document("tenant_card_a", SAMPLE_PDF_BYTES, "AlphaMenu.pdf")

    # Tenant B tries to get file path of Tenant A's document
    assert doc_service.get_document_path("tenant_card_b", doc_a["id"]) is None

    # Tenant B tries to delete Tenant A's document
    delete_result = doc_service.delete_document("tenant_card_b", doc_a["id"])
    assert delete_result is False

    # Confirm Tenant A's document is still intact
    assert doc_service.get_document_path("tenant_card_a", doc_a["id"]) is not None


def test_unpublished_document_protection(isolated_env):
    """Ensures unpublished documents cannot be resolved via public access."""
    doc_service = isolated_env["doc_service"]
    store = isolated_env["store"]

    doc = doc_service.save_document(
        "tenant_card_a",
        SAMPLE_PDF_BYTES,
        "SecretDraftMenu.pdf",
        is_published=False
    )

    # Public access check must return None
    assert doc_service.get_public_document_path(doc["id"]) is None

    # Owner can still access it via tenant-scoped path
    assert doc_service.get_document_path("tenant_card_a", doc["id"]) is not None

    # Publish it and verify public access is now granted
    store.set_document_published("tenant_card_a", doc["id"], True)
    assert doc_service.get_public_document_path(doc["id"]) is not None


def test_interrupted_write_cleanup(isolated_env, monkeypatch):
    """Ensures failed writes clean up temporary files and do not leave orphaned records."""
    doc_service = isolated_env["doc_service"]
    store = isolated_env["store"]

    def faulty_add_tenant_document(doc_data):
        raise RuntimeError("Simulated database failure during insert")

    monkeypatch.setattr(store, "add_tenant_document", faulty_add_tenant_document)

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        doc_service.save_document("tenant_card_a", SAMPLE_PDF_BYTES, "test_abort.pdf")

    # Verify no .pdf or .tmp files remain in tenant directory
    tenant_dir = doc_service._resolve_tenant_dir("tenant_card_a")
    files = list(tenant_dir.glob("*")) if tenant_dir.exists() else []
    assert len(files) == 0


# ─── 7. Backup & Restore Compatibility with Document Assets ──────────────────

def test_backup_manifest_integrity_for_document_assets(monkeypatch, isolated_env):
    """Verifies hot backup captures documents, validates manifest hashes, and restores cleanly."""
    db_path = isolated_env["db_path"]
    docs_path = isolated_env["docs_path"]
    tmp_path = isolated_env["tmp_path"]
    doc_service = isolated_env["doc_service"]
    store = isolated_env["store"]

    # Save documents for both tenants
    doc_service.save_document("tenant_card_a", SAMPLE_PDF_BYTES, "AlphaDoc.pdf")
    doc_service.save_document("tenant_card_b", SAMPLE_PDF_BYTES, "BetaDoc.pdf")

    # Save business profile
    store.upsert_business_profile("tenant_card_a", {"tagline": "Alpha Cafe Tagline"})

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))

    # 1. Create backup
    backup_dest = tmp_path / "snapshot_with_docs"
    created_dir = create_backup(dest_dir=backup_dest)
    assert created_dir.exists()

    manifest_path = created_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Database contains 1 default seeded business profile ('default_business') + 1 for 'tenant_card_a'
    assert manifest["table_counts"]["business_profiles"] == 2
    assert manifest["table_counts"]["tenant_documents"] == 2
    assert manifest["documents"] is not None
    assert len(manifest["documents"]) == 2

    # 2. Verify backup
    assert verify_backup(created_dir) is True

    # 3. Restore to isolated location
    restore_target = tmp_path / "restored_instance"
    assert restore_backup(created_dir, restore_target) is True

    # Check restored documents
    restored_docs = restore_target / "documents"
    assert restored_docs.exists()
    restored_files = list(restored_docs.rglob("*.pdf"))
    assert len(restored_files) == 2

    # Check restored table counts
    restored_counts = get_table_counts(restore_target / "reviews.sqlite3")
    assert restored_counts["business_profiles"] == 2
    assert restored_counts["tenant_documents"] == 2


def test_legacy_database_only_backup_compatibility(monkeypatch, tmp_path):
    """Verifies that backups without a documents folder continue to restore seamlessly."""
    legacy_db = tmp_path / "legacy_source" / "reviews.sqlite3"
    legacy_db.parent.mkdir(parents=True, exist_ok=True)
    store = ReviewStore(database_path=str(legacy_db))
    store.upsert_tenant({"id": "legacy_tenant", "business_name": "Legacy Cafe"})

    monkeypatch.setenv("REVIEW_DB_PATH", str(legacy_db))
    # Unset DOCUMENTS_PATH or set to non-existent folder
    monkeypatch.setenv("DOCUMENTS_PATH", str(tmp_path / "non_existent_docs"))

    backup_dest = tmp_path / "legacy_snapshot"
    create_backup(dest_dir=backup_dest)

    # Verify backup manifest has documents: None
    with open(backup_dest / "manifest.json", "r") as f:
        manifest = json.load(f)
    assert manifest.get("documents") is None

    # Verify archive passes
    assert verify_backup(backup_dest) is True

    # Restore to isolated location
    legacy_restore = tmp_path / "legacy_restored"
    assert restore_backup(backup_dest, legacy_restore) is True
    assert (legacy_restore / "reviews.sqlite3").exists()
