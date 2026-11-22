import React from 'react';

/**
 * T05 — Cozy Bed & Breakfast / Mountain Inn (hotel_cozy_inn / hotel_bnb)
 * Visual Structure: Fireside cinnamon (#9A3412), buttermilk (#FFFBEB), flannel red (#B91C1C).
 * Hero: Stone fireplace & hot cocoa, homestyle guestbook header.
 * Rating: Cozy hearth fire rating scale (🔥 warm hearth flames).
 * Topics: Country quilt-style tags.
 * Suggestions: Handwritten guestbook-style notes.
 */
export default function HotelCozyInn({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Cinnamon Hill Bed & Breakfast';
  const cinnamon = '#9A3412';
  const buttermilk = '#FFFBEB';
  const flannelRed = '#B91C1C';
  const border = '#FED7AA';

  return (
    <div
      className="vt-cozy-inn"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: buttermilk,
        minHeight: '100vh',
        color: '#431407',
        fontFamily: "'Fraunces', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      <header style={{ textAlign: 'center', padding: '20px 0 16px', borderBottom: `2px dashed ${flannelRed}40` }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '4px' }}>🏡 ☕ 🔥</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '2px', textTransform: 'uppercase', color: cinnamon, fontWeight: 700, marginBottom: '4px' }}>
          Homestyle Mountain Hospitality & Morning Bakes
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, color: flannelRed, margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: cinnamon, fontWeight: 700, fontFamily: 'sans-serif' }}>
            {touchpointLabel || 'Guest Room'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Hearth Fire Rating Scale */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 6px 18px rgba(154,52,18,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', color: flannelRed, margin: '0 0 14px 0' }}>
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
                  transform: isSel ? 'scale(1.2) translateY(-2px)' : 'scale(0.95)',
                  filter: isSel ? 'drop-shadow(0 2px 6px rgba(185,28,28,0.4))' : 'grayscale(100%) opacity(30%)',
                  transition: 'all 0.15s ease',
                }}
              >
                🔥
              </span>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: cinnamon, fontFamily: 'sans-serif' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
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
        <h3 style={{ fontSize: '1rem', color: flannelRed, margin: '0 0 12px 0', fontFamily: 'serif' }}>
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
                  borderRadius: '14px',
                  border: isSel ? `2px solid ${cinnamon}` : `1px solid ${border}`,
                  background: isSel ? cinnamon : buttermilk,
                  color: isSel ? '#FFFFFF' : '#7C2D12',
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#7C2D12', marginBottom: '6px' }}>
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
              borderRadius: '8px',
              border: `1px solid ${border}`,
              background: buttermilk,
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Guestbook Notes */}
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
        <h3 style={{ fontSize: '1rem', color: flannelRed, margin: '0 0 12px 0', fontFamily: 'serif' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '10px',
              border: selectedIdeaId === idea.id ? `2px solid ${flannelRed}` : '1px solid #FED7AA',
              background: selectedIdeaId === idea.id ? '#FFEDD5' : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: cinnamon, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#431407', lineHeight: '1.45', fontStyle: 'italic' }}>
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
            backgroundColor: flannelRed,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(185,28,28,0.25)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#9A3412', fontFamily: 'sans-serif' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: flannelRed, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
