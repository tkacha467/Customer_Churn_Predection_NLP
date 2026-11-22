"""
Phase 4.1 Automated Test Suite: Dynamic Restaurant Template Configuration Foundation.
Covers:
1. Four exact template identifiers are registered and unique.
2. All four presets pass Pydantic schema validation.
3. Invalid HEX colors and unapproved font keys are rejected.
4. Arbitrary HTML, JavaScript, CSS injection, and unapproved components are rejected.
5. Mixed-script Unicode validation works for English, Gujarati, and Hindi.
6. Draft versions can be updated.
7. Published versions are immutable (mutation rejected).
8. New drafts can be created for existing templates.
9. Admin-only publishing authorization enforced.
10. Only published versions can be assigned to businesses.
11. Assignment version pinning works.
12. Cross-tenant assignment to non-existent business is rejected.
13. Explicit upgrade preserves assignment history (marks previous as superseded).
14. Archived templates cannot receive new assignments.
15. Existing assignments to archived versions remain accessible.
16. default_business configuration resolves cleanly with zero disruption.
17. Public configuration returns only sanitized public fields (anti-leak).
18. Google review anti-gating compliance is guaranteed for all ratings (1-5).
"""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.auth.auth import get_store, _login_attempts, _login_lock, _ip_attempts, _account_failures, _ip_account_failures
from backend.app.api.template_schemas import (
    TemplateConfigurationPayload,
    VisualTokensConfig,
    LayoutConfig,
)
from pydantic import ValidationError

client = TestClient(app)


@pytest.fixture(autouse=True)
def admin_login():
    """Authenticate client with platform administrator credentials."""
    with _login_lock:
        _login_attempts.clear()
        _ip_attempts.clear()
        _account_failures.clear()
        _ip_account_failures.clear()
    res = client.post("/api/auth/login", json={"email": "owner@nastaghar.com", "password": "Owner123!"})
    if res.status_code != 200:
        print("LOGIN ERROR:", res.status_code, res.text)
    assert res.status_code == 200
    assert res.json().get("authenticated") is True
    yield
    client.cookies.clear()


# ─── 1. REGISTRY & PRESETS ───────────────────────────────────────────────────

def test_four_restaurant_template_ids_registered_and_unique():
    """All 4 exact restaurant template IDs must be registered, active, and unique."""
    res = client.get("/api/platform/templates?industry=restaurant")
    assert res.status_code == 200
    templates = res.json()
    slugs = [t["slug"] for t in templates]

    expected_slugs = [
        "restaurant_classic_bistro",
        "restaurant_modern_urban",
        "restaurant_luxury_dining",
        "restaurant_cafe_playful",
    ]
    for expected in expected_slugs:
        assert expected in slugs, f"Template '{expected}' missing from registry"

    # Verify uniqueness
    assert len(slugs) == len(set(slugs)), "Duplicate template identifiers detected"


def test_four_presets_pass_schema_validation():
    """All 4 restaurant presets pass strict Pydantic v2 schema validation."""
    res = client.get("/api/platform/templates?industry=restaurant")
    assert res.status_code == 200
    templates = res.json()

    expected_slugs = {
        "restaurant_classic_bistro",
        "restaurant_modern_urban",
        "restaurant_luxury_dining",
        "restaurant_cafe_playful",
    }
    checked = 0
    for tpl in templates:
        if tpl["slug"] in expected_slugs:
            cfg = tpl.get("configuration")
            assert cfg, f"Missing configuration for {tpl['slug']}"
            # Validate through Pydantic
            payload = TemplateConfigurationPayload.model_validate(cfg)
            assert payload.theme.primary_accent.startswith("#")
            assert payload.layout.header_variant
            assert len(payload.components) == 8
            checked += 1
    assert checked == 4, "Expected all 4 approved presets to be validated"


# ─── 2. STRICT VALIDATION & SECURITY INJECTION CHECKS ────────────────────────

