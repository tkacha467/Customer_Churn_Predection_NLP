"""
Focused Automated Test Suite for VRAJA AI Phase 3.2:
Unified Client Portal Visual Shell, Sidebar & Header Entitlements,
Route Synchronization, and Responsive Navigation Contracts.
"""

import pytest
from pathlib import Path


def test_01_portal_shell_files_exist_and_not_empty():
    """Verify that all Phase 3.2 shell component files exist and have substantial content."""
    base_dir = Path("NastaGhar/frontend/src/components/portal")
    sidebar_file = base_dir / "PortalSidebar.jsx"
    header_file = base_dir / "PortalHeader.jsx"
    shell_file = base_dir / "UnifiedClientPortal.jsx"
    css_file = base_dir / "UnifiedPortal.css"

    for f in [sidebar_file, header_file, shell_file, css_file]:
        assert f.exists(), f"File {f} is missing"
        assert f.stat().st_size > 500, f"File {f} is too small"


def test_02_portal_css_contains_corporate_design_tokens():
    """Verify that UnifiedPortal.css includes all required corporate palette tokens."""
    css_content = Path("NastaGhar/frontend/src/components/portal/UnifiedPortal.css").read_text()

    assert "--vraja-canvas: #F5F3EC" in css_content
    assert "--vraja-deep-emerald: #174D3A" in css_content
    assert "--vraja-muted-gold: #C6A66B" in css_content
    assert "--vraja-forest-charcoal: #26352D" in css_content
    assert "--vraja-pure-white: #FFFFFF" in css_content
    assert "--vraja-soft-sage: #DCE5DD" in css_content


def test_03_sidebar_enforces_entitlement_conditional_rendering():
    """Verify PortalSidebar conditionally renders Product A and Product B groups based on entitlements."""
    sidebar_code = Path("NastaGhar/frontend/src/components/portal/PortalSidebar.jsx").read_text()

    # Product A is guarded by hasEntitlement('review_manager')
    assert "hasEntitlement('review_manager')" in sidebar_code
    assert "GOOGLE REVIEW MANAGER" in sidebar_code
    assert "reviews-setup" in sidebar_code
    assert "reviews-analytics" in sidebar_code
    assert "reviews-inbox" in sidebar_code

    # Product B is guarded by hasEntitlement('digital_card')
    assert "hasEntitlement('digital_card')" in sidebar_code
    assert "DIGITAL BUSINESS CARD" in sidebar_code
    assert "card-editor" in sidebar_code
    assert "card-links" in sidebar_code
    assert "card-publish" in sidebar_code

    # Shared sections are always available
    assert "Shared Profile & Logo" in sidebar_code
    assert "Settings & Security" in sidebar_code


def test_04_header_quick_previews_enforce_entitlements():
    """Verify PortalHeader renders preview buttons strictly when entitled."""
    header_code = Path("NastaGhar/frontend/src/components/portal/PortalHeader.jsx").read_text()

    assert "hasEntitlement('review_manager')" in header_code
    assert "Preview Review Flow" in header_code

    assert "hasEntitlement('digital_card')" in header_code
    assert "Preview Digital Card" in header_code

    # Header breadcrumbs and role badge
    assert "vraja-portal-breadcrumbs" in header_code
    assert "vraja-header-role-pill" in header_code


def test_05_portal_shell_handles_route_synchronization_and_guards():
    """Verify UnifiedClientPortal synchronizes with URL query params and guards unauthorized routes."""
    shell_code = Path("NastaGhar/frontend/src/components/portal/UnifiedClientPortal.jsx").read_text()

    assert "window.location.search" in shell_code
    assert "window.history.pushState" in shell_code
    assert "popstate" in shell_code

    # Entitlement route guard
    assert "productATabs.includes(activeTab) && !hasEntitlement('review_manager')" in shell_code
    assert "productBTabs.includes(activeTab) && !hasEntitlement('digital_card')" in shell_code

    # Zero entitlements state
    assert "entitlements.length === 0" in shell_code
    assert "No Active Product Modules" in shell_code


def test_06_responsive_css_breakpoints_present():
    """Verify UnifiedPortal.css has responsive drawer and mobile media queries."""
    css_content = Path("NastaGhar/frontend/src/components/portal/UnifiedPortal.css").read_text()

    assert "@media (max-width: 1024px)" in css_content
    assert "@media (max-width: 768px)" in css_content
    assert ".vraja-portal-drawer-overlay" in css_content
    assert "overflow-x: hidden" in css_content
