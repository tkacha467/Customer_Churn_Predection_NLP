import re
from urllib.parse import urlsplit
import zoneinfo
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any

class ReviewIdeaItem(BaseModel):
    id: str
    focus: str = "General"
    text: str

class ReviewIdeasRequest(BaseModel):
    business_id: str = Field(default="default_business", min_length=1, max_length=100, description="Unique cafe/restaurant identifier")
    business_name: Optional[str] = Field(default=None, description="Display name of business")
    rating: int = Field(..., ge=1, le=5, description="Guest star rating from 1 to 5")
    aspects: Optional[List[str]] = Field(default_factory=list, max_length=20, description="Hospitality aspects experienced (e.g. food, drinks, service, vibe)")
    user_note: Optional[str] = Field(default="", max_length=2000, description="Guest freeform notes or mentioned dishes/drinks")
    language: Optional[str] = Field(default="english", description="Customer language: english, hindi, gujarati")
    category: Optional[str] = Field(default=None, description="Hospitality category, e.g. Cafe, Restaurant, Hotel, Salon")

class ReviewIdeasResponse(BaseModel):
    ideas: List[ReviewIdeaItem]

class ReviewGenerateRequest(BaseModel):
    business_id: str = Field(default="default_business", min_length=1, max_length=100, description="Unique cafe/restaurant identifier")
    business_name: Optional[str] = Field(default=None, description="Display name of business")
    rating: int = Field(..., ge=1, le=5, description="Guest star rating from 1 to 5")
    aspects: Optional[List[str]] = Field(default_factory=list, max_length=20, description="Hospitality aspects experienced (e.g. coffee, food, service, vibe)")
    user_note: Optional[str] = Field(default="", max_length=2000, description="Guest freeform notes or mentioned dishes/drinks")
    selected_idea: Optional[str] = Field(default=None, max_length=5000, description="Starting idea card text selected by customer")
    tone: Optional[str] = Field(default="natural", description="Tone: natural, casual, foodie, professional, short, detailed")
    length: Optional[str] = Field(default="medium", description="Length: short, medium, detailed")
    dining_type: Optional[str] = Field(default="dine_in", description="Context: dine_in, coffee_break, brunch, lunch_dinner, takeaway")
    emoji_preference: Optional[str] = Field(default="light", description="Emoji preference: light, none, tasteful")
    table_number: Optional[str] = Field(default=None, description="Table identifier if scanned via table QR")
    session_id: Optional[str] = Field(default=None, description="Session tracker")
    language: Optional[str] = Field(default="english", description="Customer language: english, hindi, gujarati")
    category: Optional[str] = Field(default=None, description="Hospitality category, e.g. Cafe, Restaurant, Hotel, Salon")

class ReviewGenerateResponse(BaseModel):
    review: str
    sentiment: str
    sentiment_confidence: float
    rating_consistent: bool
    warnings: List[str] = Field(default_factory=list)
    aspects_covered: List[str] = Field(default_factory=list)
    dining_type: str = "dine_in"
    table_number: Optional[str] = None
    generation_provider: str = "hospitality_engine"

class ReviewValidateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating to compare against")
    review: str = Field(..., min_length=1, max_length=10000, description="Draft review text to validate")

class ReviewValidateResponse(BaseModel):
    sentiment: str
    confidence: float
    rating_consistent: bool
    warnings: List[str] = Field(default_factory=list)
    is_sarcastic: bool = False

class TerminologySchema(BaseModel):
    customer_noun_singular: str
    customer_noun_plural: str
    touchpoint_noun: str
    touchpoint_placeholder: str
    disclaimer_noun: str
    private_feedback_title: str