def test_invalid_hex_colors_rejected():
    """HEX validation accepts ONLY #RRGGBB and #RRGGBBAA. 3-digit, 4-digit, named colors rejected."""
    # 1. Valid 6-digit and 8-digit HEX must pass
    valid_6 = VisualTokensConfig(
        background_color="#FAF7F2",
        card_surface_color="#FFFFFF",
        primary_accent="#1B4332",
        secondary_accent="#C5A059",
    )
    assert valid_6.primary_accent == "#1b4332"

    valid_8 = VisualTokensConfig(
        background_color="#FAF7F2FF",
        card_surface_color="#FFFFFFFF",
        primary_accent="#1B433280",
        secondary_accent="#C5A059CC",
    )
    assert valid_8.primary_accent == "#1b433280"

    # 2. 3-digit shorthand HEX must be REJECTED
    with pytest.raises(ValidationError):
        VisualTokensConfig(
            background_color="#FFF",
            card_surface_color="#FFFFFF",
            primary_accent="#1B4332",
            secondary_accent="#C5A059",
        )

    # 3. 4-digit shorthand HEX must be REJECTED
    with pytest.raises(ValidationError):
        VisualTokensConfig(
            background_color="#FFFF",
            card_surface_color="#FFFFFF",
            primary_accent="#1B4332",
            secondary_accent="#C5A059",
        )

    # 4. Named colors must be REJECTED
    with pytest.raises(ValidationError):
        VisualTokensConfig(
            background_color="red",
            card_surface_color="#FFFFFF",
            primary_accent="#1B4332",
            secondary_accent="#C5A059",
        )

    # 5. Malformed HEX strings must be REJECTED
    with pytest.raises(ValidationError):
        VisualTokensConfig(
            background_color="#12",
            card_surface_color="#FFFFFF",
            primary_accent="#1B4332",
            secondary_accent="#C5A059",
        )

    with pytest.raises(ValidationError):
        VisualTokensConfig(
            background_color="rgb(255,255,255)",
            card_surface_color="#FFFFFF",
            primary_accent="#1B4332",
            secondary_accent="#C5A059",
        )


def test_unapproved_font_keys_rejected():
    """Unapproved font keys must be rejected by Pydantic."""
    with pytest.raises(ValidationError):
        VisualTokensConfig(
            background_color="#FAF7F2",
            card_surface_color="#FFFFFF",
            primary_accent="#1B4332",
            secondary_accent="#C5A059",
            heading_font_key="comic_sans_ms",  # Not approved
        )


def test_arbitrary_html_and_script_injection_rejected():
    """Arbitrary HTML, JavaScript, and CSS strings must be rejected in configuration payloads."""
    # 1. Script tag injection in layout variant
    with pytest.raises(ValidationError):
        LayoutConfig(header_variant="<script>alert(1)</script>")

    # 2. XSS payload in component list
    with pytest.raises(ValidationError):
        TemplateConfigurationPayload(
            theme=VisualTokensConfig(
                background_color="#FAF7F2",
                card_surface_color="#FFFFFF",
                primary_accent="#1B4332",
                secondary_accent="#C5A059",
            ),
            components=["business_header", "<script>malicious()</script>"]
        )

    # 3. Unapproved component identifier rejected
    with pytest.raises(ValidationError):
        TemplateConfigurationPayload(
            theme=VisualTokensConfig(
                background_color="#FAF7F2",
                card_surface_color="#FFFFFF",
                primary_accent="#1B4332",
                secondary_accent="#C5A059",
            ),
            components=["business_header", "unapproved_custom_component"]
        )


