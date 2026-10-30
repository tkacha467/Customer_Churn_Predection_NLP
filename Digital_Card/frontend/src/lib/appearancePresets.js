/**
 * VRAJA AI Digital Card — Appearance & Background Preset Registry
 * Provides curated, royalty-free background presets and brand accent options.
 */

export const ACCENT_PRESETS = [
  { id: 'electric_blue', label: 'Electric Blue', hex: '#078BFF', border: '#078BFF' },
  { id: 'cyan_neon', label: 'Cyan Horizon', hex: '#12C8F5', border: '#12C8F5' },
  { id: 'champagne_gold', label: 'Champagne Gold', hex: '#E7BD59', border: '#E7BD59' },
  { id: 'emerald_mint', label: 'Emerald Mint', hex: '#10B981', border: '#10B981' },
  { id: 'crimson_flame', label: 'Crimson Flame', hex: '#EF4444', border: '#EF4444' },
  { id: 'royal_purple', label: 'Royal Violet', hex: '#8B5CF6', border: '#8B5CF6' },
];

export const BACKGROUND_PRESETS = [
  {
    id: 'default_navy',
    name: 'VRAJA Midnight (Default)',
    category: 'VRAJA Core',
    description: 'Layered midnight navy with subtle electric-blue ambiance',
    backgroundCss: 'linear-gradient(135deg, #061329 0%, #0b1f43 55%, #081a38 100%)',
    previewGradient: 'linear-gradient(135deg, #061329, #0b1f43, #078bff)',
  },
  {
    id: 'electric_cyber',
    name: 'Electric Cyber',
    category: 'Tech & Modern',
    description: 'Dynamic electric-blue gradient mesh over deep obsidian',
    backgroundCss: 'radial-gradient(ellipse at 80% 20%, rgba(7, 139, 255, 0.45) 0%, transparent 60%), linear-gradient(135deg, #040e1f 0%, #0a2550 50%, #061329 100%)',
    previewGradient: 'linear-gradient(135deg, #040e1f, #0a2550, #078bff)',
  },
  {
    id: 'cyan_horizon',
    name: 'Cyan Horizon',
    category: 'Tech & Modern',
    description: 'Deep twilight navy with electric cyan starlight glow',
    backgroundCss: 'radial-gradient(ellipse at 20% 10%, rgba(18, 200, 245, 0.35) 0%, transparent 55%), linear-gradient(135deg, #040e1f 0%, #071f40 60%, #0a335c 100%)',
    previewGradient: 'linear-gradient(135deg, #040e1f, #071f40, #12c8f5)',
  },
  {
    id: 'restaurant_gourmet',
    name: 'Bistro & Gourmet',
    category: 'Dining & Hospitality',
    description: 'Warm ambient champagne culinary glow over midnight navy',
    backgroundCss: 'radial-gradient(ellipse at 50% 15%, rgba(231, 189, 89, 0.28) 0%, transparent 60%), linear-gradient(180deg, #081528 0%, #061329 100%)',
    previewGradient: 'linear-gradient(135deg, #081528, #1a2233, #e7bd59)',
  },
  {
    id: 'gym_athletic',
    name: 'Pulse Fitness & Power',
    category: 'Fitness & Health',
    description: 'High-energy athletic kinetic grid with neon blue pulse',
    backgroundCss: 'repeating-linear-gradient(45deg, rgba(7, 139, 255, 0.08) 0px, rgba(7, 139, 255, 0.08) 2px, transparent 2px, transparent 16px), linear-gradient(180deg, #040d1c 0%, #081d3d 100%)',
    previewGradient: 'linear-gradient(135deg, #040d1c, #078bff, #081d3d)',
  },
  {
    id: 'corporate_legal',
    name: 'Executive & Legal',
    category: 'Corporate & Legal',
    description: 'Structured architectural pinstripe grid with gold accents',
    backgroundCss: 'linear-gradient(90deg, rgba(231, 189, 89, 0.05) 1px, transparent 1px) 0 0 / 20px 20px, linear-gradient(rgba(231, 189, 89, 0.05) 1px, transparent 1px) 0 0 / 20px 20px, linear-gradient(180deg, #061329 0%, #0b1f43 100%)',
    previewGradient: 'linear-gradient(135deg, #061329, #0b1f43, #e7bd59)',
  },
  {
    id: 'champagne_luxury',
    name: 'Champagne Luxury',
    category: 'Luxury & VIP',
    description: 'Deep navy infused with opulent champagne gold nebula',
    backgroundCss: 'radial-gradient(circle at 80% 20%, rgba(231, 189, 89, 0.25) 0%, transparent 50%), linear-gradient(135deg, #061329 0%, #141c2b 50%, #292419 100%)',
    previewGradient: 'linear-gradient(135deg, #061329, #1e2433, #e7bd59)',
  },
  {
    id: 'solid_navy',
    name: 'Solid Midnight',
    category: 'Minimalist',
    description: 'Ultra-clean solid midnight navy surface',
    backgroundCss: '#061329',
    previewGradient: '#061329',
  },
];

/**
 * Computes the hero header style based on cover photo, preset, and overlay opacity.
 */
export function getHeaderBackgroundStyle(coverImagePath, presetId, overlayOpacity = 0.75) {
  const safeOpacity = typeof overlayOpacity === 'number' && !isNaN(overlayOpacity)
    ? Math.max(0.15, Math.min(0.95, overlayOpacity))
    : 0.75;

  const baseGradient = `linear-gradient(180deg, rgba(6, 19, 41, ${safeOpacity}) 0%, rgba(11, 31, 67, ${Math.min(0.98, safeOpacity + 0.12)}) 100%)`;

  // 1. If tenant uploaded a custom cover image or photo
  if (coverImagePath && coverImagePath.trim()) {
    const url = coverImagePath.trim();
    return {
      backgroundImage: `${baseGradient}, url("${url}")`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
    };
  }

  // 2. If tenant selected a curated preset
  const preset = BACKGROUND_PRESETS.find((p) => p.id === presetId);
  if (preset) {
    if (preset.id === 'solid_navy') {
      return {
        background: '#061329',
      };
    }
    return {
      backgroundImage: `${baseGradient}, ${preset.backgroundCss}`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    };
  }

  // 3. Default VRAJA Midnight fallback
  const defaultPreset = BACKGROUND_PRESETS[0];
  return {
    backgroundImage: `${baseGradient}, ${defaultPreset.backgroundCss}`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  };
}
