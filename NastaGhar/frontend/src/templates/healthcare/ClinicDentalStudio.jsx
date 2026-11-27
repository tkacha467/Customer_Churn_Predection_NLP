import React from 'react';

/**
 * H02 — Modern Dental Studio & Oral Health Clinic (clinic_dental_studio / clinic_dental)
 * RESTRICTED PREVIEW-ONLY:
 * - Automated review suggestions are disabled to ensure authentic patient feedback.
 * - Neutral patient privacy notice banner.
 * - Gentle dental mint (#0D9488), sparkling white (#F0FDFA), soft aqua border (#99F6E4).
 * - Dental operatory chair touchpoint, sparkling tooth rating scale.
 */
export default function ClinicDentalStudio({ templateData, journeyState = {} }) {
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

  const bizName = templateData?.businessName || 'Sparkle Gentle Dental & Orthodontics';
  const teal = '#0D9488';
  const tealDark = '#115E59';
  const bg = '#F0FDFA';
  const border = '#99F6E4';

    const placeholder = notePlaceholder || t.notePlaceholder || 'e.g. Attentive doctor, clear consultation and reassuring care! 🩺';

  return (
    <div className="vt-page-container vt-clinic-dental" style={{
        padding: '24px 16px',
        backgroundColor: bg,
        minHeight: '100vh',
        color: '#134E4A',
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      }}><div className="vt-split-layout"><div className="vt-split-sticky-sidebar">
      {/* Neutral Patient Privacy Notice */}
      <div
        className="vt-privacy-notice"
        style={{
          backgroundColor: '#CCFBF1',
          border: '1px solid #5EEAD4',
          borderRadius: '8px',
          padding: '12px 14px',
          fontSize: '0.82rem',
          color: '#0F766E',
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
        <div style={{ fontSize: '2.2rem', marginBottom: '6px' }}>🦷 ✨ 🪥</div>
        <div style={{ fontSize: '0.75rem', letterSpacing: '1.5px', textTransform: 'uppercase', color: teal, fontWeight: 700, marginBottom: '4px' }}>
          Oral Health & Painless Dentistry
        </div>
        <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: tealDark, margin: '0 0 6px 0' }}>
          {bizName}
        </h1>
        {touchpointValue && (
          <div style={{ marginTop: '6px', fontSize: '0.85rem', color: teal, fontWeight: 600 }}>
            {touchpointLabel || 'Operatory / Chair'}: <strong>{touchpointValue}</strong>
          </div>
        )}
      </header>

      {/* Sparkling Tooth Rating */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '24px 16px',
          margin: '20px 0',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(13,148,136,0.08)',
        }}
      >
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: tealDark, margin: '0 0 14px 0' }}>
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
                  border: isExact ? `2px solid ${teal}` : isSel ? `1px solid ${teal}` : `1px solid #E2E8F0`,
                  background: isExact ? `${teal}20` : isSel ? `${teal}0A` : '#FAFAFA',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.6rem', transform: isSel ? 'scale(1.15)' : 'scale(1)', transition: 'transform 0.15s ease' }}>
                  {isSel ? '🦷' : '🤍'}
                </span>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: isSel ? teal : '#94A3B8', marginTop: '4px' }}>
                  {val === 5 ? 'Painless' : `${val} Star`}
                </span>
              </button>
            );
          })}
        </div>

        {ratingLabel && (
          <div style={{ fontSize: '0.92rem', fontWeight: 700, color: teal }}>
            {typeof ratingLabel === 'string' ? ratingLabel : `${ratingLabel?.emoji || ''} ${ratingLabel?.text || ''}`.trim()}
          </div>
        )}
      </section>

      {/* Dental Topics */}
      <section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: tealDark, margin: '0 0 12px 0' }}>
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
                  border: isSel ? `1px solid ${teal}` : '1px solid #E2E8F0',
                  background: isSel ? teal : '#F8FAFC',
                  color: isSel ? '#FFFFFF' : '#134E4A',
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

      {/* Dental Feedback Editor */}
      </div>{/* RIGHT COLUMN: Authentic Review */}<div className="vt-split-content"><section
        style={{
          background: '#FFFFFF',
          borderRadius: '16px',
          border: `1px solid ${border}`,
          padding: '20px 16px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: tealDark, margin: '0 0 8px 0' }}>
          Your Dental Care Experience
        </h3>
        <p style={{ margin: '0 0 12px 0', fontSize: '0.82rem', color: '#64748B' }}>
          Please share your genuine experience regarding dental comfort, staff hygiene, treatment clarity, and pain management.
        </p>

        <textarea
          rows={4}
          value={draftReview || personalNote || ''}
          onChange={(e) => {
            if (setDraftReview) setDraftReview(e.target.value);
            if (setPersonalNote) setPersonalNote(e.target.value);
          }}
          placeholder="Share your thoughts about your dental cleaning, procedure comfort, or dentist guidance..."
          style={{
            width: '100%',
            padding: '12px 14px',
            borderRadius: '10px',
            border: '1px solid #CBD5E1',
            background: '#F8FAFC',
            color: '#134E4A',
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
            backgroundColor: teal,
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: 'pointer',
            marginTop: '14px',
            boxShadow: '0 4px 14px rgba(13,148,136,0.25)',
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
          style={{ background: 'none', border: 'none', color: teal, fontWeight: 700, textDecoration: 'underline', cursor: 'pointer', padding: 0 }}
        >
          {t.sendPrivateNote}
        </button>
      </footer>
    </div></div></div>
  );
}
