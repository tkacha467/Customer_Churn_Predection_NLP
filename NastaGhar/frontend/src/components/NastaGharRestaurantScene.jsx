import React from 'react';

/**
 * NastaGharRestaurantScene
 * 
 * An original, fully self-contained vector illustration & CSS animated scene
 * of Nasta Ghar Gujarati Restaurant in Rajkot.
 * 
 * Features:
 * - Left: Gujarati Maharaj / Cook preparing fresh snacks at the kadai with rising steam & ladle motion
 * - Center: Authentic Gujarati dining counter & bronze thali with Dhokla, Thepla, Sabzi, Chutneys & Chai kettle
 * - Right: Friendly Nasta Ghar hospitality staff member serving a fresh hot thali
 * - Ambient: Swaying vintage brass lanterns, Gujarati archways (Toran), rising steam, and warm lighting
 * - Zero external image dependencies (pure inline SVG + CSS keyframes)
 * - Zero audio
 * - GPU-accelerated transforms & opacity, with prefers-reduced-motion fallback
 */
export default function NastaGharRestaurantScene({ compact = false }) {
  return (
    <div className={`ng-scene-wrapper ${compact ? 'compact' : ''}`} role="img" aria-label="Animated illustration of Nasta Ghar restaurant with chef cooking dhokla, central food counter, and staff serving hot food">
      <div className="ng-scene-container">
        <svg
          className="ng-scene-svg"
          viewBox="0 0 1000 420"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Gradients */}
            <linearGradient id="bgGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#102515" />
              <stop offset="50%" stopColor="#173B20" />
              <stop offset="100%" stopColor="#0C1B0F" />
            </linearGradient>

            <linearGradient id="wallPanelGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#133019" />
              <stop offset="50%" stopColor="#1A4224" />
              <stop offset="100%" stopColor="#133019" />
            </linearGradient>

            <linearGradient id="counterGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#2A5C35" />
              <stop offset="25%" stopColor="#1E4728" />
              <stop offset="100%" stopColor="#102414" />
            </linearGradient>

            <linearGradient id="counterTopGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2D663B" />
              <stop offset="50%" stopColor="#3F8550" />
              <stop offset="100%" stopColor="#2D663B" />
            </linearGradient>

            <linearGradient id="brassGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFE066" />
              <stop offset="50%" stopColor="#D4A017" />
              <stop offset="100%" stopColor="#8C6205" />
            </linearGradient>

            <linearGradient id="kansaThaliGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFF2A3" />
              <stop offset="40%" stopColor="#E2B338" />
              <stop offset="80%" stopColor="#9C6B10" />
              <stop offset="100%" stopColor="#5E3F05" />
            </linearGradient>

            <linearGradient id="dhoklaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFF97A" />
              <stop offset="60%" stopColor="#F4E026" />
              <stop offset="100%" stopColor="#C9B307" />
            </linearGradient>

            <linearGradient id="theplaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#EAD295" />
              <stop offset="50%" stopColor="#CD9B48" />
              <stop offset="100%" stopColor="#8C5C1B" />
            </linearGradient>

            <linearGradient id="kadhiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFF699" />
              <stop offset="100%" stopColor="#E0B612" />
            </linearGradient>

            <linearGradient id="chutneyGreenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#84CC16" />
              <stop offset="100%" stopColor="#3F6212" />
            </linearGradient>

            <linearGradient id="chutneyRedGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#EF4444" />
              <stop offset="100%" stopColor="#7F1D1D" />
            </linearGradient>

            <linearGradient id="signGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#C9FF00" />
              <stop offset="50%" stopColor="#F4F66A" />
              <stop offset="100%" stopColor="#C9FF00" />
            </linearGradient>

            <radialGradient id="lanternGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FFF9A6" stopOpacity="0.8" />
              <stop offset="40%" stopColor="#F4F66A" stopOpacity="0.4" />
              <stop offset="80%" stopColor="#C9FF00" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#173B20" stopOpacity="0" />
            </radialGradient>

            <radialGradient id="centerWarmth" cx="50%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#F4F66A" stopOpacity="0.18" />
              <stop offset="60%" stopColor="#173B20" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#102515" stopOpacity="0" />
            </radialGradient>

            {/* Subtle Gujarati Bandhani / Jaali Filter Pattern */}
            <pattern id="gujaratiArchPattern" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
              <circle cx="20" cy="20" r="1.5" fill="#C9FF00" fillOpacity="0.08" />
              <path d="M 0 20 Q 20 0 40 20 Q 20 40 0 20" fill="none" stroke="#F4F66A" strokeWidth="0.5" strokeOpacity="0.06" />
            </pattern>
          </defs>

          {/* ════════ BACKGROUND & INTERIOR ════════ */}
          <rect width="1000" height="420" fill="url(#bgGrad)" />
          <rect width="1000" height="420" fill="url(#gujaratiArchPattern)" />
          <rect width="1000" height="340" fill="url(#centerWarmth)" />

          {/* Gujarati Jharokha / Decorative Archway in Background */}
          <g className="ng-bg-architecture" opacity="0.35">
            {/* Center Arch */}
            <path
              d="M 320 0 L 320 80 Q 320 160 500 160 Q 680 160 680 80 L 680 0 Z"
              fill="none"
              stroke="#C9FF00"
              strokeWidth="1.5"
              strokeDasharray="4 4"
            />
            {/* Left Arch */}
            <path
              d="M 40 0 L 40 100 Q 40 180 200 180 Q 300 180 300 100 L 300 0"
              fill="none"
              stroke="#F4F66A"
              strokeWidth="1.2"
              strokeOpacity="0.6"
            />
            {/* Right Arch */}
            <path
              d="M 700 0 L 700 100 Q 700 180 820 180 Q 960 180 960 100 L 960 0"
              fill="none"
              stroke="#F4F66A"
              strokeWidth="1.2"
              strokeOpacity="0.6"
            />
          </g>

          {/* Decorative Gujarati Toran (Marigold & Mango Leaves Garland) across top */}
          <g className="ng-toran">
            <path d="M 0 15 Q 125 35 250 15 Q 375 35 500 15 Q 625 35 750 15 Q 875 35 1000 15" fill="none" stroke="#D4A017" strokeWidth="2" />
            {/* Toran Marigold Drop Tassels */}
            {[60, 125, 190, 250, 310, 375, 440, 500, 560, 625, 690, 750, 810, 875, 940].map((cx, idx) => (
              <g key={idx} transform={`translate(${cx}, ${18 + Math.sin(idx * 0.8) * 8})`}>
                <polygon points="0,0 -8,14 8,14" fill={idx % 2 === 0 ? '#1E6F33' : '#F59E0B'} />
                <circle cx="0" cy="16" r="3.5" fill="#EF4444" />
                <circle cx="0" cy="22" r="2.5" fill="#F4F66A" />
              </g>
            ))}
          </g>

          {/* Glowing Nasta Ghar Signboard Plaque on Back Wall */}
          <g className="ng-wall-sign" transform="translate(410, 45)">
            <rect x="0" y="0" width="180" height="42" rx="8" fill="#102515" stroke="#C9FF00" strokeWidth="1.2" filter="drop-shadow(0 2px 8px rgba(201,255,0,0.25))" />
            <rect x="3" y="3" width="174" height="36" rx="6" fill="#173B20" stroke="#F4F66A" strokeWidth="0.6" strokeOpacity="0.5" />
            {/* Sign Text & Emblems */}
            <text x="90" y="22" textAnchor="middle" fill="#C9FF00" fontFamily="system-ui, -apple-system, sans-serif" fontWeight="800" fontSize="13" letterSpacing="2">
              NASTA GHAR
            </text>
            <text x="90" y="33" textAnchor="middle" fill="#FFF8E8" fontFamily="system-ui, -apple-system, sans-serif" fontWeight="500" fontSize="7.5" letterSpacing="1">
              AUTHENTIC GUJARATI NASHTA
            </text>
            <circle cx="16" cy="21" r="3" fill="#F4F66A" />
            <circle cx="164" cy="21" r="3" fill="#F4F66A" />
          </g>

          {/* ════════ SWAYING HANGING LAMPS (CSS ANIMATED) ════════ */}
          {/* Lamp 1 (Left-Center) */}
          <g className="ng-lamp ng-lamp-left" transform="translate(230, 0)">
            <line x1="0" y1="0" x2="0" y2="85" stroke="#D4A017" strokeWidth="1.5" />
            <circle cx="0" cy="90" r="28" fill="url(#lanternGlow)" />
            <polygon points="-14,80 14,80 18,98 -18,98" fill="url(#brassGrad)" stroke="#5E3F05" strokeWidth="0.8" />
            <ellipse cx="0" cy="98" rx="18" ry="4" fill="#FFE066" />
            <circle cx="0" cy="96" r="5" fill="#FFF9A6" className="ng-bulb-pulse" />
          </g>

          {/* Lamp 2 (Center-Right) */}
          <g className="ng-lamp ng-lamp-right" transform="translate(770, 0)">
            <line x1="0" y1="0" x2="0" y2="95" stroke="#D4A017" strokeWidth="1.5" />
            <circle cx="0" cy="100" r="32" fill="url(#lanternGlow)" />
            <polygon points="-16,90 16,90 20,110 -20,110" fill="url(#brassGrad)" stroke="#5E3F05" strokeWidth="0.8" />
            <ellipse cx="0" cy="110" rx="20" ry="4.5" fill="#FFE066" />
            <circle cx="0" cy="108" r="6" fill="#FFF9A6" className="ng-bulb-pulse" />
          </g>

          {/* Lamp 3 (Far Center Ambient) */}
          <g className="ng-lamp ng-lamp-center" transform="translate(500, 0)">
            <line x1="0" y1="0" x2="0" y2="60" stroke="#D4A017" strokeWidth="1" opacity="0.7" />
            <circle cx="0" cy="65" r="22" fill="url(#lanternGlow)" />
            <polygon points="-10,55 10,55 12,70 -12,70" fill="url(#brassGrad)" />
            <ellipse cx="0" cy="70" rx="12" ry="3" fill="#FFE066" />
          </g>

          {/* ════════ RESTAURANT SERVICE COUNTER (FOUNDATION) ════════ */}
          <g className="ng-counter-structure">
            {/* Lower Counter Body */}
            <rect x="0" y="270" width="1000" height="150" fill="url(#counterGrad)" />
            {/* Top Polish Surface with Highlight Edge */}
            <polygon points="0,265 1000,265 1000,285 0,285" fill="url(#counterTopGrad)" />
            <line x1="0" y1="265" x2="1000" y2="265" stroke="#C9FF00" strokeWidth="2.5" strokeOpacity="0.7" />
            {/* Front Wooden Slats / Gujarati Carving Accents */}
            <line x1="0" y1="310" x2="1000" y2="310" stroke="#102515" strokeWidth="2" />
            <line x1="0" y1="355" x2="1000" y2="355" stroke="#102515" strokeWidth="2" />
            <line x1="0" y1="400" x2="1000" y2="400" stroke="#102515" strokeWidth="2" />
          </g>

          {/* ════════ LEFT: GUJARATI CHEF / KITCHEN AREA ════════ */}
          <g className="ng-chef-section" transform="translate(60, 105)">
            {/* Kitchen Back Wall & Spice Jars */}
            <g opacity="0.75">
              <rect x="10" y="90" width="130" height="10" rx="2" fill="#3D2806" />
              {/* Brass Masala Dabba / Spice Jars */}
              <rect x="20" y="65" width="16" height="25" rx="2" fill="url(#brassGrad)" />
              <rect x="42" y="68" width="14" height="22" rx="2" fill="#E2B338" />
              <rect x="62" y="62" width="18" height="28" rx="2" fill="url(#brassGrad)" />
              <rect x="86" y="66" width="15" height="24" rx="2" fill="#CD9B48" />
              <rect x="107" y="64" width="16" height="26" rx="2" fill="url(#brassGrad)" />
            </g>

            {/* Cooking Stove & Sizzling Kadai */}
            <g transform="translate(130, 130)">
              {/* Stove base */}
              <rect x="-35" y="25" width="70" height="15" rx="3" fill="#222" stroke="#444" strokeWidth="1" />
              {/* Burner Flame Glow */}
              <ellipse cx="0" cy="25" rx="22" ry="5" fill="#3B82F6" opacity="0.6" className="ng-burner-glow" />
              <ellipse cx="0" cy="24" rx="14" ry="3" fill="#60A5FA" opacity="0.9" />

              {/* Traditional Iron/Steel Deep Kadai */}
              <path d="M -30 18 Q 0 42 30 18 Q 35 15 28 15 Q 0 32 -28 15 Z" fill="#2B2D2F" stroke="#1F2937" strokeWidth="1.5" />
              <path d="M -26 18 Q 0 35 26 18 Z" fill="#D97706" opacity="0.85" />
              {/* Handles */}
              <path d="M -30 16 Q -38 12 -30 8" fill="none" stroke="#6B7280" strokeWidth="2.5" />
              <path d="M 30 16 Q 38 12 30 8" fill="none" stroke="#6B7280" strokeWidth="2.5" />

              {/* ♨️ STEAM PARTICLES FROM KADAI (CSS ANIMATED) ♨️ */}
              <g className="ng-steam-group">
                <path d="M -10 12 Q -18 -8 -8 -25 Q 0 -42 -10 -58" fill="none" stroke="#FFF8E8" strokeWidth="3" strokeLinecap="round" opacity="0.6" className="ng-steam-wisp-1" />
                <path d="M 5 10 Q 15 -10 2 -30 Q -8 -48 6 -68" fill="none" stroke="#FFF8E8" strokeWidth="3.5" strokeLinecap="round" opacity="0.7" className="ng-steam-wisp-2" />
                <path d="M -2 8 Q 8 -15 -4 -38 Q -14 -60 -2 -80" fill="none" stroke="#F4F66A" strokeWidth="2.5" strokeLinecap="round" opacity="0.5" className="ng-steam-wisp-3" />
              </g>
            </g>

            {/* Chef Maharaj Body & Pose */}
            <g className="ng-chef-body" transform="translate(65, 30)">
              {/* Torso & Traditional Gujarati Kurta / Apron */}
              <path d="M 0 75 Q -25 90 -20 150 L 35 150 Q 40 90 15 75 Z" fill="#FFF8E8" stroke="#D1D5DB" strokeWidth="1" />
              {/* Nasta Ghar Green Apron with Lime Trim */}
              <path d="M -12 90 L 22 90 L 26 150 L -16 150 Z" fill="#173B20" stroke="#C9FF00" strokeWidth="0.8" />
              {/* Apron Straps */}
              <line x1="-12" y1="90" x2="-3" y2="75" stroke="#173B20" strokeWidth="3" />
              <line x1="22" y1="90" x2="13" y2="75" stroke="#173B20" strokeWidth="3" />

              {/* Chef Neck & Face */}
              <rect x="0" y="60" width="10" height="18" fill="#D98A5B" />
              {/* Cheerful Friendly Head */}
              <circle cx="5" cy="48" r="20" fill="#EAA274" />
              {/* Traditional White Chef Pagdi / Cap */}
              <path d="M -14 42 Q 5 22 24 42 Q 26 20 5 16 Q -16 20 -14 42 Z" fill="#FFFFFF" stroke="#E5E7EB" strokeWidth="1" />
              <ellipse cx="5" cy="42" rx="19" ry="5" fill="#FFFFFF" stroke="#173B20" strokeWidth="1.5" />

              {/* Facial features: Warm smiling eyes, Gujarati Moustache, Tilak */}
              {/* Tilak */}
              <line x1="5" y1="32" x2="5" y2="39" stroke="#DC2626" strokeWidth="1.5" />
              <circle cx="5" cy="40" r="1" fill="#FBBF24" />
              {/* Eyes */}
              <path d="M -3 44 Q 0 41 3 44" fill="none" stroke="#261C14" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M 8 44 Q 11 41 14 44" fill="none" stroke="#261C14" strokeWidth="1.8" strokeLinecap="round" />
              {/* Moustache */}
              <path d="M -4 53 Q 5 50 14 53 Q 19 51 22 47 Q 15 57 5 55 Q -5 57 -12 47 Q -9 51 -4 53 Z" fill="#261C14" />
              {/* Smile */}
              <path d="M 0 57 Q 5 62 10 57" fill="none" stroke="#991B1B" strokeWidth="1.5" strokeLinecap="round" />

              {/* Left Arm Resting on Counter Side */}
              <path d="M -20 85 Q -32 110 -22 135" fill="none" stroke="#EAA274" strokeWidth="12" strokeLinecap="round" />

              {/* RIGHT ARM & COOKING LADLE (CSS ANIMATED STIRRING) */}
              <g className="ng-chef-arm-animated">
                <path d="M 18 85 Q 42 105 52 125" fill="none" stroke="#EAA274" strokeWidth="12" strokeLinecap="round" />
                {/* Hand gripping ladle */}
                <circle cx="53" cy="125" r="7" fill="#D98A5B" />
                {/* Long Stainless Steel Ladle / Jharra */}
                <line x1="53" y1="125" x2="68" y2="148" stroke="#9CA3AF" strokeWidth="3.5" strokeLinecap="round" />
                {/* Perforated Ladle Head inside Kadai */}
                <ellipse cx="70" cy="150" rx="9" ry="5" fill="#E5E7EB" stroke="#4B5563" strokeWidth="1" />
                <circle cx="70" cy="150" r="1.5" fill="#D97706" />
              </g>
            </g>
          </g>

          {/* ════════ CENTER: GUJARATI THALI & FOOD COUNTER ════════ */}
          <g className="ng-center-thali-showcase" transform="translate(400, 205)">
            {/* Raised Brass Showcase Platter Stand */}
            <ellipse cx="100" cy="85" rx="135" ry="38" fill="#0C1B0F" opacity="0.6" />
            <polygon points="-10,85 210,85 195,95 5,95" fill="#173B20" />

            {/* 🌟 GRAND AUTHENTIC GUJARATI THALI (KANSA / BRONZE) 🌟 */}
            <g className="ng-thali-plate">
              {/* Outer Rim of Thali */}
              <ellipse cx="100" cy="70" rx="120" ry="48" fill="url(#kansaThaliGrad)" stroke="#FFE066" strokeWidth="2.5" />
              {/* Inner Base of Thali */}
              <ellipse cx="100" cy="70" rx="108" ry="42" fill="#D4A017" stroke="#8C6205" strokeWidth="1.5" />

              {/* ── 1. FRESH GUJARATI DHOKLA (Center-Left) ── */}
              <g className="ng-food-dhokla" transform="translate(45, 52)">
                {/* Dhokla Piece 1 (Spongy Yellow with Mustard Seeds & Curry Leaf) */}
                <g className="ng-dhokla-cube-1">
                  <polygon points="0,8 18,0 36,8 18,16" fill="url(#dhoklaGrad)" stroke="#B45309" strokeWidth="0.8" />
                  <polygon points="0,8 18,16 18,28 0,20" fill="#EAB308" stroke="#B45309" strokeWidth="0.8" />
                  <polygon points="18,16 36,8 36,20 18,28" fill="#CA8A04" stroke="#B45309" strokeWidth="0.8" />
                  {/* Mustard Seeds (Rai) & Green Chilli */}
                  <circle cx="16" cy="7" r="1" fill="#1C1917" />
                  <circle cx="24" cy="9" r="0.8" fill="#1C1917" />
                  <circle cx="10" cy="11" r="1" fill="#1C1917" />
                  <path d="M 12 5 Q 18 8 22 5" stroke="#15803D" strokeWidth="1.2" fill="none" strokeLinecap="round" />
                </g>
                {/* Dhokla Piece 2 */}
                <g className="ng-dhokla-cube-2" transform="translate(18, -8)">
                  <polygon points="0,8 16,0 32,8 16,16" fill="url(#dhoklaGrad)" stroke="#B45309" strokeWidth="0.8" />
                  <polygon points="0,8 16,16 16,26 0,18" fill="#EAB308" stroke="#B45309" strokeWidth="0.8" />
                  <polygon points="16,16 32,8 32,18 16,26" fill="#CA8A04" stroke="#B45309" strokeWidth="0.8" />
                  <circle cx="14" cy="7" r="1" fill="#1C1917" />
                  <circle cx="20" cy="10" r="0.9" fill="#1C1917" />
                  <path d="M 10 7 Q 15 5 19 8" stroke="#15803D" strokeWidth="1.2" fill="none" strokeLinecap="round" />
                </g>
              </g>

              {/* ── 2. HOT THEPLA / ROTLI (Stacked Center) ── */}
              <g className="ng-food-thepla" transform="translate(95, 62)">
                {/* Bottom Thepla */}
                <ellipse cx="15" cy="12" rx="26" ry="11" fill="url(#theplaGrad)" stroke="#78350F" strokeWidth="0.8" />
                {/* Top Folded Methi Thepla with roasted brown specks */}
                <ellipse cx="13" cy="8" rx="25" ry="10" fill="#E0B767" stroke="#92400E" strokeWidth="0.8" />
                <circle cx="6" cy="7" r="1" fill="#78350F" />
                <circle cx="18" cy="9" r="1.2" fill="#78350F" />
                <circle cx="24" cy="6" r="0.8" fill="#78350F" />
                <circle cx="12" cy="10" r="0.7" fill="#15803D" />
                {/* Little Dollop of Fresh White Butter (Makhan) */}
                <ellipse cx="14" cy="5" rx="5" ry="2.5" fill="#FFFBEB" stroke="#FEF08A" strokeWidth="0.5" />
              </g>

              {/* ── 3. GUJARATI KADHI & SAAK IN BRASS KATORIS (BOWLS) ── */}
              {/* Bowl 1: Yellow Gujarati Kadhi with Curry Leaves (Top Left) */}
              <g className="ng-katori" transform="translate(30, 36)">
                <ellipse cx="16" cy="10" rx="18" ry="9" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1" />
                <ellipse cx="16" cy="9" rx="15" ry="7" fill="url(#kadhiGrad)" />
                <path d="M 11 9 Q 16 7 21 10" stroke="#166534" strokeWidth="1.2" fill="none" />
                <circle cx="14" cy="9" r="0.8" fill="#991B1B" />
              </g>

              {/* Bowl 2: Ringan Olo / Gujarati Shaak (Top Center) */}
              <g className="ng-katori" transform="translate(85, 30)">
                <ellipse cx="16" cy="10" rx="18" ry="9" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1" />
                <ellipse cx="16" cy="9" rx="15" ry="7" fill="#B45309" />
                <circle cx="12" cy="8" r="2" fill="#78350F" />
                <circle cx="18" cy="9" r="2.2" fill="#92400E" />
                <circle cx="20" cy="7" r="1.2" fill="#15803D" />
              </g>

              {/* Bowl 3: Green Coriander Chutney (Top Right) */}
              <g className="ng-katori" transform="translate(138, 38)">
                <ellipse cx="14" cy="9" rx="15" ry="8" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1" />
                <ellipse cx="14" cy="8" rx="12" ry="6" fill="url(#chutneyGreenGrad)" />
              </g>

              {/* Bowl 4: Sweet Dates-Tamarind Chutney (Right) */}
              <g className="ng-katori" transform="translate(150, 58)">
                <ellipse cx="13" cy="8" rx="14" ry="7.5" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1" />
                <ellipse cx="13" cy="7" rx="11" ry="5.5" fill="url(#chutneyRedGrad)" />
              </g>
            </g>

            {/* ── 4. STEAM FROM THALI (CSS ANIMATED) ── */}
            <g className="ng-thali-steam" transform="translate(95, 20)">
              <path d="M 0 10 Q -6 -5 2 -18 Q 10 -30 0 -42" fill="none" stroke="#FFF8E8" strokeWidth="2.5" strokeLinecap="round" opacity="0.6" className="ng-steam-wisp-center" />
              <path d="M 45 8 Q 52 -8 40 -24 Q 32 -38 46 -50" fill="none" stroke="#FFF8E8" strokeWidth="2" strokeLinecap="round" opacity="0.5" className="ng-steam-wisp-center-2" />
            </g>

            {/* ── 5. AUTHENTIC BRASS CHAI KETTLE & CUTTING GLASSES (Beside Thali) ── */}
            <g className="ng-chai-kettle-group" transform="translate(-85, 25)">
              {/* Traditional Indian Brass Tea Kettle */}
              {/* Base shadow */}
              <ellipse cx="25" cy="48" rx="20" ry="6" fill="#0C1B0F" opacity="0.5" />
              {/* Kettle Body */}
              <ellipse cx="25" cy="36" rx="22" ry="14" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1.2" />
              <rect x="15" y="16" width="20" height="12" rx="3" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1" />
              {/* Lid & Knob */}
              <ellipse cx="25" cy="16" rx="12" ry="4" fill="#FFE066" stroke="#78350F" strokeWidth="1" />
              <circle cx="25" cy="12" r="3" fill="#B45309" />
              {/* Spout */}
              <path d="M 40 32 Q 52 24 50 14 Q 46 16 38 24 Z" fill="url(#brassGrad)" stroke="#78350F" strokeWidth="1" />
              {/* Steam wisp from Chai kettle spout */}
              <path d="M 51 14 Q 56 4 48 -6 Q 42 -14 52 -24" fill="none" stroke="#FFF8E8" strokeWidth="2" strokeLinecap="round" opacity="0.6" className="ng-steam-wisp-chai" />
              {/* Arched Top Handle */}
              <path d="M 12 24 Q 10 -2 25 -2 Q 40 -2 38 24" fill="none" stroke="#451A03" strokeWidth="3" />

              {/* Two Cutting Chai Glasses with Rich Masala Chai */}
              <g transform="translate(56, 26)">
                {/* Glass 1 */}
                <polygon points="0,6 4,22 16,22 20,6" fill="#93C5FD" fillOpacity="0.4" stroke="#60A5FA" strokeWidth="1" />
                <polygon points="2,12 4,20 16,20 18,12" fill="#B45309" opacity="0.9" />
                {/* Cutting Chai froth */}
                <ellipse cx="10" cy="12" rx="7" ry="2" fill="#FDE68A" />
              </g>
            </g>
          </g>

          {/* ════════ RIGHT: RESTAURANT STAFF SERVING THALI ════════ */}
          <g className="ng-server-section" transform="translate(730, 80)">
            {/* Friendly Server / Hospitality Member (CSS ANIMATED FLOATING/SERVING) */}
            <g className="ng-server-character">
              {/* Server Body / Posture */}
              {/* Legs / Apron Lower */}
              <path d="M 40 180 L 35 240 L 75 240 L 70 180 Z" fill="#102515" />

              {/* Torso & Nasta Ghar Staff Uniform (Cream Shirt + Forest Green Hospitality Vest) */}
              <path d="M 25 105 Q 10 135 20 185 L 85 185 Q 95 135 80 105 Z" fill="#FFF8E8" stroke="#D1D5DB" strokeWidth="1" />
              {/* Green Vest with Lime Piping */}
              <path d="M 26 112 L 48 112 L 48 185 L 22 185 Z" fill="#173B20" stroke="#C9FF00" strokeWidth="0.8" />
              <path d="M 58 112 L 80 112 L 84 185 L 58 185 Z" fill="#173B20" stroke="#C9FF00" strokeWidth="0.8" />
              {/* Staff Badge */}
              <rect x="62" y="125" width="12" height="6" rx="1" fill="#C9FF00" />

              {/* Head & Welcoming Smile */}
              <rect x="48" y="88" width="10" height="18" fill="#D98A5B" />
              <circle cx="53" cy="74" r="19" fill="#EAA274" />
              {/* Well-groomed hair */}
              <path d="M 34 70 Q 53 50 72 70 Q 75 56 53 54 Q 32 56 34 70 Z" fill="#1F2937" />

              {/* Smiling Welcoming Facial Expression */}
              {/* Eyes */}
              <path d="M 44 71 Q 47 68 50 71" fill="none" stroke="#261C14" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M 57 71 Q 60 68 63 71" fill="none" stroke="#261C14" strokeWidth="1.8" strokeLinecap="round" />
              {/* Warm Host Smile */}
              <path d="M 47 81 Q 54 88 61 81" fill="none" stroke="#991B1B" strokeWidth="1.8" strokeLinecap="round" />
              {/* Dimples / Cheerful Cheeks */}
              <circle cx="43" cy="79" r="2.5" fill="#F87171" opacity="0.4" />
              <circle cx="64" cy="79" r="2.5" fill="#F87171" opacity="0.4" />

              {/* ARMS CARRYING SERVING TRAY & THALI (CSS ANIMATED GENTLE SWAY) */}
              <g className="ng-server-arms-tray">
                {/* Left Arm extended forward */}
                <path d="M 30 115 Q 0 135 -15 145" fill="none" stroke="#EAA274" strokeWidth="10" strokeLinecap="round" />
                {/* Right Arm supporting tray */}
                <path d="M 75 115 Q 50 140 10 148" fill="none" stroke="#EAA274" strokeWidth="10" strokeLinecap="round" />

                {/* Serving Tray (Brass / Steel) */}
                <ellipse cx="-5" cy="146" rx="55" ry="14" fill="url(#kansaThaliGrad)" stroke="#FFE066" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.3))" />
                <ellipse cx="-5" cy="145" rx="48" ry="11" fill="#D4A017" />

                {/* Hot Mini Thali on Serving Tray */}
                {/* Dhokla pieces on tray */}
                <g transform="translate(-32, 136)">
                  <polygon points="0,4 8,0 16,4 8,8" fill="url(#dhoklaGrad)" stroke="#B45309" strokeWidth="0.6" />
                  <polygon points="0,4 8,8 8,14 0,10" fill="#EAB308" />
                  <polygon points="8,8 16,4 16,10 8,14" fill="#CA8A04" />
                  <circle cx="8" cy="4" r="0.7" fill="#1C1917" />
                </g>
                <g transform="translate(-18, 134)">
                  <polygon points="0,4 8,0 16,4 8,8" fill="url(#dhoklaGrad)" stroke="#B45309" strokeWidth="0.6" />
                  <polygon points="0,4 8,8 8,14 0,10" fill="#EAB308" />
                  <polygon points="8,8 16,4 16,10 8,14" fill="#CA8A04" />
                  <circle cx="8" cy="4" r="0.7" fill="#1C1917" />
                </g>

                {/* Fresh Masala Chai Glass on Serving Tray */}
                <g transform="translate(14, 130)">
                  <polygon points="0,3 2,13 10,13 12,3" fill="#93C5FD" fillOpacity="0.5" stroke="#60A5FA" strokeWidth="0.8" />
                  <polygon points="1,7 2,12 10,12 11,7" fill="#B45309" />
                  <ellipse cx="6" cy="7" rx="4" ry="1.2" fill="#FDE68A" />
                  {/* Gentle steam from glass */}
                  <path d="M 6 4 Q 10 -4 4 -12" fill="none" stroke="#FFF8E8" strokeWidth="1.5" opacity="0.6" className="ng-steam-wisp-tray" />
                </g>
              </g>
            </g>
          </g>

          {/* ════════ AMBIENT FLOATING AROMA / LIGHT PARTICLES ════════ */}
          <g className="ng-particles" opacity="0.8">
            <circle cx="210" cy="180" r="2" fill="#C9FF00" className="ng-particle ng-p1" />
            <circle cx="340" cy="140" r="2.5" fill="#F4F66A" className="ng-particle ng-p2" />
            <circle cx="480" cy="120" r="1.5" fill="#FFE066" className="ng-particle ng-p3" />
            <circle cx="620" cy="160" r="2" fill="#C9FF00" className="ng-particle ng-p4" />
            <circle cx="710" cy="130" r="2.2" fill="#F4F66A" className="ng-particle ng-p5" />
            <circle cx="850" cy="190" r="1.8" fill="#FFE066" className="ng-particle ng-p6" />
          </g>

          {/* Bottom Foreground Gradient Fade to integrate seamlessly */}
          <rect x="0" y="405" width="1000" height="15" fill="#102515" opacity="0.9" />
        </svg>

        {/* Live Status Badge overlay on the bottom right */}
        <div className="ng-live-badge">
          <span className="ng-live-pulse-dot"></span>
          <span className="ng-live-text">Fresh & Hot • Serving with Pride</span>
        </div>
      </div>
    </div>
  );
}
