import React from 'react';

/**
 * B01 — Luxury Day Spa & Organic Sanctuary (beauty_spa_sanctuary / salon_classic)
 * Visual Structure: Calming eucalyptus green (#064E3B), sage mist (#F2FBF7), bamboo gold (#D97706).
 * Hero: Zen botanical header with lotus emblem and essential oil drops.
 * Rating: Lotus petal stones rating scale (smooth rounded stone buttons with subtle glow).
 * Topics: Organic leaf-shaped pills with botanical wellness icons.
 * Suggestions: Serene parchment quote cards with soft sage borders.
 */
export default function SalonSpaSanctuary({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Elysian Botanical Day Spa';
  const eucalyptus = '#064E3B';
  const sageMist = '#F2FBF7';
  const bambooGold = '#D97706';
  const stoneBorder = '#A7F3D0';

  return (
    <div
      className="vt-spa-sanctuary"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: sageMist,
        minHeight: '100vh',
        color: '#1F2937',
        fontFamily: "'Cormorant Garamond', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      {/* Botanical Zen Header */}
      <header style={{ textAlign: 'center', padding: '24px 0 16px', borderBottom: `1px solid ${stoneBorder}` }}>
        <div style={{ fontSize: '2.4rem', color: eucalyptus, marginBottom: '6px' }}>🪷 🌿 🕯️</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '2.5px', textTransform: 'uppercase', color: bambooGold, fontWeight: 700, marginBottom: '4px' }}>
          Holistic Botanical Sanctuary
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 600, color: eucalyptus, margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#4B5563', fontStyle: 'italic', fontFamily: 'sans-serif' }}>
          Aromatherapy, Deep Tissue Therapy & Holistic Rituals
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.82rem', color: eucalyptus, fontWeight: 600, fontFamily: 'sans-serif' }}>
            {touchpointLabel || 'Therapist / Suite'}: <span style={{ color: bambooGold }}>{touchpointValue}</span>
          </div>
        )}
      </header>

      {/* Lotus Petal Stone Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '24px',
          border: `1px solid ${stoneBorder}`,
          boxShadow: '0 8px 24px rgba(6,78,59,0.06)',
          padding: '24px 16px',
          margin: '22px 0',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '1.15rem', color: eucalyptus, margin: '0 0 14px 0' }}>
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
                  width: '52px',
                  height: '52px',
                  borderRadius: '16px 4px 16px 4px',
                  border: isSel ? `2px solid ${bambooGold}` : '1px solid #D1FAE5',
                  background: isSel ? `${bambooGold}18` : '#F9FCFA',
                  fontSize: '1.4rem',
                  cursor: 'pointer',
                  transform: isSel ? 'scale(1.1) rotate(-3deg)' : 'scale(1)',
                  transition: 'all 0.18s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isSel ? bambooGold : '#9CA3AF',
                }}
              >
                {val}★
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 600, color: eucalyptus, fontFamily: 'sans-serif' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Organic Leaf Topic Selector */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${stoneBorder}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1rem', color: eucalyptus, margin: '0 0 12px 0', fontFamily: 'serif' }}>
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
                  borderRadius: '20px 6px 20px 6px',
                  border: isSel ? `2px solid ${eucalyptus}` : '1px solid #D1FAE5',
                  background: isSel ? eucalyptus : '#F9FCFA',
                  color: isSel ? '#FFFFFF' : '#374151',
                  fontSize: '0.85rem',
                  fontWeight: isSel ? 600 : 500,
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
              borderRadius: '8px',
              border: '1px solid #D1FAE5',
              background: sageMist,
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Serene Suggestion Cards */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${stoneBorder}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1rem', color: eucalyptus, margin: '0 0 12px 0', fontFamily: 'serif' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '12px',
              border: selectedIdeaId === idea.id ? `2px solid ${eucalyptus}` : '1px solid #E5E7EB',
              background: selectedIdeaId === idea.id ? `${eucalyptus}08` : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: bambooGold, textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#1F2937', lineHeight: '1.45' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: eucalyptus,
            color: '#FFFFFF',
            border: `1px solid ${bambooGold}`,
            borderRadius: '10px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(6,78,59,0.2)',
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
          style={{ background: 'none', border: 'none', color: eucalyptus, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
