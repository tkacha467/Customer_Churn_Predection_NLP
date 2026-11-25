import React from 'react';

/**
 * B01 — Modern Barbershop & Grooming Lounge (beauty_barber_lounge / salon_barber_lounge)
 * Visual Structure: Matte carbon black (#121212), warm bourbon amber (#D97706), brushed steel (#E5E7EB).
 * Hero: Barber pole stripe accent, vintage gentleman grooming header.
 * Rating: Segmented blade badge rating.
 * Responsive dual-column split on desktop.
 */
export default function BarberGroomingLounge({ templateData, journeyState = {} }) {
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
    touchpointLabel = 'Barber Chair',
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

  const bizName = templateData?.businessName || 'The Iron & Razor Barbershop';
  const carbon = '#121212';
  const amber = '#D97706';
  const steel = '#1E1E1E';
  const border = '#383838';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Sharp skin fade and relaxing hot towel treatment! 💈🪒';

  return (
    <div
      className="vt-page-container vt-barber-lounge"
      style={{
        backgroundColor: carbon,
        minHeight: '100vh',
        color: '#E5E5E5',
        fontFamily: "'Barlow Condensed', 'Oswald', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Barber Pole Crest, Steel Blade Rating & Grooming Tags */}
        <div className="vt-split-sticky-sidebar">
          {/* Header Card */}
          <header
            style={{
              textAlign: 'center',
              padding: '24px 20px',
              borderBottom: `3px solid ${amber}`,
              background: steel,
              borderRadius: '16px',
              border: `1px solid ${border}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontSize: '2.4rem', marginBottom: '6px' }}>💈 ✂️ 🪒</div>
            <div style={{ fontSize: '0.8rem', letterSpacing: '2px', textTransform: 'uppercase', color: amber, fontWeight: 800, marginBottom: '4px' }}>
              Gentlemen’s Grooming & Hot Towel Shaves
            </div>
            <h1 style={{ fontSize: '2.1rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
              {bizName}
            </h1>
            {touchpointValue && (
              <div style={{ marginTop: '10px', display: 'inline-block', padding: '4px 14px', borderRadius: '4px', backgroundColor: `${amber}25`, color: amber, fontWeight: 800, fontSize: '0.82rem', letterSpacing: '1px', textTransform: 'uppercase' }}>
                {touchpointLabel}: {touchpointValue}
              </div>
            )}
          </header>

          {/* Segmented Blade Rating Card */}
          <section
            style={{
              background: steel,
              borderRadius: '16px',
              border: `1px solid ${border}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              padding: '22px 18px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '1rem', fontWeight: 800, color: '#FFFFFF', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 14px 0' }}>
              {t.howWasVisit || 'Rate Your Cut & Shave'}
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '12px' }}>
              {[1, 2, 3, 4, 5].map((val) => {
                const isSelected = val === rating;
                const isHovered = val === hoverRating;
                return (
                  <button
                    key={val}
                    type="button"
                    onMouseEnter={() => setHoverRating(val)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(val)}
                    style={{
                      padding: '12px 0',
                      borderRadius: '4px',
                      border: isSelected ? `2px solid ${amber}` : `1px solid ${border}`,
                      background: isSelected ? amber : isHovered ? `${amber}30` : '#141414',
                      color: isSelected ? '#000000' : '#E5E5E5',
                      fontWeight: 900,
                      fontSize: '1.2rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {val}★
                  </button>
                );
              })}
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: amber, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {ratingLabel?.emoji} {ratingLabel?.text}
            </div>
          </section>

          {/* Stamped Grooming Topics */}
          <section
            style={{
              background: steel,
              borderRadius: '16px',
              border: `1px solid ${border}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              padding: '20px 18px',
            }}
          >
            <h3 style={{ fontSize: '0.92rem', fontWeight: 800, color: '#FFFFFF', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
              {t.whatStoodOut || 'Services & Craft'}
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
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: '4px',
                      border: isSel ? `1px solid ${amber}` : `1px solid ${border}`,
                      background: isSel ? `${amber}25` : '#141414',
                      color: isSel ? amber : '#A3A3A3',
                      fontSize: '0.88rem',
                      fontWeight: isSel ? 800 : 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      textTransform: 'uppercase',
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

        {/* RIGHT COLUMN: Note, Suggestions & Bourbon Amber CTA */}
        <div className="vt-split-content">
          {/* Note Input */}
          <section
            style={{
              background: steel,
              borderRadius: '16px',
              border: `1px solid ${border}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              padding: '20px 18px',
              marginBottom: '20px',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 800, color: amber, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
              {t.personalNote || 'Personal note'} ({t.optional || 'optional'})
            </label>
            <input
              type="text"
              value={personalNote}
              onChange={(e) => setPersonalNote(e.target.value)}
              placeholder={placeholder}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '4px',
                border: `1px solid ${border}`,
                background: '#141414',
                color: '#FFFFFF',
                fontSize: '0.95rem',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
              }}
            />
          </section>

          {/* AI Suggestions Cards */}
          <section
            style={{
              background: steel,
              borderRadius: '16px',
              border: `1px solid ${border}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              padding: '22px 18px',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#FFFFFF', margin: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
                {t.reviewIdeas || 'Barbershop Review Suggestions'}
              </h3>
              <span style={{ fontSize: '0.78rem', color: amber, fontWeight: 800 }}>
                Tap to Select
              </span>
            </div>

            {ideas.map((idea) => {
              const isSelected = selectedIdeaId === idea.id;
              return (
                <div
                  key={idea.id}
                  onClick={() => onSelectIdea(idea)}
                  style={{
                    padding: '16px',
                    borderRadius: '6px',
                    border: isSelected ? `2px solid ${amber}` : `1px solid ${border}`,
                    background: isSelected ? `${amber}15` : '#141414',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 900, color: amber, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: amber }}>💈★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.95rem', color: '#E5E5E5', lineHeight: '1.45' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '8px', textAlign: 'right', fontSize: '0.8rem', color: amber, fontWeight: 800, textTransform: 'uppercase' }}>
                    {isSelected ? '✓ Selected →' : 'Use this review →'}
                  </div>
                </div>
              );
            })}

            {/* Bourbon Amber Google CTA */}
            <button
              type="button"
              onClick={() => onDirectGoogleHandoff(draftReview)}
              style={{
                width: '100%',
                padding: '16px',
                backgroundColor: amber,
                color: '#000000',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 900,
                fontSize: '1.05rem',
                cursor: 'pointer',
                marginTop: '14px',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                boxShadow: '0 6px 20px rgba(217,119,6,0.3)',
                transition: 'transform 0.15s ease',
              }}
            >
              {t.copyAndOpenGoogle || 'Publish to Google Review 💈↗'}
            </button>
          </section>

          {/* Private feedback option */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.85rem', color: '#737373' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Have private words for master barber? ') : (t.privatePromptBad || 'Direct confidential notes to owner: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: amber, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
