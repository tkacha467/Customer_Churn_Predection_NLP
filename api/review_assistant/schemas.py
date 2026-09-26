from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReviewGenerateRequest(BaseModel):
    business_id: str = Field(default="default_business", description="Unique business identifier")
    rating: int = Field(..., ge=1, le=5, description="Customer star rating from 1 to 5")
    aspects: Optional[List[str]] = Field(default_factory=list, description="Aspects customer experienced (e.g. food, service)")
    user_note: Optional[str] = Field(default="", description="Customer freeform notes or comments")
    tone: Optional[str] = Field(default="natural", description="Tone: natural, casual, professional, short, detailed")
    length: Optional[str] = Field(default="medium", description="Length: short, medium, detailed")
    session_id: Optional[str] = Field(default=None, description="Optional session tracker")

class ReviewGenerateResponse(BaseModel):
    review: str
    sentiment: str
    sentiment_confidence: float
    rating_consistent: bool
    warnings: List[str] = Field(default_factory=list)
    aspects_covered: List[str] = Field(default_factory=list)
    generation_provider: str = "ai_engine"

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

class BusinessConfigUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    google_review_url: str

class ReviewSessionCreateRequest(BaseModel):
    business_id: str = "default_business"
    customer_ref: Optional[str] = None

class ReviewSessionResponse(BaseModel):
    session_id: str
    business_id: str
    created_at: str

class AnalyticsEventRequest(BaseModel):
    session_id: Optional[str] = None
    event_name: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
