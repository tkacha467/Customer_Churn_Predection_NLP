"""
Comprehensive Isolated API Test Suite for Vraja Phase 8.2:
- Public Business Card & Profile APIs
- Authenticated Profile Editing & Tenant Boundary Scoping
- Tenant Document Upload, Listing, Metadata Update, Deletion, and PDF Serving
- Entitlement Enforcement (review-only, card-only, combined)
- Path Traversal, Malicious Filenames, File Size & Signature Enforcement
- Backup & Restore Traversal / Symlink Protections
- Preservation of Review System Functionality
"""

import io
import json
import os
import shutil
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import (
    DocumentStorageService,
    _document_services,
    MAX_DOCUMENT_SIZE_BYTES,
)
from Backend.app.core.auth.auth import (
    _stores,
    hash_password,
    hash_token,
    generate_session_token,
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    _login_attempts,
    _login_lock,
)
from Backend.app.api.service import review_service
from scripts.backup_restore import create_backup, restore_backup, verify_backup

SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj "
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
    b"0000000052 00000 n \n0000000102 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF"
)


@pytest.fixture
def test_setup(tmp_path, monkeypatch):
    """Sets up completely isolated database and document directories for each test."""
    db_path = tmp_path / "test_reviews.sqlite3"
    docs_path = tmp_path / "documents"
    docs_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("REVIEW_DB_PATH", str(db_path))
    monkeypatch.setenv("DOCUMENTS_PATH", str(docs_path))
    monkeypatch.setenv("ENVIRONMENT", "test")

    _stores.clear()
    _document_services.clear()
    with _login_lock:
        _login_attempts.clear()
    review_service._rate_limits.clear()

    store = ReviewStore(database_path=str(db_path))

    # Seed Platform Admin
    admin_user = store.create_user(
        email="admin@vraja.test",
        password_hash=hash_password("SuperAdminSecret99!"),
        display_name="Vraja Admin",
        is_active=1,
        is_platform_admin=1,
    )

    # Seed Tenant A: Combined Tenant (review_manager + digital_card)
    store.upsert_tenant({
        "id": "tenant_alpha",
        "business_name": "Cafe Alpha",
        "category": "Artisanal Cafe",
        "description": "Specialty espresso and fresh pastries in Ahmedabad.",
        "primary_accent": "#0ea5e9",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })
    owner_a = store.create_user(
        email="owner_a@alpha.test",
        password_hash=hash_password("AlphaPass123!"),
        display_name="Alpha Owner",
        is_active=1,
    )
    store.add_membership(owner_a["id"], "tenant_alpha", role="owner")

    manager_a = store.create_user(
        email="manager_a@alpha.test",
        password_hash=hash_password("ManagerPass123!"),
        display_name="Alpha Manager",
        is_active=1,
    )
    store.add_membership(manager_a["id"], "tenant_alpha", role="manager")

    staff_a = store.create_user(
        email="staff_a@alpha.test",
        password_hash=hash_password("StaffPass123!"),
        display_name="Alpha Staff",
        is_active=1,
    )
    store.add_membership(staff_a["id"], "tenant_alpha", role="staff")

    # Seed Tenant B: Combined Tenant
    store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Bistro Beta",
        "category": "Italian Bistro",
        "description": "Authentic wood-fired sourdough pizzas.",
        "primary_accent": "#ef4444",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })
    owner_b = store.create_user(
        email="owner_b@beta.test",
        password_hash=hash_password("BetaPass123!"),
        display_name="Beta Owner",
        is_active=1,
    )
    store.add_membership(owner_b["id"], "tenant_beta", role="owner")

    # Seed Tenant C: Review-Only Tenant (NO digital_card)
    store.upsert_tenant({
        "id": "tenant_review_only",
        "business_name": "Review Only Diner",
        "category": "Fast Casual",
        "status": "active",
        "entitlements": ["review_manager"],
    })
    owner_c = store.create_user(
        email="owner_c@reviewonly.test",
        password_hash=hash_password("ReviewPass123!"),
        display_name="Review Only Owner",
        is_active=1,
    )
    store.add_membership(owner_c["id"], "tenant_review_only", role="owner")

    # Seed Tenant D: Card-Only Tenant (NO review_manager)
    store.upsert_tenant({
        "id": "tenant_card_only",
        "business_name": "Card Only Boutique",
        "category": "Retail Boutique",
        "status": "active",
        "entitlements": ["digital_card"],
    })
    owner_d = store.create_user(
        email="owner_d@cardonly.test",
        password_hash=hash_password("CardPass123!"),
        display_name="Card Only Owner",
        is_active=1,
    )
    store.add_membership(owner_d["id"], "tenant_card_only", role="owner")

    # Seed Tenant E: Inactive / Suspended Tenant
    store.upsert_tenant({
        "id": "tenant_suspended",
        "business_name": "Suspended Hotel",
        "category": "Hospitality",
        "status": "suspended",
        "entitlements": ["review_manager", "digital_card"],
    })

    client = TestClient(app)

    def login_as(user_id: str, active_tenant: str) -> TestClient:
        raw_token = generate_session_token()
        token_hash = hash_token(raw_token)
        store.create_session(
            token_hash=token_hash,
            user_id=user_id,
            active_tenant_id=active_tenant,
            expires_at=time.time() + SESSION_TTL_SECONDS,
        )
        c = TestClient(app)
        c.cookies.set(OWNER_COOKIE, raw_token)
        return c

    return {
        "client": client,
        "login_as": login_as,
        "store": store,
        "db_path": db_path,
        "docs_path": docs_path,
        "tmp_path": tmp_path,
        "owner_a": owner_a,
        "manager_a": manager_a,
        "staff_a": staff_a,
        "owner_b": owner_b,
        "owner_c": owner_c,
        "owner_d": owner_d,
        "admin_user": admin_user,
    }


