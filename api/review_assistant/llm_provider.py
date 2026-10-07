"""
Review LLM Provider Abstraction for ChurnLens.
Supports Local, Hosted Inference, and Cloud providers (OpenAI, Gemini)
behind a unified, provider-agnostic interface.
"""

from abc import ABC, abstractmethod
import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

class ReviewLLMProvider(ABC):
    @abstractmethod
    def generate_review(
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
        business_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates a humanized, customer-grounded review draft."""
        pass

    @abstractmethod
    def generate_review_ideas(
        self,
        rating: int,
        aspects: List[str],
        user_note: str = "",
        business_name: str = "the restaurant",
        language: str = "english",
        business_category: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Generates 3-5 distinct, natural review candidate ideas in the chosen language."""
        pass


class LocalLLMProvider(ReviewLLMProvider):
    """
    Local High-Precision Hospitality Synthesis & Humanization Engine.
    Executes entirely on-premise without external network dependency.
    Enforces strict zero-fabrication, 15-45 word length, and 0-2 contextual emojis.
    Supports English, Roman Hinglish, and Roman Gujlish.
    """

    def generate_review_ideas(
        self,
        rating: int,
        aspects: List[str],
        user_note: str = "",
        business_name: str = "the restaurant",
        language: str = "english",
        business_category: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        from api.review_assistant.prompts import generate_candidate_ideas
        return generate_candidate_ideas(
            rating=rating,
            aspects=aspects,
            user_note=user_note,
            business_name=business_name,
            language=language,
            business_category=business_category,
        )

    def generate_review(
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
        business_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        from api.review_assistant.prompts import humanize_review_draft
        review_text = humanize_review_draft(
            rating=rating,
            aspects=aspects,
            user_note=user_note,
            selected_idea=selected_idea,
            tone=tone,
            length=length,
            dining_type=dining_type,
            emoji_preference=emoji_preference,
            business_name=business_name,
            language=language,
            business_category=business_category,
        )
        return {
            "review": review_text,
            "provider": "local-hospitality-engine"
        }


class CloudLLMProvider(ReviewLLMProvider):
    """
    Cloud / Hosted Inference Provider supporting Gemini & OpenAI.
    Gracefully falls back to LocalLLMProvider if network/API fails.
    """

    def __init__(self):
        self.local_fallback = LocalLLMProvider()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or ""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    def generate_review_ideas(
        self,
        rating: int,
        aspects: List[str],
        user_note: str = "",
        business_name: str = "the restaurant",
        language: str = "english",
        business_category: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        # Fast, deterministic ideas are consistent and instant
        return self.local_fallback.generate_review_ideas(
            rating=rating,
            aspects=aspects,
            user_note=user_note,
            business_name=business_name,
            language=language,
            business_category=business_category,
        )

    def generate_review(
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
        business_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        from api.review_assistant.prompts import build_humanized_prompt, SYSTEM_HUMANIZED_PROMPT

        prompt = build_humanized_prompt(
            rating=rating,
            aspects=aspects,
            user_note=user_note,
            selected_idea=selected_idea,
            tone=tone,
            length=length,
            dining_type=dining_type,
            emoji_preference=emoji_preference,
            business_name=business_name,
            language=language,
            business_category=business_category,
        )

        # 1. Attempt Gemini if key present
        if self.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
                payload = {
                    "system_instruction": {"parts": [{"text": SYSTEM_HUMANIZED_PROMPT}]},
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 150}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    cands = res_data.get("candidates", [])
                    if cands:
                        text = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if text:
                            return {"review": text.strip(' "\'\n'), "provider": "gemini-cloud-llm"}
            except Exception as e:
                print(f"[CloudLLMProvider] Gemini error: {e}")

        # 2. Attempt OpenAI if key present
        if self.openai_api_key:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_HUMANIZED_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 150
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.openai_api_key}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    choices = res_data.get("choices", [])
                    if choices:
                        text = choices[0].get("message", {}).get("content", "").strip()
                        if text:
                            return {"review": text.strip(' "\'\n'), "provider": "openai-cloud-llm"}
            except Exception as e:
                print(f"[CloudLLMProvider] OpenAI error: {e}")

        # Fallback to local
        return self.local_fallback.generate_review(
            rating=rating,
            aspects=aspects,
            user_note=user_note,
            selected_idea=selected_idea,
            tone=tone,
            length=length,
            dining_type=dining_type,
            emoji_preference=emoji_preference,
            business_name=business_name,
            language=language,
            business_category=business_category,
        )


def get_llm_provider() -> ReviewLLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "local").lower().strip()
    if provider_name in ["cloud", "openai", "gemini", "hosted"]:
        return CloudLLMProvider()
    return LocalLLMProvider()
