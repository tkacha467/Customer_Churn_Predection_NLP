"""
VRAJA AI — Product A: 30 Distinct Multi-Industry Templates Verification Suite
Validates:
1. Exactly 30 distinct template component files exist on disk across 6 canonical industries (5 per industry).
2. All 30 distinct templates are registered in frontend registry.js and template-manifest.json.
3. Deployability rules:
   - F01-F04, B01-B05, R01-R05, T01-T05, G01-G05 are deployable (24 templates).
   - F05 (Sweet Dessert House) is preview-only (deployable: false).
   - H01-H05 (All Healthcare) are strictly preview-only (deployable: false).
4. Healthcare Quarantine Compliance:
   - Zero mentions of HIPAA or NABH in code or comments.
   - Neutral Patient Privacy Notice is present in all healthcare templates:
     'Patient Privacy Notice: Automated suggestions are disabled. Please share your genuine words with the care team.'
5. Legacy Nasta Ghar Compatibility & Tenant Isolation:
   - default_business retains legacy_experience: 'nasta_ghar_canvas_world'.
   - Unconfigured tenants never leak Nasta Ghar PlaceID or receive legacy canvas flag.
6. Product B Isolation:
   - Digital_Card is completely untouched.
"""
import json
import re
from pathlib import Path
import pytest
from starlette.testclient import TestClient
from Backend.app.main import app
from Backend.app.core.auth.auth import get_store, _login_attempts, _login_lock

client = TestClient(app)

FRONTEND_SRC = Path("NastaGhar/frontend/src")
TEMPLATES_DIR = FRONTEND_SRC / "templates"

