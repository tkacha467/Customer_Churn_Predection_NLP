"""
VRAJA AI — Product A Canonical Industry Registry & Configuration Resolver
Single authoritative source of truth for industry classifications, subcategories,
terminology, default aspect topics, and capability flags across Product A.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

INDUSTRY_CONFIG_VERSION = "1.0.0"


@dataclass
class Terminology:
    customer_noun_singular: str
    customer_noun_plural: str
    touchpoint_noun: str
    touchpoint_placeholder: str
    disclaimer_noun: str
    private_feedback_title: str


@dataclass
class IndustryDefinition:
    industry_id: str
    display_name: str
    description: str
    subcategories: List[str]
    default_subcategory: str
    terminology: Terminology
    default_topics: List[str]
    default_negative_aspects: List[str]
    prompt_context: str
    available_features: List[str] = field(default_factory=lambda: [
        "review_acceleration",
        "private_feedback",
        "analytics",
        "custom_aspects"
    ])
    analytics_labels: Dict[str, str] = field(default_factory=dict)
    configuration_version: str = INDUSTRY_CONFIG_VERSION
    is_available: bool = True
    is_restricted: bool = False
    restriction_notice: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


# Canonical Industry Registry
CANONICAL_INDUSTRIES: Dict[str, IndustryDefinition] = {
    "restaurant": IndustryDefinition(
        industry_id="restaurant",
        display_name="Restaurants & Dining",
        description="Restaurants, cafes, bakeries, bars, and food service businesses",
        subcategories=[
            "Breakfast & Snacks",
            "Casual Dining",
            "Fine Dining",
            "Cafe & Coffee House",
            "Fast Food & QSR",
            "Bakery & Desserts",
            "Bar & Lounge"
        ],
        default_subcategory="Casual Dining",
        terminology=Terminology(
            customer_noun_singular="Diner",
            customer_noun_plural="Diners",
            touchpoint_noun="Table / Counter",
            touchpoint_placeholder="Table 4 / Takeaway",
            disclaimer_noun="dining footfall",
            private_feedback_title="Direct Diner Feedback"
        ),
        default_topics=[
            "Food Quality",
            "Taste & Flavour",
            "Service Speed",
            "Staff Hospitality",
            "Cleanliness",
            "Ambiance & Seating",
            "Value for Money"
        ],
        default_negative_aspects=[
            "Long Wait Time",
            "Food Temperature",
            "Order Mix-up",
            "Noise Level",
            "Billing Discrepancy"
        ],
        prompt_context="dining, food quality, taste, and hospitality experience",
        analytics_labels={
            "aspect_performance": "Culinary & Service Aspects",
            "touchpoint_title": "Table & Dining Area Distribution"
        }
    ),
    "hotel": IndustryDefinition(
        industry_id="hotel",
        display_name="Hotels & Hospitality",
        description="Hotels, resorts, guest houses, and boutique accommodations",
        subcategories=[
            "Boutique Hotel",
            "Business Hotel",
            "Luxury Resort",
            "Homestay & B&B",
            "Budget Hotel"
        ],
        default_subcategory="Boutique Hotel",
        terminology=Terminology(
            customer_noun_singular="Guest",
            customer_noun_plural="Guests",
            touchpoint_noun="Room / Front Desk",
            touchpoint_placeholder="Room 302 / Reception",
            disclaimer_noun="guest room occupancy",
            private_feedback_title="Guest Relations & Feedback"
        ),
        default_topics=[
            "Room Cleanliness",
            "Check-in Experience",
            "Bed Comfort",
            "Staff Hospitality",
            "Breakfast & Dining",
            "Amenities & Wi-Fi",
            "Quiet & Restful Stay"
        ],
        default_negative_aspects=[
            "Room Noise",
            "Slow Check-in",
            "AC / Heating Issue",
            "Plumbing / Water Pressure",
            "Housekeeping Delay"
        ],
        prompt_context="hotel stay, room comfort, cleanliness, and guest hospitality",
        analytics_labels={
            "aspect_performance": "Hospitality & Facility Aspects",
            "touchpoint_title": "Room & Floor Distribution"
        }
    ),
    "fitness": IndustryDefinition(
        industry_id="fitness",
        display_name="Gyms & Fitness Centers",
        description="Fitness clubs, strength gyms, yoga studios, and athletic centers",
        subcategories=[
            "Strength & Conditioning Gym",
            "CrossFit Box",
            "Yoga & Pilates Studio",
            "MMA & Combat Gym",
            "Health & Wellness Club"
        ],
        default_subcategory="Strength & Conditioning Gym",
        terminology=Terminology(
            customer_noun_singular="Member",
            customer_noun_plural="Members",
            touchpoint_noun="Zone / Floor",
            touchpoint_placeholder="Cardio Zone / Front Desk",
            disclaimer_noun="gym member check-ins",
            private_feedback_title="Member Experience & Equipment Feedback"
        ),
        default_topics=[
            "Equipment Variety & Quality",
            "Trainer Guidance",
            "Gym Cleanliness",
            "Locker Rooms & Showers",
            "Atmosphere & Music",
            "Crowd Management",
            "Membership Value"
        ],
        default_negative_aspects=[
            "Broken Equipment",
            "Overcrowding",
            "Trainer Unavailability",
            "Locker Cleanliness",
            "Air Conditioning"
        ],
        prompt_context="workout, equipment condition, trainer guidance, and fitness environment",
        analytics_labels={
            "aspect_performance": "Fitness & Facility Aspects",
            "touchpoint_title": "Zone & Floor Distribution"
        }
    ),
    "salon": IndustryDefinition(
        industry_id="salon",
        display_name="Salons & Wellness Spas",
        description="Hair salons, beauty parlors, nail bars, and luxury spas",
        subcategories=[
            "Hair & Beauty Salon",
            "Luxury Day Spa",
            "Barber Shop & Grooming",
            "Nail Studio",
            "Skincare & Esthetics"
        ],
        default_subcategory="Hair & Beauty Salon",
        terminology=Terminology(
            customer_noun_singular="Client",
            customer_noun_plural="Clients",
            touchpoint_noun="Station / Room",
            touchpoint_placeholder="Station 3 / Spa Room B",
            disclaimer_noun="salon appointment volume",
            private_feedback_title="Client Care & Service Feedback"
        ),
        default_topics=[
            "Stylist & Therapist Skill",
            "Hygiene & Sanitization",
            "Relaxing Ambience",
            "Service Timeliness",
            "Product Quality",
            "Personal Consultation",
            "Value for Money"
        ],
        default_negative_aspects=[
            "Long Waiting Time",
            "Rushed Service",
            "Result Discrepancy",
            "Pricing Transparency",
            "Cleanliness Concern"
        ],
        prompt_context="styling, grooming, spa relaxation, and personal care experience",
        analytics_labels={
            "aspect_performance": "Stylist & Spa Aspects",
            "touchpoint_title": "Station & Treatment Room Distribution"
        }
    ),
    "retail": IndustryDefinition(
        industry_id="retail",
        display_name="Retail Stores & Shopping",
        description="Boutiques, grocery stores, apparel, and specialty retail shops",
        subcategories=[
            "Fashion & Apparel",
            "Electronics & Appliances",
            "Supermarket & Gourmet Grocery",
            "Home Decor & Furniture",
            "Jewelry & Luxury Accessories"
        ],
        default_subcategory="Fashion & Apparel",
        terminology=Terminology(
            customer_noun_singular="Shopper",
            customer_noun_plural="Shoppers",
            touchpoint_noun="Counter / Department",
            touchpoint_placeholder="Billing Counter 1 / Menswear",
            disclaimer_noun="in-store retail footfall",
            private_feedback_title="Shopper Notes & Store Feedback"
        ),
        default_topics=[
            "Product Selection & Variety",
            "Staff Helpfulness",
            "Store Cleanliness & Layout",
            "Billing Speed & Checkout",
            "Fair Pricing & Offers",
            "Return & Exchange Ease"
        ],
        default_negative_aspects=[
            "Billing Queue",
            "Item Out of Stock",
            "Unhelpful Staff",
            "Cluttered Aisles",
            "Pricing Discrepancy"
        ],
        prompt_context="in-store shopping, product selection, and checkout experience",
        analytics_labels={
            "aspect_performance": "Retail & Shopping Aspects",
            "touchpoint_title": "Department & Counter Distribution"
        }
    ),
    "automotive": IndustryDefinition(
        industry_id="automotive",
        display_name="Automotive Sales & Service",
        description="Car dealerships, service workshops, detailing studios, and tyre centers",
        subcategories=[
            "Automotive Service Workshop",
            "Car & Two-Wheeler Dealership",
            "Auto Detailing & Ceramic Studio",
            "Tyre & Alignment Center"
        ],
        default_subcategory="Automotive Service Workshop",
        terminology=Terminology(
            customer_noun_singular="Vehicle Owner",
            customer_noun_plural="Vehicle Owners",
            touchpoint_noun="Service Bay / Desk",
            touchpoint_placeholder="Service Bay 2 / Reception",
            disclaimer_noun="workshop vehicle service visits",
            private_feedback_title="Service Quality & Vehicle Feedback"
        ),
        default_topics=[
            "Repair & Workmanship Quality",
            "Turnaround Time",
            "Transparent Estimate & Billing",
            "Advisor Professionalism",
            "Facility Cleanliness & Lounge",
            "Vehicle Handover Inspection"
        ],
        default_negative_aspects=[
            "Delivery Delay",
            "Unexpected Charges",
            "Unresolved Vehicle Issue",
            "Poor Communication",
            "Cleanliness on Delivery"
        ],
        prompt_context="vehicle repair, maintenance quality, and service advisor experience",
        analytics_labels={
            "aspect_performance": "Workshop & Service Aspects",
            "touchpoint_title": "Service Bay & Job Card Distribution"
        }
    ),
    "education": IndustryDefinition(
        industry_id="education",
        display_name="Education & Coaching",
        description="Coaching academies, tutoring centers, test prep, and training institutes",
        subcategories=[
            "Competitive Exam Coaching",
            "K-12 Tutoring Center",
            "Language Academy",
            "Music & Performing Arts",
            "Skill Development & Tech Academy"
        ],
        default_subcategory="Competitive Exam Coaching",
        terminology=Terminology(
            customer_noun_singular="Student / Parent",
            customer_noun_plural="Students & Parents",
            touchpoint_noun="Batch / Center",
            touchpoint_placeholder="Batch A-1 / Academic Desk",
            disclaimer_noun="academy student enrollment",
            private_feedback_title="Student & Parent Academic Feedback"
        ),
        default_topics=[
            "Faculty Expertise & Teaching",
            "Doubt Resolution Support",
            "Study Material Quality",
            "Classroom Infrastructure",
            "Student Progress Tracking",
            "Administrative Courtesy"
        ],
        default_negative_aspects=[
            "Doubt Clearing Delay",
            "Fast Syllabus Pace",
            "Crowded Classrooms",
            "Poor Communication",
            "Scheduling Conflict"
        ],
        prompt_context="classroom teaching, faculty support, and learning environment",
        analytics_labels={
            "aspect_performance": "Academic & Facility Aspects",
            "touchpoint_title": "Batch & Classroom Distribution"
        }
    ),
    "events": IndustryDefinition(
        industry_id="events",
        display_name="Event Venues & Banquets",
        description="Banquet halls, wedding lawns, conference facilities, and party spaces",
        subcategories=[
            "Banquet & Wedding Hall",
            "Open Air Lawn & Resort",
            "Corporate Conference Center",
            "Party Hall & Club Space"
        ],
        default_subcategory="Banquet & Wedding Hall",
        terminology=Terminology(
            customer_noun_singular="Event Host / Guest",
            customer_noun_plural="Hosts & Guests",
            touchpoint_noun="Hall / Lawn",
            touchpoint_placeholder="Grand Hall / Lawn B",
            disclaimer_noun="venue event bookings",
            private_feedback_title="Event Host & Organizer Feedback"
        ),
        default_topics=[
            "Venue Ambience & Decor",
            "Event Coordination & Management",
            "Catering & Food Quality",
            "Sound, Lighting & AV Setup",
            "Valet & Parking Convenience",
            "Cleanliness & Restrooms"
        ],
        default_negative_aspects=[
            "AC / Climate Issue",
            "Audio Failure",
            "Catering Delay",
            "Parking Congestion",
            "Staff Unpunctuality"
        ],
        prompt_context="event hosting, venue decor, hospitality, and event coordination",
        analytics_labels={
            "aspect_performance": "Venue & Event Aspects",
            "touchpoint_title": "Hall & Zone Distribution"
        }
    ),
    "travel": IndustryDefinition(
        industry_id="travel",
        display_name="Travel & Tourism",
        description="Tour operators, travel agencies, adventure guides, and rental services",
        subcategories=[
            "Holiday Tour Operator",
            "Travel & Visa Agency",
            "Adventure & Trekking Outfitter",
            "Vehicle Rental & Chauffeur"
        ],
        default_subcategory="Holiday Tour Operator",
        terminology=Terminology(
            customer_noun_singular="Traveler",
            customer_noun_plural="Travelers",
            touchpoint_noun="Booking / Tour",
            touchpoint_placeholder="Booking Ref / Tour Desk",
            disclaimer_noun="traveler bookings and tours",
            private_feedback_title="Traveler Care & Trip Feedback"
        ),
        default_topics=[
            "Itinerary Execution & Planning",
            "Tour Guide Knowledge",
            "Vehicle & Transport Comfort",
            "Hotel & Stay Arrangements",
            "Communication & Promptness",
            "Safety & Care"
        ],
        default_negative_aspects=[
            "Itinerary Delay",
            "Subpar Vehicle",
            "Unclear Communication",
            "Hotel Mismatch",
            "Hidden Charges"
        ],
        prompt_context="travel itinerary, tour guidance, and trip coordination experience",
        analytics_labels={
            "aspect_performance": "Travel & Tour Aspects",
            "touchpoint_title": "Tour & Booking Distribution"
        }
    ),
    "healthcare": IndustryDefinition(
        industry_id="healthcare",
        display_name="Clinics & Healthcare Practices (Restricted)",
        description="Clinics, dental practices, physiotherapy, and healthcare centers (Compliance Gated)",
        subcategories=[
            "Dental Clinic",
            "Eye Care & Optometry",
            "Physiotherapy & Rehab",
            "Pediatric Practice",
            "Dermatology Practice"
        ],
        default_subcategory="Dental Clinic",
        terminology=Terminology(
            customer_noun_singular="Patient",
            customer_noun_plural="Patients",
            touchpoint_noun="Cabin / Counter",
            touchpoint_placeholder="Cabin 2 / Reception",
            disclaimer_noun="clinic patient consultations",
            private_feedback_title="Patient Experience & Service Notes"
        ),
        default_topics=[
            "Doctor Demeanor & Empathy",
            "Waiting Time Management",
            "Clinic Cleanliness & Hygiene",
            "Staff Courteousness",
            "Appointment Booking Ease",
            "Clear Explanations"
        ],
        default_negative_aspects=[
            "Extended Waiting Time",
            "Rude Reception Staff",
            "Appointment Delay",
            "Cleanliness Issue",
            "Billing Lack of Transparency"
        ],
        prompt_context="administrative service, clinic cleanliness, and appointment experience",
        is_available=False,
        is_restricted=True,
        restriction_notice="Healthcare onboarding is disabled in production pending regulatory compliance and privacy review."
    )
}

# Explicit Unclassified Industry Definition (Unknown industries must never silently become restaurants)
UNCLASSIFIED_INDUSTRY = IndustryDefinition(
    industry_id="unclassified",
    display_name="Unclassified Business",
    description="General business and customer service establishment",
    subcategories=["General Business"],
    default_subcategory="General Business",
    terminology=Terminology(
        customer_noun_singular="Customer",
        customer_noun_plural="Customers",
        touchpoint_noun="Location / Counter",
        touchpoint_placeholder="Front Counter / Service Point",
        disclaimer_noun="physical customer visits",
        private_feedback_title="Customer Feedback & Notes"
    ),
    default_topics=[
        "Service Quality",
        "Staff Helpfulness",
        "Promptness & Timeliness",
        "Cleanliness & Organization",
        "Value for Money",
        "Overall Experience"
    ],
    default_negative_aspects=[
        "Waiting Time",
        "Staff Attitude",
        "Service Quality",
        "Pricing Transparency",
        "Communication"
    ],
    prompt_context="general customer service and business visit experience",
    analytics_labels={
        "aspect_performance": "Service & Experience Aspects",
        "touchpoint_title": "Touchpoint Distribution"
    }
)

CANONICAL_INDUSTRIES["unclassified"] = UNCLASSIFIED_INDUSTRY

# Verified Legacy Category Mapping (Specific to known product baselines)
LEGACY_CATEGORY_MAP: Dict[str, str] = {
    # Restaurant & Dining keywords
    "breakfast & snacks": "restaurant",
    "casual dining": "restaurant",
    "fine dining": "restaurant",
    "cafe": "restaurant",
    "cafe & bakery": "restaurant",
    "coffee house": "restaurant",
    "fast food": "restaurant",
    "qsr": "restaurant",
    "bakery": "restaurant",
    "restaurant": "restaurant",
    "bar": "restaurant",
    "lounge": "restaurant",
    # Hotel keywords
    "hotel": "hotel",
    "resort": "hotel",
    "boutique hotel": "hotel",
    "homestay": "hotel",
    "guest house": "hotel",
    # Fitness keywords
    "gym": "fitness",
    "fitness": "fitness",
    "fitness club": "fitness",
    "crossfit": "fitness",
    "yoga": "fitness",
    "pilates": "fitness",
    # Salon & Spa keywords
    "salon": "salon",
    "spa": "salon",
    "beauty parlor": "salon",
    "barber": "salon",
    "nail studio": "salon",
    # Retail keywords
    "retail": "retail",
    "store": "retail",
    "supermarket": "retail",
    "boutique": "retail",
    "shop": "retail",
    # Automotive keywords
    "automotive": "automotive",
    "workshop": "automotive",
    "car dealer": "automotive",
    "detailing": "automotive",
    "auto repair": "automotive",
    "auto": "automotive",
    "mechanic": "automotive",
    "car repair": "automotive",
    # Education keywords
    "coaching": "education",
    "academy": "education",
    "tutoring": "education",
    "institute": "education",
    # Events keywords
    "banquet": "events",
    "wedding hall": "events",
    "event venue": "events",
    # Travel keywords
    "travel": "travel",
    "tour": "travel",
    "tourism": "travel",
    # Healthcare keywords (Restricted)
    "clinic": "healthcare",
    "hospital": "healthcare",
    "dental": "healthcare",
    "physiotherapy": "healthcare",
    "healthcare": "healthcare",
}

# Authoritative Aliases
INDUSTRY_REGISTRY: Dict[str, IndustryDefinition] = CANONICAL_INDUSTRIES
ACTIVE_INDUSTRIES: List[str] = [k for k, v in CANONICAL_INDUSTRIES.items() if not v.is_restricted]
DEFAULT_PLATFORM_TOPICS: List[str] = UNCLASSIFIED_INDUSTRY.default_topics


def resolve_industry(
    category: Optional[str] = None,
    explicit_industry_id: Optional[str] = None,
    industry_id: Optional[str] = None,
) -> IndustryDefinition:
    """
    Resolves the canonical IndustryDefinition adhering strictly to priority:
    1. Explicit tenant industry configuration (highest precedence):
       - If valid and registered, return that canonical industry.
       - If invalid non-empty explicit ID, return UNCLASSIFIED_INDUSTRY (never silently fall through to category).
    2. Missing explicit industry ID:
       - Use verified legacy category mapping (exact match or keyword match).
       - If category is unknown or missing, return UNCLASSIFIED_INDUSTRY.
    3. Unknown legacy category:
       - Explicit unclassified state (NEVER silently fall back to restaurant).
    """
    chosen_id = explicit_industry_id or industry_id
    # 1. Explicit tenant industry ID takes precedence
    if chosen_id is not None and str(chosen_id).strip():
        norm_id = str(chosen_id).strip().lower()
        if norm_id in CANONICAL_INDUSTRIES:
            return CANONICAL_INDUSTRIES[norm_id]
        return UNCLASSIFIED_INDUSTRY

    # 2. Legacy category mapping (compatibility fallback only when explicit industry is absent)
    if category is not None and str(category).strip():
        norm_cat = str(category).strip().lower()
        # Direct exact match
        if norm_cat in LEGACY_CATEGORY_MAP:
            target_id = LEGACY_CATEGORY_MAP[norm_cat]
            if target_id in CANONICAL_INDUSTRIES:
                return CANONICAL_INDUSTRIES[target_id]

        # Word boundary lookup for verified category terms
        import re
        for keyword, ind_id in LEGACY_CATEGORY_MAP.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", norm_cat):
                if ind_id in CANONICAL_INDUSTRIES:
                    return CANONICAL_INDUSTRIES[ind_id]

    # 3. Explicit Unclassified fallback
    return UNCLASSIFIED_INDUSTRY


def resolve_effective_topics(
    tenant_topics: Optional[List[str]],
    industry_id: str
) -> List[str]:
    """
    Resolves the authoritative topic list enforcing strict precedence:
    Tenant Custom Topics -> Industry Defaults -> Platform Fallbacks
    """
    if tenant_topics and isinstance(tenant_topics, list) and len(tenant_topics) > 0:
        cleaned = [str(t).strip() for t in tenant_topics if str(t).strip()]
        if cleaned:
            return cleaned

    ind = CANONICAL_INDUSTRIES.get(industry_id, UNCLASSIFIED_INDUSTRY)
    return list(ind.default_topics)


def get_available_industries() -> List[Dict[str, Any]]:
    """
    Returns list of active, non-restricted industries available for tenant onboarding and owner portal selection.
    Restricted industries (such as healthcare) are excluded from production onboarding.
    """
    return [
        {
            "industry_id": ind.industry_id,
            "display_name": ind.display_name,
            "description": ind.description,
            "subcategories": ind.subcategories,
            "default_subcategory": ind.default_subcategory,
            "default_topics": ind.default_topics,
            "touchpoint_noun": ind.terminology.touchpoint_noun,
            "touchpoint_placeholder": ind.terminology.touchpoint_placeholder,
        }
        for ind in CANONICAL_INDUSTRIES.values()
        if ind.is_available and not ind.is_restricted and ind.industry_id != "unclassified"
    ]


def get_all_industries_metadata() -> List[Dict[str, Any]]:
    """Returns complete metadata for all registered industries including restricted ones."""
    res = []
    for ind in CANONICAL_INDUSTRIES.values():
        d = ind.to_dict()
        res.append(d)
    return res


class IndustryRegistry:
    """Canonical registry wrapper for industry resolution."""
    CANONICAL_INDUSTRIES = CANONICAL_INDUSTRIES
    get_available_industries = staticmethod(get_available_industries)
    get_all_industries_metadata = staticmethod(get_all_industries_metadata)
    resolve_industry = staticmethod(resolve_industry)
    resolve_effective_topics = staticmethod(resolve_effective_topics)
