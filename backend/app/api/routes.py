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
import struct
import zoneinfo
import ipaddress
import logging
from datetime import datetime, date, time as dtime, timedelta

logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.app.core.database.storage import ReviewStore
from backend.app.api.document_storage import (
    DocumentStorageService,
    get_document_storage,
    MAX_DOCUMENT_SIZE_BYTES,
    sanitize_filename,
)
from backend.app.api.svg_sanitizer import sanitize_svg
from backend.app.core.entitlements.entitlements import (
    check_tenant_entitlement,
    ENTITLEMENT_REVIEW_MANAGER,
    ENTITLEMENT_DIGITAL_CARD,
)

BUSINESS_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
DATE_PARAM_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def validate_business_id(business_id: str) -> str:
    if not business_id or not BUSINESS_ID_REGEX.match(business_id):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid business identifier: '{business_id}'. Must be alphanumeric, underscores, or hyphens (1-100 characters)."
        )
    return business_id

from backend.app.schemas import (
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
    PreviewTokenRequest,
    PreviewTokenResponse,
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
    IndustryConfigResponse,
    TerminologySchema,
    IndustrySummaryItem,
    AvailableIndustriesResponse,
    SharedBusinessProfileResponse,
    SharedBusinessProfileUpdateRequest,
    SharedBusinessLogoUploadResponse,
    DocumentMetadataResponse,
    DocumentUpdateRequest,
    PublicDigitalCardResponse,
    PublicDocumentItem,
)
from backend.app.api.service import review_service
from backend.app.core.tenants.google_reviews import google_review_manager
from backend.app.core.auth.auth import (
    OWNER_COOKIE,
    SESSION_TTL_SECONDS,
    DUMMY_SCRYPT_HASH,
    TenantContext,
    check_login_rate_limit,
    check_account_login_rate_limit,
    record_login_failure,
    record_login_success,
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
    create_preview_token,
    verify_preview_token,
    get_optional_auth_context,
)
from backend.app.core.auth.security_store import (
    SecurityStore,
    verify_turnstile_token,
    CF_DUMMY_PASS_SITEKEY,
    CF_DUMMY_FAIL_SITEKEY,
)
from backend.app.core.security.security_shield import (
    security_shield,
    emit_security_event,
    SecurityEventType,
    SecuritySeverity,
)

router = APIRouter()

