import React from 'react';

/**
 * T03 — Eco-Resort & Nature Retreat (hotel_eco_retreat / hotel_nature)
 * Visual Structure: Rainforest green (#064E3B), bamboo (#E2E8F0), morning mist (#ECFDF5).
 * Hero: Mountain pine & sunrise, wilderness retreat header.
 * Rating: Mountain peak rating scale (⛰️ mountain silhouette buttons).
 * Topics: Leaf-shaped badge chips.
 * Suggestions: Botanical cards with forest-green borders.
 */
export default function HotelEcoRetreat({ templateData, journeyState = {} }) {
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
    touchpointLabel = 'Table / Station',
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

  const bizName = templateData?.businessName || 'Wildflower Canopy Eco Retreat';
  const forest = '#064E3B';
  const forestDark = '#022C22';
  const mistBg = '#ECFDF5';
  const border = '#A7F3D0';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Beautiful room, exceptional hospitality and wonderful breakfast! 🏨';

  return (
    <div className="vt-page-container vt-eco-retreat" style={{
        padding: '24px 16px',
        backgroundColor: mistBg,
        minHeight: '100vh',
        color: '#064E3B',
        fontFamily: "'Fraunces', 'Georgia', 'Noto Serif Gujarati', 'Noto Serif Devanagari', serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ textAlign: 'center', padding: '20px 0 16px', borderBottom: `2px solid ${border}` }}>
        <div style={{ fontSize: '2.4rem', marginBottom: '4px' }}>🌲 ⛰️ 🧘</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '2px', textTransform: 'uppercase', color: forest, fontWeight: 700, marginBottom: '4px' }}>
          Wilderness Retreat & Sustainable Sanctuary
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 600, color: forestDark, margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: forest, fontWeight: 600, fontFamily: 'sans-serif' }}>
            {touchpointLabel || 'Canopy Villa'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Mountain Peak Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 6px 20px rgba(6,78,59,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', color: forestDark, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.3rem', marginBottom: '10px' }}>
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
                  transform: isSel ? 'scale(1.2)' : 'scale(0.95)',
                  filter: isSel ? 'drop-shadow(0 2px 6px rgba(6,78,59,0.4))' : 'grayscale(100%) opacity(30%)',
                  transition: 'all 0.15s ease',
                }}
              >
                ⛰️
              </span>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: forest, fontFamily: 'sans-serif' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1rem', color: forestDark, margin: '0 0 12px 0', fontFamily: 'serif' }}>
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
                  border: isSel ? `2px solid ${forest}` : '1px solid #D1FAE5',
                  background: isSel ? forest : '#F0FDF4',
                  color: isSel ? '#FFFFFF' : '#065F46',
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
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#065F46', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={placeholder}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: `1px solid ${border}`,
              background: mistBg,
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content">{/* Ideas */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '20px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
          fontFamily: 'sans-serif',
        }}
      >
        <h3 style={{ fontSize: '1rem', color: forestDark, margin: '0 0 12px 0', fontFamily: 'serif' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '10px',
              border: selectedIdeaId === idea.id ? `2px solid ${forest}` : '1px solid #D1FAE5',
              background: selectedIdeaId === idea.id ? '#D1FAE5' : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: forest, textTransform: 'uppercase', marginBottom: '4px' }}>
              {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#1F2937', lineHeight: '1.45' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: forest,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '12px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: '0 4px 14px rgba(6,78,59,0.25)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#047857', fontFamily: 'sans-serif' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: forest, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
