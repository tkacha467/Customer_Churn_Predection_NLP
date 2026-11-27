#!/usr/bin/env python3
"""
VRAJA AI — 30 Canonical Dynamic Templates & 6 Industries Database Migration
Seeds/migrates exactly 6 canonical industries and 30 canonical templates + versions into staging database.
Idempotent, non-destructive, strictly isolated to staging.
"""

import sys
import sqlite3
import json
import time
from pathlib import Path

CANONICAL_INDUSTRIES = [
    {
        "id": "ind_restaurant",
        "name": "Restaurant & Dining",
        "slug": "restaurant",
        "description": "Cafes, traditional eateries, fine dining, bistros, and quick-service food brands.",
        "icon": "🍽️",
        "status": "active"
    },
    {
        "id": "ind_salon",
        "name": "Salon, Spa & Wellness",
        "slug": "salon",
        "description": "Barbershops, hair salons, luxury spas, nail studios, and makeup artistry.",
        "icon": "✂️",
        "status": "active"
    },
    {
        "id": "ind_retail",
        "name": "Retail & Apparel",
        "slug": "retail",
        "description": "High-fashion boutiques, streetwear drops, ethnic wear, and artisanal lifestyle stores.",
        "icon": "🛍️",
        "status": "active"
    },
    {
        "id": "ind_hotel",
        "name": "Hotel & Hospitality",
        "slug": "hotel",
        "description": "Luxury resorts, boutique hotels, heritage inns, transit stays, and eco-lodges.",
        "icon": "🏨",
        "status": "active"
    },
    {
        "id": "ind_fitness",
        "name": "Fitness & Wellness",
        "slug": "fitness",
        "description": "Iron gyms, yoga sanctuaries, crossfit boxes, personal training, and movement studios.",
        "icon": "💪",
        "status": "active"
    },
    {
        "id": "ind_clinic",
        "name": "Healthcare & Clinic",
        "slug": "clinic",
        "description": "General care, dental studios, pediatric care, physiotherapy, and diagnostic labs.",
        "icon": "🩺",
        "status": "active"
    }
]

