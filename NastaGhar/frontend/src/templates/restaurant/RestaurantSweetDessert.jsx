import React from 'react';

/**
 * F05 — Sweet & Dessert House (restaurant_sweet_dessert)
 * STATUS: PREVIEW_ONLY / DRAFT (deployable = false)
 * Artisan desserts, patisserie, and confectionery.
 * Pastel pistachio (#D1FAE5) and berry rose (#F43F5E), polaroid card layout, candy drop rating scale.
 */
export default function RestaurantSweetDessert({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'La Petite Pâtisserie';
  const roseBerry = '#F43F5E';
  const pistachioBg = '#F0FDF4';

  return (
    <div
      className="vt-sweet-dessert"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '20px 16px',
        backgroundColor: pistachioBg,
        minHeight: '100vh',
        color: '#4B5563',
        fontFamily: "'Quicksand', 'Comfortaa', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      {/* Draft Preview Badge */}
      <div style={{ backgroundColor: '#FEF3C7', border: '1px solid #F59E0B', color: '#92400E', padding: '6px 12px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700, textAlign: 'center', marginBottom: '14px' }}>
        ⚠️ Template Status: Draft / Preview Only (Unpublished)
      </div>

      {/* Header */}
      <header style={{ textAlign: 'center', padding: '20px 0 16px' }}>
        <div style={{ fontSize: '2.6rem', marginBottom: '4px' }}>🍰 🧁 🍓</div>
        <h1 style={{ fontSize: '1.95rem', fontWeight: 800, color: roseBerry, margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#6B7280' }}>
          Artisan Sweets, Confections & Delicacies
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.82rem', color: roseBerry, fontWeight: 700 }}>
            {touchpointLabel}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Candy Drop Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '24px',
          border: `2px solid ${roseBerry}20`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 10px 25px rgba(244,63,94,0.08)',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1F2937', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.2rem', marginBottom: '10px' }}>
          {[1, 2, 3, 4, 5].map((val) => (
            <button
              key={val}
              type="button"
              onClick={() => setRating(val)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '2.2rem',
                transform: val <= rating ? 'scale(1.15)' : 'scale(0.95)',
                filter: val <= rating ? 'drop-shadow(0 2px 4px rgba(244,63,94,0.4))' : 'grayscale(100%) opacity(40%)',
                transition: 'transform 0.15s ease',
              }}
            >
              🍬
            </button>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: roseBerry }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${roseBerry}20`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#1F2937', margin: '0 0 12px 0' }}>
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
                  borderRadius: '16px',
                  border: isSel ? `2px solid ${roseBerry}` : '1px solid #E5E7EB',
                  background: isSel ? `${roseBerry}15` : '#F9FAFB',
                  color: isSel ? roseBerry : '#4B5563',
                  fontSize: '0.88rem',
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

        {/* Note */}
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
              padding: '12px',
              borderRadius: '12px',
              border: '1px solid #E5E7EB',
              background: '#F9FAFB',
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
          border: `1px solid ${roseBerry}20`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#1F2937', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '12px',
              border: selectedIdeaId === idea.id ? `2px solid ${roseBerry}` : '1px solid #F3F4F6',
              background: selectedIdeaId === idea.id ? `${roseBerry}08` : '#FAFAFA',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: roseBerry, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#374151', lineHeight: '1.45' }}>{idea.text}</p>
          </div>
        ))}

        {/* Action */}
        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '16px',
            backgroundColor: roseBerry,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '16px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 6px 18px rgba(244,63,94,0.3)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      {/* Private feedback */}
      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#9CA3AF' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: roseBerry, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
