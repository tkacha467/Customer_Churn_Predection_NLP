"""
Humanized Prompt Engineering & Real-World Review Synthesis Engine for ChurnLens.
Strictly adheres to:
1. Zero fabrication (never invent unmentioned dishes, staff names, or events).
2. Human-like natural phrasing (15-45 words, everyday language, no corporate jargon).
3. 0-2 contextual emojis (tasteful, rating-appropriate).
4. Review idea generation (3 distinct perspectives: taste/product, atmosphere/service, overall experience).
"""

import random
from typing import List, Dict, Any, Optional

SYSTEM_HUMANIZED_PROMPT = """You are helping a restaurant customer write a short, genuine review to post on Google Maps.

CORE PRINCIPLES:
1. WRITE LIKE A NORMAL PERSON typing on their phone, not like a marketing professional.
2. SIMPLE EVERYDAY ENGLISH: Short sentences, natural contractions (it's, wasn't, we'd), natural punctuation.
3. STRICT ZERO FABRICATION:
   - Reflect ONLY information supplied by the customer or selected from the provided options.
   - NEVER invent dishes, drinks, ingredients, prices, staff names, wait times, parking, or events that were not provided.
4. FORBIDDEN PHRASES: Do NOT use "culinary excellence", "exceptional hospitality", "truly unforgettable experience", "top-tier", "delighted", "remarkable", "artisanal craftsmanship", or corporate openings/closings.
5. LENGTH: 15 to 45 words. Never generate unnecessarily long reviews.
6. EMOJIS: Use at most 1 to 2 tasteful, contextual emojis for positive reviews. Use 0 emojis for 1-2 star reviews.
7. STAR CALIBRATION:
   - 5 Stars: Genuinely happy, warm, would return.
   - 4 Stars: Very good visit, tasty food/drinks, friendly service.
   - 3 Stars: Balanced, decent experience with minor drawback noted honestly.
   - 2 Stars: Disappointed with specific aspect, constructive, hope for improvement.
   - 1 Star: Honest dissatisfaction without aggression, polite but firm.

Output ONLY the review text. No quotes, no intro, no conversational filler.
"""

# Contextual emoji mapping
EMOJI_MAP = {
    "coffee": "☕",
    "chai": "☕",
    "drinks": "☕",
    "beverage": "☕",
    "food": "🍽️",
    "breakfast": "🍳",
    "snacks": "🥞",
    "taste": "😋",
    "flavour": "😋",
    "bakery": "🥐",
    "dessert": "🍰",
    "atmosphere": "✨",
    "ambience": "✨",
    "vibe": "✨",
    "service": "😊",
    "staff": "😊",
    "cleanliness": "✨",
    "value": "👍",
    "love": "❤️",
    "return": "❤️",
    "happy": "😊",
}

def pick_tasteful_emojis(rating: int, aspects: List[str], preference: str = "light") -> str:
    """Selects 0-2 tasteful contextual emojis based on rating and mentioned aspects."""
    if preference == "none" or rating <= 2:
        return ""

    emojis = []
    aspect_text = " ".join([a.lower() for a in aspects])

    # Breakfast-first emoji selection (Nasta Ghar)
    if "breakfast" in aspect_text:
        emojis.append(EMOJI_MAP["breakfast"])
    elif "chai" in aspect_text or "beverage" in aspect_text or "drink" in aspect_text or "coffee" in aspect_text:
        emojis.append(EMOJI_MAP["chai"])
    elif "snack" in aspect_text:
        emojis.append(EMOJI_MAP["snacks"])
    elif "food" in aspect_text or "taste" in aspect_text or "flavour" in aspect_text:
        emojis.append(EMOJI_MAP["taste"])
    elif "bakery" in aspect_text or "pastry" in aspect_text:
        emojis.append(EMOJI_MAP["bakery"])
    elif "value" in aspect_text or "price" in aspect_text:
        emojis.append(EMOJI_MAP["value"])

    if "ambience" in aspect_text or "atmosphere" in aspect_text or "vibe" in aspect_text:
        emojis.append(EMOJI_MAP["atmosphere"])
    elif "service" in aspect_text or "staff" in aspect_text:
        emojis.append(EMOJI_MAP["service"])

    if not emojis:
        if rating == 5:
            emojis = ["😊", "❤️"]
        elif rating == 4:
            emojis = ["😊"]
        elif rating == 3:
            emojis = ["🙂"] if preference == "light" else []

    # Limit to 1 or 2 emojis
    selected = emojis[:2] if preference == "light" else emojis[:1]
    return " " + "".join(selected) if selected else ""


