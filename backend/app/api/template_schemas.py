"""
Strict Pydantic v2 Schemas for Product A Dynamic Restaurant Template Configuration Foundation.
Enforces allowlisted component IDs, HEX color validation, approved font keys,
and sanitized trilingual localized content (English, Gujarati, Hindi).
"""
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# ─── ALLOWLISTS & VALIDATION CONSTANTS ─────────────────────────────────────────

HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")

DANGEROUS_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*style", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
]

APPROVED_COMPONENTS = {
    "business_header",
    "rating_selector",
    "topic_selector",
    "personal_note",
    "ai_suggestions",
    "review_editor",
    "google_handoff",
    "private_feedback",
}

APPROVED_HEADING_FONTS = {
    "playfair_display",
    "space_grotesk",
    "cormorant_garamond",
    "nunito",
    "inter",
    "system_ui",
}

APPROVED_BODY_FONTS = {
    "lato",
    "inter",
    "dm_sans",
    "nunito_sans",
    "system_ui",
}

APPROVED_GUJARATI_FONTS = {
    "noto_serif_gujarati",
    "noto_sans_gujarati",
    "shruti",
}

APPROVED_HINDI_FONTS = {
    "noto_serif_devanagari",
    "noto_sans_devanagari",
    "mangal",
    "mukta",
}

APPROVED_TOPICS = [
    "Food Quality",
    "Taste",
    "Freshness",
    "Presentation",
    "Service",
    "Staff Behaviour",
    "Ambience",
    "Cleanliness",
    "Value for Money",
]

APPROVED_HEADER_VARIANTS = {
    "centered_crest",
    "left_aligned_tech",
    "editorial_monogram",
    "illustrated_banner",
    "restaurant_classic",
    "restaurant_premium",
    "hotel_classic",
    "hotel_premium",
    "salon_classic",
    "salon_premium",
    "clinic_classic",
    "clinic_premium",
}

APPROVED_RATING_VARIANTS = {
    "classic_stars",
    "segmented_numeric",
    "refined_constellation",
    "bouncy_emoji_stars",
    "refined_stars",
}

APPROVED_TOPIC_SELECTOR_VARIANTS = {
    "outlined_chips",
    "compact_pills",
    "vertical_attribute_cards",
    "colorful_stickers",
    "compact_tags",
    "minimal_pills",
}

APPROVED_SUGGESTION_CARD_VARIANTS = {
    "framed_parchment",
    "dense_tech",
    "spacious_bronze",
    "speech_bubbles",
    "terminal_cards",
    "monochrome_editorial",
}

APPROVED_REVIEW_EDITOR_VARIANTS = {
    "editorial_salon",
    "tech_console",
    "minimalist_suite",
    "playful_card",
    "high_contrast_input",
}

APPROVED_BUTTON_VARIANTS = {
    "emerald_pill",
    "volt_block",
    "champagne_outline",
    "peach_rounded",
    "neon_cyber_pill",
}

APPROVED_SPACING_PRESETS = {
    "editorial",
    "compact",
    "premium",
    "friendly",
    "normal",
}

APPROVED_BORDER_RADIUS_PRESETS = {
    "none",
    "sm",
    "md",
    "lg",
    "full",
}

APPROVED_LAYOUT_DENSITIES = {
    "spacious",
    "compact",
    "normal",
}


def validate_no_injection(value: Any, field_name: str = "field") -> None:
    """Recursively checks that strings do not contain executable script or style tags."""
    if isinstance(value, str):
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(value):
                raise ValueError(f"Unsafe content detected in {field_name}: executable code or arbitrary HTML/CSS is forbidden.")
    elif isinstance(value, dict):
        for k, v in value.items():
            validate_no_injection(k, f"{field_name}.key")
            validate_no_injection(v, f"{field_name}[{k}]")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            validate_no_injection(item, f"{field_name}[{i}]")


# ─── SUB-SCHEMAS ─────────────────────────────────────────────────────────────

