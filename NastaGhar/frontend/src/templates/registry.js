import FallbackTemplate from './FallbackTemplate';

// ── Restaurant / Food & Dining (F01–F05) ──
import RestaurantClassicBistro from './restaurant/RestaurantClassicBistro';
import RestaurantModernUrban from './restaurant/RestaurantModernUrban';
import RestaurantLuxuryDining from './restaurant/RestaurantLuxuryDining';
import RestaurantCafePlayful from './restaurant/RestaurantCafePlayful';
import RestaurantSweetDessert from './restaurant/RestaurantSweetDessert';

// ── Beauty & Grooming (B01–B05) ──
import SalonSpaSanctuary from './beauty/SalonSpaSanctuary';
import BarberGroomingLounge from './beauty/BarberGroomingLounge';
import NailLashStudio from './beauty/NailLashStudio';
import SkincareAestheticLab from './beauty/SkincareAestheticLab';
import BridalGlamStudio from './beauty/BridalGlamStudio';
import SalonWellness from './beauty/SalonWellness'; // fallback

// ── Retail & Shopping (R01–R05) ──
import RetailFashionBoutique from './retail/RetailFashionBoutique';
import RetailStreetwearDrop from './retail/RetailStreetwearDrop';
import RetailArtisanalHome from './retail/RetailArtisanalHome';
import RetailOrganicPantry from './retail/RetailOrganicPantry';
import RetailTechGadgets from './retail/RetailTechGadgets';
import RetailBoutique from './retail/RetailBoutique'; // fallback

// ── Hotels & Hospitality (T01–T05) ──
import HotelHeritageResort from './hospitality/HotelHeritageResort';
import HotelUrbanBoutique from './hospitality/HotelUrbanBoutique';
import HotelEcoRetreat from './hospitality/HotelEcoRetreat';
import HotelBusinessSuite from './hospitality/HotelBusinessSuite';
import HotelCozyInn from './hospitality/HotelCozyInn';
import HotelHospitality from './hospitality/HotelHospitality'; // fallback

// ── Fitness & Wellness (G01–G05) ──
import FitnessIronForge from './fitness/FitnessIronForge';
import FitnessZenStudio from './fitness/FitnessZenStudio';
import FitnessModernClub from './fitness/FitnessModernClub';
import FitnessCombatRing from './fitness/FitnessCombatRing';
import FitnessAthleticTurf from './fitness/FitnessAthleticTurf';
import FitnessEnergy from './fitness/FitnessEnergy'; // fallback

// ── Healthcare & Clinical (H01–H05 - Quarantined Preview-Only) ──
import ClinicMultiSpecialty from './healthcare/ClinicMultiSpecialty';
import ClinicDentalStudio from './healthcare/ClinicDentalStudio';
import ClinicPhysioRehab from './healthcare/ClinicPhysioRehab';
import ClinicWellnessPreventive from './healthcare/ClinicWellnessPreventive';
import ClinicDiagnosticLab from './healthcare/ClinicDiagnosticLab';
import HealthcareCompliance from './healthcare/HealthcareCompliance'; // fallback

/**
 * MASTER TEMPLATE REGISTRY
 * Maps template slugs, IDs, and industry identifiers to approved visual renderers.
 * Exactly 30 distinct visual components across 6 canonical industries (5 per industry).
 */
