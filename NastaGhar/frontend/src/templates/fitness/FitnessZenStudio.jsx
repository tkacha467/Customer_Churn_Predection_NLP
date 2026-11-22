import React from 'react';

/**
 * G02 — Zen Yoga, Pilates & Mindful Movement (fitness_zen_studio / fitness_yoga)
 * Visual Structure: Lavender (#581C87), soft lilac (#FAF5FF), pale seafoam (#A7F3D0).
 * Hero: Yoga lotus pose & singing bowl, mindful studio banner.
 * Rating: Calming moon phase scale (🌑 to 🌕 luminous full moon).
 * Topics: Soft pastel oval pills.
 * Suggestions: Gentle floating cards with soothing lavender borders.
 */
export default function FitnessZenStudio({ templateData, journeyState }) {
  const {
    rating,
    setRating,
    hoverRating,
    setHoverRating,
    ratingLabel,
    availableTopics,
    selectedTopics,
    toggleTopic,
    personalNote,
    setPersonalNote,
    touchpointLabel,
    touchpointValue,
    ideas,
    selectedIdeaId,
    onSelectIdea,
    draftReview,
    onDirectGoogleHandoff,
    onOpenPrivateFeedback,
    t,
  } = journeyState;

  const bizName = templateData?.businessName || 'Prana Flow Yoga & Pilates Shala';
  const purple = '#581C87';
  const lilac = '#FAF5FF';
  const border = '#E9D5FF';

  const MOON_PHASES = ['🌑', '🌒', '🌓', '🌔', '🌕'];

  return (
    <div
      className="vt-zen-studio"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: lilac,
        minHeight: '100vh',
        color: '#3B0764',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}
    >
      <header style={{ textAlign: 'center', padding: '20px 0 16px', borderBottom: `1px solid ${border}` }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '4px' }}>🧘 🌸 🪷</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '2px', textTransform: 'uppercase', color: purple, fontWeight: 700, marginBottom: '4px' }}>
          Mindful Movement, Breath & Sound
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, color: purple, margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: '#7E22CE', fontWeight: 600 }}>
            {touchpointLabel || 'Studio / Mat'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Luminous Moon Phase Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '24px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 6px 20px rgba(88,28,135,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: purple, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.4rem', marginBottom: '8px' }}>
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
                  filter: isSel ? 'drop-shadow(0 2px 6px rgba(88,28,135,0.4))' : 'grayscale(100%) opacity(30%)',
                  transition: 'all 0.15s ease',
                }}
              >
                {MOON_PHASES[val - 1]}
              </span>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: purple }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: purple, margin: '0 0 12px 0' }}>
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
                  borderRadius: '20px',
                  border: isSel ? `2px solid ${purple}` : '1px solid #E9D5FF',
                  background: isSel ? purple : '#FAF5FF',
                  color: isSel ? '#FFFFFF' : '#6B21A8',
                  fontSize: '0.85rem',
                  fontWeight: 600,
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#6B21A8', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={t.notePlaceholder}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '10px',
              border: `1px solid ${border}`,
              background: lilac,
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Floating Suggestions */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: purple, margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '12px',
              border: selectedIdeaId === idea.id ? `2px solid ${purple}` : '1px solid #F3E8FF',
              background: selectedIdeaId === idea.id ? '#F3E8FF' : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: purple, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#3B0764', lineHeight: '1.45' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: purple,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '12px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(88,28,135,0.25)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#7E22CE' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: purple, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
