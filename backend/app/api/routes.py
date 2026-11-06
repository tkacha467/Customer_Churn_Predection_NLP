"""
FastAPI Routes for ChurnLens AI Hospitality & Review Platform.
Multi-tenant identity, authentication, authorization, and review assistance.
"""

import os
import time
import uuid
import hmac
import hashlib
import re
from fastapi import APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.document_storage import (
    DocumentStorageService,
    get_document_storage,
    MAX_DOCUMENT_SIZE_BYTES,
    sanitize_filename,
)
from Backend.app.api.svg_sanitizer import sanitize_svg
from Backend.app.core.entitlements.entitlements import (
    check_tenant_entitlement,
    ENTITLEMENT_REVIEW_MANAGER,
    ENTITLEMENT_DIGITAL_CARD,
)

BUSINESS_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")

def validate_business_id(business_id: str) -> str:
    if not business_id or not BUSINESS_ID_REGEX.match(business_id):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid business identifier: '{business_id}'. Must be alphanumeric, underscores, or hyphens (1-100 characters)."
        )
    return business_id

from Backend.app.schemas import (
    ReviewIdeasRequest,
    ReviewIdeasResponse,
    ReviewGenerateRequest,
    ReviewGenerateResponse,
    ReviewValidateRequest,
    ReviewValidateResponse,
    BusinessReviewLinkResponse,
    BusinessConfigUpdateRequest,
    ReviewSessionCreateRequest,
    ReviewSessionResponse,
    AnalyticsEventRequest,
    ManagerReplyRequest,
    ManagerReplyResponse,
    PrivateFeedbackRequest,
    PrivateFeedbackResponse,
    OwnerLoginRequest,
    AuthSessionResponse,
    UserResponse,
    TenantInfo,
    SwitchTenantRequest,
    TenantOnboardingRequest,
    TenantOnboardingResponse,
    TenantStatusUpdateRequest,
    TenantEntitlementsUpdateRequest,
    ALLOWED_ANALYTICS_EVENTS,
    BusinessProfileResponse,
    BusinessProfileUpdateRequest,
    DocumentMetadataResponse,
    DocumentUpdateRequest,
    PublicDigitalCardResponse,
    PublicDocumentItem,
)
from Backend.app.api.service import review_service
from Backend.app.core.tenants.google_reviews import google_review_manager
from Backend.app.core.auth.auth import (
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    TenantContext,
    check_login_rate_limit,
    generate_session_token,
    hash_token,
    hash_password,
    verify_password,
    is_cookie_secure,
    get_store,
    require_auth_context,
    require_tenant_access,
    require_platform_admin,
    require_owner,
)

router = APIRouter()

def get_client_ip(request: Request) -> str:
    """
    Safely determine the client IP address.
    If TRUSTED_PROXIES is configured in the environment (comma-separated IP list or '*'),
    and the direct peer IP is in that trusted list, the X-Forwarded-For header is inspected.
    Otherwise, only the direct peer IP from request.client is returned to prevent header spoofing.
    """
    peer_ip = request.client.host if request.client else "127.0.0.1"
    trusted_proxies_env = os.environ.get("TRUSTED_PROXIES", "").strip()
    if not trusted_proxies_env:
        return peer_ip

    trusted_list = [p.strip() for p in trusted_proxies_env.split(",") if p.strip()]
    if "*" in trusted_list or peer_ip in trusted_list:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            if client_ip:
                return client_ip
        real_ip = request.headers.get("x-real-ip")
        if real_ip and real_ip.strip():
            return real_ip.strip()

    return peer_ip


# ---------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------
@router.post("/auth/login", response_model=AuthSessionResponse)
async def owner_login(req: OwnerLoginRequest, request: Request, response: Response):
    client_ip = get_client_ip(request)
    if not check_login_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Please wait a minute.")

    store = get_store()

    if req.email:
        # Secure multi-tenant email + password authentication
        user = store.get_user_by_email(req.email)
        if not user or user.get("is_active") != 1 or not verify_password(req.password, user["password_hash"]):
            # Generic error message to prevent user enumeration
            raise HTTPException(status_code=401, detail="Invalid email or password")

        memberships = store.list_user_memberships(user["id"])
        is_admin = bool(user.get("is_platform_admin", 0))
        if not memberships and not is_admin:
            raise HTTPException(status_code=403, detail="No business access assigned to this account")

        # Choose active tenant: either caller requested tenant if authorized, or first membership
        if req.tenant_id and any(m["tenant_id"] == req.tenant_id for m in memberships):
            active_tenant_id = req.tenant_id
        elif is_admin:
            active_tenant_id = req.tenant_id or (memberships[0]["tenant_id"] if memberships else "default_business")
        else:
            active_tenant_id = memberships[0]["tenant_id"]

        if memberships and any(m["tenant_id"] == active_tenant_id for m in memberships):
            active_membership = next(m for m in memberships if m["tenant_id"] == active_tenant_id)
            current_role = active_membership["role"]
        else:
            current_role = "owner" if is_admin else "staff"
        tenant_record = store.get_tenant(active_tenant_id)
        if not is_admin and tenant_record and tenant_record.get("status") != "active":
            raise HTTPException(status_code=403, detail=f"Business '{active_tenant_id}' is inactive or suspended.")
        business_name = tenant_record.get("business_name", "Nasta Ghar") if tenant_record else "Nasta Ghar"

    else:
        # Legacy password-only authentication (strictly restricted to default_business)
        expected = os.getenv("OWNER_PASSWORD", "")
        if not expected:
            raise HTTPException(status_code=503, detail="Owner sign-in is not configured on this server.")
        if not hmac.compare_digest(req.password, expected):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = store.get_or_create_legacy_owner()
        is_admin = bool(user.get("is_platform_admin", 0))
        active_tenant_id = "default_business"
        current_role = "owner"
        memberships = store.list_user_memberships(user["id"])
        tenant_record = store.get_tenant("default_business")
        business_name = tenant_record.get("business_name", "Nasta Ghar") if tenant_record else "Nasta Ghar"

    # Create server-side session token
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    expires_at = time.time() + SESSION_TTL_SECONDS
    store.create_session(
        token_hash=token_hash,
        user_id=user["id"],
        active_tenant_id=active_tenant_id,
        expires_at=expires_at,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent", "")
    )

    # Set secure, HTTP-only cookie
    response.set_cookie(
        OWNER_COOKIE,
        raw_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=is_cookie_secure(),
        samesite="lax",
        path="/",
    )

    available = [
        TenantInfo(
            id=m["tenant_id"],
            business_name=m.get("business_name", m["tenant_id"]),
            role=m["role"]
        )
        for m in memberships
    ]

    return AuthSessionResponse(
        authenticated=True,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            display_name=user.get("display_name", ""),
            is_platform_admin=is_admin
        ),
        active_tenant=TenantInfo(
            id=active_tenant_id,
            business_name=business_name,
            role=current_role
        ),
        available_tenants=available
    )