def _ip_in_trusted_entries(ip_str: str, trusted_entries: list) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str.strip())
    except ValueError:
        return False
    for item in trusted_entries:
        if isinstance(item, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            if ip_obj in item:
                return True
        elif ip_obj == item:
            return True
    return False


def get_client_ip(request: Request) -> str:
    """
    Safely determine the client IP address.
    If TRUSTED_PROXIES is configured in the environment (comma-separated list of IPv4/IPv6
    addresses or CIDR networks; '*' permitted only in development/test), and the direct peer IP
    matches a trusted proxy, the X-Forwarded-For header is inspected right-to-left.
    Proxy traversal walks backwards to identify the first untrusted IP, preventing
    attackers from spoofing client IPs by injecting arbitrary leftmost values.
    Otherwise, only the direct peer IP from request.client is returned to prevent header spoofing.
    """
    peer_ip = request.client.host if request.client else "127.0.0.1"
    trusted_proxies_env = os.environ.get("TRUSTED_PROXIES", "").strip()
    if not trusted_proxies_env:
        return peer_ip

    raw_tokens = [p.strip() for p in trusted_proxies_env.split(",") if p.strip()]
    if not raw_tokens:
        return peer_ip

    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    is_wildcard = "*" in raw_tokens

    # Wildcard is strictly forbidden in staging/production
    if is_wildcard and env in ("staging", "production"):
        logger.error("Wildcard '*' in TRUSTED_PROXIES is prohibited in staging/production. Falling back to direct peer IP.")
        return peer_ip

    # Parse trusted IP / CIDR entries
    trusted_entries = []
    for token in raw_tokens:
        if token == "*":
            continue
        try:
            if "/" in token:
                trusted_entries.append(ipaddress.ip_network(token, strict=False))
            else:
                trusted_entries.append(ipaddress.ip_address(token))
        except ValueError:
            if env in ("staging", "production"):
                logger.error(f"Malformed TRUSTED_PROXIES entry '{token}' ignored in {env}.")

    # Direct peer validation
    peer_trusted = is_wildcard or _ip_in_trusted_entries(peer_ip, trusted_entries)
    if not peer_trusted:
        return peer_ip

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            if is_wildcard:
                candidate = parts[0]
            else:
                candidate = parts[0]
                for p in reversed(parts):
                    if not _ip_in_trusted_entries(p, trusted_entries):
                        candidate = p
                        break
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass

    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        clean_real = real_ip.strip()
        try:
            ipaddress.ip_address(clean_real)
            return clean_real
        except ValueError:
            pass

    return peer_ip


# ---------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------
@router.post("/auth/login", response_model=AuthSessionResponse)
async def owner_login(req: OwnerLoginRequest, request: Request, response: Response):
    client_ip = get_client_ip(request)
    normalized_email = req.email.strip().lower() if req.email else "__legacy_owner__"

    # Distributed Security Store Pre-Authentication Gate (SEC-04)
    # Checks IP velocity, pair cooldowns, and evaluates Turnstile challenge requirements
    is_allowed, status_code, wait_seconds, challenge_required = await SecurityStore.evaluate_pre_auth(
        client_ip, normalized_email
    )

    if not is_allowed:
        if status_code == "pair_cooldown_active":
            raise HTTPException(
                status_code=429,
                detail=f"Too many sign-in attempts for this account. Please wait {wait_seconds} seconds.",
                headers={"Retry-After": str(wait_seconds)},
            )
        elif status_code == "ip_rate_limited":
            raise HTTPException(
                status_code=429,
                detail="Too many sign-in attempts. Please wait a minute.",
                headers={"Retry-After": str(wait_seconds or 60)},
            )
        elif status_code == "valkey_unavailable":
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable. Please retry in a few moments.",
                headers={"Retry-After": str(wait_seconds or 30)},
            )
        elif status_code == "ip_capacity_exhausted":
            raise HTTPException(
                status_code=429,
                detail="Service capacity reached. Please wait before retrying.",
                headers={"Retry-After": str(wait_seconds or 60)},
            )
        else:
            raise HTTPException(
                status_code=429,
                detail=f"Too many sign-in attempts. Please wait {wait_seconds} seconds.",
                headers={"Retry-After": str(wait_seconds or 60)},
            )

    # Step-Up Bot Challenge Gate (Pre-Password Verification)
    turnstile_enabled = os.getenv("TURNSTILE_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    site_key = os.getenv("TURNSTILE_SITE_KEY", "").strip()
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    is_dev_test = env in ("development", "test")

    if not site_key:
        if not is_dev_test:
            logger.error(f"TURNSTILE_SITE_KEY is not configured in '{env}'. Challenge cannot be presented.")
            raise HTTPException(
                status_code=503,
                detail="Security challenge configuration is unavailable.",
            )
        site_key = CF_DUMMY_PASS_SITEKEY
    elif not is_dev_test and site_key in (CF_DUMMY_PASS_SITEKEY, CF_DUMMY_FAIL_SITEKEY):
        logger.error(f"Dummy site key configured in '{env}'. Rejecting login challenge initiation.")
        raise HTTPException(
            status_code=503,
            detail="Security challenge configuration is unavailable.",
        )

    if challenge_required and turnstile_enabled:
        if not req.turnstile_token:
            raise HTTPException(
                status_code=403,
                detail="Security verification required.",
                headers={
                    "X-Challenge-Required": "true",
                    "X-Challenge-Site-Key": site_key,
                },
            )
        is_valid, reason = await verify_turnstile_token(req.turnstile_token, client_ip)
        if not is_valid:
            if reason == "provider_timeout":
                raise HTTPException(
                    status_code=503,
                    detail="Security challenge provider unavailable. Please retry.",
                    headers={"Retry-After": "10"},
                )
            raise HTTPException(
                status_code=403,
                detail="Security verification failed or expired. Please complete the challenge again.",
                headers={
                    "X-Challenge-Required": "true",
                    "X-Challenge-Site-Key": site_key,
                    "X-Challenge-Error": reason,
                },
            )

    store = get_store()

    if req.email:
        # Constant-time multi-tenant email + password authentication (anti-enumeration defense)
        user = store.get_user_by_email(req.email)
        user_active = user is not None and user.get("is_active") == 1
        password_hash = user["password_hash"] if user_active else DUMMY_SCRYPT_HASH
        password_valid = verify_password(req.password, password_hash)

        if not user_active or not password_valid:
            cooldown, step = await SecurityStore.record_login_failure(client_ip, normalized_email)
            headers = {"Retry-After": str(cooldown)} if cooldown > 0 else None
            # Generic error message to prevent user enumeration
            raise HTTPException(status_code=401, detail="Invalid email or password", headers=headers)

        await SecurityStore.record_login_success(client_ip, normalized_email)

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
            cooldown, step = await SecurityStore.record_login_failure(client_ip, normalized_email)
            headers = {"Retry-After": str(cooldown)} if cooldown > 0 else None
            raise HTTPException(status_code=401, detail="Invalid credentials", headers=headers)

        await SecurityStore.record_login_success(client_ip, normalized_email)

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
def _resolve_tenant_review_context(business_id: str, endpoint: str = "reviews") -> Dict[str, Any]:
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id
    info = google_review_manager.get_review_url(valid_id)
    if not info:
        store = get_store()
        tenant = store.get_tenant(target_id)
        if tenant:
            from backend.app.core.industry_registry import resolve_industry, resolve_effective_topics
            from dataclasses import asdict, is_dataclass
            ind_def = resolve_industry(category=tenant.get("category"), explicit_industry_id=tenant.get("industry_id"))
            effective_topics = resolve_effective_topics(tenant.get("topics"), ind_def.industry_id)
            info = {
                "business_id": valid_id,
                "business_name": tenant.get("business_name") or valid_id,
                "category": tenant.get("category", "Breakfast & Snacks"),
                "industry_id": ind_def.industry_id,
                "topics": effective_topics,
                "is_restricted": ind_def.is_restricted,
                "restriction_notice": ind_def.restriction_notice,
                "status": tenant.get("status", "active"),
                "entitlements": tenant.get("entitlements", ["review_manager"]),
                "terminology": asdict(ind_def.terminology) if is_dataclass(ind_def.terminology) else ind_def.terminology,
            }
        else:
            emit_security_event(
                event_type=SecurityEventType.ACCESS_UNKNOWN_TENANT,
                severity=SecuritySeverity.MEDIUM,
                actor_id="anonymous",
                tenant_id=valid_id,
                details={"requested_tenant": valid_id, "endpoint": endpoint},
            )
            raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")

    if info.get("status") != "active":
        emit_security_event(
            event_type=SecurityEventType.ACCESS_SUSPENDED_TENANT,
            severity=SecuritySeverity.HIGH,
            actor_id="anonymous",
            tenant_id=valid_id,
            details={"requested_tenant": valid_id, "status": info.get("status"), "endpoint": endpoint},
        )
        raise HTTPException(status_code=403, detail=f"Business '{valid_id}' is inactive or suspended.")

    if info.get("is_restricted"):
        emit_security_event(
            event_type=SecurityEventType.ACCESS_HEALTHCARE_RESTRICTION,
            severity=SecuritySeverity.HIGH,
            actor_id="anonymous",
            tenant_id=valid_id,
            details={"industry_id": info.get("industry_id"), "business_id": valid_id, "endpoint": endpoint},
        )
        raise HTTPException(
            status_code=403,
            detail=f"Customer review experience is restricted for healthcare ('{info.get('industry_id')}') due to regulatory and safety compliance."
        )

    if not check_tenant_entitlement(valid_id, ENTITLEMENT_REVIEW_MANAGER):
        emit_security_event(
            event_type=SecurityEventType.TENANT_ENTITLEMENT_VIOLATION,
            severity=SecuritySeverity.HIGH,
            actor_id="anonymous",
            tenant_id=valid_id,
            details={"entitlement": ENTITLEMENT_REVIEW_MANAGER, "business_id": valid_id, "endpoint": endpoint},
        )
        raise HTTPException(
            status_code=403,
            detail=f"Feature '{ENTITLEMENT_REVIEW_MANAGER}' is not enabled for business '{valid_id}'."
        )

    from backend.app.core.tenants.google_reviews import is_safe_google_review_url
    if "review_url" in info:
        raw_u = info.get("review_url", "")
        if raw_u and not is_safe_google_review_url(raw_u):
            info["review_url"] = "https://maps.google.com"
            info["is_configured"] = False
    return info


@router.post("/reviews/ideas", response_model=ReviewIdeasResponse)
async def get_review_ideas(req: ReviewIdeasRequest, request: Request):
    if not review_service.check_rate_limit(f"ideas:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    info = _resolve_tenant_review_context(req.business_id, endpoint="ideas")
    try:
        return review_service.generate_ideas(
            req,
            resolved_industry=info.get("industry_id"),
            resolved_business_name=info.get("business_name"),
            effective_topics=info.get("topics")
        )
    except HTTPException:
        raise
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
    info = _resolve_tenant_review_context(req.business_id, endpoint="generate")
    try:
        response = review_service.generate_review(
            req,
            client_key=client_ip,
            resolved_industry=info.get("industry_id"),
            resolved_business_name=info.get("business_name"),
            effective_topics=info.get("topics")
        )
        return response
    except HTTPException:
        raise
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


@router.post("/reviews/preview-token", response_model=PreviewTokenResponse)
@router.get("/reviews/preview-token", response_model=PreviewTokenResponse)
async def issue_preview_token(
    business_id: Optional[str] = None,
    req: Optional[PreviewTokenRequest] = None,
    ctx: TenantContext = Depends(require_tenant_access("staff", required_entitlement=ENTITLEMENT_REVIEW_MANAGER))
):
    """
    Issues a cryptographically signed HMAC-SHA256 preview token for authenticated staff/owner/admin.
    Prevents unauthorized or unverified preview traffic from polluting customer production metrics.
    """
    raw_id = (req.business_id if req and req.business_id else None) or business_id or ctx.tenant_id
    valid_id = validate_business_id(raw_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    if not ctx.is_platform_admin and ctx.tenant_id != target_id:
        raise HTTPException(status_code=403, detail="Cannot issue preview token for an unrelated tenant.")

    token = create_preview_token(
        tenant_id=target_id,
        user_id=ctx.user_id,
        role=ctx.role,
        is_admin=ctx.is_platform_admin,
    )
    traffic_src = "internal_admin" if ctx.is_platform_admin else "preview"
    return PreviewTokenResponse(
        preview_token=token,
        traffic_source=traffic_src,
        tenant_id=target_id,
        expires_at=time.time() + 7200,
    )


@router.get("/reviews/preview-events")
async def list_preview_events_endpoint(
    business_id: Optional[str] = None,
    ctx: TenantContext = Depends(require_tenant_access("staff", required_entitlement=ENTITLEMENT_REVIEW_MANAGER)),
    store: ReviewStore = Depends(get_store),
):
    """Retrieves segregated preview and internal admin telemetry without touching customer metrics."""
    target = business_id or ctx.tenant_id
    valid_id = validate_business_id(target)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id
    return {"events": store.list_preview_events(target_id)}


@router.post("/reviews/session", response_model=ReviewSessionResponse)
async def create_review_session(req: ReviewSessionCreateRequest, request: Request):
    if not review_service.check_rate_limit(f"session:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    valid_id = validate_business_id(req.business_id)
    _resolve_tenant_review_context(valid_id)
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

    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    # 3-Way Traffic Source Determination:
    # 'customer' (default) vs. 'preview' (authenticated tenant owner/staff) vs. 'internal_admin' (platform admin)
    traffic_source = "customer"
    verified_token = None

    # 1. Verify signed preview token if supplied via body, header, or query
    raw_token = (
        req.preview_token
        or request.headers.get("x-preview-token")
        or request.query_params.get("preview_token")
    )
    if raw_token:
        verified_payload = verify_preview_token(raw_token)
        if verified_payload:
            token_tenant = verified_payload.get("tenant_id")
            if verified_payload.get("is_admin") or token_tenant == target_id:
                traffic_source = verified_payload.get("traffic_source", "preview")
                verified_token = raw_token

    # 2. Check active server session context if preview token was not already provided
    if traffic_source == "customer":
        auth_ctx = get_optional_auth_context(request)
        if auth_ctx:
            if auth_ctx.is_platform_admin:
                traffic_source = "internal_admin"
                verified_token = create_preview_token(target_id, auth_ctx.user_id, auth_ctx.role, is_admin=True)
            elif auth_ctx.tenant_id == target_id:
                traffic_source = "preview"
                verified_token = create_preview_token(target_id, auth_ctx.user_id, auth_ctx.role, is_admin=False)

    # Note: Client-supplied unauthenticated ?preview=true or is_preview=True is strictly NOT trusted.
    # Unverified claims automatically resolve to "customer".

    session_id = str(uuid.uuid4())
    is_preview_session = traffic_source in ("preview", "internal_admin")

    # Record verified session context in service
    review_service.record_session(
        session_id=session_id,
        business_id=valid_id,
        traffic_source=traffic_source,
        table_number=req.table_number,
        dining_type=req.dining_type,
    )

    review_service.record_event(
        "session_created",
        session_id=session_id,
        metadata={
            "business_id": valid_id,
            "table_number": req.table_number,
            "dining_type": req.dining_type,
            "traffic_source": traffic_source,
            "is_preview": is_preview_session,
        },
        tenant_id=valid_id,
        traffic_source=traffic_source,
    )

    return ReviewSessionResponse(
        session_id=session_id,
        business_id=valid_id,
        table_number=req.table_number,
        created_at=str(time.time()),
        traffic_source=traffic_source,
        is_preview=is_preview_session,
        preview_token=verified_token,
    )


@router.post("/reviews/events")
async def record_analytics_event(ev: AnalyticsEventRequest, request: Request):
    if not review_service.check_rate_limit(f"events:{get_client_ip(request)}", max_per_minute=60):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    if ev.event_name not in ALLOWED_ANALYTICS_EVENTS:
        raise HTTPException(status_code=422, detail="Unknown event type.")

    # Resolve target business ID from metadata or active session
    b_id = None
    explicit_business_id = False
    if ev.metadata and "business_id" in ev.metadata and ev.metadata["business_id"]:
        b_id = str(ev.metadata["business_id"]).strip()
        explicit_business_id = True
    elif ev.session_id and ev.session_id.strip():
        sess_lookup = review_service.get_session_info(ev.session_id.strip())
        if sess_lookup and sess_lookup.get("business_id"):
            b_id = sess_lookup["business_id"]
    if not b_id:
        b_id = "default_business"

    valid_id = validate_business_id(b_id)
    _resolve_tenant_review_context(valid_id, endpoint="events")

    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    # Session ID validation & cross-tenant ownership check
    sid = (ev.session_id or "").strip()
    is_valid_uuid = False
    verified_session_id = "anonymous"
    is_session_verified = False

    if sid and sid.lower() not in ("anonymous", "none", "null", "undefined", ""):
        try:
            parsed_uuid = uuid.UUID(sid, version=4)
            is_valid_uuid = (parsed_uuid.version == 4)
        except (ValueError, AttributeError, TypeError):
            is_valid_uuid = False

        if is_valid_uuid:
            normalized_sid = str(parsed_uuid)
            sess_info = review_service.get_session_info(normalized_sid, check_expiry=True)
            if sess_info:
                sess_biz = sess_info.get("business_id", "")
                norm_sess_biz = "default_business" if sess_biz in ("default_business", "nasta_ghar", "nasta-ghar") else sess_biz
                if norm_sess_biz != target_id:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Cross-tenant session borrowing detected: session belongs to '{sess_biz}', not '{valid_id}'."
                    )
                verified_session_id = normalized_sid
                is_session_verified = True
            else:
                # Unknown UUIDv4 or expired session: accepted as unverified customer session
                verified_session_id = normalized_sid
                is_session_verified = False
        else:
            # Malformed session ID (not UUIDv4): mark unverified telemetry
            verified_session_id = "unverified"
            is_session_verified = False

    # 1. Check server-verified session context
    traffic_source = "customer"
    if is_session_verified and verified_session_id not in ("anonymous", "unverified"):
        sess_info = review_service.get_session_info(verified_session_id)
        if sess_info and sess_info.get("traffic_source"):
            traffic_source = sess_info["traffic_source"]

    # 1b. Check registered preview session in Security Shield
    if traffic_source == "customer" and sid:
        if security_shield.is_preview_session(sid):
            traffic_source = "preview"

    # 2. Check signed preview token if supplied via payload, header, or query
    if traffic_source == "customer":
        raw_token = (
            ev.preview_token
            or request.headers.get("x-preview-token")
            or request.query_params.get("preview_token")
        )
        if raw_token:
            verified_payload = verify_preview_token(raw_token)
            if verified_payload:
                token_tenant = verified_payload.get("tenant_id")
                if verified_payload.get("is_admin") or token_tenant == target_id:
                    traffic_source = verified_payload.get("traffic_source", "preview")

    # 3. Check active server session context
    if traffic_source == "customer":
        auth_ctx = get_optional_auth_context(request)
        if auth_ctx:
            if auth_ctx.is_platform_admin:
                traffic_source = "internal_admin"
            elif auth_ctx.tenant_id == target_id:
                traffic_source = "preview"

    # Threat detection: Unregistered preview spoofing attempt
    if traffic_source not in ("preview", "internal_admin"):
        has_preview_claim = bool(ev.metadata and ev.metadata.get("is_preview") is True)
        has_preview_prefix = bool(sid and sid.lower().startswith("preview"))
        if has_preview_claim or has_preview_prefix:
            emit_security_event(
                event_type=SecurityEventType.ABUSE_PREVIEW_SPOOF_ATTEMPT,
                severity=SecuritySeverity.HIGH,
                actor_id=sid or "anonymous",
                tenant_id=valid_id,
                action_taken="DENIED_PREVIEW_MODE",
                outcome="FALLBACK_CUSTOMER",
                details={
                    "session_id": sid,
                    "business_id": valid_id,
                    "reason": "Unregistered client attempted to claim preview mode or prefix",
                }
            )

    meta = dict(ev.metadata or {})
    meta["traffic_source"] = traffic_source
    meta["is_preview"] = traffic_source in ("preview", "internal_admin")
    meta["session_verified"] = is_session_verified
    if not is_session_verified and sid and sid.lower() not in ("anonymous", "none", "null", "undefined", ""):
        meta["raw_session_id"] = sid

    res = review_service.record_event(
        event_name=ev.event_name,
        session_id=verified_session_id,
        metadata=meta,
        tenant_id=valid_id,
        traffic_source=traffic_source,
        idempotency_key=ev.idempotency_key,
        session_verified=is_session_verified,
    )
    return res


class PreviewSessionRegistrationRequest(BaseModel):
    business_id: str
    session_id: str


@router.post("/reviews/preview-session")
async def register_preview_session(
    payload: PreviewSessionRegistrationRequest,
    request: Request,
    ctx: TenantContext = Depends(require_auth_context),
):
    valid_id = validate_business_id(payload.business_id)
    if not ctx.is_platform_admin and ctx.tenant_id != valid_id:
        raise HTTPException(status_code=403, detail="Cross-tenant preview session registration forbidden.")

    security_shield.register_preview_session(
        session_id=payload.session_id,
        tenant_id=valid_id,
        user_id=ctx.user_id,
    )
    review_service.record_session(
        session_id=payload.session_id,
        business_id=valid_id,
        traffic_source="preview",
    )
    return {
        "status": "registered",
        "is_preview": True,
        "session_id": payload.session_id,
        "business_id": valid_id,
    }


@router.post("/reviews/private-feedback", response_model=PrivateFeedbackResponse)
async def submit_private_feedback(req: PrivateFeedbackRequest, request: Request):
    if not review_service.check_rate_limit(f"private-feedback:{get_client_ip(request)}", max_per_minute=5):
        raise HTTPException(status_code=429, detail="Please wait before sending another message.")
    valid_id = validate_business_id(req.business_id)
    _resolve_tenant_review_context(valid_id)
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
    info = _resolve_tenant_review_context(valid_id, endpoint="review-link")
    raw_term = info.get("terminology")
    term_dict = None
    if raw_term is not None:
        if hasattr(raw_term, "__dataclass_fields__"):
            from dataclasses import asdict
            term_dict = asdict(raw_term)
        elif isinstance(raw_term, dict):
            term_dict = raw_term
    from backend.app.core.tenants.google_reviews import is_safe_google_review_url
    raw_review_url = info.get("review_url", "")
    safe_review_url = raw_review_url if is_safe_google_review_url(raw_review_url) else "https://maps.google.com"
    is_conf = info.get("is_configured", False) if safe_review_url == raw_review_url else False

    ind_id = info.get("industry_id", "restaurant")
    if ind_id == "restaurant":
        tp_label = "Table Number"
        tp_placeholder = "e.g. Table 4"
    elif ind_id == "hotel":
        tp_label = "Room / Suite Number"
        tp_placeholder = "e.g. Room 302"
    else:
        tp_label = (term_dict or {}).get("touchpoint_noun", "Location")
        raw_ph = (term_dict or {}).get("touchpoint_placeholder", "Counter")
        tp_placeholder = raw_ph if raw_ph.lower().startswith("e.g.") else f"e.g. {raw_ph}"

    return BusinessReviewLinkResponse(
        business_id=valid_id,
        platform=info.get("platform", "google"),
        review_url=safe_review_url,
        is_configured=is_conf,
        business_name=info.get("business_name", "Nasta Ghar"),
        branch=info.get("branch", ""),
        category=info.get("category", "Breakfast & Snacks"),
        industry_id=ind_id,
        description=info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316"),
        domain=info.get("domain", ""),
        entitlements=info.get("entitlements", ["review_manager", "digital_card"]),
        logo_path=info.get("logo_path", ""),
        terminology=term_dict,
        touchpoint_label=tp_label,
        touchpoint_placeholder=tp_placeholder,
        allow_ai_ideas=not bool(info.get("is_restricted", False)),
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
        entitlements=info.get("entitlements", ["review_manager", "digital_card"]),
        logo_path=info.get("logo_path", "") or tenant.get("logo_path", "")
    )


# ---------------------------------------------------------
# Protected Owner / Manager / Staff Endpoints
# ---------------------------------------------------------
@router.get("/reviews/analytics")
async def get_analytics(
    business_id: Optional[str] = None,
    timezone: Optional[str] = "Asia/Kolkata",
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    ctx: TenantContext = Depends(require_tenant_access("staff", required_entitlement="review_manager"))
):
    target = business_id or ctx.tenant_id
    valid_id = validate_business_id(target)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id
    effective_tz = timezone
    if not timezone or timezone == "Asia/Kolkata":
        store = get_store()
        profile = store.get_shared_business_profile(target_id)
        if profile and profile.get("timezone"):
            effective_tz = profile["timezone"]

    try:
        tz = zoneinfo.ZoneInfo(effective_tz or "Asia/Kolkata")
    except Exception:
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")

    s_date = None
    e_date = None

    if start_date is not None:
        s_str = start_date.strip()
        if not DATE_PARAM_REGEX.match(s_str):
            raise HTTPException(status_code=422, detail=f"Invalid start_date format: '{start_date}'. Expected YYYY-MM-DD.")
        try:
            s_date = datetime.strptime(s_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid start_date value: '{start_date}'. Must be a valid calendar date.")

    if end_date is not None:
        e_str = end_date.strip()
        if not DATE_PARAM_REGEX.match(e_str):
            raise HTTPException(status_code=422, detail=f"Invalid end_date format: '{end_date}'. Expected YYYY-MM-DD.")
        try:
            e_date = datetime.strptime(e_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid end_date value: '{end_date}'. Must be a valid calendar date.")

    if s_date is not None and e_date is not None:
        if e_date < s_date:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid date range: end_date '{end_date}' cannot be earlier than start_date '{start_date}'."
            )

    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None

    if s_date is not None:
        # Inclusive start boundary: local 00:00:00 on start_date converted to UTC timestamp
        dt_start = datetime.combine(s_date, dtime.min, tzinfo=tz)
        start_timestamp = dt_start.timestamp()

    if e_date is not None:
        # Exclusive end boundary: local 00:00:00 on day following end_date converted to UTC timestamp
        dt_end = datetime.combine(e_date + timedelta(days=1), dtime.min, tzinfo=tz)
        end_timestamp = dt_end.timestamp()

    return review_service.get_analytics_summary(
        business_id=target_id,
        timezone_str=effective_tz or "Asia/Kolkata",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp
    )


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

    # Check if industry is specified and validate
    effective_industry = None
    if cfg.industry_id is not None and cfg.industry_id.strip():
        norm_ind = cfg.industry_id.strip().lower()
        if norm_ind == "healthcare":
            raise HTTPException(
                status_code=400,
                detail="Healthcare onboarding is disabled in production pending regulatory compliance and privacy review."
            )
        from backend.app.core.industry_registry import CANONICAL_INDUSTRIES
        if norm_ind not in CANONICAL_INDUSTRIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid industry_id '{cfg.industry_id}'. Must be a registered industry."
            )
        effective_industry = norm_ind

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
        entitlements=effective_entitlements,
        industry_id=effective_industry
    )
    from backend.app.core.tenants.google_reviews import is_safe_google_review_url
    raw_review_url = info.get("review_url", "")
    safe_review_url = raw_review_url if is_safe_google_review_url(raw_review_url) else "https://maps.google.com"
    is_conf = info.get("is_configured", False) if safe_review_url == raw_review_url else False

    return BusinessReviewLinkResponse(
        business_id=valid_id,
        platform=info.get("platform", "google"),
        review_url=safe_review_url,
        is_configured=is_conf,
        business_name=info.get("business_name", "Nasta Ghar"),
        branch=info.get("branch", ""),
        category=info.get("category", "Breakfast & Snacks"),
        industry_id=info.get("industry_id", "restaurant"),
        description=info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316"),
        domain=info.get("domain", ""),
        entitlements=info.get("entitlements", ["review_manager", "digital_card"]),
        logo_path=info.get("logo_path", "")
    )


@router.get("/businesses/{business_id}/industry-config", response_model=IndustryConfigResponse)
async def get_business_industry_config(
    business_id: str,
    ctx: TenantContext = Depends(require_tenant_access("staff", required_entitlement=ENTITLEMENT_REVIEW_MANAGER)),
    store: ReviewStore = Depends(get_store),
):
    """
    Authenticated, tenant-scoped endpoint returning the resolved industry configuration,
    authoritative topics with strict precedence (Tenant Custom Topics -> Industry Defaults -> Platform Fallbacks),
    normalized terminology, and feature capabilities.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    tenant = store.get_tenant(target_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Business '{valid_id}' not found.")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Business '{valid_id}' is inactive or suspended.")

    from backend.app.core.industry_registry import (
        resolve_industry,
        resolve_effective_topics,
    )

    explicit_ind = tenant.get("industry_id")
    category = tenant.get("category", "")
    ind_def = resolve_industry(category=category, explicit_industry_id=explicit_ind)

    tenant_topics = tenant.get("topics")
    has_custom = bool(tenant_topics and len(tenant_topics) > 0)
    effective_topics = resolve_effective_topics(tenant_topics, ind_def.industry_id)

    return IndustryConfigResponse(
        business_id=valid_id,
        industry_id=ind_def.industry_id,
        industry_name=ind_def.display_name,
        description=ind_def.description,
        subcategory=category if category else ind_def.default_subcategory,
        subcategories=ind_def.subcategories,
        terminology=TerminologySchema(
            customer_noun_singular=ind_def.terminology.customer_noun_singular,
            customer_noun_plural=ind_def.terminology.customer_noun_plural,
            touchpoint_noun=ind_def.terminology.touchpoint_noun,
            touchpoint_placeholder=ind_def.terminology.touchpoint_placeholder,
            disclaimer_noun=ind_def.terminology.disclaimer_noun,
            private_feedback_title=ind_def.terminology.private_feedback_title,
        ),
        default_topics=ind_def.default_topics,
        effective_topics=effective_topics,
        has_custom_topics=has_custom,
        configuration_version=ind_def.configuration_version,
        available_features=ind_def.available_features,
        analytics_labels=ind_def.analytics_labels,
        is_unclassified=bool(ind_def.industry_id == "unclassified"),
    )


@router.get("/industries", response_model=AvailableIndustriesResponse)
async def list_available_industries(
    _: TenantContext = Depends(require_auth_context),
):
    """
    Returns active, production-ready industries for tenant onboarding and owner portal selection.
    Restricted industries (e.g. Healthcare) are excluded from production onboarding.
    """
    from backend.app.core.industry_registry import get_available_industries
    items = get_available_industries()
    return AvailableIndustriesResponse(
        industries=[IndustrySummaryItem(**item) for item in items],
        count=len(items),
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

    # Provision canonical business_profiles record
    store.upsert_business_profile(valid_id, {
        "display_name": req.business_name,
        "category": req.category or "Cafe",
        "branch_name": req.branch or "",
        "description": req.description or "",
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
        description=profile.get("description") or tenant.get("description", ""),
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
# Phase 2 Subpart 2C: Shared Business Profile Endpoints
# ---------------------------------------------------------

@router.get("/businesses/{business_id}/shared-profile", response_model=SharedBusinessProfileResponse)
async def get_shared_business_profile_endpoint(
    business_id: str,
    ctx: TenantContext = Depends(require_tenant_access("staff")),
    store: ReviewStore = Depends(get_store),
):
    """
    Retrieves the canonical Shared Business Profile.
    Accessible to authenticated users with Staff, Manager, or Owner roles in the tenant.
    Returns strictly common shared identity fields with zero product configuration leakage.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    profile = store.get_shared_business_profile(target_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Shared business profile for '{valid_id}' not found."
        )

    return SharedBusinessProfileResponse(**profile)


@router.put("/businesses/{business_id}/shared-profile", response_model=SharedBusinessProfileResponse)
async def update_shared_business_profile_endpoint(
    business_id: str,
    req: SharedBusinessProfileUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_access("owner")),
    store: ReviewStore = Depends(get_store),
):
    """
    Updates the canonical Shared Business Profile record in business_profiles.
    Requires Owner permissions in the requested business.
    Preserves omitted fields using model_fields_set, validates URLs, hex accents, and timezones.
    Rejects unexpected product-specific configuration.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    existing = store.get_shared_business_profile(target_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Shared business profile for '{valid_id}' not found."
        )

    # Extract only fields explicitly included in the request body
    update_data = {}
    for field_name in req.model_fields_set:
        update_data[field_name] = getattr(req, field_name)

    updated = store.update_shared_business_profile(target_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=500,
            detail="Failed to update shared business profile."
        )

    return SharedBusinessProfileResponse(**updated)


# ---------------------------------------------------------
# Phase 2 Subpart 2D: Shared Business Logo Upload & Storage
# ---------------------------------------------------------

MAX_SHARED_LOGO_SIZE_BYTES = 2 * 1024 * 1024  # 2 MiB
MIN_LOGO_DIMENSION = 16
MAX_LOGO_DIMENSION = 4096
SHARED_LOGO_FILENAME_REGEX = re.compile(
    r"^logo_[a-zA-Z0-9_\-]+_[a-f0-9]{12}_\d+_[a-f0-9]{8}\.(png|jpg|jpeg|webp)$"
)


def _detect_and_validate_raster_image(content: bytes) -> tuple[str, str, int, int]:
    """
    Validates that content is an authentic raster image (PNG, JPEG, WebP).
    Strictly rejects SVG, HTML, executables, scripts, and corrupted payloads.
    Extracts and asserts reasonable dimensions (16x16 to 4096x4096).
    Returns (ext, media_type, width, height) or raises ValueError.
    """
    if len(content) < 16:
        raise ValueError("Image file is empty or too small to be a valid image.")

    # Explicit rejection of text, SVG, XML, HTML, and executables
    header_1024 = content[:1024].lower()
    if (
        b"<svg" in header_1024
        or b"<?xml" in header_1024
        or b"<html" in header_1024
        or b"<!doctype" in header_1024
        or b"<script" in header_1024
        or content.startswith(b"MZ")
        or content.startswith(b"\x7fELF")
    ):
        raise ValueError("Rejected: SVG, HTML, scripts, and executable files are strictly prohibited as shared logos.")

    ext: Optional[str] = None
    media_type: Optional[str] = None
    w: Optional[int] = None
    h: Optional[int] = None

    # 1. PNG check
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
        media_type = "image/png"
        try:
            w, h = struct.unpack(">II", content[16:24])
        except Exception:
            raise ValueError("Malformed PNG header: unable to parse dimensions.")

    # 2. JPEG check
    elif content.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
        media_type = "image/jpeg"
        idx = 2
        try:
            while idx < len(content) - 8:
                if content[idx] != 0xFF:
                    idx += 1
                    continue
                marker = content[idx + 1]
                if marker in (0xD8, 0xD9):
                    idx += 2
                    continue
                length = struct.unpack(">H", content[idx + 2 : idx + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", content[idx + 5 : idx + 9])
                    break
                idx += 2 + length
        except Exception:
            raise ValueError("Malformed JPEG: error parsing frame markers.")
        if w is None or h is None:
            raise ValueError("Malformed JPEG: Start of Frame (SOF) marker not found.")

    # 3. WebP check
    elif content.startswith(b"RIFF") and len(content) >= 30 and content[8:12] == b"WEBP":
        ext = ".webp"
        media_type = "image/webp"
        chunk = content[12:16]
        try:
            if chunk == b"VP8 " and len(content) >= 30:
                w = struct.unpack("<H", content[26:28])[0] & 0x3FFF
                h = struct.unpack("<H", content[28:30])[0] & 0x3FFF
            elif chunk == b"VP8L" and len(content) >= 25:
                b1, b2, b3, b4 = content[21:25]
                w = 1 + (((b2 & 0x3F) << 8) | b1)
                h = 1 + (((b4 & 0x0F) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
            elif chunk == b"VP8X" and len(content) >= 30:
                w = 1 + struct.unpack("<I", content[24:27] + b"\x00")[0]
                h = 1 + struct.unpack("<I", content[27:30] + b"\x00")[0]
            else:
                raise ValueError(f"Unsupported WebP chunk: {chunk}")
        except Exception as e:
            raise ValueError(f"Malformed WebP: unable to parse dimensions ({e}).")

    else:
        raise ValueError("Invalid image format. Allowed raster formats: PNG, JPEG, WebP.")

    if w < MIN_LOGO_DIMENSION or h < MIN_LOGO_DIMENSION or w > MAX_LOGO_DIMENSION or h > MAX_LOGO_DIMENSION:
        raise ValueError(
            f"Image dimensions ({w}x{h}) exceed allowed limits ({MIN_LOGO_DIMENSION}x{MIN_LOGO_DIMENSION} to {MAX_LOGO_DIMENSION}x{MAX_LOGO_DIMENSION} pixels)."
        )

    return ext, media_type, w, h


@router.post("/businesses/{business_id}/shared-profile/logo", response_model=SharedBusinessLogoUploadResponse)
async def upload_shared_business_logo(
    business_id: str,
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(require_tenant_access("owner")),
    doc_service: DocumentStorageService = Depends(get_document_storage),
    store: ReviewStore = Depends(get_store),
):
    """
    Uploads a canonical Shared Business Profile logo.
    Accessible only to tenant Owners (or Platform Admin).
    Accepts only approved raster formats (PNG, JPEG, WebP) up to 2 MiB.
    Atomic filesystem storage with automatic rollback and old logo cleanup.
    """
    valid_id = validate_business_id(business_id)
    target_id = ctx.tenant_id

    # 1. Enforce size limit (<= 2 MiB)
    content = await file.read(MAX_SHARED_LOGO_SIZE_BYTES + 1)
    if len(content) > MAX_SHARED_LOGO_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Logo file exceeds maximum allowed limit of 2 MiB ({MAX_SHARED_LOGO_SIZE_BYTES} bytes)."
        )

    # 2. Content & dimension validation
    try:
        ext, media_type, w, h = _detect_and_validate_raster_image(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    content_hash = hashlib.sha256(content).hexdigest()

    # 3. Path resolution & traversal safety
    clean_tenant = "default_business" if target_id in ("default_business", "nasta_ghar", "nasta-ghar") else target_id
    tenant_dir = doc_service._resolve_tenant_dir(clean_tenant)
    logos_dir = (tenant_dir / "logos").resolve()
    logos_dir.mkdir(parents=True, exist_ok=True)

    if not logos_dir.is_relative_to(doc_service.storage_root):
        raise HTTPException(status_code=403, detail="Storage path traversal violation.")

    # 4. Check profile existence & capture current logo path
    current_profile = store.get_shared_business_profile(target_id)
    if not current_profile:
        raise HTTPException(status_code=404, detail=f"Shared business profile for '{valid_id}' not found.")
    old_logo_path = current_profile.get("logo_path", "")

    # 5. Collision-proof immutable filename
    unique_name = f"logo_{clean_tenant}_{uuid.uuid4().hex[:12]}_{int(time.time())}_{content_hash[:8]}{ext}"
    final_file = logos_dir / unique_name
    temp_file = logos_dir / f".tmp_{uuid.uuid4().hex}.tmp"

    # 6. Atomic write sequence
    try:
        temp_file.write_bytes(content)
        if temp_file.stat().st_size != len(content):
            raise IOError("Written file size mismatch.")
        os.replace(temp_file, final_file)
    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        print(f"[SharedProfile] Failed to write image file: {e}")
        raise HTTPException(status_code=500, detail="Failed to write image file.")

    canonical_logo_url = f"/api/businesses/{valid_id}/shared-profile/logo/{unique_name}"

    # 7. Transactional database update & failure compensation
    try:
        updated = store.update_shared_business_logo(target_id, canonical_logo_url)
        if not updated:
            raise RuntimeError("Database record update returned no modified rows.")
    except Exception as db_err:
        # Compensation: remove newly created file immediately on DB error
        if final_file.exists():
            try:
                final_file.unlink()
            except OSError:
                pass
        print(f"[SharedProfile] Database update failed during logo upload: {db_err}")
        raise HTTPException(status_code=500, detail="Database update failed; logo upload aborted.")

    # 8. Post-commit cleanup of old managed logo
    if old_logo_path and "/shared-profile/logo/" in old_logo_path:
        old_filename = old_logo_path.split("/")[-1]
        if SHARED_LOGO_FILENAME_REGEX.match(old_filename) and old_filename != unique_name:
            old_file = (logos_dir / old_filename).resolve()
            if old_file.is_file() and not old_file.is_symlink() and old_file.is_relative_to(logos_dir):
                try:
                    old_file.unlink()
                except OSError:
                    pass

    return SharedBusinessLogoUploadResponse(
        success=True,
        logo_path=canonical_logo_url,
        filename=unique_name,
        media_type=media_type,
        size_bytes=len(content),
        dimensions={"width": w, "height": h},
        sha256=content_hash,
    )


@router.get("/businesses/{business_id}/shared-profile/logo/{filename}")
async def serve_shared_business_logo_file(
    business_id: str,
    filename: str,
    doc_service: DocumentStorageService = Depends(get_document_storage),
    store: ReviewStore = Depends(get_store),
):
    """
    Serves a specific versioned shared business logo file.
    Publicly accessible with nosniff and immutable long-term caching headers.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    if not SHARED_LOGO_FILENAME_REGEX.match(filename):
        raise HTTPException(status_code=404, detail="Logo not found.")

    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Logo not found.")

    tenant_dir = doc_service._resolve_tenant_dir(target_id)
    logos_dir = (tenant_dir / "logos").resolve()
    file_path = (logos_dir / filename).resolve()

    if not file_path.is_relative_to(logos_dir) or not file_path.is_file() or file_path.is_symlink():
        raise HTTPException(status_code=404, detail="Logo not found.")

    ext = file_path.suffix.lower()
    media_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_map.get(ext, "application/octet-stream")

    return Response(
        content=file_path.read_bytes(),
        media_type=media_type,
        headers={
            "Content-Type": media_type,
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/businesses/{business_id}/shared-profile/logo")
async def serve_current_shared_business_logo(
    business_id: str,
    doc_service: DocumentStorageService = Depends(get_document_storage),
    store: ReviewStore = Depends(get_store),
):
    """
    Serves the current active shared business logo for the given tenant.
    Publicly accessible for QR review flows and digital cards with no-cache revalidation.
    """
    valid_id = validate_business_id(business_id)
    target_id = "default_business" if valid_id in ("default_business", "nasta_ghar", "nasta-ghar") else valid_id

    tenant = store.get_tenant(target_id)
    if not tenant or tenant.get("status") != "active":
        raise HTTPException(status_code=404, detail="Business not found.")

    profile = store.get_shared_business_profile(target_id)
    if not profile or not profile.get("logo_path"):
        raise HTTPException(status_code=404, detail="Shared logo not configured.")

    logo_path = profile["logo_path"].strip()
    if not logo_path:
        raise HTTPException(status_code=404, detail="Shared logo not configured.")

    # Extract filename from canonical logo_path
    filename = logo_path.split("/")[-1]
    if not SHARED_LOGO_FILENAME_REGEX.match(filename):
        raise HTTPException(status_code=404, detail="Shared logo file not found.")

    tenant_dir = doc_service._resolve_tenant_dir(target_id)
    logos_dir = (tenant_dir / "logos").resolve()
    file_path = (logos_dir / filename).resolve()

    if not file_path.is_relative_to(logos_dir) or not file_path.is_file() or file_path.is_symlink():
        raise HTTPException(status_code=404, detail="Shared logo file not found.")

    ext = file_path.suffix.lower()
    media_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_map.get(ext, "application/octet-stream")

    return Response(
        content=file_path.read_bytes(),
        media_type=media_type,
        headers={
            "Content-Type": media_type,
            "Cache-Control": "no-cache, must-revalidate",
            "X-Content-Type-Options": "nosniff",
        },
    )


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
        print(f"[Documents] Failed to persist document: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist document.")

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
        print(f"[Images] Failed to save image: {e}")
        raise HTTPException(status_code=500, detail="Failed to save image.")

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


