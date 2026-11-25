import React from 'react';

/**
 * B01–B05 — Salon, Studio & Wellness (salon_classic / salon_premium)
 * Rose gold (#EC4899), soft blush lavender (#FDF2F8), stylist chair touchpoint,
 * salon and beauty terminology.
 */
export default function SalonWellness({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Aura Hair & Beauty Studio';
  const rose = '#DB2777';
  const blush = '#FDF2F8';
  const accent = '#EC4899';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Loved the haircut, styling and relaxing service! ✨';

  return (
    <div className="vt-page-container vt-salon" style={{
        padding: '24px 16px',
        backgroundColor: blush,
        minHeight: '100vh',
        color: '#374151',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '24px 0 16px' }}>
        <div style={{ fontSize: '2rem', marginBottom: '6px' }}>✂️ 💅 ✨</div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: rose, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#6B7280' }}>
          Hair Styling, Aesthetics & Wellness Spa
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: rose, fontWeight: 700 }}>
            {touchpointLabel || 'Stylist / Chair'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${rose}25`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(219,39,119,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1F2937', margin: '0 0 14px 0' }}>
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
                color: star <= (hoverRating || rating) ? accent : '#E5E7EB',
                transition: 'transform 0.15s ease',
                transform: star <= (hoverRating || rating) ? 'scale(1.15)' : 'scale(1)',
              }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: rose }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${rose}25`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1F2937', margin: '0 0 12px 0' }}>
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
                  borderRadius: '16px',
                  border: isSel ? `2px solid ${rose}` : '1px solid #E5E7EB',
                  background: isSel ? `${rose}15` : '#F9FAFB',
                  color: isSel ? rose : '#4B5563',
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#6B7280', marginBottom: '6px' }}>
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
              borderRadius: '10px',
              border: '1px solid #E5E7EB',
              background: '#F9FAFB',
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
          borderRadius: '20px',
          border: `1px solid ${rose}25`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1F2937', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '12px',
              border: selectedIdeaId === idea.id ? `2px solid ${rose}` : '1px solid #F3F4F6',
              background: selectedIdeaId === idea.id ? `${rose}08` : '#FAFAFA',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: rose, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#374151', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: rose,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '12px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(219,39,119,0.3)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#6B7280' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: rose, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
