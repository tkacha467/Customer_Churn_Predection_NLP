import React from 'react';

/**
 * G01–G05 — Fitness, Gym & Athletic Club (fitness_gym / fitness)
 * Dark athletic aesthetic (#0F172A), high-energy cyan (#06B6D4) and orange accents,
 * trainer/locker touchpoint.
 */
export default function FitnessEnergy({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Apex Performance Club';
  const cyan = '#06B6D4';
  const darkBg = '#0F172A';
  const cardBg = '#1E293B';
  const border = '#334155';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Incredible coaching, motivating energy and pristine facility! 💪';

  return (
    <div className="vt-page-container vt-fitness" style={{
        padding: '24px 16px',
        backgroundColor: darkBg,
        minHeight: '100vh',
        color: '#F8FAFC',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '24px 0 16px' }}>
        <div style={{ fontSize: '2rem', marginBottom: '6px' }}>⚡ 🏋️ ⏱️</div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 6px 0', textTransform: 'uppercase', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#94A3B8', fontWeight: 600 }}>
          Strength, Conditioning & Athletic Wellness
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: cyan, fontWeight: 700 }}>
            {touchpointLabel || 'Trainer / Zone'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Rating */}
      <section
        style={{
          background: cardBg,
          borderRadius: '14px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 800, color: '#E2E8F0', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 14px 0' }}>
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
                color: star <= (hoverRating || rating) ? cyan : '#475569',
                transition: 'transform 0.15s ease',
                transform: star <= (hoverRating || rating) ? 'scale(1.15)' : 'scale(1)',
              }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 800, color: cyan }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: cardBg,
          borderRadius: '14px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#E2E8F0', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
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
                  borderRadius: '6px',
                  border: isSel ? `1px solid ${cyan}` : `1px solid ${border}`,
                  background: isSel ? `${cyan}20` : '#0B1120',
                  color: isSel ? cyan : '#94A3B8',
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
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '6px',
              border: `1px solid ${border}`,
              background: '#0B1120',
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
          borderRadius: '14px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#E2E8F0', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '8px',
              border: selectedIdeaId === idea.id ? `2px solid ${cyan}` : `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${cyan}10` : '#0B1120',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: cyan, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
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
            backgroundColor: cyan,
            color: '#0B1120',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
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
          style={{ background: 'none', border: 'none', color: cyan, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
