import React from 'react';

/**
 * G04 — Boxing, MMA & Combat Sports Arena (fitness_combat_ring / fitness_boxing)
 * Visual Structure: Matte canvas black (#18181B), championship crimson (#DC2626), belt gold (#F59E0B).
 * Hero: Heavy bag & ring corner ropes, warrior battle banner.
 * Rating: Round punch counter scale (Round 1 sparring to Round 5 knockout star).
 * Topics: Heavy-duty combat discipline badges.
 * Suggestions: Corner coach briefing cards with red corner accent.
 */
export default function FitnessCombatRing({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Apex Combat & Boxing Club';
  const red = '#DC2626';
  const gold = '#F59E0B';
  const dark = '#18181B';
  const cardBg = '#27272A';
  const border = '#3F3F46';

  const ROUND_NAMES = ['RD 1: JAB', 'RD 2: COMBO', 'RD 3: POWER', 'RD 4: CHAMPION', 'RD 5: KNOCKOUT'];

  return (
    <div
      className="vt-combat-ring"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: dark,
        minHeight: '100vh',
        color: '#F4F4F5',
        fontFamily: "'Oswald', 'Montserrat', -apple-system, sans-serif",
      }}
    >
      {/* Header */}
      <header style={{ padding: '20px 0 16px', borderBottom: `2px solid ${red}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>🥊 🥋 🥇</span>
          <span
            style={{
              backgroundColor: red,
              color: '#FFFFFF',
              fontSize: '0.72rem',
              fontWeight: 900,
              padding: '3px 8px',
              borderRadius: '2px',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            CHAMPIONSHIP RING
          </span>
        </div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.86rem', color: '#A1A1AA' }}>
          Muay Thai, Boxing, BJJ & High-Impact Combat Conditioning
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.82rem', color: gold, fontWeight: 700 }}>
            CORNER // {touchpointLabel || 'Ring / Bag #'}: <strong>{touchpointValue}</strong>
          </div>
        )}
      </header>

      {/* Round & Knockout Rating */}
      <section
        style={{
          background: cardBg,
          borderRadius: '4px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 900, color: '#FAFAFA', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 16px 0' }}>
          {t.howWasVisit}
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', marginBottom: '14px' }}>
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
                  padding: '12px 2px',
                  borderRadius: '2px',
                  border: isExact ? `2px solid ${red}` : isSel ? `1px solid ${red}` : `1px solid ${border}`,
                  background: isExact ? red : isSel ? `${red}25` : '#18181B',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.6rem', marginBottom: '4px' }}>
                  {val === 5 ? '🏆' : val >= 4 ? '🥊' : val >= 3 ? '🥋' : '👊'}
                </span>
                <span style={{ fontSize: '0.7rem', fontWeight: 900, color: isExact ? '#FFFFFF' : isSel ? gold : '#71717A' }}>
                  {ROUND_NAMES[val - 1]}
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 800, color: gold }}>
            {ratingLabel}
          </div>
        )}
      </section>

      {/* Combat Disciplines Selector */}
      <section
        style={{
          background: cardBg,
          borderRadius: '4px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 900, color: '#FAFAFA', textTransform: 'uppercase', margin: '0 0 14px 0' }}>
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
                  padding: '8px 12px',
                  borderRadius: '2px',
                  border: isSel ? `1px solid ${red}` : `1px solid ${border}`,
                  background: isSel ? red : '#18181B',
                  color: '#FFFFFF',
                  fontWeight: 800,
                  fontSize: '0.82rem',
                  textTransform: 'uppercase',
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
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: '#A1A1AA', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '2px',
              border: `1px solid ${border}`,
              background: '#18181B',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Coach Advice Suggestions */}
      <section
        style={{
          background: cardBg,
          borderRadius: '4px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 900, color: '#FAFAFA', textTransform: 'uppercase', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>

        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '2px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${red}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${red}15` : '#18181B',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 900, color: gold, textTransform: 'uppercase', marginBottom: '4px' }}>
              ROUND ANALYSIS // {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E4E4E7', lineHeight: '1.4' }}>
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
            backgroundColor: red,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '2px',
            fontWeight: 900,
            fontSize: '1.1rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            cursor: 'pointer',
            marginTop: '12px',
            boxShadow: `0 4px 16px ${red}60`,
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      {/* Footer */}
      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#71717A' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>{' '}
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: red, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
