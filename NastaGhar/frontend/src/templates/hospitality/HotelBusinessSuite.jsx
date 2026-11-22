import React from 'react';

/**
 * T04 — Executive Business & Transit Suite (hotel_business_suite / hotel_executive)
 * Visual Structure: Executive slate (#1E293B), platinum silver (#CBD5E1), corporate blue (#2563EB).
 * Hero: Airport transit & lounge, corporate suite banner.
 * Rating: Precision metric bar (1 to 5 corporate rating blocks).
 * Topics: Sleek badge pills.
 * Suggestions: Structured executive briefing cards with blue accent bars.
 */
export default function HotelBusinessSuite({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Novus Executive Tower & Suites';
  const blue = '#2563EB';
  const slate = '#1E293B';
  const slateDark = '#0F172A';
  const border = '#334155';

  return (
    <div
      className="vt-business-suite"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: slateDark,
        minHeight: '100vh',
        color: '#F1F5F9',
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      <header style={{ padding: '20px 0 16px', borderBottom: `2px solid ${blue}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '2rem' }}>✈️ 💼 🏢</span>
          <span style={{ backgroundColor: blue, color: '#FFFFFF', fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
            EXECUTIVE_LEVEL
          </span>
        </div>
        <h1 style={{ fontSize: '1.95rem', fontWeight: 800, color: '#FFFFFF', margin: '0 0 4px 0', letterSpacing: '-0.5px' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
            RESERVATION: [{touchpointLabel || 'Suite Number'}: <span style={{ color: blue, fontWeight: 700 }}>{touchpointValue}</span>]
          </div>
        )}
      </header>

      {/* Precision Metric Bar Rating */}
      <section
        style={{
          background: slate,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h2 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#CBD5E1', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {t.howWasVisit}
          </h2>
          <span style={{ fontSize: '1.1rem', fontWeight: 800, color: blue }}>
            INDEX: {rating} / 5
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
                  border: isExact ? `2px solid ${blue}` : `1px solid ${border}`,
                  background: isExact ? blue : isSel ? `${blue}30` : '#0F172A',
                  color: isExact ? '#FFFFFF' : isSel ? blue : '#64748B',
                  fontWeight: 800,
                  fontSize: '1.1rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {val}★
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: blue }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Sleek Badge Pills */}
      <section
        style={{
          background: slate,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.85rem', fontWeight: 800, color: '#CBD5E1', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
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
                  border: isSel ? `1px solid ${blue}` : `1px solid ${border}`,
                  background: isSel ? `${blue}20` : '#0F172A',
                  color: isSel ? blue : '#94A3B8',
                  fontSize: '0.82rem',
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
            placeholder={t.notePlaceholder}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '4px',
              border: `1px solid ${border}`,
              background: '#0F172A',
              color: '#FFFFFF',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
            }}
          />
        </div>
      </section>

      {/* Briefing Cards */}
      <section
        style={{
          background: slate,
          borderRadius: '8px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.85rem', fontWeight: 800, color: '#CBD5E1', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 12px 0' }}>
          {t.reviewIdeas}
        </h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              borderLeft: selectedIdeaId === idea.id ? `4px solid ${blue}` : `4px solid ${border}`,
              borderTop: `1px solid ${border}`,
              borderRight: `1px solid ${border}`,
              borderBottom: `1px solid ${border}`,
              background: selectedIdeaId === idea.id ? `${blue}15` : '#0F172A',
              marginBottom: '10px',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: blue, textTransform: 'uppercase', marginBottom: '4px' }}>
              EXECUTIVE_BRIEF: {idea.focus}
            </div>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#E2E8F0', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: blue,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      <footer style={{ textAlign: 'center', fontSize: '0.82rem', color: '#94A3B8' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: blue, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
