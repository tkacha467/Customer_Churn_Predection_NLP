import React from 'react';

/**
 * F04 — Café & Playful (restaurant_cafe_playful / restaurant_premium)
 * Cheerful specialty coffee & all-day bakery.
 * Warm cream background (#FFFDF7), peach/coral accents (#FB923C),
 * Nunito rounded typography, bouncy emoji rating scale.
 */
export default function RestaurantCafePlayful({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Sunny Day Café';
  const coral = '#FB923C';
  const peachDark = '#EA580C';
  const creamBg = '#FFFDF7';

  const EMOJI_SCALE = {
    1: { emoji: '🥱', label: 'Sleepy / Not Great' },
    2: { emoji: '🫤', label: 'Meh, Okay' },
    3: { emoji: '🙂', label: 'Good Vibe' },
    4: { emoji: '😋', label: 'Yum! Super Nice' },
    5: { emoji: '🥳', label: 'Pure Magic! Loved It' },
  };

  return (
    <div
      className="vt-cafe-playful"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '20px 16px',
        backgroundColor: creamBg,
        minHeight: '100vh',
        color: '#374151',
        fontFamily: "'Nunito', 'Comfortaa', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      {/* Header */}
      <header style={{ textAlign: 'center', padding: '24px 0 16px' }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '4px' }}>☕ 🥐 ✨</div>
        <h1 style={{ fontSize: '1.95rem', fontWeight: 900, color: peachDark, margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#9CA3AF', fontWeight: 600 }}>
          Specialty Brews, Fresh Bakes & Good Times
        </p>
        {touchpointValue && (
          <div style={{ display: 'inline-block', marginTop: '8px', padding: '4px 12px', borderRadius: '16px', background: `${coral}20`, color: peachDark, fontSize: '0.8rem', fontWeight: 800 }}>
            {touchpointLabel}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Bouncy Emoji Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '24px',
          border: `2px dashed ${coral}40`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 8px 24px rgba(251,146,60,0.1)',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1F2937', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>

        {/* 5 Bouncy Emoji Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '12px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val === rating;
            return (
              <button
                key={val}
                type="button"
                onClick={() => setRating(val)}
                style={{
                  width: '58px',
                  height: '58px',
                  borderRadius: '50%',
                  border: isSel ? `3px solid ${peachDark}` : '2px solid #F3F4F6',
                  background: isSel ? `${coral}20` : '#F9FAFB',
                  fontSize: isSel ? '2rem' : '1.7rem',
                  cursor: 'pointer',
                  transform: isSel ? 'scale(1.15) translateY(-4px)' : 'scale(1)',
                  transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {EMOJI_SCALE[val].emoji}
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: 800, color: peachDark }}>
          {EMOJI_SCALE[rating]?.label || ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: '1px solid #F3F4F6',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#1F2937', margin: '0 0 12px 0' }}>
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
                  borderRadius: '20px',
                  border: isSel ? `2px solid ${peachDark}` : '1px solid #E5E7EB',
                  background: isSel ? coral : '#F9FAFB',
                  color: isSel ? '#FFFFFF' : '#4B5563',
                  fontSize: '0.88rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  transition: 'transform 0.15s',
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 800, color: '#6B7280', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={t.notePlaceholder}
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: '12px',
              border: '2px solid #F3F4F6',
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
          border: '1px solid #F3F4F6',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#1F2937', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '14px',
              border: selectedIdeaId === idea.id ? `2px solid ${peachDark}` : '1px solid #F3F4F6',
              background: selectedIdeaId === idea.id ? `${coral}12` : '#FAFAFA',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 900, color: peachDark, textTransform: 'uppercase', marginBottom: '4px' }}>
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
            backgroundColor: peachDark,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '14px',
            fontWeight: 900,
            fontSize: '1.05rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 6px 18px rgba(234,88,12,0.3)',
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
          style={{ background: 'none', border: 'none', color: peachDark, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