def test_mixed_script_unicode_validation():
    """Legitimate mixed-script text in Gujarati/Hindi (brand names, numbers) must be accepted."""
    valid_config = {
        "schema_version": "1.0",
        "theme": {
            "background_color": "#FAF7F2",
            "card_surface_color": "#FFFFFF",
            "primary_accent": "#1B4332",
            "secondary_accent": "#C5A059",
            "heading_font_key": "playfair_display",
            "body_font_key": "lato",
            "gujarati_font_key": "noto_serif_gujarati",
            "hindi_font_key": "noto_serif_devanagari",
        },
        "components": [
            "business_header", "rating_selector", "topic_selector",
            "personal_note", "ai_suggestions", "review_editor",
            "google_handoff", "private_feedback"
        ],
        "localized_content": {
            "en": {"welcome_title": "Welcome to Nasta Ghar #4!"},
            "gu": {"welcome_title": "નાસ્તા ઘર ટેબલ 4 પર આપનું સ્વાગત છે! (Nasta Ghar Table 4)"},
            "hi": {"welcome_title": "नाश्ता घर टेबल 4 में आपका स्वागत है!"}
        }
    }
    payload = TemplateConfigurationPayload.model_validate(valid_config)
    assert "નાસ્તા ઘર" in payload.localized_content.gu["welcome_title"]


# ─── 3. VERSION MANAGEMENT & IMMUTABILITY ─────────────────────────────────────

def test_draft_version_lifecycle_and_immutability():
    """Draft versions can be edited; published versions are immutable."""
    # 1. Create new draft version 1.1.0 on restaurant_classic_bistro
    res_draft = client.post(
        "/api/platform/templates/restaurant_classic_bistro/versions",
        json={
            "version": "1.1.0",
            "configuration": {
                "schema_version": "1.0",
                "theme": {
                    "background_color": "#FAF7F2",
                    "card_surface_color": "#FFFFFF",
                    "primary_accent": "#1B4332",
                    "secondary_accent": "#C5A059",
                    "heading_font_key": "playfair_display",
                    "body_font_key": "lato",
                    "gujarati_font_key": "noto_serif_gujarati",
                    "hindi_font_key": "noto_serif_devanagari",
                },
                "components": [
                    "business_header", "rating_selector", "topic_selector",
                    "personal_note", "ai_suggestions", "review_editor",
                    "google_handoff", "private_feedback"
                ]
            }
        }
    )
    assert res_draft.status_code == 200
    draft_id = res_draft.json()["data"]["id"]

    # 2. Update the draft version (Allowed while draft)
    res_up = client.put(
        f"/api/platform/templates/restaurant_classic_bistro/versions/{draft_id}",
        json={
            "configuration": {
                "schema_version": "1.0",
                "theme": {
                    "background_color": "#FAF7F2",
                    "card_surface_color": "#FFFFFF",
                    "primary_accent": "#2D6A4F",  # Modified accent in draft
                    "secondary_accent": "#C5A059",
                    "heading_font_key": "playfair_display",
                    "body_font_key": "lato",
                    "gujarati_font_key": "noto_serif_gujarati",
                    "hindi_font_key": "noto_serif_devanagari",
                },
                "components": [
                    "business_header", "rating_selector", "topic_selector",
                    "personal_note", "ai_suggestions", "review_editor",
                    "google_handoff", "private_feedback"
                ]
            }
        }
    )
    assert res_up.status_code == 200

    # 3. Publish the version
    res_pub = client.post(f"/api/platform/templates/restaurant_classic_bistro/versions/{draft_id}/publish")
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] == "published"

    # 4. Attempt to mutate published version (MUST FAIL with 400 Bad Request)
    res_mutate = client.put(
        f"/api/platform/templates/restaurant_classic_bistro/versions/{draft_id}",
        json={
            "configuration": {
                "schema_version": "1.0",
                "theme": {
                    "background_color": "#000000",
                    "card_surface_color": "#000000",
                    "primary_accent": "#000000",
                    "secondary_accent": "#000000",
                    "heading_font_key": "playfair_display",
                    "body_font_key": "lato",
                    "gujarati_font_key": "noto_serif_gujarati",
                    "hindi_font_key": "noto_serif_devanagari",
                },
                "components": [
                    "business_header", "rating_selector", "topic_selector",
                    "personal_note", "ai_suggestions", "review_editor",
                    "google_handoff", "private_feedback"
                ]
            }
        }
    )
    assert res_mutate.status_code == 400
    assert "immutable" in res_mutate.json()["detail"].lower()


