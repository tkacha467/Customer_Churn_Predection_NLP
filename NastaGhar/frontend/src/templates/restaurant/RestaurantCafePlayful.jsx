import React from 'react';

/**
 * F04 — Café & Playful (restaurant_cafe_playful / restaurant_premium)
 * Cheerful specialty coffee & all-day bakery.
 * Warm cream background (#FFFDF7), peach/coral accents (#FB923C),
 * Nunito rounded typography, bouncy emoji rating scale, responsive dual-column on desktop.
 */
export default function RestaurantCafePlayful({ templateData, journeyState = {} }) {
  const {
    rating = 5,
    setRating = () => {},
    hoverRating = 0,
    setHoverRating = () => {},
    ratingLabel = { text: 'Loved it!' },
    availableTopics = [],
    selectedTopics = [],
    toggleTopic = () => {},
    personalNote = '',
    setPersonalNote = () => {},
    touchpointLabel = 'Table',
    touchpointValue = null,
    ideas = [],
    selectedIdeaId = null,
    onSelectIdea = () => {},
    draftReview = '',
    onDirectGoogleHandoff = () => {},
    onOpenPrivateFeedback = () => {},
    notePlaceholder,
    t = {},
  } = journeyState || {};

  const bizName = templateData?.businessName || 'Sunny Day Café';
  const coral = '#FB923C';
  const peachDark = '#EA580C';
  const creamBg = '#FFFDF7';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Delicious iced latte and fresh warm croissants! 🥐☕';

  const EMOJI_SCALE = {
    1: { emoji: '🥱', label: 'Sleepy / Not Great' },
    2: { emoji: '🫤', label: 'Meh, Okay' },
    3: { emoji: '🙂', label: 'Good Vibe' },
    4: { emoji: '😋', label: 'Yum! Super Nice' },
    5: { emoji: '🥳', label: 'Pure Magic! Loved It' },
  };

  return (
    <div
      className="vt-page-container vt-cafe-playful"
      style={{
        backgroundColor: creamBg,
        minHeight: '100vh',
        color: '#374151',
        fontFamily: "'Nunito', 'Comfortaa', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Cafe Header, Bouncy Rating & Topic Badges */}
        <div className="vt-split-sticky-sidebar">
          {/* Header Card */}
          <header
            style={{
              textAlign: 'center',
              padding: '24px 20px',
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FED7AA',
              boxShadow: '0 8px 24px rgba(251,146,60,0.08)',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '6px' }}>☕ 🥐 ✨</div>
            <h1 style={{ fontSize: '1.95rem', fontWeight: 900, color: peachDark, margin: '0 0 6px 0' }}>
              {bizName}
            </h1>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#9A3412', fontWeight: 600 }}>
              Specialty Coffee & All-Day Fresh Bakery
            </p>
            {touchpointValue && (
              <div style={{ marginTop: '10px', display: 'inline-block', padding: '4px 14px', borderRadius: '20px', backgroundColor: '#FFEDD5', color: peachDark, fontWeight: 800, fontSize: '0.82rem' }}>
                {touchpointLabel}: {touchpointValue}
              </div>
            )}
          </header>

          {/* Bouncy Emoji Rating Card */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FED7AA',
              boxShadow: '0 8px 24px rgba(251,146,60,0.08)',
              padding: '22px 18px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: peachDark, margin: '0 0 14px 0' }}>
              {t.howWasVisit || 'How was your cafe visit?'}
            </h2>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', fontSize: '2.4rem', cursor: 'pointer', marginBottom: '10px' }}>
              {[1, 2, 3, 4, 5].map((val) => {
                const isSelected = val === rating;
                const isHovered = val === hoverRating;
                const active = isHovered || isSelected;
                return (
                  <span
                    key={val}
                    onMouseEnter={() => setHoverRating(val)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(val)}
                    style={{
                      transform: active ? 'scale(1.25)' : 'scale(1)',
                      transition: 'transform 0.15s ease',
                      filter: active ? 'none' : 'grayscale(60%) opacity(0.6)',
                      display: 'inline-block',
                    }}
                    title={EMOJI_SCALE[val]?.label}
                  >
                    {EMOJI_SCALE[val]?.emoji}
                  </span>
                );
              })}
            </div>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: peachDark }}>
              {EMOJI_SCALE[hoverRating || rating]?.label || ratingLabel?.text}
            </div>
          </section>

          {/* Highlights / Topic Badges */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FED7AA',
              boxShadow: '0 8px 24px rgba(251,146,60,0.08)',
              padding: '20px 18px',
            }}
          >
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: peachDark, margin: '0 0 12px 0' }}>
              {t.whatStoodOut || 'What did you love most?'}
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
                      borderRadius: '20px',
                      border: isSel ? `2px solid ${peachDark}` : '1px solid #FED7AA',
                      background: isSel ? '#FFEDD5' : '#FFFDF7',
                      color: isSel ? peachDark : '#6B7280',
                      fontSize: '0.85rem',
                      fontWeight: isSel ? 800 : 600,
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
          </section>
        </div>

        {/* RIGHT COLUMN: Note, Review Ideas & Google Handoff CTA */}
        <div className="vt-split-content">
          {/* Note Input */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FED7AA',
              boxShadow: '0 8px 24px rgba(251,146,60,0.08)',
              padding: '20px 18px',
              marginBottom: '20px',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 800, color: peachDark, marginBottom: '8px' }}>
              {t.personalNote || 'Personal note'} ({t.optional || 'optional'})
            </label>
            <input
              type="text"
              value={personalNote}
              onChange={(e) => setPersonalNote(e.target.value)}
              placeholder={placeholder}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1.5px solid #FED7AA',
                background: '#FFFDF7',
                fontSize: '0.92rem',
                boxSizing: 'border-box',
                color: '#374151',
              }}
            />
          </section>

          {/* AI Review Ideas */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FED7AA',
              boxShadow: '0 8px 24px rgba(251,146,60,0.08)',
              padding: '22px 18px',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: peachDark, margin: 0 }}>
                {t.reviewIdeas || 'Bite-Sized Review Suggestions'}
              </h3>
              <span style={{ fontSize: '0.78rem', color: coral, fontWeight: 700 }}>
                Tap to copy & publish
              </span>
            </div>

            {ideas.map((idea) => {
              const isSelected = selectedIdeaId === idea.id;
              return (
                <div
                  key={idea.id}
                  onClick={() => onSelectIdea(idea)}
                  style={{
                    padding: '16px',
                    borderRadius: '14px',
                    border: isSelected ? `2.5px solid ${peachDark}` : '1.5px solid #FFEDD5',
                    background: isSelected ? '#FFF7ED' : '#FFFFFF',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? '0 4px 12px rgba(251,146,60,0.15)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 900, color: coral, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: coral }}>☕★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.93rem', color: '#374151', lineHeight: '1.5' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '8px', textAlign: 'right', fontSize: '0.78rem', color: peachDark, fontWeight: 800 }}>
                    {isSelected ? '✓ Ready to post →' : 'Use this review →'}
                  </div>
                </div>
              );
            })}

            {/* Google Review Primary CTA */}
            <button
              type="button"
              onClick={() => onDirectGoogleHandoff(draftReview)}
              style={{
                width: '100%',
                padding: '16px 20px',
                backgroundColor: peachDark,
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '14px',
                fontWeight: 900,
                fontSize: '1rem',
                cursor: 'pointer',
                marginTop: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                boxShadow: '0 6px 18px rgba(234,88,12,0.3)',
                transition: 'transform 0.15s ease',
              }}
            >
              <span>{t.copyAndOpenGoogle || 'Copy & Continue to Google Review ☕↗'}</span>
            </button>
          </section>

          {/* Private feedback option */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.88rem', color: '#9CA3AF' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Want to tell our baristas something privately? ') : (t.privatePromptBad || 'Tell our café team directly: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: peachDark, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
