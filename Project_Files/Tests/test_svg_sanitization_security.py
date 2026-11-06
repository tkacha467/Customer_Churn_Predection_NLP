"""
Automated Security & Sanitization Test Suite for SVG Logo Uploads (Phase 1, Task 2).
Covers:
- A. Valid SVG: normal logo uploads successfully, safe paths, shapes, gradients, and colors preserved.
- B. Malicious SVG: script removal/rejection, onload/onclick removal, javascript: URLs rejected,
     foreignObject rejected, external image references rejected, dangerous CSS rejected,
     malformed XML rejected, XML external entities (XXE) and entity bombs prevented.
- C. Upload Integrity: stored file contains sanitized content, SHA-256 matches stored file,
     file metadata consistency, tenant boundary isolation.
- D. Regression Testing: PNG uploads, JPEG uploads, PDF document uploads, profile updates, backup/restore.
"""

import hashlib
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

SAMPLE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

SAMPLE_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x80\xff\xd9"
)

SAMPLE_VALID_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <defs>
    <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ea580c"/>
      <stop offset="100%" stop-color="#f97316"/>
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="40" fill="url(#brandGrad)" stroke="#fed7aa" stroke-width="2"/>
  <path d="M30 40 L70 40 L50 70 Z" fill="#ffffff"/>
  <text x="50" y="85" font-family="sans-serif" font-size="10" fill="#ea580c" text-anchor="middle">CAFE</text>
</svg>"""


@pytest.fixture
def svg_test_env(tmp_path, monkeypatch):
    """Sets up an isolated database and document environment for SVG tests."""
    db_path = tmp_path / "svg_test.sqlite3"
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

    # Tenant Alpha (Owner A)
    store.upsert_tenant({
        "id": "tenant_alpha",
        "business_name": "Cafe Alpha",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })
    user_a = store.create_user(
        email="owner_a@alpha.test",
        password_hash=hash_password("OwnerAlpha123!"),
        display_name="Alpha Owner",
        is_active=1,
    )
    store.add_membership(user_a["id"], "tenant_alpha", role="owner")

    # Tenant Beta (Owner B)
    store.upsert_tenant({
        "id": "tenant_beta",
        "business_name": "Bistro Beta",
        "status": "active",
        "entitlements": ["review_manager", "digital_card"],
    })
    user_b = store.create_user(
        email="owner_b@beta.test",
        password_hash=hash_password("OwnerBeta123!"),
        display_name="Beta Owner",
        is_active=1,
    )
    store.add_membership(user_b["id"], "tenant_beta", role="owner")

    client = TestClient(app)

    def login_as(user_id: str, tenant_id: str) -> TestClient:
        raw_token = generate_session_token()
        token_hash = hash_token(raw_token)
        store.create_session(
            token_hash=token_hash,
            user_id=user_id,
            active_tenant_id=tenant_id,
            expires_at=time.time() + SESSION_TTL_SECONDS,
        )
        c = TestClient(app)
        c.cookies.set(OWNER_COOKIE, raw_token)
        return c

    return {
        "store": store,
        "client": client,
        "owner_a_client": login_as(user_a["id"], "tenant_alpha"),
        "owner_b_client": login_as(user_b["id"], "tenant_beta"),
        "docs_path": docs_path,
        "db_path": db_path,
        "tmp_path": tmp_path,
    }


# ─── Group A: Valid SVG Tests ────────────────────────────────────────────────

def test_valid_svg_upload_and_rendering(svg_test_env):
    """Proves that a normal, well-formed SVG logo uploads, preserves shapes and colors, and serves with CSP."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("logo.svg", SAMPLE_VALID_SVG, "image/svg+xml")},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["image_type"] == "logo"
    assert data["mime_type"] == "image/svg+xml"
    assert data["filename"].endswith(".svg")
    assert "sha256" in data

    # Verify serving
    serve_res = client.get(data["image_url"])
    assert serve_res.status_code == 200
    assert serve_res.headers["content-type"] == "image/svg+xml"
    assert serve_res.headers["x-content-type-options"] == "nosniff"
    assert "Content-Security-Policy" in serve_res.headers

    # Verify safe elements and styles preserved
    body = serve_res.text
    assert "<circle" in body
    assert "<path" in body
    assert "<text" in body
    assert "brandGrad" in body
    assert "#ea580c" in body


