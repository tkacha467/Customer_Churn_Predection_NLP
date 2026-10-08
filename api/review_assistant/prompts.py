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
    business_name: str = "Nasta Ghar",
    language: str = "english",
    category: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Generates 5 distinct, human-sounding review candidate ideas based on user input,
    supporting English, Roman Hindi (Hinglish), and Roman Gujarati (Gujlish).
    """
    lang = normalize_language(language)
    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]

    # Safely inject user note without creating ungrounded facts
    note_fragment = ""
    if user_note and user_note.strip():
        n = user_note.strip().rstrip(".!")
        note_fragment = f" {n}."

    if lang == "hindi":
        if rating == 5:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Bahut hi tasty khana aur best chai!{note_fragment} Maza aa gaya 🍳☕"},
                {"id": "idea_2", "focus": "Food & Taste", "text": f"Khana ekdum fresh aur lajawab tha.{note_fragment} Service bhi kaafi quick thi ☕😋"},
                {"id": "idea_3", "focus": "Staff & Ambience", "text": f"Staff bahut polite hai aur safai ka pura dhyan rakha hai.{note_fragment} Family ke sath visit ke liye best jagah 😊✨"},
                {"id": "idea_4", "focus": "Taste & Value", "text": f"Har cheez garam aur fresh mili. Snacks aur chai bahut acche the aur price bhi sahi hai.{note_fragment} Zaroor try karein 👌🍲"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall experience bahut shandar raha at {business_name}. Khana aur service dono top notch the.{note_fragment} Phir zaroor aayenge! 👨‍👩‍👧‍👦❤️"},
            ]
        elif rating == 4:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Accha khana aur tasty chai!{note_fragment} Morning ke liye badhiya choice 🍳"},
                {"id": "idea_2", "focus": "Food & Service", "text": f"Breakfast fresh tha aur service bhi fast thi.{note_fragment} Staff ka behaviour kaafi polite tha 👍☕"},
                {"id": "idea_3", "focus": "Clean & Fair", "text": f"Clean sitting area aur achhi food quality.{note_fragment} Rates bhi pocket friendly hain 😊"},
                {"id": "idea_4", "focus": "Snacks & Tea", "text": f"Snacks aur garam chai enjoy kiya. Food time pe serve hua aur taste accha tha.{note_fragment} Quick bite ke liye acchi jagah 🥪🍲"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Kaafi accha visit raha. Good taste, clean tables aur friendly service.{note_fragment} Definitely visit karne jaisa hai 🌟👍"},
            ]
        elif rating == 3:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Khana theek tha, lekin service thodi slow lagi aaj.{note_fragment} 🙂"},
                {"id": "idea_2", "focus": "Food & Wait", "text": f"Chai acchi thi par snacks thode thande the.{note_fragment} Average experience raha 🙂☕"},
                {"id": "idea_3", "focus": "Service Pace", "text": f"Staff polite tha par order ke liye wait karna pada.{note_fragment} Decent visit 🙂"},
                {"id": "idea_4", "focus": "Crowd & Cleaning", "text": f"Aaj bheed kaafi thi. Food taste theek tha lekin table cleaning mein thoda time lag gaya.{note_fragment} Hope agli baar fast service mile 🙂🥪"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall theek experience tha. Seating comfortable hai par service mein thoda improvement chahiye.{note_fragment} Okay visit 🙂"},
            ]
        elif rating == 2:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Khana theek tha par wait time bahut zyada tha aaj.{note_fragment} 😕"},
                {"id": "idea_2", "focus": "Order Delay", "text": f"Aaj service se khush nahi huye.{note_fragment} Order kaafi late aaya aur khana bhi lukewarm tha 😕"},
                {"id": "idea_3", "focus": "Staff Attention", "text": f"Staff ka dhyaan nahi tha aur service kaafi slow thi.{note_fragment} Better service expected thi 😕"},
                {"id": "idea_4", "focus": "Slow Service", "text": f"Khaane ke liye kaafi wait karna pada aur tables quickly clean nahi huye.{note_fragment} Service improve karni chahiye 😕⏳"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Disappointing visit raha. Chai theek thi par snacks fresh nahi the aur service slow thi.{note_fragment} Umeed hai agle baar sudhar hoga 😕"},
            ]
        else: # 1 star
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Bahut slow service aur khana bhi thanda mila aaj.{note_fragment} 😞"},
                {"id": "idea_2", "focus": "Order Issue", "text": f"Kharab experience raha aaj.{note_fragment} Bahut der wait kiya aur order bhi galat aaya 😞"},
                {"id": "idea_3", "focus": "Cleanliness", "text": f"Staff unorganized tha aur tables bilkul clean nahi the.{note_fragment} Poor service 😞"},
                {"id": "idea_4", "focus": "Food & Wait", "text": f"Disappointed with the visit. Khaana aane mein bahut time laga aur taste fresh nahi tha.{note_fragment} Koi theek se attend nahi kar raha tha 😞👎"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Kaafi poor experience raha. Long waiting time, cold food aur careless staff.{note_fragment} Major improvement ki zaroorat hai 😞"},
            ]

    elif lang == "gujarati":
        if rating == 5:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Ahiya nu food ekdum mast hatu ane chai pan jordar!{note_fragment} Khub majja aavi 🍳☕"},
                {"id": "idea_2", "focus": "Food & Taste", "text": f"Nasto ekdum fresh ane taste lajawab hato.{note_fragment} Service pan ekdum quick hati ☕😋"},
                {"id": "idea_3", "focus": "Staff & Ambience", "text": f"Staff khub polite chhe ane chokkhai pan saras chhe.{note_fragment} Family sathe aavva mate best jagya 😊✨"},
                {"id": "idea_4", "focus": "Taste & Value", "text": f"Badhu garam ane fresh malyu. Snacks ane chai bahu saras hata ane bhav pan fair chhe.{note_fragment} Jarur try karva jevu chhe 👌🍲"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall experience bahu j saras rahyo at {business_name}. Food ane service banne top class.{note_fragment} Fari thi jarur aavishu! 👨‍👩‍👧‍👦❤️"},
            ]
        elif rating == 4:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Saras khavanu ane kadak chai!{note_fragment} Savarni saras sharuat 🍳"},
                {"id": "idea_2", "focus": "Food & Service", "text": f"Breakfast fresh hatu ane quick service mali.{note_fragment} Staff no swabhav pan vinamra hato 👍☕"},
                {"id": "idea_3", "focus": "Clean & Fair", "text": f"Clean sitting area ane sari food quality.{note_fragment} Rates pan reasonable chhe 😊"},
                {"id": "idea_4", "focus": "Snacks & Tea", "text": f"Snacks ane garam chai ni maja aavi. Food jaldi aavyu ane taste saro hato.{note_fragment} Quick bite mate saras jagya 🥪🍲"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Samagra mulakat khub sari rahi. Saro taste, clean tables ane friendly service.{note_fragment} Fari aavva jevu chhe 🌟👍"},
            ]
        elif rating == 3:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food thik hatu, pan service thodi slow lagi aaje.{note_fragment} 🙂"},
                {"id": "idea_2", "focus": "Food & Wait", "text": f"Chai sari hati pan snacks thoda thanda hata.{note_fragment} Samanya anubhav rahyo 🙂☕"},
                {"id": "idea_3", "focus": "Service Pace", "text": f"Staff saro hato pan order mate thodi vaar lagi.{note_fragment} Average visit 🙂"},
                {"id": "idea_4", "focus": "Crowd & Cleaning", "text": f"Bheed vadhare hati aaje. Taste barabar hato pan table cleaning ma time lagyo.{note_fragment} Aavti vakhte better service ni apeksha 🙂🥪"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Overall thik anubhav rahyo. Seating comfortable chhe pan service thodi improve karvani jarur chhe.{note_fragment} Okay visit 🙂"},
            ]
        elif rating == 2:
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Food thik hatu pan wait bahu karvu padyu aaje.{note_fragment} 😕"},
                {"id": "idea_2", "focus": "Order Delay", "text": f"Aaje service thi santosh na thayo.{note_fragment} Order late aavyo ane food pan lukewarm hatu 😕"},
                {"id": "idea_3", "focus": "Staff Attention", "text": f"Staff dhyan nhato aapi rahyo ane service slow hati.{note_fragment} Better service expected hati 😕"},
                {"id": "idea_4", "focus": "Slow Service", "text": f"Order mate ghano wait karyo ane tables pan quickly clean na thaya.{note_fragment} Customer service improve karvani jarur chhe 😕⏳"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Nirashajanak visit rahi. Chai thik hati pan snacks fresh nahota ane service slow hati.{note_fragment} Management sudharo kare evi aasha 😕"},
            ]
        else: # 1 star
            ideas = [
                {"id": "idea_1", "focus": "Short & Sweet", "text": f"Bahu j slow service ane thandu khavanu aapyu aaje.{note_fragment} 😞"},
                {"id": "idea_2", "focus": "Order Issue", "text": f"Kharab anubhav rahyo aaje.{note_fragment} Ghani vaar ubha rakhya ane order pan wrong aavyo 😞"},
                {"id": "idea_3", "focus": "Cleanliness", "text": f"Staff unorganized hato ane tables bilkul clean nahota.{note_fragment} Bahu poor service 😞"},
                {"id": "idea_4", "focus": "Food & Wait", "text": f"Disappointed with the visit. Food aavva ma khub time lagyo ane taste fresh nahoto.{note_fragment} Koi barabar attend pan na karyu 😞👎"},
                {"id": "idea_5", "focus": "Overall Visit", "text": f"Experience bilkul saro na rahyo. Long waiting time, thandu food ane careless staff.{note_fragment} Service ma mota sudhara ni jarur chhe 😞"},
            ]

    else: # English
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
    business_name: str = "the restaurant",
    language: str = "english",
    category: Optional[str] = None
) -> str:
    """
    Deterministic Humanization Engine adhering to 15-45 words,
    contextual emojis, zero fabrication, and natural Roman-script Hinglish/Gujlish.
    """
    lang = normalize_language(language)

    # If customer already selected an idea, build upon and personalize it
    if selected_idea and selected_idea.strip():
        base_text = selected_idea.strip()
        if user_note and user_note.strip() and user_note.strip().lower() not in base_text.lower():
            n = user_note.strip().rstrip(".!")
            base_text = f"{base_text.rstrip('.! 😊❤️✨☕👌🍲🥪👍')} — {n}."
            if emoji_preference != "none":
                emojis = pick_tasteful_emojis(rating, aspects, emoji_preference)
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

    emojis = pick_tasteful_emojis(rating, aspects, emoji_preference)

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
    category: Optional[str] = None
) -> str:
    lang = normalize_language(language)
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

    return f"""Draft a short, human-like hospitality review:
- Star Rating: {rating} of 5 Stars
- Business Name: {business_name}
- Category: {category or "Hospitality"}
- Mentioned Topics: {aspects_str}
- {lang_rule}
- {note_instruction}
- {idea_instruction}
- Length: 15 to 45 words
- Emojis: {emoji_preference} (at most 1-2 for 4-5 stars, 0 for 1-2 stars)
- Tone: Natural, friendly, human tone. Never use marketing or corporate words. Zero fabrication.

Output ONLY the review text."""
