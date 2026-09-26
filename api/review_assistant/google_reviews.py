"""
Google Review Link Management Module for ChurnLens.
Directs customers to the official business review page on Google Maps / Search.
ChurnLens does NOT submit reviews to Google directly via API;
the customer performs the final review submission.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE = Path(__file__).parent / "business_links.json"

# Default fallback if nothing configured
DEFAULT_URL = os.getenv("GOOGLE_REVIEW_URL", "")

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
            default_env = os.getenv("GOOGLE_REVIEW_URL", "")
            self._links["default_business"] = {
                "business_name": "Demo Showcase Business",
                "google_review_url": default_env,
                "platform": "google"
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
        
        # If still empty, provide a clean search placeholder or instructions
        is_configured = bool(url.strip())
        if not is_configured:
            # Fallback URL that safely opens Google Maps search
            url = "https://maps.google.com"

        return {
            "business_id": business_id,
            "platform": "google",
            "review_url": url,
            "is_configured": is_configured,
            "business_name": info.get("business_name", "Business")
        }

    def update_business_config(self, business_id: str, google_review_url: str, business_name: str = None) -> Dict[str, Any]:
        if business_id not in self._links:
            self._links[business_id] = {
                "platform": "google"
            }
        
        self._links[business_id]["google_review_url"] = google_review_url.strip()
        if business_name:
            self._links[business_id]["business_name"] = business_name.strip()
        
        self._save_links()
        return self.get_review_url(business_id)

google_review_manager = GoogleReviewManager()
