import React from 'react';

/**
 * G01 — High-Intensity CrossFit & Strength Forge (fitness_iron_forge / fitness_strength)
 * Visual Structure: Heavy cast iron (#111827), magma orange (#EA580C), industrial steel (#4B5563).
 * Hero: Barbell & kettlebell, iron gym banner.
 * Rating: Weight plate rating scale (45 LB bumper plate buttons).
 * Topics: Heavy-duty riveted badge tags.
 * Suggestions: Steel-stamped quote cards with orange hazard borders.
 */
export default function FitnessIronForge({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Iron Forge Strength & CrossFit';
  const magma = '#EA580C';
  const iron = '#111827';
  const ironCard = '#1F2937';
  const border = '#374151';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Incredible coaching, motivating energy and pristine facility! 💪';

  return (
    <div className="vt-page-container vt-iron-forge" style={{
        padding: '24px 16px',
        backgroundColor: iron,
        minHeight: '100vh',
        color: '#F9FAFB',
        fontFamily: "'Barlow Condensed', 'Oswald', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ padding: '20px 0 16px', borderBottom: `2px solid ${magma}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>🏋️ ⛓️ 🔥</span>
          <span style={{ backgroundColor: magma, color: '#000000', fontSize: '0.72rem', fontWeight: 900, padding: '2px 8px', borderRadius: '2px', textTransform: 'uppercase' }}>
            FORGED_STRENGTH
          </span>
        </div>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.82rem', color: '#9CA3AF', fontFamily: 'monospace' }}>
            RACK // [{touchpointLabel || 'Rig / Platform'}: <span style={{ color: magma }}>{touchpointValue}</span>]
          </div>
        )}
      </header>

      {/* 45LB Weight Bumper Plate Rating */}
      <section
        style={{
          background: ironCard,
          borderRadius: '4px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 900, color: '#E5E7EB', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', marginBottom: '12px' }}>
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
                  padding: '12px 0',
                  borderRadius: '4px',
                  border: isExact ? `2px solid ${magma}` : `1px solid ${border}`,
                  background: isExact ? magma : isSel ? `${magma}30` : '#111827',
                  color: isExact ? '#000000' : isSel ? magma : '#6B7280',
                  fontWeight: 900,
                  fontSize: '1.15rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {val * 10}★
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: 900, color: magma, textTransform: 'uppercase' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Riveted Badge Tags */}
      <section
        style={{
          background: ironCard,
          borderRadius: '4px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 900, color: '#E5E7EB', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
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
                  padding: '8px 14px',
                  borderRadius: '2px',
                  border: isSel ? `2px solid ${magma}` : `1px solid ${border}`,
                  background: isSel ? `${magma}25` : '#111827',
                  color: isSel ? magma : '#9CA3AF',
                  fontSize: '0.85rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                }}
              >
                <span>{top.icon}</span>
                <span>{top.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: '#9CA3AF', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '2px',
              border: `1px solid ${border}`,
              background: '#111827',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Suggestions */}
      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content"><section
        style={{
          background: ironCard,
          borderRadius: '4px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 900, color: '#E5E7EB', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '2px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${magma}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${magma}12` : '#111827',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 900, color: magma, textTransform: 'uppercase', marginBottom: '4px' }}>
              WOD // {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E5E7EB', lineHeight: '1.4', fontFamily: 'sans-serif' }}>
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
            backgroundColor: magma,
            color: '#000000',
            border: 'none',
            borderRadius: '2px',
            fontWeight: 900,
            fontSize: '1.1rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            cursor: 'pointer',
            marginTop: '12px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#6B7280' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: magma, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
