"""
Google Review Link & Restaurant Configuration Management Module for ChurnLens.
Directs customers to the official business review page on Google Maps / Search.
ChurnLens does NOT submit reviews to Google directly via API;
the customer performs the final review submission.
"""

import os
import json
import copy
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict, is_dataclass
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

ALLOWED_GOOGLE_REVIEW_HOSTS = {
    "search.google.com",
    "maps.google.com",
    "www.google.com",
    "google.com",
    "g.page",
    "maps.app.goo.gl",
    "goo.gl",
}


def validate_google_review_url(url: Optional[str], allow_empty: bool = False) -> str:
    """
    Validates a Google Review URL strictly against approved criteria:
    - Must be a string (non-empty unless allow_empty=True)
    - Scheme must be HTTPS
    - Hostname must be in ALLOWED_GOOGLE_REVIEW_HOSTS (exact match)
    - Must not contain user credentials (username, password, @ in netloc)
    - Must not specify a non-standard port
    - Length must be <= 2000 chars
    """
    if url is None or (isinstance(url, str) and not url.strip()):
        if allow_empty:
            return ""
        raise ValueError("Google review URL is required and cannot be empty")

    if not isinstance(url, str):
        raise ValueError("Google review URL must be a string")

    cleaned_url = url.strip()
    if len(cleaned_url) > 2000:
        raise ValueError("Google review URL exceeds maximum length of 2000 characters")

    try:
        parsed = urlsplit(cleaned_url)
    except Exception as e:
        raise ValueError(f"Malformed Google review URL: {e}")

    scheme = (parsed.scheme or "").lower()
    if scheme != "https":
        raise ValueError(f"Google review URL must use HTTPS scheme, got '{scheme or 'none'}'")

    if "@" in parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Google review URL must not contain user credentials")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("Google review URL missing valid hostname")

    if hostname not in ALLOWED_GOOGLE_REVIEW_HOSTS:
        raise ValueError(
            f"Invalid Google review URL domain '{hostname}'. "
            f"Allowed domains: {sorted(ALLOWED_GOOGLE_REVIEW_HOSTS)}"
        )

    if parsed.port is not None and parsed.port != 443:
        raise ValueError(f"Google review URL must not use custom port '{parsed.port}'")

    return cleaned_url


