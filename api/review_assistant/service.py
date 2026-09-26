"""
Review Assistant Orchestrator Service for ChurnLens.
Manages rate limiting, automatic regeneration loops, sentiment validation,
session persistence, and privacy-preserving analytics.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict

from api.review_assistant.schemas import (
    ReviewGenerateRequest,
    ReviewGenerateResponse,
    ReviewValidateRequest,
    ReviewValidateResponse
)
from api.review_assistant.generator import review_generator
from api.review_assistant.validator import review_validator

class ReviewService:
    def __init__(self):
        # In-memory rate limiting and sessions: client_id -> timestamps
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._session_attempts: Dict[str, int] = defaultdict(int)
        
        # Privacy-conscious event store: stores metadata, not raw review text
        self._analytics_events: List[Dict[str, Any]] = []

    def check_rate_limit(self, client_key: str, max_per_minute: int = 15) -> bool:
        """Simple sliding-window rate limiter per IP/client."""
        now = time.time()
        window_start = now - 60.0
        
        # Filter older timestamps
        self._rate_limits[client_key] = [
            t for t in self._rate_limits[client_key] if t > window_start
        ]
        
        if len(self._rate_limits[client_key]) >= max_per_minute:
            return False
            
        self._rate_limits[client_key].append(now)
        return True

    def record_event(self, event_name: str, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Logs product events without storing customer PII or raw text."""
        event_record = {
            "event_id": str(uuid.uuid4()),
            "event_name": event_name,
            "session_id": session_id or "anonymous",
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self._analytics_events.append(event_record)
        # Keep capped at 1000 recent events
        if len(self._analytics_events) > 1000:
            self._analytics_events = self._analytics_events[-1000:]

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Calculates aggregated metrics for business owners."""
        event_counts = defaultdict(int)
        ratings_count = defaultdict(int)
        sentiment_breakdown = defaultdict(int)
        
        for ev in self._analytics_events:
            event_counts[ev["event_name"]] += 1
            meta = ev.get("metadata", {})
            if "rating" in meta:
                ratings_count[str(meta["rating"])] += 1
            if "sentiment" in meta:
                sentiment_breakdown[meta["sentiment"].lower()] += 1

        total_generations = event_counts.get("review_generation_completed", 0)
        google_clicks = event_counts.get("google_review_link_clicked", 0)
        conversion_rate = (
            round((google_clicks / total_generations) * 100, 1)
            if total_generations > 0 else 0.0
        )

        return {
            "total_generations": total_generations,
            "google_clicks": google_clicks,
            "conversion_rate_percent": conversion_rate,
            "regenerations": event_counts.get("review_regenerated", 0),
            "manual_edits": event_counts.get("review_edited", 0),
            "validations_passed": event_counts.get("review_validation_passed", 0),
            "validations_failed": event_counts.get("review_validation_failed", 0),
            "rating_distribution": dict(ratings_count),
            "sentiment_distribution": dict(sentiment_breakdown),
            "recent_events": self._analytics_events[-15:]
        }

    def generate_review(
        self, req: ReviewGenerateRequest, client_key: str = "default_client"
    ) -> ReviewGenerateResponse:
        session_id = req.session_id or str(uuid.uuid4())
        
        self.record_event("review_generation_started", session_id, {
            "rating": req.rating,
            "aspects_count": len(req.aspects or []),
            "has_note": bool(req.user_note),
            "tone": req.tone
        })

        # Loop counter for automatic regeneration (up to 2 attempts max)
        max_attempts = 2
        attempt = 0
        best_draft = ""
        best_val: Dict[str, Any] = {}
        provider = "engine"

        while attempt < max_attempts:
            attempt += 1
            gen_res = review_generator.generate(
                rating=req.rating,
                aspects=req.aspects or [],
                user_note=req.user_note or "",
                tone=req.tone or "natural",
                length=req.length or "medium"
            )
            draft = gen_res["review"]
            provider = gen_res["provider"]

            val_res = review_validator.validate(rating=req.rating, review_text=draft)
            best_draft = draft
            best_val = val_res

            # If consistent, break immediately
            if val_res["rating_consistent"]:
                break
            else:
                self.record_event("review_regenerated", session_id, {
                    "reason": "sentiment_mismatch",
                    "attempt": attempt
                })

        # Log completion
        is_consistent = best_val.get("rating_consistent", True)
        sentiment = best_val.get("sentiment", "Neutral")
        
        self.record_event("review_generation_completed", session_id, {
            "rating": req.rating,
            "sentiment": sentiment,
            "rating_consistent": is_consistent,
            "provider": provider
        })

        if is_consistent:
            self.record_event("review_validation_passed", session_id)
        else:
            self.record_event("review_validation_failed", session_id)

        warnings = list(best_val.get("warnings", []))
        if not is_consistent and attempt >= max_attempts:
            warnings.append(
                "Please verify your draft or provide additional notes to match your intended rating."
            )

        return ReviewGenerateResponse(
            review=best_draft,
            sentiment=sentiment,
            sentiment_confidence=best_val.get("confidence", 0.5),
            rating_consistent=is_consistent,
            warnings=warnings,
            aspects_covered=req.aspects or [],
            generation_provider=provider
        )

    def validate_review(self, req: ReviewValidateRequest, session_id: Optional[str] = None) -> ReviewValidateResponse:
        val_res = review_validator.validate(rating=req.rating, review_text=req.review)
        
        if val_res["rating_consistent"]:
            self.record_event("review_validation_passed", session_id, {"rating": req.rating})
        else:
            self.record_event("review_validation_failed", session_id, {"rating": req.rating})

        return ReviewValidateResponse(
            sentiment=val_res["sentiment"],
            confidence=val_res["confidence"],
            rating_consistent=val_res["rating_consistent"],
            warnings=val_res["warnings"],
            is_sarcastic=val_res["is_sarcastic"]
        )

review_service = ReviewService()
