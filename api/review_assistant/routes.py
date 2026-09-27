"""
FastAPI Routes for ChurnLens AI Hospitality & Review Platform.
"""

import time
import uuid
from fastapi import APIRouter, HTTPException, Request
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
    AnalyticsEventRequest,
    ManagerReplyRequest,
    ManagerReplyResponse,
    PrivateFeedbackRequest,
    PrivateFeedbackResponse
)
from api.review_assistant.service import review_service
from api.review_assistant.google_reviews import google_review_manager

router = APIRouter()

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

# 1. Guest Review Generation Endpoint
@router.post("/reviews/generate", response_model=ReviewGenerateResponse)
async def generate_review(req: ReviewGenerateRequest, request: Request):
    client_ip = get_client_ip(request)
    
    if not review_service.check_rate_limit(client_ip, max_per_minute=30):
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

# 2. Real-Time Review Validation Endpoint
@router.post("/reviews/validate", response_model=ReviewValidateResponse)
async def validate_review(req: ReviewValidateRequest):
    try:
        response = review_service.validate_review(req)
        return response
    except Exception as e:
        print(f"[ReviewAssistant] Validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Validation failed. Please verify the review text."
        )

# 3. Manager AI Reply Studio Endpoint
@router.post("/reviews/manager-reply", response_model=ManagerReplyResponse)
async def generate_manager_reply(req: ManagerReplyRequest):
    try:
        return review_service.generate_manager_reply(req)
    except Exception as e:
        print(f"[ReviewAssistant] GM reply error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate manager response.")

# 4. Private Diner Feedback Escalation (Prevents public 1-star blowups)
@router.post("/reviews/private-feedback", response_model=PrivateFeedbackResponse)
async def submit_private_feedback(req: PrivateFeedbackRequest):
    try:
        return review_service.submit_private_feedback(req)
    except Exception as e:
        print(f"[ReviewAssistant] Private ticket error: {e}")
        raise HTTPException(status_code=500, detail="Could not route feedback to management.")

# 5. Get Private Tickets for GM
@router.get("/reviews/private-tickets")
async def get_private_tickets():
    return review_service.get_private_tickets()

# 6. Session Creation Endpoint (With Table & Dining Context)
@router.post("/reviews/session", response_model=ReviewSessionResponse)
async def create_review_session(req: ReviewSessionCreateRequest):
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

# 7. Analytics Event Logging Endpoint
@router.post("/reviews/events")
async def record_analytics_event(ev: AnalyticsEventRequest):
    review_service.record_event(
        event_name=ev.event_name,
        session_id=ev.session_id,
        metadata=ev.metadata
    )
    return {"status": "recorded"}

# 8. Hospitality Analytics Summary
@router.get("/reviews/analytics")
async def get_analytics():
    return review_service.get_analytics_summary()

# 9. Google Review Link Query
@router.get("/businesses/{business_id}/review-link", response_model=BusinessReviewLinkResponse)
async def get_business_review_link(business_id: str):
    info = google_review_manager.get_review_url(business_id)
    return BusinessReviewLinkResponse(
        business_id=business_id,
        platform=info.get("platform", "google"),
        review_url=info.get("review_url", ""),
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", "Cuore Cafe & Artisan Roastery"),
        category=info.get("category", "Artisan Cafe & Roastery")
    )

# 10. Business Configuration Update
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
        is_configured=info.get("is_configured", False),
        business_name=info.get("business_name", "Cuore Cafe & Artisan Roastery"),
        category=cfg.category or "Artisan Cafe & Roastery"
    )