class BusinessReviewLinkResponse(BaseModel):
    business_id: str
    platform: str = "google"
    review_url: str
    is_configured: bool
    business_name: str = "Nasta Ghar"
    branch: Optional[str] = ""
    category: str = "Breakfast & Snacks"
    industry_id: Optional[str] = None
    description: Optional[str] = "Authentic homestyle breakfast, chai, and snacks in Rajkot."
    topics: Optional[List[str]] = Field(default_factory=lambda: [
        "Breakfast", "Chai & Beverages", "Snacks", "Taste & Flavour", "Friendly Staff", "Cleanliness", "Value for Money", "Quick Service"
    ])
    primary_accent: Optional[str] = "#f97316"
    domain: Optional[str] = ""
    entitlements: List[str] = Field(default_factory=lambda: ["review_manager", "digital_card"])
    logo_path: Optional[str] = ""
    terminology: Optional[TerminologySchema] = None

class BusinessConfigUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    google_review_url: str
    branch: Optional[str] = None
    category: Optional[str] = "Breakfast & Snacks"
    industry_id: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    topics: Optional[List[str]] = None
    primary_accent: Optional[str] = None
    domain: Optional[str] = None
    entitlements: Optional[List[str]] = None

class IndustryConfigResponse(BaseModel):
    business_id: str
    industry_id: str
    industry_name: str
    description: str
    subcategory: str
    subcategories: List[str]
    terminology: TerminologySchema
    default_topics: List[str]
    effective_topics: List[str]
    has_custom_topics: bool
    configuration_version: str
    available_features: List[str]
    analytics_labels: Dict[str, str] = Field(default_factory=dict)
    is_unclassified: bool = False

class IndustrySummaryItem(BaseModel):
    industry_id: str
    display_name: str
    description: str
    subcategories: List[str]
    default_subcategory: str
    default_topics: List[str]
    touchpoint_noun: str
    touchpoint_placeholder: str

class AvailableIndustriesResponse(BaseModel):
    industries: List[IndustrySummaryItem]
    count: int

class PreviewTokenRequest(BaseModel):
    business_id: str = "default_business"

class PreviewTokenResponse(BaseModel):
    preview_token: str
    traffic_source: str
    tenant_id: str
    expires_at: float

class ReviewSessionCreateRequest(BaseModel):
    business_id: str = "default_business"
    customer_ref: Optional[str] = None
    table_number: Optional[str] = None
    dining_type: Optional[str] = "dine_in"
    preview_token: Optional[str] = None
    is_preview: Optional[bool] = False

class ReviewSessionResponse(BaseModel):
    session_id: str
    business_id: str
    table_number: Optional[str] = None
    created_at: str
    traffic_source: str = "customer"
    is_preview: bool = False
    preview_token: Optional[str] = None

ALLOWED_ANALYTICS_EVENTS = {
    # Server-side events (recorded internally by ReviewService)
    "session_created",
    "review_ideas_generated",
    "review_generation_started",
    "review_generation_completed",
    "review_regenerated",
    "review_validation_passed",
    "review_validation_failed",
    "review_copied",
    "google_review_link_opened",
    "google_review_link_clicked",
    "private_feedback_submitted",
    # Client-side events (sent by CustomerReview.jsx via POST /reviews/events)
    "language_selected",
    "rating_selected",
    "aspects_selected",
    "review_selected",
    "idea_selected",
    "review_approved",
    "google_review_handoff_started",
    "review_clipboard_success",
    "review_clipboard_failed",
    "google_maps_redirect",
    "private_feedback_sent",
}

class AnalyticsEventRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=200)
    event_name: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    preview_token: Optional[str] = Field(default=None, max_length=500)
    idempotency_key: Optional[str] = Field(default=None, max_length=200)

# Manager reply & private feedback for backwards compatibility
class ManagerReplyRequest(BaseModel):
    guest_review: str = Field(..., min_length=1, max_length=10000, description="The guest review from Google or in-house")
    rating: int = Field(..., ge=1, le=5, description="Star rating given by guest")
    guest_name: Optional[str] = Field(default="Valued Guest", description="Name of the guest if available")
    manager_name: Optional[str] = Field(default="The General Management Team", description="Signing authority")
    tone: Optional[str] = Field(default="gracious", description="Tone: gracious, apologetic, warm, professional")

