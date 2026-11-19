"""
Automated Test Suite for VRAJA AI Phase A3: Multi-Industry Owner Portal Frontend Architecture.

Verifies:
1. Component structure and dynamic industry configuration hook (useIndustryConfig.js).
2. ProductAReviewSetup.jsx generalization (industry selector, subcategories, touchpoint noun, topic presets).
3. ProductAReviewAnalytics.jsx generalization (dynamic disclaimer noun, season label).
4. ProductAPrivateInbox.jsx generalization (customer noun plural, touchpoint visit indicator).
5. UnifiedClientPortal.jsx generalization (customer feedback description, 5-section invariant).
6. Non-regression of Product B (Digital Card remains completely untouched).
"""

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PORTAL_DIR = REPO_ROOT / "NastaGhar" / "frontend" / "src" / "components" / "portal"
PRODUCT_A_DIR = PORTAL_DIR / "product_a"
DIGITAL_CARD_DIR = REPO_ROOT / "Digital_Card"


def test_use_industry_config_hook_exists():
    """Verify useIndustryConfig hook file exists and implements canonical configuration fetching."""
    hook_file = PORTAL_DIR / "useIndustryConfig.js"
    assert hook_file.exists(), f"useIndustryConfig.js not found at {hook_file}"

    content = hook_file.read_text(encoding="utf-8")
    assert "useIndustryConfig" in content
    assert "/api/businesses/" in content
    assert "/industry-config" in content
    assert "/api/industries" in content
    assert "customer_noun" in content
    assert "touchpoint_noun" in content
    assert "disclaimer_noun" in content


def test_product_a_review_setup_industry_controls():
    """Verify ProductAReviewSetup includes industry selector, subcategories, and load defaults."""
    setup_file = PRODUCT_A_DIR / "ProductAReviewSetup.jsx"
    assert setup_file.exists(), f"ProductAReviewSetup.jsx not found at {setup_file}"

    content = setup_file.read_text(encoding="utf-8")
    assert "useIndustryConfig" in content
    assert "availableIndustries" in content
    assert "industry_id" in content
    assert "Load Industry Defaults" in content
    assert "terminology.touchpoint_noun" in content


def test_product_a_review_analytics_dynamic_terminology():
    """Verify ProductAReviewAnalytics uses dynamic disclaimer noun and generalized seasonal label."""
    analytics_file = PRODUCT_A_DIR / "ProductAReviewAnalytics.jsx"
    assert analytics_file.exists(), f"ProductAReviewAnalytics.jsx not found at {analytics_file}"

    content = analytics_file.read_text(encoding="utf-8")
    assert "useIndustryConfig" in content
    assert "terminology.disclaimer_noun" in content
    assert "Review-system usage measures digital customer interactions" in content
    assert "Seasonal Analysis" in content


def test_product_a_private_inbox_dynamic_terminology():
    """Verify ProductAPrivateInbox uses dynamic customer noun and generalized touchpoint indicator."""
    inbox_file = PRODUCT_A_DIR / "ProductAPrivateInbox.jsx"
    assert inbox_file.exists(), f"ProductAPrivateInbox.jsx not found at {inbox_file}"

    content = inbox_file.read_text(encoding="utf-8")
    assert "useIndustryConfig" in content
    assert "terminology.customer_noun_plural" in content
    assert "General Visit" in content


def test_unified_client_portal_generalization_and_five_section_standard():
    """Verify UnifiedClientPortal uses generalized wording and preserves 5-section navigation."""
    portal_file = PORTAL_DIR / "UnifiedClientPortal.jsx"
    assert portal_file.exists(), f"UnifiedClientPortal.jsx not found at {portal_file}"

    content = portal_file.read_text(encoding="utf-8")
    # Generalization check: "Proactive customer feedback capture"
    assert "Proactive customer feedback capture, AI-assisted review drafting" in content

    # 5-section Owner Portal tabs preserved
    expected_tabs = [
        "overview",
        "reviews-setup",
        "reviews-analytics",
        "reviews-inbox",
        "settings",
    ]
    for tab in expected_tabs:
        assert tab in content


def test_digital_card_product_b_untouched():
    """Verify Digital Card directory has no phase A2/A3 modifications."""
    assert DIGITAL_CARD_DIR.exists()
    # Digital Card frontend components should not contain useIndustryConfig
    dc_frontend = DIGITAL_CARD_DIR / "frontend" / "src"
    for js_file in dc_frontend.glob("**/*.jsx"):
        content = js_file.read_text(encoding="utf-8")
        assert "useIndustryConfig" not in content
