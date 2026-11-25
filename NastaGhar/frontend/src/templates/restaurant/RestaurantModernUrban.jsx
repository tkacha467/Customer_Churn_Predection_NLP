import React from 'react';

/**
 * F02 — Modern Urban (restaurant_modern_urban)
 * Contemporary craft eatery / industrial urban dining.
 * Dark slate background (#0F172A), neon lime accents (#84CC16), segmented horizontal rating bar,
 * responsive dual-column split on desktop.
 */
export default function RestaurantModernUrban({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Urban Kitchen & Bar';
  const neonLime = '#84CC16';
  const slateDark = '#0F172A';
  const slateCard = '#1E293B';
  const slateBorder = '#334155';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Loved the craft smash burger and electric ambience! 🍔⚡';

  return (
    <div
      className="vt-page-container vt-modern-urban"
      style={{
        backgroundColor: slateDark,
        minHeight: '100vh',
        color: '#F8FAFC',
        fontFamily: "'Syne', 'Plus Jakarta Sans', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Industrial Craft Header, Segmented Pill Rating & Tags */}
        <div className="vt-split-sticky-sidebar">
          {/* Header Card */}
          <header
            style={{
              textAlign: 'center',
              padding: '24px 20px',
              background: slateCard,
              borderRadius: '16px',
              border: `1px solid ${slateBorder}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'inline-block', backgroundColor: `${neonLime}20`, border: `1px solid ${neonLime}`, color: neonLime, fontSize: '0.75rem', fontWeight: 700, padding: '3px 10px', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
              Craft & Contemporary
            </div>
            <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: '#FFFFFF', margin: '0 0 6px 0', letterSpacing: '-0.5px' }}>
              {bizName}
            </h1>
            {touchpointValue && (
              <div style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
                {touchpointLabel}: <span style={{ color: neonLime, fontWeight: 700 }}>{touchpointValue}</span>
              </div>
            )}
          </header>

          {/* Segmented Pill Rating Selector */}
          <section
            style={{
              background: slateCard,
              borderRadius: '16px',
              border: `1px solid ${slateBorder}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
              padding: '22px 18px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#E2E8F0', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 14px 0' }}>
              {t.howWasVisit || 'Rate Your Experience'}
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
                      borderRadius: '8px',
                      border: isSelected ? `2px solid ${neonLime}` : `1px solid ${slateBorder}`,
                      background: isSelected ? neonLime : isHovered ? `${neonLime}30` : '#0B1120',
                      color: isSelected ? '#000000' : '#F8FAFC',
                      fontWeight: 800,
                      fontSize: '1.15rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {val}★
                  </button>
                );
              })}
            </div>
            <div style={{ fontSize: '0.92rem', fontWeight: 600, color: neonLime }}>
              {ratingLabel?.emoji} {ratingLabel?.text}
            </div>
          </section>

          {/* Topics Selector */}
          <section
            style={{
              background: slateCard,
              borderRadius: '16px',
              border: `1px solid ${slateBorder}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
              padding: '20px 18px',
            }}
          >
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#E2E8F0', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {t.whatStoodOut || 'What stood out?'}
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
                      borderRadius: '6px',
                      border: isSel ? `1px solid ${neonLime}` : `1px solid ${slateBorder}`,
                      background: isSel ? `${neonLime}20` : '#0B1120',
                      color: isSel ? neonLime : '#94A3B8',
                      fontSize: '0.85rem',
                      fontWeight: isSel ? 700 : 500,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
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

        {/* RIGHT COLUMN: Note, Review Suggestions & Neon Lime CTA */}
        <div className="vt-split-content">
          {/* Note Input */}
          <section
            style={{
              background: slateCard,
              borderRadius: '16px',
              border: `1px solid ${slateBorder}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
              padding: '20px 18px',
              marginBottom: '20px',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '8px' }}>
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
                borderRadius: '8px',
                border: `1px solid ${slateBorder}`,
                background: '#0B1120',
                color: '#FFFFFF',
                fontSize: '0.92rem',
                boxSizing: 'border-box',
              }}
            />
          </section>

          {/* AI Review Suggestions */}
          <section
            style={{
              background: slateCard,
              borderRadius: '16px',
              border: `1px solid ${slateBorder}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
              padding: '22px 18px',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#E2E8F0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {t.reviewIdeas || 'Generated Review Ideas'}
              </h3>
              <span style={{ fontSize: '0.75rem', color: neonLime, fontWeight: 700 }}>
                1-Tap Select
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
                    borderRadius: '8px',
                    border: isSelected ? `2px solid ${neonLime}` : `1px solid ${slateBorder}`,
                    background: isSelected ? `${neonLime}15` : '#0B1120',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: neonLime, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: neonLime }}>★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.92rem', color: '#E2E8F0', lineHeight: '1.45' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '8px', textAlign: 'right', fontSize: '0.78rem', color: neonLime, fontWeight: 700 }}>
                    {isSelected ? '✓ Selected →' : 'Use this review →'}
                  </div>
                </div>
              );
            })}

            {/* Neon Lime Google CTA */}
            <button
              type="button"
              onClick={() => onDirectGoogleHandoff(draftReview)}
              style={{
                width: '100%',
                padding: '16px',
                backgroundColor: neonLime,
                color: '#000000',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 900,
                fontSize: '1rem',
                cursor: 'pointer',
                marginTop: '14px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                boxShadow: '0 6px 20px rgba(132,204,22,0.3)',
                transition: 'transform 0.15s ease',
              }}
            >
              {t.copyAndOpenGoogle || 'Publish to Google Review ↗'}
            </button>
          </section>

          {/* Private feedback link */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.85rem', color: '#94A3B8' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Have direct notes for management? ') : (t.privatePromptBad || 'Tell us directly how we can improve: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: neonLime, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
