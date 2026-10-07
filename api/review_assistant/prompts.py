"""
Humanized Prompt Engineering & Real-World Review Synthesis Engine for ChurnLens / Vajra.
Strictly adheres to:
1. Zero fabrication (never invent unmentioned dishes, staff names, or events).
2. Human-like natural phrasing (15-45 words, everyday language, no corporate jargon).
3. 1-2 contextual emojis for every rating level (tasteful, rating-appropriate).
4. Trilingual support: English, Hindi (Roman Hinglish), and Gujarati (Roman Gujlish).
   - Strict rule: Roman/Latin script for Hindi & Gujarati, strictly NO Devanagari or Gujarati script.
5. Hospitality category-aware topics (Café, Restaurant, Hotel, Salon, Breakfast, etc.).
"""

import random
from typing import List, Dict, Any, Optional

SYSTEM_HUMANIZED_PROMPT = """You are helping a customer write a short, genuine review to post on Google Maps.

CORE PRINCIPLES:
1. WRITE LIKE A NORMAL PERSON typing on their mobile phone, not like a marketing professional or AI.
2. SIMPLE EVERYDAY VOCABULARY: Short sentences, natural phrasing, natural punctuation.
3. STRICT ZERO FABRICATION:
   - Reflect ONLY information supplied by the customer or selected from the provided options.
   - NEVER invent dishes, drinks, ingredients, prices, staff names, wait times, parking, live music, discounts, or events that were not provided.
4. FORBIDDEN PHRASES: Do NOT use "culinary excellence", "exceptional hospitality", "truly unforgettable experience", "top-tier", "delighted", "remarkable", "artisanal craftsmanship", or corporate openings/closings.
5. LENGTH: 15 to 45 words. Never generate unnecessarily long reviews.
6. EMOJIS: Use 1 to 2 tasteful contextual emojis for 4-5 stars, 1 neutral (🙂) for 3 stars, and 0 or disappointed (😕😞) for 1-2 stars.
7. LANGUAGE & SCRIPT RULES:
   - If language is ENGLISH: write in simple, everyday conversational English.
   - If language is HINDI: write in natural ROMAN-SCRIPT HINGLISH (Latin letters only, e.g. "Yahan ka khana bahut tasty tha aur staff bhi kaafi friendly tha. Overall experience bahut accha raha."). Strictly DO NOT use Devanagari script.
   - If language is GUJARATI: write in natural ROMAN-SCRIPT GUJLISH (Latin letters only, e.g. "Ahiya nu food ekdum mast hatu ane staff pan khub friendly hato. Overall experience bahu saras rahyo."). Strictly DO NOT use Gujarati script.
8. STAR CALIBRATION:
   - 5 Stars: Warm, enthusiastic, positive, would return.
   - 4 Stars: Positive but natural and slightly measured.
   - 3 Stars: Balanced and neutral, decent experience with minor drawback noted honestly.
   - 2 Stars: Disappointed with specific aspect, constructive, hope for improvement.
   - 1 Star: Honest dissatisfaction without aggression, polite but firm, suitable for private feedback.

Output ONLY the review text. No quotes, no intro, no conversational filler.
"""

# Hospitality topics mapped by category
HOSPITALITY_CATEGORY_TOPICS = {
    "cafe": [
        "Food & Taste",
        "Chai / Coffee",
        "Staff",
        "Service",
        "Ambience",
        "Cleanliness",
        "Value for Money",
    ],
    "restaurant": [
        "Food & Taste",
        "Service",
        "Staff",
        "Ambience",
        "Cleanliness",
        "Portion Size",
        "Value for Money",
    ],
    "hotel": [
        "Room",
        "Cleanliness",
        "Staff",
        "Service",
        "Breakfast",
        "Location",
        "Comfort",
        "Ambience",
    ],
    "salon": [
        "Service",
        "Staff",
        "Cleanliness",
        "Experience",
        "Results",
        "Ambience",
    ],
    "breakfast": [
        "Breakfast",
        "Chai & Beverages",
        "Snacks",
        "Taste & Flavour",
        "Friendly Staff",
        "Cleanliness",
        "Value for Money",
        "Quick Service",
    ],
}

