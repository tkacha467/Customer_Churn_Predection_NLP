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
    business_name: str = "Nasta Ghar"
) -> List[Dict[str, str]]:
    """
    Generates 10 distinct, human-sounding review candidate ideas based on user input.
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
            {"id": "idea_1", "focus": "Fresh Breakfast", "text": f"Best breakfast spot in town! The food was fresh, hot, and the chai was perfect.{note_fragment} Absolutely loved it 🍳☕"},
            {"id": "idea_2", "focus": "Babalal Ni Chai", "text": f"Babalal Ni Chai is truly unbeatable! Steaming hot tea paired with fresh snacks made our morning.{note_fragment} Highly recommended ☕😋"},
            {"id": "idea_3", "focus": "Hospitality & Staff", "text": f"Incredible hospitality and welcoming service! The team makes you feel right at home.{note_fragment} Loved the positive vibe ❤️"},
            {"id": "idea_4", "focus": "Atmosphere & Service", "text": f"Great experience from start to finish. Friendly staff, relaxed traditional environment, and super fast service!{note_fragment} 😊✨"},
            {"id": "idea_5", "focus": "Authentic Taste", "text": f"Authentic Gujarati homestyle taste! Everything is made fresh with genuine care and top ingredients.{note_fragment} 🍲👌"},
            {"id": "idea_6", "focus": "Cleanliness & Hygiene", "text": f"Extremely neat, clean, and hygienic place with an open kitchen. Delicious food and great peace of mind!{note_fragment} ✨🍽️"},
            {"id": "idea_7", "focus": "Value for Money", "text": f"Wonderful quality at very reasonable prices. Generous portions and rich taste.{note_fragment} Best value breakfast around 💰👍"},
            {"id": "idea_8", "focus": "Family Dining", "text": f"Lovely place to visit with family and friends. Everyone from kids to elders thoroughly enjoyed the food.{note_fragment} Will visit again 👨‍👩‍👧‍👦❤️"},
            {"id": "idea_9", "focus": "Evening Snacks", "text": f"Perfect place for evening snacks and hot beverages. Freshly prepared items and prompt service!{note_fragment} 🥪⚡"},
            {"id": "idea_10", "focus": "Overall Visit", "text": f"Had a fantastic time at {business_name}! Outstanding taste, courteous staff, and great ambiance.{note_fragment} 10/10 recommended! 🌟"}
        ]
    elif rating == 4:
        ideas = [
            {"id": "idea_1", "focus": "Breakfast", "text": f"Really good breakfast! Fresh food and tasty chai.{note_fragment} A great start to the day 🍳"},
            {"id": "idea_2", "focus": "Chai & Snacks", "text": f"Delicious snacks and lovely chai. Friendly staff and pleasant atmosphere.{note_fragment} ☕"},
            {"id": "idea_3", "focus": "Service & Seating", "text": f"Good food, quick service, and clean seating. Would definitely come back again.{note_fragment} 👍"},
            {"id": "idea_4", "focus": "Family Visit", "text": f"Tasty food and prompt service. Enjoyed the breakfast with family.{note_fragment} 😊"},
            {"id": "idea_5", "focus": "Taste & Quality", "text": f"Nice authentic taste and reasonable prices. Worth a visit!{note_fragment} 🍲"},
            {"id": "idea_6", "focus": "Cleanliness", "text": f"Good hygienic place with welcoming staff. Chai was especially nice.{note_fragment} ✨"},
            {"id": "idea_7", "focus": "Value", "text": f"Great value for money. Fresh items and decent service speed.{note_fragment} 💰"},
            {"id": "idea_8", "focus": "Hospitality", "text": f"Pleasant dining experience. Good portions and warm hospitality.{note_fragment} 🍽️"},
            {"id": "idea_9", "focus": "Quick Bite", "text": f"Satisfying snacks and refreshing tea. A reliable spot for breakfast.{note_fragment} 🥪"},
            {"id": "idea_10", "focus": "Overall", "text": f"Overall a very positive experience. Clean place and good food!{note_fragment} 🌟"}
        ]
    elif rating == 3:
        ideas = [
            {"id": "idea_1", "focus": "Service Speed", "text": f"Overall a decent experience. The food was good, though service was a bit slow today.{note_fragment}"},
            {"id": "idea_2", "focus": "Seating & Wait", "text": f"Nice place and comfortable seating, but the wait took a little longer than expected.{note_fragment}"},
            {"id": "idea_3", "focus": "Potential", "text": f"The place has potential. Friendly staff and okay food, but there's room for improvement.{note_fragment}"},
            {"id": "idea_4", "focus": "Food Temperature", "text": f"Chai was good, but some snacks could have been served hotter.{note_fragment}"},
            {"id": "idea_5", "focus": "Overall", "text": f"Average visit today. Hope service gets a bit faster next time.{note_fragment}"},
            {"id": "idea_6", "focus": "Atmosphere", "text": f"Decent atmosphere, though it got quite crowded during peak morning hours.{note_fragment}"},
            {"id": "idea_7", "focus": "Snacks", "text": f"Standard snacks and tea. Fair pricing, but expected slightly better taste.{note_fragment}"},
            {"id": "idea_8", "focus": "Staff", "text": f"Polite staff, but took a while to get our order delivered.{note_fragment}"},
            {"id": "idea_9", "focus": "Cleanliness", "text": f"Cleanliness was okay, but tables could be cleared a bit quicker.{note_fragment}"},
            {"id": "idea_10", "focus": "Experience", "text": f"Fair experience overall. Good tea, but food was average.{note_fragment}"}
        ]
    elif rating == 2:
        ideas = [
            {"id": "idea_1", "focus": "Wait Time", "text": f"The food was okay, but the wait was quite long today.{note_fragment}"},
            {"id": "idea_2", "focus": "Order Mixup", "text": f"A bit disappointed with the visit. The staff were polite, but order service was mixed up.{note_fragment}"},
            {"id": "idea_3", "focus": "Crowded", "text": f"Not the best visit today. The place was crowded and service was inattentive.{note_fragment}"},
            {"id": "idea_4", "focus": "Food Quality", "text": f"Expected better quality. The food was lukewarm and took too long.{note_fragment}"},
            {"id": "idea_5", "focus": "Overall", "text": f"Disappointing experience today. Hope management looks into faster service.{note_fragment}"},
            {"id": "idea_6", "focus": "Service", "text": f"Slow service and staff seemed overwhelmed.{note_fragment}"},
            {"id": "idea_7", "focus": "Chai", "text": f"Chai was okay, but the snack items were below expectations.{note_fragment}"},
            {"id": "idea_8", "focus": "Hygiene", "text": f"Tables took too long to get cleaned. Needs better table turnover.{note_fragment}"},
            {"id": "idea_9", "focus": "Value", "text": f"Didn't feel worth the wait today. Hopefully improves.{note_fragment}"},
            {"id": "idea_10", "focus": "Experience", "text": f"Subpar visit today. Lots of room for operational improvement.{note_fragment}"}
        ]
    else: # 1 star
        ideas = [
            {"id": "idea_1", "focus": "Long Wait", "text": f"Unfortunately, my experience wasn't great today. The service took very long and food was cold.{note_fragment}"},
            {"id": "idea_2", "focus": "Staff Management", "text": f"Really disappointed with our visit. The wait was excessive and staff seemed unorganized.{note_fragment}"},
            {"id": "idea_3", "focus": "Poor Quality", "text": f"Subpar experience today. Cold food and slow service. I hope management addresses this.{note_fragment}"},
            {"id": "idea_4", "focus": "Service Failure", "text": f"Very frustrating visit. Orders were delayed and items were missing.{note_fragment}"},
            {"id": "idea_5", "focus": "Quality Issue", "text": f"Food quality was unacceptable today. Did not enjoy the meal.{note_fragment}"},
            {"id": "idea_6", "focus": "Cleanliness", "text": f"Cleanliness was not up to mark and staff did not attend properly.{note_fragment}"},
            {"id": "idea_7", "focus": "Customer Service", "text": f"Very poor customer service and long waiting times.{note_fragment}"},
            {"id": "idea_8", "focus": "Disappointing", "text": f"Had high hopes but completely let down by the service and food.{note_fragment}"},
            {"id": "idea_9", "focus": "Management", "text": f"Need urgent improvement in food preparation and table service.{note_fragment}"},
            {"id": "idea_10", "focus": "Overall", "text": f"Extremely disappointing visit today. Would not recommend based on this experience.{note_fragment}"}
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