CANONICAL_30_TEMPLATES = [
    # ══════════════════════════════════════════════════════════════
    # 1. FOOD & DINING (F01–F05)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "restaurant_classic_bistro",
        "industry_id": "ind_restaurant",
        "name": "Classic Bistro",
        "slug": "restaurant_classic_bistro",
        "description": "Elegant, warm, traditional dining with vintage parchment surfaces, deep emerald accents, and refined typography.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "restaurant_classic_bistro",
                "primaryAccent": "#1B4332",
                "secondaryAccent": "#D4AF37",
                "backgroundColor": "#FAF7F2",
                "cardBackground": "#FFFFFF",
                "textColor": "#1C1917",
                "subtextColor": "#78716C",
                "borderColor": "#E7E5E4",
                "heroBannerType": "classic_crest"
            },
            "topics": [
                {"label": "Food Quality", "icon": "🍽️"},
                {"label": "Taste", "icon": "😋"},
                {"label": "Freshness", "icon": "🥗"},
                {"label": "Service", "icon": "⚡"},
                {"label": "Ambience", "icon": "🕯️"},
                {"label": "Cleanliness", "icon": "🧼"}
            ],
            "ratingLabels": {
                "5": {"text": "Exceptional!", "emoji": "🌟"},
                "4": {"text": "Very Good", "emoji": "😊"},
                "3": {"text": "Satisfactory", "emoji": "🙂"},
                "2": {"text": "Needs Improvement", "emoji": "😕"},
                "1": {"text": "Disappointing", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your dining experience special?",
                "pickMatched": "Select the highlights of your meal",
                "notePlaceholder": "e.g. Signature dishes and attentive service were outstanding."
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
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "restaurant_modern_urban",
                "primaryAccent": "#22C55E",
                "secondaryAccent": "#EAB308",
                "backgroundColor": "#09090B",
                "cardBackground": "#18181B",
                "textColor": "#FAFAFA",
                "subtextColor": "#A1A1AA",
                "borderColor": "#27272A",
                "heroBannerType": "split_urban"
            },
            "topics": [
                {"label": "Signature Dishes", "icon": "🔥"},
                {"label": "Craft Beverages", "icon": "🍹"},
                {"label": "Speed of Service", "icon": "⚡"},
                {"label": "Music & Vibe", "icon": "🎧"},
                {"label": "Value for Money", "icon": "💰"}
            ],
            "ratingLabels": {
                "5": {"text": "Top Tier!", "emoji": "⚡"},
                "4": {"text": "Solid Vibe", "emoji": "👍"},
                "3": {"text": "Average", "emoji": "😐"},
                "2": {"text": "Off Today", "emoji": "👎"},
                "1": {"text": "Wack", "emoji": "❌"}
            },
            "experienceLabels": {
                "whatStoodOut": "What hit the mark today?",
                "pickMatched": "Tap your visit highlights",
                "notePlaceholder": "e.g. Great music, fast delivery and killer flavors."
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
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "restaurant_luxury_dining",
                "primaryAccent": "#D4AF37",
                "secondaryAccent": "#F3E5AB",
                "backgroundColor": "#0A0A0C",
                "cardBackground": "#141418",
                "textColor": "#E8E8E8",
                "subtextColor": "#888892",
                "borderColor": "#2A2A32",
                "heroBannerType": "luxury_masthead"
            },
            "topics": [
                {"label": "Chef Tasting Menu", "icon": "🍷"},
                {"label": "Sommelier Pairing", "icon": "🍾"},
                {"label": "Impeccable Service", "icon": "🎩"},
                {"label": "Romantic Ambiance", "icon": "🕯️"},
                {"label": "Artistic Presentation", "icon": "✨"}
            ],
            "ratingLabels": {
                "5": {"text": "Sublime!", "emoji": "✨"},
                "4": {"text": "Distinguished", "emoji": "🥂"},
                "3": {"text": "Adequate", "emoji": "👌"},
                "2": {"text": "Unrefined", "emoji": "🍂"},
                "1": {"text": "Disappointing", "emoji": "🥀"}
            },
            "experienceLabels": {
                "whatStoodOut": "What defined your gastronomic journey?",
                "pickMatched": "Select the defining moments of your evening",
                "notePlaceholder": "e.g. The sommelier's pairing and dessert presentation were breathtaking."
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
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "restaurant_cafe_playful",
                "primaryAccent": "#FB923C",
                "secondaryAccent": "#FBBF24",
                "backgroundColor": "#FFFDF7",
                "cardBackground": "#FFFFFF",
                "textColor": "#374151",
                "subtextColor": "#9CA3AF",
                "borderColor": "#F3E8D6",
                "heroBannerType": "illustrated_cafe"
            },
            "topics": [
                {"label": "Artisan Coffee", "icon": "☕"},
                {"label": "Fresh Croissants", "icon": "🥐"},
                {"label": "Warm Sourdough", "icon": "🥖"},
                {"label": "Friendly Baristas", "icon": "😊"},
                {"label": "Cozy Seating", "icon": "🪴"},
                {"label": "Fast Wi-Fi", "icon": "💻"}
            ],
            "ratingLabels": {
                "5": {"text": "Loved it!", "emoji": "🥳"},
                "4": {"text": "Super Nice", "emoji": "😋"},
                "3": {"text": "Good Vibe", "emoji": "🙂"},
                "2": {"text": "Meh, Okay", "emoji": "🫤"},
                "1": {"text": "Not Great", "emoji": "🥱"}
            },
            "experienceLabels": {
                "whatStoodOut": "What hit the spot today?",
                "pickMatched": "Tap all the goodies you loved",
                "notePlaceholder": "e.g. Best flat white and warm almond croissant in town!"
            }
        }
    },
    {
        "id": "restaurant_sweet_dessert",
        "industry_id": "ind_restaurant",
        "name": "Sweet & Dessert House",
        "slug": "restaurant_sweet_dessert",
        "description": "Charming artisanal patisserie and gelato lounge with pastel confectionery surfaces, candy-drop ratings, and polaroid review framing.",
        "version": "1.0.0",
        "status": "draft",
        "pub_status": "draft",
        "config": {
            "theme": {
                "variant": "restaurant_sweet_dessert",
                "primaryAccent": "#EC4899",
                "secondaryAccent": "#A855F7",
                "backgroundColor": "#FDF2F8",
                "cardBackground": "#FFFFFF",
                "textColor": "#831843",
                "subtextColor": "#9D174D",
                "borderColor": "#FBCFE8",
                "heroBannerType": "dessert_showcase"
            },
            "topics": [
                {"label": "Signature Pastries", "icon": "🍰"},
                {"label": "Artisan Gelato", "icon": "🍨"},
                {"label": "Macarons & Truffles", "icon": "🍬"},
                {"label": "Decadent Waffles", "icon": "🧇"},
                {"label": "Sweet Packaging", "icon": "🎀"}
            ],
            "ratingLabels": {
                "5": {"text": "Heavenly!", "emoji": "💖"},
                "4": {"text": "Delicious", "emoji": "🧁"},
                "3": {"text": "Sweet", "emoji": "🍬"},
                "2": {"text": "Too Sweet", "emoji": "🫤"},
                "1": {"text": "Not Fresh", "emoji": "💔"}
            },
            "experienceLabels": {
                "whatStoodOut": "Which sweet treat made your day?",
                "pickMatched": "Select your favorite indulgences",
                "notePlaceholder": "e.g. The pistachio éclair and dark chocolate gelato were divine."
            }
        }
    },

    # ══════════════════════════════════════════════════════════════
    # 2. BEAUTY & GROOMING (B01–B05)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "salon_barber_lounge",
        "industry_id": "ind_salon",
        "name": "Classic Barbershop",
        "slug": "salon_barber_lounge",
        "description": "Vintage gentlemen's barber parlor with rich mahogany surfaces, brushed brass accents, and razor-sharp precision controls.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "salon_barber_lounge",
                "primaryAccent": "#B45309",
                "secondaryAccent": "#D97706",
                "backgroundColor": "#1C1917",
                "cardBackground": "#292524",
                "textColor": "#F5F5F4",
                "subtextColor": "#A8A29E",
                "borderColor": "#44403C",
                "heroBannerType": "vintage_barber"
            },
            "topics": [
                {"label": "Precision Fade", "icon": "✂️"},
                {"label": "Hot Towel Shave", "icon": "🪒"},
                {"label": "Beard Sculpting", "icon": "🧔"},
                {"label": "Hair Treatment", "icon": "🧴"},
                {"label": "Barber Hospitality", "icon": "🥃"},
                {"label": "Punctual Timing", "icon": "⏱️"}
            ],
            "ratingLabels": {
                "5": {"text": "Razor Sharp!", "emoji": "💈"},
                "4": {"text": "Solid Trim", "emoji": "✂️"},
                "3": {"text": "Decent Cut", "emoji": "👌"},
                "2": {"text": "Uneven", "emoji": "🫤"},
                "1": {"text": "Poor Cut", "emoji": "🤕"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your grooming session stand out?",
                "pickMatched": "Select your favorite grooming services",
                "notePlaceholder": "e.g. Master barber gave me the cleanest low-taper fade and hot towel shave."
            }
        }
    },
    {
        "id": "salon_skincare_lab",
        "industry_id": "ind_salon",
        "name": "Skincare & Aesthetic Lab",
        "slug": "salon_skincare_lab",
        "description": "Clinical-meets-luxury dermal skincare aesthetic lab with crisp laboratory accents and science-backed skin treatments.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "salon_skincare_lab",
                "primaryAccent": "#0284C7",
                "secondaryAccent": "#38BDF8",
                "backgroundColor": "#F8FAFC",
                "cardBackground": "#FFFFFF",
                "textColor": "#0F172A",
                "subtextColor": "#475569",
                "borderColor": "#E2E8F0",
                "heroBannerType": "skincare_lab"
            },
            "topics": [
                {"label": "Skin Analysis", "icon": "🔬"},
                {"label": "Hydrafacial Treatment", "icon": "💧"},
                {"label": "Chemical Peel / Glow", "icon": "✨"},
                {"label": "Expert Aesthetician", "icon": "👩‍⚕️"},
                {"label": "Hygienic Clinic Lab", "icon": "🧼"},
                {"label": "Tailored Routine", "icon": "🧴"}
            ],
            "ratingLabels": {
                "5": {"text": "Radiant Results!", "emoji": "✨"},
                "4": {"text": "Visible Glow", "emoji": "💧"},
                "3": {"text": "Good Care", "emoji": "🙂"},
                "2": {"text": "Minimal Change", "emoji": "😕"},
                "1": {"text": "Skin Irritation", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How did your skin treatment perform?",
                "pickMatched": "Select the dermal treatments you received",
                "notePlaceholder": "e.g. Thorough skin analysis and soothing facial treatment."
            }
        }
    },
    {
        "id": "salon_spa_sanctuary",
        "industry_id": "ind_salon",
        "name": "Luxury Day Spa Sanctuary",
        "slug": "salon_spa_sanctuary",
        "description": "Serene wellness and thermal spa with warm espresso textures, soothing botanical sage accents, and meditative atmosphere.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "salon_spa_sanctuary",
                "primaryAccent": "#0D9488",
                "secondaryAccent": "#14B8A6",
                "backgroundColor": "#F0FDF4",
                "cardBackground": "#FFFFFF",
                "textColor": "#134E4A",
                "subtextColor": "#115E59",
                "borderColor": "#CCFBF1",
                "heroBannerType": "botanical_spa"
            },
            "topics": [
                {"label": "Deep Tissue Massage", "icon": "💆"},
                {"label": "Hydrating Facial", "icon": "🧖‍♀️"},
                {"label": "Aromatherapy", "icon": "🌿"},
                {"label": "Body Scrub & Polish", "icon": "✨"},
                {"label": "Peaceful Ambience", "icon": "🕯️"},
                {"label": "Therapist Empathy", "icon": "🌸"}
            ],
            "ratingLabels": {
                "5": {"text": "Deeply Restored", "emoji": "🧘‍♀️"},
                "4": {"text": "Very Relaxing", "emoji": "💆"},
                "3": {"text": "Pleasant", "emoji": "🌿"},
                "2": {"text": "Rushed", "emoji": "😕"},
                "1": {"text": "Not Relaxing", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "What brought you the deepest relaxation?",
                "pickMatched": "Tap your restorative treatments",
                "notePlaceholder": "e.g. The hot stone massage and lavender aromatherapy were sublime."
            }
        }
    },
    {
        "id": "salon_bridal_glam",
        "industry_id": "ind_salon",
        "name": "Bridal & Glam Studio",
        "slug": "salon_bridal_glam",
        "description": "Celebrity glam makeup and bridal studio with champagne rose surfaces, sparkling ring-light highlights, and lookbook framing.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "salon_bridal_glam",
                "primaryAccent": "#E11D48",
                "secondaryAccent": "#FB7185",
                "backgroundColor": "#FFF1F2",
                "cardBackground": "#FFFFFF",
                "textColor": "#881337",
                "subtextColor": "#9F1239",
                "borderColor": "#FECDD3",
                "heroBannerType": "glam_studio"
            },
            "topics": [
                {"label": "Bridal Makeover", "icon": "👰"},
                {"label": "HD Airbrush Makeup", "icon": "💄"},
                {"label": "Party Glam", "icon": "✨"},
                {"label": "Skin Prep & Glow", "icon": "🌟"},
                {"label": "Artist Skill", "icon": "🎨"},
                {"label": "Long-Lasting Look", "icon": "⏱️"}
            ],
            "ratingLabels": {
                "5": {"text": "Flawless Glam!", "emoji": "💖"},
                "4": {"text": "Gorgeous Look", "emoji": "✨"},
                "3": {"text": "Decent Makeup", "emoji": "💄"},
                "2": {"text": "Cakey/Heavy", "emoji": "😕"},
                "1": {"text": "Smudged/Poor", "emoji": "😢"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your glam session unforgettable?",
                "pickMatched": "Select the highlights of your makeover",
                "notePlaceholder": "e.g. The bridal airbrush makeup stayed glowing and flawless all night!"
            }
        }
    },
    {
        "id": "salon_nail_lash",
        "industry_id": "ind_salon",
        "name": "Nail & Lash Studio",
        "slug": "salon_nail_lash",
        "description": "Trendy nail bar and lash lounge with glossy pastel aesthetics, delicate crystal accents, and artistic nail-palette controls.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "salon_nail_lash",
                "primaryAccent": "#8B5CF6",
                "secondaryAccent": "#C084FC",
                "backgroundColor": "#FAF5FF",
                "cardBackground": "#FFFFFF",
                "textColor": "#581C87",
                "subtextColor": "#6B21A8",
                "borderColor": "#E9D5FF",
                "heroBannerType": "nail_palette"
            },
            "topics": [
                {"label": "Gel Nail Art", "icon": "💅"},
                {"label": "Acrylic Extensions", "icon": "💎"},
                {"label": "Russian Manicure", "icon": "✨"},
                {"label": "Lash Extensions", "icon": "👁️"},
                {"label": "Lash Lift & Tint", "icon": "🌸"},
                {"label": "Hygienic Tools", "icon": "🧼"}
            ],
            "ratingLabels": {
                "5": {"text": "Perfection!", "emoji": "💅"},
                "4": {"text": "Super Cute", "emoji": "💖"},
                "3": {"text": "Decent Set", "emoji": "👌"},
                "2": {"text": "Chipped Early", "emoji": "😕"},
                "1": {"text": "Damaged Nails", "emoji": "💔"}
            },
            "experienceLabels": {
                "whatStoodOut": "How did your nails or lashes turn out?",
                "pickMatched": "Select your favorite treatments",
                "notePlaceholder": "e.g. Intricate custom chrome nail art and lightweight natural lashes."
            }
        }
    },

    # ══════════════════════════════════════════════════════════════
    # 3. RETAIL & APPAREL (R01–R05)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "retail_fashion_boutique",
        "industry_id": "ind_retail",
        "name": "High-Fashion Boutique",
        "slug": "retail_fashion_boutique",
        "description": "Luxury designer couture and curated wardrobe atelier with runway editorial layout and sleek minimalist card styling.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "retail_fashion_boutique",
                "primaryAccent": "#18181B",
                "secondaryAccent": "#E4E4E7",
                "backgroundColor": "#FFFFFF",
                "cardBackground": "#F4F4F5",
                "textColor": "#09090B",
                "subtextColor": "#71717A",
                "borderColor": "#E4E4E7",
                "heroBannerType": "runway_editorial"
            },
            "topics": [
                {"label": "Curated Collection", "icon": "👗"},
                {"label": "Fabric & Tailoring", "icon": "🧵"},
                {"label": "Styling Advice", "icon": "✨"},
                {"label": "Fitting Room Comfort", "icon": "🪞"},
                {"label": "Exclusive Designs", "icon": "💎"}
            ],
            "ratingLabels": {
                "5": {"text": "Haute Couture!", "emoji": "👑"},
                "4": {"text": "Chic & Stylish", "emoji": "✨"},
                "3": {"text": "Nice Collection", "emoji": "👗"},
                "2": {"text": "Limited Sizing", "emoji": "😕"},
                "1": {"text": "Poor Quality", "emoji": "🚫"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your wardrobe selection memorable?",
                "pickMatched": "Select your shopping highlights",
                "notePlaceholder": "e.g. Gorgeous Italian linen fabrics and personalized fashion styling."
            }
        }
    },
    {
        "id": "retail_streetwear_drop",
        "industry_id": "ind_retail",
        "name": "Streetwear & Sneaker Store",
        "slug": "retail_streetwear_drop",
        "description": "High-octane urban streetwear and sneaker boutique with barcode tags, industrial typography, and sticker drop accents.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "retail_streetwear_drop",
                "primaryAccent": "#EF4444",
                "secondaryAccent": "#F97316",
                "backgroundColor": "#0A0A0A",
                "cardBackground": "#171717",
                "textColor": "#F5F5F5",
                "subtextColor": "#A3A3A3",
                "borderColor": "#262626",
                "heroBannerType": "streetwear_drop"
            },
            "topics": [
                {"label": "Exclusive Drops", "icon": "👟"},
                {"label": "Authenticity Verified", "icon": "✅"},
                {"label": "Heavyweight Hoodies", "icon": "👕"},
                {"label": "Staff Knowledge", "icon": "🧢"},
                {"label": "Store Aesthetic", "icon": "⚡"}
            ],
            "ratingLabels": {
                "5": {"text": "Straight Fire!", "emoji": "🔥"},
                "4": {"text": "Dope Drop", "emoji": "⚡"},
                "3": {"text": "Fair Cop", "emoji": "👟"},
                "2": {"text": "High Resale", "emoji": "📉"},
                "1": {"text": "L Taken", "emoji": "💀"}
            },
            "experienceLabels": {
                "whatStoodOut": "What heat did you pick up today?",
                "pickMatched": "Select your drop highlights",
                "notePlaceholder": "e.g. Got the grail pair in my size with authentic tags and swift checkout."
            }
        }
    },
    {
        "id": "retail_organic_pantry",
        "industry_id": "ind_retail",
        "name": "Organic Market & Gourmet Pantry",
        "slug": "retail_organic_pantry",
        "description": "Farm-fresh organic market and pantry store with botanical cream surfaces, harvest green accents, and provenance badges.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "retail_organic_pantry",
                "primaryAccent": "#15803D",
                "secondaryAccent": "#65A30D",
                "backgroundColor": "#F7FEE7",
                "cardBackground": "#FFFFFF",
                "textColor": "#14532D",
                "subtextColor": "#3F6212",
                "borderColor": "#D9F99D",
                "heroBannerType": "organic_pantry"
            },
            "topics": [
                {"label": "Fresh Organic Produce", "icon": "🥬"},
                {"label": "Artisan Pantry Goods", "icon": "🍯"},
                {"label": "Eco Packaging", "icon": "🌱"},
                {"label": "Fair Farm Pricing", "icon": "💰"},
                {"label": "Helpful Store Staff", "icon": "😊"},
                {"label": "Clean Aisles", "icon": "✨"}
            ],
            "ratingLabels": {
                "5": {"text": "Farm Fresh!", "emoji": "🥬"},
                "4": {"text": "Great Harvest", "emoji": "🌱"},
                "3": {"text": "Good Pantry", "emoji": "🙂"},
                "2": {"text": "Low Stock", "emoji": "😕"},
                "1": {"text": "Poor Freshness", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your organic market visit?",
                "pickMatched": "Select your pantry & produce highlights",
                "notePlaceholder": "e.g. Ultra-fresh organic produce, raw honey selection and helpful staff."
            }
        }
    },
    {
        "id": "retail_tech_gadgets",
        "industry_id": "ind_retail",
        "name": "Electronics & Tech Haven",
        "slug": "retail_tech_gadgets",
        "description": "Cyber hardware and electronics outpost with dark HUD panels, cyan/violet power cells, and demo station badges.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "retail_tech_gadgets",
                "primaryAccent": "#06B6D4",
                "secondaryAccent": "#A855F7",
                "backgroundColor": "#030712",
                "cardBackground": "#0B1329",
                "textColor": "#E0E7FF",
                "subtextColor": "#94A3B8",
                "borderColor": "#1E293B",
                "heroBannerType": "cyber_hud"
            },
            "topics": [
                {"label": "Hardware Lineup", "icon": "💻"},
                {"label": "Audio & Peripherals", "icon": "🎧"},
                {"label": "Hands-On Demo", "icon": "🎮"},
                {"label": "Specialist Advice", "icon": "⚡"},
                {"label": "Warranty Support", "icon": "🛡️"},
                {"label": "Fair Tech Pricing", "icon": "💳"}
            ],
            "ratingLabels": {
                "5": {"text": "Overclocked!", "emoji": "⚡"},
                "4": {"text": "Great Specs", "emoji": "💻"},
                "3": {"text": "Good Gear", "emoji": "🙂"},
                "2": {"text": "Limited Stock", "emoji": "😕"},
                "1": {"text": "Poor Support", "emoji": "🚫"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your tech shopping experience?",
                "pickMatched": "Select your hardware & service highlights",
                "notePlaceholder": "e.g. Tested mechanical keyboards at the workstation and got clear expert advice."
            }
        }
    },
    {
        "id": "retail_artisanal_home",
        "industry_id": "ind_retail",
        "name": "Artisanal & Lifestyle Store",
        "slug": "retail_artisanal_home",
        "description": "Warm artisanal home decor and handcrafted lifestyle shop with terracotta textures, woven linen tags, and mindful living aesthetics.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "retail_artisanal_home",
                "primaryAccent": "#C2410C",
                "secondaryAccent": "#D97706",
                "backgroundColor": "#FAF5F0",
                "cardBackground": "#FFFFFF",
                "textColor": "#431407",
                "subtextColor": "#7C2D12",
                "borderColor": "#FED7AA",
                "heroBannerType": "artisanal_craft"
            },
            "topics": [
                {"label": "Handmade Ceramics", "icon": "🏺"},
                {"label": "Organic Linen", "icon": "🧶"},
                {"label": "Scented Candles", "icon": "🕯️"},
                {"label": "Sustainable Craft", "icon": "🌱"},
                {"label": "Artistic Gifts", "icon": "🎁"},
                {"label": "Eco Packaging", "icon": "📦"}
            ],
            "ratingLabels": {
                "5": {"text": "Pure Craftsmanship!", "emoji": "🪴"},
                "4": {"text": "Lovely Pieces", "emoji": "✨"},
                "3": {"text": "Nice Finds", "emoji": "🏺"},
                "2": {"text": "Fragile/Pricy", "emoji": "😕"},
                "1": {"text": "Broken Items", "emoji": "📦"}
            },
            "experienceLabels": {
                "whatStoodOut": "What handcrafted piece caught your eye?",
                "pickMatched": "Select your lifestyle favorites",
                "notePlaceholder": "e.g. Beautiful studio ceramics and soothing botanical scents."
            }
        }
    },

    # ══════════════════════════════════════════════════════════════
    # 4. HEALTHCARE & MEDICAL (H01–H05 - Quarantined Preview-Only)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "clinic_multi_specialty",
        "industry_id": "ind_clinic",
        "name": "Multi-Specialty Care Center",
        "slug": "clinic_multi_specialty",
        "description": "Preview-only clinical care center with hygienic card styling and mandatory neutral Patient Privacy Notice.",
        "version": "1.0.0",
        "status": "draft",
        "pub_status": "draft",
        "config": {
            "theme": {
                "variant": "clinic_multi_specialty",
                "primaryAccent": "#0284C7",
                "secondaryAccent": "#0EA5E9",
                "backgroundColor": "#F0F9FF",
                "cardBackground": "#FFFFFF",
                "textColor": "#0C4A6E",
                "subtextColor": "#0369A1",
                "borderColor": "#BAE6FD",
                "heroBannerType": "clinical_trust"
            },
            "topics": [
                {"label": "Doctor Empathy", "icon": "🩺"},
                {"label": "Clear Explanation", "icon": "📋"},
                {"label": "Minimal Waiting Time", "icon": "⏱️"},
                {"label": "Clean Facility", "icon": "🧼"},
                {"label": "Caring Staff", "icon": "🤝"}
            ],
            "ratingLabels": {
                "5": {"text": "Excellent Care", "emoji": "🩺"},
                "4": {"text": "Good Consultation", "emoji": "👍"},
                "3": {"text": "Standard Visit", "emoji": "👌"},
                "2": {"text": "Long Wait", "emoji": "⏱️"},
                "1": {"text": "Poor Care", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your consultation experience?",
                "pickMatched": "Select your clinic visit highlights",
                "notePlaceholder": "e.g. Doctor explained the diagnosis thoroughly with great empathy."
            }
        }
    },
    {
        "id": "clinic_dental_studio",
        "industry_id": "ind_clinic",
        "name": "Modern Dental Studio",
        "slug": "clinic_dental_studio",
        "description": "State-of-the-art dental lounge featuring bright cyan accents, sterile modern cards, and gentle painless care highlights.",
        "version": "1.0.0",
        "status": "draft",
        "pub_status": "draft",
        "config": {
            "theme": {
                "variant": "clinic_dental_studio",
                "primaryAccent": "#06B6D4",
                "secondaryAccent": "#0891B2",
                "backgroundColor": "#ECFEFF",
                "cardBackground": "#FFFFFF",
                "textColor": "#164E63",
                "subtextColor": "#155E75",
                "borderColor": "#A5F3FC",
                "heroBannerType": "dental_smile"
            },
            "topics": [
                {"label": "Painless Treatment", "icon": "🦷"},
                {"label": "Teeth Cleaning & Polish", "icon": "✨"},
                {"label": "Gentle Dentist", "icon": "😊"},
                {"label": "Modern Equipment", "icon": "🔬"},
                {"label": "Transparent Charges", "icon": "💰"}
            ],
            "ratingLabels": {
                "5": {"text": "Bright Smile!", "emoji": "🦷"},
                "4": {"text": "Very Gentle", "emoji": "✨"},
                "3": {"text": "Decent Dental", "emoji": "🙂"},
                "2": {"text": "Discomfort", "emoji": "😣"},
                "1": {"text": "Painful/Rough", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your dental care today?",
                "pickMatched": "Select your dental highlights",
                "notePlaceholder": "e.g. Completely painless tooth scaling and friendly dentist."
            }
        }
    },
    {
        "id": "clinic_wellness_preventive",
        "industry_id": "ind_clinic",
        "name": "Preventive Health & Longevity Center",
        "slug": "clinic_wellness_preventive",
        "description": "Preview-only preventive care sanctuary with gentle palette and mandatory neutral Patient Privacy Notice.",
        "version": "1.0.0",
        "status": "draft",
        "pub_status": "draft",
        "config": {
            "theme": {
                "variant": "clinic_wellness_preventive",
                "primaryAccent": "#F59E0B",
                "secondaryAccent": "#10B981",
                "backgroundColor": "#FEFCE8",
                "cardBackground": "#FFFFFF",
                "textColor": "#713F12",
                "subtextColor": "#854D0E",
                "borderColor": "#FEF08A",
                "heroBannerType": "pediatric_playful"
            },
            "topics": [
                {"label": "Child Comforted", "icon": "🧸"},
                {"label": "Gentle Vaccination", "icon": "💉"},
                {"label": "Patient Pediatrician", "icon": "🩺"},
                {"label": "Play Area Cleanliness", "icon": "🎨"},
                {"label": "Quick Prescription", "icon": "📝"}
            ],
            "ratingLabels": {
                "5": {"text": "Kids Loved It!", "emoji": "🧸"},
                "4": {"text": "Gentle & Kind", "emoji": "😊"},
                "3": {"text": "Good Doctor", "emoji": "🙂"},
                "2": {"text": "Crying/Waiting", "emoji": "😢"},
                "1": {"text": "Rough Care", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your child's clinic visit?",
                "pickMatched": "Select pediatric care highlights",
                "notePlaceholder": "e.g. Doctor made my daughter feel so safe and calm during vaccination."
            }
        }
    },
    {
        "id": "clinic_physio_rehab",
        "industry_id": "ind_clinic",
        "name": "Physiotherapy & Rehab Clinic",
        "slug": "clinic_physio_rehab",
        "description": "Active physical therapy and sports recovery clinic with dynamic posture progress cards and recovery goals.",
        "version": "1.0.0",
        "status": "draft",
        "pub_status": "draft",
        "config": {
            "theme": {
                "variant": "clinic_physio_rehab",
                "primaryAccent": "#10B981",
                "secondaryAccent": "#059669",
                "backgroundColor": "#ECFDF5",
                "cardBackground": "#FFFFFF",
                "textColor": "#064E3B",
                "subtextColor": "#065F46",
                "borderColor": "#A7F3D0",
                "heroBannerType": "mobility_rehab"
            },
            "topics": [
                {"label": "Pain Relief", "icon": "💪"},
                {"label": "Posture Correction", "icon": "🧘"},
                {"label": "Guided Exercises", "icon": "🏃"},
                {"label": "Modern Therapy Machines", "icon": "⚡"},
                {"label": "Home Exercise Plan", "icon": "📋"}
            ],
            "ratingLabels": {
                "5": {"text": "Great Relief!", "emoji": "🏃"},
                "4": {"text": "Good Therapy", "emoji": "💪"},
                "3": {"text": "Standard Session", "emoji": "🙂"},
                "2": {"text": "Slow Progress", "emoji": "😕"},
                "1": {"text": "Pain Increased", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How did your physical therapy session help?",
                "pickMatched": "Select your rehabilitation highlights",
                "notePlaceholder": "e.g. Noticed huge relief in lower back pain after the mobility session."
            }
        }
    },
    {
        "id": "clinic_diagnostic_lab",
        "industry_id": "ind_clinic",
        "name": "Diagnostics & Pathology Lab",
        "slug": "clinic_diagnostic_lab",
        "description": "High-accuracy diagnostic testing and pathology center with clinical precision badges and rapid digital report delivery.",
        "version": "1.0.0",
        "status": "draft",
        "pub_status": "draft",
        "config": {
            "theme": {
                "variant": "clinic_diagnostic_lab",
                "primaryAccent": "#4F46E5",
                "secondaryAccent": "#6366F1",
                "backgroundColor": "#EEF2FF",
                "cardBackground": "#FFFFFF",
                "textColor": "#312E81",
                "subtextColor": "#3730A3",
                "borderColor": "#C7D2FE",
                "heroBannerType": "lab_precision"
            },
            "topics": [
                {"label": "Painless Blood Draw", "icon": "🩸"},
                {"label": "Fast Report Delivery", "icon": "📄"},
                {"label": "Home Sample Collection", "icon": "🏠"},
                {"label": "Sterile Needle Kits", "icon": "🧼"},
                {"label": "Accurate Testing", "icon": "🔬"}
            ],
            "ratingLabels": {
                "5": {"text": "Prompt & Accurate", "emoji": "🔬"},
                "4": {"text": "Smooth Test", "emoji": "📄"},
                "3": {"text": "Standard Lab", "emoji": "🙂"},
                "2": {"text": "Delayed Report", "emoji": "⏱️"},
                "1": {"text": "Bruised/Inaccurate", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your diagnostic testing experience?",
                "pickMatched": "Select your laboratory highlights",
                "notePlaceholder": "e.g. Phlebotomist was gentle and reports arrived on WhatsApp in 4 hours."
            }
        }
    },

    # ══════════════════════════════════════════════════════════════
    # 5. HOTELS & HOSPITALITY (T01–T05)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "hotel_heritage_resort",
        "industry_id": "ind_hotel",
        "name": "Heritage Palace & Grand Resort",
        "slug": "hotel_heritage_resort",
        "description": "Elite heritage palace resort with royal champagne accents, panoramic courtyard views, and concierge styling.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "hotel_heritage_resort",
                "primaryAccent": "#D4AF37",
                "secondaryAccent": "#38BDF8",
                "backgroundColor": "#030712",
                "cardBackground": "#111827",
                "textColor": "#F9FAFB",
                "subtextColor": "#9CA3AF",
                "borderColor": "#1F2937",
                "heroBannerType": "resort_panorama"
            },
            "topics": [
                {"label": "Scenic Suite View", "icon": "🌅"},
                {"label": "Infinity Pool", "icon": "🏊"},
                {"label": "Concierge Service", "icon": "🛎️"},
                {"label": "Gourmet Breakfast", "icon": "🥂"},
                {"label": "Spa & Hydrotherapy", "icon": "🌸"},
                {"label": "Effortless Check-in", "icon": "⚡"}
            ],
            "ratingLabels": {
                "5": {"text": "Paradise!", "emoji": "🌴"},
                "4": {"text": "Luxurious Stay", "emoji": "🥂"},
                "3": {"text": "Pleasant Resort", "emoji": "🙂"},
                "2": {"text": "Below 5-Star", "emoji": "😕"},
                "1": {"text": "Poor Stay", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "What made your luxury getaway unforgettable?",
                "pickMatched": "Select your resort highlights",
                "notePlaceholder": "e.g. Breathtaking ocean sunset from the villa and attentive butler service."
            }
        }
    },
    {
        "id": "hotel_business_suite",
        "industry_id": "ind_hotel",
        "name": "Business Hotel",
        "slug": "hotel_business_suite",
        "description": "Executive corporate hotel designed for seamless business productivity, high-speed connectivity, and express services.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "hotel_business_suite",
                "primaryAccent": "#0284C7",
                "secondaryAccent": "#475569",
                "backgroundColor": "#0F172A",
                "cardBackground": "#1E293B",
                "textColor": "#F8FAFC",
                "subtextColor": "#94A3B8",
                "borderColor": "#334155",
                "heroBannerType": "business_executive"
            },
            "topics": [
                {"label": "High-Speed Wi-Fi", "icon": "💻"},
                {"label": "Ergonomic Desk", "icon": "💼"},
                {"label": "Soundproof Rooms", "icon": "🤫"},
                {"label": "Express Check-in/out", "icon": "⚡"},
                {"label": "Airport Shuttle", "icon": "🚐"},
                {"label": "24/7 Room Service", "icon": "🍽️"}
            ],
            "ratingLabels": {
                "5": {"text": "Executive Class", "emoji": "💼"},
                "4": {"text": "Very Efficient", "emoji": "✈️"},
                "3": {"text": "Good Stay", "emoji": "🙂"},
                "2": {"text": "Noisy/Slow Wi-Fi", "emoji": "😕"},
                "1": {"text": "Unprofessional", "emoji": "🚫"}
            },
            "experienceLabels": {
                "whatStoodOut": "How did the executive suite support your trip?",
                "pickMatched": "Select your business stay highlights",
                "notePlaceholder": "e.g. Perfect quiet room for Zoom meetings, super fast Wi-Fi and express breakfast."
            }
        }
    },
    {
        "id": "hotel_urban_boutique",
        "industry_id": "ind_hotel",
        "name": "Urban Boutique & Design Hotel",
        "slug": "hotel_urban_boutique",
        "description": "Design-forward urban boutique hotel with architectural framing and curated hospitality cues.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "hotel_urban_boutique",
                "primaryAccent": "#B45309",
                "secondaryAccent": "#78350F",
                "backgroundColor": "#FFFBEB",
                "cardBackground": "#FFFFFF",
                "textColor": "#451A03",
                "subtextColor": "#78350F",
                "borderColor": "#FDE68A",
                "heroBannerType": "heritage_courtyard"
            },
            "topics": [
                {"label": "Architectural Charm", "icon": "🏰"},
                {"label": "Warm Host Hospitality", "icon": "🙏"},
                {"label": "Authentic Local Dining", "icon": "🍲"},
                {"label": "Courtyard Serenity", "icon": "🌿"},
                {"label": "Heritage Antique Decor", "icon": "🗝️"}
            ],
            "ratingLabels": {
                "5": {"text": "Timeless Charm!", "emoji": "🏰"},
                "4": {"text": "Lovely Heritage", "emoji": "✨"},
                "3": {"text": "Quaint Stay", "emoji": "🙂"},
                "2": {"text": "Aged Facilities", "emoji": "😕"},
                "1": {"text": "Poor Upkeep", "emoji": "🏚️"}
            },
            "experienceLabels": {
                "whatStoodOut": "What heritage touch made your stay magical?",
                "pickMatched": "Select your boutique highlights",
                "notePlaceholder": "e.g. Stunning central courtyard, warm traditional tea and antique four-poster bed."
            }
        }
    },
    {
        "id": "hotel_cozy_inn",
        "industry_id": "ind_hotel",
        "name": "Cozy Cottage & Boutique Inn",
        "slug": "hotel_cozy_inn",
        "description": "Warm boutique inn with spotless bedding, heartfelt hospitality, and cottage comforts.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "hotel_cozy_inn",
                "primaryAccent": "#2563EB",
                "secondaryAccent": "#3B82F6",
                "backgroundColor": "#F8FAFC",
                "cardBackground": "#FFFFFF",
                "textColor": "#0F172A",
                "subtextColor": "#64748B",
                "borderColor": "#E2E8F0",
                "heroBannerType": "transit_smart"
            },
            "topics": [
                {"label": "Spotless Bedding", "icon": "🛏️"},
                {"label": "Hot Power Shower", "icon": "🚿"},
                {"label": "AC & Ventilation", "icon": "❄️"},
                {"label": "Proximity to Transit", "icon": "🚉"},
                {"label": "Secure Baggage", "icon": "🔒"}
            ],
            "ratingLabels": {
                "5": {"text": "Smart & Clean!", "emoji": "⚡"},
                "4": {"text": "Great Value", "emoji": "👍"},
                "3": {"text": "Decent Stopover", "emoji": "🙂"},
                "2": {"text": "Cramped/Noisy", "emoji": "😕"},
                "1": {"text": "Unclean/Unsafe", "emoji": "🚫"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your stopover rest?",
                "pickMatched": "Select your transit stay highlights",
                "notePlaceholder": "e.g. Seamless late-night check-in, pristine white bed sheets and great AC."
            }
        }
    },
    {
        "id": "hotel_eco_retreat",
        "industry_id": "ind_hotel",
        "name": "Eco-Resort & Nature Sanctuary",
        "slug": "hotel_eco_retreat",
        "description": "Earthy nature retreat and farmstay with forest canopy textures, solar-powered warmth, and homegrown farm-to-table breakfast.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "hotel_eco_retreat",
                "primaryAccent": "#15803D",
                "secondaryAccent": "#65A30D",
                "backgroundColor": "#F0FDF4",
                "cardBackground": "#FFFFFF",
                "textColor": "#14532D",
                "subtextColor": "#166534",
                "borderColor": "#BBF7D0",
                "heroBannerType": "forest_canopy"
            },
            "topics": [
                {"label": "Farm-to-Table Meals", "icon": "🥗"},
                {"label": "Birds & Nature Walks", "icon": "🦜"},
                {"label": "Starlit Campfire", "icon": "🪵"},
                {"label": "Eco-Friendly Living", "icon": "🌱"},
                {"label": "Warm Family Host", "icon": "🏡"}
            ],
            "ratingLabels": {
                "5": {"text": "Pure Serenity!", "emoji": "🌿"},
                "4": {"text": "Loved Nature", "emoji": "🍃"},
                "3": {"text": "Peaceful Stay", "emoji": "🙂"},
                "2": {"text": "Bug Issues", "emoji": "🦟"},
                "1": {"text": "Uncomfortable", "emoji": "🌧️"}
            },
            "experienceLabels": {
                "whatStoodOut": "What connected you to nature here?",
                "pickMatched": "Select your eco-retreat highlights",
                "notePlaceholder": "e.g. Woke up to peacocks calling and enjoyed fresh organic milk and homemade parathas."
            }
        }
    },

    # ══════════════════════════════════════════════════════════════
    # 6. FITNESS & WELLNESS (G01–G05)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "fitness_iron_forge",
        "industry_id": "ind_fitness",
        "name": "Powerlifting & Iron Gym",
        "slug": "fitness_iron_forge",
        "description": "Heavyweight powerlifting and bodybuilding dungeon with raw knurled steel aesthetics, brutalist typography, and chalk plate counters.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "fitness_iron_forge",
                "primaryAccent": "#E11D48",
                "secondaryAccent": "#FB7185",
                "backgroundColor": "#09090B",
                "cardBackground": "#18181B",
                "textColor": "#FAFAFA",
                "subtextColor": "#A1A1AA",
                "borderColor": "#27272A",
                "heroBannerType": "iron_dungeon"
            },
            "topics": [
                {"label": "Heavy Barbells & Racks", "icon": "🏋️‍♂️"},
                {"label": "Calibrated Iron Plates", "icon": "⛓️"},
                {"label": "Deadlift Platforms", "icon": "🪵"},
                {"label": "Chalk Allowed", "icon": "💨"},
                {"label": "Hardcore Motivation", "icon": "🔥"},
                {"label": "Clean Locker Rooms", "icon": "🚿"}
            ],
            "ratingLabels": {
                "5": {"text": "PR Day!", "emoji": "🔥"},
                "4": {"text": "Solid Pump", "emoji": "💪"},
                "3": {"text": "Decent Lift", "emoji": "🏋️"},
                "2": {"text": "Crowded Racks", "emoji": "😤"},
                "1": {"text": "Broken Equipment", "emoji": "💀"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was the workout energy today?",
                "pickMatched": "Select your training highlights",
                "notePlaceholder": "e.g. Calibrated plates, rock solid combo racks and intense training atmosphere."
            }
        }
    },
    {
        "id": "fitness_zen_studio",
        "industry_id": "ind_fitness",
        "name": "Yoga & Meditation Sanctuary",
        "slug": "fitness_zen_studio",
        "description": "Tranquil bamboo yoga and breathwork shala with natural linen textures, singing bowl acoustics, and mindful flow pacing.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "fitness_zen_studio",
                "primaryAccent": "#059669",
                "secondaryAccent": "#10B981",
                "backgroundColor": "#F0FDF4",
                "cardBackground": "#FFFFFF",
                "textColor": "#064E3B",
                "subtextColor": "#065F46",
                "borderColor": "#A7F3D0",
                "heroBannerType": "zen_shala"
            },
            "topics": [
                {"label": "Mindful Breathwork", "icon": "🧘‍♀️"},
                {"label": "Vinyasa Flow", "icon": "✨"},
                {"label": "Sound Healing Bowls", "icon": "🔔"},
                {"label": "Supportive Teacher", "icon": "🌸"},
                {"label": "Natural Sunlight", "icon": "☀️"},
                {"label": "Calming Incense", "icon": "🕯️"}
            ],
            "ratingLabels": {
                "5": {"text": "Blissful Peace", "emoji": "🧘"},
                "4": {"text": "Centered & Grounded", "emoji": "🌿"},
                "3": {"text": "Good Practice", "emoji": "✨"},
                "2": {"text": "Distracting Noise", "emoji": "😕"},
                "1": {"text": "Rushed Session", "emoji": "😞"}
            },
            "experienceLabels": {
                "whatStoodOut": "How did your mindfulness practice feel today?",
                "pickMatched": "Select your yoga & sound highlights",
                "notePlaceholder": "e.g. The sound bath and restorative yin flow completely melted away my stress."
            }
        }
    },
    {
        "id": "fitness_modern_club",
        "industry_id": "ind_fitness",
        "name": "Modern Athletic & Luxury Club",
        "slug": "fitness_modern_club",
        "description": "Luxury athletic performance club with sleek architectural surfaces, studio classes, and recovery lounge highlights.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "fitness_modern_club",
                "primaryAccent": "#F97316",
                "secondaryAccent": "#EAB308",
                "backgroundColor": "#0F172A",
                "cardBackground": "#1E293B",
                "textColor": "#F8FAFC",
                "subtextColor": "#94A3B8",
                "borderColor": "#334155",
                "heroBannerType": "crossfit_arena"
            },
            "topics": [
                {"label": "Killer WOD", "icon": "⏱️"},
                {"label": "Coaching Cues", "icon": "📢"},
                {"label": "Rogue Equipment", "icon": "🏋️"},
                {"label": "Community Vibe", "icon": "🤝"},
                {"label": "Olympic Lifting", "icon": "⚡"},
                {"label": "Mobility Warmup", "icon": "🤸"}
            ],
            "ratingLabels": {
                "5": {"text": "Crushed the WOD!", "emoji": "🏆"},
                "4": {"text": "Great Sweat", "emoji": "⚡"},
                "3": {"text": "Tough Workout", "emoji": "💪"},
                "2": {"text": "Poor Scaling", "emoji": "😕"},
                "1": {"text": "Unsafe Coaching", "emoji": "⚠️"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was the team energy during the workout?",
                "pickMatched": "Select your CrossFit highlights",
                "notePlaceholder": "e.g. Excellent barbell form feedback from the coach and great partner WOD."
            }
        }
    },
    {
        "id": "fitness_combat_ring",
        "industry_id": "ind_fitness",
        "name": "Boxing, MMA & Combat Arena",
        "slug": "fitness_combat_ring",
        "description": "High-octane boxing and combat training gym with intense ring contrast, round-bell badges, and coach focus.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "fitness_combat_ring",
                "primaryAccent": "#3B82F6",
                "secondaryAccent": "#60A5FA",
                "backgroundColor": "#F8FAFC",
                "cardBackground": "#FFFFFF",
                "textColor": "#0F172A",
                "subtextColor": "#475569",
                "borderColor": "#CBD5E1",
                "heroBannerType": "pt_suite"
            },
            "topics": [
                {"label": "Customized Workout", "icon": "📋"},
                {"label": "Trainer Dedication", "icon": "🤝"},
                {"label": "Form Correction", "icon": "🎯"},
                {"label": "Nutrition Guidance", "icon": "🥗"},
                {"label": "Private Gym Pod", "icon": "🔒"},
                {"label": "Measurable Results", "icon": "📈"}
            ],
            "ratingLabels": {
                "5": {"text": "Game Changer!", "emoji": "🎯"},
                "4": {"text": "Very Attentive", "emoji": "💪"},
                "3": {"text": "Good Session", "emoji": "👍"},
                "2": {"text": "Distracted Trainer", "emoji": "📱"},
                "1": {"text": "Unprofessional", "emoji": "🚫"}
            },
            "experienceLabels": {
                "whatStoodOut": "How did your personal coach elevate your session?",
                "pickMatched": "Select your 1-on-1 coaching highlights",
                "notePlaceholder": "e.g. Trainer kept me accountable on form and designed a program matched to my goals."
            }
        }
    },
    {
        "id": "fitness_athletic_turf",
        "industry_id": "ind_fitness",
        "name": "Athletic Track, CrossFit & Outdoor Turf",
        "slug": "fitness_athletic_turf",
        "description": "Sprint turf and conditioning arena with bold field lines, agility metrics, and dynamic coaching feedback.",
        "version": "1.0.0",
        "status": "active",
        "pub_status": "published",
        "config": {
            "theme": {
                "variant": "fitness_athletic_turf",
                "primaryAccent": "#EC4899",
                "secondaryAccent": "#F472B6",
                "backgroundColor": "#FDF2F8",
                "cardBackground": "#FFFFFF",
                "textColor": "#831843",
                "subtextColor": "#9D174D",
                "borderColor": "#FBCFE8",
                "heroBannerType": "pilates_reformer"
            },
            "topics": [
                {"label": "Reformer Machine Flow", "icon": "🩰"},
                {"label": "Core Burn", "icon": "🔥"},
                {"label": "Rhythm & Music", "icon": "🎵"},
                {"label": "Instructor Energy", "icon": "✨"},
                {"label": "Posture Alignment", "icon": "📐"},
                {"label": "Maple Studio Vibe", "icon": "🪞"}
            ],
            "ratingLabels": {
                "5": {"text": "Felt the Burn!", "emoji": "🩰"},
                "4": {"text": "Great Flow", "emoji": "💖"},
                "3": {"text": "Good Movement", "emoji": "✨"},
                "2": {"text": "Crowded Reformers", "emoji": "🫤"},
                "1": {"text": "Disorganized", "emoji": "💔"}
            },
            "experienceLabels": {
                "whatStoodOut": "How was your reformer or dance movement today?",
                "pickMatched": "Select your Pilates & movement highlights",
                "notePlaceholder": "e.g. Intense reformer core workout with uplifting music and motivating instructor."
            }
        }
    }
]

