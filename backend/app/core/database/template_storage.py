"""
Dynamic Industry Template Storage Engine for Product A (Vraja Review Studio).
Additive, non-destructive database tables, migrations, version management, and CRUD helpers.
"""
import json
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional

# ─── DEFAULT INDUSTRY SEED DATA ───────────────────────────────────────────────
DEFAULT_INDUSTRIES = [
    {
        "id": "ind_restaurant",
        "name": "Restaurant & Dining",
        "slug": "restaurant",
        "description": "Cafes, traditional eateries, fine dining, bistros, and quick-service food brands.",
        "icon": "🍽️",
        "status": "active"
    },
    {
        "id": "ind_hotel",
        "name": "Hotel & Hospitality",
        "slug": "hotel",
        "description": "Boutique hotels, luxury resorts, serviced apartments, and homestays.",
        "icon": "🏨",
        "status": "active"
    },
    {
        "id": "ind_salon",
        "name": "Salon, Spa & Wellness",
        "slug": "salon",
        "description": "Hair salons, nail bars, day spas, skincare clinics, and grooming studios.",
        "icon": "✂️",
        "status": "active"
    },
    {
        "id": "ind_clinic",
        "name": "Healthcare & Clinic",
        "slug": "clinic",
        "description": "Dental practices, outpatient clinics, diagnostics, and specialist doctors.",
        "icon": "🩺",
        "status": "active"
    }
]

RESTAURANT_DEFAULT_TOPICS = [
    {"label": "Food Quality", "icon": "🍽️"},
    {"label": "Taste", "icon": "😋"},
    {"label": "Freshness", "icon": "🥗"},
    {"label": "Presentation", "icon": "✨"},
    {"label": "Service", "icon": "⚡"},
    {"label": "Staff Behaviour", "icon": "😊"},
    {"label": "Ambience", "icon": "🕯️"},
    {"label": "Cleanliness", "icon": "🧼"},
    {"label": "Value for Money", "icon": "💰"},
]