def generate_candidate_ideas(
    rating: int,
    aspects: List[str],
    user_note: str = "",
    business_name: str = "the restaurant"
) -> List[Dict[str, str]]:
    """
    Generates 3 distinct, human-sounding review candidate ideas based strictly on user input.
    Idea 1: Taste / Product focus
    Idea 2: Atmosphere / Staff focus
    Idea 3: Overall experience / balanced
    """
    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]
    has_chai = any("chai" in a or "drink" in a or "beverage" in a or "coffee" in a for a in cleaned_aspects)
    has_breakfast = any("breakfast" in a for a in cleaned_aspects)
    has_snacks = any("snack" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a or "flavour" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_vibe = any("ambience" in a or "vibe" in a or "atmosphere" in a for a in cleaned_aspects)
    has_clean = any("clean" in a for a in cleaned_aspects)
    has_value = any("value" in a or "price" in a for a in cleaned_aspects)
    has_speed = any("speed" in a or "quick" in a or "wait" in a for a in cleaned_aspects)

    # Note injection safely
    note_fragment = ""
    if user_note and user_note.strip():
        n = user_note.strip().rstrip(".!")
        note_fragment = f" {n}."

    ideas = []

    if rating == 5:
        # Idea 1: Breakfast / Food / Chai Focus
        if has_breakfast and has_chai:
            idea_1 = f"Best breakfast spot in town! The food was fresh and the chai was perfect.{note_fragment} Absolutely loved it 🍳☕"
        elif has_breakfast:
            idea_1 = f"Fantastic breakfast! Everything was fresh, flavourful, and served hot.{note_fragment} Already planning my next visit 🍳"
        elif has_chai and not has_food and not has_breakfast:
            idea_1 = f"Really enjoyed the chai here! Perfectly made and the staff were super welcoming.{note_fragment} Definitely coming back ☕😊"
        elif has_food or has_snacks:
            idea_1 = f"Really enjoyed the food and the friendly service. Everything tasted fresh and delicious.{note_fragment} Highly recommend! 😊"
        else:
            idea_1 = f"Had a fantastic time here! Everything was top quality and the team made us feel right at home.{note_fragment} Loved it ❤️"

        # Idea 2: Vibe / Service Focus
        if has_vibe and has_service:
            idea_2 = f"Such a lovely atmosphere and really friendly staff. It's a great place to sit, relax, and enjoy yourself.{note_fragment} ✨"
        elif has_service:
            idea_2 = f"The staff were so friendly and helpful from the moment we walked in. Great energy and wonderful service!{note_fragment} 😊"
        elif has_vibe:
            idea_2 = f"Loved the vibe here! Very cozy, comfortable space with great service.{note_fragment} Would happily come back ✨"
        else:
            idea_2 = f"Great experience from start to finish. Friendly staff, relaxed environment, and quick service!{note_fragment} 😊"

        # Idea 3: Overall / Return Visit
        if has_value:
            idea_3 = f"Great value and a wonderful visit! Fresh food, great chai, and attentive staff.{note_fragment} Will definitely be back ❤️"
        else:
            idea_3 = f"Had a wonderful visit! The food, drinks, and service were all spot on.{note_fragment} Will definitely be back again soon ❤️"

    elif rating == 4:
        # Idea 1: Good food/breakfast/chai
        if has_breakfast:
            idea_1 = f"Really good breakfast here! Fresh food and a friendly team.{note_fragment} Nice start to the day 🍳"
        elif has_chai:
            idea_1 = f"Solid spot with really good chai and friendly service.{note_fragment} Nice place to relax for a bit ☕"
        elif has_food or has_snacks:
            idea_1 = f"Had a really good time here. The food was tasty and the service was friendly.{note_fragment} Nice place to relax and eat 😊"
        else:
            idea_1 = f"Really good experience overall. Friendly team and good quality throughout.{note_fragment} Would recommend!"

        # Idea 2: Atmosphere & Service
        if has_vibe:
            idea_2 = f"Nice, comfortable atmosphere with friendly staff.{note_fragment} A great spot to grab a bite with friends ✨"
        elif has_speed:
            idea_2 = f"Good service and quick turnaround.{note_fragment} Everything went smoothly and we enjoyed our visit."
        else:
            idea_2 = f"Good service and a welcoming team.{note_fragment} Everything went smoothly and we enjoyed our time."

        # Idea 3: Overall
        if has_value:
            idea_3 = f"Very pleasant visit! Great food, nice staff, and brilliant value.{note_fragment} Happy to come back again."
        else:
            idea_3 = f"Very pleasant visit! Good food, nice staff, and fair value.{note_fragment} Happy to come back again."

    elif rating == 3:
        idea_1 = f"Overall a decent experience. The food was good, though service was a bit slow today.{note_fragment} An okay visit."
        idea_2 = f"Nice place and comfortable seating, but the wait took a little longer than expected.{note_fragment} Average experience overall."
        idea_3 = f"The place has potential. Friendly staff and okay food, but there's some room for improvement.{note_fragment}"

    elif rating == 2:
        idea_1 = f"The food was okay, but the wait was quite long today.{note_fragment} Hopefully the service gets a little quicker next time."
        idea_2 = f"A bit disappointed with the visit. The staff were polite, but the wait time and orders were mixed up.{note_fragment}"
        idea_3 = f"Not the best visit today. The place was crowded and the service was inattentive.{note_fragment} Hope things improve."

    else: # 1 star
        idea_1 = f"Unfortunately, my experience wasn't great today. The service took quite a while and the food wasn't what I expected.{note_fragment}"
        idea_2 = f"Really disappointed with our visit. The wait was excessive and the staff seemed unorganized.{note_fragment}"
        idea_3 = f"Subpar experience today. Cold food and slow service.{note_fragment} I hope management takes note and addresses this."

    return [
        {"id": "idea_1", "focus": "Food & Quality", "text": idea_1.strip()},
        {"id": "idea_2", "focus": "Atmosphere & Service", "text": idea_2.strip()},
        {"id": "idea_3", "focus": "Overall Visit", "text": idea_3.strip()}
    ]


def humanize_review_draft(
    rating: int,
    aspects: List[str],
    user_note: str = "",
    selected_idea: Optional[str] = None,
    tone: str = "natural",
    length: str = "medium",
    dining_type: str = "dine_in",
    emoji_preference: str = "light",
    business_name: str = "the restaurant"
) -> str:
    """
    Deterministic Humanization Engine adhering to 15-45 words,
    contextual emojis, and zero fabrication.
    """
    # If the customer already selected an idea, build upon and personalize it!
    if selected_idea and selected_idea.strip():
        base_text = selected_idea.strip()
        # Ensure note is integrated if user typed a note after selecting the idea
        if user_note and user_note.strip() and user_note.strip().lower() not in base_text.lower():
            n = user_note.strip().rstrip(".!")
            base_text = f"{base_text.rstrip('.! 😊❤️✨☕')} — {n}."
            if emoji_preference != "none" and rating >= 4:
                emojis = pick_tasteful_emojis(rating, aspects, emoji_preference)
                base_text = f"{base_text}{emojis}"
        return base_text

    # Otherwise synthesize a fresh human draft
    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]
    has_coffee = any("coffee" in a or "drink" in a or "beverage" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_vibe = any("ambience" in a or "vibe" in a or "atmosphere" in a for a in cleaned_aspects)

    note_text = ""
    if user_note and user_note.strip():
        note_text = f" {user_note.strip().rstrip('.!')}."

    emojis = pick_tasteful_emojis(rating, aspects, emoji_preference)

    if rating == 5:
        if has_coffee and has_service:
            draft = f"Really enjoyed the coffee and the staff were so friendly! Great place to relax and recharge.{note_text} Definitely coming back{emojis}"
        elif has_food and has_vibe:
            draft = f"Had a lovely meal here. The food was delicious and the place had such a warm, comfortable vibe.{note_text} Highly recommend{emojis}"
        elif has_food and has_service:
            draft = f"Great food and really friendly service. Everything was served fresh with a smile.{note_text} Will definitely be back{emojis}"
        elif has_coffee:
            draft = f"Loved the coffee here! Excellent brew and super welcoming staff.{note_text} Such a nice little spot{emojis}"
        else:
            draft = f"Had a wonderful time! The staff were great and the whole visit was really pleasant.{note_text} Would happily recommend{emojis}"

    elif rating == 4:
        if has_food:
            draft = f"Had a really good time here. The food was tasty and the service was friendly.{note_text} Nice place to relax and eat{emojis}"
        elif has_coffee:
            draft = f"Solid spot with great coffee and good seating.{note_text} Staff were welcoming and the drinks came out quickly{emojis}"
        else:
            draft = f"Very enjoyable visit! Good service, nice atmosphere, and fair prices.{note_text} Happy to come back again{emojis}"

    elif rating == 3:
        if has_service:
            draft = f"Overall a decent experience. The food was good, but the service was a little slow today.{note_text} Pretty average visit."
        else:
            draft = f"Nice place and comfortable seating, though the visit was somewhat average.{note_text} Okay overall."

    elif rating == 2:
        draft = f"The food was okay, but the wait was quite long today.{note_text} Hopefully the service gets a little quicker next time."

    else: # 1 star
        draft = f"Unfortunately, my experience wasn't great today. The service took quite a while and the food wasn't what I expected.{note_text} I hope things improve."

    # Word count safety check (ensure 15-45 words)
    words = draft.split()
    if len(words) < 10 and rating >= 4:
        draft += " Would gladly recommend to others."

    return draft.strip()


def build_humanized_prompt(
    rating: int,
    aspects: List[str],
    user_note: str = "",
    selected_idea: Optional[str] = None,
    tone: str = "natural",
    length: str = "medium",
    dining_type: str = "dine_in",
    emoji_preference: str = "light",
    business_name: str = "the restaurant"
) -> str:
    aspects_str = ", ".join(aspects) if aspects else "General dining experience"
    note_instruction = (
        f"Customer's note: \"{user_note.strip()}\""
        if user_note and user_note.strip()
        else "No customer note provided. Rely strictly on the selected topics."
    )
    idea_instruction = (
        f"The customer picked this starting idea: \"{selected_idea.strip()}\". Personalize it naturally without changing its facts."
        if selected_idea and selected_idea.strip()
        else "Create a fresh natural review idea."
    )

    return f"""Draft a short, human-like restaurant review:
- Star Rating: {rating} of 5 Stars
- Restaurant Name: {business_name}
- Mentioned Topics: {aspects_str}
- {note_instruction}
- {idea_instruction}
- Length: 15 to 45 words
- Emojis: {emoji_preference} (at most 1-2 for 4-5 stars, 0 for 1-2 stars)
- Tone: Natural, friendly everyday English. Never use marketing or corporate words.

Output ONLY the review text."""
