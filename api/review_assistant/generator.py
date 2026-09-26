"""
Review Generation Engine for ChurnLens.
Supports:
1. Google Gemini / OpenAI LLM providers if an API key is configured.
2. Built-in Deterministic & Natural NLP Synthesis Engine (offline-capable fallback)
   that strictly adheres to zero-fabrication rules, rating calibration, and selected aspects.
"""

import os
import json
import random
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from api.review_assistant.prompts import SYSTEM_PROMPT, build_review_prompt

class ReviewGenerator:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or ""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    def generate(
        self,
        rating: int,
        aspects: List[str],
        user_note: str = "",
        tone: str = "natural",
        length: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a review draft according to star rating, aspects, user notes, and tone.
        Attempts LLM call if credentials exist, otherwise seamlessly uses the
        anti-fabrication natural synthesis engine.
        """
        cleaned_aspects = [a.strip() for a in aspects if a.strip()]
        cleaned_note = user_note.strip() if user_note else ""
        norm_tone = tone.lower().strip() if tone else "natural"
        norm_length = length.lower().strip() if length else "medium"

        # Check for external LLM execution first
        if self.gemini_api_key:
            try:
                review_text = self._call_gemini(rating, cleaned_aspects, cleaned_note, norm_tone, norm_length)
                if review_text:
                    return {
                        "review": review_text.strip(' "\'\n'),
                        "provider": "gemini-api"
                    }
            except Exception as e:
                print(f"[ReviewGenerator] Gemini API error, falling back to natural engine: {e}")

        if self.openai_api_key:
            try:
                review_text = self._call_openai(rating, cleaned_aspects, cleaned_note, norm_tone, norm_length)
                if review_text:
                    return {
                        "review": review_text.strip(' "\'\n'),
                        "provider": "openai-api"
                    }
            except Exception as e:
                print(f"[ReviewGenerator] OpenAI API error, falling back to natural engine: {e}")

        # Fallback to Built-in Grounded Natural Synthesis Engine
        review_text = self._synthesize_natural_review(
            rating=rating,
            aspects=cleaned_aspects,
            user_note=cleaned_note,
            tone=norm_tone,
            length=norm_length
        )

        return {
            "review": review_text,
            "provider": "churnlens-grounded-engine"
        }

    def _call_gemini(
        self, rating: int, aspects: List[str], user_note: str, tone: str, length: str
    ) -> Optional[str]:
        """Calls Google Gemini API via standard lightweight HTTP."""
        prompt = build_review_prompt(rating, aspects, user_note, tone, length)
        # Try gemini-1.5-flash or gemini-2.5-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 250,
                "topP": 0.85
            }
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return None

    def _call_openai(
        self, rating: int, aspects: List[str], user_note: str, tone: str, length: str
    ) -> Optional[str]:
        """Calls OpenAI API via standard lightweight HTTP."""
        prompt = build_review_prompt(rating, aspects, user_note, tone, length)
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 200
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            choices = res_data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        return None

    def _synthesize_natural_review(
        self, rating: int, aspects: List[str], user_note: str, tone: str, length: str
    ) -> str:
        """
        Anti-Fabrication Natural Review Synthesizer.
        Generates genuine, fluent reviews based solely on selected aspects and note.
        Does NOT invent any dish, discount, staff name, or unmentioned fact.
        """
        sentences = []

        # 1. Incorporate User Note with Tone Alignment
        formatted_note = ""
        if user_note:
            cleaned = user_note.strip().rstrip(".")
            if tone == "casual":
                formatted_note = f"{cleaned}."
            elif tone == "professional":
                formatted_note = f"Notably, {cleaned.lower()}."
            else:
                formatted_note = f"{cleaned}."

        # 2. Rating-Calibrated Openers
        if rating == 5:
            openers = {
                "natural": "Had a wonderful experience here.",
                "casual": "Really impressed with everything here!",
                "professional": "Exceptional experience overall.",
                "short": "Outstanding experience all around.",
                "detailed": "We had an absolutely fantastic visit from start to finish."
            }
        elif rating == 4:
            openers = {
                "natural": "Had a very positive experience overall.",
                "casual": "Really solid place with lots to like.",
                "professional": "A very pleasant visit with quality service.",
                "short": "Great visit with good overall service.",
                "detailed": "Overall, we had a very good experience and enjoyed our visit."
            }
        elif rating == 3:
            openers = {
                "natural": "A decent experience overall, though fairly average.",
                "casual": "It was an okay visit, some things were fine and others had room for improvement.",
                "professional": "A balanced experience meeting standard expectations.",
                "short": "An acceptable visit overall.",
                "detailed": "Our visit was satisfactory, though with several areas that could be improved."
            }
        elif rating == 2:
            openers = {
                "natural": "Disappointing experience overall, with several issues during our visit.",
                "casual": "Honestly wasn't impressed with our visit here.",
                "professional": "Regrettably, the experience fell below reasonable expectations.",
                "short": "Disappointing experience with noticeable shortcomings.",
                "detailed": "Unfortunately, our visit did not meet expectations due to several clear shortcomings."
            }
        else: # 1 star
            openers = {
                "natural": "Very disappointed with this experience.",
                "casual": "Really bad experience, would definitely not recommend.",
                "professional": "Extremely dissatisfied with the service and overall standards.",
                "short": "Extremely poor experience.",
                "detailed": "A very frustrating and subpar experience that failed on basic standards."
            }

        opener = openers.get(tone, openers["natural"])
        sentences.append(opener)

        # 3. Add User Note early if provided
        if formatted_note:
            sentences.append(formatted_note)

        # 4. Integrate Aspects (Without fabricating specific details!)
        aspect_clauses = []
        for aspect in aspects:
            asp_key = aspect.lower().strip()
            clause = self._get_aspect_phrase(asp_key, rating, tone)
            if clause:
                aspect_clauses.append(clause)

        if aspect_clauses:
            if length == "short":
                # Only take the first aspect to keep it short
                sentences.append(aspect_clauses[0])
            elif length == "detailed":
                sentences.extend(aspect_clauses[:3])
            else:
                sentences.extend(aspect_clauses[:2])

        # 5. Rating-Calibrated Closers
        if length != "short":
            if rating == 5:
                closers = {
                    "natural": "Will definitely be returning again soon!",
                    "casual": "Definitely coming back!",
                    "professional": "I gladly recommend this establishment to others.",
                    "detailed": "Highly recommended and looking forward to our next visit."
                }
            elif rating == 4:
                closers = {
                    "natural": "I would certainly recommend checking them out.",
                    "casual": "Worth stopping by.",
                    "professional": "A commendable establishment that I would recommend.",
                    "detailed": "We would happily visit again in the future."
                }
            elif rating == 3:
                closers = {
                    "natural": "Hope to see some improvements on future visits.",
                    "casual": "Might give them another shot later on.",
                    "professional": "With a few minor adjustments, the experience could be considerably better.",
                    "detailed": "Average overall, but potential is certainly there."
                }
            elif rating == 2:
                closers = {
                    "natural": "Substantial improvements are needed here.",
                    "casual": "Probably won't be returning anytime soon.",
                    "professional": "Management should address these operational concerns.",
                    "detailed": "We hope management takes constructive note of these issues."
                }
            else:
                closers = {
                    "natural": "Cannot recommend based on this visit.",
                    "casual": "Won't be returning.",
                    "professional": "A completely unsatisfactory experience that needs urgent management review.",
                    "detailed": "I strongly advise looking elsewhere until standards are elevated."
                }
            sentences.append(closers.get(tone, closers["natural"]))

        # Join cleanly
        final_text = " ".join([s.strip() for s in sentences if s.strip()])
        return final_text

    def _get_aspect_phrase(self, aspect: str, rating: int, tone: str) -> Optional[str]:
        """Maps aspect + rating into grounded phrasing without inventing specifics."""
        pos = rating >= 4
        neu = rating == 3
        
        if "food" in aspect or "taste" in aspect or "quality" in aspect:
            if pos:
                return "The food quality was wonderful and genuinely flavorful." if tone != "professional" else "The culinary offerings were well-prepared and of high quality."
            elif neu:
                return "The food was acceptable, though neither memorable nor particularly distinct."
            else:
                return "The quality of the food was subpar and did not meet basic expectations."

        if "service" in aspect or "staff" in aspect:
            if pos:
                return "The staff members were attentive, courteous, and very helpful."
            elif neu:
                return "Service was standard, though a bit slow at times."
            else:
                return "Customer service was inattentive and unhelpful throughout."

        if "ambiance" in aspect or "cleanliness" in aspect:
            if pos:
                return "The atmosphere was pleasant, clean, and comfortable."
            elif neu:
                return "The environment was okay, though could be refreshed."
            else:
                return "The environment was poorly maintained and lacked cleanliness."

        if "value" in aspect or "price" in aspect:
            if pos:
                return "Great value for money considering the overall quality."
            elif neu:
                return "Pricing was moderate for what was provided."
            else:
                return "Overpriced for the level of quality received."

        if "waiting" in aspect or "wait" in aspect:
            if pos:
                return "Everything was handled in a timely manner with minimal waiting."
            elif neu:
                return "Wait times were moderate but manageable."
            else:
                return "Excessive waiting times detracted significantly from the visit."

        if "location" in aspect:
            if pos:
                return "The location is convenient and accessible."
            elif neu:
                return "The location was easy enough to reach."
            else:
                return "The location was difficult to access."

        # Default fallback for other aspects
        if pos:
            return f"The {aspect} was commendable."
        elif neu:
            return f"The {aspect} was acceptable."
        else:
            return f"The {aspect} was disappointing."

review_generator = ReviewGenerator()