DEFAULT_TEMPLATES = [
    # ─── RESTAURANT ───
    {
        "id": "tpl_restaurant_classic",
        "industry_id": "ind_restaurant",
        "name": "Restaurant Classic (Obsidian & Lime)",
        "slug": "restaurant_classic",
        "description": "Signature Nasta Ghar aesthetic with animated Gujarati food world banner and vibrant accents.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "restaurant_classic",
                "primaryAccent": "#f97316",
                "secondaryAccent": "#c9ff00",
                "backgroundColor": "#0d130e",
                "cardBackground": "#162017",
                "textColor": "#f8fafc",
                "subtextColor": "#94a3b8",
                "heroBannerType": "animated_world",
                "badgeText": "Authentic Taste"
            },
            "topics": [
                {"label": "Breakfast", "icon": "🥣"},
                {"label": "Hot Chai", "icon": "☕"},
                {"label": "Farsan / Snacks", "icon": "🥟"},
                {"label": "Cleanliness", "icon": "✨"},
                {"label": "Quick Service", "icon": "⚡"}
            ],
            "ratingLabels": {
                "5": {"text": "Loved it!", "emoji": "🤩"},
                "4": {"text": "Really good", "emoji": "😊"},
                "3": {"text": "It was okay", "emoji": "🙂"},
                "2": {"text": "Disappointed", "emoji": "😕"},
                "1": {"text": "Not good", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "What stood out?",
                "pickMatched": "Pick anything that matched your visit",
                "notePlaceholder": "e.g. The poha and special chai were absolutely perfect! 😋"
            }
        }
    },
    {
        "id": "tpl_restaurant_premium",
        "industry_id": "ind_restaurant",
        "name": "Fine Dining & Bistro (Charcoal & Gold)",
        "slug": "restaurant_premium",
        "description": "Understated luxury aesthetic tailored for fine dining, bistros, and lounge experiences.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "restaurant_premium",
                "primaryAccent": "#d4af37",
                "secondaryAccent": "#f59e0b",
                "backgroundColor": "#121214",
                "cardBackground": "#1a1a1e",
                "textColor": "#ffffff",
                "subtextColor": "#a1a1aa",
                "heroBannerType": "luxury_card",
                "badgeText": "Gourmet Hospitality"
            },
            "topics": [
                {"label": "Food Quality", "icon": "🍷"},
                {"label": "Ambiance", "icon": "🕯️"},
                {"label": "Staff Hospitality", "icon": "🎩"},
                {"label": "Presentation", "icon": "✨"},
                {"label": "Craft Beverages", "icon": "🍸"}
            ],
            "ratingLabels": {
                "5": {"text": "Exquisite!", "emoji": "🌟"},
                "4": {"text": "Very Pleased", "emoji": "😊"},
                "3": {"text": "Satisfactory", "emoji": "🙂"},
                "2": {"text": "Underwhelming", "emoji": "😕"},
                "1": {"text": "Subpar", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your dining memorable?",
                "pickMatched": "Select the highlights of your experience",
                "notePlaceholder": "e.g. The chef's tasting menu and attentive table service were superb."
            }
        }
    },
    # ─── HOTEL ───
    {
        "id": "tpl_hotel_classic",
        "industry_id": "ind_hotel",
        "name": "Hotel & Hospitality Suite (Royal Navy & Cyan)",
        "slug": "hotel_classic",
        "description": "Crisp, welcoming hospitality design for boutique hotels, business stays, and serviced suites.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "hotel_classic",
                "primaryAccent": "#38bdf8",
                "secondaryAccent": "#818cf8",
                "backgroundColor": "#0b132b",
                "cardBackground": "#132144",
                "textColor": "#f8fafc",
                "subtextColor": "#94a3b8",
                "heroBannerType": "hotel_card",
                "badgeText": "Guest Hospitality"
            },
            "topics": [
                {"label": "Room Cleanliness", "icon": "🛏️"},
                {"label": "Staff Courtesy", "icon": "🛎️"},
                {"label": "Check-in Speed", "icon": "⚡"},
                {"label": "Comfortable Bed", "icon": "🌙"},
                {"label": "Breakfast Buffet", "icon": "🍳"},
                {"label": "Prime Location", "icon": "📍"}
            ],
            "ratingLabels": {
                "5": {"text": "Exceptional Stay!", "emoji": "⭐"},
                "4": {"text": "Comfortable Stay", "emoji": "😊"},
                "3": {"text": "Average", "emoji": "🙂"},
                "2": {"text": "Disappointed", "emoji": "😕"},
                "1": {"text": "Unpleasant", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your stay with us?",
                "pickMatched": "Select aspects that defined your visit",
                "notePlaceholder": "e.g. Check-in was swift, and the room was sparkling clean and peaceful."
            }
        }
    },
    {
        "id": "tpl_hotel_premium",
        "industry_id": "ind_hotel",
        "name": "Luxury Resort & Spa (Midnight & Champagne)",
        "slug": "hotel_premium",
        "description": "Elite resort aesthetic with champagne accents, tailored for 5-star properties and retreats.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "hotel_premium",
                "primaryAccent": "#e2b170",
                "secondaryAccent": "#fbbf24",
                "backgroundColor": "#090d16",
                "cardBackground": "#121929",
                "textColor": "#f8fafc",
                "subtextColor": "#94a3b8",
                "heroBannerType": "luxury_card",
                "badgeText": "Luxury Retreat"
            },
            "topics": [
                {"label": "Luxury Amenities", "icon": "🥂"},
                {"label": "Concierge Care", "icon": "🛎️"},
                {"label": "Suite & View", "icon": "🌅"},
                {"label": "Spa & Pool", "icon": "🌿"},
                {"label": "Gourmet Dining", "icon": "🍽️"}
            ],
            "ratingLabels": {
                "5": {"text": "Unforgettable!", "emoji": "✨"},
                "4": {"text": "Very Relaxing", "emoji": "😊"},
                "3": {"text": "Acceptable", "emoji": "🙂"},
                "2": {"text": "Needs Improvement", "emoji": "😕"},
                "1": {"text": "Unacceptable", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your stay remarkable?",
                "pickMatched": "Select your resort highlights",
                "notePlaceholder": "e.g. The breathtaking suite view and personalized concierge made our holiday special."
            }
        }
    },
    # ─── SALON ───
    {
        "id": "tpl_salon_classic",
        "industry_id": "ind_salon",
        "name": "Studio Salon & Grooming (Plum & Rose Gold)",
        "slug": "salon_classic",
        "description": "Modern studio aesthetic designed for hair stylists, beauty salons, and grooming lounges.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "salon_classic",
                "primaryAccent": "#f472b6",
                "secondaryAccent": "#fb7185",
                "backgroundColor": "#170c1d",
                "cardBackground": "#24132e",
                "textColor": "#fdf2f8",
                "subtextColor": "#d8b4fe",
                "heroBannerType": "salon_card",
                "badgeText": "Hair & Beauty"
            },
            "topics": [
                {"label": "Hair Styling", "icon": "✂️"},
                {"label": "Friendly Team", "icon": "💖"},
                {"label": "Clean & Sanitized", "icon": "🧼"},
                {"label": "Punctual Appointment", "icon": "⏰"},
                {"label": "Relaxing Vibe", "icon": "🌸"}
            ],
            "ratingLabels": {
                "5": {"text": "Loved my look!", "emoji": "💅"},
                "4": {"text": "Looks great", "emoji": "😊"},
                "3": {"text": "Fair service", "emoji": "🙂"},
                "2": {"text": "Not satisfied", "emoji": "😕"},
                "1": {"text": "Poor experience", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How do you love your new look?",
                "pickMatched": "Pick your salon highlights",
                "notePlaceholder": "e.g. The haircut and beard styling were immaculate, super friendly team!"
            }
        }
    },
    {
        "id": "tpl_salon_premium",
        "industry_id": "ind_salon",
        "name": "Luxury Spa Sanctuary (Warm Espresso & Champagne)",
        "slug": "salon_premium",
        "description": "Warm, peaceful sanctuary design for high-end aesthetic clinics and wellness spas.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "salon_premium",
                "primaryAccent": "#e5c378",
                "secondaryAccent": "#d97706",
                "backgroundColor": "#181414",
                "cardBackground": "#251f1f",
                "textColor": "#faf7f2",
                "subtextColor": "#d6cec2",
                "heroBannerType": "luxury_card",
                "badgeText": "Wellness Sanctuary"
            },
            "topics": [
                {"label": "Master Stylist", "icon": "✨"},
                {"label": "Therapeutic Ambiance", "icon": "🕯️"},
                {"label": "Premium Products", "icon": "🧴"},
                {"label": "Custom Consultation", "icon": "📋"},
                {"label": "Serene Massage", "icon": "🌿"}
            ],
            "ratingLabels": {
                "5": {"text": "Pure Rejuvenation!", "emoji": "🧖"},
                "4": {"text": "Very Peaceful", "emoji": "😊"},
                "3": {"text": "Decent", "emoji": "🙂"},
                "2": {"text": "Rushed", "emoji": "😕"},
                "1": {"text": "Unpleasant", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your wellness treatment?",
                "pickMatched": "Select your treatment highlights",
                "notePlaceholder": "e.g. The therapist took great care, atmosphere was deeply calming."
            }
        }
    },
    # ─── CLINIC ───
    {
        "id": "tpl_clinic_classic",
        "industry_id": "ind_clinic",
        "name": "Clinical Healthcare (Slate & Clean Cyan)",
        "slug": "clinic_classic",
        "description": "Professional, trust-inspiring medical design for dental practices, diagnostics, and family clinics.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "clinic_classic",
                "primaryAccent": "#0ea5e9",
                "secondaryAccent": "#10b981",
                "backgroundColor": "#091422",
                "cardBackground": "#102035",
                "textColor": "#f8fafc",
                "subtextColor": "#94a3b8",
                "heroBannerType": "clinic_card",
                "badgeText": "Healthcare & Care"
            },
            "topics": [
                {"label": "Doctor Empathy", "icon": "🩺"},
                {"label": "Clear Explanation", "icon": "💬"},
                {"label": "Hygienic Facility", "icon": "🛡️"},
                {"label": "Minimal Waiting", "icon": "⏱️"},
                {"label": "Supportive Staff", "icon": "🤝"}
            ],
            "ratingLabels": {
                "5": {"text": "Excellent Care!", "emoji": "🩺"},
                "4": {"text": "Good Experience", "emoji": "😊"},
                "3": {"text": "Satisfactory", "emoji": "🙂"},
                "2": {"text": "Long Wait / Disappointed", "emoji": "😕"},
                "1": {"text": "Poor Care", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your consultation experience?",
                "pickMatched": "Select what mattered most in your visit",
                "notePlaceholder": "e.g. The doctor listened attentively and explained the treatment clearly."
            }
        }
    },
    {
        "id": "tpl_clinic_premium",
        "industry_id": "ind_clinic",
        "name": "Specialist Medical Care (Dark Navy & Emerald)",
        "slug": "clinic_premium",
        "description": "High-trust design for advanced surgical centers, specialized dental and skin clinics.",
        "version": "1.0.0",
        "config": {
            "theme": {
                "variant": "clinic_premium",
                "primaryAccent": "#10b981",
                "secondaryAccent": "#3b82f6",
                "backgroundColor": "#09121a",
                "cardBackground": "#12202c",
                "textColor": "#f1f5f9",
                "subtextColor": "#94a3b8",
                "heroBannerType": "luxury_card",
                "badgeText": "Specialist Medicine"
            },
            "topics": [
                {"label": "Specialist Expertise", "icon": "🔬"},
                {"label": "Modern Equipment", "icon": "⚙️"},
                {"label": "Thorough Consultation", "icon": "📋"},
                {"label": "Caring Nursing Staff", "icon": "🤍"},
                {"label": "Smooth Follow-up", "icon": "📲"}
            ],
            "ratingLabels": {
                "5": {"text": "Exceptional Care!", "emoji": "🌟"},
                "4": {"text": "Very Professional", "emoji": "😊"},
                "3": {"text": "Moderate", "emoji": "🙂"},
                "2": {"text": "Disappointed", "emoji": "😕"},
                "1": {"text": "Substandard", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your consultation and treatment?",
                "pickMatched": "Select key highlights of your care",
                "notePlaceholder": "e.g. Modern equipment, reassuring explanation, and zero discomfort."
            }
        }
    }
]




