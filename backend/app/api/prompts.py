"""
Humanized Prompt Engineering & Real-World Review Synthesis Engine for ChurnLens / VRAJA AI.
Strictly adheres to:
1. Zero fabrication (never invent unmentioned dishes, staff names, or events).
2. Proper native script language enforcement (Gujarati in Gujarati Unicode script, Hindi in Devanagari script, English in natural English).
3. Human-like natural phrasing (15-45 words, everyday language, no corporate jargon).
4. 1-2 contextual emojis for every rating level (tasteful, rating-appropriate).
5. Review idea generation (3 distinct perspectives: Short & Natural, Detailed & Expressive, Simple & Personal).
"""

import random
from typing import List, Dict, Any, Optional

SYSTEM_HUMANIZED_PROMPT = """You are helping a customer write a short, genuine review to post on Google Maps.

CORE PRINCIPLES:
1. WRITE LIKE A NORMAL PERSON typing on their phone, not like a marketing professional.
2. SCRIPT & LANGUAGE RULES:
   - If Gujarati: Write the complete review in natural, grammatically correct Gujarati using Gujarati Unicode script (ગુજરાતી લિપિ). Every sentence must be written in Gujarati script. Never transliterate Gujarati into English/Roman letters. Never generate Roman Gujarati, Gujlish, Hinglish, or English sentences mixed with Gujarati words. Use natural Gujarati vocabulary and grammar, preserving the customer's original meaning and factual details.
   - If Hindi: Write the complete review in natural, grammatically correct Hindi using Devanagari script (देवनागरी लिपि). Every sentence must be written in Devanagari script. Never transliterate Hindi into English/Roman letters. Never generate Roman Hindi or Hinglish. Use natural Hindi vocabulary and grammar.
   - If English: Write in simple, natural everyday English.
   - NEVER generate in English and translate via translation tools. Formulate naturally in the requested native language and script.
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

EMOJI_MAP = {
    "coffee": "☕",
    "chai": "☕",
    "drinks": "☕",
    "beverage": "☕",
    "food": "😋",
    "breakfast": "🍳",
    "snacks": "🥪",
    "taste": "😋",
    "flavour": "😋",
    "bakery": "🥐",
    "dessert": "🍨",
    "atmosphere": "✨",
    "ambience": "✨",
    "vibe": "✨",
    "service": "😊",
    "staff": "😊",
    "cleanliness": "✨",
    "value": "💰",
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

    selected = emojis[:2] if preference == "light" else emojis[:1]
    return " " + "".join(selected) if selected else ""

def _clean_business_name(name: str, lang: str) -> str:
    n = (name or "").strip()
    if not n or n in ("default_business", "default", "nasta_ghar", "nasta-ghar"):
        if lang == "gujarati":
            return "નાસ્તા ઘર"
        elif lang == "hindi":
            return "नाश्ता घर"
        return "Nasta Ghar"
    if n in ("Nasta Ghar", "NastaGhar"):
        if lang == "gujarati":
            return "નાસ્તા ઘર"
        elif lang == "hindi":
            return "नाश्ता घर"
    return n

def generate_candidate_ideas(
    rating: int,
    aspects: List[str],
    user_note: str = "",
    business_name: str = "Nasta Ghar",
    language: str = "english",
    category: Optional[str] = None
) -> List[Dict[str, str]]:
    lang = normalize_language(language)
    b_name = _clean_business_name(business_name, lang)
    cleaned_aspects = [a.lower().strip() for a in aspects if a.strip()]

    has_breakfast = any("breakfast" in a or "nasto" in a or "nasta" in a for a in cleaned_aspects)
    has_coffee = any("coffee" in a or "chai" in a or "tea" in a or "drink" in a or "beverage" in a for a in cleaned_aspects)
    has_food = any("food" in a or "taste" in a or "breakfast" in a or "snack" in a or "bakery" in a for a in cleaned_aspects)
    has_service = any("service" in a or "staff" in a for a in cleaned_aspects)
    has_ambience = any("ambience" in a or "atmosphere" in a or "vibe" in a for a in cleaned_aspects)
    has_clean = any("clean" in a or "sitting" in a for a in cleaned_aspects)

    if has_breakfast and has_coffee:
        topic_en = "breakfast and chai"
        topic_hi = "नाश्ता और चाय"
        topic_gu = "નાસ્તો અને ચા"
    elif has_breakfast:
        topic_en = "breakfast"
        topic_hi = "नाश्ता"
        topic_gu = "નાસ્તો"
    elif has_coffee:
        topic_en = "coffee and tea"
        topic_hi = "चाय और कॉफ़ी"
        topic_gu = "ચા અને કૉફી"
    elif has_food:
        topic_en = "food"
        topic_hi = "स्वादिष्ट भोजन"
        topic_gu = "સ્વાદિષ્ટ વાનગીઓ"
    elif has_service:
        topic_en = "service"
        topic_hi = "सर्विस"
        topic_gu = "સર્વિસ"
    elif has_ambience:
        topic_en = "atmosphere"
        topic_hi = "माहौल"
        topic_gu = "વાતાવરણ"
    elif has_clean:
        topic_en = "seating area and cleanliness"
        topic_hi = "बैठक व्यवस्था और साफ़-सफ़ाई"
        topic_gu = "બેઠક વ્યવસ્થા અને સ્વચ્છતા"
    else:
        topic_en = ""
        topic_hi = ""
        topic_gu = ""

    note_fragment = ""
    if user_note and user_note.strip():
        n = user_note.strip().rstrip(".!")
        note_fragment = f" {n}."

    if lang == "gujarati":
        focus_1 = "ટૂંકું અને સ્વાભાવિક"
        focus_2 = "વિગતવાર અને અભિવ્યક્તિપૂર્ણ"
        focus_3 = "સરળ અને વ્યક્તિગત"

        if rating == 5:
            if topic_gu:
                short_text = f"{b_name}માં {topic_gu} ખૂબ જ સરસ હતાં!{note_fragment} ખૂબ મજા આવી ગઈ 🍳☕"
                detailed_text = f"{b_name}માં {topic_gu}નો અનુભવ ખરેખર લાજવાબ રહ્યો.{note_fragment} બધી વ્યવસ્થા એકદમ ઉત્તમ હતી 😊✨"
                personal_text = f"મને {b_name}માં {topic_gu} ખૂબ જ પસંદ આવ્યા.{note_fragment} મુલાકાતથી ઘણો આનંદ થયો ❤️"
            else:
                short_text = f"{b_name}માં ખૂબ જ સરસ અનુભવ રહ્યો!{note_fragment} ખૂબ મજા આવી ગઈ 😊✨"
                detailed_text = f"સમગ્ર મુલાકાત {b_name} ખાતે ઘણી શાનદાર રહી.{note_fragment} બધી વ્યવસ્થા એકદમ સુવ્યવસ્થિત હતી 👍"
                personal_text = f"મને {b_name}ની મુલાકાત ખૂબ જ ગમી.{note_fragment} ખરેખર સંતોષકારક અનુભવ રહ્યો ❤️"

        elif rating == 4:
            if topic_gu:
                short_text = f"{b_name}માં {topic_gu} સરસ હતાં.{note_fragment} સારો અનુભવ રહ્યો 👍"
                detailed_text = f"{b_name}માં {topic_gu}નો અનુભવ એકંદરે ઘણો સારો રહ્યો.{note_fragment} વ્યવસ્થા સારી લાગી 🙂"
                personal_text = f"મને {b_name}માં {topic_gu} ગમ્યા.{note_fragment} એકંદરે સારો સમય રહ્યો 👍"
            else:
                short_text = f"{b_name}માં સારો અનુભવ રહ્યો.{note_fragment} બધું બરાબર હતું 👍"
                detailed_text = f"{b_name}ની મુલાકાત એકંદરે ઘણી સારી રહી.{note_fragment} સંતોષકારક વ્યવસ્થા હતી 🙂"
                personal_text = f"મને {b_name}ની મુલાકાત સારી લાગી.{note_fragment} એકંદરે સારો સમય પસાર થયો 👍"

        elif rating == 3:
            if topic_gu:
                short_text = f"{b_name}માં {topic_gu} સામાન્ય રહ્યાં.{note_fragment} ઠીક મુલાકાત હતી 🙂"
                detailed_text = f"{b_name}માં {topic_gu} ઠીક હતાં, પણ થોડા સુધારાની જરૂર જણાય છે.{note_fragment} સરેરાશ અનુભવ 🙂"
                personal_text = f"મારા માટે {b_name}માં {topic_gu}નો અનુભવ સરેરાશ રહ્યો.{note_fragment} સામાન્ય વિઝિટ 🙂"
            else:
                short_text = f"આજનો અનુભવ {b_name} ખાતે ઠીક-ઠાક રહ્યો.{note_fragment} સામાન્ય મુલાકાત રહી 🙂"
                detailed_text = f"એકંદરે મુલાકાત {b_name} ખાતે સામાન્ય રહી.{note_fragment} થોડા સુધારાની જરૂર છે 🙂"
                personal_text = f"મારા માટે {b_name}નો અનુભવ સામાન્ય રહ્યો.{note_fragment} સાધારણ મુલાકાત 🙂"

        elif rating == 2:
            if topic_gu:
                short_text = f"{b_name}માં {topic_gu} અપેક્ષા કરતાં ઓછા રહ્યાં.{note_fragment} 😕"
                detailed_text = f"{b_name}માં {topic_gu}થી થોડી નિરાશા થઈ.{note_fragment} સુધારો કરવો જરૂરી છે 😕"
                personal_text = f"મને {b_name}માં {topic_gu} માટે આવી અપેક્ષા નહોતી.{note_fragment} 😕"
            else:
                short_text = f"આજે {b_name}માં અનુભવ સારો ન રહ્યો.{note_fragment} 😕"
                detailed_text = f"{b_name}ની મુલાકાતથી નિરાશા થઈ.{note_fragment} સર્વિસ અને સંભાળમાં સુધારાની જરૂર છે 😕"
                personal_text = f"મને {b_name}માં આવી અપેક્ષા નહોતી.{note_fragment} 😕"

        else: # 1 star
            if topic_gu:
                short_text = f"{b_name}માં {topic_gu}નો અનુભવ ઘણો ખરાબ રહ્યો.{note_fragment} 😞"
                detailed_text = f"{b_name}માં {topic_gu}થી બિલકુલ સંતોષ ન થયો.{note_fragment} મોટા સુધારાની જરૂર છે 😞"
                personal_text = f"{b_name}માં {topic_gu}થી ખૂબ જ નિરાશાજનક મુલાકાત રહી.{note_fragment} 😞"
            else:
                short_text = f"{b_name}માં આજનો અનુભવ ખૂબ ખરાબ રહ્યો.{note_fragment} 😞"
                detailed_text = f"આજે {b_name}ની મુલાકાતથી બિલકુલ સંતોષ ન થયો.{note_fragment} મોટા સુધારાની તાતી જરૂર છે 😞"
                personal_text = f"{b_name} ખાતે આજની મુલાકાત ઘણી નિરાશાજનક રહી.{note_fragment} 😞"

    elif lang == "hindi":
        focus_1 = "छोटा और स्वाभाविक"
        focus_2 = "विस्तृत और स्पष्ट"
        focus_3 = "सरल और व्यक्तिगत"

        if rating == 5:
            if topic_hi:
                short_text = f"{b_name} में {topic_hi} बहुत पसंद आया!{note_fragment} मज़ा आ गया 🍳☕"
                detailed_text = f"{b_name} में {topic_hi} का अनुभव वाकई लाजवाब रहा।{note_fragment} सब कुछ बहुत अच्छे से व्यवस्थित था 😊✨"
                personal_text = f"व्यक्तिगत रूप से {b_name} में {topic_hi} बहुत अच्छा लगा।{note_fragment} विज़िट से बहुत खुशी हुई ❤️"
            else:
                short_text = f"बहुत ही अच्छा अनुभव रहा {b_name} में!{note_fragment} मज़ा आ गया 😊✨"
                detailed_text = f"समग्र विज़िट {b_name} में काफी शानदार रही।{note_fragment} व्यवस्था बहुत अच्छी थी 👍"
                personal_text = f"मुझे {b_name} की विज़िट बहुत पसंद आई।{note_fragment} काफी सुखद अनुभव रहा ❤️"

        elif rating == 4:
            if topic_hi:
                short_text = f"{b_name} में {topic_hi} काफी अच्छा था।{note_fragment} अच्छा अनुभव रहा 👍"
                detailed_text = f"{b_name} में {topic_hi} का अनुभव काफी सुखद रहा।{note_fragment} सब कुछ बढ़िया था 🙂"
                personal_text = f"मुझे {b_name} में {topic_hi} पसंद आया।{note_fragment} एक अच्छी विज़िट रही 👍"
            else:
                short_text = f"काफी अच्छा अनुभव रहा {b_name} में।{note_fragment} अच्छा लगा 👍"
                detailed_text = f"कुल मिलाकर {b_name} की विज़िट अच्छी रही।{note_fragment} व्यवस्था ठीक रही 🙂"
                personal_text = f"मुझे {b_name} की विज़िट पसंद आई।{note_fragment} बढ़िया समय बीता 👍"

        elif rating == 3:
            if topic_hi:
                short_text = f"{b_name} में {topic_hi} ठीक-ठाक रहा।{note_fragment} सामान्य अनुभव 🙂"
                detailed_text = f"{b_name} में {topic_hi} औसत रहा।{note_fragment} थोड़े और सुधार की गुंजाइश है 🙂"
                personal_text = f"मेरे लिए {b_name} में {topic_hi} साधारण रहा।{note_fragment} सामान्य विज़िट 🙂"
            else:
                short_text = f"आज {b_name} का अनुभव सामान्य रहा।{note_fragment} ठीक-ठाक विज़िट 🙂"
                detailed_text = f"कुल मिलाकर {b_name} का अनुभव औसत रहा।{note_fragment} कुछ सुधार हो सकता है 🙂"
                personal_text = f"मेरे लिए {b_name} की विज़िट साधारण रही।{note_fragment} ठीक अनुभव रहा 🙂"

        elif rating == 2:
            if topic_hi:
                short_text = f"{b_name} में {topic_hi} उम्मीद के मुताबिक नहीं था।{note_fragment} 😕"
                detailed_text = f"{b_name} में {topic_hi} से थोड़ी निराशा हुई।{note_fragment} सुधार की ज़रूरत है 😕"
                personal_text = f"मुझे {b_name} में {topic_hi} से ऐसी उम्मीद नहीं थी।{note_fragment} 😕"
            else:
                short_text = f"आज {b_name} का अनुभव उम्मीद से कम रहा।{note_fragment} 😕"
                detailed_text = f"{b_name} की विज़िट से थोड़ी निराशा हुई।{note_fragment} सर्विस में सुधार की ज़रूरत है 😕"
                personal_text = f"मुझे ऐसी उम्मीद नहीं थी {b_name} में।{note_fragment} 😕"

        else: # 1 star
            if topic_hi:
                short_text = f"{b_name} में {topic_hi} का अनुभव खराब रहा।{note_fragment} 😞"
                detailed_text = f"{b_name} में {topic_hi} से बिल्कुल संतुष्ट नहीं हुए।{note_fragment} बड़े सुधार की ज़रूरत है 😞"
                personal_text = f"{b_name} में {topic_hi} से काफी निराशाजनक अनुभव रहा।{note_fragment} 😞"
            else:
                short_text = f"आज {b_name} में खराब अनुभव रहा।{note_fragment} 😞"
                detailed_text = f"आज {b_name} की विज़िट से बिल्कुल संतुष्ट नहीं हुए।{note_fragment} बड़े सुधार की ज़रूरत है 😞"
                personal_text = f"{b_name} में आज का अनुभव काफी निराशाजनक रहा।{note_fragment} 😞"

    else: # English
        focus_1 = "Short & Natural"
        focus_2 = "Detailed & Expressive"
        focus_3 = "Simple & Personal"

        if rating == 5:
            if topic_en:
                short_text = f"Really enjoyed the {topic_en} at {b_name}!{note_fragment} Loved it 🍳☕"
                detailed_text = f"Had a lovely visit at {b_name}. The {topic_en} was wonderful and prepared nicely.{note_fragment} Truly enjoyed it 😊✨"
                personal_text = f"The {topic_en} at {b_name} was delicious today.{note_fragment} Very happy with my visit ❤️"
            else:
                short_text = f"Had a wonderful visit at {b_name}! Really enjoyed every moment.{note_fragment} Loved it 😊✨"
                detailed_text = f"Had a lovely and wonderful visit at {b_name}. Everything was handled nicely.{note_fragment} Truly enjoyed it 👍"
                personal_text = f"I genuinely enjoyed my time at {b_name}.{note_fragment} Very happy with my visit ❤️"

        elif rating == 4:
            if topic_en:
                short_text = f"Good {topic_en} at {b_name}.{note_fragment} Nice visit 👍"
                detailed_text = f"Solid and enjoyable experience with the {topic_en} at {b_name}.{note_fragment} Well managed throughout 😊"
                personal_text = f"Had a good experience with the {topic_en} at {b_name}.{note_fragment} Happy with my visit overall 👍"
            else:
                short_text = f"Very pleasant visit at {b_name}.{note_fragment} Good spot to stop by 👍"
                detailed_text = f"Overall a solid and enjoyable experience at {b_name}.{note_fragment} Everything was well arranged 😊"
                personal_text = f"Had a good visit at {b_name}.{note_fragment} Happy with my experience overall 👍"

        elif rating == 3:
            if topic_en:
                short_text = f"Decent visit for {topic_en} at {b_name}.{note_fragment} Standard experience 🙂"
                detailed_text = f"The {topic_en} at {b_name} was fine overall.{note_fragment} An average visit with room for minor improvement 🙂"
                personal_text = f"It was a pretty average experience for {topic_en} at {b_name}.{note_fragment} Decent visit overall 🙂"
            else:
                short_text = f"Decent visit today at {b_name}.{note_fragment} Standard experience 🙂"
                detailed_text = f"Overall a fair and average experience at {b_name}. A few good points, but there is room for improvement.{note_fragment} Decent visit 🙂"
                personal_text = f"It was a pretty average visit for me at {b_name}.{note_fragment} Fair experience overall 🙂"

        elif rating == 2:
            if topic_en:
                short_text = f"The {topic_en} at {b_name} fell below expectations today.{note_fragment} 😕"
                detailed_text = f"Disappointed with the {topic_en} at {b_name}.{note_fragment} The experience needs attention and improvement 😕"
                personal_text = f"Expected a better experience with the {topic_en} at {b_name}.{note_fragment} Hope to see improvements 😕"
            else:
                short_text = f"Visit fell below expectations today at {b_name}.{note_fragment} 😕"
                detailed_text = f"Somewhat disappointed with the visit at {b_name}.{note_fragment} Several areas need attention and better care 😕"
                personal_text = f"Expected a better experience than what I had at {b_name} today.{note_fragment} Hope to see improvements 😕"

        else: # 1 star
            if topic_en:
                short_text = f"Very disappointing experience with the {topic_en} at {b_name}.{note_fragment} 😞"
                detailed_text = f"Unsatisfied with the {topic_en} during today's visit to {b_name}.{note_fragment} Major improvements are needed 😞"
                personal_text = f"Really unhappy with the {topic_en} at {b_name} today.{note_fragment} Disappointed with how things went 😞"
            else:
                short_text = f"Very disappointing experience today at {b_name}.{note_fragment} 😞"
                detailed_text = f"Extremely unsatisfied with today's visit at {b_name}.{note_fragment} Major improvements are needed in service and quality 😞"
                personal_text = f"Really unhappy with the experience today.{note_fragment} Disappointed with how things were handled at {b_name} 😞"

    return [
        {"id": "idea_1", "focus": focus_1, "text": short_text},
        {"id": "idea_2", "focus": focus_2, "text": detailed_text},
        {"id": "idea_3", "focus": focus_3, "text": personal_text},
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
    category: Optional[str] = None
) -> str:
    lang = normalize_language(language)
    b_name = _clean_business_name(business_name, lang)

    if selected_idea and selected_idea.strip():
        base_text = selected_idea.strip()
        if user_note and user_note.strip() and user_note.strip().lower() not in base_text.lower():
            n = user_note.strip().rstrip(".!")
            sep = " — " if lang == "english" else " "
            base_text = f"{base_text.rstrip('.! ')}{sep}{n}."
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

    if lang == "gujarati":
        if rating == 5:
            if has_coffee and has_service:
                draft = f"{b_name}માં નાસ્તો અને ચા ખરેખર એકદમ સ્વાદિષ્ટ હતાં! સ્ટાફનો વ્યવહાર પણ ખૂબ જ સારો અને વિનમ્ર રહ્યો.{note_text} ફરીથી જરૂર આવીશું{emojis}"
            elif has_food and has_vibe:
                draft = f"{b_name}માં આવીને ખૂબ મજા આવી. ખાવાનું એકદમ તાજું હતું અને વાતાવરણ પણ ઘણું સુખદ હતું.{note_text} જરૂર મુલાકાત લેવા જેવું સ્થળ છે{emojis}"
            else:
                draft = f"{b_name}માં સમગ્ર અનુભવ ખૂબ જ સરસ રહ્યો! નાસ્તો તાજો હતો અને સર્વિસ પણ ઝડપી મળી.{note_text} બધાને અહીં આવવાની ભલામણ કરું છું{emojis}"
        elif rating == 4:
            draft = f"{b_name}માં ખૂબ સારો અનુભવ રહ્યો. વાનગીઓનો સ્વાદ સરસ હતો અને સ્ટાફનો વ્યવહાર પણ વિનમ્ર રહ્યો.{note_text} નાસ્તા માટે ઉત્તમ સ્થળ છે{emojis}"
        elif rating == 3:
            draft = f"{b_name}માં સ્વાદ ઠીક હતો, પણ સર્વિસ આજે થોડી ધીમી લાગી.{note_text} એકંદરે સરેરાશ મુલાકાત રહી.{emojis}"
        elif rating == 2:
            draft = f"{b_name}માં ખાવાનું સામાન્ય હતું પણ રાહ વધારે જોવી પડી.{note_text} આગલી વખતે સર્વિસ થોડી ઝડપી મળે તેવી આશા.{emojis}"
        else: # 1 star
            draft = f"{b_name}માં આજનો અનુભવ બિલકુલ સારો ન રહ્યો. સર્વિસ ખૂબ ધીમી હતી અને નાસ્તો ઠંડો આવ્યો હતો.{note_text} ગુણવત્તામાં સુધારો કરવાની જરૂર છે.{emojis}"

    elif lang == "hindi":
        if rating == 5:
            if has_coffee and has_service:
                draft = f"{b_name} में चाय और नाश्ता सच में लाजवाब थे! स्टाफ का व्यवहार भी बहुत मिलनसार था।{note_text} यहाँ दोबारा ज़रूर आएंगे{emojis}"
            elif has_food and has_vibe:
                draft = f"{b_name} में आकर बहुत अच्छा लगा। खाना ताज़ा और स्वादिष्ट था और माहौल भी काफी सुकून भरा था।{note_text} ज़रूर विज़िट करें{emojis}"
            else:
                draft = f"{b_name} में समग्र विज़िट बहुत ही शानदार रही! खाना ताज़ा था और सर्विस भी तेज़ और अच्छी थी।{note_text} हम सभी को यहाँ आने की सलाह देते हैं{emojis}"
        elif rating == 4:
            draft = f"{b_name} में काफी अच्छा अनुभव रहा। स्वाद बढ़िया था और स्टाफ भी मददगार था।{note_text} नाश्ते के लिए अच्छी जगह है{emojis}"
        elif rating == 3:
            draft = f"{b_name} में स्वाद ठीक था, लेकिन सर्विस थोड़ी धीमी लगी।{note_text} कुल मिलाकर सामान्य विज़िट रही।{emojis}"
        elif rating == 2:
            draft = f"{b_name} में खाना ठीक था पर इंतज़ार काफी करना पड़ा।{note_text} उम्मीद है अगली बार सर्विस थोड़ी तेज़ होगी।{emojis}"
        else: # 1 star
            draft = f"{b_name} में आज का अनुभव बिल्कुल अच्छा नहीं रहा। सर्विस बहुत धीमी थी और खाना भी ठंडा था।{note_text} सुधार की सख्त ज़रूरत है।{emojis}"

    else: # English
        if rating == 5:
            if has_coffee and has_service:
                draft = f"Really enjoyed the coffee at {b_name} and the staff were so friendly! Great place to relax and recharge.{note_text} Definitely coming back{emojis}"
            elif has_food and has_vibe:
                draft = f"Had a lovely meal at {b_name}. The food was delicious and the place had such a warm, comfortable vibe.{note_text} Highly recommend{emojis}"
            elif has_food and has_service:
                draft = f"Great food at {b_name} and really friendly service. Everything was served fresh with a smile.{note_text} Will definitely be back{emojis}"
            elif has_coffee:
                draft = f"Loved the coffee at {b_name}! Excellent brew and super welcoming staff.{note_text} Such a nice little spot{emojis}"
            else:
                draft = f"Had a wonderful time at {b_name}! The staff were great and the whole visit was really pleasant.{note_text} Would happily recommend{emojis}"
        elif rating == 4:
            if has_food:
                draft = f"Had a really good time at {b_name}. The food was tasty and the service was friendly.{note_text} Nice place to relax and eat{emojis}"
            elif has_coffee:
                draft = f"Solid spot at {b_name} with great coffee and good seating.{note_text} Staff were welcoming and the drinks came out quickly{emojis}"
            else:
                draft = f"Very enjoyable visit at {b_name}! Good service, nice atmosphere, and fair prices.{note_text} Happy to come back again{emojis}"
        elif rating == 3:
            if has_service:
                draft = f"Overall a decent experience at {b_name}. The food was good, but the service was a little slow today.{note_text} Pretty average visit.{emojis}"
            else:
                draft = f"Nice place and comfortable seating at {b_name}, though the visit was somewhat average.{note_text} Okay overall.{emojis}"
        elif rating == 2:
            draft = f"The food was okay at {b_name}, but the wait was quite long today.{note_text} Hopefully the service gets a little quicker next time.{emojis}"
        else: # 1 star
            draft = f"Unfortunately, my experience wasn't great at {b_name} today. The service took quite a while and the food wasn't what I expected.{note_text} I hope things improve.{emojis}"

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
    b_name = _clean_business_name(business_name, lang)
    aspects_str = ", ".join(aspects) if aspects else "General visit"
    clean_note = user_note.strip() if user_note else ""
    note_instruction = (
        f'Customer note: "{clean_note}"'
        if clean_note
        else "No customer note provided. Rely strictly on the selected topics."
    )
    clean_idea = selected_idea.strip() if selected_idea else ""
    idea_instruction = (
        f'The customer picked this starting idea: "{clean_idea}". Personalize it naturally without changing its facts.'
        if clean_idea
        else "Create a fresh natural review idea."
    )

    if lang == "gujarati":
        lang_rule = (
            "Language & Writing System: Write the complete review in natural, grammatically correct Gujarati using Gujarati Unicode script (ગુજરાતી લિપિ). "
            "Every sentence must be written in Gujarati script. Never transliterate Gujarati into English letters. "
            "Never generate Roman Gujarati, Gujlish, Hinglish, or English sentences mixed with Gujarati words. "
            "Use natural Gujarati vocabulary and preserve the customer's original meaning and factual details."
        )
    elif lang == "hindi":
        lang_rule = (
            "Language & Writing System: Write the complete review in natural, grammatically correct Hindi using Devanagari script (देवनागरी लिपि). "
            "Every sentence must be written in Devanagari script. Never transliterate Hindi into English letters. "
            "Never generate Roman Hindi or Hinglish. Use natural Hindi vocabulary and preserve the customer's original meaning."
        )
    else:
        lang_rule = "Language & Writing System: Write the complete review in natural everyday English."

    return f"""Draft a short, human-like hospitality review:
- Star Rating: {rating} of 5 Stars
- Business Name: {b_name}
- Category: {category or 'Hospitality'}
- Mentioned Topics: {aspects_str}
- {lang_rule}
- {note_instruction}
- {idea_instruction}
- Length: 15 to 45 words
- Emojis: {emoji_preference} (at most 1-2 for 4-5 stars, 0 for 1-2 stars)
- Tone: Natural, friendly, human tone. Never use marketing or corporate words. Zero fabrication.

Output ONLY the review text."""
