from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReviewIdeaItem(BaseModel):
    id: str
    focus: str = "General"
    text: str

class ReviewIdeasRequest(BaseModel):
    business_id: str = Field(default="default_business", min_length=1, max_length=100, description="Unique cafe/restaurant identifier")
    rating: int = Field(..., ge=1, le=5, description="Guest star rating from 1 to 5")
    aspects: Optional[List[str]] = Field(default_factory=list, max_length=20, description="Hospitality aspects experienced (e.g. food, drinks, service, vibe)")
    user_note: Optional[str] = Field(default="", max_length=2000, description="Guest freeform notes or mentioned dishes/drinks")

class ReviewIdeasResponse(BaseModel):
    ideas: List[ReviewIdeaItem]

class ReviewGenerateRequest(BaseModel):
    business_id: str = Field(default="default_business", min_length=1, max_length=100, description="Unique cafe/restaurant identifier")
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

class BusinessReviewLinkResponse(BaseModel):
    business_id: str
    platform: str = "google"
    review_url: str
    is_configured: bool
    business_name: str = "Nasta Ghar"
    branch: Optional[str] = ""
    category: str = "Breakfast & Snacks"
    description: Optional[str] = "Authentic homestyle breakfast, chai, and snacks in Rajkot."
    topics: Optional[List[str]] = Field(default_factory=lambda: [
        "Breakfast", "Chai & Beverages", "Snacks", "Taste & Flavour", "Friendly Staff", "Cleanliness", "Value for Money", "Quick Service"
    ])
    primary_accent: Optional[str] = "#f97316"

class BusinessConfigUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    google_review_url: str
    branch: Optional[str] = None
    category: Optional[str] = "Breakfast & Snacks"
    description: Optional[str] = None
    tagline: Optional[str] = None
    topics: Optional[List[str]] = None
    primary_accent: Optional[str] = None

class ReviewSessionCreateRequest(BaseModel):
    business_id: str = "default_business"
    customer_ref: Optional[str] = None
    table_number: Optional[str] = None
    dining_type: Optional[str] = "dine_in"

class ReviewSessionResponse(BaseModel):
    session_id: str
    business_id: str
    table_number: Optional[str] = None
    created_at: str

ALLOWED_ANALYTICS_EVENTS = {
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
}

class AnalyticsEventRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=200)
    event_name: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

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
    password: str = Field(..., min_length=1, max_length=256)
