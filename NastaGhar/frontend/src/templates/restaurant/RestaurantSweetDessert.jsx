import React from 'react';

/**
 * F05 — Sweet & Dessert House (restaurant_sweet_dessert)
 * STATUS: PREVIEW_ONLY / DRAFT (deployable = false)
 * Artisan desserts, patisserie, and confectionery.
 * Pastel pistachio (#F0FDF4) and berry rose (#F43F5E), polaroid card layout, candy drop rating scale,
 * responsive dual-column split on desktop.
 */
export default function RestaurantSweetDessert({ templateData, journeyState = {} }) {
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
  } = journeyState || {};

  const bizName = templateData?.businessName || 'La Petite Pâtisserie';
  const roseBerry = '#F43F5E';
  const pistachioBg = '#F0FDF4';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Loved the pistachio macarons and raspberry tart! 🍰🍓';

  return (
    <div
      className="vt-page-container vt-sweet-dessert"
      style={{
        backgroundColor: pistachioBg,
        minHeight: '100vh',
        color: '#4B5563',
        fontFamily: "'Quicksand', 'Comfortaa', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Patisserie Header, Candy Rating & Sweet Highlights */}
        <div className="vt-split-sticky-sidebar">
          {/* Draft Preview Notice */}
          <div style={{ backgroundColor: '#FEF3C7', border: '1px solid #F59E0B', color: '#92400E', padding: '6px 12px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 700, textAlign: 'center', marginBottom: '16px' }}>
            ⚠️ Template Status: Draft / Preview Only (Unpublished)
          </div>

          {/* Header Card */}
          <header
            style={{
              textAlign: 'center',
              padding: '24px 20px',
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FBCFE8',
              boxShadow: '0 8px 24px rgba(244,63,94,0.08)',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontSize: '2.6rem', marginBottom: '4px' }}>🍰 🧁 🍓</div>
            <h1 style={{ fontSize: '1.95rem', fontWeight: 800, color: roseBerry, margin: '0 0 4px 0' }}>
              {bizName}
            </h1>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#6B7280' }}>
              Artisan Sweets, Confections & Delicacies
            </p>
            {touchpointValue && (
              <div style={{ marginTop: '10px', display: 'inline-block', padding: '4px 14px', borderRadius: '16px', backgroundColor: '#FCE7F3', color: roseBerry, fontWeight: 700, fontSize: '0.82rem' }}>
                {touchpointLabel}: {touchpointValue}
              </div>
            )}
          </header>

          {/* Candy Drop Rating Card */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FBCFE8',
              boxShadow: '0 8px 24px rgba(244,63,94,0.08)',
              padding: '22px 18px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: roseBerry, margin: '0 0 14px 0' }}>
              {t.howWasVisit || 'How sweet was your experience?'}
            </h2>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', fontSize: '2.5rem', cursor: 'pointer', marginBottom: '8px' }}>
              {[1, 2, 3, 4, 5].map((val) => {
                const active = val <= (hoverRating || rating);
                return (
                  <span
                    key={val}
                    onMouseEnter={() => setHoverRating(val)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(val)}
                    style={{
                      color: active ? roseBerry : '#E5E7EB',
                      transform: active ? 'scale(1.2)' : 'scale(1)',
                      transition: 'transform 0.15s ease',
                      display: 'inline-block',
                    }}
                  >
                    🍭
                  </span>
                );
              })}
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: roseBerry }}>
              {ratingLabel?.emoji} {ratingLabel?.text}
            </div>
          </section>

          {/* Highlights / Sweet Chips */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FBCFE8',
              boxShadow: '0 8px 24px rgba(244,63,94,0.08)',
              padding: '20px 18px',
            }}
          >
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: roseBerry, margin: '0 0 12px 0' }}>
              {t.whatStoodOut || 'What did you indulge in?'}
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
                      border: isSel ? `2px solid ${roseBerry}` : '1px solid #FBCFE8',
                      background: isSel ? '#FCE7F3' : '#FFFFFF',
                      color: isSel ? roseBerry : '#6B7280',
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

        {/* RIGHT COLUMN: Note, Review Ideas & Sweet Rose CTA */}
        <div className="vt-split-content">
          {/* Note Input */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FBCFE8',
              boxShadow: '0 8px 24px rgba(244,63,94,0.08)',
              padding: '20px 18px',
              marginBottom: '20px',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: roseBerry, marginBottom: '8px' }}>
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
                border: '1.5px solid #FBCFE8',
                background: '#FDF2F8',
                fontSize: '0.92rem',
                boxSizing: 'border-box',
                color: '#4B5563',
              }}
            />
          </section>

          {/* AI Review Ideas */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: '2px solid #FBCFE8',
              boxShadow: '0 8px 24px rgba(244,63,94,0.08)',
              padding: '22px 18px',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: roseBerry, margin: 0 }}>
                {t.reviewIdeas || 'Sweet Review Suggestions'}
              </h3>
              <span style={{ fontSize: '0.78rem', color: roseBerry, fontWeight: 700 }}>
                Tap to Select
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
                    border: isSelected ? `2px solid ${roseBerry}` : '1px solid #FBCFE8',
                    background: isSelected ? '#FDF2F8' : '#FFFFFF',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: roseBerry, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: roseBerry }}>🍓★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.92rem', color: '#374151', lineHeight: '1.5' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '8px', textAlign: 'right', fontSize: '0.78rem', color: roseBerry, fontWeight: 700 }}>
                    {isSelected ? '✓ Selected →' : 'Use this review →'}
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
                backgroundColor: roseBerry,
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '14px',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                marginTop: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                boxShadow: '0 6px 18px rgba(244,63,94,0.3)',
                transition: 'transform 0.15s ease',
              }}
            >
              <span>{t.copyAndOpenGoogle || 'Publish to Google Review 🍰↗'}</span>
            </button>
          </section>

          {/* Private feedback option */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.88rem', color: '#9CA3AF' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Want to tell our pastry chef privately? ') : (t.privatePromptBad || 'Tell our team directly: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: roseBerry, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
