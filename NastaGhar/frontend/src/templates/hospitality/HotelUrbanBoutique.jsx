import React from 'react';

/**
 * T02 — Boutique Urban Lifestyle Pod (hotel_urban_boutique / hotel_modern)
 * Visual Structure: Concrete charcoal (#18181B), electric turquoise (#14B8A6).
 * Hero: Modern keycard & rooftop pool, loft lifestyle banner.
 * Rating: Minimalist horizontal dot matrix rating (1 to 5 illuminated circles).
 * Topics: Neon-accented pill tags.
 * Suggestions: High-contrast modular cards with clean teal borders.
 */
export default function HotelUrbanBoutique({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Komorebi Urban Loft & Pods';
  const teal = '#14B8A6';
  const charcoal = '#18181B';
  const cardBg = '#27272A';
  const border = '#3F3F46';

  return (
    <div
      className="vt-urban-boutique"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: charcoal,
        minHeight: '100vh',
        color: '#F4F4F5',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}
    >
      <header style={{ textAlign: 'center', padding: '20px 0 16px' }}>
        <div style={{ fontSize: '2.2rem', marginBottom: '4px' }}>🏙️ 🏊 🍸</div>
        <div style={{ display: 'inline-block', backgroundColor: `${teal}20`, border: `1px solid ${teal}`, color: teal, fontSize: '0.75rem', fontWeight: 800, padding: '3px 10px', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>
          Urban Loft & Rooftop Lounge
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: teal, fontWeight: 700 }}>
            {touchpointLabel || 'Pod / Suite'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Illuminated Dot Matrix Rating */}
      <section
        style={{
          background: cardBg,
          borderRadius: '12px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: `0 8px 24px rgba(20,184,166,0.1)`,
        }}
      >
        <h2 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#E4E4E7', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginBottom: '12px' }}>
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
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  border: isExact ? `2px solid ${teal}` : `1px solid ${border}`,
                  background: isExact ? teal : isSel ? `${teal}30` : '#18181B',
                  color: isExact ? '#000000' : isSel ? teal : '#71717A',
                  fontSize: '1.1rem',
                  fontWeight: 900,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  boxShadow: isExact ? `0 0 12px ${teal}` : 'none',
                }}
              >
                {val}
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 800, color: teal }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: cardBg,
          borderRadius: '12px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#E4E4E7', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
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
                  border: isSel ? `1px solid ${teal}` : `1px solid ${border}`,
                  background: isSel ? `${teal}20` : '#18181B',
                  color: isSel ? teal : '#A1A1AA',
                  fontSize: '0.85rem',
                  fontWeight: 700,
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
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#A1A1AA', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              border: `1px solid ${border}`,
              background: '#18181B',
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
          background: cardBg,
          borderRadius: '12px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#E4E4E7', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '6px',
              border: selectedIdeaId === idea.id ? `2px solid ${teal}` : `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${teal}10` : '#18181B',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: teal, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E4E4E7', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: teal,
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

      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#71717A' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: teal, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
