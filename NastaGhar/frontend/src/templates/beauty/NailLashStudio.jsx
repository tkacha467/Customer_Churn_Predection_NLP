import React from 'react';

/**
 * B03 — High-Energy Nail & Lash Studio (beauty_nail_lash / salon_modern)
 * Visual Structure: Neon fuchsia (#EC4899), iridescent gloss (#FDF2F8), holographic violet (#8B5CF6).
 * Hero: Glossy nail polish bottle & lashes, sparkling marquee banner.
 * Rating: Heart gem rating scale (💖 glowing gems scaling on hover).
 * Topics: Pastel chip buttons with glitter border effects.
 * Suggestions: Glossy rounded bubble cards with neon gradient borders.
 */
export default function NailLashStudio({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Velvet Gloss Nail & Lash Bar';
  const fuchsia = '#EC4899';
  const fuchsiaDark = '#BE185D';
  const violet = '#8B5CF6';
  const bg = '#FDF2F8';

  return (
    <div
      className="vt-nail-lash"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#374151',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}
    >
      <header style={{ textAlign: 'center', padding: '20px 0 16px' }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '4px' }}>💅 👁️ ✨</div>
        <div style={{ display: 'inline-block', backgroundColor: `${fuchsia}18`, border: `1px solid ${fuchsia}40`, color: fuchsiaDark, fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '20px', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
          Lash Extensions & Nail Artistry
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: fuchsiaDark, margin: '0 0 4px 0', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: fuchsiaDark, fontWeight: 700 }}>
            {touchpointLabel || 'Artist / Station'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Heart Gem Rating Scale */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '24px',
          border: `2px solid ${fuchsia}30`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 8px 24px rgba(236,72,153,0.12)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1F2937', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '10px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val <= (hoverRating || rating);
            return (
              <button
                key={val}
                type="button"
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(val)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '2.4rem',
                  transform: isSel ? 'scale(1.2)' : 'scale(0.95)',
                  filter: isSel ? 'drop-shadow(0 2px 8px rgba(236,72,153,0.5))' : 'grayscale(90%) opacity(40%)',
                  transition: 'all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1)',
                }}
              >
                💖
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: 800, color: fuchsiaDark }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${fuchsia}25`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1F2937', margin: '0 0 12px 0' }}>
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
                  border: isSel ? `2px solid ${fuchsia}` : '1px solid #FBCFE8',
                  background: isSel ? `linear-gradient(135deg, ${fuchsia} 0%, ${violet} 100%)` : '#FFF5F8',
                  color: isSel ? '#FFFFFF' : '#4B5563',
                  fontSize: '0.88rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  transition: 'transform 0.15s ease',
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
            placeholder={t.notePlaceholder}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '12px',
              border: '1px solid #FBCFE8',
              background: '#FFF5F8',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Ideas */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${fuchsia}25`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1F2937', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '14px',
              border: selectedIdeaId === idea.id ? `2px solid ${fuchsia}` : '1px solid #FCE7F3',
              background: selectedIdeaId === idea.id ? `${fuchsia}10` : '#FAFAFA',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 900, color: fuchsiaDark, textTransform: 'uppercase', marginBottom: '4px' }}>
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
            background: `linear-gradient(135deg, ${fuchsia} 0%, ${violet} 100%)`,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '14px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 6px 18px rgba(236,72,153,0.3)',
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
          style={{ background: 'none', border: 'none', color: fuchsiaDark, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