class VisualTokensConfig(BaseModel):
    background_color: str = Field(..., description="Canvas background HEX color")
    card_surface_color: str = Field(..., description="Card surface background HEX color")
    primary_accent: str = Field(..., description="Primary accent HEX color")
    secondary_accent: str = Field(..., description="Secondary accent HEX color")
    text_color: str = Field(default="#1A241E", description="Main text HEX color")
    border_color: str = Field(default="#E5DEC9", description="Border/divider HEX color")
    heading_font_key: str = Field(default="playfair_display", description="Approved heading font key")
    body_font_key: str = Field(default="lato", description="Approved body font key")
    gujarati_font_key: str = Field(default="noto_serif_gujarati", description="Approved Gujarati font key")
    hindi_font_key: str = Field(default="noto_serif_devanagari", description="Approved Hindi font key")

    @field_validator("background_color", "card_surface_color", "primary_accent", "secondary_accent", "text_color", "border_color")
    @classmethod
    def validate_hex_colors(cls, v: str) -> str:
        if not v or not HEX_COLOR_REGEX.match(v.strip()):
            raise ValueError(f"Invalid HEX color format '{v}'. Expected #RRGGBB or #RRGGBBAA.")
        return v.strip().lower()

    @field_validator("heading_font_key")
    @classmethod
    def validate_heading_font(cls, v: str) -> str:
        k = v.lower().strip()
        if k not in APPROVED_HEADING_FONTS:
            raise ValueError(f"Font key '{v}' is not an approved heading font. Allowed: {sorted(APPROVED_HEADING_FONTS)}")
        return k

    @field_validator("body_font_key")
    @classmethod
    def validate_body_font(cls, v: str) -> str:
        k = v.lower().strip()
        if k not in APPROVED_BODY_FONTS:
            raise ValueError(f"Font key '{v}' is not an approved body font. Allowed: {sorted(APPROVED_BODY_FONTS)}")
        return k

    @field_validator("gujarati_font_key")
    @classmethod
    def validate_gujarati_font(cls, v: str) -> str:
        k = v.lower().strip()
        if k not in APPROVED_GUJARATI_FONTS:
            raise ValueError(f"Font key '{v}' is not an approved Gujarati font. Allowed: {sorted(APPROVED_GUJARATI_FONTS)}")
        return k

    @field_validator("hindi_font_key")
    @classmethod
    def validate_hindi_font(cls, v: str) -> str:
        k = v.lower().strip()
        if k not in APPROVED_HINDI_FONTS:
            raise ValueError(f"Font key '{v}' is not an approved Hindi font. Allowed: {sorted(APPROVED_HINDI_FONTS)}")
        return k