def normalize_language(lang: Optional[str]) -> str:
    """Normalizes language string to english, hindi, or gujarati. Defaults to english."""
    if not lang:
        return "english"
    l = str(lang).lower().strip()
    if "guj" in l:
        return "gujarati"
    if "hin" in l:
        return "hindi"
    return "english"

def get_category_topics(category: Optional[str]) -> List[str]:
    """Resolves sensible hospitality topics based on business category."""
    if not category:
        return HOSPITALITY_CATEGORY_TOPICS["breakfast"]
    cat_lower = category.lower().strip()
    if "cafe" in cat_lower or "coffee" in cat_lower:
        return HOSPITALITY_CATEGORY_TOPICS["cafe"]
    if "hotel" in cat_lower or "stay" in cat_lower or "resort" in cat_lower:
        return HOSPITALITY_CATEGORY_TOPICS["hotel"]
    if "salon" in cat_lower or "spa" in cat_lower or "parlour" in cat_lower or "parlor" in cat_lower:
        return HOSPITALITY_CATEGORY_TOPICS["salon"]
    if "restaurant" in cat_lower or "dining" in cat_lower or "bistro" in cat_lower:
        return HOSPITALITY_CATEGORY_TOPICS["restaurant"]
    if "breakfast" in cat_lower or "snack" in cat_lower or "nasta" in cat_lower:
        return HOSPITALITY_CATEGORY_TOPICS["breakfast"]
    return [
        "Food & Taste",
        "Service",
        "Staff",
        "Ambience",
        "Cleanliness",
        "Value for Money",
    ]