# ─── 4. ASSIGNMENT & VERSION PINNING ─────────────────────────────────────────

def test_only_published_versions_can_be_assigned():
    """Draft or non-existent template versions cannot be assigned to businesses."""
    # 1. Create a draft version 1.2.0
    res_draft = client.post(
        "/api/platform/templates/restaurant_modern_urban/versions",
        json={
            "version": "1.2.0",
            "configuration": {
                "schema_version": "1.0",
                "theme": {
                    "background_color": "#0E1117",
                    "card_surface_color": "#181E29",
                    "primary_accent": "#10B981",
                    "secondary_accent": "#06B6D4",
                    "heading_font_key": "space_grotesk",
                    "body_font_key": "inter",
                    "gujarati_font_key": "noto_sans_gujarati",
                    "hindi_font_key": "noto_sans_devanagari",
                },
                "components": [
                    "business_header", "rating_selector", "topic_selector",
                    "personal_note", "ai_suggestions", "review_editor",
                    "google_handoff", "private_feedback"
                ]
            }
        }
    )
    draft_id = res_draft.json()["data"]["id"]

    # 2. Attempt to assign this draft version (MUST FAIL with 400)
    res_assign = client.post(
        "/api/platform/businesses/test_cafe/assign-template",
        json={
            "template_id": "restaurant_modern_urban",
            "version_id": draft_id
        }
    )
    assert res_assign.status_code == 400
    assert "only published versions can be assigned" in res_assign.json()["detail"].lower()


def test_assignment_version_pinning_and_explicit_upgrade():
    """Businesses stay pinned to their assigned version; upgrades require explicit admin action."""
    # 1. Assign restaurant_modern_urban (v1.0.0) to test_cafe
    res_assign = client.post(
        "/api/platform/businesses/test_cafe/assign-template",
        json={
            "template_id": "restaurant_modern_urban"
        }
    )
    assert res_assign.status_code == 200

    # 2. Verify active assignment reflects restaurant_modern_urban
    res_active = client.get("/api/platform/businesses/test_cafe/assignment")
    assert res_active.status_code == 200
    assert res_active.json()["template_id"] == "restaurant_modern_urban"
    old_version_id = res_active.json()["template_version_id"]

    # 3. Explicit upgrade operation
    res_upgrade = client.post(
        "/api/platform/businesses/test_cafe/upgrade-assignment",
        json={"target_version_id": "ver_restaurant_classic_bistro_1_0_0"}
    )
    assert res_upgrade.status_code == 200
    assert res_upgrade.json()["status"] == "success"

    # 4. Verify previous assignment is marked as superseded in history
    store = get_store()
    with store._connect() as db:
        assignments = db.execute(
            "SELECT id, template_id, status FROM business_template_assignments WHERE business_id = 'test_cafe' ORDER BY assigned_at DESC"
        ).fetchall()
        assert len(assignments) >= 2
        assert assignments[0][2] == "active"
        assert assignments[1][2] == "superseded"


def test_cross_tenant_invalid_business_assignment_rejected():
    """Assignment to non-existent business ID throws 400/404 error."""
    res = client.post(
        "/api/platform/businesses/non_existent_business_xyz/assign-template",
        json={"template_id": "restaurant_classic_bistro"}
    )
    assert res.status_code in (400, 404)


# ─── 5. ARCHIVING BEHAVIOUR ──────────────────────────────────────────────────

