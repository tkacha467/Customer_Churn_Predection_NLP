"""
Google Review Link & Restaurant Configuration Management Module for ChurnLens.
Directs customers to the official business review page on Google Maps / Search.
ChurnLens does NOT submit reviews to Google directly via API;
the customer performs the final review submission.
"""

import os
import json
import copy
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

SOURCE_CONFIG_FILE = Path(__file__).parent / "business_links.json"
CONFIG_FILE = Path(os.getenv("BUSINESS_LINKS_PATH", str(SOURCE_CONFIG_FILE))).expanduser()

DEFAULT_TOPICS = [
    "Breakfast",
    "Chai & Beverages",
    "Snacks",
    "Taste & Flavour",
    "Friendly Staff",
    "Cleanliness",
    "Value for Money",
    "Quick Service"
]

HOSPITALITY_CATEGORY_TOPICS: Dict[str, List[str]] = {
    "cafe": [
        "Food & Taste",
        "Chai / Coffee",
        "Staff",
        "Service",
        "Ambience",
        "Cleanliness",
        "Value for Money",
    ],
    "restaurant": [
        "Food & Taste",
        "Service",
        "Staff",
        "Ambience",
        "Cleanliness",
        "Portion Size",
        "Value for Money",
    ],
    "hotel": [
        "Room",
        "Cleanliness",
        "Staff",
        "Service",
        "Breakfast",
        "Location",
        "Comfort",
        "Ambience",
    ],
    "salon": [
        "Service",
        "Staff",
        "Cleanliness",
        "Experience",
        "Results",
        "Ambience",
    ],
    "breakfast & snacks": [
        "Breakfast",
        "Chai & Beverages",
        "Snacks",
        "Taste & Flavour",
        "Friendly Staff",
        "Cleanliness",
        "Value for Money",
        "Quick Service",
    ],
}

def get_category_topics(category: Optional[str]) -> List[str]:
    if not category:
        return DEFAULT_TOPICS
    cat_lower = category.lower().strip()
    for key, topics in HOSPITALITY_CATEGORY_TOPICS.items():
        if key in cat_lower or cat_lower in key:
            return list(topics)
    return list(DEFAULT_TOPICS)

class GoogleReviewManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._links: Dict[str, Dict[str, Any]] = {}
        self._load_links()

    def _load_links(self):
        with self._lock:
            source = CONFIG_FILE if CONFIG_FILE.exists() else SOURCE_CONFIG_FILE
            if source.exists():
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        self._links = json.load(f)
                except Exception as e:
                    print(f"[GoogleReviewManager] Error loading links: {e}")
                    self._links = {}

            # Ensure default business entry exists
            if "default_business" not in self._links:
                default_env = os.getenv("GOOGLE_REVIEW_URL", "https://maps.google.com")
                self._links["default_business"] = {
                    "business_name": "Nasta Ghar",
                    "branch": "",
                    "category": "Breakfast & Snacks",
                    "description": "Authentic homestyle breakfast, chai, and snacks in Rajkot.",
                    "google_review_url": default_env,
                    "platform": "google",
                    "topics": DEFAULT_TOPICS,
                    "primary_accent": "#f97316"
                }

    def _save_links(self):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            temporary = CONFIG_FILE.with_name(
                f"{CONFIG_FILE.name}.{os.getpid()}.{threading.get_ident()}.{id(self)}.tmp"
            )
            with open(temporary, "w", encoding="utf-8") as f:
                json.dump(self._links, f, indent=2)
            temporary.replace(CONFIG_FILE)
        except Exception as e:
            raise RuntimeError("Could not persist restaurant configuration") from e

    def get_review_url(self, business_id: str, allow_default_fallback: bool = False) -> Optional[Dict[str, Any]]:
        with self._lock:
            # First attempt lookup in SQLite ReviewStore
            from api.review_assistant.storage import ReviewStore
            store = ReviewStore()
            tenant = store.get_tenant(business_id)
            if tenant:
                url = tenant.get("review_url") or os.getenv("GOOGLE_REVIEW_URL", "")
                is_configured = bool(url.strip()) and url.strip() != "https://maps.google.com"
                if not url.strip():
                    url = "https://maps.google.com"
                category = tenant.get("category", "Breakfast & Snacks")
                topics = tenant.get("topics") or get_category_topics(category)
                return {
                    "business_id": business_id,
                    "platform": tenant.get("platform", "google"),
                    "review_url": url,
                    "is_configured": is_configured,
                    "business_name": tenant.get("business_name", "Nasta Ghar"),
                    "branch": tenant.get("branch", ""),
                    "category": category,
                    "description": tenant.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
                    "topics": topics,
                    "primary_accent": tenant.get("primary_accent", "#f97316"),
                    "domain": tenant.get("domain", ""),
                    "entitlements": tenant.get("entitlements", ["review_manager", "digital_card"]),
                    "status": tenant.get("status", "active")
                }

            if business_id in ("default_business", "nasta_ghar"):
                info = self._links.get(business_id) or self._links.get("default_business", {})
            elif business_id in self._links:
                info = self._links[business_id]
            elif allow_default_fallback:
                info = self._links.get("default_business", {})
            else:
                return None

            url = info.get("google_review_url") or os.getenv("GOOGLE_REVIEW_URL", "")
            is_configured = bool(url.strip()) and url.strip() != "https://maps.google.com"
            if not url.strip():
                url = "https://maps.google.com"

            category = info.get("category", "Breakfast & Snacks")
            topics = info.get("topics") or get_category_topics(category)

            return {
                "business_id": business_id,
                "platform": "google",
                "review_url": url,
                "is_configured": is_configured,
                "business_name": info.get("business_name", "Nasta Ghar"),
                "branch": info.get("branch", ""),
                "category": category,
                "description": info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
                "topics": topics,
                "primary_accent": info.get("primary_accent", "#f97316"),
                "domain": info.get("domain", ""),
                "entitlements": info.get("entitlements", ["review_manager", "digital_card"]),
                "status": info.get("status", "active")
            }

    def update_business_config(
        self,
        business_id: str,
        google_review_url: str,
        business_name: Optional[str] = None,
        branch: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        primary_accent: Optional[str] = None,
        domain: Optional[str] = None,
        entitlements: Optional[List[str]] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            previous_links = copy.deepcopy(self._links)
            if business_id not in self._links:
                self._links[business_id] = {
                    "platform": "google",
                    "topics": DEFAULT_TOPICS
                }

            self._links[business_id]["google_review_url"] = google_review_url.strip()
            if business_name:
                self._links[business_id]["business_name"] = business_name.strip()
            if branch is not None:
                self._links[business_id]["branch"] = branch.strip()
            if category is not None:
                self._links[business_id]["category"] = category.strip()
            if description is not None:
                self._links[business_id]["description"] = description.strip()
            if topics is not None:
                self._links[business_id]["topics"] = [t.strip() for t in topics if t.strip()]
            if primary_accent is not None:
                self._links[business_id]["primary_accent"] = primary_accent.strip()
            if domain is not None:
                self._links[business_id]["domain"] = domain.strip().lower()
            if entitlements is not None:
                self._links[business_id]["entitlements"] = list(entitlements)
            if status is not None:
                self._links[business_id]["status"] = status.strip()

            try:
                self._save_links()
                # Mirror update to SQLite ReviewStore
                from api.review_assistant.storage import ReviewStore
                store = ReviewStore()
                current_tenant = store.get_tenant(business_id)
                persisted_status = self._links[business_id].get(
                    "status",
                    current_tenant.get("status", "active") if current_tenant else "active"
                )
                cur_name = (business_name if business_name is not None else None) or (current_tenant.get("business_name") if current_tenant else None) or self._links[business_id].get("business_name") or "Nasta Ghar"
                cur_url = (google_review_url if google_review_url is not None else None) or (current_tenant.get("review_url") if current_tenant else None) or self._links[business_id].get("google_review_url", "")
                cur_branch = (branch if branch is not None else None) or (current_tenant.get("branch") if current_tenant and current_tenant.get("branch") is not None else None) or self._links[business_id].get("branch", "")
                cur_cat = (category if category is not None else None) or (current_tenant.get("category") if current_tenant else None) or self._links[business_id].get("category") or "Cafe"
                cur_desc = (description if description is not None else None) or (current_tenant.get("description") if current_tenant and current_tenant.get("description") is not None else None) or self._links[business_id].get("description", "")
                cur_topics = (list(topics) if topics is not None else None) or (current_tenant.get("topics") if current_tenant and current_tenant.get("topics") else None) or self._links[business_id].get("topics") or DEFAULT_TOPICS
                cur_accent = (primary_accent if primary_accent is not None else None) or (current_tenant.get("primary_accent") if current_tenant else None) or self._links[business_id].get("primary_accent") or "#f97316"
                cur_domain = (domain if domain is not None else None) or (current_tenant.get("domain") if current_tenant and current_tenant.get("domain") is not None else None) or self._links[business_id].get("domain", "")
                cur_entitlements = (list(entitlements) if entitlements is not None else None) or (current_tenant.get("entitlements") if current_tenant and current_tenant.get("entitlements") else None) or self._links[business_id].get("entitlements") or ["review_manager", "digital_card"]

                # Keep in-memory cache synchronized with the authoritative state
                self._links[business_id]["topics"] = cur_topics
                self._links[business_id]["business_name"] = cur_name
                self._links[business_id]["category"] = cur_cat
                self._links[business_id]["primary_accent"] = cur_accent
                if cur_branch:
                    self._links[business_id]["branch"] = cur_branch
                if cur_desc:
                    self._links[business_id]["description"] = cur_desc
                if cur_domain:
                    self._links[business_id]["domain"] = cur_domain

                store.upsert_tenant({
                    "id": business_id,
                    "business_name": cur_name,
                    "review_url": cur_url,
                    "branch": cur_branch,
                    "category": cur_cat,
                    "description": cur_desc,
                    "topics": cur_topics,
                    "primary_accent": cur_accent,
                    "platform": self._links[business_id].get("platform", "google"),
                    "domain": cur_domain,
                    "entitlements": cur_entitlements,
                    "status": persisted_status
                })
            except Exception:
                self._links = previous_links
                raise
        return self.get_review_url(business_id)

google_review_manager = GoogleReviewManager()