def is_safe_google_review_url(url: Optional[str]) -> bool:
    """Check if a URL is an acceptable Google review URL without raising an exception."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    try:
        validate_google_review_url(url, allow_empty=False)
        return True
    except (ValueError, Exception):
        return False

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
        self._lock = threading.RLock()
        self._links: Dict[str, Dict[str, Any]] = {}
        self._last_cache_key = (0, 0)
        self._load_links()

    def _refresh_if_needed(self):
        source = CONFIG_FILE if CONFIG_FILE.exists() else SOURCE_CONFIG_FILE
        if source.exists():
            try:
                st = source.stat()
                cache_key = (st.st_mtime_ns, st.st_size)
                if cache_key != self._last_cache_key:
                    self._load_links()
            except OSError:
                pass

    def invalidate_cache(self):
        """Force a fresh load of configuration from disk, invalidating worker cache."""
        with self._lock:
            self._last_cache_key = (0, 0)
            self._load_links()

    def _load_links(self):
        with self._lock:
            source = CONFIG_FILE if CONFIG_FILE.exists() else SOURCE_CONFIG_FILE
            if source.exists():
                try:
                    st = source.stat()
                    self._last_cache_key = (st.st_mtime_ns, st.st_size)
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
            st = CONFIG_FILE.stat()
            self._last_cache_key = (st.st_mtime_ns, st.st_size)
        except Exception as e:
            raise RuntimeError("Could not persist restaurant configuration") from e

    def get_review_url(self, business_id: str, allow_default_fallback: bool = False) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._refresh_if_needed()
            # First attempt lookup in SQLite ReviewStore (authoritative database-backed resolution)
            from backend.app.core.database.storage import ReviewStore
            store = ReviewStore()
            tenant = store.get_tenant(business_id)
            if tenant:
                url = tenant.get("review_url") or os.getenv("GOOGLE_REVIEW_URL", "")
                if url and not is_safe_google_review_url(url):
                    logger.warning(
                        "[Security] Stored review URL '%s' for business '%s' is unsafe/invalid. Neutralizing to default.",
                        url, business_id
                    )
                    url = "https://maps.google.com"
                    is_configured = False
                else:
                    is_configured = bool(url.strip()) and url.strip() != "https://maps.google.com"
                if not url.strip():
                    url = "https://maps.google.com"
                category = tenant.get("category", "Breakfast & Snacks")
                explicit_ind = tenant.get("industry_id") or self._links.get(business_id, {}).get("industry_id")
                from backend.app.core.industry_registry import resolve_industry, resolve_effective_topics
                ind_def = resolve_industry(category=category, explicit_industry_id=explicit_ind)
                topics = tenant.get("topics")
                effective_topics = resolve_effective_topics(topics, ind_def.industry_id)
                return {
                    "business_id": business_id,
                    "platform": tenant.get("platform", "google"),
                    "review_url": url,
                    "is_configured": is_configured,
                    "business_name": tenant.get("business_name", "Nasta Ghar"),
                    "branch": tenant.get("branch", ""),
                    "category": category,
                    "industry_id": ind_def.industry_id,
                    "description": tenant.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
                    "topics": effective_topics,
                    "primary_accent": tenant.get("primary_accent", "#f97316"),
                    "domain": tenant.get("domain", ""),
                    "entitlements": tenant.get("entitlements", ["review_manager"]),
                    "status": tenant.get("status", "active"),
                    "logo_path": tenant.get("logo_path", ""),
                    "terminology": asdict(ind_def.terminology) if is_dataclass(ind_def.terminology) else ind_def.terminology,
                    "is_restricted": ind_def.is_restricted,
                    "restriction_notice": ind_def.restriction_notice
                }

            if business_id in ("default_business", "nasta_ghar", "nasta-ghar"):
                info = self._links.get(business_id) or self._links.get("default_business", {})
            elif business_id in self._links:
                info = self._links[business_id]
            elif allow_default_fallback:
                info = self._links.get("default_business", {})
            else:
                return None

            url = info.get("google_review_url") or os.getenv("GOOGLE_REVIEW_URL", "")
            if url and not is_safe_google_review_url(url):
                logger.warning(
                    "[Security] Config review URL '%s' for business '%s' is unsafe/invalid. Neutralizing to default.",
                    url, business_id
                )
                url = "https://maps.google.com"
                is_configured = False
            else:
                is_configured = bool(url.strip()) and url.strip() != "https://maps.google.com"
            if not url.strip():
                url = "https://maps.google.com"

            category = info.get("category", "Breakfast & Snacks")
            explicit_ind = info.get("industry_id")
            from backend.app.core.industry_registry import resolve_industry, resolve_effective_topics
            ind_def = resolve_industry(category=category, explicit_industry_id=explicit_ind)
            topics = info.get("topics") or get_category_topics(category)
            effective_topics = resolve_effective_topics(topics, ind_def.industry_id)

            return {
                "business_id": business_id,
                "platform": "google",
                "review_url": url,
                "is_configured": is_configured,
                "business_name": info.get("business_name", "Nasta Ghar"),
                "branch": info.get("branch", ""),
                "category": category,
                "industry_id": ind_def.industry_id,
                "description": info.get("description", "Authentic homestyle breakfast, chai, and snacks in Rajkot."),
                "topics": effective_topics,
                "primary_accent": info.get("primary_accent", "#f97316"),
                "domain": info.get("domain", ""),
                "entitlements": info.get("entitlements", ["review_manager"]),
                "status": info.get("status", "active"),
                "logo_path": info.get("logo_path", ""),
                "terminology": asdict(ind_def.terminology) if is_dataclass(ind_def.terminology) else ind_def.terminology,
                "is_restricted": ind_def.is_restricted,
                "restriction_notice": ind_def.restriction_notice
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
        status: Optional[str] = None,
        industry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            clean_review_url = validate_google_review_url(google_review_url, allow_empty=True)
            previous_links = copy.deepcopy(self._links)
            if business_id not in self._links:
                self._links[business_id] = {
                    "platform": "google",
                    "topics": DEFAULT_TOPICS
                }

            self._links[business_id]["google_review_url"] = clean_review_url
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
            if industry_id is not None:
                self._links[business_id]["industry_id"] = industry_id.strip().lower()

            try:
                self._save_links()
                # Mirror update to SQLite ReviewStore
                from backend.app.core.database.storage import ReviewStore
                store = ReviewStore()
                current_tenant = store.get_tenant(business_id)
                persisted_status = self._links[business_id].get(
                    "status",
                    current_tenant.get("status", "active") if current_tenant else "active"
                )
                cur_name = (business_name if business_name is not None else None) or (current_tenant.get("business_name") if current_tenant else None) or self._links[business_id].get("business_name") or "Nasta Ghar"
                cur_url = clean_review_url
                cur_branch = (branch if branch is not None else None) or (current_tenant.get("branch") if current_tenant and current_tenant.get("branch") is not None else None) or self._links[business_id].get("branch", "")
                cur_cat = (category if category is not None else None) or (current_tenant.get("category") if current_tenant else None) or self._links[business_id].get("category") or "Cafe"
                cur_desc = (description if description is not None else None) or (current_tenant.get("description") if current_tenant and current_tenant.get("description") is not None else None) or self._links[business_id].get("description", "")
                cur_topics = (list(topics) if topics is not None else None) or (current_tenant.get("topics") if current_tenant and current_tenant.get("topics") else None) or self._links[business_id].get("topics") or DEFAULT_TOPICS
                cur_accent = (primary_accent if primary_accent is not None else None) or (current_tenant.get("primary_accent") if current_tenant else None) or self._links[business_id].get("primary_accent") or "#f97316"
                cur_domain = (domain if domain is not None else None) or (current_tenant.get("domain") if current_tenant and current_tenant.get("domain") is not None else None) or self._links[business_id].get("domain", "")
                cur_entitlements = (list(entitlements) if entitlements is not None else None) or (current_tenant.get("entitlements") if current_tenant and current_tenant.get("entitlements") else None) or self._links[business_id].get("entitlements") or ["review_manager"]

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

                cur_ind = (industry_id if industry_id is not None else None) or (current_tenant.get("industry_id") if current_tenant else None) or self._links[business_id].get("industry_id")

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
                    "status": persisted_status,
                    "industry_id": cur_ind
                })

                # Synchronize shared identity fields to canonical business_profiles
                shared_update = {}
                if business_name is not None and str(business_name).strip():
                    shared_update["display_name"] = str(business_name).strip()
                if branch is not None:
                    shared_update["branch_name"] = str(branch).strip()
                if category is not None and str(category).strip():
                    shared_update["category"] = str(category).strip()
                if description is not None:
                    shared_update["description"] = str(description).strip()
                if shared_update:
                    store.update_shared_business_profile(business_id, shared_update)
            except Exception:
                self._links = previous_links
                raise
        return self.get_review_url(business_id)

google_review_manager = GoogleReviewManager()