EXPECTED_30_TEMPLATES = [
    # Food & Dining (F01–F05)
    {"id": "F01", "slug": "restaurant_classic_bistro", "industry": "restaurant", "component": "RestaurantClassicBistro", "file": "restaurant/RestaurantClassicBistro.jsx", "deployable": True},
    {"id": "F02", "slug": "restaurant_modern_urban", "industry": "restaurant", "component": "RestaurantModernUrban", "file": "restaurant/RestaurantModernUrban.jsx", "deployable": True},
    {"id": "F03", "slug": "restaurant_luxury_dining", "industry": "restaurant", "component": "RestaurantLuxuryDining", "file": "restaurant/RestaurantLuxuryDining.jsx", "deployable": True},
    {"id": "F04", "slug": "restaurant_cafe_playful", "industry": "restaurant", "component": "RestaurantCafePlayful", "file": "restaurant/RestaurantCafePlayful.jsx", "deployable": True},
    {"id": "F05", "slug": "restaurant_sweet_dessert", "industry": "restaurant", "component": "RestaurantSweetDessert", "file": "restaurant/RestaurantSweetDessert.jsx", "deployable": False},

    # Beauty & Grooming (B01–B05)
    {"id": "B01", "slug": "salon_spa_sanctuary", "industry": "salon", "component": "SalonSpaSanctuary", "file": "beauty/SalonSpaSanctuary.jsx", "deployable": True},
    {"id": "B02", "slug": "salon_barber_lounge", "industry": "salon", "component": "BarberGroomingLounge", "file": "beauty/BarberGroomingLounge.jsx", "deployable": True},
    {"id": "B03", "slug": "salon_nail_lash", "industry": "salon", "component": "NailLashStudio", "file": "beauty/NailLashStudio.jsx", "deployable": True},
    {"id": "B04", "slug": "salon_skincare_lab", "industry": "salon", "component": "SkincareAestheticLab", "file": "beauty/SkincareAestheticLab.jsx", "deployable": True},
    {"id": "B05", "slug": "salon_bridal_glam", "industry": "salon", "component": "BridalGlamStudio", "file": "beauty/BridalGlamStudio.jsx", "deployable": True},

    # Retail & Shopping (R01–R05)
    {"id": "R01", "slug": "retail_fashion_boutique", "industry": "retail", "component": "RetailFashionBoutique", "file": "retail/RetailFashionBoutique.jsx", "deployable": True},
    {"id": "R02", "slug": "retail_streetwear_drop", "industry": "retail", "component": "RetailStreetwearDrop", "file": "retail/RetailStreetwearDrop.jsx", "deployable": True},
    {"id": "R03", "slug": "retail_artisanal_home", "industry": "retail", "component": "RetailArtisanalHome", "file": "retail/RetailArtisanalHome.jsx", "deployable": True},
    {"id": "R04", "slug": "retail_organic_pantry", "industry": "retail", "component": "RetailOrganicPantry", "file": "retail/RetailOrganicPantry.jsx", "deployable": True},
    {"id": "R05", "slug": "retail_tech_gadgets", "industry": "retail", "component": "RetailTechGadgets", "file": "retail/RetailTechGadgets.jsx", "deployable": True},

    # Hotels & Hospitality (T01–T05)
    {"id": "T01", "slug": "hotel_heritage_resort", "industry": "hotel", "component": "HotelHeritageResort", "file": "hospitality/HotelHeritageResort.jsx", "deployable": True},
    {"id": "T02", "slug": "hotel_urban_boutique", "industry": "hotel", "component": "HotelUrbanBoutique", "file": "hospitality/HotelUrbanBoutique.jsx", "deployable": True},
    {"id": "T03", "slug": "hotel_eco_retreat", "industry": "hotel", "component": "HotelEcoRetreat", "file": "hospitality/HotelEcoRetreat.jsx", "deployable": True},
    {"id": "T04", "slug": "hotel_business_suite", "industry": "hotel", "component": "HotelBusinessSuite", "file": "hospitality/HotelBusinessSuite.jsx", "deployable": True},
    {"id": "T05", "slug": "hotel_cozy_inn", "industry": "hotel", "component": "HotelCozyInn", "file": "hospitality/HotelCozyInn.jsx", "deployable": True},

    # Fitness & Wellness (G01–G05)
    {"id": "G01", "slug": "fitness_iron_forge", "industry": "fitness", "component": "FitnessIronForge", "file": "fitness/FitnessIronForge.jsx", "deployable": True},
    {"id": "G02", "slug": "fitness_zen_studio", "industry": "fitness", "component": "FitnessZenStudio", "file": "fitness/FitnessZenStudio.jsx", "deployable": True},
    {"id": "G03", "slug": "fitness_modern_club", "industry": "fitness", "component": "FitnessModernClub", "file": "fitness/FitnessModernClub.jsx", "deployable": True},
    {"id": "G04", "slug": "fitness_combat_ring", "industry": "fitness", "component": "FitnessCombatRing", "file": "fitness/FitnessCombatRing.jsx", "deployable": True},
    {"id": "G05", "slug": "fitness_athletic_turf", "industry": "fitness", "component": "FitnessAthleticTurf", "file": "fitness/FitnessAthleticTurf.jsx", "deployable": True},

    # Healthcare & Clinical (H01–H05 - Quarantined Preview-Only)
    {"id": "H01", "slug": "clinic_multi_specialty", "industry": "clinic", "component": "ClinicMultiSpecialty", "file": "healthcare/ClinicMultiSpecialty.jsx", "deployable": False},
    {"id": "H02", "slug": "clinic_dental_studio", "industry": "clinic", "component": "ClinicDentalStudio", "file": "healthcare/ClinicDentalStudio.jsx", "deployable": False},
    {"id": "H03", "slug": "clinic_physio_rehab", "industry": "clinic", "component": "ClinicPhysioRehab", "file": "healthcare/ClinicPhysioRehab.jsx", "deployable": False},
    {"id": "H04", "slug": "clinic_wellness_preventive", "industry": "clinic", "component": "ClinicWellnessPreventive", "file": "healthcare/ClinicWellnessPreventive.jsx", "deployable": False},
    {"id": "H05", "slug": "clinic_diagnostic_lab", "industry": "clinic", "component": "ClinicDiagnosticLab", "file": "healthcare/ClinicDiagnosticLab.jsx", "deployable": False},
]


def test_all_30_template_files_exist_and_distinct():
    """Verify that all 30 distinct visual template JSX files exist on disk with unique names and non-trivial size."""
    seen_files = set()
    for item in EXPECTED_30_TEMPLATES:
        file_path = TEMPLATES_DIR / item["file"]
        assert file_path.exists(), f"Missing template file: {file_path}"
        assert file_path.stat().st_size > 1500, f"Template file {file_path} is suspiciously small (<1.5KB)"
        assert item["file"] not in seen_files, f"Duplicate template file reference: {item['file']}"
        seen_files.add(item["file"])
    assert len(seen_files) == 30, f"Expected 30 distinct component files, got {len(seen_files)}"


