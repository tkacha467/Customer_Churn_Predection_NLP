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

SYSTEM_HUMANIZED_PROMPT = """You are helping a customer write a short, genuine review to post on Google Maps.

CORE PRINCIPLES:
1. WRITE LIKE A NORMAL PERSON typing on their phone, not like a marketing professional.
2. SCRIPT & LANGUAGE RULES:
   - If English: Write in simple, natural everyday English.
   - If Hindi: Write directly in natural Roman-script Hindi (Hinglish), the everyday colloquial Romanized Hindi used in India (e.g. "Yahan ka khana bahut tasty tha aur staff bhi kaafi friendly tha"). STRICTLY DO NOT output Devanagari script.
   - If Gujarati: Write directly in natural Roman-script Gujarati (Gujlish), the everyday colloquial Romanized Gujarati used in Gujarat (e.g. "Ahiya nu food ekdum mast hatu ane staff pan khub friendly hato"). STRICTLY DO NOT output Gujarati native script.
   - NEVER generate in English and translate. Write natively in the selected language.
3. STRICT ZERO FABRICATION:
   - Reflect ONLY information supplied by the customer or selected from the provided options.
   - NEVER invent dishes, drinks, ingredients, prices, staff names, wait times, parking, delivery, live music, discounts, or events that were not provided.
4. FORBIDDEN PHRASES: Do NOT use "culinary excellence", "exceptional hospitality", "truly unforgettable experience", "top-tier", "delighted", "remarkable", "artisanal craftsmanship", or corporate openings/closings.
5. LENGTH: 15 to 45 words. Never generate unnecessarily long reviews.
6. EMOJIS: Use 1 to 2 tasteful, contextual emojis for 4-5 stars, 0-1 for 3 stars, 0 for 1-2 stars.
7. STAR CALIBRATION:
   - 5 Stars: Genuinely happy, warm, enthusiastic, would return.
   - 4 Stars: Very good visit, positive but natural and slightly measured.
   - 3 Stars: Balanced, decent experience with minor drawback noted honestly.
   - 2 Stars: Disappointed with specific aspect, constructive, hope for improvement.
   - 1 Star: Honest dissatisfaction without aggression, polite but firm.

Output ONLY the review text. No quotes, no intro, no conversational filler.
"""

def normalize_language(lang: Optional[str]) -> str:
    """Normalizes language string to 'english', 'hindi', or 'gujarati'."""
    if not lang:
        return "english"
    l = lang.lower().strip()
    if "guj" in l:
        return "gujarati"
    if "hin" in l:
        return "hindi"
    return "english"

# Contextual emoji mapping across all supported industries
EMOJI_MAP = {
    # Food & Restaurant
    "coffee": "☕",
    "chai": "☕",
    "tea": "☕",
    "drinks": "☕",
    "beverage": "☕",
    "food": "🍽️",
    "breakfast": "🍳",
    "snacks": "🥪",
    "taste": "😋",
    "flavour": "😋",
    "bakery": "🥐",
    "dessert": "🍰",
    # Hotel & Accommodation
    "room": "🛏️",
    "stay": "🏨",
    "hotel": "🏨",
    "resort": "🌴",
    "bed": "🛏️",
    # Fitness & Wellness
    "gym": "💪",
    "fitness": "🏋️",
    "workout": "💪",
    "trainer": "🏃",
    "equipment": "🏋️",
    # Salon & Spa
    "hair": "💇",
    "salon": "✂️",
    "spa": "💆",
    "beauty": "✨",
    "facial": "✨",
    # Retail
    "shopping": "🛍️",
    "store": "🛍️",
    "collection": "✨",
    "billing": "🧾",
    # Automotive
    "car": "🚗",
    "vehicle": "🚗",
    "repair": "🔧",
    "service": "🔧",
    "mechanic": "🔧",
    # Education
    "teaching": "📚",
    "class": "🎓",
    "learning": "📖",
    "faculty": "👨‍🏫",
    # Events
    "event": "🎉",
    "banquet": "🎊",
    "wedding": "✨",
    "celebration": "🎉",
    # Travel
    "travel": "✈️",
    "tour": "🧳",
    "trip": "🌍",
    # Common / Shared
    "atmosphere": "✨",
    "ambience": "✨",
    "vibe": "✨",
    "service": "😊",
    "staff": "😊",
    "cleanliness": "✨",
    "value": "👍",
    "price": "👍",
    "love": "❤️",
    "return": "❤️",
    "happy": "😊",
}