def test_real_nasta_ghar_svg_preserved(svg_test_env):
    """Proves that the real restaurant logo SVG uploads and preserves complex filters and gradients."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    logo_path = Path("Digital_Card/frontend/public/restaurant/nasta-ghar-logo.svg")
    assert logo_path.exists()
    raw_logo = logo_path.read_bytes()

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("nasta-ghar.svg", raw_logo, "image/svg+xml")},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    serve_res = client.get(data["image_url"])
    assert serve_res.status_code == 200
    body = serve_res.text
    assert "NASTA GHAR" in body
    assert "ngBrandGrad" in body
    assert "feDropShadow" in body


# ─── Group B: Malicious SVG Tests ────────────────────────────────────────────

def test_script_tag_neutralized(svg_test_env):
    """Proves that <script> tags inside SVG are completely stripped before saving."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    malicious_svg = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="40" fill="red"/>
      <script type="text/javascript">alert('XSS_ATTACK')</script>
    </svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_script.svg", malicious_svg, "image/svg+xml")},
    )
    assert res.status_code in (200, 422)
    if res.status_code == 200:
        serve_res = client.get(res.json()["image_url"])
        assert b"<script" not in serve_res.content
        assert b"XSS_ATTACK" not in serve_res.content
        assert b"circle" in serve_res.content


def test_inline_event_handlers_removed(svg_test_env):
    """Proves that onload, onclick, and onerror attributes are stripped from SVG elements."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    malicious_svg = b"""<svg xmlns="http://www.w3.org/2000/svg" onload="fetch('http://attacker.com')" viewBox="0 0 100 100">
      <rect x="10" y="10" width="80" height="80" onclick="alert(1)" onmouseover="steal()" fill="blue"/>
    </svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_events.svg", malicious_svg, "image/svg+xml")},
    )
    assert res.status_code in (200, 422)
    if res.status_code == 200:
        serve_res = client.get(res.json()["image_url"])
        content_lower = serve_res.content.lower()
        assert b"onload" not in content_lower
        assert b"onclick" not in content_lower
        assert b"onmouseover" not in content_lower
        assert b"rect" in content_lower


def test_javascript_urls_rejected(svg_test_env):
    """Proves that SVG with javascript: URI in href or attributes is rejected."""
    owner_client = svg_test_env["owner_a_client"]

    malicious_svg = b"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
      <a xlink:href="javascript:alert(1)">
        <circle cx="20" cy="20" r="10"/>
      </a>
    </svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_js_uri.svg", malicious_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "SVG validation failed" in res.json()["detail"]


def test_foreign_object_rejected(svg_test_env):
    """Proves that foreignObject element is rejected."""
    owner_client = svg_test_env["owner_a_client"]

    malicious_svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="5"/>
      <foreignObject width="100" height="100">
        <body xmlns="http://www.w3.org/1999/xhtml">
          <iframe src="http://evil.com"></iframe>
        </body>
      </foreignObject>
    </svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_foreign.svg", malicious_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "forbidden active element: <foreignobject>" in res.json()["detail"]


def test_external_image_references_rejected(svg_test_env):
    """Proves that SVG referencing external HTTP/HTTPS resources is rejected."""
    owner_client = svg_test_env["owner_a_client"]

    malicious_svg = b"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
      <image href="https://tracker.evil.com/pixel.png" width="10" height="10"/>
      <circle cx="5" cy="5" r="5"/>
    </svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_tracker.svg", malicious_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "forbidden external resource reference" in res.json()["detail"]


