import React from 'react';

/**
 * T01–T05 — Hospitality & Hotel Stay (hotel_classic / hotel_premium)
 * Deep navy (#1E293B) with warm amber gold (#EAB308), room number touchpoint,
 * concierge and hospitality terminology.
 */
export default function HotelHospitality({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Grand Heritage Hotel & Suites';
  const navy = '#0F172A';
  const gold = '#EAB308';
  const cardBg = '#1E293B';
  const border = '#334155';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Beautiful room, exceptional hospitality and wonderful breakfast! 🏨';

  return (
    <div className="vt-page-container vt-hospitality" style={{
        padding: '24px 16px',
        backgroundColor: navy,
        minHeight: '100vh',
        color: '#F8FAFC',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '24px 0 16px' }}>
        <div style={{ fontSize: '2rem', marginBottom: '6px' }}>🏨 ⭐ 🛎️</div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#FFFFFF', margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#94A3B8' }}>
          Hospitality, Comfort & Guest Services
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: gold, fontWeight: 700 }}>
            {touchpointLabel || 'Room / Suite'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Rating */}
      <section
        style={{
          background: cardBg,
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#E2E8F0', margin: '0 0 14px 0' }}>
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
                color: star <= (hoverRating || rating) ? gold : '#475569',
                transition: 'transform 0.15s ease',
                transform: star <= (hoverRating || rating) ? 'scale(1.15)' : 'scale(1)',
              }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: gold }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: cardBg,
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#E2E8F0', margin: '0 0 12px 0' }}>
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
                  border: isSel ? `1px solid ${gold}` : `1px solid ${border}`,
                  background: isSel ? `${gold}20` : '#0F172A',
                  color: isSel ? gold : '#CBD5E1',
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#94A3B8', marginBottom: '6px' }}>
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
              background: '#0F172A',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content">{/* Ideas */}
      <section
        style={{
          background: cardBg,
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#E2E8F0', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '8px',
              border: selectedIdeaId === idea.id ? `2px solid ${gold}` : `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${gold}10` : '#0F172A',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: gold, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E2E8F0', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: gold,
            color: '#0F172A',
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

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#94A3B8' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: gold, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
