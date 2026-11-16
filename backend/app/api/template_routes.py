"""
FastAPI Routes for Product A Dynamic Restaurant Template Configuration Foundation.
Provides administrative template versioning, assignment, explicit upgrades,
and sanitized public configuration resolution.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from Backend.app.core.auth.auth import (
    TenantContext,
    get_store,
    require_auth_context,
    require_platform_admin,
)
from Backend.app.api.template_schemas import (
    AssignTemplateRequest,
    CreateDraftVersionRequest,
    IndustryResponse,
    PublicBusinessConfigResponse,
    TemplateResponse,
    TemplateVersionResponse,
    UpdateBusinessConfigRequest,
    UpdateDraftVersionRequest,
    UpgradeAssignmentRequest,
)

template_router = APIRouter()


# ─── 1. PUBLIC ENDPOINTS (Fast, Sanitized, Version-Aware) ───────────────────
@template_router.get("/public/businesses/{business_id}/config", response_model=PublicBusinessConfigResponse)
async def get_public_business_config(business_id: str):
    """
    Returns the complete, version-aware sanitized customer review configuration.
    Includes exact pinned template version, theme colors, layout presets, and review topics.
    Zero-fabrication and Google anti-gating compliant (equal Google Review access across all ratings).
    Never exposes internal draft versions, audit logs, or other tenants' data.
    """
    store = get_store()
    try:
        config = store.template_repo.get_public_business_config(business_id)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load business configuration: {str(e)}")


# ─── 2. PLATFORM ADMIN TEMPLATE CATALOG ENDPOINTS ────────────────────────────
@template_router.get("/platform/industries", response_model=List[IndustryResponse])
async def list_industries():
    """List all available platform industries."""
    store = get_store()
    return store.template_repo.list_industries()


@template_router.get("/platform/templates", response_model=List[TemplateResponse])
async def list_templates(
    industry: Optional[str] = Query(None, description="Optional industry slug filter (e.g. restaurant)")
):
    """List active templates with their active published configurations and industry metadata."""
    store = get_store()
    return store.template_repo.list_templates(industry_slug=industry)


@template_router.get("/platform/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """Get single template definition by its ID."""
    store = get_store()
    tpl = store.template_repo.get_template_by_id(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return tpl


@template_router.post("/platform/templates/{template_id}/archive")
async def archive_template(
    template_id: str,
    admin: TenantContext = Depends(require_platform_admin)
):
    """Archive a template. Archived templates cannot receive new assignments."""
    store = get_store()
    try:
        res = store.template_repo.archive_template(template_id)
        return {"status": "success", "message": f"Template '{template_id}' archived successfully", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to archive template: {str(e)}")


# ─── 3. TEMPLATE VERSION MANAGEMENT ENDPOINTS ───────────────────────────────
@template_router.get("/platform/templates/{template_id}/versions", response_model=List[TemplateVersionResponse])
async def list_template_versions(
    template_id: str,
    admin: TenantContext = Depends(require_platform_admin)
):
    """List all versions (draft, published, archived) for a specific template."""
    store = get_store()
    tpl = store.template_repo.get_template_by_id(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return store.template_repo.list_template_versions(template_id)


@template_router.post("/platform/templates/{template_id}/versions", response_model=Dict[str, Any])
async def create_template_draft_version(
    template_id: str,
    req: CreateDraftVersionRequest,
    admin: TenantContext = Depends(require_platform_admin)
):
    """
    Creates a new editable draft version for a template.
    Strictly validates configuration payload using Pydantic schema.
    """
    store = get_store()
    try:
        config_json = req.configuration.model_dump_json()
        res = store.template_repo.create_draft_version(
            template_id=template_id,
            version=req.version,
            configuration_json=config_json,
            created_by=admin.email
        )
        return {"status": "success", "message": f"Draft version '{req.version}' created", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create draft version: {str(e)}")


@template_router.put("/platform/templates/{template_id}/versions/{version_id}")
async def update_template_draft_version(
    template_id: str,
    version_id: str,
    req: UpdateDraftVersionRequest,
    admin: TenantContext = Depends(require_platform_admin)
):
    """
    Updates an existing draft version.
    Throws 400 Bad Request if the version is published (enforcing immutability).
    """
    store = get_store()
    try:
        config_json = req.configuration.model_dump_json()
        res = store.template_repo.update_draft_version(
            version_id=version_id,
            configuration_json=config_json
        )
        return {"status": "success", "message": f"Draft version '{version_id}' updated", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update draft version: {str(e)}")


@template_router.post("/platform/templates/{template_id}/versions/{version_id}/publish")
async def publish_template_version(
    template_id: str,
    version_id: str,
    admin: TenantContext = Depends(require_platform_admin)
):
    """
    Publishes a draft version, making it immutable and available for assignment.
    Requires platform administrator privileges.
    """
    store = get_store()
    try:
        res = store.template_repo.publish_version(
            version_id=version_id,
            published_by=admin.email
        )
        return {"status": "success", "message": f"Version '{version_id}' published successfully", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish version: {str(e)}")


# ─── 4. BUSINESS ASSIGNMENT & VERSION PINNING ENDPOINTS ──────────────────────
@template_router.get("/platform/businesses/{business_id}/assignment")
async def get_business_assignment(
    business_id: str,
    admin: TenantContext = Depends(require_platform_admin)
):
    """Get the active template assignment for a specific business."""
    store = get_store()
    assignment = store.template_repo.get_active_business_assignment(business_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"No active template assignment found for business '{business_id}'")
    return assignment


@template_router.post("/platform/businesses/{business_id}/assign-template")
async def assign_template_to_business(
    business_id: str,
    req: AssignTemplateRequest,
    admin: TenantContext = Depends(require_platform_admin)
):
    """
    Assign a specific template (and exact published version) to a business.
    Exclusive to VRAJA Platform Administrators. Rejects draft or archived assignments.
    """
    store = get_store()
    try:
        result = store.template_repo.assign_template_to_business(
            business_id=business_id,
            template_id=req.template_id,
            version_id=req.version_id,
            assigned_by=admin.email
        )
        return {"status": "success", "message": f"Template assigned successfully to '{business_id}'", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign template: {str(e)}")


@template_router.post("/platform/businesses/{business_id}/upgrade-assignment")
async def upgrade_business_assignment(
    business_id: str,
    req: UpgradeAssignmentRequest,
    admin: TenantContext = Depends(require_platform_admin)
):
    """
    Explicit administrator operation to upgrade a business's pinned version.
    Guarantees businesses never silently auto-upgrade when templates are modified.
    """
    store = get_store()
    try:
        result = store.template_repo.upgrade_business_assignment(
            business_id=business_id,
            target_version_id=req.target_version_id,
            upgraded_by=admin.email
        )
        return {"status": "success", "message": f"Assignment upgraded for '{business_id}'", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upgrade assignment: {str(e)}")


@template_router.put("/platform/businesses/{business_id}/template-config")
async def update_business_template_config(
    business_id: str,
    req: UpdateBusinessConfigRequest,
    admin: TenantContext = Depends(require_platform_admin)
):
    """
    Update tenant-specific styling, branding overrides, custom topics, or review link.
    """
    store = get_store()
    try:
        updated = store.template_repo.update_business_config(
            business_id=business_id,
            logo_url=req.logo_url,
            cover_image_url=req.cover_image_url,
            primary_accent=req.primary_accent,
            custom_topics=req.custom_topics,
            localized_content=req.localized_content,
            google_review_url=req.google_review_url
        )
        return {"status": "success", "data": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template configuration: {str(e)}")