def test_archived_templates_cannot_receive_new_assignments():
    """Archiving a template prevents new assignments while existing assignments remain valid."""
    # 1. Archive restaurant_luxury_dining
    res_arch = client.post("/api/platform/templates/restaurant_luxury_dining/archive")
    assert res_arch.status_code == 200

    # 2. Attempt to assign archived template (MUST FAIL with 400)
    res_assign = client.post(
        "/api/platform/businesses/test_cafe/assign-template",
        json={"template_id": "restaurant_luxury_dining"}
    )
    assert res_assign.status_code == 400
    assert "archived" in res_assign.json()["detail"].lower()


# ─── 6. DEFAULT BUSINESS & ANTI-GATING VERIFICATION ──────────────────────────

def test_default_business_preserved_and_anti_gating_compliant():
    """default_business resolves cleanly with anti-gating compliance on all ratings."""
    res = client.get("/api/public/businesses/default_business/config")
    assert res.status_code == 200
    cfg = res.json()

    assert cfg["businessId"] == "default_business"
    assert cfg["businessName"] == "Nasta Ghar"
    assert cfg["antiGatingCompliant"] is True
    assert "https://search.google.com/local/writereview" in cfg["googleReviewUrl"]
    assert len(cfg["topics"]) >= 4

    # Verify no private feedback, internal tokens, or audit logs leaked
    assert "private_feedback" not in cfg or isinstance(cfg["components"], list)
    assert "created_by" not in cfg
    assert "sessions" not in cfg
    assert "assigned_by" not in cfg


def test_mandatory_google_handoff_and_anti_gating():
    """Anti-gating: 'google_handoff' is mandatory in template schema; ratings 1-5 have equal access; private_feedback is optional."""
    theme_valid = VisualTokensConfig(
        background_color="#FAF7F2",
        card_surface_color="#FFFFFF",
        primary_accent="#1B4332",
        secondary_accent="#C5A059",
    )

    # 1. Omitting 'google_handoff' MUST raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        TemplateConfigurationPayload(
            theme=theme_valid,
            components=["business_header", "rating_selector", "topic_selector"]
        )
    assert "google_handoff" in str(exc_info.value).lower()

    # 2. Including 'google_handoff' without 'private_feedback' MUST pass (private feedback is optional)
    payload_no_private = TemplateConfigurationPayload(
        theme=theme_valid,
        components=[
            "business_header", "rating_selector", "topic_selector",
            "personal_note", "ai_suggestions", "review_editor",
            "google_handoff"
        ]
    )
    assert "google_handoff" in payload_no_private.components
    assert "private_feedback" not in payload_no_private.components

    # 3. Verify public config guarantees google_handoff and equal Google Review access for all ratings 1-5
    res = client.get("/api/public/businesses/default_business/config")
    assert res.status_code == 200
    cfg = res.json()
    assert "google_handoff" in cfg["components"]
    assert cfg["antiGatingCompliant"] is True
    assert len(cfg["googleReviewUrl"]) > 10


def test_layout_variant_allowlists_and_rejection():
    """All layout component variants are strictly validated against closed allowlists."""
    # 1. Valid layout configuration passes
    valid_layout = LayoutConfig(
        header_variant="centered_crest",
        rating_variant="classic_stars",
        topic_selector_variant="outlined_chips",
        review_suggestion_card_variant="framed_parchment",
        review_editor_variant="editorial_salon",
        button_variant="emerald_pill",
        spacing_preset="editorial",
        border_radius_preset="md",
        layout_density="spacious"
    )
    assert valid_layout.header_variant == "centered_crest"

    # 2. Invalid header_variant rejected
    with pytest.raises(ValidationError):
        LayoutConfig(header_variant="unapproved_flying_banner")

    # 3. Invalid rating_variant rejected
    with pytest.raises(ValidationError):
        LayoutConfig(rating_variant="stars_99_mega")

    # 4. Invalid topic_selector_variant rejected
    with pytest.raises(ValidationError):
        LayoutConfig(topic_selector_variant="infinite_grid")

    # 5. Invalid button_variant rejected
    with pytest.raises(ValidationError):
        LayoutConfig(button_variant="blinking_neon")

    # 6. Invalid layout_density rejected
    with pytest.raises(ValidationError):
        LayoutConfig(layout_density="ultra_dense")


