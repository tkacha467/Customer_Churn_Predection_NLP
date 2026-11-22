import React from 'react';

/**
 * FallbackTemplate — High-Contrast Accessible Neutral Card
 * Fallback skin when a specific template renderer is not assigned.
 */
export default function FallbackTemplate({ templateData, journeyState }) {
  const {
    rating,
    setRating,
    hoverRating,
    setHoverRating,
    ratingLabel,
    availableTopics,
    selectedTopics,
    toggleTopic,
    nothingSpecific,
    setNothingSpecific,
    personalNote,
    setPersonalNote,
    touchpointLabel,
    touchpointValue,
    ideas,
    loadingIdeas,
    selectedIdeaId,
    onSelectIdea,
    draftReview,
    setDraftReview,
    onDirectGoogleHandoff,
    onOpenPrivateFeedback,
    language,
    t,
  } = journeyState;

  const bizName = templateData?.businessName || 'Business';
  const accent = templateData?.theme?.primaryAccent || '#2563EB';

  return (
    <div className="vt-template vt-fallback-container" style={{ maxWidth: '640px', margin: '0 auto', padding: '16px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <header className="vt-header" style={{ textAlign: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0F172A', margin: '0 0 6px 0' }}>{bizName}</h1>
        {touchpointValue && (
          <span style={{ fontSize: '0.85rem', color: '#64748B', backgroundColor: '#F1F5F9', padding: '3px 10px', borderRadius: '12px' }}>
            {touchpointLabel}: {touchpointValue}
          </span>
        )}
      </header>

      {/* Rating Section */}
      <section className="vt-card" style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '16px', padding: '24px', textAlign: 'center', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#334155', marginBottom: '14px' }}>{t.howWasVisit}</h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.4rem', cursor: 'pointer', marginBottom: '10px' }}>
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              onClick={() => setRating(star)}
              style={{ color: star <= (hoverRating || rating) ? '#F59E0B' : '#CBD5E1', transition: 'transform 0.15s', transform: star <= (hoverRating || rating) ? 'scale(1.1)' : 'scale(1)' }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: 600, color: '#475569' }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics Section */}
      <section className="vt-card" style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '16px', padding: '20px', marginBottom: '20px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', marginBottom: '12px' }}>{t.whatStoodOut}</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
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
                  border: isSel ? `2px solid ${accent}` : '1px solid #E2E8F0',
                  background: isSel ? `${accent}15` : '#F8FAFC',
                  color: isSel ? accent : '#475569',
                  fontWeight: isSel ? 600 : 500,
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                }}
              >
                <span>{top.icon}</span>
                <span>{top.label}</span>
              </button>
            );
          })}
        </div>

        {/* Personal Note */}
        <div style={{ marginTop: '14px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#64748B', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <input
            type="text"
            value={personalNote}
            onChange={(e) => setPersonalNote(e.target.value)}
            placeholder={t.notePlaceholder}
            style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '0.9rem', boxSizing: 'border-box' }}
          />
        </div>
      </section>

      {/* Suggestions or Direct Review Action */}
      <section className="vt-card" style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '16px', padding: '20px', marginBottom: '20px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', marginBottom: '12px' }}>{t.reviewIdeas}</h3>
        {ideas.map((idea) => (
          <div
            key={idea.id}
            onClick={() => onSelectIdea(idea)}
            style={{
              padding: '14px',
              border: selectedIdeaId === idea.id ? `2px solid ${accent}` : '1px solid #E2E8F0',
              borderRadius: '10px',
              marginBottom: '10px',
              cursor: 'pointer',
              background: selectedIdeaId === idea.id ? `${accent}0A` : '#FFFFFF',
              transition: 'all 0.15s',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: accent, textTransform: 'uppercase', marginBottom: '4px' }}>{idea.focus}</div>
            <p style={{ margin: 0, fontSize: '0.92rem', color: '#1E293B', lineHeight: '1.4' }}>{idea.text}</p>
          </div>
        ))}

        {/* Google Handoff CTA */}
        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: accent,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 700,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          <span>{t.copyAndOpenGoogle}</span>
        </button>
      </section>

      {/* Private feedback option */}
      <footer style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.88rem', color: '#64748B' }}>
        <span>{rating >= 4 ? t.privatePromptGood : t.privatePromptBad}</span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: accent, fontWeight: 600, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
