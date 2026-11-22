import React from 'react';

/**
 * H04 — Preventive Medicine, Holistic Health & Longevity (clinic_wellness_preventive / clinic_preventive)
 * RESTRICTED PREVIEW-ONLY:
 * - Automated review suggestions are disabled to ensure authentic patient feedback.
 * - Neutral patient privacy notice banner.
 * - Holistic botanical sage & deep forest (#3F6212 / #1A2E05), warm ivory background (#FEFCE8), lime border (#D9F99D).
 * - Consultation suite touchpoint, vitality blossom rating scale.
 */
export default function ClinicWellnessPreventive({ templateData, journeyState }) {
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
    draftReview,
    setDraftReview,
    onDirectGoogleHandoff,
    onOpenPrivateFeedback,
    t,
  } = journeyState;

  const bizName = templateData?.businessName || 'Living Well Preventive & Integrative Health';
  const olive = '#3F6212';
  const forest = '#1A2E05';
  const bg = '#FEFCE8';
  const border = '#D9F99D';

  const BLOSSOM_ICONS = ['🌱', '🌿', '🍃', '🌸', '🌟'];

  return (
    <div
      className="vt-clinic-preventive"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#1A2E05',
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}
    >
      {/* Neutral Patient Privacy Notice */}
      <div
        className="vt-privacy-notice"
        style={{
          backgroundColor: '#F7FEE7',
          border: '1px solid #BEF264',
          borderRadius: '8px',
          padding: '12px 14px',
          fontSize: '0.82rem',
          color: '#3F6212',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          lineHeight: '1.4',
        }}
      >
        <span style={{ fontSize: '1.2rem' }}>🔒</span>
        <span>
          <strong>Patient Privacy Notice:</strong> Automated suggestions are disabled. Please share your genuine words with the care team.
        </span>
      </div>

      {/* Header */}
      <header style={{ textAlign: 'center', padding: '16px 0', borderBottom: `1px solid ${border}` }}>
        <div style={{ fontSize: '2.2rem', marginBottom: '6px' }}>🌿 🩺 ☀️</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '1.5px', textTransform: 'uppercase', color: olive, fontWeight: 700, marginBottom: '4px' }}>
          Integrative Medicine & Preventive Wellness
        </div>
        <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: forest, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: olive, fontWeight: 600 }}>
            {touchpointLabel || 'Consultation Suite'}: <strong>{touchpointValue}</strong>
          </div>
        )}
      </header>

      {/* Vitality Blossom Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(63,98,18,0.08)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: forest, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '10px' }}>
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
                  padding: '10px 12px',
                  borderRadius: '10px',
                  border: isExact ? `2px solid ${olive}` : isSel ? `1px solid ${olive}` : '1px solid #E2E8F0',
                  background: isExact ? `${olive}20` : isSel ? `${olive}0A` : '#FAFAFA',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.6rem', transform: isSel ? 'scale(1.15)' : 'scale(1)', transition: 'transform 0.15s ease' }}>
                  {BLOSSOM_ICONS[val - 1]}
                </span>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: isSel ? olive : '#94A3B8', marginTop: '4px' }}>
                  {val}/5
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 700, color: olive }}>
            {ratingLabel}
          </div>
        )}
      </section>

      {/* Wellness Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: forest, margin: '0 0 12px 0' }}>
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
                  borderRadius: '999px',
                  border: isSel ? `1px solid ${olive}` : '1px solid #E2E8F0',
                  background: isSel ? olive : '#F8FAFC',
                  color: isSel ? '#FFFFFF' : '#1A2E05',
                  fontWeight: 600,
                  fontSize: '0.84rem',
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

      {/* Patient Experience Feedback Editor */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: forest, margin: '0 0 8px 0' }}>
          Your Wellness Experience
        </h3>
        <p style={{ margin: '0 0 12px 0', fontSize: '0.82rem', color: '#64748B' }}>
          Please share your personal reflection on your doctor consultation, wellness plan, lifestyle guidance, or clinic environment.
        </p>

        <textarea
          rows={4}
          value={draftReview || personalNote || ''}
          onChange={(e) => {
            if (setDraftReview) setDraftReview(e.target.value);
            if (setPersonalNote) setPersonalNote(e.target.value);
          }}
          placeholder="Share your thoughts about your wellness consultation, personalized advice, or staff warmth..."
          style={{
            width: '100%',
            padding: '12px 14px',
            borderRadius: '10px',
            border: '1px solid #CBD5E1',
            background: '#F8FAFC',
            color: '#1A2E05',
            fontSize: '0.9rem',
            lineHeight: '1.5',
            boxSizing: 'border-box',
            resize: 'vertical',
            fontFamily: 'inherit',
          }}
        />

        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview || personalNote || '')}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: olive,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '14px',
            boxShadow: '0 4px 14px rgba(63,98,18,0.25)',
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
          style={{ background: 'none', border: 'none', color: olive, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
