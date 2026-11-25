import React from 'react';

/**
 * B03 — Luxury Day Spa & Organic Sanctuary (beauty_spa_sanctuary / salon_spa_sanctuary)
 * Calming eucalyptus green (#064E3B), sage mist (#F2FBF7), bamboo gold (#D97706).
 * Hero: Zen botanical header with lotus emblem and essential oil drops.
 * Rating: Lotus petal stones rating scale.
 * Responsive dual-column split on desktop.
 */
export default function SalonSpaSanctuary({ templateData, journeyState = {} }) {
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
    touchpointLabel = 'Suite',
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

  const bizName = templateData?.businessName || 'Elysian Botanical Day Spa';
  const eucalyptus = '#064E3B';
  const sageMist = '#F2FBF7';
  const bambooGold = '#D97706';
  const stoneBorder = '#A7F3D0';
  const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Pure bliss! The aromatherapy massage and herbal tea were divine. 🪷🕯️';

  return (
    <div
      className="vt-page-container vt-spa-sanctuary"
      style={{
        backgroundColor: sageMist,
        minHeight: '100vh',
        color: '#1F2937',
        fontFamily: "'Cormorant Garamond', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}
    >
      <div className="vt-split-layout">
        {/* LEFT COLUMN: Botanical Zen Header, River Stone Rating & Wellness Tags */}
        <div className="vt-split-sticky-sidebar">
          {/* Header Card */}
          <header
            style={{
              textAlign: 'center',
              padding: '24px 20px',
              borderBottom: `2px solid ${stoneBorder}`,
              background: '#FFFFFF',
              borderRadius: '20px',
              border: `1px solid ${stoneBorder}`,
              boxShadow: '0 8px 24px rgba(6,78,59,0.06)',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontSize: '2.5rem', color: eucalyptus, marginBottom: '6px' }}>🪷 🌿 🕯️</div>
            <div style={{ fontSize: '0.75rem', letterSpacing: '2.5px', textTransform: 'uppercase', color: bambooGold, fontWeight: 700, marginBottom: '4px' }}>
              Holistic Botanical Sanctuary
            </div>
            <h1 style={{ fontSize: '2.1rem', fontWeight: 600, color: eucalyptus, margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
              {bizName}
            </h1>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#4B5563', fontStyle: 'italic', fontFamily: 'sans-serif' }}>
              Mindful Relaxation & Aromatherapy Rituals
            </p>
            {touchpointValue && (
              <div style={{ marginTop: '10px', display: 'inline-block', padding: '4px 14px', borderRadius: '16px', backgroundColor: '#ECFDF5', color: eucalyptus, fontWeight: 700, fontSize: '0.82rem', fontFamily: 'sans-serif' }}>
                {touchpointLabel}: {touchpointValue}
              </div>
            )}
          </header>

          {/* River Stone Rating Card */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: `1px solid ${stoneBorder}`,
              boxShadow: '0 8px 24px rgba(6,78,59,0.06)',
              padding: '24px 20px',
              marginBottom: '20px',
              textAlign: 'center',
            }}
          >
            <h2 style={{ fontSize: '1.15rem', color: eucalyptus, margin: '0 0 14px 0', letterSpacing: '1px' }}>
              {t.howWasVisit || 'Rate Your Sanctuary Experience'}
            </h2>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '12px' }}>
              {[1, 2, 3, 4, 5].map((val) => {
                const active = val <= (hoverRating || rating);
                return (
                  <button
                    key={val}
                    type="button"
                    onMouseEnter={() => setHoverRating(val)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(val)}
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      border: active ? `2px solid ${eucalyptus}` : `1px solid ${stoneBorder}`,
                      background: active ? eucalyptus : '#F0FDF4',
                      color: active ? '#FFFFFF' : eucalyptus,
                      fontSize: '1.2rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: active ? '0 4px 12px rgba(6,78,59,0.2)' : 'none',
                    }}
                  >
                    ★
                  </button>
                );
              })}
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, color: eucalyptus, fontFamily: 'sans-serif' }}>
              {ratingLabel?.emoji} {ratingLabel?.text}
            </div>
          </section>

          {/* Botanical Highlights */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: `1px solid ${stoneBorder}`,
              boxShadow: '0 8px 24px rgba(6,78,59,0.06)',
              padding: '20px 18px',
              fontFamily: 'sans-serif',
            }}
          >
            <h3 style={{ fontSize: '0.95rem', color: eucalyptus, margin: '0 0 12px 0', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>
              {t.whatStoodOut || 'Sensory Highlights'}
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
                      border: isSel ? `2px solid ${eucalyptus}` : `1px solid ${stoneBorder}`,
                      background: isSel ? '#ECFDF5' : '#FFFFFF',
                      color: isSel ? eucalyptus : '#4B5563',
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

        {/* RIGHT COLUMN: Note, Serene Review Cards & Eucalyptus CTA */}
        <div className="vt-split-content">
          {/* Note Input */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: `1px solid ${stoneBorder}`,
              boxShadow: '0 8px 24px rgba(6,78,59,0.06)',
              padding: '20px 18px',
              marginBottom: '20px',
              fontFamily: 'sans-serif',
            }}
          >
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: eucalyptus, marginBottom: '8px' }}>
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
                borderRadius: '10px',
                border: `1px solid ${stoneBorder}`,
                background: '#F0FDF4',
                color: '#1F2937',
                fontSize: '0.92rem',
                boxSizing: 'border-box',
              }}
            />
          </section>

          {/* AI Suggestions Cards */}
          <section
            style={{
              background: '#FFFFFF',
              borderRadius: '20px',
              border: `1px solid ${stoneBorder}`,
              boxShadow: '0 8px 24px rgba(6,78,59,0.06)',
              padding: '22px 18px',
              marginBottom: '20px',
              fontFamily: 'sans-serif',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: eucalyptus, margin: 0 }}>
                {t.reviewIdeas || 'Serene Guest Reflections'}
              </h3>
              <span style={{ fontSize: '0.78rem', color: bambooGold, fontWeight: 700 }}>
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
                    borderRadius: '12px',
                    border: isSelected ? `2px solid ${eucalyptus}` : `1px solid ${stoneBorder}`,
                    background: isSelected ? '#ECFDF5' : '#FFFFFF',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: bambooGold, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {idea.focus}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: bambooGold }}>🌿★★★★★</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.93rem', color: '#1F2937', lineHeight: '1.5' }}>
                    "{idea.text}"
                  </p>
                  <div style={{ marginTop: '8px', textAlign: 'right', fontSize: '0.78rem', color: eucalyptus, fontWeight: 700 }}>
                    {isSelected ? '✓ Ready to post →' : 'Use this review →'}
                  </div>
                </div>
              );
            })}

            {/* Eucalyptus Google CTA */}
            <button
              type="button"
              onClick={() => onDirectGoogleHandoff(draftReview)}
              style={{
                width: '100%',
                padding: '16px 20px',
                backgroundColor: eucalyptus,
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '12px',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: 'pointer',
                marginTop: '14px',
                boxShadow: '0 6px 18px rgba(6,78,59,0.25)',
                transition: 'transform 0.15s ease',
              }}
            >
              <span>{t.copyAndOpenGoogle || 'Publish to Google Review 🪷↗'}</span>
            </button>
          </section>

          {/* Private feedback option */}
          <footer style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.88rem', color: '#6B7280', fontFamily: 'sans-serif' }}>
            <span>{rating >= 4 ? (t.privatePromptGood || 'Wish to share a private thought with our spa director? ') : (t.privatePromptBad || 'Tell our management team directly: ')}</span>
            <button
              type="button"
              onClick={onOpenPrivateFeedback}
              style={{ background: 'none', border: 'none', color: eucalyptus, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
            >
              {t.sendPrivateNote || 'Send private note'}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
