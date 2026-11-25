import React from 'react';

/**
 * R04 — Organic Farmers Market & Pantry (retail_organic_pantry / retail_pantry)
 * Visual Structure: Harvest green (#15803D), kraft paper brown (#78350F), sunshine yellow (#CA8A04).
 * Hero: Wicker basket & farm harvest, market chalkboard banner.
 * Rating: Fresh harvest apple rating scale (🍏 crisp green apple buttons).
 * Topics: Wooden crate-style tags.
 * Suggestions: Chalkboard-style dark green cards with chalk lettering.
 */
export default function RetailOrganicPantry({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Green Meadow Organic Market';
  const green = '#15803D';
  const greenDark = '#14532D';
  const kraft = '#FEFCE8';
  const border = '#BBF7D0';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Great collection, perfect fit and helpful styling advice! 🛍️';

  return (
    <div className="vt-page-container vt-organic-pantry" style={{
        padding: '24px 16px',
        backgroundColor: kraft,
        minHeight: '100vh',
        color: '#1E3A1E',
        fontFamily: "'Outfit', 'Plus Jakarta Sans', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '20px 0 16px', borderBottom: `2px solid ${border}` }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '4px' }}>🍎 🥕 🌾</div>
        <div style={{ display: 'inline-block', backgroundColor: '#DCFCE7', color: greenDark, fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '16px', textTransform: 'uppercase', marginBottom: '6px' }}>
          Farm Direct & Zero Waste Pantry
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: greenDark, margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: green, fontWeight: 700 }}>
            {touchpointLabel || 'Checkout Counter'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Fresh Harvest Apple Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '18px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 6px 20px rgba(21,128,61,0.08)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: greenDark, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.4rem', marginBottom: '10px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val <= (hoverRating || rating);
            return (
              <span
                key={val}
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(val)}
                style={{
                  cursor: 'pointer',
                  transform: isSel ? 'scale(1.2)' : 'scale(0.95)',
                  filter: isSel ? 'drop-shadow(0 2px 6px rgba(21,128,61,0.4))' : 'grayscale(100%) opacity(30%)',
                  transition: 'all 0.15s ease',
                }}
              >
                🍏
              </span>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 800, color: green }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Crate Style Tags */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '18px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: greenDark, margin: '0 0 12px 0' }}>
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
                  borderRadius: '12px',
                  border: isSel ? `2px solid ${green}` : '1px solid #BBF7D0',
                  background: isSel ? green : '#F0FDF4',
                  color: isSel ? '#FFFFFF' : '#166534',
                  fontSize: '0.85rem',
                  fontWeight: 800,
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#166534', marginBottom: '6px' }}>
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
              background: '#F0FDF4',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Chalkboard Suggestions */}
      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content"><section
        style={{
          background: '#FFFFFF',
          borderRadius: '18px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: greenDark, margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '10px',
              border: selectedIdeaId === idea.id ? `2px solid ${green}` : '1px solid #DCFCE7',
              background: selectedIdeaId === idea.id ? '#DCFCE7' : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 900, color: green, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#1E3A1E', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: green,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '12px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(21,128,61,0.25)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#15803D' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: greenDark, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