class LayoutConfig(BaseModel):
    header_variant: str = Field(default="centered_crest")
    rating_variant: str = Field(default="classic_stars")
    topic_selector_variant: str = Field(default="outlined_chips")
    review_suggestion_card_variant: str = Field(default="framed_parchment")
    review_editor_variant: str = Field(default="editorial_salon")
    button_variant: str = Field(default="emerald_pill")
    spacing_preset: str = Field(default="editorial")
    border_radius_preset: str = Field(default="md")
    layout_density: str = Field(default="normal")

    @field_validator("header_variant")
    @classmethod
    def validate_header_variant(cls, v: str) -> str:
        validate_no_injection(v, "header_variant")
        k = v.strip().lower()
        if k not in APPROVED_HEADER_VARIANTS:
            raise ValueError(f"Header variant '{v}' is not approved. Allowed: {sorted(APPROVED_HEADER_VARIANTS)}")
        return k

    @field_validator("rating_variant")
    @classmethod
    def validate_rating_variant(cls, v: str) -> str:
        validate_no_injection(v, "rating_variant")
        k = v.strip().lower()
        if k not in APPROVED_RATING_VARIANTS:
            raise ValueError(f"Rating variant '{v}' is not approved. Allowed: {sorted(APPROVED_RATING_VARIANTS)}")
        return k

    @field_validator("topic_selector_variant")
    @classmethod
    def validate_topic_selector_variant(cls, v: str) -> str:
        validate_no_injection(v, "topic_selector_variant")
        k = v.strip().lower()
        if k not in APPROVED_TOPIC_SELECTOR_VARIANTS:
            raise ValueError(f"Topic selector variant '{v}' is not approved. Allowed: {sorted(APPROVED_TOPIC_SELECTOR_VARIANTS)}")
        return k

    @field_validator("review_suggestion_card_variant")
    @classmethod
    def validate_card_variant(cls, v: str) -> str:
        validate_no_injection(v, "review_suggestion_card_variant")
        k = v.strip().lower()
        if k not in APPROVED_SUGGESTION_CARD_VARIANTS:
            raise ValueError(f"Review suggestion card variant '{v}' is not approved. Allowed: {sorted(APPROVED_SUGGESTION_CARD_VARIANTS)}")
        return k

    @field_validator("review_editor_variant")
    @classmethod
    def validate_editor_variant(cls, v: str) -> str:
        validate_no_injection(v, "review_editor_variant")
        k = v.strip().lower()
        if k not in APPROVED_REVIEW_EDITOR_VARIANTS:
            raise ValueError(f"Review editor variant '{v}' is not approved. Allowed: {sorted(APPROVED_REVIEW_EDITOR_VARIANTS)}")
        return k

    @field_validator("button_variant")
    @classmethod
    def validate_button_variant(cls, v: str) -> str:
        validate_no_injection(v, "button_variant")
        k = v.strip().lower()
        if k not in APPROVED_BUTTON_VARIANTS:
            raise ValueError(f"Button variant '{v}' is not approved. Allowed: {sorted(APPROVED_BUTTON_VARIANTS)}")
        return k

    @field_validator("spacing_preset")
    @classmethod
    def validate_spacing_preset(cls, v: str) -> str:
        validate_no_injection(v, "spacing_preset")
        k = v.strip().lower()
        if k not in APPROVED_SPACING_PRESETS:
            raise ValueError(f"Spacing preset '{v}' is not approved. Allowed: {sorted(APPROVED_SPACING_PRESETS)}")
        return k

    @field_validator("border_radius_preset")
    @classmethod
    def validate_border_radius_preset(cls, v: str) -> str:
        validate_no_injection(v, "border_radius_preset")
        k = v.strip().lower()
        if k not in APPROVED_BORDER_RADIUS_PRESETS:
            raise ValueError(f"Border radius preset '{v}' is not approved. Allowed: {sorted(APPROVED_BORDER_RADIUS_PRESETS)}")
        return k

    @field_validator("layout_density")
    @classmethod
    def validate_layout_density(cls, v: str) -> str:
        validate_no_injection(v, "layout_density")
        k = v.strip().lower()
        if k not in APPROVED_LAYOUT_DENSITIES:
            raise ValueError(f"Layout density '{v}' is not approved. Allowed: {sorted(APPROVED_LAYOUT_DENSITIES)}")
        return k


class LocalizedStringsBlock(BaseModel):
    welcome_title: Optional[str] = None
    welcome_subtitle: Optional[str] = None
    rating_prompt: Optional[str] = None
    topics_title: Optional[str] = None
    topics_subtitle: Optional[str] = None
    suggestions_title: Optional[str] = None
    cta_button: Optional[str] = None
    thank_you: Optional[str] = None


class LocalizedContentConfig(BaseModel):
    en: Dict[str, Any] = Field(default_factory=dict)
    gu: Dict[str, Any] = Field(default_factory=dict)
    hi: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_localized_strings(self) -> "LocalizedContentConfig":
        for lang in ("en", "gu", "hi"):
            block = getattr(self, lang, {})
            validate_no_injection(block, f"localized_content.{lang}")
        return self


