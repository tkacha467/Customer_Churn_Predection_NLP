"""
VRAJA AI — Security Shield Platform API Endpoints.
Provides platform administrators with real-time security telemetry, incident management,
audit event inspection, outbox controls, synthetic test alert verification, and database integrity checks.
All endpoints strictly require active platform administrator authorization.
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.app.core.auth.auth import (
    TenantContext,
    require_platform_admin,
)
from backend.app.api.routes import get_client_ip
from backend.app.api.service import review_service
from backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)
from backend.app.core.security.alert_mailer import (
    alert_mailer,
    DEFAULT_ALERT_EMAIL,
)
from backend.app.core.security.code_integrity import verify_database_schema_integrity


security_router = APIRouter(prefix="/platform/security-shield", tags=["security_shield"])


class UpdateIncidentRequest(BaseModel):
    status: Optional[str] = None
    resolution_note: Optional[str] = None


class TestAlertRequest(BaseModel):
    recipient: Optional[str] = None


@security_router.get("/overview")
async def get_security_overview(admin: TenantContext = Depends(require_platform_admin)):
    """High-level security telemetry, counts, and dispatcher status."""
    return security_shield.get_overview_metrics()


@security_router.get("/incidents")
async def list_security_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: TenantContext = Depends(require_platform_admin),
):
    """List aggregated security incidents with status/severity/tenant filtering."""
    if status == "all":
        status = None
    if severity == "all":
        severity = None

    incidents, total = security_shield.list_incidents(
        status=status,
        severity=severity,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return {"incidents": incidents, "total_count": total}


@security_router.get("/events")
async def list_security_events(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    admin: TenantContext = Depends(require_platform_admin),
):
    """List raw security audit events with pagination and filtering."""
    if severity == "all":
        severity = None

    events, total = security_shield.list_events_paginated(
        limit=limit,
        offset=offset,
        severity=severity,
        tenant_id=tenant_id,
        event_type=event_type,
    )
    return {
        "events": events,
        "total_count": total,
        "target_email": DEFAULT_ALERT_EMAIL,
    }


@security_router.get("/outbox")
async def list_security_outbox(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: TenantContext = Depends(require_platform_admin),
):
    """List queued, sent, and failed security email alert outbox records."""
    if status == "all":
        status = None

    items, total = security_shield._store.list_outbox(
        status=status,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total_count": total}


@security_router.patch("/incidents/{incident_id}")
async def update_security_incident(
    incident_id: str,
    payload: UpdateIncidentRequest,
    admin: TenantContext = Depends(require_platform_admin),
):
    """Acknowledge or resolve an incident with optional resolution note."""
    existing = security_shield.get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")

    ack_by = admin.email if payload.status in ("investigating", "acknowledged") else None
    res_by = admin.email if payload.status == "resolved" else None

    # If resolving directly and not yet acknowledged, record acknowledged_by as well
    if payload.status == "resolved" and not existing.get("acknowledged_by"):
        ack_by = admin.email

    security_shield.update_incident(
        incident_id=incident_id,
        status=payload.status,
        acknowledged_by=ack_by,
        resolution_note=payload.resolution_note,
        resolved_by=res_by,
    )

    # Emit audit event for incident mutation
    emit_security_event(
        event_type="SECURITY_INCIDENT_MUTATED",
        severity=SecuritySeverity.LOW if hasattr(SecuritySeverity, "LOW") else "LOW",
        actor_id=admin.user_id,
        tenant_id=existing.get("affected_tenant"),
        details={
            "incident_id": incident_id,
            "status": payload.status,
            "resolution_note": payload.resolution_note,
            "mutated_by": admin.email,
        },
    )

    fresh = security_shield.get_incident(incident_id)
    return fresh or existing


@security_router.post("/outbox/retry")
async def retry_security_outbox(
    request: Request,
    admin: TenantContext = Depends(require_platform_admin),
):
    """Flush pending/failed alert outbox records with rate limiting."""
    client_ip = get_client_ip(request)
    if not review_service.check_rate_limit(f"sec_outbox_retry:{client_ip}", max_per_minute=5):
        raise HTTPException(status_code=429, detail="Too many outbox retry requests. Please wait.")

    res = alert_mailer.process_outbox(security_shield._store)
    return {"status": "success", "result": res}


@security_router.post("/export")
async def export_security_events(
    request: Request,
    admin: TenantContext = Depends(require_platform_admin),
):
    """Export security audit events as downloadable JSON with rate limiting."""
    client_ip = get_client_ip(request)
    if not review_service.check_rate_limit(f"sec_export:{client_ip}", max_per_minute=5):
        raise HTTPException(status_code=429, detail="Export rate limit exceeded. Please try again later.")

    events, total = security_shield.list_events_paginated(limit=10000)
    return JSONResponse(
        content={
            "events": events,
            "total_count": total,
            "exported_at": time.time(),
            "exported_by": admin.email,
        }
    )


@security_router.post("/test-alert")
async def trigger_synthetic_test_alert(
    request: Request,
    payload: Optional[TestAlertRequest] = Body(None),
    admin: TenantContext = Depends(require_platform_admin),
):
    """
    Triggers an authorized synthetic security test alert to the verified target recipient.
    Strictly rate limited to max 3 requests per minute.
    Recipient cannot be overridden to unauthorized addresses.
    """
    client_ip = get_client_ip(request)
    if not review_service.check_rate_limit(f"sec_test_alert:{client_ip}", max_per_minute=3):
        raise HTTPException(status_code=429, detail="Too many test alert requests. Maximum 3 requests per minute allowed.")

    if payload and payload.recipient:
        if payload.recipient.strip() != DEFAULT_ALERT_EMAIL:
            raise HTTPException(
                status_code=400,
                detail=f"Unauthorized recipient '{payload.recipient}'. Must be {DEFAULT_ALERT_EMAIL}."
            )

    result = alert_mailer.send_synthetic_test_alert(
        initiated_by=admin.email,
        store=security_shield._store,
        recipient=payload.recipient if (payload and payload.recipient) else None,
    )
    return result


@security_router.get("/test-alert/{test_id}")
async def get_test_alert_status(
    test_id: str,
    admin: TenantContext = Depends(require_platform_admin),
):
    """Retrieve synthetic test alert delivery status and details."""
    rec = security_shield._store.get_synthetic_test(test_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Synthetic test not found")
    return rec


@security_router.get("/integrity")
async def check_database_integrity(
    admin: TenantContext = Depends(require_platform_admin),
):
    """Audit database schema hash and structural integrity."""
    db_path = Path(os.getenv("REVIEW_DB_PATH", "Project_Files/Data/nasta-ghar/reviews.sqlite3"))
    is_healthy, quick_status, schema_hash = verify_database_schema_integrity(db_path)
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": {
            "is_healthy": is_healthy,
            "structural_check": quick_status,
            "schema_hash": schema_hash,
        },
        "target_alert_recipient": DEFAULT_ALERT_EMAIL,
    }
