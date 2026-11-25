import React from 'react';

/**
 * B05 — Bridal & Glamour Makeup Lounge (beauty_bridal_glam / salon_luxe)
 * Visual Structure: Rose gold (#BE185D), champagne shimmer (#FEF3C7), ivory silk (#FFFBEB).
 * Hero: Tiara and glam mirror, golden foil frame effect.
 * Rating: Starburst diamond rating scale (💎 sparkling diamond icons).
 * Topics: Elegant silk pill badges.
 * Suggestions: Ivory satin cards with delicate rose-gold borders.
 */
export default function BridalGlamStudio({ templateData, journeyState = {} }) {
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
    touchpointLabel = 'Table / Station',
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

  const bizName = templateData?.businessName || 'Maharani Bridal & Couture Glam';
  const roseGold = '#BE185D';
  const goldAccent = '#D97706';
  const ivory = '#FFFBEB';
  const border = '#FDE68A';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Loved the haircut, styling and relaxing service! ✨';

  return (
    <div className="vt-page-container vt-bridal-glam" style={{
        padding: '24px 16px',
        backgroundColor: ivory,
        minHeight: '100vh',
        color: '#374151',
        fontFamily: "'Playfair Display', 'Cormorant Garamond', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '24px 0 16px', borderBottom: `2px double ${border}` }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '6px' }}>👑 💄 ✨</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '2.5px', textTransform: 'uppercase', color: goldAccent, fontWeight: 700, marginBottom: '4px' }}>
          Couture Bridal & Trousseau Glamour
        </div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: 700, color: roseGold, margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: goldAccent, fontWeight: 600, fontFamily: 'sans-serif' }}>
            {touchpointLabel || 'Bridal Suite'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Starburst Diamond Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 6px 20px rgba(190,24,93,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.15rem', color: roseGold, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', fontSize: '2.4rem', cursor: 'pointer', marginBottom: '8px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val <= (hoverRating || rating);
            return (
              <span
                key={val}
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(val)}
                style={{
                  transform: isSel ? 'scale(1.2) translateY(-2px)' : 'scale(1)',
                  filter: isSel ? 'drop-shadow(0 2px 6px rgba(217,119,6,0.4))' : 'grayscale(100%) opacity(30%)',
                  transition: 'all 0.15s ease',
                }}
              >
                💎
              </span>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: roseGold, fontFamily: 'sans-serif' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', color: roseGold, margin: '0 0 12px 0', fontFamily: 'serif' }}>
          {t.whatStoodOut}
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
                  padding: '8px 16px',
                  borderRadius: '24px',
                  border: isSel ? `2px solid ${roseGold}` : `1px solid ${border}`,
                  background: isSel ? roseGold : ivory,
                  color: isSel ? '#FFFFFF' : '#4B5563',
                  fontSize: '0.85rem',
                  fontWeight: isSel ? 600 : 500,
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

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#6B7280', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={placeholder}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: `1px solid ${border}`,
              background: ivory,
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content">{/* Ideas */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', color: roseGold, margin: '0 0 12px 0', fontFamily: 'serif' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '10px',
              border: selectedIdeaId === idea.id ? `2px solid ${roseGold}` : '1px solid #F3F4F6',
              background: selectedIdeaId === idea.id ? `${roseGold}08` : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: goldAccent, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#374151', lineHeight: '1.45' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            background: `linear-gradient(135deg, ${roseGold} 0%, ${goldAccent} 100%)`,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(190,24,93,0.25)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#6B7280', fontFamily: 'sans-serif' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: roseGold, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
