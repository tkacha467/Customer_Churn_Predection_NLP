import React from 'react';

/**
 * R02 — Urban Streetwear & Sneaker Drop (retail_streetwear_drop / retail_modern)
 * Visual Structure: Pitch black (#0A0A0A), safety hazard orange (#F97316), brutalist typography.
 * Hero: Sneaker box & tape drop banner, barcode aesthetic.
 * Rating: Stamped hype box meter (1 to 5 flame/lightning buttons).
 * Topics: Caution-stripe styled tags.
 * Suggestions: Streetwear receipt-style cards with monospace typography.
 */
export default function RetailStreetwearDrop({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Kicks & Thread Drop Lab';
  const black = '#0A0A0A';
  const orange = '#F97316';
  const darkCard = '#171717';
  const border = '#262626';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Great collection, perfect fit and helpful styling advice! 🛍️';

  return (
    <div className="vt-page-container vt-streetwear-drop" style={{
        padding: '24px 16px',
        backgroundColor: black,
        minHeight: '100vh',
        color: '#FAFAFA',
        fontFamily: "'Space Grotesk', 'Syne', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ padding: '20px 0 16px', borderBottom: `2px dashed ${orange}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>👟 🧢 ⚡</span>
          <span style={{ backgroundColor: orange, color: '#000000', fontSize: '0.75rem', fontWeight: 900, padding: '2px 8px', borderRadius: '2px', textTransform: 'uppercase' }}>
            DROP_VERIFIED
          </span>
        </div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.8rem', color: '#A3A3A3', fontFamily: 'monospace' }}>
            REGISTER // [{touchpointLabel || 'Terminal'}: {touchpointValue}]
          </div>
        )}
      </header>

      {/* Hype Box Meter Rating */}
      <section
        style={{
          background: darkCard,
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '0.95rem', fontWeight: 900, textTransform: 'uppercase', color: '#E5E5E5', letterSpacing: '1px', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '12px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val <= (hoverRating || rating);
            const isExact = val === rating;
            return (
              <button
                key={val}
                type="button"
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(val)}
                style={{
                  padding: '12px 0',
                  border: isExact ? `2px solid ${orange}` : `1px solid ${border}`,
                  background: isExact ? orange : isSel ? `${orange}25` : '#0A0A0A',
                  color: isExact ? '#000000' : isSel ? orange : '#737373',
                  fontWeight: 900,
                  fontSize: '1.15rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  borderRadius: '2px',
                }}
              >
                {val}🔥
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 800, color: orange }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Caution Stripe Tags */}
      <section
        style={{
          background: darkCard,
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 900, textTransform: 'uppercase', color: '#E5E5E5', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
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
                  padding: '8px 14px',
                  border: isSel ? `1px solid ${orange}` : `1px solid ${border}`,
                  background: isSel ? `${orange}20` : '#0A0A0A',
                  color: isSel ? orange : '#A3A3A3',
                  fontSize: '0.85rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  borderRadius: '2px',
                  textTransform: 'uppercase',
                }}
              >
                <span>{top.icon}</span>
                <span>{top.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: '#A3A3A3', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              border: `1px solid ${border}`,
              background: '#0A0A0A',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              borderRadius: '2px',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Streetwear Monospace Cards */}
      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content"><section
        style={{
          background: darkCard,
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 900, textTransform: 'uppercase', color: '#E5E5E5', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${orange}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${orange}10` : '#0A0A0A',
              marginBottom: '10px',
              cursor: 'pointer',
              borderRadius: '2px',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 900, color: orange, textTransform: 'uppercase', marginBottom: '4px', fontFamily: 'monospace' }}>
              TAG // {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E5E5E5', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: orange,
            color: '#000000',
            border: 'none',
            borderRadius: '2px',
            fontWeight: 900,
            fontSize: '1rem',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#737373' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: orange, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
