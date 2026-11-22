import React from 'react';

/**
 * H01 — Multi-Specialty Hospital & Medical Center (clinic_multi_specialty / clinic_general)
 * RESTRICTED PREVIEW-ONLY:
 * - Automated review suggestions are disabled to ensure authentic patient feedback.
 * - Neutral patient privacy notice banner.
 * - Clinical deep ocean blue (#0369A1), sterile serene background (#F0F9FF), sky border (#BAE6FD).
 * - Stethoscope & clinical cross hero, medical department touchpoint.
 */
export default function ClinicMultiSpecialty({ templateData, journeyState }) {
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

  const bizName = templateData?.businessName || 'Apex Multi-Specialty Medical Center';
  const ocean = '#0369A1';
  const oceanDark = '#0C4A6E';
  const bg = '#F0F9FF';
  const border = '#BAE6FD';

  return (
    <div
      className="vt-clinic-multispecialty"
      style={{
        maxWidth: '580px',
        margin: '0 auto',
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#0F172A',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Neutral Patient Privacy Notice */}
      <div
        className="vt-privacy-notice"
        style={{
          backgroundColor: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: '8px',
          padding: '12px 14px',
          fontSize: '0.82rem',
          color: '#1E40AF',
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
        <div style={{ fontSize: '2.2rem', marginBottom: '6px' }}>🩺 🏥 🤍</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '1.5px', textTransform: 'uppercase', color: ocean, fontWeight: 700, marginBottom: '4px' }}>
          Consultation & Multi-Specialty Care
        </div>
        <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: oceanDark, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: ocean, fontWeight: 600 }}>
            {touchpointLabel || 'Department / Room'}: <strong>{touchpointValue}</strong>
          </div>
        )}
      </header>

      {/* Pulse / Heart Rhythm Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(3,105,161,0.08)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: oceanDark, margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '10px' }}>
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
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: isExact ? `2px solid ${ocean}` : isSel ? `1px solid ${ocean}` : `1px solid #E2E8F0`,
                  background: isExact ? `${ocean}15` : isSel ? `${ocean}08` : '#F8FAFC',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.6rem', transform: isSel ? 'scale(1.15)' : 'scale(1)', transition: 'transform 0.15s ease' }}>
                  {isSel ? '❤️' : '🤍'}
                </span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: isSel ? ocean : '#94A3B8', marginTop: '4px' }}>
                  {val}/5
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 700, color: ocean }}>
            {ratingLabel}
          </div>
        )}
      </section>

      {/* Clinical Care Touchpoints */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: oceanDark, margin: '0 0 12px 0' }}>
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
                  border: isSel ? `1px solid ${ocean}` : '1px solid #E2E8F0',
                  background: isSel ? ocean : '#F8FAFC',
                  color: isSel ? '#FFFFFF' : '#334155',
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

      {/* Authentic Patient Review / Feedback Editor */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: oceanDark, margin: '0 0 8px 0' }}>
          Your Patient Experience
        </h3>
        <p style={{ margin: '0 0 12px 0', fontSize: '0.82rem', color: '#64748B' }}>
          Please write directly in your own words regarding your visit, our care team, and facilities.
        </p>

        <textarea
          rows={4}
          value={draftReview || personalNote || ''}
          onChange={(e) => {
            if (setDraftReview) setDraftReview(e.target.value);
            if (setPersonalNote) setPersonalNote(e.target.value);
          }}
          placeholder="Share your thoughts about the doctors, nursing staff, wait times, or cleanliness..."
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
            backgroundColor: ocean,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '1rem',
            letterSpacing: '0.3px',
            cursor: 'pointer',
            marginTop: '14px',
            boxShadow: '0 4px 14px rgba(3,105,161,0.25)',
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
          style={{ background: 'none', border: 'none', color: ocean, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div>
  );
}
