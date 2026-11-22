import React from 'react';

/**
 * F01 — Classic Bistro (restaurant_classic_bistro / restaurant_classic)
 * Warm parchment aesthetic (#FAF7F2), deep culinary emerald (#1B4332), brass accents (#C5A880),
 * traditional serif headings, and classic star rating.
 */
export default function RestaurantClassicBistro({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Classic Bistro';
  const primaryColor = '#1B4332';
  const brassAccent = '#C5A880';
  const parchmentBg = '#FAF7F2';

  return (
    <div
      className="vt-classic-bistro"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '20px 16px',
        backgroundColor: parchmentBg,
        minHeight: '100vh',
        color: '#2D3748',
        fontFamily: "'Playfair Display', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      {/* Header */}
      <header style={{ textAlign: 'center', padding: '24px 0 16px', borderBottom: `2px double ${brassAccent}` }}>
        <div style={{ fontSize: '1.8rem', color: primaryColor, marginBottom: '6px' }}>🍷 🍽️ 🥖</div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 700, color: primaryColor, margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#718096', fontStyle: 'italic', fontFamily: 'sans-serif' }}>
          Classic Culinary Tradition & Dining
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.8rem', color: primaryColor, fontWeight: 600, fontFamily: 'sans-serif' }}>
            {touchpointLabel}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Rating Card */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '12px',
          border: `1px solid ${brassAccent}40`,
          boxShadow: '0 4px 16px rgba(27,67,50,0.06)',
          padding: '24px 16px',
          margin: '24px 0',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '1.2rem', color: primaryColor, margin: '0 0 12px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', fontSize: '2.6rem', cursor: 'pointer', marginBottom: '8px' }}>
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              onClick={() => setRating(star)}
              style={{
                color: star <= (hoverRating || rating) ? brassAccent : '#E2E8F0',
                transition: 'transform 0.15s ease',
                transform: star <= (hoverRating || rating) ? 'scale(1.15)' : 'scale(1)',
              }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: primaryColor, fontFamily: 'sans-serif' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topic selection */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '12px',
          border: `1px solid ${brassAccent}40`,
          padding: '20px 16px',
          marginBottom: '24px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', color: primaryColor, margin: '0 0 12px 0', fontFamily: 'serif' }}>
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
                  borderRadius: '24px',
                  border: isSel ? `2px solid ${primaryColor}` : '1px solid #CBD5E0',
                  background: isSel ? primaryColor : '#F7FAFC',
                  color: isSel ? '#FFFFFF' : '#4A5568',
                  fontSize: '0.85rem',
                  fontWeight: isSel ? 600 : 500,
                  cursor: 'pointer',
                }}
              >
                <span>{top.icon}</span>
                <span>{top.label}</span>
              </button>
            );
          })}
        </div>

        {/* Note input */}
        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#718096', marginBottom: '6px' }}>
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
              border: `1px solid ${brassAccent}60`,
              background: parchmentBg,
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
          borderRadius: '12px',
          border: `1px solid ${brassAccent}40`,
          padding: '20px 16px',
          marginBottom: '24px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1.05rem', color: primaryColor, margin: '0 0 14px 0', fontFamily: 'serif' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '8px',
              border: selectedIdeaId === idea.id ? `2px solid ${primaryColor}` : '1px solid #E2E8F0',
              background: selectedIdeaId === idea.id ? `${primaryColor}08` : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
              transition: 'border-color 0.15s ease',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: brassAccent, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#2D3748', lineHeight: '1.45' }}>{idea.text}</p>
          </div>
        ))}

        {/* Google Handoff CTA */}
        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: primaryColor,
            color: '#FFFFFF',
            border: `1px solid ${brassAccent}`,
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(27,67,50,0.2)',
          }}
        >
          <span>{t.copyAndOpenGoogle}</span>
        </button>
      </section>

      {/* Private feedback link */}
      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#718096', fontFamily: 'sans-serif' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: primaryColor, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
