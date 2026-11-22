import React from 'react';

/**
 * F02 — Modern Urban (restaurant_modern_urban)
 * Contemporary craft eatery / industrial urban dining.
 * Dark slate background (#0F172A), neon lime accents (#84CC16), segmented horizontal rating bar.
 */
export default function RestaurantModernUrban({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Urban Kitchen & Bar';
  const neonLime = '#84CC16';
  const slateDark = '#0F172A';
  const slateCard = '#1E293B';
  const slateBorder = '#334155';

  return (
    <div
      className="vt-modern-urban"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '20px 16px',
        backgroundColor: slateDark,
        minHeight: '100vh',
        color: '#F8FAFC',
        fontFamily: "'Syne', 'Plus Jakarta Sans', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      {/* Header */}
      <header style={{ textAlign: 'center', padding: '24px 0 16px' }}>
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
          borderRadius: '14px',
          border: `1px solid ${slateBorder}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#E2E8F0', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        {/* Segmented Pill Bar */}
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

      {/* Topics */}
      <section
        style={{
          background: slateCard,
          borderRadius: '14px',
          border: `1px solid ${slateBorder}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#E2E8F0', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
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
                  border: isSel ? `1px solid ${neonLime}` : `1px solid ${slateBorder}`,
                  background: isSel ? `${neonLime}20` : '#0B1120',
                  color: isSel ? neonLime : '#94A3B8',
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

        {/* Note */}
        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '6px',
              border: `1px solid ${slateBorder}`,
              background: '#0B1120',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Ideas */}
      <section
        style={{
          background: slateCard,
          borderRadius: '14px',
          border: `1px solid ${slateBorder}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#E2E8F0', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '8px',
              border: selectedIdeaId === idea.id ? `2px solid ${neonLime}` : `1px solid ${slateBorder}`,
              background: selectedIdeaId === idea.id ? `${neonLime}10` : '#0B1120',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: neonLime, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E2E8F0', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        {/* Action Button */}
        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: neonLime,
            color: '#000000',
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

      {/* Private feedback link */}
      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#94A3B8' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: neonLime, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
