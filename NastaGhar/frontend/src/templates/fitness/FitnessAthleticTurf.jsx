import React from 'react';

/**
 * G05 — Field Turf, Agility & Athletic Conditioning (fitness_athletic_turf / fitness_turf)
 * Visual Structure: Stadium field turf green (#14532D), bright yard lines (#F8FAFC), solar gold (#FBBF24).
 * Hero: Field turf sprint lanes, agility cones, stadium scoreboard banner.
 * Rating: Stopwatch split-time rating scale (Split 1 to Split 5 gold medal).
 * Topics: Field drill tags (Sled Push, Agility Turf, Sprint Lane, Kettlebell, Mobility).
 * Suggestions: Coach whistle playbook cards.
 */
export default function FitnessAthleticTurf({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'ProTurf Field & Athletic Performance';
  const turf = '#14532D';
  const turfDark = '#052E16';
  const gold = '#FBBF24';
  const yardLine = '#22C55E';
  const border = '#166534';

  const SPLIT_MARKS = ['SPLIT 1', 'SPLIT 2', 'SPLIT 3', 'SPLIT 4', 'RECORD SPLIT'];

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Incredible coaching, motivating energy and pristine facility! 💪';

  return (
    <div className="vt-page-container vt-athletic-turf" style={{
        padding: '24px 16px',
        backgroundColor: turfDark,
        minHeight: '100vh',
        color: '#F8FAFC',
        fontFamily: "'Inter', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      {/* Field Header */}
      <header style={{ padding: '20px 0 16px', borderBottom: `2px dashed ${yardLine}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>🏟️ ⏱️ 🏃</span>
          <span
            style={{
              backgroundColor: gold,
              color: '#052E16',
              fontSize: '0.72rem',
              fontWeight: 900,
              padding: '3px 8px',
              borderRadius: '4px',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            FIELD_TURF 100YD
          </span>
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.86rem', color: '#86EFAC' }}>
          Turf Sleds, Sprint Drills, Functional Movement & Plyometrics
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.82rem', color: '#BBF7D0', fontWeight: 700 }}>
            YARD // {touchpointLabel || 'Lane / Field Section'}: <span style={{ color: gold }}>{touchpointValue}</span>
          </div>
        )}
      </header>

      {/* Stopwatch Split Rating */}
      <section
        style={{
          background: '#0B3A1C',
          borderRadius: '12px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 6px 24px rgba(0,0,0,0.4)',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 800, color: '#F0FDF4', margin: '0 0 16px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
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
                  borderRadius: '8px',
                  border: isExact ? `2px solid ${gold}` : isSel ? `1px solid ${yardLine}` : `1px solid ${border}`,
                  background: isExact ? `${gold}25` : isSel ? `${yardLine}20` : '#052E16',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.6rem', marginBottom: '4px' }}>
                  {val === 5 ? '🏅' : val >= 4 ? '⏱️' : val >= 3 ? '👟' : '🚩'}
                </span>
                <span style={{ fontSize: '0.68rem', fontWeight: 900, color: isExact ? gold : isSel ? '#86EFAC' : '#4ADE80' }}>
                  {SPLIT_MARKS[val - 1]}
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 800, color: gold }}>
            {typeof ratingLabel === 'string' ? ratingLabel : `${ratingLabel?.emoji || ''} ${ratingLabel?.text || ''}`.trim()}
          </div>
        )}
      </section>

      {/* Field Drills Topic Selector */}
      <section
        style={{
          background: '#0B3A1C',
          borderRadius: '12px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#F0FDF4', margin: '0 0 14px 0' }}>
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
                  borderRadius: '6px',
                  border: isSel ? `1px solid ${gold}` : `1px solid ${border}`,
                  background: isSel ? gold : '#052E16',
                  color: isSel ? '#052E16' : '#DCFCE7',
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
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#86EFAC', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '6px',
              border: `1px solid ${border}`,
              background: '#052E16',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Playbook Feedback Cards */}
      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content"><section
        style={{
          background: '#0B3A1C',
          borderRadius: '12px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#F0FDF4', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>

        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              borderRadius: '6px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${gold}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${gold}15` : '#052E16',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: gold, textTransform: 'uppercase', marginBottom: '4px' }}>
              PLAYBOOK // {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#DCFCE7', lineHeight: '1.4' }}>
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
            backgroundColor: gold,
            color: '#052E16',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 900,
            fontSize: '1.05rem',
            letterSpacing: '0.5px',
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      {/* Footer */}
      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#86EFAC' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>{' '}
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: gold, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
