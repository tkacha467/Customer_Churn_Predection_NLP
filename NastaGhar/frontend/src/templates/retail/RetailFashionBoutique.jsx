import React from 'react';

/**
 * R01 — Luxury Fashion Boutique & Atelier (retail_fashion_boutique / retail_classic)
 * Visual Structure: Haute couture monochrome (#000000 & #FFFFFF), champagne gold (#D4AF37).
 * Hero: Minimalist atelier runway header, lookbook editorial style.
 * Rating: Fine-line serif star scale with Roman numerals (I, II, III, IV, V).
 * Topics: Minimalist luxury tag badges with thin hairline borders.
 * Suggestions: Lookbook editorial cards with serif quotes.
 */
export default function RetailFashionBoutique({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Maison de Mode Atelier';
  const black = '#000000';
  const gold = '#D4AF37';
  const border = '#E5E5E5';

  const ROMAN_NUMERALS = ['I', 'II', 'III', 'IV', 'V'];

  return (
    <div
      className="vt-retail-fashion"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '28px 16px',
        backgroundColor: '#FFFFFF',
        minHeight: '100vh',
        color: '#171717',
        fontFamily: "'Didot', 'Playfair Display', 'Cormorant Garamond', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      <header style={{ textAlign: 'center', padding: '24px 0 20px', borderBottom: '1px solid #171717' }}>
        <div style={{ letterSpacing: '4px', textTransform: 'uppercase', fontSize: '0.72rem', color: '#737373', marginBottom: '8px' }}>
          Atelier & Ready-to-Wear
        </div>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 400, color: black, margin: '0 0 6px 0', letterSpacing: '2px', textTransform: 'uppercase' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.78rem', letterSpacing: '2px', color: gold, textTransform: 'uppercase', marginTop: '6px' }}>
            {touchpointLabel || 'Fitting Suite'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Roman Numeral Editorial Rating */}
      <section
        style={{
          border: '1px solid #E5E5E5',
          padding: '28px 20px',
          margin: '24px 0',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 400, letterSpacing: '2px', textTransform: 'uppercase', color: '#525252', margin: '0 0 16px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '14px' }}>
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
                  width: '50px',
                  height: '50px',
                  border: isExact ? `1px solid ${black}` : '1px solid #D4D4D4',
                  background: isExact ? black : isSel ? '#F5F5F5' : '#FFFFFF',
                  color: isExact ? '#FFFFFF' : '#171717',
                  fontSize: '1rem',
                  fontFamily: 'serif',
                  letterSpacing: '1px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {ROMAN_NUMERALS[val - 1]}
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.9rem', color: gold, fontStyle: 'italic', letterSpacing: '1px' }}>
          {ratingLabel?.text}
        </div>
      </section>

      {/* Hairline Topics */}
      <section
        style={{
          border: '1px solid #E5E5E5',
          padding: '20px',
          marginBottom: '24px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '0.85rem', fontWeight: 600, letterSpacing: '2px', textTransform: 'uppercase', color: '#171717', margin: '0 0 14px 0' }}>
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
                  padding: '7px 14px',
                  border: isSel ? `1px solid ${black}` : '1px solid #E5E5E5',
                  background: isSel ? black : '#FFFFFF',
                  color: isSel ? '#FFFFFF' : '#525252',
                  fontSize: '0.82rem',
                  letterSpacing: '0.5px',
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
          <label style={{ display: 'block', fontSize: '0.75rem', letterSpacing: '1.5px', color: '#737373', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              border: '1px solid #E5E5E5',
              background: '#FAFAFA',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Editorial Suggestions */}
      <section
        style={{
          border: '1px solid #E5E5E5',
          padding: '20px',
          marginBottom: '24px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '0.85rem', fontWeight: 600, letterSpacing: '2px', textTransform: 'uppercase', color: '#171717', margin: '0 0 14px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              border: selectedIdeaId === idea.id ? `1px solid ${black}` : '1px solid #E5E5E5',
              background: selectedIdeaId === idea.id ? '#F5F5F5' : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', letterSpacing: '2px', color: gold, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#262626', lineHeight: '1.45', fontFamily: 'serif' }}>
              "{idea.text}"
            </p>
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
            fontSize: '0.9rem',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            fontWeight: 700,
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#737373', fontFamily: 'sans-serif' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: black, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