export const TEMPLATE_REGISTRY = {
  // ══════════════════════════════════════════════════════════════
  // FOOD & DINING (F01–F05)
  // ══════════════════════════════════════════════════════════════
  'restaurant_classic_bistro': {
    name: 'Classic Bistro',
    industry: 'restaurant',
    component: RestaurantClassicBistro,
    deployable: true,
  },
  'restaurant_classic': {
    name: 'Classic Bistro',
    industry: 'restaurant',
    component: RestaurantClassicBistro,
    deployable: true,
  },
  'tpl_restaurant_classic': {
    name: 'Classic Bistro',
    industry: 'restaurant',
    component: RestaurantClassicBistro,
    deployable: true,
  },
  'restaurant_modern_urban': {
    name: 'Modern Urban',
    industry: 'restaurant',
    component: RestaurantModernUrban,
    deployable: true,
  },
  'tpl_restaurant_modern_urban': {
    name: 'Modern Urban',
    industry: 'restaurant',
    component: RestaurantModernUrban,
    deployable: true,
  },
  'restaurant_luxury_dining': {
    name: 'Luxury Dining',
    industry: 'restaurant',
    component: RestaurantLuxuryDining,
    deployable: true,
  },
  'tpl_restaurant_luxury_dining': {
    name: 'Luxury Dining',
    industry: 'restaurant',
    component: RestaurantLuxuryDining,
    deployable: true,
  },
  'restaurant_cafe_playful': {
    name: 'Café & Playful',
    industry: 'restaurant',
    component: RestaurantCafePlayful,
    deployable: true,
  },
  'restaurant_premium': {
    name: 'Café & Playful',
    industry: 'restaurant',
    component: RestaurantCafePlayful,
    deployable: true,
  },
  'tpl_restaurant_premium': {
    name: 'Café & Playful',
    industry: 'restaurant',
    component: RestaurantCafePlayful,
    deployable: true,
  },
  'restaurant_sweet_dessert': {
    name: 'Sweet & Dessert House',
    industry: 'restaurant',
    component: RestaurantSweetDessert,
    deployable: false, // PREVIEW_ONLY draft
    preview_only: true,
  },
  'tpl_restaurant_sweet_dessert': {
    name: 'Sweet & Dessert House',
    industry: 'restaurant',
    component: RestaurantSweetDessert,
    deployable: false,
    preview_only: true,
  },

  // ══════════════════════════════════════════════════════════════
  // BEAUTY & GROOMING (B01–B05)
  // ══════════════════════════════════════════════════════════════
  'salon_spa_sanctuary': {
    name: 'Spa & Wellness Sanctuary',
    industry: 'salon',
    component: SalonSpaSanctuary,
    deployable: true,
  },
  'tpl_salon_spa_sanctuary': {
    name: 'Spa & Wellness Sanctuary',
    industry: 'salon',
    component: SalonSpaSanctuary,
    deployable: true,
  },
  'salon_barber_lounge': {
    name: 'Grooming & Barber Lounge',
    industry: 'salon',
    component: BarberGroomingLounge,
    deployable: true,
  },
  'tpl_salon_barber_lounge': {
    name: 'Grooming & Barber Lounge',
    industry: 'salon',
    component: BarberGroomingLounge,
    deployable: true,
  },
  'salon_nail_lash': {
    name: 'Nail & Lash Artistry',
    industry: 'salon',
    component: NailLashStudio,
    deployable: true,
  },
  'tpl_salon_nail_lash': {
    name: 'Nail & Lash Artistry',
    industry: 'salon',
    component: NailLashStudio,
    deployable: true,
  },
  'salon_skincare_lab': {
    name: 'Skincare & Aesthetic Lab',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'tpl_salon_skincare_lab': {
    name: 'Skincare & Aesthetic Lab',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'salon_bridal_glam': {
    name: 'Bridal & Glam Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_bridal_glam': {
    name: 'Bridal & Glam Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'tpl_salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  // Legacy aliases
  'salon_classic': {
    name: 'Salon Studio',
    industry: 'salon',
    component: SalonSpaSanctuary,
    deployable: true,
  },
  'tpl_salon_classic': {
    name: 'Salon Studio',
    industry: 'salon',
    component: SalonSpaSanctuary,
    deployable: true,
  },
  'salon_premium': {
    name: 'Salon Sanctuary',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_premium': {
    name: 'Salon Sanctuary',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },

  // ══════════════════════════════════════════════════════════════
  // RETAIL & SHOPPING (R01–R05)
  // ══════════════════════════════════════════════════════════════
  'retail_fashion_boutique': {
    name: 'Fashion Boutique & Haute Couture',
    industry: 'retail',
    component: RetailFashionBoutique,
    deployable: true,
  },
  'tpl_retail_fashion_boutique': {
    name: 'Fashion Boutique & Haute Couture',
    industry: 'retail',
    component: RetailFashionBoutique,
    deployable: true,
  },
  'retail_streetwear_drop': {
    name: 'Streetwear & Sneaker Drop',
    industry: 'retail',
    component: RetailStreetwearDrop,
    deployable: true,
  },
  'tpl_retail_streetwear_drop': {
    name: 'Streetwear & Sneaker Drop',
    industry: 'retail',
    component: RetailStreetwearDrop,
    deployable: true,
  },
  'retail_artisanal_home': {
    name: 'Artisanal Home & Living',
    industry: 'retail',
    component: RetailArtisanalHome,
    deployable: true,
  },
  'tpl_retail_artisanal_home': {
    name: 'Artisanal Home & Living',
    industry: 'retail',
    component: RetailArtisanalHome,
    deployable: true,
  },
  'retail_organic_pantry': {
    name: 'Organic Market & Gourmet Pantry',
    industry: 'retail',
    component: RetailOrganicPantry,
    deployable: true,
  },
  'tpl_retail_organic_pantry': {
    name: 'Organic Market & Gourmet Pantry',
    industry: 'retail',
    component: RetailOrganicPantry,
    deployable: true,
  },
  'retail_tech_gadgets': {
    name: 'Electronics & Tech Haven',
    industry: 'retail',
    component: RetailTechGadgets,
    deployable: true,
  },
  'tpl_retail_tech_gadgets': {
    name: 'Electronics & Tech Haven',
    industry: 'retail',
    component: RetailTechGadgets,
    deployable: true,
  },
  'salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'tpl_salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  // Legacy aliases
  'retail_boutique': {
    name: 'Retail Boutique',
    industry: 'retail',
    component: RetailFashionBoutique,
    deployable: true,
  },
  'retail_general': {
    name: 'Retail General',
    industry: 'retail',
    component: RetailArtisanalHome,
    deployable: true,
  },

  // ══════════════════════════════════════════════════════════════
  // HOTELS & HOSPITALITY (T01–T05)
  // ══════════════════════════════════════════════════════════════
  'hotel_heritage_resort': {
    name: 'Heritage Palace & Grand Resort',
    industry: 'hotel',
    component: HotelHeritageResort,
    deployable: true,
  },
  'tpl_hotel_heritage_resort': {
    name: 'Heritage Palace & Grand Resort',
    industry: 'hotel',
    component: HotelHeritageResort,
    deployable: true,
  },
  'hotel_urban_boutique': {
    name: 'Urban Boutique & Design Hotel',
    industry: 'hotel',
    component: HotelUrbanBoutique,
    deployable: true,
  },
  'tpl_hotel_urban_boutique': {
    name: 'Urban Boutique & Design Hotel',
    industry: 'hotel',
    component: HotelUrbanBoutique,
    deployable: true,
  },
  'hotel_eco_retreat': {
    name: 'Eco-Resort & Nature Sanctuary',
    industry: 'hotel',
    component: HotelEcoRetreat,
    deployable: true,
  },
  'tpl_hotel_eco_retreat': {
    name: 'Eco-Resort & Nature Sanctuary',
    industry: 'hotel',
    component: HotelEcoRetreat,
    deployable: true,
  },
  'hotel_business_suite': {
    name: 'Executive Business Suite',
    industry: 'hotel',
    component: HotelBusinessSuite,
    deployable: true,
  },
  'tpl_hotel_business_suite': {
    name: 'Executive Business Suite',
    industry: 'hotel',
    component: HotelBusinessSuite,
    deployable: true,
  },
  'hotel_cozy_inn': {
    name: 'Cozy Homestay & Bed & Breakfast',
    industry: 'hotel',
    component: HotelCozyInn,
    deployable: true,
  },
  'tpl_hotel_cozy_inn': {
    name: 'Cozy Homestay & Bed & Breakfast',
    industry: 'hotel',
    component: HotelCozyInn,
    deployable: true,
  },
  'salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'tpl_salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  // Legacy aliases
  'hotel_classic': {
    name: 'Hotel Classic',
    industry: 'hotel',
    component: HotelHeritageResort,
    deployable: true,
  },
  'tpl_hotel_classic': {
    name: 'Hotel Classic',
    industry: 'hotel',
    component: HotelHeritageResort,
    deployable: true,
  },
  'hotel_premium': {
    name: 'Hotel Premium',
    industry: 'hotel',
    component: HotelBusinessSuite,
    deployable: true,
  },
  'tpl_hotel_premium': {
    name: 'Hotel Premium',
    industry: 'hotel',
    component: HotelBusinessSuite,
    deployable: true,
  },

  // ══════════════════════════════════════════════════════════════
  // FITNESS & WELLNESS (G01–G05)
  // ══════════════════════════════════════════════════════════════
  'fitness_iron_forge': {
    name: 'Iron Forge Strength & CrossFit',
    industry: 'fitness',
    component: FitnessIronForge,
    deployable: true,
  },
  'tpl_fitness_iron_forge': {
    name: 'Iron Forge Strength & CrossFit',
    industry: 'fitness',
    component: FitnessIronForge,
    deployable: true,
  },
  'fitness_zen_studio': {
    name: 'Zen Yoga & Mindful Studio',
    industry: 'fitness',
    component: FitnessZenStudio,
    deployable: true,
  },
  'tpl_fitness_zen_studio': {
    name: 'Zen Yoga & Mindful Studio',
    industry: 'fitness',
    component: FitnessZenStudio,
    deployable: true,
  },
  'fitness_modern_club': {
    name: 'Modern Athletic Performance Club',
    industry: 'fitness',
    component: FitnessModernClub,
    deployable: true,
  },
  'tpl_fitness_modern_club': {
    name: 'Modern Athletic Performance Club',
    industry: 'fitness',
    component: FitnessModernClub,
    deployable: true,
  },
  'fitness_combat_ring': {
    name: 'Boxing & Combat Ring',
    industry: 'fitness',
    component: FitnessCombatRing,
    deployable: true,
  },
  'tpl_fitness_combat_ring': {
    name: 'Boxing & Combat Ring',
    industry: 'fitness',
    component: FitnessCombatRing,
    deployable: true,
  },
  'fitness_athletic_turf': {
    name: 'Field Turf & Conditioning',
    industry: 'fitness',
    component: FitnessAthleticTurf,
    deployable: true,
  },
  'tpl_fitness_athletic_turf': {
    name: 'Field Turf & Conditioning',
    industry: 'fitness',
    component: FitnessAthleticTurf,
    deployable: true,
  },
  'salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'tpl_salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  // Legacy aliases
  'fitness_gym': {
    name: 'Fitness Energy',
    industry: 'fitness',
    component: FitnessIronForge,
    deployable: true,
  },

  // ══════════════════════════════════════════════════════════════
  // HEALTHCARE & CLINICAL (H01–H05) [QUARANTINED PREVIEW-ONLY]
  // ══════════════════════════════════════════════════════════════
  'clinic_multi_specialty': {
    name: 'Multi-Specialty Medical Center',
    industry: 'clinic',
    component: ClinicMultiSpecialty,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_multi_specialty': {
    name: 'Multi-Specialty Medical Center',
    industry: 'clinic',
    component: ClinicMultiSpecialty,
    deployable: false,
    preview_only: true,
  },
  'clinic_dental_studio': {
    name: 'Modern Dental Studio',
    industry: 'clinic',
    component: ClinicDentalStudio,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_dental_studio': {
    name: 'Modern Dental Studio',
    industry: 'clinic',
    component: ClinicDentalStudio,
    deployable: false,
    preview_only: true,
  },
  'clinic_physio_rehab': {
    name: 'Physiotherapy & Rehab Clinic',
    industry: 'clinic',
    component: ClinicPhysioRehab,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_physio_rehab': {
    name: 'Physiotherapy & Rehab Clinic',
    industry: 'clinic',
    component: ClinicPhysioRehab,
    deployable: false,
    preview_only: true,
  },
  'clinic_wellness_preventive': {
    name: 'Preventive Wellness & Longevity',
    industry: 'clinic',
    component: ClinicWellnessPreventive,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_wellness_preventive': {
    name: 'Preventive Wellness & Longevity',
    industry: 'clinic',
    component: ClinicWellnessPreventive,
    deployable: false,
    preview_only: true,
  },
  'clinic_diagnostic_lab': {
    name: 'Diagnostics & Pathology Lab',
    industry: 'clinic',
    component: ClinicDiagnosticLab,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_diagnostic_lab': {
    name: 'Diagnostics & Pathology Lab',
    industry: 'clinic',
    component: ClinicDiagnosticLab,
    deployable: false,
    preview_only: true,
  },
  'salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'tpl_salon_hair_modern': {
    name: 'Modern Hair Salon',
    industry: 'salon',
    component: SkincareAestheticLab,
    deployable: true,
  },
  'salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  'tpl_salon_beauty_makeup': {
    name: 'Beauty & Makeup Studio',
    industry: 'salon',
    component: BridalGlamStudio,
    deployable: true,
  },
  // Legacy aliases
  'clinic_classic': {
    name: 'Clinic Classic',
    industry: 'clinic',
    component: ClinicMultiSpecialty,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_classic': {
    name: 'Clinic Classic',
    industry: 'clinic',
    component: ClinicMultiSpecialty,
    deployable: false,
    preview_only: true,
  },
  'clinic_premium': {
    name: 'Clinic Premium',
    industry: 'clinic',
    component: ClinicDentalStudio,
    deployable: false,
    preview_only: true,
  },
  'tpl_clinic_premium': {
    name: 'Clinic Premium',
    industry: 'clinic',
    component: ClinicDentalStudio,
    deployable: false,
    preview_only: true,
  },
};

/**
 * Resolves the visual template component for a given template configuration.
 */
export function resolveTemplateComponent(templateData) {
  if (!templateData) return FallbackTemplate;

  const slug = templateData.template?.slug;
  const id = templateData.template?.id;
  const indSlug = templateData.industry?.slug;

  if (slug && TEMPLATE_REGISTRY[slug]?.component) {
    return TEMPLATE_REGISTRY[slug].component;
  }
  if (id && TEMPLATE_REGISTRY[id]?.component) {
    return TEMPLATE_REGISTRY[id].component;
  }

  // Industry-level fallback
  if (indSlug === 'restaurant' || indSlug === 'dining') return RestaurantClassicBistro;
  if (indSlug === 'salon' || indSlug === 'beauty') return SalonSpaSanctuary;
  if (indSlug === 'retail' || indSlug === 'shopping') return RetailFashionBoutique;
  if (indSlug === 'hotel' || indSlug === 'hospitality') return HotelHeritageResort;
  if (indSlug === 'fitness' || indSlug === 'wellness') return FitnessIronForge;
  if (indSlug === 'clinic' || indSlug === 'healthcare') return ClinicMultiSpecialty;

  return FallbackTemplate;
}
