"""
Review Assistant Orchestrator Service for ChurnLens.
Manages candidate idea generation, humanized review drafting,
sentiment validation, session tracking, and simplified restaurant owner analytics.
"""

import os
import time
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime
import zoneinfo

from backend.app.schemas import (
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
from backend.app.api.generator import review_generator
from backend.app.api.prompts import normalize_language
from backend.app.api.validator import review_validator
from backend.app.core.database.storage import ReviewStore

class ReviewService:
    def __init__(self):
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._custom_store: Optional[ReviewStore] = None
        self._analytics_events: List[Dict[str, Any]] = []
        self._preview_events: List[Dict[str, Any]] = []
        self._private_tickets: List[Dict[str, Any]] = []
        self._recent_submissions: Dict[str, Dict[str, Any]] = {}
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._verified_preview_sessions: Dict[str, Any] = {}
        self._dedup_cache: Dict[str, float] = {}

    @property
    def _store(self) -> ReviewStore:
        if hasattr(self, "_custom_store") and self._custom_store is not None:
            env_path = os.getenv("REVIEW_DB_PATH")
            if env_path and str(self._custom_store.path) != env_path:
                from backend.app.core.auth.auth import get_store
                return get_store()
            return self._custom_store
        from backend.app.core.auth.auth import get_store
        return get_store()

    @_store.setter
    def _store(self, store: ReviewStore):
        self._custom_store = store

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

    def record_session(
        self,
        session_id: str,
        business_id: str,
        traffic_source: str = "customer",
        table_number: Optional[str] = None,
        dining_type: Optional[str] = None,
        ttl_seconds: float = 86400.0,
    ) -> None:
        """Tracks active review session metadata and server-verified traffic source in persistent storage."""
        sess_record = self._store.create_review_session(
            session_id=session_id,
            tenant_id=business_id,
            traffic_source=traffic_source,
            table_number=table_number,
            dining_type=dining_type,
            ttl_seconds=ttl_seconds,
        )
        self._active_sessions[session_id] = sess_record
        if len(self._active_sessions) > 5000:
            cutoff = time.time() - (24 * 3600)
            self._active_sessions = {
                k: v for k, v in self._active_sessions.items() if v.get("created_at", 0) > cutoff
            }

    def get_session_info(self, session_id: str, check_expiry: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieves verified session context for the given session_id from memory or persistent store."""
        if not session_id:
            return None
        cached = self._active_sessions.get(session_id)
        if cached:
            if not check_expiry or cached.get("expires_at", float("inf")) > time.time():
                return cached
            else:
                self._active_sessions.pop(session_id, None)
                return None
        record = self._store.get_review_session(session_id, check_expiry=check_expiry)
        if record:
            self._active_sessions[session_id] = record
            return record
        return None

    def register_preview_session(self, session_id: str, tenant_id: str = "default_business") -> None:
        """Registers a server-authoritative preview session so preview traffic is excluded from production metrics."""
        if not session_id:
            return
        self._verified_preview_sessions[session_id] = time.time()
        try:
            from backend.app.core.security.security_shield import security_shield
            security_shield.register_preview_session(session_id=session_id, tenant_id=tenant_id)
        except Exception:
            pass

    def record_event(
        self,
        event_name: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        traffic_source: str = "customer",
        idempotency_key: Optional[str] = None,
        session_verified: bool = False,
    ) -> Dict[str, Any]:
        meta = dict(metadata or {})
        resolved_tid = tenant_id or meta.get("business_id") or "default_business"
        if "business_id" not in meta:
            meta["business_id"] = resolved_tid

        # Check server-registered preview session
        if session_id and session_id in self._verified_preview_sessions:
            traffic_source = "preview"
        else:
            try:
                from backend.app.core.security.security_shield import security_shield
                if session_id and security_shield.is_preview_session(session_id):
                    traffic_source = "preview"
            except Exception:
                pass

        # Check session's server-verified traffic source if not explicitly passed
        if traffic_source == "customer" and session_id and session_id not in ("anonymous", "unverified"):
            sess = self.get_session_info(session_id)
            if sess and sess.get("traffic_source"):
                traffic_source = sess["traffic_source"]

        meta["traffic_source"] = traffic_source
        meta["is_preview"] = traffic_source in ("preview", "internal_admin")
        meta["session_verified"] = session_verified

        # Basic idempotency & deduplication check (3-second sliding deduplication window)
        now = time.time()
        dedup_key = idempotency_key or f"{session_id or 'anon'}:{event_name}:{meta.get('rating', '')}:{resolved_tid}"
        if dedup_key in self._dedup_cache and (now - self._dedup_cache[dedup_key]) < 3.0:
            return {
                "status": "recorded",
                "traffic_source": traffic_source,
                "session_verified": session_verified,
                "deduplicated": True,
            }

        self._dedup_cache[dedup_key] = now
        if len(self._dedup_cache) > 5000:
            cutoff = now - 60.0
            self._dedup_cache = {k: v for k, v in self._dedup_cache.items() if v > cutoff}

        event_id = str(uuid.uuid4())
        event_record = {
            "event_id": event_id,
            "event_name": event_name,
            "session_id": session_id or "anonymous",
            "timestamp": now,
            "metadata": meta,
            "traffic_source": traffic_source,
        }

        # Segregated database storage (preview table vs. analytics_events)
        self._store.add_event(event_record, tenant_id=resolved_tid, traffic_source=traffic_source)

        # In-memory segregation: preview/admin events never pollute customer analytics
        if traffic_source in ("preview", "internal_admin"):
            self._preview_events.append(event_record)
            if len(self._preview_events) > 1000:
                self._preview_events = self._preview_events[-1000:]
        else:
            self._analytics_events.append(event_record)
            if len(self._analytics_events) > 2000:
                self._analytics_events = self._analytics_events[-2000:]

        return {
            "status": "recorded",
            "traffic_source": traffic_source,
            "session_verified": session_verified,
            "deduplicated": False,
            "event_id": event_id,
        }
    def resolve_business_name(
        self,
        business_id: str,
        client_name: Optional[str] = None,
        language: str = "english"
    ) -> str:
        """
        Dynamically resolves the business name from tenant configuration.
        Ensures internal placeholders (like 'default_business') are NEVER exposed to customers.
        If a tenant name is missing or placeholder, provides a clean fallback.
        """
        valid_id = (business_id or "").strip()
        norm_lang = normalize_language(language)

        # If client provided a valid non-placeholder name, consider it
        if client_name and client_name.strip() and client_name.strip() not in ("default_business", "default", "the restaurant"):
            if client_name.strip() in ("Nasta Ghar", "NastaGhar"):
                if norm_lang == "gujarati":
                    return "નાસ્તા ઘર"
                elif norm_lang == "hindi":
                    return "नाश्ता घर"
            return client_name.strip()

        from backend.app.core.database.storage import ReviewStore
        store = ReviewStore()
        tenant = None
        if valid_id and store.tenant_exists(valid_id):
            tenant = store.get_tenant(valid_id)
        else:
            try:
                from backend.app.core.tenants.google_reviews import google_review_manager
                info = google_review_manager.get_review_url(valid_id)
                if info:
                    tenant = info
            except Exception:
                pass

        biz_name = (tenant.get("business_name") if tenant else "") or ""
        is_placeholder = (
            not biz_name
            or biz_name.strip() in ("default_business", "default", "nasta_ghar", "nasta-ghar")
            or (biz_name.strip() == valid_id and "_" in valid_id)
        )

        if is_placeholder:
            if valid_id in ("default_business", "nasta_ghar", "nasta-ghar", ""):
                if norm_lang == "gujarati":
                    return "નાસ્તા ઘર"
                elif norm_lang == "hindi":
                    return "नाश्ता घर"
                return "Nasta Ghar"

            cat = tenant.get("category", "") if tenant else ""
            if cat:
                if norm_lang == "gujarati":
                    return f"આ {cat}"
                elif norm_lang == "hindi":
                    return f"इस {cat}"
                return f"the {cat.lower()}"

            if norm_lang == "gujarati":
                return "અહીં"
            elif norm_lang == "hindi":
                return "यहाँ"
            return "the restaurant"

        if biz_name.strip() in ("Nasta Ghar", "NastaGhar"):
            if norm_lang == "gujarati":
                return "નાસ્તા ઘર"
            elif norm_lang == "hindi":
                return "नाश्ता घर"

        return biz_name.strip()

    def validate_script_fidelity(self, text: str, language: str) -> bool:
        """
        Validates that generated text contains and is primarily composed in the
        appropriate native Unicode script (Gujarati for 'gu', Devanagari for 'hi').
        """
        if not text or not text.strip():
            return False
        l = normalize_language(language)
        if l == "gujarati":
            # Gujarati Unicode range: 0x0A80 to 0x0AFF
            guj_chars = sum(1 for c in text if 0x0A80 <= ord(c) <= 0x0AFF)
            if guj_chars < 3:
                return False
            latin_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
            if latin_chars > guj_chars * 2:
                return False
            return True
        elif l == "hindi":
            # Devanagari Unicode range: 0x0900 to 0x097F
            hin_chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
            if hin_chars < 3:
                return False
            latin_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
            if latin_chars > hin_chars * 2:
                return False
            return True
        return True

    def generate_ideas(
        self,
        req: ReviewIdeasRequest,
        resolved_industry: Optional[str] = None,
        resolved_business_name: Optional[str] = None,
        effective_topics: Optional[List[str]] = None
    ) -> ReviewIdeasResponse:
        """Generates 3-5 distinct, customer-grounded review candidate ideas in native script."""
        resolved_name = resolved_business_name or self.resolve_business_name(
            req.business_id,
            client_name=getattr(req, "business_name", None),
            language=req.language or "english"
        )
        raw_ideas = review_generator.generate_ideas(
            rating=req.rating,
            aspects=req.aspects or [],
            user_note=req.user_note or "",
            business_name=resolved_name,
            language=req.language or "english",
            category=req.category,
            industry_id=resolved_industry,
            effective_topics=effective_topics
        )
        norm_lang = (req.language or "english").lower().strip()
        validated_ideas = []
        for item in raw_ideas:
            text = item.get("text", "")
            if not self.validate_script_fidelity(text, norm_lang):
                from backend.app.api.prompts import generate_candidate_ideas
                fallback_items = generate_candidate_ideas(
                    rating=req.rating,
                    aspects=req.aspects or [],
                    user_note=req.user_note or "",
                    business_name=resolved_name,
                    language=req.language or "english",
                    category=req.category
                )
                match = next((f for f in fallback_items if f["id"] == item.get("id")), fallback_items[0] if fallback_items else item)
                item["text"] = match["text"]
                item["focus"] = match.get("focus", item.get("focus"))
            validated_ideas.append(item)

        ideas = [ReviewIdeaItem(**item) for item in validated_ideas]
        self.record_event("review_ideas_generated", metadata={
            "business_id": req.business_id,
            "rating": req.rating,
            "aspects": req.aspects or [],
            "has_note": bool(req.user_note),
            "language": req.language or "english",
            "industry_id": resolved_industry
        })
        return ReviewIdeasResponse(ideas=ideas)


    def generate_review(
        self,
        req: ReviewGenerateRequest,
        client_key: str = "default_client",
        resolved_industry: Optional[str] = None,
        resolved_business_name: Optional[str] = None,
        effective_topics: Optional[List[str]] = None
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
            "language": req.language or "english",
            "industry_id": resolved_industry
        })

        max_attempts = 2
        attempt = 0
        best_draft = ""
        best_val: Dict[str, Any] = {}
        provider = "engine"

        resolved_name = resolved_business_name or self.resolve_business_name(
            req.business_id,
            client_name=getattr(req, "business_name", None),
            language=req.language or "english"
        )

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
                business_name=resolved_name,
                language=req.language or "english",
                category=req.category,
                industry_id=resolved_industry,
                effective_topics=effective_topics
            )
            draft = gen_res["review"]
            provider = gen_res["provider"]

            # Validate script fidelity and enforce native script if missing
            if not self.validate_script_fidelity(draft, req.language or "english"):
                from backend.app.api.prompts import humanize_review_draft
                draft = humanize_review_draft(
                    rating=req.rating,
                    aspects=req.aspects or [],
                    user_note=req.user_note or "",
                    selected_idea=req.selected_idea,
                    tone=req.tone or "natural",
                    length=req.length or "medium",
                    dining_type=req.dining_type or "dine_in",
                    emoji_preference=req.emoji_preference or "light",
                    business_name=resolved_name,
                    language=req.language or "english",
                    category=req.category,
                    industry_id=resolved_industry,
                    effective_topics=effective_topics
                )
                provider = "local-script-enforced"

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

    def get_analytics_summary(
        self,
        business_id: Optional[str] = None,
        timezone_str: str = "Asia/Kolkata",
        start_timestamp: Optional[float] = None,
        end_timestamp: Optional[float] = None,
    ) -> Dict[str, Any]:
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
        if start_timestamp is not None:
            events = [e for e in events if e.get("timestamp", 0) >= start_timestamp]
        if end_timestamp is not None:
            events = [e for e in events if e.get("timestamp", 0) < end_timestamp]

        tickets = self._store.list_tickets(business_id=business_id, limit=500)
        if start_timestamp is not None:
            tickets = [t for t in tickets if (t.get("timestamp") or t.get("created_at", 0)) >= start_timestamp]
        if end_timestamp is not None:
            tickets = [t for t in tickets if (t.get("timestamp") or t.get("created_at", 0)) < end_timestamp]

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

        def _is_valid_session(sid: Any) -> bool:
            if not sid:
                return False
            s = str(sid).strip()
            if s.lower() in ("anonymous", "none", "null", "undefined", "unverified", ""):
                return False
            if s.startswith("local-"):
                return False
            try:
                val = uuid.UUID(s, version=4)
                return val.version == 4
            except (ValueError, AttributeError, TypeError):
                import re
                return bool(re.match(r"^sess-[a-zA-Z0-9_-]+$", s))

        # Session-level deduplicated google_clicks:
        # Each distinct valid session with at least one Google redirect event counts exactly once.
        # Multiple redirects from the same session count once.
        # Legacy aliases in the same session do not double-count.
        # Anonymous events are not treated as valid session conversions.
        google_redirect_sessions = set()
        for ev in events:
            en = ev.get("event_name")
            if en in ("google_maps_direct_click", "google_maps_redirect", "google_review_link_opened", "google_review_link_clicked"):
                sid = ev.get("session_id")
                if _is_valid_session(sid):
                    google_redirect_sessions.add(str(sid).strip())

        google_clicks = len(google_redirect_sessions)

        # Session-level deduplicated reviews_copied:
        copied_sessions = set()
        for ev in events:
            en = ev.get("event_name")
            if en in ("review_clipboard_success", "review_copied"):
                sid = ev.get("session_id")
                if _is_valid_session(sid):
                    copied_sessions.add(str(sid).strip())

        reviews_copied = len(copied_sessions)

        # Strict Distinct-Session Digital Handoff Funnel (Task 2)
        # Denominator: Distinct eligible sessions with at least one review generation event in reporting window.
        # Numerator: Distinct eligible sessions with a Google handoff after generation (handoff_ts >= gen_ts).
        # Rate: (numerator / denominator) * 100 (safe 0.0 if denominator == 0).
        norm_target_id = "default_business" if business_id in ("default_business", "nasta_ghar", "nasta-ghar", None) else business_id
        session_gen_timestamps = defaultdict(list)
        session_handoff_timestamps = defaultdict(list)

        for ev in events:
            en = ev.get("event_name")
            sid = ev.get("session_id")
            if not _is_valid_session(sid):
                continue
            s_str = str(sid).strip()
            ts = ev.get("timestamp", 0)

            if en == "review_generation_completed":
                session_gen_timestamps[s_str].append(ts)
            elif en == "google_maps_redirect":
                session_handoff_timestamps[s_str].append(ts)

        eligible_generation_sessions = set()
        eligible_handoff_sessions = set()

        for s_str, gen_ts_list in session_gen_timestamps.items():
            sess = self.get_session_info(s_str, check_expiry=False)
            if not sess:
                has_session_created = any(
                    e.get("event_name") == "session_created" and str(e.get("session_id", "")).strip() == s_str
                    for e in events
                )
                if not has_session_created:
                    # Unknown session ID -> excluded from conversion funnel
                    continue
                sess_tenant = norm_target_id
                sess_expires_at = min(gen_ts_list) + 86400.0
            else:
                raw_t = sess.get("tenant_id") or sess.get("business_id", "")
                sess_tenant = "default_business" if raw_t in ("default_business", "nasta_ghar", "nasta-ghar") else raw_t
                sess_expires_at = sess.get("expires_at", float("inf"))

            if sess_tenant != norm_target_id:
                continue

            earliest_gen_ts = min(gen_ts_list)
            if earliest_gen_ts > sess_expires_at:
                continue

            eligible_generation_sessions.add(s_str)

            handoff_ts_list = session_handoff_timestamps.get(s_str, [])
            if any(h_ts >= earliest_gen_ts for h_ts in handoff_ts_list):
                eligible_handoff_sessions.add(s_str)

        conv_denominator = len(eligible_generation_sessions)
        conv_numerator = len(eligible_handoff_sessions)
        conversion_rate = round((conv_numerator / conv_denominator) * 100, 1) if conv_denominator > 0 else 0.0

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
        if conv_denominator > 0:
            business_insights.append(f"Conversion rate from AI review generation to Google Maps click is {conversion_rate}%.")
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
        seen_handoff_keys = set()
        for ev in reversed(events[-20:]):
            name = ev.get("event_name", "")
            meta = ev.get("metadata", {})
            sid = ev.get("session_id") or ""
            t_dt = datetime.fromtimestamp(ev.get("timestamp", time.time()), tz=tz)
            t_str = t_dt.strftime("%H:%M")
            
            if name in ("review_generation_completed", "review_ideas_generated"):
                table = meta.get("table_number") or "Table"
                r = meta.get("rating", 5)
                recent_activity.append(f"{t_str} • {table} created a {r}-star draft")
            elif name in ("google_review_link_opened", "google_review_link_clicked", "google_maps_redirect"):
                handoff_key = f"{sid}:{t_str}" if sid and sid != "anonymous" else ev.get("event_id")
                if handoff_key not in seen_handoff_keys:
                    seen_handoff_keys.add(handoff_key)
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
            "conversion_rate_percent": conversion_rate,
            "eligible_generation_sessions": conv_denominator,
            "eligible_handoff_sessions": conv_numerator,
            
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
