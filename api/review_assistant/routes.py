"""
FastAPI Routes for ChurnLens AI Hospitality & Review Platform.
"""

import os
import time
import uuid
import hmac
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from typing import Dict, Any

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
)
from api.review_assistant.service import review_service
from api.review_assistant.google_reviews import google_review_manager
from api.review_assistant.auth import (
    OWNER_COOKIE, SESSION_TTL_SECONDS, check_login_rate_limit, make_session, require_owner
)

router = APIRouter()

def get_client_ip(request: Request) -> str:
    # Only trust the socket peer unless a trusted proxy is configured separately.
    return request.client.host if request.client else "127.0.0.1"

@router.post("/auth/login")
async def owner_login(req: OwnerLoginRequest, request: Request, response: Response):
    if not check_login_rate_limit(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Please wait a minute.")
    expected = os.getenv("OWNER_PASSWORD", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Owner sign-in is not configured on this server.")
    if not hmac.compare_digest(req.password, expected):
        raise HTTPException(status_code=401, detail="Password is incorrect")
    response.set_cookie(
        OWNER_COOKIE,
        make_session(),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development").lower() == "production",
        samesite="strict",
        path="/",
    )
    return {"authenticated": True}

@router.get("/auth/session", dependencies=[Depends(require_owner)])
async def owner_session():
    return {"authenticated": True}

@router.post("/auth/logout")
async def owner_logout(response: Response):
    response.delete_cookie(OWNER_COOKIE, path="/", httponly=True, samesite="strict")
    return {"authenticated": False}

# 1. Review Candidate Ideas Endpoint (MAJOR FEATURE)
@router.post("/reviews/ideas", response_model=ReviewIdeasResponse)
async def get_review_ideas(req: ReviewIdeasRequest, request: Request):
    if not review_service.check_rate_limit(f"ideas:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    try:
        return review_service.generate_ideas(req)
    except Exception as e:
        print(f"[ReviewAssistant] Ideas error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not generate review ideas right now. Please try again."
        )

# 2. Guest Review Generation Endpoint
@router.post("/reviews/generate", response_model=ReviewGenerateResponse)
async def generate_review(req: ReviewGenerateRequest, request: Request):
    client_ip = get_client_ip(request)
    
    if not review_service.check_rate_limit(f"generate:{client_ip}", max_per_minute=30):
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached. Please wait a moment before generating another review."
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

# 3. Real-Time Review Validation Endpoint
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

# 4. Manager AI Reply Studio Endpoint
@router.post("/reviews/manager-reply", response_model=ManagerReplyResponse)
async def generate_manager_reply(req: ManagerReplyRequest, _: None = Depends(require_owner)):
    try:
        return review_service.generate_manager_reply(req)
    except Exception as e:
        print(f"[ReviewAssistant] GM reply error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate manager response.")

# 5. Private Diner Feedback Escalation (Optional direct management note)
@router.post("/reviews/private-feedback", response_model=PrivateFeedbackResponse)
async def submit_private_feedback(req: PrivateFeedbackRequest, request: Request):
    if not review_service.check_rate_limit(f"private-feedback:{get_client_ip(request)}", max_per_minute=5):
        raise HTTPException(status_code=429, detail="Please wait before sending another message.")
    try:
        return review_service.submit_private_feedback(req)
    except Exception as e:
        print(f"[ReviewAssistant] Private ticket error: {e}")
        raise HTTPException(status_code=500, detail="Could not route feedback to management.")

# 6. Get Private Tickets for GM
@router.get("/reviews/private-tickets", dependencies=[Depends(require_owner)])
async def get_private_tickets():
    return review_service.get_private_tickets()

# 7. Session Creation Endpoint (With Table & Dining Context)
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

# 8. Analytics Event Logging Endpoint
@router.post("/reviews/events")
async def record_analytics_event(ev: AnalyticsEventRequest, request: Request):
    if not review_service.check_rate_limit(f"events:{get_client_ip(request)}", max_per_minute=60):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    from api.review_assistant.schemas import ALLOWED_ANALYTICS_EVENTS
    if ev.event_name not in ALLOWED_ANALYTICS_EVENTS:
        raise HTTPException(status_code=422, detail="Unknown event type.")
    review_service.record_event(
        event_name=ev.event_name,
        session_id=ev.session_id,
        metadata=ev.metadata
    )
    return {"status": "recorded"}

# 9. Hospitality Analytics Summary
@router.get("/reviews/analytics", dependencies=[Depends(require_owner)])
async def get_analytics():
    return review_service.get_analytics_summary()

# 10. Google Review Link & Restaurant Config Query
@router.get("/businesses/{business_id}/review-link", response_model=BusinessReviewLinkResponse)
async def get_business_review_link(business_id: str):
    info = google_review_manager.get_review_url(business_id)
    return BusinessReviewLinkResponse(
        business_id=business_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", "Nasta Ghar"),
        branch=info.get("branch", ""),
        category=info.get("category", "Breakfast & Snacks"),
        description=info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316")
    )

# 11. Business Configuration Update
@router.post("/businesses/{business_id}/config", response_model=BusinessReviewLinkResponse, dependencies=[Depends(require_owner)])
async def update_business_config(business_id: str, cfg: BusinessConfigUpdateRequest):
    info = google_review_manager.update_business_config(
        business_id=business_id,
        google_review_url=cfg.google_review_url,
        business_name=cfg.business_name,
        branch=cfg.branch,
        category=cfg.category,
        description=cfg.description,
        topics=cfg.topics,
        primary_accent=cfg.primary_accent
    )
    return BusinessReviewLinkResponse(
        business_id=business_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", "Nasta Ghar"),
        branch=info.get("branch", ""),
        category=info.get("category", "Breakfast & Snacks"),
        description=info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
        topics=info.get("topics", []),
        primary_accent=info.get("primary_accent", "#f97316")
    )