def migrate_30_templates(db_path: Path):
    if not db_path.exists():
        print(f"[Error] Target DB not found: {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    now = time.time()

    print(f"[Info] Connected to database: {db_path}")

    # 1. Seed all 6 Canonical Industries
    for ind in CANONICAL_INDUSTRIES:
        cur.execute("""
            INSERT INTO industries (id, name, slug, description, icon, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                slug = excluded.slug,
                description = excluded.description,
                icon = excluded.icon,
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (ind["id"], ind["name"], ind["slug"], ind["description"], ind["icon"], ind["status"], now, now))
    print(f"[Success] Upserted {len(CANONICAL_INDUSTRIES)} canonical industries.")

    # 2. Seed all 30 Canonical Templates + Versions
    seeded_count = 0
    for tpl in CANONICAL_30_TEMPLATES:
        cur.execute("""
            INSERT INTO templates (id, industry_id, name, slug, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                industry_id = excluded.industry_id,
                name = excluded.name,
                slug = excluded.slug,
                description = excluded.description,
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (tpl["id"], tpl["industry_id"], tpl["name"], tpl["slug"], tpl["description"], tpl["status"], now, now))

        ver_id = f"ver_{tpl['slug']}_{tpl['version'].replace('.', '_')}"
        cfg_json = json.dumps(tpl["config"])

        cur.execute("""
            INSERT INTO template_versions (
                id, template_id, version, configuration_json, schema_version, publication_status, published_at, created_at, created_by
            ) VALUES (?, ?, ?, ?, '1.0', ?, ?, ?, 'system')
            ON CONFLICT(id) DO UPDATE SET
                configuration_json = excluded.configuration_json,
                publication_status = excluded.publication_status,
                published_at = excluded.published_at
        """, (ver_id, tpl["id"], tpl["version"], cfg_json, tpl["pub_status"], now if tpl["pub_status"] == 'published' else None, now))
        seeded_count += 1

    conn.commit()
    print(f"[Success] Upserted {seeded_count} canonical templates and versions.")

    # Check total counts
    total_ind = cur.execute("SELECT count(*) FROM industries").fetchone()[0]
    total_tpl = cur.execute("SELECT count(*) FROM templates").fetchone()[0]
    total_ver = cur.execute("SELECT count(*) FROM template_versions").fetchone()[0]
    print(f"[Verification] Staging Database totals: Industries={total_ind}, Templates={total_tpl}, Versions={total_ver}")

    conn.close()
    return True

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (repo_root / "Project_Files" / "Data" / "nasta-ghar" / "reviews_staging.sqlite3")
    success = migrate_30_templates(target)
    sys.exit(0 if success else 1)
