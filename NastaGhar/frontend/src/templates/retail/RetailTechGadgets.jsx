import React from 'react';

/**
 * R05 — Tech, Gadgets & Gaming Den (retail_tech_gadgets / retail_electronics)
 * Visual Structure: Cyber navy (#030712), electric cyan (#06B6D4), violet (#A855F7).
 * Hero: Cyber hardware & headset, HUD grid interface.
 * Rating: Neon energy bar / segmented LED power cells ([■■■■■]).
 * Topics: Circuit-board styled chip buttons.
 * Suggestions: Terminal/HUD style prompt boxes with glowing borders.
 */
export default function RetailTechGadgets({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'CyberCore Tech & Gaming Outpost';
  const cyan = '#06B6D4';
  const violet = '#A855F7';
  const cyberDark = '#030712';
  const cardBg = '#0B1329';
  const border = '#1E293B';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Great collection, perfect fit and helpful styling advice! 🛍️';

  return (
    <div className="vt-page-container vt-tech-gadgets" style={{
        padding: '24px 16px',
        backgroundColor: cyberDark,
        minHeight: '100vh',
        color: '#E0E7FF',
        fontFamily: "'Space Grotesk', monospace, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      <header style={{ padding: '20px 0 16px', borderBottom: `1px solid ${cyan}40` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>💻 🎧 🎮</span>
          <span style={{ color: cyan, border: `1px solid ${cyan}`, fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}>
            STATUS: OVERCLOCKED
          </span>
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#FFFFFF', margin: '0 0 4px 0', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.8rem', color: '#818CF8', fontFamily: 'monospace' }}>
            TERMINAL // [{touchpointLabel || 'Workstation'}: {touchpointValue}]
          </div>
        )}
      </header>

      {/* Segmented LED Power Cell Rating */}
      <section
        style={{
          background: cardBg,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: `0 0 20px ${cyan}15`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h2 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#94A3B8', margin: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
            {t.howWasVisit}
          </h2>
          <span style={{ fontSize: '0.95rem', fontWeight: 800, color: cyan, fontFamily: 'monospace' }}>
            PWR: {rating * 20}%
          </span>
        </div>

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
                  border: isExact ? `2px solid ${cyan}` : `1px solid ${border}`,
                  background: isExact ? `linear-gradient(180deg, ${cyan} 0%, ${violet} 100%)` : isSel ? `${cyan}20` : '#030712',
                  color: isExact ? '#000000' : isSel ? cyan : '#475569',
                  fontWeight: 900,
                  fontSize: '1.1rem',
                  fontFamily: 'monospace',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {val}⚡
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 800, color: cyan }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Circuit Board Tags */}
      <section
        style={{
          background: cardBg,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.85rem', fontWeight: 800, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 12px 0' }}>
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
                  borderRadius: '4px',
                  border: isSel ? `1px solid ${cyan}` : `1px solid ${border}`,
                  background: isSel ? `${cyan}20` : '#030712',
                  color: isSel ? cyan : '#94A3B8',
                  fontSize: '0.85rem',
                  fontWeight: 700,
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
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '4px',
              border: `1px solid ${border}`,
              background: '#030712',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* HUD Prompt Cards */}
      </div>{/* RIGHT COLUMN: Ideas & Google Handoff */}<div className="vt-split-content"><section
        style={{
          background: cardBg,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.85rem', fontWeight: 800, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${cyan}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${cyan}10` : '#030712',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', fontWeight: 800, color: violet, textTransform: 'uppercase', marginBottom: '4px', fontFamily: 'monospace' }}>
              SYS_LOG // {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E0E7FF', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            background: `linear-gradient(90deg, ${cyan} 0%, ${violet} 100%)`,
            color: '#000000',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 900,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            textTransform: 'uppercase',
            letterSpacing: '1px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#64748B' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: cyan, fontWeight: 800, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
