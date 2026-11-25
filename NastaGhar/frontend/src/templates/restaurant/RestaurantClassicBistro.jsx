import React from 'react';

/**
 * F01 — Classic Bistro (restaurant_classic_bistro / restaurant_classic)
 * Warm parchment aesthetic (#FAF7F2), deep culinary emerald (#1B4332), brass accents (#C5A880),
 * traditional serif headings, classic star rating, and responsive dual-column split on desktop.
 */
export default function RestaurantClassicBistro({ templateData, journeyState = {} }) {
  const {
    rating = 5,
    setRating = () => {},
    hoverRating = 0,
    setHoverRating = () => {},
    ratingLabel,
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
  } = journeyState;

  const bizName = templateData?.businessName || 'Classic Bistro';
  const primaryColor = '#1B4332';
  const brassAccent = '#C5A880';
  const parchmentBg = '#FAF7F2';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Delicious food and exceptional hospitality! 🍷';

  return (
    <div
      className="vt-page-container vt-classic-bistro"
      style={{
        backgroundColor: parchmentBg,
        minHeight: '100vh',
        color: '#2D3748',
        fontFamily: "'Playfair Display', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Brand Crest, Rating & Highlights */}
        <div className="vt-split-sticky-sidebar">
          {/* Header Card */}
          <header
            className="vt-bistro-card"
            style={{
              textAlign: 'center',
              padding: '24px 20px',
              borderBottom: `2px double ${brassAccent}`,
              background: '#FFFFFF',
              borderRadius: '16px',
              border: `1px solid ${brassAccent}40`,
              boxShadow: '0 4px 16px rgba(27,67,50,0.06)',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontSize: '2rem', color: primaryColor, marginBottom: '6px' }}>🍷 🍽️ 🥖</div>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 700, color: primaryColor, margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
              {bizName}
            </h1>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#718096', fontStyle: 'italic', fontFamily: 'sans-serif' }}>
              Classic Culinary Tradition & Dining
            </p>
            {touchpointValue && (
              <div style={{ marginTop: '10px', display: 'inline-block', padding: '4px 14px', borderRadius: '16px', backgroundColor: `${brassAccent}20`, fontSize: '0.82rem', color: primaryColor, fontWeight: 700, fontFamily: 'sans-serif' }}>
                {touchpointLabel}: {touchpointValue}
              </div>
            )}
          </header>

          {/* Rating Card */}
          <section
            className="vt-bistro-card"
            style={{
              background: '#FFFFFF',
              borderRadius: '16px',
              border: `1px solid ${brassAccent}40`,
              boxShadow: '0 4px 16px rgba(27,67,50,0.06)',
              padding: '22px 18px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '1.15rem', color: primaryColor, margin: '0 0 10px 0' }}>
              {t.howWasVisit || 'How was your dining experience?'}
            </h2>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.5rem', cursor: 'pointer', marginBottom: '8px' }}>
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

          {/* Highlights / Topic Selector */}
          <section
            className="vt-bistro-card"
            style={{
              background: '#FFFFFF',
              borderRadius: '16px',
              border: `1px solid ${brassAccent}40`,
              boxShadow: '0 4px 16px rgba(27,67,50,0.06)',
              padding: '20px 18px',
              fontFamily: 'sans-serif',
            }}
          >
            <h3 style={{ fontSize: '1rem', color: primaryColor, margin: '0 0 12px 0', fontFamily: 'serif', fontWeight: 700 }}>
              {t.whatStoodOut || 'What stood out?'}
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
                      fontWeight: isSel ? 700 : 500,
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
          {/* Personal Note Card */}
          <section
            className="vt-bistro-card"
            style={{
              background: '#FFFFFF',
              borderRadius: '16px',
              border: `1px solid ${brassAccent}40`,
              boxShadow: '0 4px 16px rgba(27,67,50,0.06)',
              padding: '20px 18px',
              marginBottom: '20px',
              fontFamily: 'sans-serif',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: primaryColor, marginBottom: '8px', fontFamily: 'serif' }}>
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
                borderRadius: '8px',
                border: `1px solid ${brassAccent}60`,
                background: parchmentBg,
                fontSize: '0.92rem',
                boxSizing: 'border-box',
                color: '#2D3748',
              }}
            />
          </section>

          {/* Curated AI Review Folio */}
          <section
            className="vt-bistro-card"
            style={{
              background: '#FFFFFF',
              borderRadius: '16px',
              border: `1px solid ${brassAccent}40`,
              boxShadow: '0 4px 16px rgba(27,67,50,0.06)',
              padding: '22px 18px',
              marginBottom: '20px',
              fontFamily: 'sans-serif',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.05rem', color: primaryColor, margin: 0, fontFamily: 'serif', fontWeight: 700 }}>
                {t.reviewIdeas || 'Curated Review Suggestions'}
              </h3>
              <span style={{ fontSize: '0.75rem', color: brassAccent, fontStyle: 'italic', fontWeight: 600 }}>
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
                    borderRadius: '10px',
                    border: isSelected ? `2px solid ${primaryColor}` : '1px solid #E2E8F0',
                    background: isSelected ? `${primaryColor}0C` : '#FAFAFA',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? '0 4px 12px rgba(27,67,50,0.1)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: brassAccent, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: brassAccent }}>★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.93rem', color: '#2D3748', lineHeight: '1.5' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '8px', textAlign: 'right', fontSize: '0.78rem', color: primaryColor, fontWeight: 700 }}>
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
                padding: '15px 20px',
                backgroundColor: primaryColor,
                color: '#FFFFFF',
                border: `1px solid ${brassAccent}`,
                borderRadius: '10px',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: 'pointer',
                marginTop: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                boxShadow: '0 6px 16px rgba(27,67,50,0.25)',
                transition: 'transform 0.15s ease, box-shadow 0.15s ease',
              }}
            >
              <span>{t.copyAndOpenGoogle || 'Copy & Continue to Google Review ↗'}</span>
            </button>
          </section>

          {/* Private feedback option */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.88rem', color: '#718096', fontFamily: 'sans-serif' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Want to tell us something privately? ') : (t.privatePromptBad || 'Share feedback directly with management: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: primaryColor, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
