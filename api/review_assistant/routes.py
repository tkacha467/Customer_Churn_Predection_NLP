"""
FastAPI Routes for ChurnLens AI Hospitality & Review Platform.
Multi-tenant identity, authentication, authorization, and review assistance.
"""

import os
import time
import uuid
import hmac
import re
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from typing import Dict, Any, Optional, List

BUSINESS_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")

def validate_business_id(business_id: str) -> str:
    if not business_id or not BUSINESS_ID_REGEX.match(business_id):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid business identifier: '{business_id}'. Must be alphanumeric, underscores, or hyphens (1-100 characters)."
        )
    return business_id

from api.review_assistant.schemas import (
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
    ALLOWED_ANALYTICS_EVENTS,
)
from api.review_assistant.service import review_service
from api.review_assistant.google_reviews import google_review_manager
from api.review_assistant.auth import (
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
        business_name = tenant_record.get("business_name", "Nasta Ghar") if tenant_record else "Nasta Ghar"

    else:
        # Legacy password-only authentication (strictly restricted to default_business)
        expected = os.getenv("OWNER_PASSWORD", "")
        if not expected:
            raise HTTPException(status_code=503, detail="Owner sign-in is not configured on this server.")
        if not hmac.compare_digest(req.password, expected):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = store.get_or_create_legacy_owner()
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
            display_name=user.get("display_name", "")
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
            display_name=ctx.display_name
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
    target_tenant = "default_business" if req.tenant_id in ("default_business", "nasta_ghar") else req.tenant_id
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
            display_name=ctx.display_name
        ),
        active_tenant=TenantInfo(
            id=target_tenant,
            business_name=business_name,
            role=membership["role"]
        ),
        available_tenants=available
    )


# ---------------------------------------------------------
# Customer Review Flow Endpoints (Public)
# ---------------------------------------------------------
@router.post("/reviews/ideas", response_model=ReviewIdeasResponse)
async def get_review_ideas(req: ReviewIdeasRequest, request: Request):
    if not review_service.check_rate_limit(f"ideas:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    from api.review_assistant.entitlements import check_tenant_entitlement, ENTITLEMENT_REVIEW_MANAGER
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
    from api.review_assistant.entitlements import check_tenant_entitlement, ENTITLEMENT_REVIEW_MANAGER
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
    session_id = str(uuid.uuid4())
    review_service.record_event(
        "session_created",
        session_id=session_id,
        metadata={
            "business_id": req.business_id,
            "table_number": req.table_number,
            "dining_type": req.dining_type
        }
    )
    return ReviewSessionResponse(
        session_id=session_id,
        business_id=req.business_id,
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
    ctx: TenantContext = Depends(require_tenant_access("staff", required_entitlement="review_manager"))
):
    target = business_id or ctx.tenant_id
    validate_business_id(target)
    return review_service.get_analytics_summary(business_id=target)


@router.get("/reviews/private-tickets")
async def get_private_tickets(
    business_id: Optional[str] = None,
    ctx: TenantContext = Depends(require_tenant_access("manager", required_entitlement="review_manager"))
):
    target = business_id or ctx.tenant_id
    validate_business_id(target)
    return review_service.get_private_tickets(business_id=target)


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
    ctx: TenantContext = Depends(require_tenant_access("owner"))
):
    valid_id = validate_business_id(business_id)
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
        entitlements=cfg.entitlements
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
