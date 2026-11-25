import React from 'react';

/**
 * F03 — Luxury Dining (restaurant_luxury_dining)
 * Haute cuisine, Michelin-inspired opulence.
 * Midnight velvet background (#0A0A0C), Champagne gold accents (#D4AF37),
 * Cormorant Garamond typography, and responsive dual-column split on desktop.
 */
export default function RestaurantLuxuryDining({ templateData, journeyState = {} }) {
  const {
    rating = 5,
    setRating = () => {},
    hoverRating = 0,
    setHoverRating = () => {},
    ratingLabel,
    availableTopics = [],
    selectedTopics = [],
    toggleTopic = () => {},
    personalNote = '',
    setPersonalNote = () => {},
    touchpointLabel = 'Table',
    touchpointValue = null,
    ideas = [],
    selectedIdeaId = null,
    onSelectIdea = () => {},
    draftReview = '',
    onDirectGoogleHandoff = () => {},
    onOpenPrivateFeedback = () => {},
    notePlaceholder,
    t = {},
  } = journeyState || {};

  const bizName = templateData?.businessName || 'L’Étoile Dining Room';
  const gold = '#D4AF37';
  const goldLight = '#F3E5AB';
  const midnight = '#0A0A0C';
  const velvetCard = '#141418';
  const velvetBorder = '#2A2A32';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. The degustation tasting menu and sommelier pairing were flawless! 🍾✨';

  return (
    <div
      className="vt-page-container vt-luxury-dining"
      style={{
        backgroundColor: midnight,
        minHeight: '100vh',
        color: '#E8E8E8',
        fontFamily: "'Cormorant Garamond', 'Didot', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Haute Cuisine Crest, Gold Star Continuum & Pairing Topics */}
        <div className="vt-split-sticky-sidebar">
          {/* Header Card */}
          <header
            style={{
              textAlign: 'center',
              padding: '28px 20px',
              borderBottom: `1px solid ${gold}33`,
              background: velvetCard,
              borderRadius: '16px',
              border: `1px solid ${velvetBorder}`,
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              marginBottom: '20px',
            }}
          >
            <div style={{ letterSpacing: '4px', textTransform: 'uppercase', fontSize: '0.75rem', color: gold, marginBottom: '8px', fontWeight: 600 }}>
              Exquisite Gastronomy
            </div>
            <h1 style={{ fontSize: '2.1rem', fontWeight: 400, color: goldLight, margin: '0 0 8px 0', letterSpacing: '1px' }}>
              {bizName}
            </h1>
            {touchpointValue && (
              <div style={{ fontSize: '0.8rem', letterSpacing: '2px', color: '#888892', textTransform: 'uppercase', marginTop: '8px' }}>
                {touchpointLabel}: <span style={{ color: gold }}>{touchpointValue}</span>
              </div>
            )}
          </header>

          {/* Gold Continuum Rating Card */}
          <section
            style={{
              background: velvetCard,
              borderRadius: '16px',
              border: `1px solid ${gold}40`,
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              padding: '24px 20px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '1.1rem', fontWeight: 400, color: goldLight, letterSpacing: '2px', textTransform: 'uppercase', margin: '0 0 16px 0' }}>
              {t.howWasVisit || 'Rate Your Evening'}
            </h2>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', fontSize: '2.5rem', cursor: 'pointer', marginBottom: '10px' }}>
              {[1, 2, 3, 4, 5].map((val) => {
                const active = val <= (hoverRating || rating);
                return (
                  <span
                    key={val}
                    onMouseEnter={() => setHoverRating(val)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(val)}
                    style={{
                      color: active ? gold : '#3A3A44',
                      transition: 'all 0.2s ease',
                      transform: active ? 'scale(1.15)' : 'scale(1)',
                    }}
                  >
                    ★
                  </span>
                );
              })}
            </div>
            <div style={{ fontSize: '1rem', color: gold, letterSpacing: '1px' }}>
              {ratingLabel?.emoji} {ratingLabel?.text}
            </div>
          </section>

          {/* Highlights / Sommelier Topics */}
          <section
            style={{
              background: velvetCard,
              borderRadius: '16px',
              border: `1px solid ${velvetBorder}`,
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              padding: '22px 20px',
            }}
          >
            <h3 style={{ fontSize: '0.95rem', fontWeight: 400, color: goldLight, margin: '0 0 14px 0', letterSpacing: '2px', textTransform: 'uppercase' }}>
              {t.whatStoodOut || 'Memorable Highlights'}
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {availableTopics.map((top) => {
                const isSel = selectedTopics.includes(top.label);
                return (
                  <button
                    key={top.label}
                    type="button"
                    onClick={() => toggleTopic(top.label)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 16px',
                      borderRadius: '4px',
                      border: isSel ? `1px solid ${gold}` : `1px solid ${velvetBorder}`,
                      background: isSel ? `${gold}20` : '#0E0E12',
                      color: isSel ? goldLight : '#888892',
                      fontSize: '0.88rem',
                      letterSpacing: '0.5px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span>{top.icon}</span>
                    <span>{top.label}</span>
                  </button>
                );
              })}
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN: Note, Curated Review Folio & Gold CTA */}
        <div className="vt-split-content">
          {/* Note Input */}
          <section
            style={{
              background: velvetCard,
              borderRadius: '16px',
              border: `1px solid ${velvetBorder}`,
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              padding: '22px 20px',
              marginBottom: '20px',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.82rem', letterSpacing: '1px', textTransform: 'uppercase', color: gold, marginBottom: '8px' }}>
              {t.personalNote || 'Personal note'} ({t.optional || 'optional'})
            </label>
            <input
              type="text"
              value={personalNote}
              onChange={(e) => setPersonalNote(e.target.value)}
              placeholder={placeholder}
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: '6px',
                border: `1px solid ${velvetBorder}`,
                background: '#0E0E12',
                color: '#E8E8E8',
                fontSize: '0.95rem',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
              }}
            />
          </section>

          {/* AI Curated Review Folio */}
          <section
            style={{
              background: velvetCard,
              borderRadius: '16px',
              border: `1px solid ${velvetBorder}`,
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              padding: '24px 20px',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 400, color: goldLight, margin: 0, letterSpacing: '2px', textTransform: 'uppercase' }}>
                {t.reviewIdeas || 'Curated Gastronomic Impressions'}
              </h3>
              <span style={{ fontSize: '0.78rem', color: gold, letterSpacing: '1px' }}>
                Select to Publish
              </span>
            </div>

            {ideas.map((idea) => {
              const isSelected = selectedIdeaId === idea.id;
              return (
                <div
                  key={idea.id}
                  onClick={() => onSelectIdea(idea)}
                  style={{
                    padding: '18px',
                    borderRadius: '6px',
                    border: isSelected ? `1px solid ${gold}` : `1px solid ${velvetBorder}`,
                    background: isSelected ? `${gold}10` : '#0E0E12',
                    marginBottom: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', letterSpacing: '2px', textTransform: 'uppercase', color: gold }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: gold }}>★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.95rem', color: '#D4D4D8', lineHeight: '1.6', fontStyle: 'italic' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '10px', textAlign: 'right', fontSize: '0.8rem', color: gold, letterSpacing: '1px' }}>
                    {isSelected ? '✓ Selected for Google →' : 'Publish this review →'}
                  </div>
                </div>
              );
            })}

            {/* Gold CTA */}
            <button
              type="button"
              onClick={() => onDirectGoogleHandoff(draftReview)}
              style={{
                width: '100%',
                padding: '16px',
                backgroundColor: gold,
                color: '#0A0A0C',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '1rem',
                letterSpacing: '2px',
                textTransform: 'uppercase',
                cursor: 'pointer',
                marginTop: '16px',
                boxShadow: '0 8px 24px rgba(212,175,55,0.25)',
                transition: 'all 0.2s ease',
              }}
            >
              {t.copyAndOpenGoogle || 'Publish to Google Review ↗'}
            </button>
          </section>

          {/* Private feedback option */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.88rem', color: '#888892' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Wish to share a private note with our Maître d’hôtel? ') : (t.privatePromptBad || 'Direct confidential notes to general management: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: gold, fontWeight: 600, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
