"""
Review Assistant Orchestrator Service for ChurnLens.
Manages candidate idea generation, humanized review drafting,
sentiment validation, session tracking, and simplified restaurant owner analytics.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict

from api.review_assistant.schemas import (
    ReviewIdeasRequest,
    ReviewIdeasResponse,
    ReviewIdeaItem,
    ReviewGenerateRequest,
    ReviewGenerateResponse,
    ReviewValidateRequest,
    ReviewValidateResponse,
    ManagerReplyRequest,
    ManagerReplyResponse,
    PrivateFeedbackRequest,
    PrivateFeedbackResponse
)
from api.review_assistant.generator import review_generator
from api.review_assistant.validator import review_validator
from api.review_assistant.storage import ReviewStore

class ReviewService:
    def __init__(self):
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._store = ReviewStore()
        self._analytics_events: List[Dict[str, Any]] = self._store.list_events()
        self._private_tickets: List[Dict[str, Any]] = self._store.list_tickets(limit=5000)

    def check_rate_limit(self, client_key: str, max_per_minute: int = 30) -> bool:
        """Sliding-window rate limiter per client IP."""
        now = time.time()
        window_start = now - 60.0
        self._rate_limits[client_key] = [
            t for t in self._rate_limits[client_key] if t > window_start
        ]
        if len(self._rate_limits[client_key]) >= max_per_minute:
            return False
        self._rate_limits[client_key].append(now)
        return True

    def record_event(
        self,
        event_name: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        event_record = {
            "event_id": str(uuid.uuid4()),
            "event_name": event_name,
            "session_id": session_id or "anonymous",
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self._store.add_event(event_record)
        self._analytics_events.append(event_record)
        if len(self._analytics_events) > 2000:
            self._analytics_events = self._analytics_events[-2000:]

    def generate_ideas(self, req: ReviewIdeasRequest) -> ReviewIdeasResponse:
        """Generates 3-5 distinct, customer-grounded review candidate ideas."""
        raw_ideas = review_generator.generate_ideas(
            rating=req.rating,
            aspects=req.aspects or [],
            user_note=req.user_note or "",
            business_name=req.business_id,
            language=req.language or "english",
            category=req.category
        )
        ideas = [ReviewIdeaItem(**item) for item in raw_ideas]
        self.record_event("review_ideas_generated", metadata={
            "rating": req.rating,
            "aspects": req.aspects or [],
            "has_note": bool(req.user_note),
            "language": req.language or "english"
        })
        return ReviewIdeasResponse(ideas=ideas)

    def generate_review(
        self, req: ReviewGenerateRequest, client_key: str = "default_client"
    ) -> ReviewGenerateResponse:
        session_id = req.session_id or str(uuid.uuid4())
        
        self.record_event("review_generation_started", session_id, {
            "rating": req.rating,
            "dining_type": req.dining_type,
            "table_number": req.table_number,
            "aspects_count": len(req.aspects or []),
            "has_note": bool(req.user_note),
            "has_idea": bool(req.selected_idea),
            "tone": req.tone,
            "language": req.language or "english"
        })

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
                selected_idea=req.selected_idea,
                tone=req.tone or "natural",
                length=req.length or "medium",
                dining_type=req.dining_type or "dine_in",
                emoji_preference=req.emoji_preference or "light",
                business_name=req.business_id,
                language=req.language or "english",
                category=req.category
            )
            draft = gen_res["review"]
            provider = gen_res["provider"]

            val_res = review_validator.validate(rating=req.rating, review_text=draft)
            best_draft = draft
            best_val = val_res

            if val_res["rating_consistent"]:
                break
            else:
                self.record_event("review_regenerated", session_id, {
                    "reason": "sentiment_mismatch",
                    "attempt": attempt
                })

        is_consistent = best_val.get("rating_consistent", True)
        sentiment = best_val.get("sentiment", "Neutral")
        
        self.record_event("review_generation_completed", session_id, {
            "rating": req.rating,
            "sentiment": sentiment,
            "rating_consistent": is_consistent,
            "table_number": req.table_number,
            "provider": provider,
            "language": req.language or "english"
        })

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
            dining_type=req.dining_type or "dine_in",
            table_number=req.table_number,
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

    def submit_private_feedback(self, req: PrivateFeedbackRequest) -> PrivateFeedbackResponse:
        """Stores optional direct diner notes for restaurant management without rating manipulation."""
        ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
        ticket = {
            "ticket_id": ticket_id,
            "business_id": req.business_id,
            "table_number": req.table_number or "General",
            "rating": req.rating,
            "diner_note": req.diner_note,
            "aspects": req.aspects,
            "guest_contact": req.guest_contact,
            "timestamp": time.time(),
            "status": "OPEN"
        }
        self._private_tickets.append(ticket)
        self._store.add_ticket(ticket)
        self.record_event("private_feedback_submitted", metadata={"ticket_id": ticket_id, "rating": req.rating})
        
        return PrivateFeedbackResponse(
            status="escalated",
            ticket_id=ticket_id,
            message="Your feedback has been shared with the restaurant team. Thank you for helping us improve!"
        )

    def get_private_tickets(self) -> List[Dict[str, Any]]:
        return self._store.list_tickets(limit=20)

    def generate_manager_reply(self, req: ManagerReplyRequest) -> ManagerReplyResponse:
        val_res = review_validator.validate(rating=req.rating, review_text=req.guest_review)
        sentiment = val_res.get("sentiment", "Neutral")
        
        res = review_generator.generate_manager_reply(
            guest_review=req.guest_review,
            rating=req.rating,
            guest_name=req.guest_name or "Valued Guest",
            manager_name=req.manager_name or "Management Team",
            tone=req.tone or "gracious"
        )
        
        action = "Send appreciation" if req.rating >= 4 else "Management follow-up"
        return ManagerReplyResponse(
            reply=res["reply"],
            detected_sentiment=sentiment,
            recommended_action=action
        )

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Calculates authentic, non-faked activity metrics for the restaurant owner."""
        self._analytics_events = self._store.list_events()
        event_counts = defaultdict(int)
        ratings_count = defaultdict(int)
        sentiment_breakdown = defaultdict(int)
        topic_counts = defaultdict(int)
        
        for ev in self._analytics_events:
            ev_name = ev["event_name"]
            event_counts[ev_name] += 1
            meta = ev.get("metadata", {})
            if "rating" in meta:
                ratings_count[str(meta["rating"])] += 1
            if "sentiment" in meta:
                sentiment_breakdown[meta["sentiment"].lower()] += 1
            if "aspects" in meta and isinstance(meta["aspects"], list):
                for asp in meta["aspects"]:
                    topic_counts[asp] += 1

        total_generations = event_counts.get("review_generation_completed", 0)
        # Support both new and legacy event names for Google link clicks
        google_clicks = (
            event_counts.get("google_review_link_opened", 0) +
            event_counts.get("google_review_link_clicked", 0)
        )
        reviews_copied = event_counts.get("review_copied", 0)

        # Build clean recent activity feed
        recent_activity = []
        for ev in reversed(self._analytics_events[-20:]):
            name = ev["event_name"]
            meta = ev.get("metadata", {})
            t_str = time.strftime("%H:%M", time.localtime(ev["timestamp"]))
            
            if name == "review_generation_completed":
                table = meta.get("table_number") or "Table"
                r = meta.get("rating", 5)
                recent_activity.append(f"{t_str} • {table} created a {r}-star draft")
            elif name in ["google_review_link_opened", "google_review_link_clicked"]:
                recent_activity.append(f"{t_str} • Customer opened Google review link")
            elif name == "review_copied":
                recent_activity.append(f"{t_str} • Customer copied review draft")
            elif name == "private_feedback_submitted":
                recent_activity.append(f"{t_str} • Private feedback submitted")

        # Top topics
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        top_topics_formatted = [{"topic": k, "count": v} for k, v in top_topics]

        return {
            "total_generations": total_generations,
            "google_clicks": google_clicks,
            "reviews_copied": reviews_copied,
            "rating_distribution": dict(ratings_count),
            "sentiment_distribution": dict(sentiment_breakdown),
            "top_topics": top_topics_formatted,
            "recent_activity": recent_activity[:10],
            "private_tickets_count": self._store.ticket_count(),
            # Backwards compatibility fields
            "conversion_rate_percent": round((google_clicks / total_generations) * 100, 1) if total_generations > 0 else 0.0,
            "recent_events": self._analytics_events[-15:]
        }

review_service = ReviewService()