# ─── FOUR APPROVED RESTAURANT TEMPLATE PRESETS ───────────────────────────────
FOUR_APPROVED_RESTAURANT_PRESETS = [
    {
        "id": "restaurant_classic_bistro",
        "industry_id": "ind_restaurant",
        "name": "Classic Bistro",
        "slug": "restaurant_classic_bistro",
        "description": "Elegant, warm, traditional dining with vintage parchment surfaces, deep emerald accents, and refined typography.",
        "version": "1.0.0",
        "config": {
            "schema_version": "1.0",
            "theme": {
                "background_color": "#FAF7F2",
                "card_surface_color": "#FFFFFF",
                "primary_accent": "#1B4332",
                "secondary_accent": "#C5A059",
                "text_color": "#1A241E",
                "border_color": "#E5DEC9",
                "heading_font_key": "playfair_display",
                "body_font_key": "lato",
                "gujarati_font_key": "noto_serif_gujarati",
                "hindi_font_key": "noto_serif_devanagari"
            },
            "layout": {
                "header_variant": "centered_crest",
                "rating_variant": "classic_stars",
                "topic_selector_variant": "outlined_chips",
                "review_suggestion_card_variant": "framed_parchment",
                "review_editor_variant": "editorial_salon",
                "button_variant": "emerald_pill",
                "spacing_preset": "editorial",
                "border_radius_preset": "md",
                "layout_density": "spacious"
            },
            "components": [
                "business_header", "rating_selector", "topic_selector",
                "personal_note", "ai_suggestions", "review_editor",
                "google_handoff", "private_feedback"
            ],
            "topics": RESTAURANT_DEFAULT_TOPICS,
            "rating_labels": {
                "5": {"text": "Loved it!", "emoji": "🤩"},
                "4": {"text": "Really good", "emoji": "😊"},
                "3": {"text": "It was okay", "emoji": "🙂"},
                "2": {"text": "Disappointed", "emoji": "😕"},
                "1": {"text": "Not good", "emoji": "😞"}
            },
            "experience_labels": {
                "whatStoodOut": "What stood out?",
                "pickMatched": "Pick anything that matched your visit",
                "notePlaceholder": "e.g. The hand-crafted dishes and authentic chai were exquisite."
            },
            "localized_content": {
                "en": {
                    "welcome_title": "How was your experience?",
                    "welcome_sub": "Share your dining highlights with us"
                },
                "gu": {
                    "welcome_title": "તમારો અનુભવ કેવો રહ્યો?",
                    "welcome_sub": "તમારા ભોજનના અનુભવો શેર કરો"
                },
                "hi": {
                    "welcome_title": "आपका अनुभव कैसा रहा?",
                    "welcome_sub": "अपने भोजन के अनुभव हमारे साथ साझा करें"
                }
            }
        }
    },
    {
        "id": "restaurant_modern_urban",
        "industry_id": "ind_restaurant",
        "name": "Modern Urban",
        "slug": "restaurant_modern_urban",
        "description": "High-energy, compact urban dining with dark slate surfaces, electric signal green accents, and high-efficiency controls.",
        "version": "1.0.0",
        "config": {
            "schema_version": "1.0",
            "theme": {
                "background_color": "#0E1117",
                "card_surface_color": "#181E29",
                "primary_accent": "#10B981",
                "secondary_accent": "#06B6D4",
                "text_color": "#FFFFFF",
                "border_color": "#263042",
                "heading_font_key": "space_grotesk",
                "body_font_key": "inter",
                "gujarati_font_key": "noto_sans_gujarati",
                "hindi_font_key": "noto_sans_devanagari"
            },
            "layout": {
                "header_variant": "left_aligned_tech",
                "rating_variant": "segmented_numeric",
                "topic_selector_variant": "compact_pills",
                "review_suggestion_card_variant": "dense_tech",
                "review_editor_variant": "tech_console",
                "button_variant": "volt_block",
                "spacing_preset": "compact",
                "border_radius_preset": "sm",
                "layout_density": "compact"
            },
            "components": [
                "business_header", "rating_selector", "topic_selector",
                "personal_note", "ai_suggestions", "review_editor",
                "google_handoff", "private_feedback"
            ],
            "topics": RESTAURANT_DEFAULT_TOPICS,
            "rating_labels": {
                "5": {"text": "Exceptional!", "emoji": "⚡"},
                "4": {"text": "Solid & Fast", "emoji": "👍"},
                "3": {"text": "Decent", "emoji": "🙂"},
                "2": {"text": "Slow / Off", "emoji": "😕"},
                "1": {"text": "Subpar", "emoji": "😞"}
            },
            "experience_labels": {
                "whatStoodOut": "Highlights // Select all that hit",
                "pickMatched": "Select tags matching your order",
                "notePlaceholder": "e.g. Crisp textures, fire burgers, and rapid table speed."
            },
            "localized_content": {
                "en": {
                    "welcome_title": "How was your meal?",
                    "welcome_sub": "Quick feedback & Google Review"
                },
                "gu": {
                    "welcome_title": "તમારું ભોજન કેવું રહ્યું?",
                    "welcome_sub": "ઝડપી પ્રતિસાદ અને ગૂગલ સમીક્ષા"
                },
                "hi": {
                    "welcome_title": "आपका भोजन कैसा रहा?",
                    "welcome_sub": "त्वरित फीडबैक और गूगल समीक्षा"
                }
            }
        }
    },
    {
        "id": "restaurant_luxury_dining",
        "industry_id": "ind_restaurant",
        "name": "Luxury Dining",
        "slug": "restaurant_luxury_dining",
        "description": "Understated fine dining aesthetic featuring midnight velvet depths, radiant vintage champagne, and spacious editorial layout.",
        "version": "1.0.0",
        "config": {
            "schema_version": "1.0",
            "theme": {
                "background_color": "#0A0D12",
                "card_surface_color": "#121620",
                "primary_accent": "#E5C378",
                "secondary_accent": "#A68A56",
                "text_color": "#F8FAFC",
                "border_color": "#222938",
                "heading_font_key": "cormorant_garamond",
                "body_font_key": "dm_sans",
                "gujarati_font_key": "noto_serif_gujarati",
                "hindi_font_key": "noto_serif_devanagari"
            },
            "layout": {
                "header_variant": "editorial_monogram",
                "rating_variant": "refined_constellation",
                "topic_selector_variant": "vertical_attribute_cards",
                "review_suggestion_card_variant": "spacious_bronze",
                "review_editor_variant": "minimalist_suite",
                "button_variant": "champagne_outline",
                "spacing_preset": "premium",
                "border_radius_preset": "none",
                "layout_density": "spacious"
            },
            "components": [
                "business_header", "rating_selector", "topic_selector",
                "personal_note", "ai_suggestions", "review_editor",
                "google_handoff", "private_feedback"
            ],
            "topics": RESTAURANT_DEFAULT_TOPICS,
            "rating_labels": {
                "5": {"text": "An Exquisite Journey", "emoji": "✦"},
                "4": {"text": "Distinguished Experience", "emoji": "✧"},
                "3": {"text": "Pleasant", "emoji": "🙂"},
                "2": {"text": "Below Expectations", "emoji": "😕"},
                "1": {"text": "Unsatisfactory", "emoji": "😞"}
            },
            "experience_labels": {
                "whatStoodOut": "Curated Impressions",
                "pickMatched": "Select the hallmarks of your evening",
                "notePlaceholder": "e.g. The sommelier pairing and chef tasting notes were immaculate."
            },
            "localized_content": {
                "en": {
                    "welcome_title": "How was your evening with us?",
                    "welcome_sub": "Your impressions shape our culinary standards"
                },
                "gu": {
                    "welcome_title": "અમારી સાથે તમારી સાંજ કેવી રહી?",
                    "welcome_sub": "તમારા વિચારો અમારા રાંધણ ધોરણોને ઘડે છે"
                },
                "hi": {
                    "welcome_title": "हमारे साथ आपकी शाम कैसी रही?",
                    "welcome_sub": "आपके अनुभव हमारे आतिथ्य को निखारते हैं"
                }
            }
        }
    },
    {
        "id": "restaurant_cafe_playful",
        "industry_id": "ind_restaurant",
        "name": "Café & Playful",
        "slug": "restaurant_cafe_playful",
        "description": "Warm, welcoming neighborhood café and bakery aesthetic with soft morning cream surfaces, terracotta peach, and rounded sticker components.",
        "version": "1.0.0",
        "config": {
            "schema_version": "1.0",
            "theme": {
                "background_color": "#FFFDF7",
                "card_surface_color": "#FFFFFF",
                "primary_accent": "#FB923C",
                "secondary_accent": "#FBBF24",
                "text_color": "#2D2118",
                "border_color": "#F3E8D6",
                "heading_font_key": "nunito",
                "body_font_key": "nunito_sans",
                "gujarati_font_key": "noto_sans_gujarati",
                "hindi_font_key": "noto_sans_devanagari"
            },
            "layout": {
                "header_variant": "illustrated_banner",
                "rating_variant": "bouncy_emoji_stars",
                "topic_selector_variant": "colorful_stickers",
                "review_suggestion_card_variant": "speech_bubbles",
                "review_editor_variant": "playful_card",
                "button_variant": "peach_rounded",
                "spacing_preset": "friendly",
                "border_radius_preset": "full",
                "layout_density": "normal"
            },
            "components": [
                "business_header", "rating_selector", "topic_selector",
                "personal_note", "ai_suggestions", "review_editor",
                "google_handoff", "private_feedback"
            ],
            "topics": RESTAURANT_DEFAULT_TOPICS,
            "rating_labels": {
                "5": {"text": "Loved it!", "emoji": "🤩"},
                "4": {"text": "Really good", "emoji": "😊"},
                "3": {"text": "Pretty nice", "emoji": "🙂"},
                "2": {"text": "Needs love", "emoji": "😕"},
                "1": {"text": "Bummer", "emoji": "😞"}
            },
            "experience_labels": {
                "whatStoodOut": "What hit the spot?",
                "pickMatched": "Tap all the goodies you loved",
                "notePlaceholder": "e.g. Best flat white and warm sourdough in town!"
            },
            "localized_content": {
                "en": {
                    "welcome_title": "How was your visit?",
                    "welcome_sub": "Brewed with love • Share your thoughts"
                },
                "gu": {
                    "welcome_title": "તમારી મુલાકાત કેવી રહી?",
                    "welcome_sub": "પ્રેમથી પીરસવામાં આવ્યું • તમારા વિચારો શેર કરો"
                },
                "hi": {
                    "welcome_title": "आपकी यात्रा कैसी रही?",
                    "welcome_sub": "प्यार से बनाया गया • अपने विचार साझा करें"
                }
            }
        }
    }
]