@router.get("/auth/session", response_model=AuthSessionResponse)
async def owner_session(ctx: TenantContext = Depends(require_auth_context)):
    store = get_store()
    user = store.get_user_by_id(ctx.user_id)
    memberships = store.list_user_memberships(ctx.user_id)
    tenant_record = store.get_tenant(ctx.tenant_id)
    business_name = tenant_record.get("business_name", ctx.tenant_id) if tenant_record else ctx.tenant_id

    available = [
        TenantInfo(
            id=m["tenant_id"],
            business_name=m.get("business_name", m["tenant_id"]),
            role=m["role"]
        )
        for m in memberships
    ]

    return AuthSessionResponse(
        authenticated=True,
        user=UserResponse(
            id=ctx.user_id,
            email=ctx.email,
            display_name=ctx.display_name,
            is_platform_admin=ctx.is_platform_admin
        ),
        active_tenant=TenantInfo(
            id=ctx.tenant_id,
            business_name=business_name,
            role=ctx.role
        ),
        available_tenants=available
    )


@router.post("/auth/logout")
async def owner_logout(request: Request, response: Response):
    token = request.cookies.get(OWNER_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    if token:
        store = get_store()
        store.revoke_session(hash_token(token))

    response.delete_cookie(
        OWNER_COOKIE,
        path="/",
        httponly=True,
        secure=is_cookie_secure(),
        samesite="lax",
    )
    return {"authenticated": False}


@router.get("/auth/tenants")
async def list_user_tenants(ctx: TenantContext = Depends(require_auth_context)):
    store = get_store()
    memberships = store.list_user_memberships(ctx.user_id)
    return {
        "tenants": [
            {
                "id": m["tenant_id"],
                "business_name": m.get("business_name", m["tenant_id"]),
                "role": m["role"],
                "category": m.get("category", ""),
                "primary_accent": m.get("primary_accent", "#f97316")
            }
            for m in memberships
        ]
    }


@router.post("/auth/switch-tenant", response_model=AuthSessionResponse)
async def switch_tenant(
    req: SwitchTenantRequest,
    request: Request,
    ctx: TenantContext = Depends(require_auth_context)
):
    target_tenant = "default_business" if req.tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else req.tenant_id
    store = get_store()

    tenant_record = store.get_tenant(target_tenant)
    if not tenant_record or tenant_record.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail=f"Business '{target_tenant}' is inactive or suspended."
        )

    membership = store.get_membership(ctx.user_id, target_tenant)
    if not membership:
        raise HTTPException(status_code=403, detail="You do not have access to this business.")

    token = request.cookies.get(OWNER_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    if token:
        store.update_session_active_tenant(hash_token(token), target_tenant)

    user = store.get_user_by_id(ctx.user_id)
    tenant_record = store.get_tenant(target_tenant)
    business_name = tenant_record.get("business_name", target_tenant) if tenant_record else target_tenant
    memberships = store.list_user_memberships(ctx.user_id)

    available = [
        TenantInfo(
            id=m["tenant_id"],
            business_name=m.get("business_name", m["tenant_id"]),
            role=m["role"]
        )
        for m in memberships
    ]

    return AuthSessionResponse(
        authenticated=True,
        user=UserResponse(
            id=ctx.user_id,
            email=ctx.email,
            display_name=ctx.display_name,
            is_platform_admin=ctx.is_platform_admin
        ),
        active_tenant=TenantInfo(
            id=target_tenant,
            business_name=business_name,
            role=membership["role"]
        ),
        available_tenants=available
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/auth/change-password")
async def change_password(
    req: ChangePasswordRequest,
    ctx: TenantContext = Depends(require_auth_context)
):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long.")

    store = get_store()
    user = store.get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    new_hash = hash_password(req.new_password)
    with store._connect() as db:
        db.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (new_hash, time.time(), ctx.user_id)
        )
    return {"status": "success", "message": "Password updated successfully."}


# ---------------------------------------------------------
# Customer Review Flow Endpoints (Public)
# ---------------------------------------------------------
@router.post("/reviews/ideas", response_model=ReviewIdeasResponse)
async def get_review_ideas(req: ReviewIdeasRequest, request: Request):
    if not review_service.check_rate_limit(f"ideas:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    from Backend.app.core.entitlements.entitlements import check_tenant_entitlement, ENTITLEMENT_REVIEW_MANAGER
    if not check_tenant_entitlement(req.business_id, ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(
            status_code=403,
            detail=f"Feature '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{req.business_id}'."
        )
    try:
        return review_service.generate_ideas(req)
    except Exception as e:
        print(f"[ReviewAssistant] Ideas error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not generate review ideas right now. Please try again."
        )


@router.post("/reviews/generate", response_model=ReviewGenerateResponse)
async def generate_review(req: ReviewGenerateRequest, request: Request):
    client_ip = get_client_ip(request)
    if not review_service.check_rate_limit(f"generate:{client_ip}", max_per_minute=30):
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached. Please wait a moment before generating another review."
        )
    from Backend.app.core.entitlements.entitlements import check_tenant_entitlement, ENTITLEMENT_REVIEW_MANAGER
    if not check_tenant_entitlement(req.business_id, ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(
            status_code=403,
            detail=f"Feature '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{req.business_id}'."
        )
    try:
        response = review_service.generate_review(req, client_key=client_ip)
        return response
    except Exception as e:
        print(f"[ReviewAssistant] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Review drafting is momentarily busy. Please try again shortly."
        )


@router.post("/reviews/validate", response_model=ReviewValidateResponse)
async def validate_review(req: ReviewValidateRequest, request: Request):
    if not review_service.check_rate_limit(f"validate:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    try:
        response = review_service.validate_review(req)
        return response
    except Exception as e:
        print(f"[ReviewAssistant] Validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Validation failed. Please verify the review text."
        )


@router.post("/reviews/session", response_model=ReviewSessionResponse)
async def create_review_session(req: ReviewSessionCreateRequest, request: Request):
    if not review_service.check_rate_limit(f"session:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    valid_id = validate_business_id(req.business_id)
    store = get_store()
    if not store.tenant_exists(valid_id):
        raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")
    tenant = store.get_tenant(valid_id)
    if tenant and tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Business '{valid_id}' is inactive or suspended.")
    if not check_tenant_entitlement(valid_id, ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(
            status_code=403,
            detail=f"Module '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{valid_id}'."
        )
    session_id = str(uuid.uuid4())
    review_service.record_event(
        "session_created",
        session_id=session_id,
        metadata={
            "business_id": valid_id,
            "table_number": req.table_number,
            "dining_type": req.dining_type
        }
    )
    return ReviewSessionResponse(
        session_id=session_id,
        business_id=valid_id,
        table_number=req.table_number,
        created_at=str(time.time())
    )


@router.post("/reviews/events")
async def record_analytics_event(ev: AnalyticsEventRequest, request: Request):
    if not review_service.check_rate_limit(f"events:{get_client_ip(request)}", max_per_minute=60):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    if ev.event_name not in ALLOWED_ANALYTICS_EVENTS:
        raise HTTPException(status_code=422, detail="Unknown event type.")

    b_id = ev.metadata.get("business_id", "default_business") if ev.metadata else "default_business"
    valid_id = validate_business_id(b_id)
    store = get_store()
    if not store.tenant_exists(valid_id):
        raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")
    tenant = store.get_tenant(valid_id)
    if tenant and tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Business '{valid_id}' is inactive or suspended.")
    if not check_tenant_entitlement(valid_id, ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(
            status_code=403,
            detail=f"Module '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{valid_id}'."
        )

    review_service.record_event(
        event_name=ev.event_name,
        session_id=ev.session_id,
        metadata=ev.metadata
    )
    return {"status": "recorded"}


@router.post("/reviews/private-feedback", response_model=PrivateFeedbackResponse)
async def submit_private_feedback(req: PrivateFeedbackRequest, request: Request):
    if not review_service.check_rate_limit(f"private-feedback:{get_client_ip(request)}", max_per_minute=5):
        raise HTTPException(status_code=429, detail="Please wait before sending another message.")
    valid_id = validate_business_id(req.business_id)
    store = get_store()
    if not store.tenant_exists(valid_id):
        raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")
    tenant = store.get_tenant(valid_id)
    if tenant and tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Business '{valid_id}' is inactive or suspended.")
    if not check_tenant_entitlement(valid_id, ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(
            status_code=403,
            detail=f"Module '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{valid_id}'."
        )
    try:
        return review_service.submit_private_feedback(req)
    except Exception as e:
        print(f"[ReviewAssistant] Private ticket error: {e}")
        raise HTTPException(status_code=500, detail="Could not route feedback to management.")


# ---------------------------------------------------------
# Public Business Config Query
# ---------------------------------------------------------
@router.get("/businesses/{business_id}/review-link", response_model=BusinessReviewLinkResponse)
async def get_business_review_link(business_id: str):
    valid_id = validate_business_id(business_id)
    info = google_review_manager.get_review_url(valid_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")
    if info.get("status") == "suspended":
        raise HTTPException(status_code=403, detail=f"Business '{valid_id}' is inactive or suspended.")
    if not check_tenant_entitlement(valid_id, ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(status_code=403, detail=f"Module '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{valid_id}'.")
    return BusinessReviewLinkResponse(
        business_id=valid_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", "Nasta Ghar"),
        branch=info.get("branch", ""),
        category=info.get("category", "Breakfast & Snacks"),
        description=info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316"),
        domain=info.get("domain", ""),
        entitlements=info.get("entitlements", ["review_manager", "digital_card"])
    )


@router.get("/businesses/{business_id}/entitlements")
async def get_business_entitlements(business_id: str):
    valid_id = validate_business_id(business_id)
    info = google_review_manager.get_review_url(valid_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")
    return {
        "business_id": valid_id,
        "entitlements": info.get("entitlements", ["review_manager", "digital_card"]),
        "status": info.get("status", "active")
    }


@router.get("/businesses/by-domain/{domain}", response_model=BusinessReviewLinkResponse)
async def get_business_by_domain(domain: str):
    store = get_store()
    clean_domain = domain.strip().lower()
    tenant = store.get_tenant_by_domain(clean_domain)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"No active business mapped to domain '{clean_domain}'.")
    info = google_review_manager.get_review_url(tenant["id"])
    if not info:
        raise HTTPException(status_code=404, detail=f"Business configuration for '{tenant['id']}' not found.")
    if info.get("status") == "suspended":
        raise HTTPException(status_code=403, detail=f"Business '{tenant['id']}' is inactive or suspended.")
    if not check_tenant_entitlement(tenant["id"], ENTITLEMENT_REVIEW_MANAGER):
        raise HTTPException(
            status_code=403,
            detail=f"Module '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{tenant['id']}'."
        )
    return BusinessReviewLinkResponse(
        business_id=tenant["id"],
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", tenant.get("business_name", "")),
        branch=info.get("branch", ""),
        category=info.get("category", "Cafe"),
        description=info.get("description", ""),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316"),
        domain=tenant.get("domain", ""),
        entitlements=info.get("entitlements", ["review_manager", "digital_card"])
    )


# ---------------------------------------------------------
# Protected Owner / Manager / Staff Endpoints
# ---------------------------------------------------------
@router.get("/reviews/analytics")
async def get_analytics(
    business_id: Optional[str] = None,
    timezone: Optional[str] = "Asia/Kolkata",
    ctx: TenantContext = Depends(require_tenant_access("staff", required_entitlement="review_manager"))
):
    target = business_id or ctx.tenant_id
    validate_business_id(target)
    return review_service.get_analytics_summary(business_id=target, timezone_str=timezone or "Asia/Kolkata")


@router.get("/reviews/private-tickets")
async def get_private_tickets(
    business_id: Optional[str] = None,
    ctx: TenantContext = Depends(require_tenant_access("manager", required_entitlement="review_manager"))
):
    target = business_id or ctx.tenant_id
    validate_business_id(target)
    return review_service.get_private_tickets(business_id=target)


class TicketStatusUpdateRequest(BaseModel):
    status: str


@router.patch("/reviews/private-tickets/{ticket_id}/status")
async def update_private_ticket_status(
    ticket_id: str,
    req: TicketStatusUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_access("manager", required_entitlement="review_manager"))
):
    norm_status = req.status.strip().upper()
    if norm_status not in ("OPEN", "RESOLVED", "ESCALATED"):
        raise HTTPException(status_code=400, detail="Invalid status. Must be OPEN, RESOLVED, or ESCALATED.")
    
    success = review_service.update_ticket_status(ticket_id=ticket_id, status=norm_status, tenant_id=ctx.tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found or does not belong to this tenant.")
    return {"status": "success", "ticket_id": ticket_id, "new_status": norm_status}


@router.post("/reviews/manager-reply", response_model=ManagerReplyResponse)
async def generate_manager_reply(
    req: ManagerReplyRequest,
    _: TenantContext = Depends(require_tenant_access("manager", required_entitlement="review_manager"))
):
    try:
        return review_service.generate_manager_reply(req)
    except Exception as e:
        print(f"[ReviewAssistant] GM reply error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate manager response.")


@router.post("/businesses/{business_id}/config", response_model=BusinessReviewLinkResponse)
async def update_business_config(
    business_id: str,
    cfg: BusinessConfigUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_access("owner", required_entitlement=ENTITLEMENT_REVIEW_MANAGER))
):
    valid_id = validate_business_id(business_id)
    # Only platform admins can modify entitlements; tenant owners cannot self-assign packages
    effective_entitlements = cfg.entitlements if ctx.is_platform_admin else None
    info = google_review_manager.update_business_config(
        business_id=valid_id,
        google_review_url=cfg.google_review_url,
        business_name=cfg.business_name,
        branch=cfg.branch,
        category=cfg.category,
        description=cfg.description,
        topics=cfg.topics,
        primary_accent=cfg.primary_accent,
        domain=cfg.domain,
        entitlements=effective_entitlements
    )
    return BusinessReviewLinkResponse(
        business_id=valid_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", "Nasta Ghar"),
        branch=info.get("branch", ""),
        category=info.get("category", "Breakfast & Snacks"),
        description=info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316"),
        domain=info.get("domain", ""),
        entitlements=info.get("entitlements", ["review_manager", "digital_card"])
    )


# ---------------------------------------------------------
# Platform Administration & Tenant Onboarding
# ---------------------------------------------------------
@router.post("/platform/tenants", response_model=TenantOnboardingResponse, status_code=201)
async def onboard_tenant(
    req: TenantOnboardingRequest,
    ctx: TenantContext = Depends(require_platform_admin)
):
    valid_id = validate_business_id(req.tenant_id)
    store = get_store()

    # Prevent duplicate tenant IDs or claiming existing tenant
    if store.tenant_exists(valid_id):
        raise HTTPException(
            status_code=409,
            detail=f"Tenant '{valid_id}' already exists. Platform onboarding cannot overwrite existing tenants."
        )

    # Validate or create owner user
    norm_email = req.owner_email.strip().lower()
    existing_user = store.get_user_by_email(norm_email)
    if existing_user:
        owner_id = existing_user["id"]
    else:
        new_user = store.create_user(
            email=norm_email,
            password_hash=hash_password(req.owner_password),
            display_name=req.owner_name or norm_email.split("@")[0].title(),
            is_active=1,
            is_platform_admin=0
        )
        owner_id = new_user["id"]

    # Provision tenant in database
    tenant_record = store.upsert_tenant({
        "id": valid_id,
        "business_name": req.business_name,
        "status": req.status or "active",
        "platform": "google",
        "review_url": req.review_url or "",
        "branch": req.branch or "",
        "category": req.category or "Cafe",
        "description": req.description or "",
        "topics": req.topics or [],
        "primary_accent": req.primary_accent or "#0ea5e9",
        "domain": req.domain or "",
        "entitlements": req.entitlements or ["review_manager", "digital_card"]
    })

    # Grant initial owner membership
    store.add_membership(owner_id, valid_id, role="owner")

    # Sync with google_review_manager cache
    google_review_manager.update_business_config(
        business_id=valid_id,
        google_review_url=req.review_url or "",
        business_name=req.business_name,
        branch=req.branch or "",
        category=req.category or "Cafe",
        description=req.description or "",
        topics=req.topics or [],
        primary_accent=req.primary_accent or "#0ea5e9",
        domain=req.domain or "",
        entitlements=req.entitlements or ["review_manager", "digital_card"]
    )

    return TenantOnboardingResponse(
        tenant_id=valid_id,
        business_name=tenant_record.get("business_name", req.business_name),
        owner_email=norm_email,
        owner_user_id=owner_id,
        status=tenant_record.get("status", "active"),
        entitlements=tenant_record.get("entitlements", []),
        created=True
    )


@router.get("/platform/tenants")
async def list_tenants_admin(
    ctx: TenantContext = Depends(require_platform_admin)
):
    store = get_store()
    return store.list_tenants()


@router.patch("/platform/tenants/{business_id}/status")
async def update_tenant_status(
    business_id: str,
    req: TenantStatusUpdateRequest,
    ctx: TenantContext = Depends(require_platform_admin)
):
    valid_id = validate_business_id(business_id)
    store = get_store()
    tenant = store.get_tenant(valid_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{valid_id}' not found.")

    tenant["status"] = req.status
    store.upsert_tenant(tenant)
    google_review_manager.update_business_config(
        business_id=valid_id,
        google_review_url=tenant.get("review_url", ""),
        status=req.status
    )
    return {"tenant_id": valid_id, "status": req.status}


@router.get("/platform/tenants/{business_id}")
async def get_tenant_admin(
    business_id: str,
    ctx: TenantContext = Depends(require_platform_admin)
):
    valid_id = validate_business_id(business_id)
    store = get_store()
    tenant = store.get_tenant_admin_details(valid_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{valid_id}' not found.")
    profile = store.get_business_profile(valid_id)
    tenant["profile"] = profile
    return tenant


@router.patch("/platform/tenants/{business_id}/entitlements")
async def update_tenant_entitlements(
    business_id: str,
    req: TenantEntitlementsUpdateRequest,
    ctx: TenantContext = Depends(require_platform_admin)
):
    valid_id = validate_business_id(business_id)
    store = get_store()
    tenant = store.get_tenant(valid_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{valid_id}' not found.")

    tenant["entitlements"] = req.entitlements
    store.upsert_tenant(tenant)
    google_review_manager.update_business_config(
        business_id=valid_id,
        google_review_url=tenant.get("review_url", ""),
        entitlements=req.entitlements
    )
    return {
        "tenant_id": valid_id,
        "entitlements": req.entitlements,
        "status": tenant.get("status", "active")
    }


# ---------------------------------------------------------
# Digital Business Card & Shared Business Profile Endpoints
# ---------------------------------------------------------

@router.get("/businesses/{business_id}/card", response_model=PublicDigitalCardResponse)
async def get_public_digital_card(
    business_id: str,
    store: ReviewStore = Depends(get_store),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Public digital business card endpoint.
    Exposes only explicitly allowed public fields for active, entitled tenants with published cards.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    # 1. Tenant verification & active status
    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Business card not found or not published.")

    # 2. Digital Card entitlement check
    if not check_tenant_entitlement(target_id, ENTITLEMENT_DIGITAL_CARD):
        raise HTTPException(status_code=404, detail="Business card not found or not published.")

    # 3. Profile existence & publication check
    profile = store.get_business_profile(target_id)
    if not profile or not profile.get("is_published"):
        raise HTTPException(status_code=404, detail="Business card not found or not published.")

    # 4. Fetch published documents only
    raw_docs = doc_service.list_documents(target_id, published_only=True)
    doc_items = [
        PublicDocumentItem(
            id=d["id"],
            document_type=d["document_type"],
            display_name=d["display_name"],
            file_size_bytes=d["file_size_bytes"],
            mime_type=d.get("mime_type", "application/pdf"),
            download_url=f"/api/businesses/{valid_id}/documents/{d['id']}/file",
        )
        for d in raw_docs
    ]

    # Determine business name: display_name overrides registered tenant name if present
    display_name = (profile.get("display_name") or "").strip()
    business_name = display_name if display_name else tenant.get("business_name", valid_id)
    category = (profile.get("category") or tenant.get("category", "")).strip()

    show_review = bool(profile.get("show_review_button", True)) and check_tenant_entitlement(target_id, ENTITLEMENT_REVIEW_MANAGER)
    google_review_url = tenant.get("review_url", "") if show_review else ""
    primary_accent = profile.get("primary_accent") or tenant.get("primary_accent") or "#078BFF"

    return PublicDigitalCardResponse(
        tenant_id=valid_id,
        business_name=business_name,
        display_name=display_name,
        category=category,
        description=tenant.get("description", ""),
        primary_accent=primary_accent,
        tagline=profile.get("tagline", ""),
        opening_hours=profile.get("opening_hours", ""),
        welcome_message=profile.get("welcome_message", ""),
        email=profile.get("email", ""),
        phone_number=profile.get("phone_number", ""),
        website_url=profile.get("website_url", ""),
        address=profile.get("address", ""),
        map_url=profile.get("map_url", ""),
        whatsapp_url=profile.get("whatsapp_url", ""),
        whatsapp_group_url=profile.get("whatsapp_group_url", ""),
        instagram_url=profile.get("instagram_url", ""),
        facebook_url=profile.get("facebook_url", ""),
        youtube_url=profile.get("youtube_url", ""),
        logo_path=profile.get("logo_path", ""),
        cover_image_path=profile.get("cover_image_path", ""),
        background_preset=profile.get("background_preset", ""),
        overlay_opacity=float(profile.get("overlay_opacity") if profile.get("overlay_opacity") is not None else 0.75),
        custom_links=profile.get("custom_links", []),
        show_review_button=show_review,
        google_review_url=google_review_url,
        documents=doc_items,
    )


@router.get("/businesses/{business_id}/card/qr-info")
async def get_digital_card_qr_info(
    business_id: str,
    store: ReviewStore = Depends(get_store),
):
    """
    Returns public destination and routing information for Digital Business Card QR codes.
    Requires an active tenant and the digital_card entitlement.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Business not found or inactive.")

    if not check_tenant_entitlement(target_id, ENTITLEMENT_DIGITAL_CARD):
        raise HTTPException(status_code=403, detail="Digital Business Card module is not enabled for this business.")

    profile = store.get_business_profile(target_id)
    is_pub = bool(profile.get("is_published", False)) if profile else False

    return {
        "business_id": valid_id,
        "card_path": f"/card/{valid_id}",
        "card_url": f"/card/{valid_id}",
        "is_published": is_pub,
    }


@router.get("/businesses/{business_id}/profile", response_model=BusinessProfileResponse)
async def get_business_profile(
    business_id: str,
    request: Request,
    store: ReviewStore = Depends(get_store),
):
    """
    Retrieves the business profile.
    - Authorized tenant members (owner/manager/staff) or platform admins can inspect unpublished drafts.
    - Anonymous visitors can view only published profiles for active, entitled tenants.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    # Check whether caller has verified session for this tenant
    is_authorized = False
    try:
        ctx = await require_auth_context(request)
        if ctx.is_platform_admin or ctx.tenant_id == target_id:
            is_authorized = True
        else:
            membership = store.get_membership(ctx.user_id, target_id)
            if membership:
                is_authorized = True
    except HTTPException:
        is_authorized = False

    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Business profile not found or not published.")

    if not check_tenant_entitlement(target_id, ENTITLEMENT_DIGITAL_CARD):
        if is_authorized:
            raise HTTPException(status_code=403, detail=f"Feature module '{ENTITLEMENT_DIGITAL_CARD}' is not enabled for business '{valid_id}'.")
        raise HTTPException(status_code=404, detail="Business profile not found or not published.")

    profile = store.get_business_profile(target_id)

    if not is_authorized:
        if not profile or not profile.get("is_published"):
            raise HTTPException(status_code=404, detail="Business profile not found or not published.")

    if not profile:
        now = time.time()
        return BusinessProfileResponse(
            tenant_id=valid_id,
            is_published=False,
            show_review_button=True,
            created_at=now,
            updated_at=now,
        )

    profile["tenant_id"] = valid_id
    return BusinessProfileResponse(**profile)


@router.put("/businesses/{business_id}/profile", response_model=BusinessProfileResponse)
@router.post("/businesses/{business_id}/profile", response_model=BusinessProfileResponse)
async def update_business_profile(
    business_id: str,
    req: BusinessProfileUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_access("owner", required_entitlement=ENTITLEMENT_DIGITAL_CARD)),
    store: ReviewStore = Depends(get_store),
):
    """
    Owner-level profile update endpoint.
    Preserves omitted fields, normalizes links, validates phone numbers, and enforces tenant scoping.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    update_payload = req.model_dump(exclude_unset=True)
    updated = store.upsert_business_profile(target_id, update_payload)
    updated["tenant_id"] = valid_id
    return BusinessProfileResponse(**updated)


# ---------------------------------------------------------
# Tenant Document Endpoints (Menus, Catalogs, Brochures)
# ---------------------------------------------------------

@router.post("/businesses/{business_id}/documents", response_model=DocumentMetadataResponse, status_code=201)
async def upload_tenant_document(
    business_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("food_menu"),
    display_name: Optional[str] = Form(None),
    is_published: bool = Form(True),
    ctx: TenantContext = Depends(require_tenant_access("owner", required_entitlement=ENTITLEMENT_DIGITAL_CARD)),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Uploads a tenant-scoped PDF document (up to 10 MiB) with signature checking and atomic write.
    Requires owner role and digital_card entitlement.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    # Read and enforce file limits (10 MiB)
    content = await file.read(MAX_DOCUMENT_SIZE_BYTES + 1)
    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of 10 MiB ({MAX_DOCUMENT_SIZE_BYTES} bytes)."
        )
    if not content or len(content) < 10:
        raise HTTPException(status_code=422, detail="File is empty or corrupted.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=422,
            detail="Invalid document signature: File must be a valid PDF document starting with '%PDF-'."
        )

    safe_original = sanitize_filename(file.filename or "document.pdf")
    try:
        record = doc_service.save_document(
            tenant_id=target_id,
            content=content,
            original_filename=safe_original,
            document_type=document_type,
            display_name=display_name,
            is_published=is_published,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist document: {str(e)}")

    record["download_url"] = f"/api/businesses/{valid_id}/documents/{record['id']}/file"
    return DocumentMetadataResponse(**record)


@router.get("/businesses/{business_id}/documents", response_model=List[DocumentMetadataResponse])
async def list_tenant_documents(
    business_id: str,
    ctx: TenantContext = Depends(require_tenant_access("manager", required_entitlement=ENTITLEMENT_DIGITAL_CARD)),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Lists all documents for a tenant (including unpublished).
    Requires manager or owner role and digital_card entitlement.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id
    docs = doc_service.list_documents(target_id, published_only=False)
    results = []
    for d in docs:
        d["download_url"] = f"/api/businesses/{valid_id}/documents/{d['id']}/file"
        results.append(DocumentMetadataResponse(**d))
    return results


@router.patch("/businesses/{business_id}/documents/{document_id}", response_model=DocumentMetadataResponse)
async def update_tenant_document_metadata(
    business_id: str,
    document_id: str,
    req: DocumentUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_access("owner", required_entitlement=ENTITLEMENT_DIGITAL_CARD)),
    store: ReviewStore = Depends(get_store),
):
    """
    Updates document display name, category, or publication state.
    Requires owner role and digital_card entitlement.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    doc = store.get_tenant_document(target_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    updated = store.update_tenant_document(target_id, document_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Document not found.")

    updated["download_url"] = f"/api/businesses/{valid_id}/documents/{updated['id']}/file"
    return DocumentMetadataResponse(**updated)


@router.delete("/businesses/{business_id}/documents/{document_id}")
async def delete_tenant_document(
    business_id: str,
    document_id: str,
    ctx: TenantContext = Depends(require_tenant_access("owner", required_entitlement=ENTITLEMENT_DIGITAL_CARD)),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Deletes a document from both disk storage and database metadata.
    Enforces tenant ownership strictly.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    doc = doc_service.store.get_tenant_document(target_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    deleted = doc_service.delete_document(target_id, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {"status": "deleted", "id": document_id}


@router.get("/businesses/{business_id}/documents/{document_id}/file")
async def serve_tenant_document(
    business_id: str,
    document_id: str,
    request: Request,
    store: ReviewStore = Depends(get_store),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Serves a tenant document PDF with safe headers.
    - Published documents are accessible to anonymous visitors.
    - Unpublished documents require verified membership (staff/manager/owner) in the owning tenant.
    - Always applies X-Content-Type-Options: nosniff and Content-Type: application/pdf.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Document not found.")

    if not check_tenant_entitlement(target_id, ENTITLEMENT_DIGITAL_CARD):
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = store.get_tenant_document(target_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.get("is_published"):
        # Unpublished document: check membership
        try:
            ctx = await require_auth_context(request)
            if not (ctx.is_platform_admin or ctx.tenant_id == target_id or store.get_membership(ctx.user_id, target_id)):
                raise HTTPException(status_code=404, detail="Document not found.")
        except HTTPException:
            raise HTTPException(status_code=404, detail="Document not found.")

    file_path = doc_service.get_document_path(target_id, document_id)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found.")

    file_bytes = file_path.read_bytes()
    clean_filename = sanitize_filename(doc.get("original_filename", "document.pdf"))

    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'inline; filename="{clean_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600" if doc.get("is_published") else "no-store, no-cache",
        }
    )


@router.get("/documents/{document_id}")
async def serve_public_document_direct(
    document_id: str,
    store: ReviewStore = Depends(get_store),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Direct public document resolution endpoint.
    Serves published PDFs for active, entitled tenants.
    """
    doc = store.get_document_by_id(document_id)
    if not doc or not doc.get("is_published"):
        raise HTTPException(status_code=404, detail="Document not found.")

    target_id = doc["tenant_id"]
    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Document not found.")

    if not check_tenant_entitlement(target_id, ENTITLEMENT_DIGITAL_CARD):
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = doc_service.get_public_document_path(document_id)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found.")

    file_bytes = file_path.read_bytes()
    clean_filename = sanitize_filename(doc.get("original_filename", "document.pdf"))

    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'inline; filename="{clean_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
        }
    )


# ---------------------------------------------------------
# Tenant Brand Image Endpoints (Logo & Cover Photo)
# ---------------------------------------------------------

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
IMAGE_FILENAME_REGEX = re.compile(r"^(logo|cover)_[a-f0-9]{12}\.(png|jpg|jpeg|webp|svg)$")


def _detect_image_format(content: bytes) -> tuple[str, str]:
    """
    Detects valid image formats by header magic bytes.
    Returns (extension, media_type) or raises ValueError.
    """
    if len(content) < 16:
        raise ValueError("Image file is empty or corrupted.")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png", "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        return ".webp", "image/webp"
    trimmed = content[:256].strip().lower()
    if (trimmed.startswith(b"<?xml") or trimmed.startswith(b"<svg")) and b"<svg" in content[:1024]:
        return ".svg", "image/svg+xml"
    raise ValueError("Invalid image format. Allowed formats: PNG, JPEG, WebP, SVG.")


@router.post("/businesses/{business_id}/images")
async def upload_tenant_image(
    business_id: str,
    file: UploadFile = File(...),
    image_type: str = Form("logo"),
    ctx: TenantContext = Depends(require_tenant_access("owner", required_entitlement=ENTITLEMENT_DIGITAL_CARD)),
    doc_service: DocumentStorageService = Depends(get_document_storage),
    store: ReviewStore = Depends(get_store),
):
    """
    Uploads a tenant-scoped logo or cover banner image (up to 5 MiB).
    Validates magic bytes, writes atomically, cleans up replaced assets,
    and updates business profile automatically.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    norm_type = "logo" if str(image_type).strip().lower() == "logo" else "cover"

    content = await file.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image file exceeds maximum allowed limit of 5 MiB ({MAX_IMAGE_SIZE_BYTES} bytes)."
        )

    try:
        ext, media_type = _detect_image_format(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if ext == ".svg":
        try:
            content = sanitize_svg(content)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"SVG validation failed: {str(e)}")

    sha256_hash = hashlib.sha256(content).hexdigest()

    tenant_dir = doc_service._resolve_tenant_dir(target_id)
    images_dir = (tenant_dir / "images").resolve()
    images_dir.mkdir(parents=True, exist_ok=True)

    if not images_dir.is_relative_to(doc_service.storage_root):
        raise HTTPException(status_code=403, detail="Storage path traversal violation.")

    # Clean up previous asset if an uploaded image exists
    current_profile = store.get_business_profile(target_id) or {}
    old_path = current_profile.get("logo_path" if norm_type == "logo" else "cover_image_path", "")
    if old_path and f"/api/businesses/{valid_id}/images/" in old_path:
        old_filename = old_path.split("/")[-1]
        if IMAGE_FILENAME_REGEX.match(old_filename):
            old_file = images_dir / old_filename
            if old_file.is_file() and not old_file.is_symlink():
                try:
                    old_file.unlink()
                except OSError:
                    pass

    unique_name = f"{norm_type}_{uuid.uuid4().hex[:12]}{ext}"
    final_file = images_dir / unique_name
    temp_file = images_dir / f"{unique_name}.tmp"

    try:
        temp_file.write_bytes(content)
        os.replace(temp_file, final_file)
    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    image_url = f"/api/businesses/{valid_id}/images/{unique_name}"

    # Automatically persist to profile
    field_name = "logo_path" if norm_type == "logo" else "cover_image_path"
    store.upsert_business_profile(target_id, {field_name: image_url})

    return {
        "image_url": image_url,
        "image_type": norm_type,
        "filename": unique_name,
        "size_bytes": len(content),
        "mime_type": media_type,
        "sha256": sha256_hash,
    }


@router.get("/businesses/{business_id}/images/{filename}")
async def serve_tenant_image(
    business_id: str,
    filename: str,
    store: ReviewStore = Depends(get_store),
    doc_service: DocumentStorageService = Depends(get_document_storage),
):
    """
    Serves tenant brand image with public caching and nosniff protection.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    if not IMAGE_FILENAME_REGEX.match(filename):
        raise HTTPException(status_code=404, detail="Image not found.")

    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Image not found.")

    if not check_tenant_entitlement(target_id, ENTITLEMENT_DIGITAL_CARD):
        raise HTTPException(status_code=404, detail="Image not found.")

    tenant_dir = doc_service._resolve_tenant_dir(target_id)
    images_dir = (tenant_dir / "images").resolve()
    file_path = (images_dir / filename).resolve()

    if not file_path.is_relative_to(images_dir) or not file_path.is_file() or file_path.is_symlink():
        raise HTTPException(status_code=404, detail="Image not found.")

    ext = file_path.suffix.lower()
    media_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    media_type = media_map.get(ext, "application/octet-stream")

    headers = {
        "Content-Type": media_type,
        "Cache-Control": "public, max-age=86400",
        "X-Content-Type-Options": "nosniff",
    }
    if ext == ".svg":
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"

    return Response(
        content=file_path.read_bytes(),
        media_type=media_type,
        headers=headers,
    )