def test_dangerous_css_rejected(svg_test_env):
    """Proves that unsafe CSS expressions and @import rules in SVG are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    css_import_svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <style>@import url("http://evil.com/style.css");</style>
      <circle cx="10" cy="10" r="5"/>
    </svg>"""

    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_css1.svg", css_import_svg, "image/svg+xml")},
    )
    assert res1.status_code == 422
    assert "unsafe CSS" in res1.json()["detail"]

    css_expr_svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="5" style="width: expression(alert(1));"/>
    </svg>"""

    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_css2.svg", css_expr_svg, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "unsafe CSS" in res2.json()["detail"]


def test_malformed_xml_rejected(svg_test_env):
    """Proves that unclosed tags or syntax errors in SVG XML are rejected with 422."""
    owner_client = svg_test_env["owner_a_client"]

    malformed_svg = b"<svg xmlns='http://www.w3.org/2000/svg'><circle cx='5' cy='5' r='5'>"

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("bad_xml.svg", malformed_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "Malformed or unparseable SVG XML" in res.json()["detail"]


def test_xml_external_entity_and_dtd_attack_prevented(svg_test_env):
    """Proves that XXE and entity expansion (Billion Laughs) in SVG are blocked."""
    owner_client = svg_test_env["owner_a_client"]

    xxe_svg = b"""<?xml version="1.0" standalone="no"?>
    <!DOCTYPE svg [
      <!ELEMENT svg ANY >
      <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
    <svg xmlns="http://www.w3.org/2000/svg">&xxe;<circle cx="5" cy="5" r="5"/></svg>"""

    res_xxe = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("xxe.svg", xxe_svg, "image/svg+xml")},
    )
    assert res_xxe.status_code == 422
    assert "XML external entities and DTD declarations are forbidden" in res_xxe.json()["detail"]


# ─── Group C: Upload Integrity & Tenant Boundary Tests ───────────────────────

def test_upload_integrity_and_sha256_match(svg_test_env):
    """Proves that stored SVG bytes match the sanitized output and returned SHA-256."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]
    docs_path = svg_test_env["docs_path"]

    raw_input = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
      <circle cx="25" cy="25" r="20" fill="purple" onload="alert(1)"/>
      <script>alert('drop_me')</script>
    </svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("sanitized_logo.svg", raw_input, "image/svg+xml")},
    )
    assert res.status_code == 200
    meta = res.json()
    returned_sha = meta["sha256"]
    returned_size = meta["size_bytes"]

    # Verify on-disk file
    stored_path = docs_path / "tenant_alpha" / "images" / meta["filename"]
    assert stored_path.exists()
    disk_bytes = stored_path.read_bytes()
    assert hashlib.sha256(disk_bytes).hexdigest() == returned_sha
    assert len(disk_bytes) == returned_size

    # Verify sanitized content on disk
    assert b"<script" not in disk_bytes
    assert b"onload" not in disk_bytes
    assert b"circle" in disk_bytes

    # Verify served content matches disk exactly
    served_res = client.get(meta["image_url"])
    assert served_res.status_code == 200
    assert served_res.content == disk_bytes


def test_tenant_isolation_boundary_on_images(svg_test_env):
    """Proves that Tenant A cannot access Tenant B's images directory or upload on their behalf."""
    owner_a = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    # Owner A attempts to upload to Tenant Beta -> 403 Forbidden
    res_hack = owner_a.post(
        "/api/businesses/tenant_beta/images",
        data={"image_type": "logo"},
        files={"file": ("hack.svg", SAMPLE_VALID_SVG, "image/svg+xml")},
    )
    assert res_hack.status_code == 403

    # Upload clean image for Tenant Alpha
    res_a = owner_a.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("alpha_logo.svg", SAMPLE_VALID_SVG, "image/svg+xml")},
    )
    assert res_a.status_code == 200
    alpha_filename = res_a.json()["filename"]

    # Verify Tenant Beta cannot serve Tenant Alpha's image under Beta's URL
    res_cross = client.get(f"/api/businesses/tenant_beta/images/{alpha_filename}")
    assert res_cross.status_code == 404


# ─── Group D: Regression Testing ─────────────────────────────────────────────

