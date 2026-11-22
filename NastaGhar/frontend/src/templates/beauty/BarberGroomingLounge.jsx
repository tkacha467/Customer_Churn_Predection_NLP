import React from 'react';

/**
 * B02 — Modern Barbershop & Grooming Lounge (beauty_barber_lounge / salon_premium)
 * Visual Structure: Matte carbon black (#121212), warm bourbon amber (#D97706), brushed steel (#E5E7EB).
 * Hero: Barber pole stripe accent, vintage gentleman grooming header.
 * Rating: Segmented industrial blade badge rating (1 to 5 steel badges).
 * Topics: Stamped badge tags (Fade & Taper, Hot Towel Shave, Beard Sculpt, Haircut).
 * Suggestions: Dark textured cards with amber stitching borders.
 */
export default function BarberGroomingLounge({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'The Iron & Razor Barbershop';
  const carbon = '#121212';
  const amber = '#D97706';
  const steel = '#262626';
  const border = '#404040';

  return (
    <div
      className="vt-barber-lounge"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: carbon,
        minHeight: '100vh',
        color: '#E5E5E5',
        fontFamily: "'Barlow Condensed', 'Oswald', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      {/* Barber Pole & Crest Header */}
      <header style={{ textAlign: 'center', padding: '20px 0 16px', borderBottom: `2px solid ${amber}` }}>
        <div style={{ fontSize: '2.2rem', marginBottom: '6px' }}>💈 ✂️ 🪒</div>
        <div style={{ fontSize: '0.8rem', letterSpacing: '2px', textTransform: 'uppercase', color: amber, fontWeight: 800, marginBottom: '4px' }}>
          Classic Cuts & Hot Towel Shaves
        </div>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: '#A3A3A3', fontWeight: 700 }}>
            {touchpointLabel || 'Barber Chair'}: <span style={{ color: amber }}>{touchpointValue}</span>
          </div>
        )}
      </header>

      {/* Segmented Industrial Blade Badge Rating */}
      <section
        style={{
          background: steel,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '22px 0',
          textAlign: 'center',
          boxShadow: '0 6px 20px rgba(0,0,0,0.6)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#F5F5F5', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '12px' }}>
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
                  padding: '12px 0',
                  borderRadius: '4px',
                  border: isExact ? `2px solid ${amber}` : `1px solid ${border}`,
                  background: isExact ? amber : isSel ? `${amber}30` : '#171717',
                  color: isExact ? '#000000' : isSel ? amber : '#A3A3A3',
                  fontWeight: 900,
                  fontSize: '1.2rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  textTransform: 'uppercase',
                }}
              >
                {val}★
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: 800, color: amber, letterSpacing: '0.5px' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Stamped Badge Tags */}
      <section
        style={{
          background: steel,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#F5F5F5', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
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
                  borderRadius: '4px',
                  border: isSel ? `2px solid ${amber}` : `1px solid ${border}`,
                  background: isSel ? `${amber}25` : '#171717',
                  color: isSel ? amber : '#A3A3A3',
                  fontSize: '0.88rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
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
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 800, color: '#A3A3A3', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '4px',
              border: `1px solid ${border}`,
              background: '#171717',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Dark Textured Suggestion Cards */}
      <section
        style={{
          background: steel,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#F5F5F5', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              border: selectedIdeaId === idea.id ? `2px solid ${amber}` : `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${amber}12` : '#171717',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 900, color: amber, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#D4D4D4', lineHeight: '1.4', fontFamily: 'sans-serif' }}>
              {idea.text}
            </p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: amber,
            color: '#000000',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 900,
            fontSize: '1.1rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#737373' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: amber, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
