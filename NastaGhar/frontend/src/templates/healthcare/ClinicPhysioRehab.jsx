import React from 'react';

/**
 * H03 — Physical Therapy, Sports Rehab & Ortho Care (clinic_physio_rehab / clinic_physio)
 * RESTRICTED PREVIEW-ONLY:
 * - Automated review suggestions are disabled to ensure authentic patient feedback.
 * - Neutral patient privacy notice banner.
 * - Recovery cyan & deep slate (#0284C7 / #0F172A), mobility light blue (#F0F9FF), soft border (#BAE6FD).
 * - Physical therapy treatment bay touchpoint, mobility recovery progress scale.
 */
export default function ClinicPhysioRehab({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Kinetic Motion Physiotherapy & Sports Rehab';
  const cyan = '#0284C7';
  const slateDark = '#0F172A';
  const bg = '#F0F9FF';
  const border = '#BAE6FD';

  const MOBILITY_LEVELS = ['REST', 'MOBILITY', 'STRENGTH', 'RECOVERY', 'FULL MOTION'];

  return (
    <div
      className="vt-clinic-physio"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#0F172A',
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      {/* Neutral Patient Privacy Notice */}
      <div
        className="vt-privacy-notice"
        style={{
          backgroundColor: '#E0F2FE',
          border: '1px solid #7DD3FC',
          borderRadius: '8px',
          padding: '12px 14px',
          fontSize: '0.82rem',
          color: '#0369A1',
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
        <div style={{ fontSize: '2.2rem', marginBottom: '6px' }}>🏃 🦴 🩹</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '1.5px', textTransform: 'uppercase', color: cyan, fontWeight: 700, marginBottom: '4px' }}>
          Physical Therapy & Functional Rehabilitation
        </div>
        <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: slateDark, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: cyan, fontWeight: 600 }}>
            {touchpointLabel || 'Therapy Bay / Specialist'}: <strong>{touchpointValue}</strong>
          </div>
        )}
      </header>

      {/* Mobility Progress Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(2,132,199,0.08)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: slateDark, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', marginBottom: '10px' }}>
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
                  padding: '10px 4px',
                  borderRadius: '10px',
                  border: isExact ? `2px solid ${cyan}` : isSel ? `1px solid ${cyan}` : `1px solid #E2E8F0`,
                  background: isExact ? `${cyan}20` : isSel ? `${cyan}0A` : '#F8FAFC',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.5rem', marginBottom: '4px' }}>
                  {val === 5 ? '🏃‍♂️' : val >= 4 ? '🚶' : val >= 3 ? '🧍' : '🩹'}
                </span>
                <span style={{ fontSize: '0.65rem', fontWeight: 800, color: isSel ? cyan : '#94A3B8' }}>
                  {MOBILITY_LEVELS[val - 1]}
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 700, color: cyan }}>
            {ratingLabel}
          </div>
        )}
      </section>

      {/* Therapy Care Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: slateDark, margin: '0 0 12px 0' }}>
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
                  border: isSel ? `1px solid ${cyan}` : '1px solid #E2E8F0',
                  background: isSel ? cyan : '#F8FAFC',
                  color: isSel ? '#FFFFFF' : '#0F172A',
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

      {/* Direct Rehab Feedback Editor */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: slateDark, margin: '0 0 8px 0' }}>
          Your Rehabilitation Feedback
        </h3>
        <p style={{ margin: '0 0 12px 0', fontSize: '0.82rem', color: '#64748B' }}>
          Please share your personal experience regarding therapist attention, exercise guidance, pain relief, and facility equipment.
        </p>

        <textarea
          rows={4}
          value={draftReview || personalNote || ''}
          onChange={(e) => {
            if (setDraftReview) setDraftReview(e.target.value);
            if (setPersonalNote) setPersonalNote(e.target.value);
          }}
          placeholder="Share your experience regarding your recovery sessions, therapist care, or rehabilitation progress..."
          style={{
            width: '100%',
            padding: '12px 14px',
            borderRadius: '10px',
            border: '1px solid #CBD5E1',
            background: '#F8FAFC',
            color: '#0F172A',
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
            backgroundColor: cyan,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '14px',
            boxShadow: '0 4px 14px rgba(2,132,199,0.25)',
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
          style={{ background: 'none', border: 'none', color: cyan, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