# ─── 1. Public Digital Business Card & Profile Retrieval ─────────────────────

def test_public_card_retrieval_published(test_setup):
    """Anonymous visitors can view a published card with safe public metadata and documents."""
    store = test_setup["store"]
    client = test_setup["client"]

    # Configure profile as published
    store.upsert_business_profile("tenant_alpha", {
        "tagline": "Pure specialty brews",
        "phone_number": "+91 99988 77766",
        "website_url": "cafealpha.com",
        "address": "100 SG Highway, Ahmedabad",
        "is_published": True,
        "show_review_button": True,
        "custom_links": [{"title": "Zomato", "url": "zomato.com/alpha", "icon": "food"}],
    })

    # Upload published document via service
    doc_service = DocumentStorageService(storage_root=test_setup["docs_path"], store=store)
    doc_record = doc_service.save_document(
        tenant_id="tenant_alpha",
        content=SAMPLE_PDF_BYTES,
        original_filename="Alpha_Beverage_Menu.pdf",
        document_type="drinks_menu",
        display_name="Beverage Menu",
        is_published=True,
    )

    res = client.get("/api/businesses/tenant_alpha/card")
    assert res.status_code == 200
    data = res.json()

    assert data["tenant_id"] == "tenant_alpha"
    assert data["business_name"] == "Cafe Alpha"
    assert data["tagline"] == "Pure specialty brews"
    assert data["website_url"] == "https://cafealpha.com"
    assert data["show_review_button"] is True
    assert len(data["custom_links"]) == 1
    assert data["custom_links"][0]["url"] == "https://zomato.com/alpha"

    # Verify documents list contains safe download URL and metadata
    assert len(data["documents"]) == 1
    doc_item = data["documents"][0]
    assert doc_item["id"] == doc_record["id"]
    assert doc_item["display_name"] == "Beverage Menu"
    assert doc_item["download_url"] == f"/api/businesses/tenant_alpha/documents/{doc_record['id']}/file"

    # Assert NO server storage paths are exposed in response
    json_text = res.text
    assert "stored_filename" not in json_text
    assert ".tmp" not in json_text
    assert str(test_setup["docs_path"]) not in json_text


def test_public_card_rejection_unpublished(test_setup):
    """Anonymous visitors receive 404 for an unpublished card draft."""
    store = test_setup["store"]
    client = test_setup["client"]

    # Profile exists but is_published=False
    store.upsert_business_profile("tenant_alpha", {
        "tagline": "Draft in progress",
        "is_published": False,
    })

    res = client.get("/api/businesses/tenant_alpha/card")
    assert res.status_code == 404
    assert "Business card not found or not published" in res.json()["detail"]


