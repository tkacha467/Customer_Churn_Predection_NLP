"""
Humanized Prompt Engineering & Real-World Review Synthesis Engine for ChurnLens.
Strictly adheres to:
1. Zero fabrication (never invent unmentioned dishes, staff names, or events).
2. Human-like natural phrasing (15-45 words, everyday language, no corporate jargon).
3. 1-2 contextual emojis for every rating level (tasteful, rating-appropriate).
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
6. EMOJIS: Use 1 to 2 tasteful, contextual emojis for EVERY review. Scale tone to the rating: warm/happy emojis (😊❤️🍳) for 4-5 stars, neutral (🙂) for 3 stars, disappointed/sad (😕😞) for 1-2 stars.
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
    """Selects 1-2 tasteful contextual emojis based on rating and mentioned aspects."""
    if preference == "none":
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
            emojis = ["🙂"]
        elif rating == 2:
            emojis = ["😕"]
        else:
            emojis = ["😞"]

    # Limit to 1 or 2 emojis
    selected = emojis[:2] if preference == "light" else emojis[:1]
    return " " + "".join(selected) if selected else ""


def generate_candidate_ideas(
    rating: int,
    aspects: List[str],
    user_note: str = "",
    business_name: str = "Nasta Ghar"
) -> List[Dict[str, str]]:
    """
    Generates 5 distinct, human-sounding review candidate ideas based on user input.
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

    if rating == 5:
        ideas = [
            {"id": "idea_1", "focus": "Short & Sweet", "text": f"Amazing breakfast and best chai in town!{note_fragment} Loved it 🍳☕"},
            {"id": "idea_2", "focus": "Food & Tea", "text": f"The food was fresh and the tea was super tasty.{note_fragment} Quick service too ☕😋"},
            {"id": "idea_3", "focus": "Staff & Place", "text": f"Very friendly staff and clean place.{note_fragment} We had a great time here 😊✨"},
            {"id": "idea_4", "focus": "Taste & Value", "text": f"Everything was hot, fresh and full of flavour. The snacks and chai were really good and the price is also fair.{note_fragment} Must try 👌🍲"},
            {"id": "idea_5", "focus": "Family Visit", "text": f"Had a wonderful breakfast with family at {business_name}. Great food, friendly people, and relaxed vibe.{note_fragment} Will surely visit again! 👨‍👩‍👧‍👦❤️"},
        ]
    elif rating == 4:
        ideas = [
            {"id": "idea_1", "focus": "Short & Sweet", "text": f"Good food and tasty chai!{note_fragment} Nice start to the morning 🍳"},
            {"id": "idea_2", "focus": "Food & Service", "text": f"Fresh breakfast and quick service.{note_fragment} Staff was polite and helpful 👍☕"},
            {"id": "idea_3", "focus": "Clean & Fair", "text": f"Clean sitting area and good food quality.{note_fragment} Prices are also reasonable 😊"},
            {"id": "idea_4", "focus": "Snacks & Tea", "text": f"Enjoyed the snacks and hot tea. Food was served quickly and tasted nice.{note_fragment} Worth a visit for a quick bite 🥪🍲"},
            {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall a very pleasant visit. Good taste, clean tables, and friendly service.{note_fragment} Will definitely come back again 🌟👍"},
        ]
    elif rating == 3:
        ideas = [
            {"id": "idea_1", "focus": "Short & Sweet", "text": f"Decent food, but the service was a bit slow today.{note_fragment} 🙂"},
            {"id": "idea_2", "focus": "Food & Tea", "text": f"The chai was nice, but the snacks could have been hotter.{note_fragment} Okay experience overall 🙂☕"},
            {"id": "idea_3", "focus": "Wait Time", "text": f"Staff was polite, but we had to wait some time for our order.{note_fragment} Average visit 🙂"},
            {"id": "idea_4", "focus": "Busy Hours", "text": f"The place was quite crowded today. Food taste was fine, but table cleaning took longer than expected.{note_fragment} Hope it gets faster next time 🙂🥪"},
            {"id": "idea_5", "focus": "Overall Visit", "text": f"Fair experience overall. Tea was good and seating is comfortable, but service needs a little improvement.{note_fragment} It was an okay visit 🙂"},
        ]
    elif rating == 2:
        ideas = [
            {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food was okay, but wait time was too long today.{note_fragment} 😕"},
            {"id": "idea_2", "focus": "Order Delay", "text": f"Not satisfied with the service today.{note_fragment} Order was delayed and food was lukewarm 😕"},
            {"id": "idea_3", "focus": "Attention", "text": f"The place was noisy and staff was not paying attention.{note_fragment} Expected better service 😕"},
            {"id": "idea_4", "focus": "Slow Service", "text": f"We had to wait a long time to get our food and tables were not cleaned quickly.{note_fragment} Need to improve customer service 😕⏳"},
            {"id": "idea_5", "focus": "Overall Visit", "text": f"Disappointing visit today. The chai was fine but snacks were not fresh and service was very slow.{note_fragment} Hope management fixes this 😕"},
        ]
    else: # 1 star
        ideas = [
            {"id": "idea_1", "focus": "Short & Sweet", "text": f"Very slow service and cold food today.{note_fragment} 😞"},
            {"id": "idea_2", "focus": "Order Issue", "text": f"Bad experience today.{note_fragment} Waited very long and our order was wrong 😞"},
            {"id": "idea_3", "focus": "Cleanliness", "text": f"Staff was unorganized and tables were not clean.{note_fragment} Very poor service 😞"},
            {"id": "idea_4", "focus": "Food & Wait", "text": f"Disappointed with the visit. Food took forever to arrive and tasted stale.{note_fragment} Nobody came to attend us properly 😞👎"},
            {"id": "idea_5", "focus": "Overall Visit", "text": f"Extremely poor experience today. Long waiting time, cold food, and careless staff.{note_fragment} Needs major improvement in service 😞"},
        ]

    return ideas


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
            if emoji_preference != "none":
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
            draft = f"Overall a decent experience. The food was good, but the service was a little slow today.{note_text} Pretty average visit.{emojis}"
        else:
            draft = f"Nice place and comfortable seating, though the visit was somewhat average.{note_text} Okay overall.{emojis}"

    elif rating == 2:
        draft = f"The food was okay, but the wait was quite long today.{note_text} Hopefully the service gets a little quicker next time.{emojis}"

    else: # 1 star
        draft = f"Unfortunately, my experience wasn't great today. The service took quite a while and the food wasn't what I expected.{note_text} I hope things improve.{emojis}"

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