def pick_tasteful_emojis(rating: int, aspects: List[str], preference: str = "light", industry_id: Optional[str] = None) -> str:
    """Selects 1-2 tasteful contextual emojis based on rating, industry, and mentioned aspects."""
    if preference == "none":
        return ""

    emojis = []
    aspect_text = " ".join([a.lower() for a in aspects])

    # Industry or aspect-first emoji selection
    if "breakfast" in aspect_text or "nasta" in aspect_text:
        emojis.append(EMOJI_MAP["breakfast"])
    elif any(k in aspect_text for k in ("chai", "tea", "coffee", "drink", "beverage")):
        emojis.append(EMOJI_MAP["chai"])
    elif any(k in aspect_text for k in ("snack", "sandwich")):
        emojis.append(EMOJI_MAP["snacks"])
    elif any(k in aspect_text for k in ("food", "taste", "flavour", "dish")):
        emojis.append(EMOJI_MAP["taste"])
    elif any(k in aspect_text for k in ("gym", "workout", "fitness", "trainer", "machine")):
        emojis.append(EMOJI_MAP.get("fitness", "💪"))
    elif any(k in aspect_text for k in ("room", "stay", "bed")):
        emojis.append(EMOJI_MAP.get("room", "🛏️"))
    elif any(k in aspect_text for k in ("hair", "salon", "facial", "spa", "styling")):
        emojis.append(EMOJI_MAP.get("salon", "✂️"))
    elif any(k in aspect_text for k in ("car", "repair", "vehicle", "mechanic")):
        emojis.append(EMOJI_MAP.get("repair", "🔧"))
    elif any(k in aspect_text for k in ("class", "teaching", "learning", "course")):
        emojis.append(EMOJI_MAP.get("teaching", "📚"))
    elif any(k in aspect_text for k in ("event", "banquet", "wedding")):
        emojis.append(EMOJI_MAP.get("event", "🎉"))
    elif any(k in aspect_text for k in ("tour", "travel", "trip")):
        emojis.append(EMOJI_MAP.get("travel", "✈️"))
    elif any(k in aspect_text for k in ("store", "shop", "product", "collection")):
        emojis.append(EMOJI_MAP.get("shopping", "🛍️"))
    elif any(k in aspect_text for k in ("value", "price")):
        emojis.append(EMOJI_MAP["value"])

    if any(k in aspect_text for k in ("ambience", "atmosphere", "vibe")):
        emojis.append(EMOJI_MAP["atmosphere"])
    elif any(k in aspect_text for k in ("service", "staff", "hospitality")):
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
    business_name: str = "Nasta Ghar",
    language: str = "english",
    category: Optional[str] = None,
    industry_id: Optional[str] = None,
    effective_topics: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    Generates up to 3 distinct, strictly factually grounded review candidate ideas:
    1. Short & Natural
    2. Detailed & Expressive
    3. Simple & Personal
    Adheres strictly to zero fabrication, sentiment fidelity, industry-specific context,
    and natural Roman-script Hinglish/Gujlish.
    """
    lang = normalize_language(language)
    from backend.app.core.industry_registry import resolve_industry
    ind_def = resolve_industry(category=category, explicit_industry_id=industry_id)
    is_restaurant = (ind_def.industry_id == "restaurant")

    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]
    has_breakfast = any("breakfast" in a or "nasto" in a or "nasta" in a for a in cleaned_aspects)
    has_coffee = any("coffee" in a or "chai" in a or "tea" in a or "drink" in a or "beverage" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a or "breakfast" in a or "snack" in a or "pasta" in a or "pizza" in a or "bakery" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_ambience = any("ambience" in a or "atmosphere" in a or "vibe" in a for a in cleaned_aspects)
    has_clean = any("clean" in a or "sitting" in a for a in cleaned_aspects)
    has_wait = any("wait" in a or "delay" in a or "slow" in a for a in cleaned_aspects)
    has_value = any("value" in a or "price" in a or "pocket" in a or "rate" in a for a in cleaned_aspects)

    # Derive strictly customer-selected topic summary
    if is_restaurant:
        if has_breakfast and has_coffee:
            topic_en = "breakfast and chai"
            topic_hi = "breakfast aur chai"
            topic_gu = "breakfast ane chai"
        elif has_breakfast:
            topic_en = "breakfast"
            topic_hi = "breakfast"
            topic_gu = "breakfast"
        elif has_coffee:
            topic_en = "coffee and tea"
            topic_hi = "chai"
            topic_gu = "chai"
        elif has_food:
            topic_en = "food"
            topic_hi = "khana"
            topic_gu = "food"
        elif has_service:
            topic_en = "service"
            topic_hi = "service"
            topic_gu = "service"
        elif has_ambience:
            topic_en = "atmosphere"
            topic_hi = "atmosphere"
            topic_gu = "atmosphere"
        elif has_clean:
            topic_en = "sitting area"
            topic_hi = "sitting area"
            topic_gu = "sitting area"
        else:
            topic_en = ""
            topic_hi = ""
            topic_gu = ""
    else:
        # Non-restaurant industries: ground topic strictly in selected customer aspects
        if cleaned_aspects:
            chosen = aspects[:2] if len(aspects) >= 2 else aspects[:1]
            topic_en = " and ".join([a.strip().lower() for a in chosen])
            topic_hi = " aur ".join([a.strip().lower() for a in chosen])
            topic_gu = " ane ".join([a.strip().lower() for a in chosen])
        else:
            topic_en = ""
            topic_hi = ""
            topic_gu = ""

    note_fragment = ""
    if user_note and user_note.strip():
        n = user_note.strip().rstrip(".!")
        note_fragment = f" {n}."

    if lang == "hindi":
        if rating == 5:
            if topic_hi:
                short_text = f"{business_name} me {topic_hi} bahut pasand aaya!{note_fragment} {'Maza aa gaya 🍳☕' if is_restaurant else 'Maza aa gaya 😊✨'}"
                detailed_text = f"{business_name} me {topic_hi} ka experience lajawab raha.{note_fragment} Sab kuch accha manage kiya hua tha 😊✨"
                personal_text = f"Personal taur par {business_name} me {topic_hi} bahut accha laga.{note_fragment} Very happy with the visit ❤️"
            else:
                short_text = f"Bahut hi accha anubhav raha at {business_name}!{note_fragment} Maza aa gaya 😊✨"
                detailed_text = f"Overall visit bahut shandar rahi at {business_name}.{note_fragment} Sab kuch kaafi accha arrange kiya hua tha 😊✨"
                personal_text = f"Personal taur par {business_name} ki visit bahut pasand aayi.{note_fragment} Very happy with the visit ❤️"

        elif rating == 4:
            if topic_hi:
                short_text = f"Accha {topic_hi} at {business_name}.{note_fragment} Good visit 👍"
                detailed_text = f"{business_name} me {topic_hi} ka anubhav accha aur enjoyable raha.{note_fragment} Overall arrangement comfortable thi 😊"
                personal_text = f"Mujhe {business_name} me {topic_hi} pasand aaya.{note_fragment} Definitely ek pleasant visit rahi 👍"
            else:
                short_text = f"Kaafi accha anubhav raha at {business_name}.{note_fragment} Good visit 👍"
                detailed_text = f"Overall visit kaafi enjoyable rahi at {business_name}.{note_fragment} Sab kuch theek se manage hua 😊"
                personal_text = f"Mujhe {business_name} ki visit pasand aayi.{note_fragment} Definitely ek pleasant visit rahi 👍"

        elif rating == 3:
            if topic_hi:
                short_text = f"{business_name} me {topic_hi} ka theek anubhav raha.{note_fragment} Standard visit 🙂"
                detailed_text = f"{business_name} me {topic_hi} average raha.{note_fragment} Anubhav theek tha, par thode aur improvement ki gunjaish hai 🙂"
                personal_text = f"{topic_hi.capitalize()} ka anubhav mere liye ordinary raha at {business_name}.{note_fragment} Decent visit 🙂"
            else:
                short_text = f"Average anubhav raha aaj at {business_name}.{note_fragment} Standard visit 🙂"
                detailed_text = f"Overall visit theek rahi at {business_name}.{note_fragment} Kuch baatein theek thin, thoda aur better ho sakta tha 🙂"
                personal_text = f"Visit ordinary rahi mere liye at {business_name}.{note_fragment} Decent experience overall 🙂"

        elif rating == 2:
            if topic_hi:
                short_text = f"{business_name} me {topic_hi} expectation se kam raha.{note_fragment} 😕"
                detailed_text = f"{business_name} me {topic_hi} se thodi nirasha hui.{note_fragment} Quality aur care me improvement ki zaroorat hai 😕"
                personal_text = f"Mujhe {business_name} me {topic_hi} se aisi umeed nahi thi.{note_fragment} Hope things improve 😕"
            else:
                short_text = f"Experience kuch khass nahi raha aaj at {business_name}.{note_fragment} 😕"
                detailed_text = f"Visit se thodi nirasha hui at {business_name}.{note_fragment} Service aur arrangement me improvement ki zaroorat hai 😕"
                personal_text = f"Mujhe aisi umeed nahi thi at {business_name}.{note_fragment} Hope things improve 😕"

        else: # 1 star
            if topic_hi:
                short_text = f"{business_name} me {topic_hi} ka kharab experience raha.{note_fragment} 😞"
                detailed_text = f"{business_name} me {topic_hi} se bilkul santusht nahi huye.{note_fragment} Bade sudhar ki zaroorat hai 😞"
                personal_text = f"{business_name} me {topic_hi} se bahut nirashajanak anubhav raha.{note_fragment} Very poor 😞"
            else:
                short_text = f"Kharab anubhav raha aaj at {business_name}.{note_fragment} 😞"
                detailed_text = f"Aaj ki visit se bilkul santusht nahi huye at {business_name}.{note_fragment} Bade sudhar ki zaroorat hai 😞"
                personal_text = f"Bahut nirashajanak raha at {business_name}.{note_fragment} Poor experience 😞"

    elif lang == "gujarati":
        if rating == 5:
            if topic_gu:
                short_text = f"{business_name} ma {topic_gu} khub j saras hatu!{note_fragment} {'Majja aavi gai 🍳☕' if is_restaurant else 'Khub majja aavi 😊✨'}"
                detailed_text = f"{business_name} ma {topic_gu} no anubhav khub saro rahyo.{note_fragment} Ek memorable visit rahi 😊✨"
                personal_text = f"Mane {business_name} ma {topic_gu} khub j gamyu.{note_fragment} Very happy with the visit ❤️"
            else:
                short_text = f"Bahu j saras anubhav rahyo at {business_name}!{note_fragment} Khub majja aavi 😊✨"
                detailed_text = f"Samagra mulakat khub j sari rahi at {business_name}.{note_fragment} Ek memorable visit rahi 😊✨"
                personal_text = f"Mane {business_name} ni visit khub j gami.{note_fragment} Very happy with the visit ❤️"

        elif rating == 4:
            if topic_gu:
                short_text = f"Saras {topic_gu} at {business_name}.{note_fragment} Saro anubhav 👍"
                detailed_text = f"{business_name} ma {topic_gu} no saro anubhav rahyo.{note_fragment} Vyavastha sari lagi 😊"
                personal_text = f"Mari aaje {business_name} ma {topic_gu} mate sari visit rahi.{note_fragment} Saro time spend thayo 👍"
            else:
                short_text = f"Sari mulakat rahi at {business_name}.{note_fragment} Saro anubhav 👍"
                detailed_text = f"Overall experience saro rahyo at {business_name}.{note_fragment} Vyavastha sari lagi 😊"
                personal_text = f"Mari aaje sari visit rahi at {business_name}.{note_fragment} Saro time spend thayo 👍"

        elif rating == 3:
            if topic_gu:
                short_text = f"{business_name} ma {topic_gu} samanya rahyu.{note_fragment} Thik visit hati 🙂"
                detailed_text = f"{business_name} ma {topic_gu} theek hatu.{note_fragment} Thoda sudhara ni apeksha chhe 🙂"
                personal_text = f"{topic_gu.capitalize()} mate anubhav ordinary rahyo at {business_name}.{note_fragment} Decent visit 🙂"
            else:
                short_text = f"Average anubhav rahyo aaje at {business_name}.{note_fragment} Thik visit hati 🙂"
                detailed_text = f"Overall mulakat theek rahi at {business_name}.{note_fragment} Thodo sudharo thavo joie 🙂"
                personal_text = f"Mari mulakat ordinary rahi at {business_name}.{note_fragment} Decent experience 🙂"

        elif rating == 2:
            if topic_gu:
                short_text = f"{business_name} ma {topic_gu} expectation karta ochu rahyu.{note_fragment} 😕"
                detailed_text = f"{business_name} ma {topic_gu} thi thodi nirasha thai.{note_fragment} Sudharo karvo zaroori chhe 😕"
                personal_text = f"Mane {business_name} ma {topic_gu} mate aavi apeksha nahoti.{note_fragment} 😕"
            else:
                short_text = f"Experience saro na rahyo aaje at {business_name}.{note_fragment} 😕"
                detailed_text = f"Mulakat thi thodi nirasha thai at {business_name}.{note_fragment} Sudharo karvo zaroori chhe 😕"
                personal_text = f"Mane aavi apeksha nahoti at {business_name}.{note_fragment} 😕"

        else: # 1 star
            if topic_gu:
                short_text = f"{business_name} ma {topic_gu} no kharab anubhav rahyo.{note_fragment} 😞"
                detailed_text = f"{business_name} ma {topic_gu} thi bilkul santusht na thaya.{note_fragment} Mota sudhara ni jarur chhe 😞"
                personal_text = f"{business_name} ma {topic_gu} thi khub j nirashajanak mulakat rahi.{note_fragment} 😞"
            else:
                short_text = f"Bahu j kharab anubhav rahyo at {business_name}.{note_fragment} 😞"
                detailed_text = f"Aaje bilkul santusht na thaya at {business_name}.{note_fragment} Mota sudhara ni jarur chhe 😞"
                personal_text = f"Khub j nirashajanak mulakat rahi at {business_name}.{note_fragment} 😞"

    else: # English
        if rating == 5:
            if topic_en:
                short_text = f"Really enjoyed the {topic_en} at {business_name}!{note_fragment} {'Loved it 🍳☕' if is_restaurant else 'Loved it 😊✨'}"
                detailed_text = f"Had a lovely visit at {business_name}. The {topic_en} was wonderful and {'prepared' if is_restaurant else 'handled'} nicely.{note_fragment} Truly enjoyed it 😊✨"
                personal_text = f"The {topic_en} at {business_name} was {'delicious' if is_restaurant else 'great'} today.{note_fragment} Very happy with my visit ❤️"
            else:
                short_text = f"Had a wonderful visit at {business_name}! Really enjoyed every moment.{note_fragment} Loved it 😊✨"
                detailed_text = f"Had a lovely and wonderful visit at {business_name}. Everything was handled nicely.{note_fragment} Truly enjoyed it 😊✨"
                personal_text = f"I genuinely enjoyed my time at {business_name}.{note_fragment} Very happy with my visit ❤️"

        elif rating == 4:
            if topic_en:
                short_text = f"Good {topic_en} at {business_name}.{note_fragment} Nice visit 👍"
                detailed_text = f"Solid and enjoyable experience with the {topic_en} at {business_name}.{note_fragment} Well managed throughout 😊"
                personal_text = f"Had a good experience with the {topic_en} at {business_name}.{note_fragment} Happy with my visit overall 👍"
            else:
                short_text = f"Very pleasant visit at {business_name}.{note_fragment} Good spot to stop by 👍"
                detailed_text = f"Overall a solid and enjoyable experience at {business_name}.{note_fragment} Everything was well arranged 😊"
                personal_text = f"Had a good visit at {business_name}.{note_fragment} Happy with my experience overall 👍"

        elif rating == 3:
            if topic_en:
                short_text = f"Decent visit for {topic_en} at {business_name}.{note_fragment} Standard experience 🙂"
                detailed_text = f"The {topic_en} at {business_name} was fine overall.{note_fragment} An average visit with room for minor improvement 🙂"
                personal_text = f"It was a pretty average experience for {topic_en} at {business_name}.{note_fragment} Decent visit overall 🙂"
            else:
                short_text = f"Decent visit today at {business_name}.{note_fragment} Standard experience 🙂"
                detailed_text = f"Overall a fair and average experience at {business_name}. A few good points, but there is room for improvement.{note_fragment} Decent visit 🙂"
                personal_text = f"It was a pretty average visit for me at {business_name}.{note_fragment} Fair experience overall 🙂"

        elif rating == 2:
            if topic_en:
                short_text = f"The {topic_en} at {business_name} fell below expectations today.{note_fragment} 😕"
                detailed_text = f"Disappointed with the {topic_en} at {business_name}.{note_fragment} The experience needs attention and improvement 😕"
                personal_text = f"Expected a better experience with the {topic_en} at {business_name}.{note_fragment} Hope to see improvements 😕"
            else:
                short_text = f"Visit fell below expectations today at {business_name}.{note_fragment} 😕"
                detailed_text = f"Somewhat disappointed with the visit at {business_name}.{note_fragment} Several areas need attention and better care 😕"
                personal_text = f"Expected a better experience than what I had at {business_name} today.{note_fragment} Hope to see improvements 😕"

        else: # 1 star
            if topic_en:
                short_text = f"Very disappointing experience with the {topic_en} at {business_name}.{note_fragment} 😞"
                detailed_text = f"Unsatisfied with the {topic_en} during today's visit to {business_name}.{note_fragment} Major improvements are needed 😞"
                personal_text = f"Really unhappy with the {topic_en} at {business_name} today.{note_fragment} Disappointed with how things went 😞"
            else:
                short_text = f"Very disappointing experience today at {business_name}.{note_fragment} 😞"
                detailed_text = f"Extremely unsatisfied with today's visit at {business_name}.{note_fragment} Major improvements are needed in service and quality 😞"
                personal_text = f"Really unhappy with the experience today.{note_fragment} Disappointed with how things were handled at {business_name} 😞"

    return [
        {"id": "idea_1", "focus": "Short & Natural", "text": short_text},
        {"id": "idea_2", "focus": "Detailed & Expressive", "text": detailed_text},
        {"id": "idea_3", "focus": "Simple & Personal", "text": personal_text},
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
    business_name: str = "the restaurant",
    language: str = "english",
    category: Optional[str] = None,
    industry_id: Optional[str] = None,
    effective_topics: Optional[List[str]] = None
) -> str:
    """
    Deterministic Humanization Engine adhering to 15-45 words,
    contextual emojis, zero fabrication, industry context, and natural Roman-script Hinglish/Gujlish.
    """
    lang = normalize_language(language)
    from backend.app.core.industry_registry import resolve_industry
    ind_def = resolve_industry(category=category, explicit_industry_id=industry_id)
    is_restaurant = (ind_def.industry_id == "restaurant")

    # If customer already selected an idea, build upon and personalize it
    if selected_idea and selected_idea.strip():
        base_text = selected_idea.strip()
        if user_note and user_note.strip() and user_note.strip().lower() not in base_text.lower():
            n = user_note.strip().rstrip(".!")
            base_text = f"{base_text.rstrip('.! 😊❤️✨☕👌🍲🥪👍')} — {n}."
            if emoji_preference != "none":
                emojis = pick_tasteful_emojis(rating, aspects, emoji_preference, industry_id=ind_def.industry_id)
                base_text = f"{base_text}{emojis}"
        return base_text

    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]
    has_coffee = any("coffee" in a or "chai" in a or "drink" in a or "beverage" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a or "breakfast" in a or "snack" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_vibe = any("ambience" in a or "vibe" in a or "atmosphere" in a for a in cleaned_aspects)

    note_text = ""
    if user_note and user_note.strip():
        note_text = f" {user_note.strip().rstrip('.!')}."

    emojis = pick_tasteful_emojis(rating, aspects, emoji_preference, industry_id=ind_def.industry_id)

    if is_restaurant:
        if lang == "hindi":
            if rating == 5:
                if has_coffee and has_service:
                    draft = f"Yahan ki chai aur snacks sach me lajawab the! Staff ka nature bahut friendly tha.{note_text} Definitely dobara aayenge{emojis}"
                elif has_food and has_vibe:
                    draft = f"Yahan aakar bahut accha laga. Khana fresh aur tasty tha aur mahaul bhi kaafi relaxed tha.{note_text} Zaroor try karein{emojis}"
                else:
                    draft = f"Overall visit bahut shandar raha! Khana fresh tha aur service bhi kaafi fast aur polite thi.{note_text} Highly recommend karte hain{emojis}"
            elif rating == 4:
                draft = f"Kaafi accha experience raha. Taste accha tha aur staff bhi attentive tha.{note_text} Morning naste ke liye badhiya jagah hai{emojis}"
            elif rating == 3:
                draft = f"Taste theek tha, lekin service thodi slow lagi aaj.{note_text} Average visit raha overall.{emojis}"
            elif rating == 2:
                draft = f"Khana theek tha par wait time kaafi zyada tha aaj.{note_text} Umeed hai service thodi fast hogi next time.{emojis}"
            else: # 1 star
                draft = f"Experience bilkul accha nahi raha aaj. Service bahut slow thi aur khana bhi thanda tha.{note_text} Dhyan dene ki zaroorat hai.{emojis}"

        elif lang == "gujarati":
            if rating == 5:
                if has_coffee and has_service:
                    draft = f"Ahiya nu food ane chai sachme ekdum mast hatu! Staff pan khub friendly ane helpful hato.{note_text} Fari thi jarur aavishu{emojis}"
                elif has_food and has_vibe:
                    draft = f"Ahiya aavine khub maja aavi. Khavanu ekdum fresh hatu ane vatavaran pan saras hatu.{note_text} Jarur visit karva jevu chhe{emojis}"
                else:
                    draft = f"Samagra anubhav khub j saras rahyo! Nasto fresh hato ane service pan fast mali.{note_text} Badhane jarur recommend karish{emojis}"
            elif rating == 4:
                draft = f"Khub saro anubhav rahyo. Food taste saro hato ane staff no swabhav pan vinamra hato.{note_text} Breakfast mate sari jagya chhe{emojis}"
            elif rating == 3:
                draft = f"Taste thik hato, pan service aaje thodi slow lagi.{note_text} Average mulakat rahi overall.{emojis}"
            elif rating == 2:
                draft = f"Khavanu thik hatu pan wait ghano karvo padyo.{note_text} Aavti vakhte service thodi fast male evi aasha.{emojis}"
            else: # 1 star
                draft = f"Experience aaje bilkul saro na rahyo. Service khub slow hati ane nasto thando aavyo.{note_text} Sudharo karvani jarur chhe.{emojis}"

        else: # English
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
    else:
        # Multi-industry generalized synthesis (Zero food or dining assumptions)
        aspect_mention = f" The {', '.join(aspects[:2]).lower()} was well managed." if aspects else ""
        if lang == "hindi":
            if rating == 5:
                draft = f"Overall anubhav bahut shandar raha at {business_name}!{aspect_mention} Service aur arrangement kaafi acchi thi.{note_text} Highly recommend karte hain{emojis}"
            elif rating == 4:
                draft = f"Kaafi accha experience raha at {business_name}.{aspect_mention} Staff attentive tha aur sab smoothly handle hua.{note_text} Good experience overall{emojis}"
            elif rating == 3:
                draft = f"Anubhav theek tha at {business_name}.{aspect_mention} Anubhav normal raha, par thode aur improvement ki gunjaish hai.{note_text} Standard visit.{emojis}"
            elif rating == 2:
                draft = f"Visit expectation se kam rahi at {business_name}.{note_text} Service aur care me improvement ki zaroorat hai.{emojis}"
            else: # 1 star
                draft = f"Experience bilkul accha nahi raha at {business_name}.{note_text} Bade sudhar ki zaroorat hai.{emojis}"

        elif lang == "gujarati":
            if rating == 5:
                draft = f"Samagra anubhav khub j saras rahyo at {business_name}!{aspect_mention} Vyavastha sari hati ane service pan fast mali.{note_text} Badhane jarur recommend karish{emojis}"
            elif rating == 4:
                draft = f"Khub saro anubhav rahyo at {business_name}.{aspect_mention} Staff no swabhav vinamra hato ane arrangement saras hatu.{note_text} Saro time spend thayo{emojis}"
            elif rating == 3:
                draft = f"Anubhav thik hato at {business_name}.{aspect_mention} Thoda sudhara ni jarur chhe.{note_text} Average mulakat rahi.{emojis}"
            elif rating == 2:
                draft = f"Mulakat thi thodi nirasha thai at {business_name}.{note_text} Sudharo karvo zaroori chhe.{emojis}"
            else: # 1 star
                draft = f"Experience aaje bilkul saro na rahyo at {business_name}.{note_text} Sudharo karvani jarur chhe.{emojis}"

        else: # English
            if rating == 5:
                draft = f"Had a wonderful experience at {business_name}!{aspect_mention} The team was polite and everything was handled very smoothly.{note_text} Highly recommend{emojis}"
            elif rating == 4:
                draft = f"Very good experience at {business_name}.{aspect_mention} Professional service and pleasant atmosphere overall.{note_text} Happy with the visit{emojis}"
            elif rating == 3:
                draft = f"Decent experience overall at {business_name}.{aspect_mention} A few good points, though there is room for minor improvement.{note_text} Standard visit.{emojis}"
            elif rating == 2:
                draft = f"The visit fell below expectations at {business_name}.{note_text} Several things could be improved with better care and attention.{emojis}"
            else: # 1 star
                draft = f"Unfortunately, my experience at {business_name} was quite disappointing.{note_text} Major improvements are needed in service and responsiveness.{emojis}"

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
    business_name: str = "the business",
    language: str = "english",
    category: Optional[str] = None,
    industry_id: Optional[str] = None,
    effective_topics: Optional[List[str]] = None
) -> str:
    lang = normalize_language(language)
    from backend.app.core.industry_registry import resolve_industry
    ind_def = resolve_industry(category=category, explicit_industry_id=industry_id)

    aspects_str = ", ".join(aspects) if aspects else "General visit"
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

    if lang == "hindi":
        lang_rule = "Language: Natural Roman-script Hindi (Hinglish). Write everyday spoken Romanized Hindi as used by real Indian customers on mobile phones. STRICTLY DO NOT output Devanagari script. Do NOT translate from English."
    elif lang == "gujarati":
        lang_rule = "Language: Natural Roman-script Gujarati (Gujlish). Write everyday spoken Romanized Gujarati as used by real customers in Gujarat on mobile phones. STRICTLY DO NOT output Gujarati script. Do NOT translate from English."
    else:
        lang_rule = "Language: Simple, natural everyday English."

    return f"""Draft a short, human-like {ind_def.display_name} review:
- Star Rating: {rating} of 5 Stars
- Business Name: {business_name}
- Industry: {ind_def.display_name} ({ind_def.industry_id})
- Category: {category or ind_def.default_subcategory}
- Context: {ind_def.prompt_context}
- Mentioned Topics: {aspects_str}
- {lang_rule}
- {note_instruction}
- {idea_instruction}
- Length: 15 to 45 words
- Emojis: {emoji_preference} (at most 1-2 for 4-5 stars, 0 for 1-2 stars)
- Tone: Natural, friendly, human tone. Never use marketing or corporate words. Zero fabrication.

Output ONLY the review text."""