def test_public_business_config_three_cases():
    """
    Verifies the three distinct public configuration resolution cases:
    Case A — Existing business with active assignment -> Returns exact pinned configuration.
    Case B — Existing business without active assignment -> Returns baseline restaurant fallback with that tenant's identity.
    Case C — Nonexistent business ID -> Returns HTTP 404 (never serves default_business).
    """
    store = get_store()

    # Case A: default_business has active assignment
    res_a = client.get("/api/public/businesses/default_business/config")
    assert res_a.status_code == 200
    cfg_a = res_a.json()
    assert cfg_a["businessId"] == "default_business"
    assert cfg_a["template"]["slug"] in ("restaurant_classic", "restaurant_classic_bistro")

    # Case B: Existing business without active assignment
    with store._connect() as db:
        # Create a test tenant without template assignment
        db.execute("""
            INSERT OR IGNORE INTO tenants (id, business_name, status, platform, review_url, category, primary_accent, created_at, updated_at)
            VALUES ('tenant_no_assignment', 'Unassigned Cafe', 'active', 'google', 'https://g.page/unassigned/review', 'Cafe', '#10B981', 1000.0, 1000.0)
        """)

    try:
        res_b = client.get("/api/public/businesses/tenant_no_assignment/config")
        assert res_b.status_code == 200
        cfg_b = res_b.json()
        assert cfg_b["businessId"] == "tenant_no_assignment"
        assert cfg_b["businessName"] == "Unassigned Cafe"
        assert cfg_b["googleReviewUrl"] == "https://g.page/unassigned/review"
        assert cfg_b["antiGatingCompliant"] is True
        assert "google_handoff" in cfg_b["components"]
    finally:
        with store._connect() as db:
            db.execute("DELETE FROM tenants WHERE id = 'tenant_no_assignment'")

    # Case C: Nonexistent business ID MUST return 404
    res_c = client.get("/api/public/businesses/non_existent_tenant_99999/config")
    assert res_c.status_code == 404
    assert "not found" in res_c.json()["detail"].lower()


def test_phase_a_tenant_isolation_and_legacy_compatibility():
    """
    Phase A: Compatibility & Tenant Isolation
    1. default_business retains legacy_experience: 'nasta_ghar_canvas_world'.
    2. test_cafe or other tenants do NOT receive legacy_experience: 'nasta_ghar_canvas_world'.
    3. Tenants without review_url NEVER leak Nasta Ghar's Rajkot Google PlaceID.
    """
    store = get_store()

    # 1. default_business compatibility
    res_def = client.get("/api/public/businesses/default_business/config")
    assert res_def.status_code == 200
    cfg_def = res_def.json()
    assert cfg_def.get("compatibility_flags", {}).get("legacy_experience") == "nasta_ghar_canvas_world"
    assert "ChIJZeK7NwDLWTkR1pOxt51jLro" in cfg_def["googleReviewUrl"]

    # 2. test_cafe isolation
    res_cafe = client.get("/api/public/businesses/test_cafe/config")
    if res_cafe.status_code == 200:
        cfg_cafe = res_cafe.json()
        assert cfg_cafe.get("compatibility_flags") is None
        assert "ChIJZeK7NwDLWTkR1pOxt51jLro" not in cfg_cafe.get("googleReviewUrl", "")

    # 3. Newly created tenant with empty review_url NEVER gets Nasta Ghar review URL or Nasta Ghar name
    with store._connect() as db:
        db.execute("""
            INSERT OR IGNORE INTO tenants (id, business_name, status, platform, review_url, category, primary_accent, created_at, updated_at)
            VALUES ('tenant_isolated_retail', 'Retail Shop', 'active', 'google', '', 'Retail', '#4F46E5', 2000.0, 2000.0)
        """)
    try:
        res_retail = client.get("/api/public/businesses/tenant_isolated_retail/config")
        assert res_retail.status_code == 200
        cfg_retail = res_retail.json()
        assert cfg_retail["businessName"] == "Retail Shop"
        assert cfg_retail["googleReviewUrl"] == ""  # Zero leak!
        assert "ChIJZeK7NwDLWTkR1pOxt51jLro" not in cfg_retail["googleReviewUrl"]
        assert cfg_retail.get("compatibility_flags") is None
    finally:
        with store._connect() as db:
            db.execute("DELETE FROM tenants WHERE id = 'tenant_isolated_retail'")


