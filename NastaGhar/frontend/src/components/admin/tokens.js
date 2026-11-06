/**
 * VRAJA AI Enterprise Super Admin Panel — Official Design Tokens
 * 
 * Strict palette and typography rules:
 * - Primary: Warm Ivory, Deep Emerald, Muted Gold, Forest Charcoal
 * - Supporting: Pure White, Soft Sage, Muted Grey-Green, Subtle Border
 * - Semantic: Emerald Green (Success), Amber (Warning), Crimson (Critical/Suspended)
 */

export const ADMIN_TOKENS = {
  colors: {
    // Primary palette
    warmIvory: '#F5F3EC',        // Main application background
    deepEmerald: '#174D3A',      // Sidebar, primary actions, high-importance accents
    deepEmeraldHover: '#113B2C', // Primary button hover
    deepEmeraldActive: '#0C2A20',// Active button click
    mutedGold: '#C6A66B',        // Brand insignia, premium highlights, accents
    mutedGoldLight: '#F7F3E9',   // Gold tint for badges/icons
    forestCharcoal: '#26352D',   // Primary text, headings, prominent numerals

    // Supporting palette
    pureWhite: '#FFFFFF',        // Card surfaces, modals, popovers
    softSage: '#DCE5DD',         // Selected navigation, secondary buttons, subtle fills
    softSageHover: '#CFDDD0',    // Secondary button hover
    mutedGreyGreen: '#718078',   // Secondary text, table headers, helper captions
    subtleBorder: '#E3E8E3',     // Component borders, dividers
    subtleBorderHover: '#CCD6CD',// Interactive border hover

    // Semantic colors
    success: {
      text: '#1D7A4D',
      bg: '#E8F5EE',
      border: '#BFE4CE',
    },
    warning: {
      text: '#945B09',
      bg: '#FEF7E6',
      border: '#F9DF9C',
    },
    critical: {
      text: '#B42318',
      bg: '#FEECEB',
      border: '#F7C6C3',
    },
    neutral: {
      text: '#718078',
      bg: '#F1F4F1',
      border: '#E3E8E3',
    },
  },

  typography: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', Helvetica, Arial, sans-serif",
    fontSize: {
      display: '32px',
      title: '22px',
      heading: '16px',
      body: '14px',
      caption: '12px',
      micro: '11px',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.65,
    },
  },

  radii: {
    sm: '6px',
    md: '8px',
    lg: '10px',
    xl: '14px',
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 2px rgba(38, 53, 45, 0.04)',
    card: '0 1px 3px rgba(38, 53, 45, 0.05), 0 4px 12px rgba(38, 53, 45, 0.03)',
    elevated: '0 4px 6px -1px rgba(38, 53, 45, 0.08), 0 12px 28px -4px rgba(38, 53, 45, 0.10)',
    modal: '0 20px 40px -8px rgba(22, 33, 27, 0.25)',
  },

  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
};

export default ADMIN_TOKENS;
