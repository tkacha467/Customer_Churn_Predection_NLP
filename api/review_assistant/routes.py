"""
FastAPI Routes for ChurnLens AI Review Assistant & Business Google Integration.
"""

import time
import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, Any

from api.review_assistant.schemas import (
    ReviewGenerateRequest,
    ReviewGenerateResponse,
    ReviewValidateRequest,
    ReviewValidateResponse,
    BusinessReviewLinkResponse,
    BusinessConfigUpdateRequest,
    ReviewSessionCreateRequest,
    ReviewSessionResponse,
    AnalyticsEventRequest
)
from api.review_assistant.service import review_service
from api.review_assistant.google_reviews import google_review_manager

router = APIRouter()

def get_client_ip(request: Request) -> str:
    """Extract client IP for rate limiting."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

# 1. Review Generation Endpoint
@router.post("/reviews/generate", response_model=ReviewGenerateResponse)
async def generate_review(req: ReviewGenerateRequest, request: Request):
    client_ip = get_client_ip(request)
    
    if not review_service.check_rate_limit(client_ip, max_per_minute=20):
        raise HTTPException(
            status_code=429,
            detail="Review generation rate limit exceeded. Please wait a moment before trying again."
        )

    try:
        response = review_service.generate_review(req, client_key=client_ip)
        return response
    except Exception as e:
        # Never leak internal stack trace to customer
        print(f"[ReviewAssistant] Generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Review generation is temporarily unavailable. Please try again shortly."
        )

# 2. Review Validation Endpoint
@router.post("/reviews/validate", response_model=ReviewValidateResponse)
async def validate_review(req: ReviewValidateRequest):
    try:
        response = review_service.validate_review(req)
        return response
    except Exception as e:
        print(f"[ReviewAssistant] Validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Review validation failed. Please check your review text and try again."
        )

# 3. Session Creation Endpoint
@router.post("/reviews/session", response_model=ReviewSessionResponse)
async def create_review_session(req: ReviewSessionCreateRequest):
    session_id = str(uuid.uuid4())
    review_service.record_event(
        "session_created",
        session_id=session_id,
        metadata={"business_id": req.business_id, "customer_ref": req.customer_ref}
    )
    return ReviewSessionResponse(
        session_id=session_id,
        business_id=req.business_id,
        created_at=str(time.time())
    )

# 4. Analytics Event Logging Endpoint
@router.post("/reviews/events")
async def record_analytics_event(ev: AnalyticsEventRequest):
    review_service.record_event(
        event_name=ev.event_name,
        session_id=ev.session_id,
        metadata=ev.metadata
    )
    return {"status": "recorded"}

# 5. Analytics Summary for Business Owner
@router.get("/reviews/analytics")
async def get_analytics():
    return review_service.get_analytics_summary()

# 6. Business Google Review Link Query
@router.get("/businesses/{business_id}/review-link", response_model=BusinessReviewLinkResponse)
async def get_business_review_link(business_id: str):
    info = google_review_manager.get_review_url(business_id)
    return BusinessReviewLinkResponse(
        business_id=business_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False)
    )

# 7. Business Google Review Link Configuration (Owner Portal)
@router.post("/businesses/{business_id}/config", response_model=BusinessReviewLinkResponse)
async def update_business_config(business_id: str, cfg: BusinessConfigUpdateRequest):
    info = google_review_manager.update_business_config(
        business_id=business_id,
        google_review_url=cfg.google_review_url,
        business_name=cfg.business_name
    )
    return BusinessReviewLinkResponse(
        business_id=business_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False)
    )
