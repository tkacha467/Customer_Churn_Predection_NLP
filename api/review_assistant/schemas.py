from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReviewGenerateRequest(BaseModel):
    business_id: str = Field(default="default_business", description="Unique cafe/restaurant identifier")
    rating: int = Field(..., ge=1, le=5, description="Guest star rating from 1 to 5")
    aspects: Optional[List[str]] = Field(default_factory=list, description="Hospitality aspects experienced (e.g. coffee, food, service, vibe)")
    user_note: Optional[str] = Field(default="", description="Guest freeform notes or mentioned dishes/drinks")
    tone: Optional[str] = Field(default="natural", description="Tone: natural, casual, foodie, professional, short, detailed")
    length: Optional[str] = Field(default="medium", description="Length: short, medium, detailed")
    dining_type: Optional[str] = Field(default="dine_in", description="Context: dine_in, coffee_break, brunch, lunch_dinner, takeaway")
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
    review: str = Field(..., min_length=1, description="Draft review text to validate")

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
    business_name: str = "Cafe / Restaurant"
    category: str = "Hospitality & Dining"

class BusinessConfigUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    google_review_url: str
    category: Optional[str] = "Artisan Cafe & Roastery"
    tagline: Optional[str] = None

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

class AnalyticsEventRequest(BaseModel):
    session_id: Optional[str] = None
    event_name: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# Real-world Manager Tools: Review Response Assistant
class ManagerReplyRequest(BaseModel):
    guest_review: str = Field(..., description="The guest review from Google or in-house")
    rating: int = Field(..., ge=1, le=5, description="Star rating given by guest")
    guest_name: Optional[str] = Field(default="Valued Guest", description="Name of the guest if available")
    manager_name: Optional[str] = Field(default="The General Management Team", description="Signing authority")
    tone: Optional[str] = Field(default="gracious", description="Tone: gracious, apologetic, warm, professional")

class ManagerReplyResponse(BaseModel):
    reply: str
    detected_sentiment: str
    recommended_action: str

# Private Manager Feedback Escalation (Prevents Public 1-star blowups)
class PrivateFeedbackRequest(BaseModel):
    business_id: str = "default_business"
    table_number: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    diner_note: str = Field(..., description="Direct guest feedback")
    aspects: Optional[List[str]] = Field(default_factory=list)
    guest_contact: Optional[str] = Field(default="", description="Email or phone for GM follow-up")

class PrivateFeedbackResponse(BaseModel):
    status: str = "received"
    ticket_id: str
    message: str