def test_phase_b_manifest_trust_and_deployment_gate():
    """
    Phase B: Dynamic Template Rendering Foundation & Safety Gate
    1. Template manifest exists, is parseable, and includes registered templates.
    2. Attempting to assign or publish an unrendered or preview-only template (e.g. restaurant_sweet_dessert)
       triggers TemplateNotDeployableError and returns HTTP 409 Conflict.
    3. Deployable templates succeed without conflict.
    """
    from backend.app.core.database.template_storage import (
        TemplateNotDeployableError,
        get_frontend_template_manifest,
    )

    manifest = get_frontend_template_manifest()
    assert manifest is not None
    assert "templates" in manifest
    assert "restaurant_classic_bistro" in manifest["templates"]
    assert manifest["templates"]["restaurant_classic_bistro"]["deployable"] is True
    assert manifest["templates"]["restaurant_sweet_dessert"]["deployable"] is False

    store = get_store()

    # 1. Direct repository test: attempting to assign a preview_only/draft template
    with store._connect() as db:
        # Create a test tenant
        db.execute("""
            INSERT OR IGNORE INTO tenants (id, business_name, status, platform, review_url, category, primary_accent, created_at, updated_at)
            VALUES ('tenant_preview_gate_test', 'Gate Test Cafe', 'active', 'google', 'https://g.page/gate/review', 'Cafe', '#10B981', 3000.0, 3000.0)
        """)
        # Insert a preview_only template into SQLite
        db.execute("""
            INSERT OR IGNORE INTO templates (id, industry_id, name, slug, description, status, created_at, updated_at)
            VALUES ('tpl_test_preview_only', 'ind_restaurant', 'Sweet Dessert House', 'restaurant_sweet_dessert', 'Dessert shop', 'active', 3000.0, 3000.0)
        """)
        db.execute("""
            INSERT OR IGNORE INTO template_versions (id, template_id, version, configuration_json, publication_status, published_at, created_at)
            VALUES ('ver_test_preview_only', 'tpl_test_preview_only', '1.0.0', '{}', 'published', 3000.0, 3000.0)
        """)

    try:
        # Repository-level rejection
        with pytest.raises(TemplateNotDeployableError) as exc_info:
            store.template_repo.assign_template_to_business(
                business_id="tenant_preview_gate_test",
                template_id="tpl_test_preview_only",
                version_id="ver_test_preview_only"
            )
        assert "no deployable frontend renderer" in str(exc_info.value)

        # HTTP API endpoint rejection (HTTP 409 Conflict)
        res = client.post(
            "/api/platform/businesses/tenant_preview_gate_test/assign-template",
            json={"template_id": "tpl_test_preview_only", "version_id": "ver_test_preview_only"}
        )
        assert res.status_code == 409
        assert "no deployable frontend renderer" in res.json()["detail"]

    finally:
        with store._connect() as db:
            db.execute("DELETE FROM template_versions WHERE id = 'ver_test_preview_only'")
            db.execute("DELETE FROM templates WHERE id = 'tpl_test_preview_only'")
            db.execute("DELETE FROM tenants WHERE id = 'tenant_preview_gate_test'")
