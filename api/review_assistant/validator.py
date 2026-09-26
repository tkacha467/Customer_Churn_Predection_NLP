"""
Review Validation Module for ChurnLens.
Validates review draft sentiment against selected star rating using the existing NLP & Fusion pipeline.
"""

from typing import Dict, Any, Tuple, List
from api.preprocessing.text_cleaner import text_cleaner
from api.models.sentiment import sentiment_model
from api.models.sarcasm import sarcasm_model
from api.fusion.engine import fusion_engine

class ReviewValidator:
    def validate(self, rating: int, review_text: str) -> Dict[str, Any]:
        """
        Runs the review text through the existing sentiment and sarcasm fusion engine,
        then evaluates consistency against the user's star rating.
        """
        text = review_text.strip()
        if not text:
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "rating_consistent": False,
                "is_sarcastic": False,
                "warnings": ["Review text is empty."]
            }

        cleaned = text_cleaner.clean(text)

        # 1. Run sarcasm model
        sarcasm_res = sarcasm_model.predict(cleaned)
        sarcasm_prob = sarcasm_res.get("sarcasm_probability", 0.0)

        # 2. Run sentiment model
        sentiment_res = sentiment_model.predict(cleaned)

        # 3. Fusion Engine
        fusion_res = fusion_engine.fuse(sentiment_res, sarcasm_prob)
        predicted_sentiment = fusion_res["prediction"].upper() # POSITIVE, NEUTRAL, NEGATIVE
        fused_probs = fusion_res["probabilities"]
        confidence = float(fused_probs.get(predicted_sentiment.lower(), 0.5))
        is_sarcastic = fusion_res["debug"].get("sarcasm_activated", False)

        # 4. Consistency Check against Rating
        rating_consistent, warnings = self._check_rating_consistency(
            rating=rating,
            sentiment=predicted_sentiment,
            confidence=confidence,
            is_sarcastic=is_sarcastic
        )

        return {
            "sentiment": predicted_sentiment.capitalize(),
            "confidence": round(confidence, 4),
            "rating_consistent": rating_consistent,
            "is_sarcastic": is_sarcastic,
            "warnings": warnings,
            "probabilities": fused_probs
        }

    def _check_rating_consistency(
        self, rating: int, sentiment: str, confidence: float, is_sarcastic: bool
    ) -> Tuple[bool, List[str]]:
        warnings = []
        consistent = True

        if rating >= 4:
            # 4 or 5 stars should not be negative
            if sentiment == "NEGATIVE":
                consistent = False
                warnings.append(
                    f"Selected rating is {rating} stars, but the review tone was analyzed as Negative ({int(confidence*100)}% confidence)."
                )
            elif is_sarcastic:
                consistent = False
                warnings.append("Sarcastic phrasing was detected in a positive rating.")
        elif rating <= 2:
            # 1 or 2 stars should not be positive
            if sentiment == "POSITIVE":
                consistent = False
                warnings.append(
                    f"Selected rating is {rating} stars, but the review tone was analyzed as Positive ({int(confidence*100)}% confidence)."
                )
        elif rating == 3:
            # 3 stars is balanced/neutral; high positive or high negative can be noted
            if is_sarcastic:
                consistent = False
                warnings.append("Sarcastic tone detected in a balanced review.")

        return consistent, warnings

review_validator = ReviewValidator()
