import React from 'react';

/**
 * T01 — Grand Heritage Hotel & Resort (hotel_heritage_resort / hotel_classic)
 * Visual Structure: Imperial navy (#1E1B4B), regal antique gold (#CA8A04), ivory (#FDFBF7).
 * Hero: Grand palace crest, concierge welcome banner.
 * Rating: Golden imperial medallion rating scale.
 * Topics: Brass luggage-tag styled chips.
 * Suggestions: Gold-embossed parchment cards with royal gold trim.
 */
export default function HotelHeritageResort({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'The Raj Mahal Palace & Spa';
  const navy = '#1E1B4B';
  const gold = '#CA8A04';
  const goldLight = '#FEF08A';
  const ivory = '#FDFBF7';
  const border = '#E2D9C8';

  return (
    <div
      className="vt-heritage-resort"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: ivory,
        minHeight: '100vh',
        color: '#1E1B4B',
        fontFamily: "'Cinzel', 'Playfair Display', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      <header style={{ textAlign: 'center', padding: '24px 0 16px', borderBottom: `2px double ${gold}` }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '6px' }}>🏰 🛎️ 👑</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '3px', textTransform: 'uppercase', color: gold, fontWeight: 700, marginBottom: '4px' }}>
          Palatial Luxury & Royal Hospitality
        </div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: 700, color: navy, margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: gold, fontWeight: 600, fontFamily: 'sans-serif' }}>
            {touchpointLabel || 'Royal Suite'}: <span style={{ color: navy }}>{touchpointValue}</span>
          </div>
        )}
      </header>

      {/* Golden Imperial Medallion Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '22px 0',
          textAlign: 'center',
          boxShadow: '0 6px 20px rgba(30,27,75,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', color: navy, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.5rem', cursor: 'pointer', marginBottom: '8px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val <= (hoverRating || rating);
            return (
              <span
                key={val}
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(val)}
                style={{
                  color: isSel ? gold : '#D1D5DB',
                  transform: isSel ? 'scale(1.2)' : 'scale(1)',
                  filter: isSel ? 'drop-shadow(0 2px 6px rgba(202,138,4,0.4))' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                ★
              </span>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: gold, fontFamily: 'sans-serif' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Brass Luggage Tag Chips */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1rem', color: navy, margin: '0 0 12px 0', fontFamily: 'serif' }}>
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
                  borderRadius: '6px',
                  border: isSel ? `2px solid ${gold}` : `1px solid ${border}`,
                  background: isSel ? navy : ivory,
                  color: isSel ? goldLight : '#374151',
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#6B7280', marginBottom: '6px' }}>
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
              background: ivory,
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Gold Trim Suggestions */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1rem', color: navy, margin: '0 0 12px 0', fontFamily: 'serif' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '8px',
              border: selectedIdeaId === idea.id ? `2px solid ${gold}` : `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${gold}10` : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: gold, textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#1F2937', lineHeight: '1.45', fontFamily: 'serif' }}>
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
            background: `linear-gradient(135deg, ${navy} 0%, #312E81 100%)`,
            color: goldLight,
            border: `1px solid ${gold}`,
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(30,27,75,0.3)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#6B7280', fontFamily: 'sans-serif' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: navy, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
