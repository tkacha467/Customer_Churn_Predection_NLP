"""
Hospitality Review & Manager Response Generation Engine for ChurnLens.
Supports:
1. ReviewLLMProvider abstraction (Local & Cloud).
2. Zero-fabrication humanized synthesis (15-45 words, 0-2 contextual emojis).
3. Candidate review ideas generation.
"""

from typing import List, Dict, Any, Optional
from api.review_assistant.llm_provider import get_llm_provider

class ReviewGenerator:
    def __init__(self):
        self.provider = get_llm_provider()

    def generate_ideas(
        self,
        rating: int,
        aspects: List[str],
        user_note: str = "",
        business_name: str = "the restaurant",
        language: str = "english",
        category: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Generates 3-5 distinct candidate review ideas."""
        return self.provider.generate_review_ideas(
            rating=rating,
            aspects=aspects,
            user_note=user_note,
            business_name=business_name,
            language=language,
            category=category
        )

    def generate(
        self,
        rating: int,
        aspects: List[str],
        user_note: str = "",
        selected_idea: Optional[str] = None,
        tone: str = "natural",
        length: str = "medium",
        dining_type: str = "dine_in",
        emoji_preference: str = "light",
        business_name: str = "the restaurant",
        language: str = "english",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates humanized, grounded review draft adhering to zero-fabrication standards."""
        cleaned_aspects = [a.strip() for a in aspects if a.strip()]
        cleaned_note = user_note.strip() if user_note else ""

        return self.provider.generate_review(
            rating=rating,
            aspects=cleaned_aspects,
            user_note=cleaned_note,
            selected_idea=selected_idea,
            tone=tone,
            length=length,
            dining_type=dining_type,
            emoji_preference=emoji_preference,
            business_name=business_name,
            language=language,
            category=category
        )

    def generate_manager_reply(
        self,
        guest_review: str,
        rating: int,
        guest_name: str = "Valued Guest",
        manager_name: str = "The Management Team",
        tone: str = "gracious"
    ) -> Dict[str, Any]:
        """Standard courteous GM responses for Google Maps reviews."""
        if rating >= 4:
            reply = (
                f"Dear {guest_name}, thank you so much for your kind review! "
                f"We are delighted you enjoyed your visit with us. Our team takes great pride "
                f"in providing a welcoming experience, and we look forward to seeing you again soon! "
                f"— Warmly, {manager_name}"
            )
        elif rating == 3:
            reply = (
                f"Dear {guest_name}, thank you for sharing your feedback. "
                f"We appreciate your honest comments and are continually working to improve our service and quality. "
                f"We hope to welcome you back for an even better experience next time. "
                f"— Sincerely, {manager_name}"
            )
        else:
            reply = (
                f"Dear {guest_name}, we sincerely apologize that your experience fell short of expectations. "
                f"We take guest feedback very seriously and would appreciate the opportunity to make things right. "
                f"Please feel free to connect with our management directly so we can assist you personally. "
                f"— With apologies, {manager_name}"
            )
        return {"reply": reply, "provider": "churnlens-gm-rules"}

review_generator = ReviewGenerator()
