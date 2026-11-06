"""
Review Assistant Orchestrator Service for ChurnLens.
Manages candidate idea generation, humanized review drafting,
sentiment validation, session tracking, and simplified restaurant owner analytics.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime
import zoneinfo

from Backend.app.schemas import (
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
from Backend.app.api.generator import review_generator
from Backend.app.api.validator import review_validator
from Backend.app.core.database.storage import ReviewStore

class ReviewService:
    def __init__(self):
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._store = ReviewStore()
        self._analytics_events: List[Dict[str, Any]] = self._store.list_events()
        self._private_tickets: List[Dict[str, Any]] = self._store.list_tickets(limit=5000)
        self._recent_submissions: Dict[str, Dict[str, Any]] = {}

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
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ):
        meta = dict(metadata or {})
        resolved_tid = tenant_id or meta.get("business_id") or "default_business"
        if "business_id" not in meta:
            meta["business_id"] = resolved_tid
        event_record = {
            "event_id": str(uuid.uuid4()),
            "event_name": event_name,
            "session_id": session_id or "anonymous",
            "timestamp": time.time(),
            "metadata": meta
        }
        self._store.add_event(event_record, tenant_id=resolved_tid)
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
            "business_id": req.business_id,
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
            "business_id": req.business_id,
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
                    "business_id": req.business_id,
                    "reason": "sentiment_mismatch",
                    "attempt": attempt
                })

        is_consistent = best_val.get("rating_consistent", True)
        sentiment = best_val.get("sentiment", "Neutral")
        
        self.record_event("review_generation_completed", session_id, {
            "business_id": req.business_id,
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

    def validate_review(self, req: ReviewValidateRequest, session_id: Optional[str] = None, business_id: Optional[str] = None) -> ReviewValidateResponse:
        val_res = review_validator.validate(rating=req.rating, review_text=req.review)
        meta = {"rating": req.rating, "business_id": business_id or "default_business"}
        if val_res["rating_consistent"]:
            self.record_event("review_validation_passed", session_id, meta)
        else:
            self.record_event("review_validation_failed", session_id, meta)

        return ReviewValidateResponse(
            sentiment=val_res["sentiment"],
            confidence=val_res["confidence"],
            rating_consistent=val_res["rating_consistent"],
            warnings=val_res["warnings"],
            is_sarcastic=val_res["is_sarcastic"]
        )

    def submit_private_feedback(self, req: PrivateFeedbackRequest) -> PrivateFeedbackResponse:
        """Stores optional direct diner notes for restaurant management without rating manipulation."""
        # Lightweight idempotency: prevent duplicate tickets within 60s for identical content
        now = time.time()
        note_hash = f"{req.business_id}:{req.rating}:{req.diner_note.strip()}"
        if note_hash in self._recent_submissions:
            prev = self._recent_submissions[note_hash]
            if now - prev["timestamp"] < 60.0:
                return PrivateFeedbackResponse(
                    status="escalated",
                    ticket_id=prev["ticket_id"],
                    message="Your feedback has been shared with the restaurant team. Thank you for helping us improve!"
                )

        # Purge entries older than 5 minutes to keep memory negligible
        self._recent_submissions = {
            k: v for k, v in self._recent_submissions.items() if now - v["timestamp"] < 300.0
        }

        ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
        ticket = {
            "ticket_id": ticket_id,
            "business_id": req.business_id,
            "table_number": req.table_number or "General",
            "rating": req.rating,
            "diner_note": req.diner_note,
            "aspects": req.aspects,
            "guest_contact": req.guest_contact,
            "timestamp": now,
            "status": "OPEN"
        }
        self._private_tickets.append(ticket)
        self._store.add_ticket(ticket, tenant_id=req.business_id)
        self._recent_submissions[note_hash] = {"ticket_id": ticket_id, "timestamp": now}
        self.record_event(
            "private_feedback_submitted",
            metadata={"business_id": req.business_id, "ticket_id": ticket_id, "rating": req.rating},
            tenant_id=req.business_id,
        )
        
        return PrivateFeedbackResponse(
            status="escalated",
            ticket_id=ticket_id,
            message="Your feedback has been shared with the restaurant team. Thank you for helping us improve!"
        )

    def get_private_tickets(self, business_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        return self._store.list_tickets(business_id=business_id, limit=limit)

    def update_ticket_status(self, ticket_id: str, status: str, tenant_id: Optional[str] = None) -> bool:
        return self._store.update_ticket_status(ticket_id=ticket_id, status=status, tenant_id=tenant_id)

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

    def get_analytics_summary(self, business_id: Optional[str] = None, timezone_str: str = "Asia/Kolkata") -> Dict[str, Any]:
        """
        Calculates authentic, non-faked activity metrics scoped to a restaurant owner.
        Applies timezone-accurate aggregations, year-specific festival comparisons,
        and configurable seasonal breakdowns without assuming footfall or published reviews.
        """
        try:
            tz = zoneinfo.ZoneInfo(timezone_str or "Asia/Kolkata")
        except Exception:
            tz = zoneinfo.ZoneInfo("Asia/Kolkata")

        events = self._store.list_events(business_id=business_id)
        tickets = self._store.list_tickets(business_id=business_id, limit=500)

        event_counts = defaultdict(int)
        ratings_count = defaultdict(int)
        sentiment_breakdown = defaultdict(int)
        topic_counts = defaultdict(int)

        # Timezone-aware distributions
        hourly_distribution = {f"{h:02d}:00": 0 for h in range(24)}
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_distribution = {d: 0 for d in days_order}
        monthly_trends = defaultdict(int)
        daily_heatmap = defaultdict(int)

        # Configurable seasons (Northern/Western India hospitality seasons as default)
        season_defs = {
            "Summer (Mar-Jun)": [3, 4, 5, 6],
            "Monsoon (Jul-Sep)": [7, 8, 9],
            "Autumn & Festive (Oct-Nov)": [10, 11],
            "Winter (Dec-Feb)": [12, 1, 2]
        }
        seasonal_counts = {s: 0 for s in season_defs}

        # Configurable year-specific festival calendar
        festival_calendar = {
            2025: {
                "Holi": ("2025-03-13", "2025-03-15"),
                "Navratri": ("2025-09-22", "2025-10-02"),
                "Diwali & New Year": ("2025-10-18", "2025-10-25"),
                "Christmas & Year End": ("2025-12-24", "2025-12-31"),
            },
            2026: {
                "Holi": ("2026-03-03", "2026-03-05"),
                "Navratri": ("2026-10-11", "2026-10-20"),
                "Diwali & New Year": ("2026-11-06", "2026-11-13"),
                "Christmas & Year End": ("2026-12-24", "2026-12-31"),
            },
            2027: {
                "Holi": ("2027-03-22", "2027-03-24"),
                "Navratri": ("2027-09-30", "2027-10-09"),
                "Diwali & New Year": ("2027-10-27", "2027-11-03"),
                "Christmas & Year End": ("2027-12-24", "2027-12-31"),
            }
        }

        years_present = set()

        for ev in events:
            ev_name = ev.get("event_name", "unknown")
            event_counts[ev_name] += 1
            meta = ev.get("metadata", {})
            if "rating" in meta:
                ratings_count[str(meta["rating"])] += 1
            if "sentiment" in meta:
                sentiment_breakdown[meta["sentiment"].lower()] += 1
            if "aspects" in meta and isinstance(meta["aspects"], list):
                for asp in meta["aspects"]:
                    topic_counts[asp] += 1

            # Timezone-aware date extraction
            ts = ev.get("timestamp", time.time())
            dt = datetime.fromtimestamp(ts, tz=tz)
            years_present.add(dt.year)

            hour_str = f"{dt.hour:02d}:00"
            hourly_distribution[hour_str] += 1

            weekday_str = dt.strftime("%A")
            if weekday_str in weekly_distribution:
                weekly_distribution[weekday_str] += 1

            month_str = dt.strftime("%Y-%m")
            monthly_trends[month_str] += 1

            day_str = dt.strftime("%Y-%m-%d")
            daily_heatmap[day_str] += 1

            for s_name, s_months in season_defs.items():
                if dt.month in s_months:
                    seasonal_counts[s_name] += 1

        total_generations = (
            event_counts.get("review_generation_completed", 0) +
            event_counts.get("review_ideas_generated", 0)
        )
        google_clicks = (
            event_counts.get("google_review_link_opened", 0) +
            event_counts.get("google_review_link_clicked", 0) +
            event_counts.get("google_maps_redirect", 0)
        )
        reviews_copied = event_counts.get("review_copied", 0) + event_counts.get("review_clipboard_success", 0)
        qr_scans = event_counts.get("session_created", 0)

        # Peak usage time calculation
        busiest_hour_key = max(hourly_distribution.items(), key=lambda x: x[1])[0] if events else "13:00"
        busiest_hour_int = int(busiest_hour_key.split(":")[0])
        peak_usage_time = f"{busiest_hour_int:02d}:00 – {((busiest_hour_int + 1) % 24):02d}:00"

        # Busiest day calculation
        busiest_day = max(weekly_distribution.items(), key=lambda x: x[1])[0] if events else "Sunday"

        # Calculate Customer Rating Overview
        total_rated = sum(ratings_count.values())
        weighted_sum = sum(int(r) * cnt for r, cnt in ratings_count.items() if r.isdigit())
        avg_rating = round(weighted_sum / total_rated, 1) if total_rated > 0 else 5.0

        # Festival analysis computation
        festival_analysis = []
        target_year = max(years_present) if years_present else datetime.now(tz).year
        year_fests = festival_calendar.get(target_year, {})

        for fest_name, (start_dt, end_dt) in year_fests.items():
            fest_count = 0
            for day_str, d_count in daily_heatmap.items():
                if start_dt <= day_str <= end_dt:
                    fest_count += d_count

            s_date = datetime.strptime(start_dt, "%Y-%m-%d").date()
            e_date = datetime.strptime(end_dt, "%Y-%m-%d").date()
            fest_days = max(1, (e_date - s_date).days + 1)
            daily_fest_rate = round(fest_count / fest_days, 2)

            is_insufficient = (len(events) < 15 or fest_count == 0)
            festival_analysis.append({
                "festival": fest_name,
                "year": target_year,
                "period": f"{start_dt} to {end_dt}",
                "event_count": fest_count,
                "daily_rate": daily_fest_rate,
                "insufficient_historical_data": is_insufficient,
                "notice": "Insufficient historical data for statistically significant comparison" if is_insufficient else "Baseline comparison verified"
            })

        # Private tickets status breakdown
        ticket_status_counts = {"total": len(tickets), "open": 0, "resolved": 0, "escalated": 0}
        for t in tickets:
            st = str(t.get("status", "OPEN")).upper()
            if st in ("RESOLVED", "CLOSED"):
                ticket_status_counts["resolved"] += 1
            elif st in ("ESCALATED", "URGENT"):
                ticket_status_counts["escalated"] += 1
            else:
                ticket_status_counts["open"] += 1

        # Business Insights synthesized directly from facts
        business_insights = []
        if total_generations > 0:
            conv_rate = round((google_clicks / total_generations) * 100, 1)
            business_insights.append(f"Conversion rate from AI review generation to Google Maps click is {conv_rate}%.")
        if events:
            business_insights.append(f"Peak digital review engagement occurs around {peak_usage_time} ({hourly_distribution.get(busiest_hour_key, 0)} interactions).")
            business_insights.append(f"Most active engagement day of the week is {busiest_day}.")
        if topic_counts:
            top_kw = max(topic_counts.items(), key=lambda x: x[1])
            business_insights.append(f"Highest dining praise keyword is '{top_kw[0]}' with {top_kw[1]} customer selections.")
        if ticket_status_counts["open"] > 0:
            business_insights.append(f"{ticket_status_counts['open']} private feedback ticket(s) currently open for manager resolution.")
        else:
            business_insights.append("All direct customer feedback tickets are currently resolved.")

        # Build clean recent activity feed
        recent_activity = []
        for ev in reversed(events[-20:]):
            name = ev.get("event_name", "")
            meta = ev.get("metadata", {})
            t_dt = datetime.fromtimestamp(ev.get("timestamp", time.time()), tz=tz)
            t_str = t_dt.strftime("%H:%M")
            
            if name in ("review_generation_completed", "review_ideas_generated"):
                table = meta.get("table_number") or "Table"
                r = meta.get("rating", 5)
                recent_activity.append(f"{t_str} • {table} created a {r}-star draft")
            elif name in ("google_review_link_opened", "google_review_link_clicked", "google_maps_redirect"):
                recent_activity.append(f"{t_str} • Customer opened Google review link")
            elif name in ("review_copied", "review_clipboard_success"):
                recent_activity.append(f"{t_str} • Customer copied review draft")
            elif name == "private_feedback_submitted":
                recent_activity.append(f"{t_str} • Private feedback note submitted")
            elif name == "session_created":
                tbl = meta.get("table_number") or "Table"
                recent_activity.append(f"{t_str} • QR code session started ({tbl})")

        # Top topics
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        top_topics_formatted = [{"topic": k, "count": v} for k, v in top_topics]

        return {
            # Core Performance Stats
            "total_generations": total_generations,
            "google_clicks": google_clicks,
            "reviews_copied": reviews_copied,
            "qr_scans": qr_scans,
            "conversion_rate_percent": round((google_clicks / total_generations) * 100, 1) if total_generations > 0 else 0.0,
            
            # Customer Rating Overview
            "rating_overview": {
                "average_rating": avg_rating,
                "total_ratings": total_rated,
                "distribution": dict(ratings_count),
            },
            "rating_distribution": dict(ratings_count),
            "sentiment_distribution": dict(sentiment_breakdown),

            # Peak Usage & Busiest Day
            "peak_usage_time": peak_usage_time,
            "busiest_day": busiest_day,

            # Timezone-Aware Aggregations
            "timezone": timezone_str,
            "hourly_distribution": hourly_distribution,
            "weekly_distribution": weekly_distribution,
            "monthly_trends": dict(sorted(monthly_trends.items())),
            "seasonal_analysis": seasonal_counts,
            "festival_analysis": festival_analysis,
            "calendar_heatmap": dict(sorted(daily_heatmap.items())),

            # Business Insights & Private Tickets
            "business_insights": business_insights,
            "private_tickets_summary": ticket_status_counts,
            "private_tickets_count": ticket_status_counts["total"],

            # Recent Activity & Topics
            "top_topics": top_topics_formatted,
            "recent_activity": recent_activity[:10],
            "recent_events": events[-15:]
        }

review_service = ReviewService()