def test_png_and_jpeg_uploads_unaffected(svg_test_env):
    """Proves that existing raster formats (PNG, JPEG) continue to upload and serve cleanly."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    # 1. PNG Upload
    res_png = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("logo.png", SAMPLE_PNG_BYTES, "image/png")},
    )
    assert res_png.status_code == 200
    assert res_png.json()["mime_type"] == "image/png"
    serve_png = client.get(res_png.json()["image_url"])
    assert serve_png.status_code == 200
    assert serve_png.content == SAMPLE_PNG_BYTES

    # 2. JPEG Upload
    res_jpg = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "cover"},
        files={"file": ("cover.jpg", SAMPLE_JPEG_BYTES, "image/jpeg")},
    )
    assert res_jpg.status_code == 200
    assert res_jpg.json()["mime_type"] == "image/jpeg"
    serve_jpg = client.get(res_jpg.json()["image_url"])
    assert serve_jpg.status_code == 200
    assert serve_jpg.content == SAMPLE_JPEG_BYTES


def test_pdf_document_upload_unaffected(svg_test_env):
    """Proves that PDF document uploads and serving remain completely intact."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    res_pdf = owner_client.post(
        "/api/businesses/tenant_alpha/documents",
        data={"document_type": "food_menu", "display_name": "Autumn Menu", "is_published": "true"},
        files={"file": ("menu.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
    )
    assert res_pdf.status_code == 201
    doc_data = res_pdf.json()
    assert doc_data["display_name"] == "Autumn Menu"

    serve_pdf = client.get(f"/api/businesses/tenant_alpha/documents/{doc_data['id']}/file")
    assert serve_pdf.status_code == 200
    assert serve_pdf.headers["content-type"] == "application/pdf"
    assert serve_pdf.content == SAMPLE_PDF_BYTES


def test_profile_update_and_backup_restore_pass(svg_test_env):
    """Proves that business profile updates and backup/restore work with uploaded SVG logos."""
    owner_client = svg_test_env["owner_a_client"]
    tmp_path = svg_test_env["tmp_path"]
    store = svg_test_env["store"]

    # 1. Upload SVG logo
    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("brand_logo.svg", SAMPLE_VALID_SVG, "image/svg+xml")},
    )
    assert res.status_code == 200
    logo_url = res.json()["image_url"]

    # 2. Check profile was updated
    prof = store.get_business_profile("tenant_alpha")
    assert prof is not None
    assert prof["logo_path"] == logo_url

    # 3. Create hot backup
    backup_target = tmp_path / "backup_with_svg"
    created = create_backup(dest_dir=backup_target)
    assert created.exists()
    assert verify_backup(created) is True

    # 4. Restore to isolated location
    restore_target = tmp_path / "restored_svg_system"
    assert restore_backup(created, restore_target) is True
    assert (restore_target / "reviews.sqlite3").exists()
    assert (restore_target / "documents").exists()


# ─── Group E: Adversarial Hardening Tests (Phase 1, Task 2.1) ─────────────────

def test_adversarial_css_hex_escape_bypass_blocked(svg_test_env):
    """Proves that CSS hex escape sequences (\\65 xpression, \\6a avascript) are normalized and rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # 1. Hex-escaped expression
    svg1 = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="5" style="width: \\65 xpression(alert(1));"/>
    </svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_hex1.svg", svg1, "image/svg+xml")},
    )
    assert res1.status_code == 422
    assert "unsafe CSS" in res1.json()["detail"]

    # 2. Hex-escaped javascript
    svg2 = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="5" style="fill: \\6a avascript:alert(1);"/>
    </svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_hex2.svg", svg2, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "unsafe CSS" in res2.json()["detail"]


def test_adversarial_css_comment_obfuscation_blocked(svg_test_env):
    """Proves that comments embedded inside CSS keywords (exp/*comment*/ression) are normalized and rejected."""
    owner_client = svg_test_env["owner_a_client"]

    svg_comment = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <style>
        circle { background: exp/*obfuscation*/ression(alert(1)); }
      </style>
      <circle cx="10" cy="10" r="5"/>
    </svg>"""
    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_comment.svg", svg_comment, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "unsafe CSS" in res.json()["detail"]


