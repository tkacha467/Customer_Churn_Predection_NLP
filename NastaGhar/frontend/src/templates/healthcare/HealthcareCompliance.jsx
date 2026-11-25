import React from 'react';

/**
 * H00 — Healthcare Generic / Fallback Template
 * RESTRICTED PREVIEW-ONLY:
 * - Automated review suggestions are disabled to ensure authentic patient feedback.
 * - Direct patient experience feedback & confidential patient advocacy.
 * - Clinical teal (#0D9488) on sterile calm background (#F8FAFC).
 */
export default function HealthcareCompliance({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'CareWell Medical Center';
  const teal = '#0D9488';
  const tealDark = '#115E59';
  const bg = '#F8FAFC';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Attentive doctor, clear consultation and reassuring care! 🩺';

  return (
    <div className="vt-page-container vt-healthcare" style={{
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#1E293B',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      {/* Privacy Notice Banner */}
      <div
        className="vt-privacy-notice"
        style={{
          backgroundColor: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: '8px',
          padding: '10px 14px',
          fontSize: '0.8rem',
          color: '#1E40AF',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span>🔒</span>
        <span>
          <strong>Patient Privacy Notice:</strong> Automated suggestions are disabled. Please share your genuine words with the care team.
        </span>
      </div>

      <header style={{ textAlign: 'center', padding: '16px 0' }}>
        <div style={{ fontSize: '2rem', marginBottom: '6px' }}>🩺 🏥 🤍</div>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: tealDark, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#64748B' }}>
          Patient Care, Clinical Excellence & Health Services
        </p>
        {touchpointValue && (
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: teal, fontWeight: 700 }}>
            {touchpointLabel || 'Department / Room'}: {touchpointValue}
          </div>
        )}
      </header>

      {/* Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 4px 16px rgba(13,148,136,0.06)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1E293B', margin: '0 0 14px 0' }}>
          {t.howWasVisit}
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', fontSize: '2.5rem', cursor: 'pointer', marginBottom: '8px' }}>
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              onClick={() => setRating(star)}
              style={{
                color: star <= (hoverRating || rating) ? '#F59E0B' : '#E2E8F0',
                transition: 'transform 0.15s ease',
                transform: star <= (hoverRating || rating) ? 'scale(1.15)' : 'scale(1)',
              }}
            >
              ★
            </span>
          ))}
        </div>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: tealDark }}>
          {ratingLabel?.emoji} {ratingLabel?.text}
        </div>
      </section>

      {/* Topics */}
      </div>{/* RIGHT COLUMN: Authentic Review */}<div className="vt-split-content"><section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: '1px solid #E2E8F0',
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1E293B', margin: '0 0 12px 0' }}>
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
                  borderRadius: '16px',
                  border: isSel ? `2px solid ${teal}` : '1px solid #E2E8F0',
                  background: isSel ? `${teal}15` : '#F8FAFC',
                  color: isSel ? tealDark : '#475569',
                  fontSize: '0.85rem',
                  fontWeight: isSel ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                <span>{top.icon}</span>
                <span>{top.label}</span>
              </button>
            );
          })}
        </div>

        {/* Note / Feedback */}
        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#64748B', marginBottom: '6px' }}>
            {t.personalNote} ({t.optional})
          </label>
          <textarea
            rows={3}
            value={personalNote || draftReview}
            onChange={(e) => {
              setPersonalNote(e.target.value);
              setDraftReview(e.target.value);
            }}
            placeholder="Share your experience with the care team..."
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              background: '#F8FAFC',
              fontSize: '0.9rem',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
          />
        </div>

        {/* Direct Google Action */}
        <button
          type="button"
          onClick={() => onDirectGoogleHandoff(draftReview || personalNote)}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: teal,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '16px',
            boxShadow: '0 4px 14px rgba(13,148,136,0.25)',
          }}
        >
          {t.copyAndOpenGoogle}
        </button>
      </section>

      {/* Confidential Private Note */}
      <footer style={{ textAlign: 'center', fontSize: '0.85rem', color: '#64748B' }}>
        <span>Want to send confidential feedback to patient relations? </span>
        <button
          type="button"
          onClick={onOpenPrivateFeedback}
          style={{ background: 'none', border: 'none', color: tealDark, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
