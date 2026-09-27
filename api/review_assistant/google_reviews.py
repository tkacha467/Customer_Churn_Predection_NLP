"""
Google Review Link & Restaurant Configuration Management Module for ChurnLens.
Directs customers to the official business review page on Google Maps / Search.
ChurnLens does NOT submit reviews to Google directly via API;
the customer performs the final review submission.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

CONFIG_FILE = Path(__file__).parent / "business_links.json"

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

class GoogleReviewManager:
    def __init__(self):
        self._links: Dict[str, Dict[str, Any]] = {}
        self._load_links()

    def _load_links(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
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
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._links, f, indent=2)
        except Exception as e:
            print(f"[GoogleReviewManager] Error saving links: {e}")

    def get_review_url(self, business_id: str) -> Dict[str, Any]:
        info = self._links.get(business_id) or self._links.get("default_business", {})
        url = info.get("google_review_url") or os.getenv("GOOGLE_REVIEW_URL", "")
        
        is_configured = bool(url.strip()) and url.strip() != "https://maps.google.com"
        if not url.strip():
            url = "https://maps.google.com"

        return {
            "business_id": business_id,
            "platform": "google",
            "review_url": url,
            "is_configured": is_configured,
            "business_name": info.get("business_name", "Nasta Ghar"),
            "branch": info.get("branch", ""),
            "category": info.get("category", "Breakfast & Snacks"),
            "description": info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
            "topics": info.get("topics", DEFAULT_TOPICS),
            "primary_accent": info.get("primary_accent", "#f97316")
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
        primary_accent: Optional[str] = None
    ) -> Dict[str, Any]:
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
        
        self._save_links()
        return self.get_review_url(business_id)

google_review_manager = GoogleReviewManager()