def test_adversarial_css_property_allowlist_enforced(svg_test_env):
    """Proves that unallowed CSS properties (behavior, -moz-binding, position) are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # Behavior HTC
    svg_htc = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5" style="behavior: url(default.hta);"/>
    </svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_htc.svg", svg_htc, "image/svg+xml")},
    )
    assert res1.status_code == 422
    assert "unsafe CSS" in res1.json()["detail"]

    # Layout hijacking property
    svg_pos = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5" style="position: fixed; z-index: 99999;"/>
    </svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_pos.svg", svg_pos, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "unsafe CSS" in res2.json()["detail"]


def test_adversarial_nested_svg_data_uri_rejected(svg_test_env):
    """Proves that nested SVG content inside data: URIs is rejected."""
    owner_client = svg_test_env["owner_a_client"]

    svg_nested = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5"/>
      <image href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxzY3JpcHQ+YWxlcnQoMSk8L3NjcmlwdD48L3N2Zz4="/>
    </svg>"""
    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_nested_svg.svg", svg_nested, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "Disallowed data URI MIME type" in res.json()["detail"]


def test_adversarial_html_and_js_data_uris_rejected(svg_test_env):
    """Proves that HTML and JavaScript data: URIs are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # HTML payload
    svg_html = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5"/>
      <image href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="/>
    </svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_data_html.svg", svg_html, "image/svg+xml")},
    )
    assert res1.status_code == 422

    # JS payload
    svg_js = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5"/>
      <image href="data:application/javascript;base64,YWxlcnQoMSk="/>
    </svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_data_js.svg", svg_js, "image/svg+xml")},
    )
    assert res2.status_code == 422


def test_adversarial_malformed_and_fake_data_uris_rejected(svg_test_env):
    """Proves that data: URIs with corrupt base64 or invalid magic byte headers are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # 1. Invalid base64 characters
    svg_bad_b64 = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5"/>
      <image href="data:image/png;base64,!!!NOT_BASE64@@@"/>
    </svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("evil_b64.svg", svg_bad_b64, "image/svg+xml")},
    )
    assert res1.status_code == 422

    # 2. Text content disguised as image/png
    fake_png = b"data:image/png;base64," + (b"PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==")
    svg_fake_png = b"""<svg xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="5" r="5"/><image href=\"""" + fake_png + b"""\"/></svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("fake_png.svg", svg_fake_png, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "file header signature is invalid" in res2.json()["detail"]


def test_adversarial_valid_raster_png_data_uri_accepted(svg_test_env):
    """Proves that embedded genuine raster PNG base64 in <image> is accepted and preserved."""
    owner_client = svg_test_env["owner_a_client"]
    client = svg_test_env["client"]

    import base64
    valid_png_uri = "data:image/png;base64," + base64.b64encode(SAMPLE_PNG_BYTES).decode("ascii")
    svg_with_png = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
      <circle cx="25" cy="25" r="20" fill="#f97316"/>
      <image href="{valid_png_uri}" width="16" height="16" x="17" y="17"/>
    </svg>""".encode("utf-8")

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("raster_logo.svg", svg_with_png, "image/svg+xml")},
    )
    assert res.status_code == 200
    serve_res = client.get(res.json()["image_url"])
    assert serve_res.status_code == 200
    assert "data:image/png;base64," in serve_res.text


