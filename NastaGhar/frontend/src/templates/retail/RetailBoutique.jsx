import React from 'react';

/**
 * R01–R05 — Retail & Boutique Store (retail_boutique / retail_general)
 * Clean minimalist monochrome (#FAFAFA & #18181B), sharp accents, receipt / counter touchpoint.
 */
export default function RetailBoutique({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Atelier & Co.';
  const black = '#18181B';
  const bg = '#FAFAFA';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Great collection, perfect fit and helpful styling advice! 🛍️';

  return (
    <div className="vt-page-container vt-retail" style={{
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#18181B',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '24px 0 16px' }}>
        <div style={{ fontSize: '2rem', marginBottom: '6px' }}>🛍️ 🏷️ ✨</div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: black, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#71717A' }}>
          Curated Apparel, Accessories & Goods
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: black, fontWeight: 700 }}>
            {touchpointLabel || 'Receipt / Counter'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E4E4E7',
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: black, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.5rem', cursor: 'pointer', marginBottom: '8px' }}>
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              onClick={() => setRating(star)}
              style={{
                color: star <= (hoverRating || rating) ? '#F59E0B' : '#E4E4E7',
                transition: 'transform 0.15s ease',
                transform: star <= (hoverRating || rating) ? 'scale(1.15)' : 'scale(1)',
              }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#3F3F46' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E4E4E7',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: black, margin: '0 0 12px 0' }}>
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
                  borderRadius: '8px',
                  border: isSel ? `2px solid ${black}` : '1px solid #E4E4E7',
                  background: isSel ? black : '#F4F4F5',
                  color: isSel ? '#FFFFFF' : '#3F3F46',
                  fontSize: '0.85rem',
                  fontWeight: isSel ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                <span>{top.icon}</span>
                <span>{top.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#71717A', marginBottom: '6px' }}>
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
              border: '1px solid #E4E4E7',
              background: '#F4F4F5',
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
          borderRadius: '12px',
          border: '1px solid #E4E4E7',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: black, margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '8px',
              border: selectedIdeaId === idea.id ? `2px solid ${black}` : '1px solid #E4E4E7',
              background: selectedIdeaId === idea.id ? '#F4F4F5' : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: black, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#27272A', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: black,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#71717A' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: black, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