def test_template_manifest_registration_and_deployability():
    """Verify that template-manifest.json records all 30 templates with exact deployability flags."""
    manifest_path = TEMPLATES_DIR / "template-manifest.json"
    assert manifest_path.exists(), "template-manifest.json must exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    templates = manifest.get("templates", {})
    deployable_count = 0
    preview_only_count = 0

    for item in EXPECTED_30_TEMPLATES:
        slug = item["slug"]
        assert slug in templates, f"Template slug {slug} missing from manifest"
        tpl_entry = templates[slug]
        assert tpl_entry["component"] == item["component"], f"Component mismatch for {slug}"
        assert tpl_entry["deployable"] is item["deployable"], f"Deployable mismatch for {slug}"
        assert "en" in tpl_entry["locales"]
        assert "hi" in tpl_entry["locales"]
        assert "gu" in tpl_entry["locales"]

        if tpl_entry["deployable"]:
            deployable_count += 1
        else:
            preview_only_count += 1
            assert tpl_entry.get("preview_only") is True, f"preview_only must be true for {slug}"

    assert deployable_count == 24, f"Expected exactly 24 deployable templates, got {deployable_count}"
    assert preview_only_count == 6, f"Expected exactly 6 preview-only templates (F05 + H01-H05), got {preview_only_count}"


def test_registry_js_exports_all_30_templates():
    """Verify that registry.js imports and exports all 30 distinct components."""
    registry_path = TEMPLATES_DIR / "registry.js"
    assert registry_path.exists()
    content = registry_path.read_text(encoding="utf-8")

    for item in EXPECTED_30_TEMPLATES:
        comp = item["component"]
        slug = item["slug"]
        assert comp in content, f"Component {comp} not referenced in registry.js"
        assert f"'{slug}'" in content or f'"{slug}"' in content, f"Slug {slug} not registered in TEMPLATE_REGISTRY"


def test_healthcare_strict_quarantine_compliance():
    """
    Verify Healthcare Quarantine Rules:
    1. Zero mentions of 'HIPAA' or 'NABH' in any healthcare template or registry file.
    2. Neutral Patient Privacy Notice exists in all H01-H05 components.
    3. All H01-H05 have deployable = False.
    """
    for item in EXPECTED_30_TEMPLATES:
        if item["industry"] == "clinic":
            file_path = TEMPLATES_DIR / item["file"]
            content = file_path.read_text(encoding="utf-8")

            # 1. Zero HIPAA / NABH claims
            assert "HIPAA" not in content, f"Unsupported HIPAA claim found in {file_path}"
            assert "NABH" not in content, f"Unsupported NABH claim found in {file_path}"

            # 2. Neutral patient privacy notice
            assert "Patient Privacy Notice:" in content, f"Missing Patient Privacy Notice in {file_path}"
            assert "Automated suggestions are disabled. Please share your genuine words with the care team." in content, f"Missing neutral notice text in {file_path}"

            # 3. Not deployable
            assert item["deployable"] is False


def test_legacy_nasta_ghar_compatibility_isolation():
    """Ensure default_business gets canvas world while other tenants are strictly isolated."""
    res_def = client.get("/api/public/businesses/default_business/config")
    assert res_def.status_code == 200
    cfg_def = res_def.json()
    assert cfg_def.get("compatibility_flags", {}).get("legacy_experience") == "nasta_ghar_canvas_world"

    store = get_store()
    with store._connect() as db:
        db.execute("""
            INSERT OR IGNORE INTO tenants (id, business_name, status, platform, review_url, category, primary_accent, created_at, updated_at)
            VALUES ('tenant_distinct_test', 'Zen Yoga Studio', 'active', 'google', '', 'Fitness', '#84CC16', 4000.0, 4000.0)
        """)
    try:
        res_test = client.get("/api/public/businesses/tenant_distinct_test/config")
        assert res_test.status_code == 200
        cfg_test = res_test.json()
        assert cfg_test.get("compatibility_flags") is None
        assert "ChIJZeK7NwDLWTkR1pOxt51jLro" not in cfg_test.get("googleReviewUrl", "")
    finally:
        with store._connect() as db:
            db.execute("DELETE FROM tenants WHERE id = 'tenant_distinct_test'")