# Contextual emoji mapping
EMOJI_MAP = {
    "coffee": "☕",
    "chai": "☕",
    "tea": "☕",
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
    "room": "🛏️",
    "comfort": "✨",
    "location": "📍",
    "value": "👍",
    "price": "👍",
    "portion": "🍽️",
    "results": "✨",
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

    if "breakfast" in aspect_text:
        emojis.append(EMOJI_MAP["breakfast"])
    elif any(k in aspect_text for k in ["chai", "tea", "beverage", "drink", "coffee"]):
        emojis.append(EMOJI_MAP["chai"])
    elif "snack" in aspect_text:
        emojis.append(EMOJI_MAP["snacks"])
    elif any(k in aspect_text for k in ["food", "taste", "flavour", "portion"]):
        emojis.append(EMOJI_MAP["taste"])
    elif any(k in aspect_text for k in ["room", "comfort"]):
        emojis.append(EMOJI_MAP["room"])
    elif "value" in aspect_text or "price" in aspect_text:
        emojis.append(EMOJI_MAP["value"])

    if any(k in aspect_text for k in ["ambience", "atmosphere", "vibe", "results"]):
        emojis.append(EMOJI_MAP["atmosphere"])
    elif any(k in aspect_text for k in ["service", "staff", "experience"]):
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

    selected = emojis[:2] if preference == "light" else emojis[:1]
    return " " + "".join(selected) if selected else ""

def generate_candidate_ideas(
    rating: int,
    aspects: List[str],
    user_note: str = "",
    business_name: str = "Nasta Ghar",
    language: str = "english",
    business_category: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Generates 5 distinct, human-sounding review candidate ideas based on:
    - rating (1-5 calibrated tone)
    - selected language: english, hindi (Roman Hinglish), or gujarati (Roman Gujlish)
    - selected hospitality aspects and user note
    - zero fabrication: never invents unprovided details
    """
    lang = normalize_language(language)
    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]

    # Safely format note fragment without trailing punctuation conflicts
    note_fragment = ""
    if user_note and user_note.strip():
        n = user_note.strip().rstrip(".!")
        note_fragment = f" {n}."

    # Language badge helper
    lang_badge = "English" if lang == "english" else ("Hindi" if lang == "hindi" else "Gujarati")

    # Detect hospitality focus keywords
    has_chai = any("chai" in a or "tea" in a or "drink" in a or "beverage" in a or "coffee" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a or "flavour" in a or "breakfast" in a or "snack" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_vibe = any("ambience" in a or "vibe" in a or "atmosphere" in a for a in cleaned_aspects)
    has_clean = any("clean" in a for a in cleaned_aspects)
    has_value = any("value" in a or "price" in a or "money" in a for a in cleaned_aspects)
    has_room = any("room" in a or "comfort" in a or "stay" in a for a in cleaned_aspects)

    if lang == "hindi":
        # ─── HINDI (ROMAN SCRIPT / HINGLISH) ──────────────────────────────
        if rating == 5:
            food_word = "breakfast aur chai" if has_chai else ("khana aur taste" if has_food else "service")
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Bahut accha experience raha aur {food_word} sach me lajawab tha!{note_fragment} Loved it 😊👌", "language": "hindi"},
                {"id": "idea_2", "focus": "Taste & Service", "text": f"Food ekdum fresh tha aur staff ka nature bhi kaafi polite tha.{note_fragment} Quick service mili 😋👍", "language": "hindi"},
                {"id": "idea_3", "focus": "Staff & Ambience", "text": f"Staff ka behaviour bahut friendly tha aur jagah bilkul clean thi.{note_fragment} Bohot achha time spend hua ✨😊", "language": "hindi"},
                {"id": "idea_4", "focus": "Taste & Value", "text": f"Har cheez garam aur fresh serve hui. Taste badhiya tha aur price bhi reasonable hai.{note_fragment} Jarur try karein 👌🍽️", "language": "hindi"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Hamara visit {business_name} par bohot accha raha. Badhiya service, fresh taste aur welcoming log.{note_fragment} Definitely wapas aayenge! ❤️🌟", "language": "hindi"},
            ]
        elif rating == 4:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Accha khana aur pleasant atmosphere.{note_fragment} Ek badhiya visit rahi 👍😊", "language": "hindi"},
                {"id": "idea_2", "focus": "Taste & Service", "text": f"Khana fresh tha aur staff ne bhi achhe se attend kiya.{note_fragment} Service time par mili 👍☕", "language": "hindi"},
                {"id": "idea_3", "focus": "Clean & Fair", "text": f"Saaf-suthri jagah hai aur pricing bhi fair hai.{note_fragment} Food quality acchi lagi 😊", "language": "hindi"},
                {"id": "idea_4", "focus": "Staff & Ambience", "text": f"Staff helpful tha aur seating comfortable thi. Taste bhi accha tha.{note_fragment} Ek baar aane layak jagah hai 🌟👍", "language": "hindi"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall kaafi accha experience raha. Taste aur service dono satisfactory the.{note_fragment} Fir se visit karenge 😊", "language": "hindi"},
            ]
        elif rating == 3:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Khana theek tha, lekin aaj service thodi slow lagi.{note_fragment} Average visit 🙂", "language": "hindi"},
                {"id": "idea_2", "focus": "Taste & Wait", "text": f"Taste decent tha, par order aane me thoda zyada time lag gaya.{note_fragment} Theek-thaak raha 🙂☕", "language": "hindi"},
                {"id": "idea_3", "focus": "Ambience & Service", "text": f"Staff polite tha par thoda rush zyada tha.{note_fragment} Service me thoda improvement ho sakta hai 🙂", "language": "hindi"},
                {"id": "idea_4", "focus": "Food & Prep", "text": f"Food theek-thaak tha, thoda garam hota toh aur accha lagta.{note_fragment} Average experience 🙂", "language": "hindi"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall thik-thak visit raha. Jagah achhi hai par order delay hua.{note_fragment} Umeed hai agli baar behtar hoga 🙂", "language": "hindi"},
            ]
        elif rating == 2:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Khana average tha aur wait time kaafi lamba ho gaya.{note_fragment} Thoda disappointed 😕", "language": "hindi"},
                {"id": "idea_2", "focus": "Service Issue", "text": f"Aaj service se satisfaction nahi mila. Order late aaya aur khana lukewarm tha.{note_fragment} 😕", "language": "hindi"},
                {"id": "idea_3", "focus": "Cleanliness & Attention", "text": f"Staff ka dhyan nahi tha aur table safai me time laga.{note_fragment} Better service expect ki thi 😕", "language": "hindi"},
                {"id": "idea_4", "focus": "Taste & Delay", "text": f"Taste khas nahi tha aur order aane me kaafi der hui.{note_fragment} Management ko thoda dhyan dena chahiye 😕", "language": "hindi"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Aaj ka visit disappointing raha. Service kaafi unorganized thi aur wait karna pada.{note_fragment} Hope this improves 😕", "language": "hindi"},
            ]
        else: # 1 star
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Bahut slow service aur khana bhi thanda tha.{note_fragment} Kaafi bura experience raha 😞", "language": "hindi"},
                {"id": "idea_2", "focus": "Order Delay", "text": f"Aaj ka experience bilkul accha nahi raha. Lamba wait karwaya aur order galat aaya.{note_fragment} 😞", "language": "hindi"},
                {"id": "idea_3", "focus": "Staff & Cleanliness", "text": f"Tables saaf nahi thi aur staff careless laga.{note_fragment} Service me kaafi kami hai 😞", "language": "hindi"},
                {"id": "idea_4", "focus": "Food & Attention", "text": f"Khana fresh nahi tha aur koi attend karne wala bhi nahi tha.{note_fragment} Total disappointment 😞", "language": "hindi"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Bohot kharab experience raha aaj. Slow service aur thanda khana.{note_fragment} Management needs major improvement 😞", "language": "hindi"},
            ]

    elif lang == "gujarati":
        # ─── GUJARATI (ROMAN SCRIPT / GUJLISH) ────────────────────────────
        if rating == 5:
            food_word = "nasto ane chai" if has_chai else ("food ane taste" if has_food else "service")
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Ahiya nu {food_word} ekdum mast hatu ane service pan jordar.{note_fragment} Bahu maza aavi! 🍳☕😋", "language": "gujarati"},
                {"id": "idea_2", "focus": "Taste & Service", "text": f"Food khub fresh ane tasty hatu. Staff pan ekdum polite ane helpful hato.{note_fragment} Quick service mali 👌😊", "language": "gujarati"},
                {"id": "idea_3", "focus": "Staff & Ambience", "text": f"Staff no swabhav bahu saras hato ane jagya ekdum chokhi hati.{note_fragment} Khub gamyu ahiya aavi ne ✨😊", "language": "gujarati"},
                {"id": "idea_4", "focus": "Taste & Value", "text": f"Badhu garam ane fresh hatu. Taste ekdum authentic ane rates pan reasonable che.{note_fragment} Must try 👌🍲", "language": "gujarati"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"{business_name} ni visit ekdum saras rahi. Food mast, staff premal ane relaxed vatavaran.{note_fragment} Fari thi chokkas aavishu! ❤️👍", "language": "gujarati"},
            ]
        elif rating == 4:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food saras hatu ane vatavaran pan acchu hatu.{note_fragment} Ek vaar javay evo anubhav 🍳👍", "language": "gujarati"},
                {"id": "idea_2", "focus": "Taste & Service", "text": f"Nasto ekdum garam ane tasty hato. Staff no response pan quick hato.{note_fragment} Saras service mali 😊☕", "language": "gujarati"},
                {"id": "idea_3", "focus": "Clean & Fair", "text": f"Chokkhai sarasi hati ane price pan yogya che.{note_fragment} Food quality acchi lagi 👍😊", "language": "gujarati"},
                {"id": "idea_4", "focus": "Staff & Ambience", "text": f"Staff helpful hato ane besvani vyavastha sari che.{note_fragment} Khub anand aavyo 🌟👍", "language": "gujarati"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall visit khub sari rahi. Badhu vyavasthit hatu ane taste pan gamyu.{note_fragment} Fari mulakat laishu 😊", "language": "gujarati"},
            ]
        elif rating == 3:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food theek hatu, pan aaje service thodi dhimi lagi.{note_fragment} Average anubhav 🙂", "language": "gujarati"},
                {"id": "idea_2", "focus": "Taste & Wait", "text": f"Taste barabar hato, pan order aavta vaar lagi.{note_fragment} Theek-thaak rahya aaje 🙂☕", "language": "gujarati"},
                {"id": "idea_3", "focus": "Ambience & Service", "text": f"Staff polite hato pan rush lidhe order delay thayo.{note_fragment} Service sudharvani jarur che 🙂", "language": "gujarati"},
                {"id": "idea_4", "focus": "Food & Prep", "text": f"Food thodu thandu hatu, thodu garam hoy to vadhare maza aave.{note_fragment} Average visit 🙂", "language": "gujarati"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall theek-thaak visit rahi. Taste decent pan service thodi slow hati.{note_fragment} Aasha che aagal sudharo thase 🙂", "language": "gujarati"},
            ]
        elif rating == 2:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food average hatu ane aaje wait time bahu vadhare hato.{note_fragment} Nirasha thai 😕", "language": "gujarati"},
                {"id": "idea_2", "focus": "Service Issue", "text": f"Service ma maza na aavi aaje. Order late aavyo ane food lukewarm hatu.{note_fragment} 😕", "language": "gujarati"},
                {"id": "idea_3", "focus": "Cleanliness & Attention", "text": f"Staff dhyan na aaptu hatu ane table chokkha na hata.{note_fragment} Vadhu sari service ni apeksha hati 😕", "language": "gujarati"},
                {"id": "idea_4", "focus": "Taste & Delay", "text": f"Taste khas na lagyo ane order mate lambo wait karvo padhyo.{note_fragment} Improvement joiye 😕", "language": "gujarati"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Aaje visit disappointing rahi. Service unorganized hati ane time pan kharab thayo.{note_fragment} Hope this improves 😕", "language": "gujarati"},
            ]
        else: # 1 star
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Bahu slow service ane food pan thandu hatu.{note_fragment} Khub kharab anubhav thayo 😞", "language": "gujarati"},
                {"id": "idea_2", "focus": "Order Delay", "text": f"Aaje bilkul maza na aavi. Lambo wait karavyo ane order pan barabar na aavyo.{note_fragment} 😞", "language": "gujarati"},
                {"id": "idea_3", "focus": "Staff & Cleanliness", "text": f"Tables chokkha na hata ane staff beparwah hatu.{note_fragment} Service khub kharab hati 😞", "language": "gujarati"},
                {"id": "idea_4", "focus": "Food & Attention", "text": f"Food fresh na hatu ane koi dhyan pan aaptu na hatu.{note_fragment} Khub nirasha thai 😞", "language": "gujarati"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Bahu kharab visit rahi aaje. Thandu food ane careless staff.{note_fragment} Management ne sudhara ni sakht jarur che 😞", "language": "gujarati"},
            ]

    else:
        # ─── ENGLISH ──────────────────────────────────────────────────────
        if rating == 5:
            item_phrase = "breakfast and chai" if has_chai else ("food and taste" if has_food else "service and hospitality")
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Amazing {item_phrase} and great experience!{note_fragment} Loved it 🍳☕", "language": "english"},
                {"id": "idea_2", "focus": "Food & Service", "text": f"The food was fresh and flavourful, and service was quick.{note_fragment} Truly satisfied 😋👍", "language": "english"},
                {"id": "idea_3", "focus": "Staff & Ambience", "text": f"Very friendly staff and very clean place.{note_fragment} We had a wonderful time here 😊✨", "language": "english"},
                {"id": "idea_4", "focus": "Taste & Value", "text": f"Everything was served hot, fresh and full of flavour. Fair prices and great quality.{note_fragment} Must try 👌🍲", "language": "english"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Had a wonderful visit at {business_name}. Great food, friendly people, and relaxed vibe.{note_fragment} Will surely visit again! 👨‍👩‍👧‍👦❤️", "language": "english"},
            ]
        elif rating == 4:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Good food and tasty chai!{note_fragment} Nice start to the morning 🍳", "language": "english"},
                {"id": "idea_2", "focus": "Food & Service", "text": f"Fresh breakfast and quick service.{note_fragment} Staff was polite and helpful 👍☕", "language": "english"},
                {"id": "idea_3", "focus": "Clean & Fair", "text": f"Clean sitting area and good food quality.{note_fragment} Prices are also reasonable 😊", "language": "english"},
                {"id": "idea_4", "focus": "Snacks & Ambience", "text": f"Enjoyed the snacks and warm ambience. Food arrived promptly and tasted nice.{note_fragment} Worth a visit 🥪🍲", "language": "english"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall a very pleasant visit. Good taste, clean tables, and friendly service.{note_fragment} Will definitely come back again 🌟👍", "language": "english"},
            ]
        elif rating == 3:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Decent food, but the service was a bit slow today.{note_fragment} 🙂", "language": "english"},
                {"id": "idea_2", "focus": "Food & Wait", "text": f"The food was nice, but we had to wait some time for our order.{note_fragment} Okay experience overall 🙂☕", "language": "english"},
                {"id": "idea_3", "focus": "Staff & Service", "text": f"Staff was polite, but they were quite busy today.{note_fragment} Average visit 🙂", "language": "english"},
                {"id": "idea_4", "focus": "Busy Hours", "text": f"The place was crowded today. Food taste was fine, but table cleaning took longer than expected.{note_fragment} Average visit 🙂", "language": "english"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Fair experience overall. Tea was good and seating was fine, but service has room for improvement.{note_fragment} It was an okay visit 🙂", "language": "english"},
            ]
        elif rating == 2:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food was okay, but wait time was too long today.{note_fragment} 😕", "language": "english"},
                {"id": "idea_2", "focus": "Order Delay", "text": f"Not satisfied with the service today.{note_fragment} Order was delayed and food was lukewarm 😕", "language": "english"},
                {"id": "idea_3", "focus": "Attention & Staff", "text": f"Staff was inattentive and tables were not cleaned quickly.{note_fragment} Expected better service 😕", "language": "english"},
                {"id": "idea_4", "focus": "Slow Service", "text": f"We had to wait a long time to get our food today.{note_fragment} Need to improve customer service 😕⏳", "language": "english"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Disappointing visit today. The food was not fresh and service was very slow.{note_fragment} Hope management fixes this 😕", "language": "english"},
            ]
        else: # 1 star
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Very slow service and cold food today.{note_fragment} 😞", "language": "english"},
                {"id": "idea_2", "focus": "Order Issue", "text": f"Bad experience today.{note_fragment} Waited very long and our order was wrong 😞", "language": "english"},
                {"id": "idea_3", "focus": "Cleanliness & Care", "text": f"Staff was disorganized and tables were not clean.{note_fragment} Very poor service 😞", "language": "english"},
                {"id": "idea_4", "focus": "Food & Wait", "text": f"Disappointed with the visit. Food took forever to arrive and tasted stale.{note_fragment} Nobody came to attend us properly 😞👎", "language": "english"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Extremely poor experience today. Long waiting time, cold food, and careless staff.{note_fragment} Needs major improvement in service 😞", "language": "english"},
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
    business_name: str = "the restaurant",
    language: str = "english",
    business_category: Optional[str] = None
) -> str:
    """
    Deterministic Humanization Engine adhering to:
    - 15-45 words
    - contextual emojis
    - zero fabrication
    - selected language: english, hindi (Roman Hinglish), or gujarati (Roman Gujlish)
    """
    lang = normalize_language(language)

    # If customer selected an idea, personalize and ground it
    if selected_idea and selected_idea.strip():
        base_text = selected_idea.strip()
        if user_note and user_note.strip() and user_note.strip().lower() not in base_text.lower():
            n = user_note.strip().rstrip(".!")
            base_text = f"{base_text.rstrip('.! 😊❤️✨☕')} — {n}."
            if emoji_preference != "none":
                emojis = pick_tasteful_emojis(rating, aspects, emoji_preference)
                base_text = f"{base_text}{emojis}"
        return base_text

    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]
    has_coffee = any("coffee" in a or "chai" in a or "tea" in a or "drink" in a or "beverage" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a or "breakfast" in a or "snack" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_vibe = any("ambience" in a or "vibe" in a or "atmosphere" in a for a in cleaned_aspects)

    note_text = ""
    if user_note and user_note.strip():
        note_text = f" {user_note.strip().rstrip('.!')}."

    emojis = pick_tasteful_emojis(rating, aspects, emoji_preference)

    if lang == "hindi":
        # Roman Hinglish synthesis
        if rating == 5:
            if has_food and has_service:
                draft = f"Yahan ka khana bahut tasty tha aur staff bhi kaafi friendly tha.{note_text} Overall experience bahut accha raha{emojis}"
            elif has_coffee:
                draft = f"Chai aur snacks dono bahut badhiya the! Staff ne smile ke saath serve kiya.{note_text} Definitely wapas aayenge{emojis}"
            elif has_vibe:
                draft = f"Bohot hi pyara ambience hai aur food bhi fresh tha.{note_text} Yahan aakar bahut accha laga{emojis}"
            else:
                draft = f"Hamara visit bohot accha raha! Sabhi cheezein time par aur fresh mili.{note_text} Highly recommend karte hain{emojis}"
        elif rating == 4:
            if has_food:
                draft = f"Accha khana aur pleasant atmosphere tha. Staff ne bhi ache se attend kiya.{note_text} Ek acchi visit rahi{emojis}"
            else:
                draft = f"Service time par mili aur jagah bhi clean thi.{note_text} Overall kaafi accha experience raha{emojis}"
        elif rating == 3:
            draft = f"Khana theek tha par aane me thoda time laga.{note_text} Service me thoda improvement ho sakta hai.{emojis}"
        elif rating == 2:
            draft = f"Khana lukewarm tha aur service kaafi slow thi aaj.{note_text} Thoda disappointing experience raha.{emojis}"
        else: # 1 star
            draft = f"Bohot slow service aur thanda khana mila aaj.{note_text} Staff careless laga aur visit bilkul accha nahi raha.{emojis}"

    elif lang == "gujarati":
        # Roman Gujlish synthesis
        if rating == 5:
            if has_food and has_service:
                draft = f"Ahiya nu food ekdum mast hatu ane staff pan khub friendly hato.{note_text} Overall experience bahu saras rahyo{emojis}"
            elif has_coffee:
                draft = f"Chai ane nasto ekdum jordar hatu! Fast service mali ane maja aavi.{note_text} Fari thi chokkas aavishu{emojis}"
            elif has_vibe:
                draft = f"Jagya khub shanti vali hati ane food pan ekdum fresh hatu.{note_text} Visit bahu sari rahi{emojis}"
            else:
                draft = f"{business_name} ni visit ekdum saras rahi. Badhu fresh ane swadist hatu.{note_text} Chokkas recommend karishu{emojis}"
        elif rating == 4:
            if has_food:
                draft = f"Food taste ma saras hatu ane staff no response pan quick hato.{note_text} Saras anubhav rahyo{emojis}"
            else:
                draft = f"Chokkhai sari hati ane seating pan comfortable hati.{note_text} Overall visit sari rahi{emojis}"
        elif rating == 3:
            draft = f"Taste theek hato pan order aavta vaar lagi.{note_text} Average experience rahyo aaje.{emojis}"
        elif rating == 2:
            draft = f"Order delay thayo ane food thandu hatu.{note_text} Service ma sudharo thavo joie.{emojis}"
        else: # 1 star
            draft = f"Aaje bilkul maza na aavi. Lambo wait karavyo ane food pan kharab hatu.{note_text} Bohot kharab anubhav thayo.{emojis}"

    else:
        # English synthesis
        if rating == 5:
            if has_coffee and has_service:
                draft = f"Really enjoyed the chai and coffee, and the staff were so friendly! Great place to relax.{note_text} Definitely coming back{emojis}"
            elif has_food and has_vibe:
                draft = f"Had a lovely meal here. The food was delicious and the place had such a warm vibe.{note_text} Highly recommend{emojis}"
            elif has_food and has_service:
                draft = f"Great food and really friendly service. Everything was served fresh with a smile.{note_text} Will definitely be back{emojis}"
            elif has_coffee:
                draft = f"Loved the beverages here! Freshly brewed and super welcoming staff.{note_text} Such a nice spot{emojis}"
            else:
                draft = f"Had a wonderful time! The staff were great and the whole visit was really pleasant.{note_text} Would happily recommend{emojis}"
        elif rating == 4:
            if has_food:
                draft = f"Had a really good time here. The food was tasty and the service was friendly.{note_text} Nice place to relax and eat{emojis}"
            elif has_coffee:
                draft = f"Solid spot with great drinks and good seating.{note_text} Staff were welcoming and items came out quickly{emojis}"
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

    # Word count safety check
    words = draft.split()
    if len(words) < 10 and rating >= 4:
        if lang == "hindi":
            draft += " Zaroor visit karein."
        elif lang == "gujarati":
            draft += " Chokkas visit karjo."
        else:
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
    business_name: str = "the restaurant",
    language: str = "english",
    business_category: Optional[str] = None
) -> str:
    lang = normalize_language(language)
    aspects_str = ", ".join(aspects) if aspects else "General hospitality experience"
    category_str = business_category or "Hospitality"

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
        lang_rule = """- TARGET LANGUAGE: HINDI IN ROMAN / LATIN SCRIPT (HINGLISH).
- STRICT MANDATE: Do NOT output Devanagari script. Use Roman letters only (e.g. "Yahan ka khana bahut tasty tha aur staff bhi kaafi friendly tha. Overall experience bahut accha raha.").
- STYLE: Casual Indian customer typing naturally on WhatsApp or Google Maps. Avoid textbook Hindi."""
    elif lang == "gujarati":
        lang_rule = """- TARGET LANGUAGE: GUJARATI IN ROMAN / LATIN SCRIPT (GUJLISH).
- STRICT MANDATE: Do NOT output Gujarati native script. Use Roman letters only (e.g. "Ahiya nu food ekdum mast hatu ane staff pan khub friendly hato. Overall experience bahu saras rahyo.").
- STYLE: Casual Gujarati customer typing naturally on mobile. Avoid textbook Gujarati."""
    else:
        lang_rule = """- TARGET LANGUAGE: Simple, everyday conversational English.
- STYLE: Casual customer typing on mobile."""

    return f"""Draft a short, human-like customer review for Google Maps:
- Business Name: {business_name}
- Category: {category_str}
- Star Rating: {rating} of 5 Stars
- Selected Topics: {aspects_str}
- {note_instruction}
- {idea_instruction}
{lang_rule}
- Length: 15 to 45 words
- Emojis: {emoji_preference} (1-2 for 4-5 stars, 1 for 3 stars, 0 or sad for 1-2 stars)
- Tone: Calibrated to {rating} stars. Authentic, genuine, zero marketing buzzwords, strict zero fabrication.

Output ONLY the review text."""