class ManagerReplyResponse(BaseModel):
    reply: str
    detected_sentiment: str
    recommended_action: str

class PrivateFeedbackRequest(BaseModel):
    business_id: str = Field(default="default_business", min_length=1, max_length=100)
    table_number: Optional[str] = Field(default=None, max_length=80)
    rating: int = Field(..., ge=1, le=5)
    diner_note: str = Field(..., min_length=1, max_length=5000, description="Direct guest feedback")
    aspects: Optional[List[str]] = Field(default_factory=list, max_length=20)
    guest_contact: Optional[str] = Field(default="", max_length=256, description="Email or phone for GM follow-up")

class PrivateFeedbackResponse(BaseModel):
    status: str = "received"
    ticket_id: str
    message: str

class OwnerLoginRequest(BaseModel):
    email: Optional[str] = Field(default=None, max_length=256)
    password: str = Field(..., min_length=1, max_length=256)
    tenant_id: Optional[str] = Field(default=None, max_length=100)

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str = ""
    is_platform_admin: bool = False

class TenantInfo(BaseModel):
    id: str
    business_name: str
    role: str

class AuthSessionResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    active_tenant: Optional[TenantInfo] = None
    available_tenants: List[TenantInfo] = Field(default_factory=list)

class SwitchTenantRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=100)

class TenantOnboardingRequest(BaseModel):
    tenant_id: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")
    business_name: str = Field(..., min_length=1, max_length=150)
    owner_email: str = Field(..., min_length=3, max_length=256)
    owner_password: str = Field(..., min_length=10, max_length=256)
    owner_name: Optional[str] = Field(default="", max_length=150)
    category: Optional[str] = Field(default="Cafe", max_length=100)
    review_url: Optional[str] = Field(default="", max_length=2000)
    branch: Optional[str] = Field(default="", max_length=100)
    description: Optional[str] = Field(default="", max_length=1000)
    primary_accent: Optional[str] = Field(default="#0ea5e9", max_length=20)
    domain: Optional[str] = Field(default="", max_length=256)
    topics: Optional[List[str]] = Field(default_factory=lambda: [
        "Taste & Flavour", "Quick Service", "Cleanliness", "Friendly Staff", "Value for Money"
    ])
    entitlements: Optional[List[str]] = Field(default_factory=lambda: ["review_manager", "digital_card"])
    status: Optional[str] = Field(default="active", pattern=r"^(active|suspended|inactive)$")

    @field_validator("entitlements")
    @classmethod
    def validate_entitlements(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return ["review_manager", "digital_card"]
        valid_set = {"review_manager", "digital_card"}
        cleaned = []
        for e in v:
            norm = str(e).strip().lower()
            if norm not in valid_set:
                raise ValueError(f"Invalid entitlement: '{e}'. Allowed entitlements are: {sorted(list(valid_set))}")
            if norm not in cleaned:
                cleaned.append(norm)
        return cleaned

class TenantOnboardingResponse(BaseModel):
    tenant_id: str
    business_name: str
    owner_email: str
    owner_user_id: str
    status: str
    entitlements: List[str]
    created: bool

class TenantStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(active|suspended|inactive)$")


class TenantEntitlementsUpdateRequest(BaseModel):
    entitlements: List[str] = Field(..., description="Module entitlements for the tenant")

    @field_validator("entitlements")
    @classmethod
    def validate_entitlements(cls, v: List[str]) -> List[str]:
        valid_set = {"review_manager", "digital_card"}
        cleaned = []
        for e in v:
            norm = str(e).strip().lower()
            if norm not in valid_set:
                raise ValueError(f"Invalid entitlement: '{e}'. Allowed entitlements are: {sorted(list(valid_set))}")
            if norm not in cleaned:
                cleaned.append(norm)
        return cleaned



# ---------------------------------------------------------
# Shared Business Profile & Document Schemas (Product 2 & Combined)
# ---------------------------------------------------------
PHONE_REGEX = re.compile(r"^[+]?[\d\s\-().]{5,25}$")


def normalize_url(url: Optional[str]) -> str:
    """Normalizes URL by stripping whitespace and ensuring an http(s) scheme."""
    if not url:
        return ""
    stripped = url.strip()
    if not stripped:
        return ""
    if not stripped.startswith(("http://", "https://")):
        return f"https://{stripped}"
    return stripped


class CustomLinkItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=1000)
    icon: Optional[str] = Field(default="link", max_length=50)

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Any) -> str:
        norm = normalize_url(str(v) if v is not None else "")
        if not norm:
            raise ValueError("Link URL cannot be empty")
        return norm


