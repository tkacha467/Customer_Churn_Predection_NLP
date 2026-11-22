import React from 'react';

/**
 * B04 — Minimalist Aesthetic & Skincare Lab (beauty_skincare_lab / salon_clinical)
 * Visual Structure: Pure clinical white (#FFFFFF), cool slate (#475569), clinical cobalt (#2563EB).
 * Hero: Laboratory precision droplet, treatment session details.
 * Rating: Stepped laboratory dial / numerical precision slider (1.0 to 5.0).
 * Topics: Clean grid data chips with medical precision borders.
 * Suggestions: Lab report-style clean data cards with blue diagnostic accents.
 */
export default function SkincareAestheticLab({ templateData, journeyState }) {
  const {
    rating,
    setRating,
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

  const bizName = templateData?.businessName || 'Dermacell Skincare Lab';
  const cobalt = '#2563EB';
  const cobaltDark = '#1D4ED8';
  const slateText = '#334155';
  const border = '#E2E8F0';

  return (
    <div
      className="vt-skincare-lab"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: '#FFFFFF',
        minHeight: '100vh',
        color: slateText,
        fontFamily: "'Space Grotesk', 'Inter', monospace, sans-serif",
      }}
    >
      <header style={{ padding: '20px 0 16px', borderBottom: `2px solid ${border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '1.8rem' }}>🧴 🔬 💧</span>
          <span style={{ fontSize: '0.72rem', letterSpacing: '1px', textTransform: 'uppercase', color: cobalt, border: `1px solid ${cobalt}`, padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
            Clinical Aesthetics
          </span>
        </div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0F172A', margin: '0 0 4px 0', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.8rem', color: '#64748B', fontFamily: 'monospace' }}>
            REF_SESSION: [{touchpointLabel || 'Operatory'}: {touchpointValue}]
          </div>
        )}
      </header>

      {/* Stepped Numerical Laboratory Slider */}
      <section
        style={{
          border: `1px solid ${border}`,
          borderRadius: '8px',
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          background: '#F8FAFC',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0F172A', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {t.howWasVisit}
          </h2>
          <span style={{ fontSize: '1.15rem', fontWeight: 800, color: cobalt, fontFamily: 'monospace' }}>
            GRADE: {rating}.0 / 5.0
          </span>
        </div>

        <input
          type="range"
          min="1"
          max="5"
          step="1"
          value={rating}
          onChange={(e) => setRating(parseInt(e.target.value, 10))}
          style={{
            width: '100%',
            accentColor: cobalt,
            cursor: 'pointer',
            height: '6px',
            marginBottom: '12px',
          }}
        />

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px', fontSize: '0.75rem', fontFamily: 'monospace', color: '#64748B' }}>
          <span>[1.0 POOR]</span>
          <span>[2.0 FAIR]</span>
          <span>[3.0 GOOD]</span>
          <span>[4.0 GREAT]</span>
          <span style={{ color: cobalt, fontWeight: 700 }}>[5.0 OPTIMAL]</span>
        </div>
      </section>

      {/* Clinical Grid Data Chips */}
      <section
        style={{
          border: `1px solid ${border}`,
          borderRadius: '8px',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0F172A', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {t.whatStoodOut}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '8px' }}>
          {availableTopics.map((top) => {
            const isSel = selectedTopics.includes(top.label);
            return (
              <button
                key={top.label}
                type="button"
                onClick={() => toggleTopic(top.label)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 10px',
                  borderRadius: '4px',
                  border: isSel ? `2px solid ${cobalt}` : `1px solid ${border}`,
                  background: isSel ? `${cobalt}10` : '#FFFFFF',
                  color: isSel ? cobaltDark : '#475569',
                  fontSize: '0.82rem',
                  fontWeight: isSel ? 700 : 500,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <span>{top.icon}</span>
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{top.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '6px' }}>
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
              borderRadius: '4px',
              border: `1px solid ${border}`,
              background: '#F8FAFC',
              fontSize: '0.88rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Lab Report Style Cards */}
      <section
        style={{
          border: `1px solid ${border}`,
          borderRadius: '8px',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0F172A', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${cobalt}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${cobalt}08` : '#FFFFFF',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: cobalt, textTransform: 'uppercase', marginBottom: '4px', fontFamily: 'monospace' }}>
              DIAGNOSTIC_FOCUS: {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#1E293B', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: cobalt,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 800,
            fontSize: '0.95rem',
            cursor: 'pointer',
            marginTop: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#64748B' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: cobalt, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