# ─── DATABASE INITIALIZATION & SCHEMA ─────────────────────────────────────────

def init_template_schema(db: sqlite3.Connection) -> None:
    """Create additive tables and indexes for Dynamic Industry Template system."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS industries (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT '🏢',
            status TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_industries_slug ON industries(slug)")

    db.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            industry_id TEXT NOT NULL REFERENCES industries(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_templates_industry ON templates(industry_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_templates_slug ON templates(slug)")

    db.execute("""
        CREATE TABLE IF NOT EXISTS template_versions (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
            version TEXT NOT NULL,
            configuration_json TEXT NOT NULL,
            schema_version TEXT NOT NULL DEFAULT '1.0',
            publication_status TEXT NOT NULL DEFAULT 'published',
            published_at REAL,
            created_at REAL NOT NULL,
            created_by TEXT DEFAULT 'system',
            UNIQUE(template_id, version)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_template_versions_tpl ON template_versions(template_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_template_versions_pub ON template_versions(template_id, publication_status)")

    db.execute("""
        CREATE TABLE IF NOT EXISTS business_template_assignments (
            id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            template_id TEXT NOT NULL REFERENCES templates(id) ON DELETE RESTRICT,
            template_version_id TEXT NOT NULL REFERENCES template_versions(id) ON DELETE RESTRICT,
            assigned_by TEXT DEFAULT 'system',
            assigned_at REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_biz_assignments_biz ON business_template_assignments(business_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_biz_assignments_status ON business_template_assignments(business_id, status)")

    db.execute("""
        CREATE TABLE IF NOT EXISTS business_configurations (
            id TEXT PRIMARY KEY,
            business_id TEXT UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            logo_url TEXT DEFAULT '',
            cover_image_url TEXT DEFAULT '',
            primary_accent TEXT DEFAULT '',
            custom_topics_json TEXT DEFAULT '[]',
            localized_content_json TEXT DEFAULT '{}',
            google_review_url TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_biz_configs_biz ON business_configurations(business_id)")


def seed_default_templates(db: sqlite3.Connection) -> None:
    """Idempotently seed default industries, four approved restaurant templates, and versions."""
    now = time.time()

    # 1. Seed industries
    for ind in DEFAULT_INDUSTRIES:
        db.execute("""
            INSERT OR IGNORE INTO industries (id, name, slug, description, icon, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ind["id"], ind["name"], ind["slug"], ind["description"], ind["icon"], ind["status"], now, now))

    # 2. Seed multi-industry templates
    for tpl in DEFAULT_TEMPLATES:
        db.execute("""
            INSERT OR IGNORE INTO templates (id, industry_id, name, slug, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
        """, (tpl["id"], tpl["industry_id"], tpl["name"], tpl["slug"], tpl["description"], now, now))

        version_id = f"ver_{tpl['slug']}_{tpl['version'].replace('.', '_')}"
        db.execute("""
            INSERT OR IGNORE INTO template_versions (
                id, template_id, version, configuration_json, schema_version, publication_status, published_at, created_at, created_by
            ) VALUES (?, ?, ?, ?, '1.0', 'published', ?, ?, 'system')
        """, (version_id, tpl["id"], tpl["version"], json.dumps(tpl["config"]), now, now))

    # 3. Seed four approved restaurant templates
    for tpl in FOUR_APPROVED_RESTAURANT_PRESETS:
        db.execute("""
            INSERT OR IGNORE INTO templates (id, industry_id, name, slug, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
        """, (tpl["id"], tpl["industry_id"], tpl["name"], tpl["slug"], tpl["description"], now, now))

        version_id = f"ver_{tpl['slug']}_{tpl['version'].replace('.', '_')}"
        db.execute("""
            INSERT OR IGNORE INTO template_versions (
                id, template_id, version, configuration_json, schema_version, publication_status, published_at, created_at, created_by
            ) VALUES (?, ?, ?, ?, '1.0', 'published', ?, ?, 'system')
        """, (version_id, tpl["id"], tpl["version"], json.dumps(tpl["config"]), now, now))

    # 3. Default business rule: preserve existing assignment if one exists; if none exists, assign restaurant_classic_bistro
    existing_assignment = db.execute(
        "SELECT id, template_id FROM business_template_assignments WHERE business_id = 'default_business' AND status = 'active'"
    ).fetchone()

    if not existing_assignment:
        classic_ver = db.execute(
            "SELECT id FROM template_versions WHERE template_id = 'restaurant_classic_bistro' AND publication_status = 'published' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if classic_ver:
            db.execute("""
                INSERT INTO business_template_assignments (id, business_id, template_id, template_version_id, assigned_by, assigned_at, status)
                VALUES (?, 'default_business', 'restaurant_classic_bistro', ?, 'system', ?, 'active')
            """, (str(uuid.uuid4()), classic_ver[0], now))

    # 4. Seed default business_configuration if missing
    existing_cfg = db.execute("SELECT id FROM business_configurations WHERE business_id = 'default_business'").fetchone()
    if not existing_cfg:
        default_tenant = db.execute("SELECT review_url, primary_accent FROM tenants WHERE id = 'default_business'").fetchone()
        r_url = default_tenant[0] if default_tenant else "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro"
        p_acc = default_tenant[1] if default_tenant else "#1B4332"
        db.execute("""
            INSERT INTO business_configurations (id, business_id, logo_url, cover_image_url, primary_accent, custom_topics_json, localized_content_json, google_review_url, status, created_at, updated_at)
            VALUES (?, 'default_business', '', '', ?, '[]', '{}', ?, 'active', ?, ?)
        """, (str(uuid.uuid4()), p_acc, r_url, now, now))


# ─── REPOSITORY IMPLEMENTATION ───────────────────────────────────────────────

class TemplateRepository:
    def __init__(self, db_connect_fn):
        self._connect = db_connect_fn

    # ── Industry operations ──
    def list_industries(self) -> List[Dict[str, Any]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM industries WHERE status = 'active' ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    # ── Template operations ──
    def list_templates(self, industry_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            query = """
                SELECT t.*, i.name as industry_name, i.slug as industry_slug, i.icon as industry_icon,
                       v.id as active_version_id, v.version as active_version, v.configuration_json
                FROM templates t
                JOIN industries i ON t.industry_id = i.id
                LEFT JOIN template_versions v ON t.id = v.template_id AND v.publication_status = 'published'
                WHERE t.status != 'archived'
            """
            params = []
            if industry_slug:
                query += " AND i.slug = ?"
                params.append(industry_slug)
            query += " ORDER BY t.name ASC"

            rows = db.execute(query, params).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                if item.get("configuration_json"):
                    try:
                        item["configuration"] = json.loads(item["configuration_json"])
                    except Exception:
                        item["configuration"] = {}
                else:
                    item["configuration"] = {}
                result.append(item)
            return result

    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("""
                SELECT t.*, i.name as industry_name, i.slug as industry_slug, i.icon as industry_icon,
                       v.id as active_version_id, v.version as active_version, v.configuration_json
                FROM templates t
                JOIN industries i ON t.industry_id = i.id
                LEFT JOIN template_versions v ON t.id = v.template_id AND v.publication_status = 'published'
                WHERE t.id = ?
            """, (template_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("configuration_json"):
                try:
                    item["configuration"] = json.loads(item["configuration_json"])
                except Exception:
                    item["configuration"] = {}
            return item

    def archive_template(self, template_id: str) -> Dict[str, Any]:
        with self._connect() as db:
            now = time.time()
            cursor = db.execute("UPDATE templates SET status = 'archived', updated_at = ? WHERE id = ?", (now, template_id))
            if cursor.rowcount == 0:
                raise ValueError(f"Template '{template_id}' not found")
            return {"template_id": template_id, "status": "archived", "updated_at": now}

    # ── Version management operations ──
    def list_template_versions(self, template_id: str) -> List[Dict[str, Any]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM template_versions WHERE template_id = ? ORDER BY created_at DESC",
                (template_id,)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["configuration"] = json.loads(item.get("configuration_json") or "{}")
                except Exception:
                    item["configuration"] = {}
                result.append(item)
            return result

    def get_template_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM template_versions WHERE id = ?", (version_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            try:
                item["configuration"] = json.loads(item.get("configuration_json") or "{}")
            except Exception:
                item["configuration"] = {}
            return item

    def create_draft_version(
        self, template_id: str, version: str, configuration_json: str, created_by: str = "admin"
    ) -> Dict[str, Any]:
        """Creates a new editable draft version for a template. Rejects duplicate version string."""
        with self._connect() as db:
            # Verify template exists and is not archived
            tpl = db.execute("SELECT id, status FROM templates WHERE id = ?", (template_id,)).fetchone()
            if not tpl:
                raise ValueError(f"Template '{template_id}' not found")
            if tpl[1] == "archived":
                raise ValueError(f"Cannot create new version for archived template '{template_id}'")

            # Check version uniqueness
            existing = db.execute(
                "SELECT id FROM template_versions WHERE template_id = ? AND version = ?",
                (template_id, version)
            ).fetchone()
            if existing:
                raise ValueError(f"Version '{version}' already exists for template '{template_id}'")

            now = time.time()
            version_id = f"ver_{template_id}_{version.replace('.', '_')}_{uuid.uuid4().hex[:6]}"
            db.execute("""
                INSERT INTO template_versions (id, template_id, version, configuration_json, schema_version, publication_status, created_at, created_by)
                VALUES (?, ?, ?, ?, '1.0', 'draft', ?, ?)
            """, (version_id, template_id, version, configuration_json, now, created_by))

            return {
                "id": version_id,
                "template_id": template_id,
                "version": version,
                "publication_status": "draft",
                "created_at": now,
                "created_by": created_by
            }

    def update_draft_version(self, version_id: str, configuration_json: str) -> Dict[str, Any]:
        """Updates an existing draft version. Throws error if version is published or archived (immutable)."""
        with self._connect() as db:
            ver = db.execute(
                "SELECT id, publication_status FROM template_versions WHERE id = ?", (version_id,)
            ).fetchone()
            if not ver:
                raise ValueError(f"Template version '{version_id}' not found")

            status = ver[1]
            if status == "published":
                raise ValueError(
                    f"Template version '{version_id}' is published and immutable. "
                    "Create a new draft version to modify configuration."
                )
            if status == "archived":
                raise ValueError(f"Template version '{version_id}' is archived and cannot be edited.")

            db.execute(
                "UPDATE template_versions SET configuration_json = ? WHERE id = ?",
                (configuration_json, version_id)
            )
            return {"id": version_id, "status": "updated"}

    def publish_version(self, version_id: str, published_by: str = "admin") -> Dict[str, Any]:
        """Publishes a draft version, making it immutable and assignable to businesses."""
        with self._connect() as db:
            ver = db.execute(
                "SELECT id, template_id, version, publication_status FROM template_versions WHERE id = ?", (version_id,)
            ).fetchone()
            if not ver:
                raise ValueError(f"Template version '{version_id}' not found")

            if ver[3] == "published":
                return {"id": version_id, "status": "already_published"}
            if ver[3] == "archived":
                raise ValueError(f"Cannot publish archived version '{version_id}'")

            now = time.time()
            db.execute(
                "UPDATE template_versions SET publication_status = 'published', published_at = ? WHERE id = ?",
                (now, version_id)
            )
            return {"id": version_id, "status": "published", "published_at": now, "published_by": published_by}

    # ── Business Assignment & Version Pinning ──
    def get_active_business_assignment(self, business_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("""
                SELECT a.*, t.name as template_name, t.slug as template_slug,
                       i.name as industry_name, i.slug as industry_slug, i.icon as industry_icon,
                       v.version as template_version, v.configuration_json, v.publication_status as version_status
                FROM business_template_assignments a
                JOIN templates t ON a.template_id = t.id
                JOIN industries i ON t.industry_id = i.id
                JOIN template_versions v ON a.template_version_id = v.id
                WHERE a.business_id = ? AND a.status = 'active'
                ORDER BY a.assigned_at DESC
                LIMIT 1
            """, (business_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("configuration_json"):
                try:
                    item["configuration"] = json.loads(item["configuration_json"])
                except Exception:
                    item["configuration"] = {}
            return item

    def assign_template_to_business(
        self, business_id: str, template_id: str, version_id: Optional[str] = None, assigned_by: str = "admin"
    ) -> Dict[str, Any]:
        """
        Assigns an approved template version to a business.
        Enforces:
        1. Business tenant exists and is registered.
        2. Template exists and is active.
        3. Version exists and is PUBLISHED (cannot assign draft or archived version).
        4. Preserves previous active assignment with status = 'superseded'.
        """
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            now = time.time()

            # 1. Validate business exists
            biz = db.execute("SELECT id, status FROM tenants WHERE id = ?", (business_id,)).fetchone()
            if not biz:
                raise ValueError(f"Business '{business_id}' does not exist as an authorized tenant")

            # 2. Validate template exists and is active
            tpl = db.execute("SELECT id, status, industry_id FROM templates WHERE id = ?", (template_id,)).fetchone()
            if not tpl:
                raise ValueError(f"Template '{template_id}' not found")
            if tpl["status"] == "archived":
                raise ValueError(f"Cannot assign archived template '{template_id}' to business")

            # 3. Determine or validate published version
            if version_id:
                ver = db.execute(
                    "SELECT id, publication_status FROM template_versions WHERE id = ? AND template_id = ?",
                    (version_id, template_id)
                ).fetchone()
                if not ver:
                    raise ValueError(f"Version '{version_id}' does not belong to template '{template_id}'")
                if ver["publication_status"] != "published":
                    raise ValueError(f"Cannot assign version '{version_id}' because its status is '{ver['publication_status']}'. Only published versions can be assigned.")
                target_version_id = ver["id"]
            else:
                ver = db.execute(
                    "SELECT id FROM template_versions WHERE template_id = ? AND publication_status = 'published' ORDER BY created_at DESC LIMIT 1",
                    (template_id,)
                ).fetchone()
                if not ver:
                    raise ValueError(f"No published version found for template '{template_id}'")
                target_version_id = ver["id"]

            # 4. Mark previous active assignment as superseded
            db.execute(
                "UPDATE business_template_assignments SET status = 'superseded' WHERE business_id = ? AND status = 'active'",
                (business_id,)
            )

            # 5. Insert new assignment
            new_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO business_template_assignments (id, business_id, template_id, template_version_id, assigned_by, assigned_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (new_id, business_id, template_id, target_version_id, assigned_by, now))

            return {
                "assignment_id": new_id,
                "business_id": business_id,
                "template_id": template_id,
                "template_version_id": target_version_id,
                "status": "active",
                "assigned_at": now,
                "assigned_by": assigned_by
            }

    def upgrade_business_assignment(
        self, business_id: str, target_version_id: str, upgraded_by: str = "admin"
    ) -> Dict[str, Any]:
        """
        Explicit administrator operation to upgrade a business's pinned version.
        Guarantees that existing assignments never silently auto-upgrade.
        """
        with self._connect() as db:
            active_assign = self.get_active_business_assignment(business_id)
            if not active_assign:
                raise ValueError(f"No active template assignment found for business '{business_id}'")

            target_ver = self.get_template_version(target_version_id)
            if not target_ver:
                raise ValueError(f"Target version '{target_version_id}' not found")
            if target_ver["publication_status"] != "published":
                raise ValueError(f"Target version must be published (current: '{target_ver['publication_status']}')")

            # Execute upgrade through assign_template_to_business
            return self.assign_template_to_business(
                business_id=business_id,
                template_id=target_ver["template_id"],
                version_id=target_version_id,
                assigned_by=upgraded_by
            )

    # ── Business Configuration Overrides ──
    def get_or_create_business_config(self, business_id: str) -> Dict[str, Any]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM business_configurations WHERE business_id = ?", (business_id,)).fetchone()
            if row:
                item = dict(row)
                try:
                    item["custom_topics"] = json.loads(item.get("custom_topics_json") or "[]")
                except Exception:
                    item["custom_topics"] = []
                try:
                    item["localized_content"] = json.loads(item.get("localized_content_json") or "{}")
                except Exception:
                    item["localized_content"] = {}
                return item

            # Auto-create baseline if missing
            now = time.time()
            new_id = str(uuid.uuid4())
            tenant = db.execute("SELECT review_url, primary_accent FROM tenants WHERE id = ?", (business_id,)).fetchone()
            r_url = tenant["review_url"] if tenant else ""
            accent = tenant["primary_accent"] if tenant else "#1B4332"

            db.execute("""
                INSERT INTO business_configurations (id, business_id, logo_url, cover_image_url, primary_accent, custom_topics_json, localized_content_json, google_review_url, status, created_at, updated_at)
                VALUES (?, ?, '', '', ?, '[]', '{}', ?, 'active', ?, ?)
            """, (new_id, business_id, accent, r_url, now, now))

            return {
                "id": new_id,
                "business_id": business_id,
                "logo_url": "",
                "cover_image_url": "",
                "primary_accent": accent,
                "custom_topics": [],
                "localized_content": {},
                "google_review_url": r_url,
                "status": "active"
            }

    def update_business_config(
        self,
        business_id: str,
        logo_url: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        primary_accent: Optional[str] = None,
        custom_topics: Optional[List[Dict[str, Any]]] = None,
        localized_content: Optional[Dict[str, Any]] = None,
        google_review_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        existing = self.get_or_create_business_config(business_id)
        now = time.time()

        up_logo = logo_url if logo_url is not None else existing.get("logo_url", "")
        up_cover = cover_image_url if cover_image_url is not None else existing.get("cover_image_url", "")
        up_accent = primary_accent if primary_accent is not None else existing.get("primary_accent", "#1B4332")
        up_topics = json.dumps(custom_topics) if custom_topics is not None else json.dumps(existing.get("custom_topics", []))
        up_loc = json.dumps(localized_content) if localized_content is not None else json.dumps(existing.get("localized_content", {}))
        up_url = google_review_url if google_review_url is not None else existing.get("google_review_url", "")

        with self._connect() as db:
            db.execute("""
                UPDATE business_configurations
                SET logo_url = ?, cover_image_url = ?, primary_accent = ?, custom_topics_json = ?,
                    localized_content_json = ?, google_review_url = ?, updated_at = ?
                WHERE business_id = ?
            """, (up_logo, up_cover, up_accent, up_topics, up_loc, up_url, now, business_id))

        return self.get_or_create_business_config(business_id)

    # ── Sanitized Public Configuration Resolution ──
    def get_public_business_config(self, business_id: str) -> Dict[str, Any]:
        """
        Builds the complete, sanitized public customer configuration DTO.
        Fetches the EXACT pinned published template version. Never exposes drafts,
        internal audit history, or other businesses' private data.
        Guarantees Google Anti-Gating compliance.
        """
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            tenant = db.execute("SELECT * FROM tenants WHERE id = ?", (business_id,)).fetchone()
            if not tenant:
                # Case C: Nonexistent business ID -> Raise ValueError (mapped to HTTP 404)
                raise ValueError(f"Business '{business_id}' not found")

            t_dict = dict(tenant)

        # 1. Resolve exact pinned template assignment for this tenant
        assignment = self.get_active_business_assignment(t_dict["id"])

        if assignment:
            # Case A: Existing business with active template assignment
            template_meta = {
                "id": assignment["template_id"],
                "name": assignment["template_name"],
                "slug": assignment["template_slug"],
                "industry_name": assignment["industry_name"],
                "industry_slug": assignment["industry_slug"],
                "industry_icon": assignment["industry_icon"],
                "version": assignment["template_version"],
                "config": assignment.get("configuration") or {}
            }
        else:
            # Case B: Existing business without an active template assignment
            # Fall back to baseline restaurant preset while strictly preserving this tenant's identity, review URL, and accent
            default_tpl = FOUR_APPROVED_RESTAURANT_PRESETS[0]
            template_meta = {
                "id": default_tpl["id"],
                "name": default_tpl["name"],
                "slug": default_tpl["slug"],
                "industry_name": "Restaurant & Dining",
                "industry_slug": "restaurant",
                "industry_icon": "🍽️",
                "version": default_tpl["version"],
                "config": default_tpl["config"]
            }

        # 2. Get business configuration overrides
        biz_cfg = self.get_or_create_business_config(t_dict["id"])

        # 3. Compute effective topics: custom_topics if defined and non-empty, else template default topics
        template_config = template_meta.get("config", {})
        default_topics = template_config.get("topics", RESTAURANT_DEFAULT_TOPICS)
        effective_topics = biz_cfg.get("custom_topics") if (biz_cfg.get("custom_topics") and len(biz_cfg["custom_topics"]) > 0) else default_topics

        # 4. Compute effective theme
        base_theme = template_config.get("theme", {})
        effective_accent = biz_cfg.get("primary_accent") or t_dict.get("primary_accent") or base_theme.get("primary_accent") or base_theme.get("primaryAccent", "#1B4332")
        theme_merged = {
            **base_theme,
            "primary_accent": effective_accent,
            "primaryAccent": effective_accent,
            "background_color": base_theme.get("background_color") or base_theme.get("backgroundColor", "#FAF7F2"),
            "backgroundColor": base_theme.get("backgroundColor") or base_theme.get("background_color", "#FAF7F2"),
            "variant": base_theme.get("variant") or "restaurant_classic",
            "logo_url": biz_cfg.get("logo_url", ""),
            "cover_image_url": biz_cfg.get("cover_image_url", ""),
        }

        # 5. Effective Google Review URL (Strictly present for Anti-Gating compliance)
        effective_review_url = biz_cfg.get("google_review_url") or t_dict.get("review_url") or "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro"

        # 6. Localized content merge
        merged_localized = {
            **template_config.get("localized_content", {}),
            **biz_cfg.get("localized_content", {})
        }

        return {
            "businessId": t_dict["id"],
            "businessName": t_dict.get("business_name", "Nasta Ghar"),
            "category": t_dict.get("category", "Restaurant"),
            "googleReviewUrl": effective_review_url,
            "antiGatingCompliant": True,  # Equal Google Maps access regardless of rating
            "industry": {
                "slug": template_meta["industry_slug"],
                "name": template_meta["industry_name"],
                "icon": template_meta["industry_icon"]
            },
            "template": {
                "id": template_meta["id"],
                "name": template_meta["name"],
                "slug": template_meta["slug"],
                "version": template_meta["version"]
            },
            "theme": theme_merged,
            "layout": template_config.get("layout", {}),
            "components": list(template_config.get("components", [
                "business_header", "rating_selector", "topic_selector",
                "personal_note", "ai_suggestions", "review_editor",
                "google_handoff", "private_feedback"
            ])) if "google_handoff" in template_config.get("components", ["google_handoff"]) else list(template_config.get("components", [])) + ["google_handoff"],
            "topics": effective_topics,
            "ratingLabels": template_config.get("rating_labels", {}),
            "experienceLabels": template_config.get("experience_labels", {}),
            "localizedContent": merged_localized
        }