class BusinessProfileResponse(BaseModel):
    tenant_id: str
    tagline: str = ""
    display_name: str = ""
    branch_name: str = ""
    category: str = ""
    description: str = ""
    opening_hours: str = ""
    welcome_message: str = ""
    email: str = ""
    phone_number: str = ""
    website_url: str = ""
    address: str = ""
    map_url: str = ""
    whatsapp_url: str = ""
    whatsapp_group_url: str = ""
    instagram_url: str = ""
    facebook_url: str = ""
    youtube_url: str = ""
    logo_path: str = ""
    cover_image_path: str = ""
    background_preset: str = ""
    overlay_opacity: float = 0.75
    primary_accent: str = "#078BFF"
    brand_accent: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    custom_links: List[CustomLinkItem] = Field(default_factory=list)
    is_published: bool = False
    show_review_button: bool = True
    created_at: float
    updated_at: float


class BusinessProfileUpdateRequest(BaseModel):
    tagline: Optional[str] = Field(default=None, max_length=250)
    display_name: Optional[str] = Field(default=None, max_length=150)
    branch_name: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    opening_hours: Optional[str] = Field(default=None, max_length=150)
    welcome_message: Optional[str] = Field(default=None, max_length=1000)
    email: Optional[str] = Field(default=None, max_length=256)
    phone_number: Optional[str] = Field(default=None, max_length=25)
    website_url: Optional[str] = Field(default=None, max_length=500)
    address: Optional[str] = Field(default=None, max_length=500)
    map_url: Optional[str] = Field(default=None, max_length=2000)
    whatsapp_url: Optional[str] = Field(default=None, max_length=500)
    whatsapp_group_url: Optional[str] = Field(default=None, max_length=500)
    instagram_url: Optional[str] = Field(default=None, max_length=500)
    facebook_url: Optional[str] = Field(default=None, max_length=500)
    youtube_url: Optional[str] = Field(default=None, max_length=500)
    logo_path: Optional[str] = Field(default=None, max_length=500)
    cover_image_path: Optional[str] = Field(default=None, max_length=500)
    background_preset: Optional[str] = Field(default=None, max_length=100)
    overlay_opacity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    primary_accent: Optional[str] = Field(default=None, max_length=50)
    custom_links: Optional[List[CustomLinkItem]] = None
    is_published: Optional[bool] = None
    show_review_button: Optional[bool] = None

    @field_validator("website_url", "map_url", "whatsapp_url", "whatsapp_group_url", "instagram_url", "facebook_url", "youtube_url", mode="before")
    @classmethod
    def normalize_link_fields(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return normalize_url(str(v))

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        stripped = str(v).strip().lower()
        if not stripped:
            return ""
        if "@" not in stripped or "." not in stripped.split("@")[-1]:
            raise ValueError(f"Invalid email address: '{stripped}'")
        return stripped

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        stripped = str(v).strip()
        if not stripped:
            return ""
        if not PHONE_REGEX.match(stripped):
            raise ValueError(f"Invalid phone number format: '{stripped}'. Must be 5-25 digits/symbols.")
        return stripped


class DocumentMetadataResponse(BaseModel):
    id: str
    tenant_id: str
    document_type: str
    display_name: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    is_published: bool
    download_url: str = ""
    created_at: float
    updated_at: float


class DocumentUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=150)
    document_type: Optional[str] = Field(default=None, max_length=50)
    is_published: Optional[bool] = None

    @field_validator("display_name", mode="before")
    @classmethod
    def clean_display_name(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        cleaned = str(v).strip()
        if not cleaned:
            raise ValueError("Display name cannot be empty")
        return cleaned[:150]


class PublicDocumentItem(BaseModel):
    id: str
    document_type: str
    display_name: str
    file_size_bytes: int
    mime_type: str = "application/pdf"
    download_url: str


class PublicDigitalCardResponse(BaseModel):
    tenant_id: str
    business_name: str
    display_name: str = ""
    category: str = ""
    description: str = ""
    primary_accent: str = "#f97316"
    tagline: str = ""
    opening_hours: str = ""
    welcome_message: str = ""
    email: str = ""
    phone_number: str = ""
    website_url: str = ""
    address: str = ""
    map_url: str = ""
    whatsapp_url: str = ""
    whatsapp_group_url: str = ""
    instagram_url: str = ""
    facebook_url: str = ""
    youtube_url: str = ""
    logo_path: str = ""
    cover_image_path: str = ""
    background_preset: str = ""
    overlay_opacity: float = 0.75
    primary_accent: str = "#078BFF"
    custom_links: List[CustomLinkItem] = Field(default_factory=list)
    show_review_button: bool = True
    google_review_url: str = ""
    documents: List[PublicDocumentItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 2 Subpart 2C: Shared Business Profile Schemas (Canonical Common Identity)
# ---------------------------------------------------------------------------

class SharedBusinessProfileResponse(BaseModel):
    tenant_id: str
    display_name: str
    category: str
    branch_name: str = ""
    description: str = ""
    tagline: str = ""
    logo_path: str = ""
    phone_number: str = ""
    email: str = ""
    address: str = ""
    website_url: str = ""
    opening_hours: str = ""
    map_url: str = ""
    brand_accent: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    entitlements: List[str] = Field(default_factory=list)
    created_at: float
    updated_at: float


class SharedBusinessProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    branch_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    tagline: Optional[str] = Field(None, max_length=300)
    phone_number: Optional[str] = Field(None, max_length=40)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = Field(None, max_length=500)
    opening_hours: Optional[str] = Field(None, max_length=250)
    map_url: Optional[str] = Field(None, max_length=500)
    brand_accent: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=100)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("display_name must not be empty or whitespace-only.")
            # Preserve original casing verbatim
            return clean
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if clean not in zoneinfo.available_timezones():
                raise ValueError(f"Invalid IANA timezone identifier: '{clean}'.")
            return clean
        return v

    @field_validator("website_url", "map_url")
    @classmethod
    def validate_http_url(cls, v: Optional[str]) -> Optional[str]:
        """Strong URL validation using urllib.parse.urlsplit."""
        if v is None:
            return None
        clean = v.strip()
        if clean == "":
            return ""
        if any(c in clean for c in (" ", "\t", "\r", "\n")):
            raise ValueError("URL must not contain whitespace characters.")
        try:
            parsed = urlsplit(clean)
        except Exception as e:
            raise ValueError(f"Malformed URL: {e}")
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("URL must use http or https scheme.")
        if not parsed.netloc or not parsed.hostname:
            raise ValueError("URL must include a valid host domain.")
        if "." not in parsed.hostname and parsed.hostname != "localhost":
            raise ValueError("URL host must be a fully qualified domain name or localhost.")
        return clean

    @field_validator("brand_accent")
    @classmethod
    def validate_hex_accent(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "":
            clean = v.strip()
            if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", clean):
                raise ValueError("Brand accent must be a valid hex color string (e.g. #174D3A or #F00).")
            return clean
        return None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip().lower()
        if not stripped:
            return ""
        if "@" not in stripped or "." not in stripped.split("@")[-1]:
            raise ValueError(f"Invalid email address format: '{stripped}'.")
        return stripped


class SharedBusinessLogoUploadResponse(BaseModel):
    success: bool = True
    logo_path: str
    filename: str
    media_type: str
    size_bytes: int
    dimensions: Dict[str, int]
    sha256: str