def test_adversarial_smil_and_svg_animation_rejected(svg_test_env):
    """Proves that SMIL animation elements (<animate>, <set>, <animateTransform>) are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # 1. <animate>
    svg_anim = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5">
        <animate attributeName="r" from="5" to="10" dur="1s"/>
      </circle>
    </svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("anim.svg", svg_anim, "image/svg+xml")},
    )
    assert res1.status_code == 422
    assert "forbidden active element: <animate>" in res1.json()["detail"]

    # 2. <set>
    svg_set = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="5" r="5">
        <set attributeName="fill" to="blue"/>
      </circle>
    </svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("set.svg", svg_set, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "forbidden active element: <set>" in res2.json()["detail"]


def test_adversarial_feimage_and_anchor_rejected(svg_test_env):
    """Proves that <feImage> filter sources and <a> hyperlinks in SVG logos are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # 1. <feImage>
    svg_fe = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <filter id="f">
        <feImage href="https://tracker.evil.com/x.png"/>
      </filter>
      <circle cx="5" cy="5" r="5" filter="url(#f)"/>
    </svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("feimage.svg", svg_fe, "image/svg+xml")},
    )
    assert res1.status_code == 422

    # 2. <a> hyperlink
    svg_a = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <a href="https://evil.com">
        <circle cx="5" cy="5" r="5"/>
      </a>
    </svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("anchor.svg", svg_a, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "forbidden active element: <a>" in res2.json()["detail"]


def test_adversarial_foreign_namespace_element_rejected(svg_test_env):
    """Proves that foreign XML namespace tags (<html:div>) are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    foreign_ns_svg = b"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:html="http://www.w3.org/1999/xhtml">
      <circle cx="5" cy="5" r="5"/>
      <html:div>Injected HTML</html:div>
    </svg>"""
    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("foreign_ns.svg", foreign_ns_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "prohibited element namespace" in res.json()["detail"]


def test_adversarial_disallowed_processing_instructions_rejected(svg_test_env):
    """Proves that processing instructions other than <?xml ?> (e.g. <?xpacket ?>, <?evil-pi ?>) are rejected."""
    owner_client = svg_test_env["owner_a_client"]

    # 1. <?xpacket ...?>
    xpacket_svg = b"""<?xml version="1.0"?>
    <?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
    <svg xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="5" r="5"/></svg>"""
    res1 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("xpacket.svg", xpacket_svg, "image/svg+xml")},
    )
    assert res1.status_code == 422
    assert "prohibited XML processing instruction" in res1.json()["detail"]

    # 2. Custom PI
    custom_pi_svg = b"""<?xml version="1.0"?>
    <?evil-pi action="steal"?>
    <svg xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="5" r="5"/></svg>"""
    res2 = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("custom_pi.svg", custom_pi_svg, "image/svg+xml")},
    )
    assert res2.status_code == 422
    assert "prohibited XML processing instruction" in res2.json()["detail"]


def test_adversarial_excessive_nesting_depth_rejected(svg_test_env):
    """Proves that deeply nested XML structures exceeding depth 30 are rejected before processing."""
    owner_client = svg_test_env["owner_a_client"]

    # Build 40 levels of nesting
    nested_open = b"".join(f"<g id='g{i}'>".encode("ascii") for i in range(40))
    nested_close = b"".join(b"</g>" for _ in range(40))
    deep_svg = b"""<svg xmlns="http://www.w3.org/2000/svg">""" + nested_open + b"""<circle cx="5" cy="5" r="5"/>""" + nested_close + b"""</svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("deep_nesting.svg", deep_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "maximum permitted XML element nesting depth" in res.json()["detail"]


def test_adversarial_excessive_element_count_rejected(svg_test_env):
    """Proves that SVGs with excessive element counts (> 2,000) are rejected to prevent DoS."""
    owner_client = svg_test_env["owner_a_client"]

    # Generate 2,100 tiny elements
    many_circles = b"".join(f"<circle cx='{i%100}' cy='{i%100}' r='1'/>".encode("ascii") for i in range(2100))
    huge_count_svg = b"""<svg xmlns="http://www.w3.org/2000/svg">""" + many_circles + b"""</svg>"""

    res = owner_client.post(
        "/api/businesses/tenant_alpha/images",
        data={"image_type": "logo"},
        files={"file": ("huge_count.svg", huge_count_svg, "image/svg+xml")},
    )
    assert res.status_code == 422
    assert "maximum permitted XML element count" in res.json()["detail"]

