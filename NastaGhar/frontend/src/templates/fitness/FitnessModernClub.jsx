import React from 'react';

/**
 * G03 — Modern Athletic Performance Club (fitness_modern_club / fitness_club)
 * Visual Structure: Athletic deep slate (#0F172A), electric lime (#84CC16), sleek ice silver (#F1F5F9).
 * Hero: High-performance training floor, dynamic velocity meter banner.
 * Rating: Dynamic speed / wattage performance bar scale (10 to 50 km/h metric blocks).
 * Topics: Slanted aerodynamic pill badges with electric lime accents.
 * Suggestions: High-contrast athletic training cards with neon markers.
 */
export default function FitnessModernClub({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Velocity High-Performance Athletic Club';
  const lime = '#84CC16';
  const slateDark = '#0F172A';
  const slateCard = '#1E293B';
  const border = '#334155';

  const PERFORMANCE_TIERS = ['WARMUP', 'ENDURANCE', 'TEMPO', 'THRESHOLD', 'PEAK MAX'];

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Incredible coaching, motivating energy and pristine facility! 💪';

  return (
    <div className="vt-page-container vt-fitness-club" style={{
        padding: '24px 16px',
        backgroundColor: slateDark,
        minHeight: '100vh',
        color: '#F8FAFC',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      {/* Header */}
      <header style={{ padding: '20px 0 16px', borderBottom: `2px solid ${lime}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>⚡ 🏃‍♂️ 💨</span>
          <span
            style={{
              backgroundColor: `${lime}20`,
              color: lime,
              border: `1px solid ${lime}`,
              fontSize: '0.72rem',
              fontWeight: 800,
              padding: '3px 8px',
              borderRadius: '999px',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            PEAK PERFORMANCE
          </span>
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#94A3B8' }}>
          Next-Gen Conditioning, Strength Dynamics & Recovery
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.82rem', color: '#CBD5E1', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: lime }}>▶</span>
            <span>{touchpointLabel || 'Locker / Station'}: <strong>{touchpointValue}</strong></span>
          </div>
        )}
      </header>

      {/* Speedometer Wattage Rating */}
      <section
        style={{
          background: slateCard,
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#F1F5F9', margin: '0 0 16px 0' }}>
          {t.howWasVisit}
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '14px' }}>
          {[1, 2, 3, 4, 5].map((val) => {
            const isSel = val <= (hoverRating || rating);
            const isExact = val === rating;
            return (
              <button
                key={val}
                type="button"
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(val)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '14px 4px',
                  borderRadius: '10px',
                  border: isExact ? `2px solid ${lime}` : isSel ? `1px solid ${lime}` : `1px solid ${border}`,
                  background: isExact ? `${lime}25` : isSel ? `${lime}10` : '#0F172A',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.5rem', marginBottom: '4px' }}>
                  {val === 5 ? '🚀' : val >= 4 ? '⚡' : val >= 3 ? '🔥' : '🏃'}
                </span>
                <span style={{ fontSize: '1rem', fontWeight: 900, color: isSel ? lime : '#64748B' }}>
                  {val * 10} km/h
                </span>
                <span style={{ fontSize: '0.62rem', fontWeight: 700, color: isSel ? '#F8FAFC' : '#475569', marginTop: '2px' }}>
                  {PERFORMANCE_TIERS[val - 1]}
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 800, color: lime }}>
            {typeof ratingLabel === 'string' ? ratingLabel : `${ratingLabel?.emoji || ''} ${ratingLabel?.text || ''}`.trim()}
          </div>
        )}
      </section>

      {/* Aerodynamic Topic Selector */}
      <section
        style={{
          background: slateCard,
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#F1F5F9', margin: '0 0 14px 0' }}>
          {t.whatStoodOut}
        </h3>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {(availableTopics || []).map((top) => {
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
                  borderRadius: '8px',
                  border: isSel ? `1px solid ${lime}` : `1px solid ${border}`,
                  background: isSel ? lime : '#0F172A',
                  color: isSel ? '#000000' : '#E2E8F0',
                  fontWeight: 700,
                  fontSize: '0.85rem',
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
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={placeholder}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: '8px',
              border: `1px solid ${border}`,
              background: '#0F172A',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content">{/* Ideas / Training Feedback Suggestions */}
      <section
        style={{
          background: slateCard,
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#F1F5F9', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>

        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '10px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${lime}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${lime}15` : '#0F172A',
              marginBottom: '10px',
              cursor: 'pointer',
              transition: 'background 0.15s ease',
            }}
          >
            <div style={{ fontSize: '0.74rem', fontWeight: 800, color: lime, textTransform: 'uppercase', marginBottom: '4px' }}>
              LOG // {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E2E8F0', lineHeight: '1.4' }}>
              {idea.text}
            </p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: lime,
            color: '#000000',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 900,
            fontSize: '1.05rem',
            letterSpacing: '0.5px',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: `0 4px 14px ${lime}40`,
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      {/* Footer */}
      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#64748B' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>{' '}
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: lime, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