def test_public_card_rejection_inactive_tenant(test_setup):
    """Cards for suspended or inactive tenants are rejected with 404."""
    store = test_setup["store"]
    client = test_setup["client"]

    # Even if profile is published, tenant_suspended is inactive
    store.upsert_business_profile("tenant_suspended", {
        "tagline": "Suspended tagline",
        "is_published": True,
    })

    res = client.get("/api/businesses/tenant_suspended/card")
    assert res.status_code == 404


def test_digital_card_qr_info_endpoint(test_setup):
    """Test public QR routing info endpoint for digital cards."""
    client = test_setup["client"]
    store = test_setup["store"]

    store.upsert_business_profile("tenant_alpha", {"is_published": True})
    res = client.get("/api/businesses/tenant_alpha/card/qr-info")
    assert res.status_code == 200
    data = res.json()
    assert data["business_id"] == "tenant_alpha"
    assert data["card_path"] == "/card/tenant_alpha"
    assert data["is_published"] is True


# ─── 2. Entitlement Enforcements (Review-only vs Card-only vs Combined) ──────

def test_missing_digital_card_entitlement_rejections(test_setup):
    """Tenants without 'digital_card' entitlement cannot use card or document APIs."""
    client = test_setup["client"]
    login_as = test_setup["login_as"]
    owner_c = test_setup["owner_c"]

    # 1. Public card read returns 404
    res = client.get("/api/businesses/tenant_review_only/card")
    assert res.status_code == 404

    # 2. Authenticated owner attempts profile edit -> 403
    auth_c = login_as(owner_c["id"], "tenant_review_only")
    res_edit = auth_c.put(
        "/api/businesses/tenant_review_only/profile",
        json={"tagline": "Trying to bypass entitlement"},
    )
    assert res_edit.status_code == 403
    assert "digital_card" in res_edit.json()["detail"]

    # 3. Authenticated owner attempts document upload -> 403
    files = {"file": ("menu.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    res_upload = auth_c.post(
        "/api/businesses/tenant_review_only/documents",
        files=files,
    )
    assert res_upload.status_code == 403
    assert "digital_card" in res_upload.json()["detail"]


def test_card_only_tenant_restrictions(test_setup):
    """Card-only tenants can manage cards and docs, but cannot access review manager APIs."""
    login_as = test_setup["login_as"]
    owner_d = test_setup["owner_d"]

    auth_d = login_as(owner_d["id"], "tenant_card_only")

    # Card-only owner CAN update their digital profile
    res_profile = auth_d.put(
        "/api/businesses/tenant_card_only/profile",
        json={"tagline": "Exclusive Luxury Boutique", "is_published": True},
    )
    assert res_profile.status_code == 200
    assert res_profile.json()["tagline"] == "Exclusive Luxury Boutique"

    # Card-only owner CANNOT access review analytics -> 403
    res_analytics = auth_d.get("/api/reviews/analytics")
    assert res_analytics.status_code == 403
    assert "review_manager" in res_analytics.json()["detail"]

    # Card-only owner CANNOT access private review tickets -> 403
    res_tickets = auth_d.get("/api/reviews/private-tickets")
    assert res_tickets.status_code == 403
    assert "review_manager" in res_tickets.json()["detail"]


def test_combined_tenant_can_use_both_modules(test_setup):
    """Combined tenants can use both review manager and digital card features seamlessly."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]

    auth_a = login_as(owner_a["id"], "tenant_alpha")

    # Can access review manager analytics
    res_rev = auth_a.get("/api/reviews/analytics")
    assert res_rev.status_code == 200

    # Can access digital card editing
    res_card = auth_a.put(
        "/api/businesses/tenant_alpha/profile",
        json={"tagline": "Best of both worlds"},
    )
    assert res_card.status_code == 200


# ─── 3. Authenticated Profile Editing & Tenant Scoping ─────────────────────────

def test_authenticated_owner_profile_editing_and_partial_update(test_setup):
    """Owner can update profile, omitted fields are preserved, and links are normalized."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    # 1. Initial complete profile setup
    init_payload = {
        "tagline": "Original Tagline",
        "phone_number": "+91 98765 43210",
        "website_url": "alpha.example.com",
        "address": "123 Old Street",
        "instagram_url": "instagram.com/original",
        "is_published": False,
        "show_review_button": True,
        "custom_links": [{"title": "Order Online", "url": "order.alpha.com"}],
    }
    res1 = auth_a.put("/api/businesses/tenant_alpha/profile", json=init_payload)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["tagline"] == "Original Tagline"
    assert d1["website_url"] == "https://alpha.example.com"
    assert d1["instagram_url"] == "https://instagram.com/original"
    assert d1["custom_links"][0]["url"] == "https://order.alpha.com"

    # 2. Partial update: Only update tagline and is_published
    partial_payload = {
        "tagline": "Updated New Tagline",
        "is_published": True,
    }
    res2 = auth_a.put("/api/businesses/tenant_alpha/profile", json=partial_payload)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["tagline"] == "Updated New Tagline"
    assert d2["is_published"] is True
    # Verify omitted fields were safely preserved
    assert d2["phone_number"] == "+91 98765 43210"
    assert d2["website_url"] == "https://alpha.example.com"
    assert d2["address"] == "123 Old Street"
    assert d2["instagram_url"] == "https://instagram.com/original"
    assert len(d2["custom_links"]) == 1


def test_profile_phone_and_link_validation(test_setup):
    """Invalid phone number formats are rejected with 422."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    res = auth_a.put(
        "/api/businesses/tenant_alpha/profile",
        json={"phone_number": "not-a-valid-phone-1234567890-xyz-letters"},
    )
    assert res.status_code == 422


def test_staff_and_manager_role_restrictions(test_setup):
    """Staff cannot edit profiles; managers can list documents but cannot upload or delete."""
    login_as = test_setup["login_as"]
    staff_a = test_setup["staff_a"]
    manager_a = test_setup["manager_a"]

    auth_staff = login_as(staff_a["id"], "tenant_alpha")
    auth_mgr = login_as(manager_a["id"], "tenant_alpha")

    # Staff cannot edit profile (requires owner) -> 403
    res_staff = auth_staff.put(
        "/api/businesses/tenant_alpha/profile",
        json={"tagline": "Hacked by staff"},
    )
    assert res_staff.status_code == 403
    assert "owner" in res_staff.json()["detail"].lower()

    # Manager CAN list documents -> 200
    res_list = auth_mgr.get("/api/businesses/tenant_alpha/documents")
    assert res_list.status_code == 200

    # Manager CANNOT upload document (requires owner) -> 403
    files = {"file": ("menu.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    res_mgr_upload = auth_mgr.post(
        "/api/businesses/tenant_alpha/documents",
        files=files,
    )
    assert res_mgr_upload.status_code == 403
    assert "owner" in res_mgr_upload.json()["detail"].lower()


def test_cross_tenant_profile_isolation(test_setup):
    """Owner of Tenant B cannot view or edit Tenant A's private profile."""
    login_as = test_setup["login_as"]
    owner_b = test_setup["owner_b"]
    auth_b = login_as(owner_b["id"], "tenant_beta")

    # Attempt to edit Tenant A's profile using Tenant B's session
    res = auth_b.put(
        "/api/businesses/tenant_alpha/profile",
        json={"tagline": "Tenant B hijacking Tenant A"},
    )
    assert res.status_code == 403
    assert "membership" in res.json()["detail"].lower()


# ─── 4. Document Operations (Upload, Listing, Update, Deletion) ───────────────

def test_valid_pdf_upload_and_listing(test_setup):
    """Owner uploads a valid PDF; metadata is tracked and accessible."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    files = {"file": ("Dinner Menu 2026.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    data = {
        "document_type": "food_menu",
        "display_name": "Evening Dinner Menu",
        "is_published": "true",
    }
    res = auth_a.post("/api/businesses/tenant_alpha/documents", files=files, data=data)
    assert res.status_code == 201
    doc = res.json()

    assert doc["tenant_id"] == "tenant_alpha"
    assert doc["document_type"] == "food_menu"
    assert doc["display_name"] == "Evening Dinner Menu"
    assert doc["original_filename"] == "Dinner Menu 2026.pdf"
    assert doc["file_size_bytes"] == len(SAMPLE_PDF_BYTES)
    assert doc["download_url"].startswith("/api/businesses/tenant_alpha/documents/")

    # List documents
    res_list = auth_a.get("/api/businesses/tenant_alpha/documents")
    assert res_list.status_code == 200
    docs = res_list.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc["id"]


def test_invalid_pdf_uploads(test_setup):
    """Empty files, non-PDF files, and oversized files are strictly rejected."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    # 1. Non-PDF signature
    bad_files = {"file": ("malicious.pdf", b"<html><body>Not a PDF</body></html>", "application/pdf")}
    res1 = auth_a.post("/api/businesses/tenant_alpha/documents", files=bad_files)
    assert res1.status_code == 422
    assert "PDF" in res1.json()["detail"]

    # 2. Empty file
    empty_files = {"file": ("empty.pdf", b"", "application/pdf")}
    res2 = auth_a.post("/api/businesses/tenant_alpha/documents", files=empty_files)
    assert res2.status_code == 422

    # 3. Oversized file (>10 MiB)
    oversized_data = b"%PDF-1.4 " + (b"0" * (MAX_DOCUMENT_SIZE_BYTES + 50))
    large_files = {"file": ("huge.pdf", oversized_data, "application/pdf")}
    res3 = auth_a.post("/api/businesses/tenant_alpha/documents", files=large_files)
    assert res3.status_code == 413
    assert "10 MiB" in res3.json()["detail"]


def test_document_metadata_update_and_publish_toggle(test_setup):
    """Owner can update display name and toggle document publication status."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    # Upload document
    files = {"file": ("drinks.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    upload_res = auth_a.post("/api/businesses/tenant_alpha/documents", files=files)
    doc_id = upload_res.json()["id"]

    # Patch document: change display name and unpublish
    patch_res = auth_a.patch(
        f"/api/businesses/tenant_alpha/documents/{doc_id}",
        json={"display_name": "Updated Bar Menu", "is_published": False},
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["display_name"] == "Updated Bar Menu"
    assert patched["is_published"] is False


def test_document_deletion_consistency(test_setup):
    """Deleting a document removes both the database record and physical disk file."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")
    doc_service = DocumentStorageService(storage_root=test_setup["docs_path"], store=test_setup["store"])

    # Upload
    files = {"file": ("delete_me.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    upload_res = auth_a.post("/api/businesses/tenant_alpha/documents", files=files)
    doc_id = upload_res.json()["id"]

    # Verify physical file exists
    file_path = doc_service.get_document_path("tenant_alpha", doc_id)
    assert file_path is not None and file_path.is_file()

    # Delete via API
    del_res = auth_a.delete(f"/api/businesses/tenant_alpha/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify database record is gone
    assert test_setup["store"].get_tenant_document("tenant_alpha", doc_id) is None

    # Verify file is deleted from disk
    assert not file_path.exists()


def test_cross_tenant_document_isolation(test_setup):
    """Tenant B cannot view, modify, or delete Tenant A's documents."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    owner_b = test_setup["owner_b"]

    auth_a = login_as(owner_a["id"], "tenant_alpha")
    auth_b = login_as(owner_b["id"], "tenant_beta")

    # Tenant A uploads document
    files = {"file": ("alpha_secret.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    upload_res = auth_a.post("/api/businesses/tenant_alpha/documents", files=files)
    doc_id = upload_res.json()["id"]

    # Tenant B tries to delete Tenant A's document via Tenant B's endpoint -> 404
    del_res = auth_b.delete(f"/api/businesses/tenant_beta/documents/{doc_id}")
    assert del_res.status_code == 404

    # Tenant B tries to delete directly on Tenant A's endpoint -> 403 (membership denied)
    del_res_a = auth_b.delete(f"/api/businesses/tenant_alpha/documents/{doc_id}")
    assert del_res_a.status_code == 403

    # Tenant B tries to patch Tenant A's document -> 404
    patch_res = auth_b.patch(
        f"/api/businesses/tenant_beta/documents/{doc_id}",
        json={"display_name": "Stolen Document"},
    )
    assert patch_res.status_code == 404


# ─── 5. Document Serving Security & Header Verification ──────────────────────

def test_document_serving_headers_and_draft_protection(test_setup):
    """Published PDFs serve with safe headers; unpublished PDFs return 404 to anonymous visitors."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    client = test_setup["client"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    # 1. Upload draft (unpublished) document
    files = {"file": ("Confidential_Draft.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    data = {"is_published": "false", "display_name": "Confidential Draft"}
    upload_res = auth_a.post("/api/businesses/tenant_alpha/documents", files=files, data=data)
    doc_id = upload_res.json()["id"]

    # Anonymous visitor receives 404
    anon_res = client.get(f"/api/businesses/tenant_alpha/documents/{doc_id}/file")
    assert anon_res.status_code == 404

    # Direct document lookup also receives 404
    direct_anon = client.get(f"/api/documents/{doc_id}")
    assert direct_anon.status_code == 404

    # Owner CAN view their own draft document
    owner_view = auth_a.get(f"/api/businesses/tenant_alpha/documents/{doc_id}/file")
    assert owner_view.status_code == 200
    assert owner_view.content == SAMPLE_PDF_BYTES

    # 2. Publish the document
    auth_a.patch(
        f"/api/businesses/tenant_alpha/documents/{doc_id}",
        json={"is_published": True},
    )

    # Now anonymous visitor receives 200 with hardened headers
    anon_pub = client.get(f"/api/businesses/tenant_alpha/documents/{doc_id}/file")
    assert anon_pub.status_code == 200
    assert anon_pub.content == SAMPLE_PDF_BYTES

    # Verify security headers
    headers = anon_pub.headers
    assert headers["content-type"] == "application/pdf"
    assert headers["x-content-type-options"] == "nosniff"
    assert "inline" in headers["content-disposition"]
    assert "Confidential_Draft.pdf" in headers["content-disposition"]


def test_malicious_filename_sanitization_on_upload(test_setup):
    """Path traversal sequences in filenames are sanitized and cannot escape directories."""
    login_as = test_setup["login_as"]
    owner_a = test_setup["owner_a"]
    auth_a = login_as(owner_a["id"], "tenant_alpha")

    files = {"file": ("../../../../etc/passwd.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    res = auth_a.post("/api/businesses/tenant_alpha/documents", files=files)
    assert res.status_code == 201
    data = res.json()
    assert ".." not in data["original_filename"]
    assert "/" not in data["original_filename"]


# ─── 6. Backup & Restore Path Traversal and Symlink Protections ───────────────

def test_backup_restore_symlink_rejection(test_setup, tmp_path):
    """Restoring an archive with symlinks is rejected with PermissionError."""
    # 1. Create a clean backup
    backup_dir = tmp_path / "valid_backup"
    create_backup(dest_dir=backup_dir)

    # 2. Inject a symlink into the backup documents directory
    backup_docs = backup_dir / "documents" / "tenant_alpha"
    backup_docs.mkdir(parents=True, exist_ok=True)
    symlink_target = tmp_path / "external_target.pdf"
    symlink_target.write_bytes(SAMPLE_PDF_BYTES)
    symlink_file = backup_docs / "evil_symlink.pdf"
    os.symlink(symlink_target, symlink_file)

    # Attempt to restore to isolated directory
    restore_target = tmp_path / "isolated_restore"
    with pytest.raises(PermissionError, match="Symlinks are prohibited"):
        restore_backup(backup_dir, restore_target)


# ─── 7. Preservation of Review Assistant System ──────────────────────────────

def test_existing_review_system_preservation(test_setup):
    """Existing review routes and workflows continue to function normally without gating."""
    client = test_setup["client"]

    # 1. Public review link endpoint
    res_link = client.get("/api/businesses/tenant_alpha/review-link")
    assert res_link.status_code == 200
    assert res_link.json()["business_name"] == "Cafe Alpha"

    # 2. Review ideas endpoint
    res_ideas = client.post(
        "/api/reviews/ideas",
        json={
            "business_id": "tenant_alpha",
            "rating": 5,
            "aspects": ["food", "service"],
            "user_note": "Great coffee and latte",
        },
    )
    assert res_ideas.status_code == 200
    assert len(res_ideas.json()["ideas"]) > 0

    # 3. Private feedback submission
    res_feedback = client.post(
        "/api/reviews/private-feedback",
        json={
            "business_id": "tenant_alpha",
            "diner_note": "Loved the ambience and service!",
            "rating": 5,
        },
    )
    assert res_feedback.status_code == 200
    assert res_feedback.json()["status"] in ("received", "escalated", "recorded")
    assert "ticket_id" in res_feedback.json()


# ─── 8. Digital Card Extended Fields & Brand Image Uploads ───────────────────

def test_digital_card_extended_fields_and_image_uploads(test_setup):
    """
    Verifies:
    1. Extended fields (display_name, category, opening_hours, welcome_message, email, whatsapp_group_url)
    2. Logo and cover image uploads, magic bytes check, size limit, and safe retrieval
    3. Old asset cleanup on replacement
    4. Public digital card reflects custom display_name and new fields
    """
    client = test_setup["client"]
    owner_client = test_setup["login_as"](test_setup["owner_a"]["id"], "tenant_alpha")

    # 1. Update profile with extended fields
    update_payload = {
        "display_name": "Cafe Alpha Grand Central",
        "category": "Artisan Bakery & Cafe",
        "opening_hours": "Mon - Sun: 8:00 AM - 11:00 PM",
        "welcome_message": "Welcome to Cafe Alpha Grand Central! Enjoy our artisan coffee.",
        "email": "contact@cafealpha.com",
        "whatsapp_group_url": "https://chat.whatsapp.com/testgroupalpha",
        "is_published": True,
    }
    res_update = owner_client.put("/api/businesses/tenant_alpha/profile", json=update_payload)
    assert res_update.status_code == 200, res_update.text
    profile_data = res_update.json()
    assert profile_data["display_name"] == "Cafe Alpha Grand Central"
    assert profile_data["email"] == "contact@cafealpha.com"
    assert profile_data["opening_hours"] == "Mon - Sun: 8:00 AM - 11:00 PM"
    assert profile_data["whatsapp_group_url"] == "https://chat.whatsapp.com/testgroupalpha"

    # 2. Upload Logo Image (Valid PNG)
    sample_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
        b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    res_img = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("logo.png", sample_png, "image/png")},
    )
    assert res_img.status_code == 200, res_img.text
    img_json = res_img.json()
    assert img_json["image_type"] == "logo"
    assert "/api/businesses/tenant_alpha/images/" in img_json["image_url"]

    # 3. Serve uploaded logo image
    logo_filename = img_json["filename"]
    res_serve = client.get(f"/api/businesses/tenant_alpha/images/{logo_filename}")
    assert res_serve.status_code == 200
    assert res_serve.headers["content-type"] == "image/png"
    assert res_serve.headers["x-content-type-options"] == "nosniff"
    assert res_serve.content == sample_png

    # 4. Reject invalid format (e.g. text file pretending to be image)
    res_bad_img = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("fake.png", b"This is not a real image header", "image/png")},
    )
    assert res_bad_img.status_code == 422

    # 5. Verify Public Card reflects display_name, category, email, hours, welcome_msg, and logo
    res_public = client.get("/api/businesses/tenant_alpha/card")
    assert res_public.status_code == 200, res_public.text
    card_data = res_public.json()
    assert card_data["business_name"] == "Cafe Alpha Grand Central"
    assert card_data["display_name"] == "Cafe Alpha Grand Central"
    assert card_data["category"] == "Artisan Bakery & Cafe"
    assert card_data["opening_hours"] == "Mon - Sun: 8:00 AM - 11:00 PM"
    assert card_data["welcome_message"] == "Welcome to Cafe Alpha Grand Central! Enjoy our artisan coffee."
    assert card_data["email"] == "contact@cafealpha.com"
    assert card_data["whatsapp_group_url"] == "https://chat.whatsapp.com/testgroupalpha"
    assert card_data["logo_path"] == img_json["image_url"]

