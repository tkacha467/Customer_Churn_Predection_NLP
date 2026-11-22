import React from 'react';

/**
 * F03 — Luxury Dining (restaurant_luxury_dining)
 * Haute cuisine, Michelin-inspired opulence.
 * Midnight velvet background (#0A0A0C), Champagne gold accents (#D4AF37),
 * Cormorant Garamond typography, and refined continuum slider rating.
 */
export default function RestaurantLuxuryDining({ templateData, journeyState }) {
  const {
    rating,
    setRating,
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

  const bizName = templateData?.businessName || 'L’Étoile Dining Room';
  const gold = '#D4AF37';
  const goldLight = '#F3E5AB';
  const midnight = '#0A0A0C';
  const velvetCard = '#141418';
  const velvetBorder = '#2A2A32';

  return (
    <div
      className="vt-luxury-dining"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '28px 16px',
        backgroundColor: midnight,
        minHeight: '100vh',
        color: '#E8E8E8',
        fontFamily: "'Cormorant Garamond', 'Didot', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      {/* Header */}
      <header style={{ textAlign: 'center', padding: '24px 0', borderBottom: `1px solid ${gold}33` }}>
        <div style={{ letterSpacing: '4px', textTransform: 'uppercase', fontSize: '0.75rem', color: gold, marginBottom: '8px', fontWeight: 600 }}>
          Exquisite Gastronomy
        </div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: 400, color: goldLight, margin: '0 0 8px 0', letterSpacing: '1px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.8rem', letterSpacing: '2px', color: '#888892', textTransform: 'uppercase' }}>
            {touchpointLabel}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Refined Slider Rating */}
      <section
        style={{
          background: velvetCard,
          border: `1px solid ${velvetBorder}`,
          borderRadius: '4px',
          padding: '28px 20px',
          margin: '24px 0',
          textAlign: 'center',
          boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
        }}
      >
        <h2 style={{ fontSize: '1.25rem', fontWeight: 400, color: goldLight, margin: '0 0 16px 0', letterSpacing: '1px' }}>
          {t.howWasVisit}
        </h2>

        {/* Rating Continuum Dial / Slider */}
        <div style={{ padding: '0 10px', marginBottom: '16px' }}>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            value={rating}
            onChange={(e) => setRating(parseInt(e.target.value, 10))}
            style={{
              width: '100%',
              accentColor: gold,
              cursor: 'pointer',
              height: '4px',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '0.75rem', color: '#888892', letterSpacing: '1px', textTransform: 'uppercase' }}>
            <span>1 — Fair</span>
            <span>2</span>
            <span>3 — Gracious</span>
            <span>4</span>
            <span style={{ color: gold, fontWeight: 700 }}>5 — Sublime</span>
          </div>
        </div>

        <div style={{ fontSize: '1.1rem', color: gold, marginTop: '8px' }}>
          {'★'.repeat(rating)}{'☆'.repeat(5 - rating)}
        </div>
        <div style={{ fontSize: '0.9rem', color: '#AAAAAF', marginTop: '4px', fontStyle: 'italic' }}>
          {ratingLabel?.text}
        </div>
      </section>

      {/* Culinary Highlights (Topics) */}
      <section
        style={{
          background: velvetCard,
          border: `1px solid ${velvetBorder}`,
          borderRadius: '4px',
          padding: '20px',
          marginBottom: '24px',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', color: goldLight, margin: '0 0 14px 0', letterSpacing: '0.5px' }}>
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
                  padding: '6px 14px',
                  borderRadius: '2px',
                  border: isSel ? `1px solid ${gold}` : `1px solid ${velvetBorder}`,
                  background: isSel ? `${gold}15` : '#0A0A0C',
                  color: isSel ? gold : '#AAAAAF',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  letterSpacing: '0.5px',
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
          <label style={{ display: 'block', fontSize: '0.75rem', letterSpacing: '1.5px', color: '#888892', textTransform: 'uppercase', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={t.notePlaceholder}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: '2px',
              border: `1px solid ${velvetBorder}`,
              background: '#0A0A0C',
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
          background: velvetCard,
          border: `1px solid ${velvetBorder}`,
          borderRadius: '4px',
          padding: '20px',
          marginBottom: '24px',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', color: goldLight, margin: '0 0 14px 0', letterSpacing: '0.5px' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              border: selectedIdeaId === idea.id ? `1px solid ${gold}` : `1px solid ${velvetBorder}`,
              borderRadius: '2px',
              background: selectedIdeaId === idea.id ? `${gold}0A` : '#0A0A0C',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', letterSpacing: '1.5px', color: gold, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#DDDDDF', lineHeight: '1.5', fontFamily: 'sans-serif' }}>
              {idea.text}
            </p>
          </div>
        ))}

        {/* CTA */}
        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            background: `linear-gradient(135deg, ${gold} 0%, #A67C1E 100%)`,
            color: '#0A0A0C',
            border: 'none',
            borderRadius: '2px',
            fontWeight: 700,
            fontSize: '0.92rem',
            letterSpacing: '1px',
            textTransform: 'uppercase',
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      {/* Private note link */}
      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#777782' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: gold, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