class TemplateConfigurationPayload(BaseModel):
    schema_version: str = Field(default="1.0", description="Schema version identifier")
    theme: VisualTokensConfig
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    components: List[str] = Field(
        default_factory=lambda: [
            "business_header", "rating_selector", "topic_selector",
            "personal_note", "ai_suggestions", "review_editor",
            "google_handoff", "private_feedback"
        ]
    )
    topics: List[Dict[str, Any]] = Field(default_factory=list)
    rating_labels: Dict[str, Any] = Field(default_factory=dict)
    experience_labels: Dict[str, Any] = Field(default_factory=dict)
    localized_content: LocalizedContentConfig = Field(default_factory=LocalizedContentConfig)

    @field_validator("components")
    @classmethod
    def validate_component_list(cls, components: List[str]) -> List[str]:
        for comp in components:
            if comp not in APPROVED_COMPONENTS:
                raise ValueError(
                    f"Component '{comp}' is not an approved component identifier. "
                    f"Allowed components: {sorted(APPROVED_COMPONENTS)}"
                )
        if "google_handoff" not in components:
            raise ValueError(
                "Anti-gating compliance violation: 'google_handoff' is mandatory and cannot be omitted from template components."
            )
        return components

    @model_validator(mode="after")
    def check_all_payload_injections(self) -> "TemplateConfigurationPayload":
        validate_no_injection(self.topics, "topics")
        validate_no_injection(self.rating_labels, "rating_labels")
        validate_no_injection(self.experience_labels, "experience_labels")
        return self


# ─── API DTO SCHEMAS ─────────────────────────────────────────────────────────

class IndustryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str = ""
    icon: str = "🏢"
    status: str = "active"


class TemplateResponse(BaseModel):
    id: str
    industry_id: str
    industry_name: Optional[str] = None
    industry_slug: Optional[str] = None
    industry_icon: Optional[str] = None
    name: str
    slug: str
    description: str = ""
    status: str = "active"
    active_version_id: Optional[str] = None
    active_version: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TemplateVersionResponse(BaseModel):
    id: str
    template_id: str
    version: str
    schema_version: str = "1.0"
    publication_status: str  # draft | published | archived
    published_at: Optional[float] = None
    created_at: float
    created_by: str = "system"
    configuration: Dict[str, Any] = Field(default_factory=dict)


class CreateDraftVersionRequest(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version string, e.g. 1.1.0")
    configuration: TemplateConfigurationPayload


class UpdateDraftVersionRequest(BaseModel):
    configuration: TemplateConfigurationPayload


class AssignTemplateRequest(BaseModel):
    template_id: str
    version_id: Optional[str] = None


class UpgradeAssignmentRequest(BaseModel):
    target_version_id: str


class UpdateBusinessConfigRequest(BaseModel):
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    primary_accent: Optional[str] = None
    custom_topics: Optional[List[Dict[str, Any]]] = None
    localized_content: Optional[Dict[str, Any]] = None
    google_review_url: Optional[str] = None

    @field_validator("primary_accent")
    @classmethod
    def validate_accent(cls, v: Optional[str]) -> Optional[str]:
        if v and not HEX_COLOR_REGEX.match(v.strip()):
            raise ValueError(f"Invalid primary accent HEX color: '{v}'")
        return v.strip().lower() if v else v

    @model_validator(mode="after")
    def validate_no_xss(self) -> "UpdateBusinessConfigRequest":
        if self.custom_topics:
            validate_no_injection(self.custom_topics, "custom_topics")
        if self.localized_content:
            validate_no_injection(self.localized_content, "localized_content")
        return self


class PublicBusinessConfigResponse(BaseModel):
    businessId: str
    businessName: str
    category: str
    googleReviewUrl: str
    antiGatingCompliant: bool = True
    industry: Dict[str, Any]
    template: Dict[str, Any]
    theme: Dict[str, Any]
    layout: Dict[str, Any] = Field(default_factory=dict)
    components: List[str] = Field(default_factory=list)
    topics: List[Dict[str, Any]]
    ratingLabels: Dict[str, Any]
    experienceLabels: Dict[str, Any]
    localizedContent: Dict[str, Any]
