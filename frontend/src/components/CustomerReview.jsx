import { useState, useEffect } from 'react';
import NastaGharRestaurantScene from './NastaGharRestaurantScene';

// ─── NASTA GHAR BRAND CONSTANTS ──────────────────────────────────────────────
// These are hardcoded. The API enriches config but NEVER overrides the name.
const BRAND = {
  name: 'Nasta Ghar',
  emoji: '🍳',
  category: 'Breakfast & Snacks · Rajkot',
  googleMapUrl:
    'https://search.google.com/local/writereview?placeid=ChIJEGXiuzcAy1k51pOxt51jLro',
};

const DEFAULT_TOPICS = [
  { label: 'Breakfast', icon: '🍳' },
  { label: 'Chai & Tea', icon: '☕' },
  { label: 'Snacks', icon: '🥪' },
  { label: 'Taste & Flavour', icon: '😋' },
  { label: 'Friendly Staff', icon: '😊' },
  { label: 'Cleanliness', icon: '✨' },
  { label: 'Value for Money', icon: '💰' },
  { label: 'Quick Service', icon: '⚡' },
];

const RATING_LABELS = {
  5: { text: 'Loved it!', emoji: '🤩' },
  4: { text: 'Really good', emoji: '😊' },
  3: { text: 'It was okay', emoji: '🙂' },
  2: { text: 'Disappointed', emoji: '😕' },
  1: { text: 'Not good', emoji: '😞' },
};

export default function CustomerReview({
  businessId = 'default_business',
  onSwitchToOwner = null,
  isPreview = false,
}) {
  const urlParams = new URLSearchParams(window.location.search);
  const tableParam = urlParams.get('table') || null;
  const isPreviewMode = isPreview || urlParams.get('preview') === 'true';

  // Step state
  const [step, setStep] = useState(1);

  // Rating
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);

  // Topics
  const [availableTopics, setAvailableTopics] = useState(DEFAULT_TOPICS);
  const [selectedTopics, setSelectedTopics] = useState(['Breakfast', 'Chai & Tea']);
  const [nothingSpecific, setNothingSpecific] = useState(false);
  const [personalNote, setPersonalNote] = useState('');

  // Google Review URL (from API, fallback to hardcoded)
  const [googleReviewUrl, setGoogleReviewUrl] = useState(BRAND.googleMapUrl);
  const [isUrlConfigured, setIsUrlConfigured] = useState(true);

  // Ideas
  const [ideas, setIdeas] = useState([]);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);

  // Editor
  const [draftReview, setDraftReview] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Session & analytics
  const [sessionId, setSessionId] = useState('');

  // Handoff
  const [handoffOpen, setHandoffOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [copyAgainSuccess, setCopyAgainSuccess] = useState(false);

  // Private feedback
  const [showPrivate, setShowPrivate] = useState(false);
  const [privateNote, setPrivateNote] = useState('');
  const [privateContact, setPrivateContact] = useState('');
  const [privateSent, setPrivateSent] = useState(false);

  // Cookie & Auto-Paste Consent
  const [cookieConsent, setCookieConsent] = useState(() => {
    try {
      return localStorage.getItem('ng_auto_paste_consent') === 'true';
    } catch {
      return false;
    }
  });

  const handleAcceptConsent = () => {
    try {
      localStorage.setItem('ng_auto_paste_consent', 'true');
    } catch {}
    setCookieConsent(true);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 2500);
  };

  // ─── FETCH CONFIG (optional enrichment, never overrides brand name) ─────────
  useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/businesses/${businessId}/review-link`)
      .then((r) => r.json())
      .then((d) => {
        // Only update Google URL if configured, never update name
        if (d.review_url && d.is_configured) {
          setGoogleReviewUrl(d.review_url);
          setIsUrlConfigured(true);
        }
        // Update topics from API if available
        if (d.topics && d.topics.length > 0) {
          const enriched = d.topics.map((t) => ({
            label: t,
            icon: getTopicIcon(t),
          }));
          setAvailableTopics(enriched);
          setSelectedTopics(d.topics.slice(0, 2));
        }
      })
      .catch(() => {/* use defaults */});

    // Initialize session
    fetch('http://127.0.0.1:8000/api/reviews/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        business_id: businessId,
        table_number: tableParam || 'Walk-in',
        dining_type: 'dine_in',
      }),
    })
      .then((r) => r.json())
      .then((d) => setSessionId(d.session_id))
      .catch(() => setSessionId(`local-${Date.now()}`));
  }, [businessId]);

  function getTopicIcon(label) {
    const l = label.toLowerCase();
    if (l.includes('breakfast') || l.includes('nasta')) return '🍳';
    if (l.includes('chai') || l.includes('tea') || l.includes('coffee') || l.includes('drink') || l.includes('beverage')) return '☕';
    if (l.includes('snack')) return '🥪';
    if (l.includes('taste') || l.includes('flavour') || l.includes('food')) return '😋';
    if (l.includes('staff') || l.includes('service') || l.includes('friendly')) return '😊';
    if (l.includes('clean')) return '✨';
    if (l.includes('value') || l.includes('money') || l.includes('price')) return '💰';
    if (l.includes('quick') || l.includes('fast') || l.includes('speed')) return '⚡';
    if (l.includes('atmosphere') || l.includes('vibe') || l.includes('ambience')) return '🌟';
    return '👍';
  }

  // ─── ANALYTICS ──────────────────────────────────────────────────────────────
  const logEvent = (name, meta = {}) => {
    if (!sessionId) return;
    fetch('http://127.0.0.1:8000/api/reviews/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        event_name: name,
        metadata: { business_id: businessId, rating, ...meta },
      }),
    }).catch(() => {});
  };

  // ─── BULLETPROOF CLIPBOARD COPY ─────────────────────────────────────────────
  const copyTextToClipboard = async (text) => {
    if (!text) return false;
    let ok = false;
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        ok = true;
      } catch (e) {
        console.warn('navigator.clipboard failed:', e);
      }
    }
    if (!ok) {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '-9999px';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        ok = document.execCommand('copy');
        document.body.removeChild(ta);
      } catch (e) {
        console.error('execCommand copy failed:', e);
      }
    }
    return ok;
  };

  // ─── HANDLERS ───────────────────────────────────────────────────────────────
  const handleRating = (s) => { setRating(s); logEvent('rating_selected', { rating: s }); };

  const toggleTopic = (label) => {
    setNothingSpecific(false);
    setSelectedTopics((prev) =>
      prev.includes(label) ? prev.filter((t) => t !== label) : [...prev, label]
    );
  };

  const handleProceedToIdeas = async () => {
    setLoadingIdeas(true);
    setStep(3);
    logEvent('aspects_selected', { aspects: selectedTopics });
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: nothingSpecific ? [] : selectedTopics,
          user_note: personalNote.trim(),
        }),
      });
      const data = await res.json();
      if (data.ideas?.length) setIdeas(data.ideas);
    } catch {
      // Fallback ideas
      setIdeas([
        {
          id: 'fb1',
          focus: 'Breakfast',
          text:
            rating >= 4
              ? `Really enjoyed the breakfast at ${BRAND.name}! Fresh, hot, and full of flavour. Definitely coming back! 🍳`
              : `Visited ${BRAND.name} for breakfast. Food was okay, hoping for a better experience next time.`,
        },
        {
          id: 'fb2',
          focus: 'Overall',
          text:
            rating >= 4
              ? `Great spot for chai and snacks. The staff were friendly and service was quick! ☕`
              : `The place has potential. Chai was good but some things could be improved.`,
        },
        {
          id: 'fb3',
          focus: 'Value',
          text:
            rating >= 4
              ? `Wonderful value for money! ${BRAND.name} offers great breakfast at very reasonable prices. Loved the chai ☕`
              : `Average experience. Could be better for the price.`,
        },
      ]);
    } finally {
      setLoadingIdeas(false);
    }
  };

  // 1-Click: Select, Auto-copy to clipboard, and Open Google Review directly
  const handlePostDirectly = async (idea) => {
    setSelectedIdeaId(idea.id);
    setDraftReview(idea.text);
    logEvent('idea_selected', { idea_id: idea.id });
    logEvent('review_approved', { length: idea.text.length, direct_post: true });

    // Notify Chrome Extension (if installed) for automatic pasting & star selection
    window.postMessage({
      type: 'NASTA_GHAR_REVIEW_SELECTED',
      payload: {
        reviewText: idea.text,
        rating: rating,
        timestamp: Date.now()
      }
    }, '*');

    const ok = await copyTextToClipboard(idea.text);
    setCopied(ok);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3500);

    logEvent('google_review_link_opened');
    window.open(googleReviewUrl, '_blank', 'noopener,noreferrer');
    setHandoffOpen(true);
  };

  // Customize/Edit idea in Step 4
  const handleSelectIdea = (idea) => {
    setSelectedIdeaId(idea.id);
    setDraftReview(idea.text);
    logEvent('idea_selected', { idea_id: idea.id });
    setStep(4);
  };

  const handleMakeNatural = async () => {
    setIsRegenerating(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: selectedTopics,
          user_note: personalNote.trim(),
          selected_idea: draftReview || undefined,
          emoji_preference: 'light',
        }),
      });
      const data = await res.json();
      if (data.review) setDraftReview(data.review);
    } catch { /* keep current */ }
    finally { setIsRegenerating(false); }
  };

  const handleContinueToGoogle = async () => {
    if (!draftReview.trim()) return;
    logEvent('review_approved', { length: draftReview.length });

    // Notify Chrome Extension (if installed) for automatic pasting & star selection
    window.postMessage({
      type: 'NASTA_GHAR_REVIEW_SELECTED',
      payload: {
        reviewText: draftReview,
        rating: rating,
        timestamp: Date.now()
      }
    }, '*');

    const ok = await copyTextToClipboard(draftReview);
    setCopied(ok);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3500);

    logEvent('google_review_link_opened');
    window.open(googleReviewUrl, '_blank', 'noopener,noreferrer');
    setHandoffOpen(true);
  };

  const handlePrivateFeedback = async (e) => {
    e.preventDefault();
    if (!privateNote.trim()) return;
    try {
      await fetch('http://127.0.0.1:8000/api/reviews/private-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          table_number: tableParam,
          rating,
          diner_note: privateNote,
          aspects: selectedTopics,
          guest_contact: privateContact,
        }),
      });
      setPrivateSent(true);
      logEvent('private_feedback_sent');
    } catch { setPrivateSent(true); }
  };

  const activeRating = hoverRating || rating;
  const ratingLabel = RATING_LABELS[activeRating] || RATING_LABELS[5];

  // ─── RENDER ─────────────────────────────────────────────────────────────────
  return (
    <div className="ng-page">
      {/* Preview Banner */}
      {isPreviewMode && (
        <div className="ng-preview-bar">
          <span>👁️ Owner Preview Mode</span>
          {onSwitchToOwner && (
            <button type="button" className="ng-preview-back" onClick={onSwitchToOwner}>
              ← Back to Dashboard
            </button>
          )}
        </div>
      )}

      <div className="ng-card">
        {/* ── HEADER ─────────────────────────────────────────────────────── */}
        <header className="ng-header">
          <div className="ng-logo-ring">
            <span className="ng-logo-emoji">{BRAND.emoji}</span>
          </div>
          <h1 className="ng-brand-name">{BRAND.name}</h1>
          <p className="ng-brand-sub">{BRAND.category}</p>
          {tableParam && (
            <span className="ng-table-pill">📍 {tableParam}</span>
          )}
        </header>

        {/* ── ANIMATED RESTAURANT SCENE ──────────────────────────────────── */}
        <NastaGharRestaurantScene />

        {/* ── PROGRESS DOTS ──────────────────────────────────────────────── */}
        <div className="ng-steps-row">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className={`ng-step-dot ${step >= s ? 'done' : ''} ${step === s ? 'active' : ''}`} />
          ))}
        </div>

        {/* ════════════════════════════════════════════════════════════════
            STEP 1 — RATING
        ════════════════════════════════════════════════════════════════ */}
        {step === 1 && (
          <div className="ng-step ng-fade-in">
            <h2 className="ng-step-title">How was your visit?</h2>
            <p className="ng-step-sub">Tap a star to rate your experience</p>

            <div className="ng-stars-row" role="radiogroup" aria-label="Star rating">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`ng-star ${activeRating >= s ? 'lit' : ''}`}
                  onClick={() => handleRating(s)}
                  onMouseEnter={() => setHoverRating(s)}
                  onMouseLeave={() => setHoverRating(0)}
                  aria-label={`${s} star${s > 1 ? 's' : ''}`}
                >
                  ★
                </button>
              ))}
            </div>

            <div className="ng-rating-label">
              <span className="ng-rating-emoji">{ratingLabel.emoji}</span>
              <span>{ratingLabel.text}</span>
            </div>

            <button type="button" className="ng-btn-primary" onClick={() => setStep(2)}>
              Continue →
            </button>
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════
            STEP 2 — TOPICS
        ════════════════════════════════════════════════════════════════ */}
        {step === 2 && (
          <div className="ng-step ng-fade-in">
            <h2 className="ng-step-title">What stood out?</h2>
            <p className="ng-step-sub">Pick anything that matched your visit</p>

            <div className="ng-chips-grid">
              {availableTopics.map(({ label, icon }) => {
                const selected = selectedTopics.includes(label);
                return (
                  <button
                    key={label}
                    type="button"
                    className={`ng-chip ${selected ? 'selected' : ''}`}
                    onClick={() => toggleTopic(label)}
                  >
                    <span className="ng-chip-icon">{icon}</span>
                    <span>{label}</span>
                  </button>
                );
              })}
              <button
                type="button"
                className={`ng-chip ng-chip-neutral ${nothingSpecific ? 'selected' : ''}`}
                onClick={() => { setNothingSpecific(true); setSelectedTopics([]); }}
              >
                <span className="ng-chip-icon">—</span>
                <span>Nothing specific</span>
              </button>
            </div>

            <div className="ng-note-wrap">
              <label htmlFor="ng-note" className="ng-note-label">
                Personal note <span className="ng-optional">(optional)</span>
              </label>
              <input
                id="ng-note"
                type="text"
                className="ng-note-input"
                placeholder="e.g. The poha was absolutely perfect! 😋"
                value={personalNote}
                onChange={(e) => setPersonalNote(e.target.value)}
                maxLength={100}
              />
            </div>

            <div className="ng-btn-row">
              <button type="button" className="ng-btn-secondary" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button type="button" className="ng-btn-primary" onClick={handleProceedToIdeas}>
                See Review Ideas →
              </button>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════
            STEP 3 — IDEA CARDS
        ════════════════════════════════════════════════════════════════ */}
        {step === 3 && (
          <div className="ng-step ng-fade-in">
            <h2 className="ng-step-title">Your review ideas</h2>
            <p className="ng-step-sub">Pick the one that feels right — you can edit it next!</p>

            {loadingIdeas ? (
              <div className="ng-loading-box">
                <div className="ng-loading-spinner">🍳</div>
                <p className="ng-loading-text">Crafting honest ideas for you...</p>
              </div>
            ) : (
              <div className="ng-ideas-list">
                {ideas.map((idea, i) => (
                  <div key={idea.id || i} className={`ng-idea-card ${selectedIdeaId === idea.id ? 'picked' : ''}`}>
                    <div className="ng-idea-meta">
                      <span className="ng-idea-num">Option {i + 1}</span>
                      <span className="ng-idea-focus">{idea.focus}</span>
                    </div>
                    <p className="ng-idea-text">"{idea.text}"</p>
                    <div className="ng-idea-actions">
                      <button
                        type="button"
                        className="ng-btn-post-direct"
                        onClick={() => handlePostDirectly(idea)}
                      >
                        🚀 Post to Google
                      </button>
                      <button
                        type="button"
                        className="ng-btn-edit-idea"
                        onClick={() => handleSelectIdea(idea)}
                        title="Customize or edit this review before posting"
                      >
                        ✏️ Customize
                      </button>
                    </div>
                  </div>
                ))}

                <div className="ng-divider"><span>or</span></div>

                <button
                  type="button"
                  className="ng-btn-write-own"
                  onClick={() => { setSelectedIdeaId('custom'); setDraftReview(''); setStep(4); }}
                >
                  ✍️ Write my own review
                </button>
              </div>
            )}

            <div style={{ marginTop: '1rem' }}>
              <button type="button" className="ng-btn-secondary" onClick={() => setStep(2)}>
                ← Change highlights
              </button>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════
            STEP 4 — EDITOR
        ════════════════════════════════════════════════════════════════ */}
        {step === 4 && (
          <div className="ng-step ng-fade-in">
            <div className="ng-editor-header">
              <h2 className="ng-step-title" style={{ margin: 0 }}>Your review</h2>
              <span className="ng-char-pill">{draftReview.length} chars</span>
            </div>
            <p className="ng-step-sub">Edit anything before posting — it's your words!</p>

            <div className="ng-textarea-wrap">
              <textarea
                className="ng-textarea"
                rows={5}
                value={draftReview}
                onChange={(e) => setDraftReview(e.target.value)}
                placeholder="Write your review here..."
              />
            </div>

            <div className="ng-editor-tools">
              <button
                type="button"
                className="ng-btn-tool"
                onClick={handleMakeNatural}
                disabled={isRegenerating || !draftReview.trim()}
              >
                {isRegenerating ? '✨ Refining...' : '✨ Make it more natural'}
              </button>
              <button
                type="button"
                className="ng-btn-tool"
                onClick={() => setStep(3)}
              >
                🔄 Try another idea
              </button>
            </div>

            <div className="ng-google-notice">
              ✅ You post directly on Google — your words, your review.
            </div>

            <button
              type="button"
              className="ng-btn-primary ng-btn-cta"
              onClick={handleContinueToGoogle}
              disabled={!draftReview.trim()}
            >
              🚀 Copy & Post to Google
            </button>

            <div className="ng-private-prompt">
              Want to tell us privately?{' '}
              <button type="button" className="ng-link-btn" onClick={() => setShowPrivate(true)}>
                Send private note
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ════════ FLOATING COPY TOAST ════════ */}
      {showCopyToast && (
        <div className="ng-toast" role="alert">
          <span className="ng-toast-icon">📋</span>
          <span className="ng-toast-msg">Review copied to clipboard! Paste it on Google & tap Post.</span>
        </div>
      )}

      {/* ════════ HANDOFF MODAL ════════ */}
      {handoffOpen && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <div className="ng-modal-icon">📋</div>
            <h3 className="ng-modal-title">
              {copied ? 'Review Copied to Clipboard!' : 'Google Review Ready!'}
            </h3>
            <p className="ng-modal-body">
              Google Maps is opening for <strong>{BRAND.name}</strong>.
              Your review is copied — just paste and tap Post!
            </p>

            <div className="ng-modal-steps">
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">1</span>
                <span>Select <strong>{rating} stars</strong> on Google</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">2</span>
                <span><strong>Paste</strong> your review (Right-Click ➔ Paste or Ctrl+V)</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">3</span>
                <span>Tap <strong>Post</strong> — done in seconds! 🎊</span>
              </div>
            </div>

            <div className="ng-preview-box">
              <p className="ng-preview-text">"{draftReview}"</p>
              <button
                type="button"
                className="ng-btn-copy-mini"
                onClick={async () => {
                  await copyTextToClipboard(draftReview);
                  setCopyAgainSuccess(true);
                  setTimeout(() => setCopyAgainSuccess(false), 2000);
                }}
              >
                {copyAgainSuccess ? '✓ Copied!' : '📋 Copy Again'}
              </button>
            </div>

            <div className="ng-modal-actions">
              <button
                type="button"
                className="ng-btn-primary"
                onClick={() => window.open(googleReviewUrl, '_blank', 'noopener,noreferrer')}
              >
                ↗ Re-open Google Maps
              </button>
              <button
                type="button"
                className="ng-btn-secondary"
                onClick={() => setHandoffOpen(false)}
              >
                Done ✓
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ════════ PRIVATE FEEDBACK MODAL ════════ */}
      {showPrivate && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <h3 className="ng-modal-title">Direct note to {BRAND.name}</h3>
            <p className="ng-modal-body">Share anything you'd like our team to know privately.</p>

            {privateSent ? (
              <div className="ng-private-success">
                <span style={{ fontSize: '2rem' }}>💌</span>
                <h4>Thank you!</h4>
                <p>Your message has been sent directly to the team.</p>
                <button
                  type="button"
                  className="ng-btn-primary"
                  onClick={() => setShowPrivate(false)}
                  style={{ marginTop: '1rem' }}
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handlePrivateFeedback} className="ng-private-form">
                <textarea
                  className="ng-textarea"
                  rows={4}
                  placeholder="Share your thoughts, suggestions, or anything else..."
                  value={privateNote}
                  onChange={(e) => setPrivateNote(e.target.value)}
                  required
                />
                <input
                  type="text"
                  className="ng-note-input"
                  placeholder="Your name or contact (optional)"
                  value={privateContact}
                  onChange={(e) => setPrivateContact(e.target.value)}
                  style={{ marginTop: '0.75rem' }}
                />
                <div className="ng-modal-actions" style={{ marginTop: '1.25rem' }}>
                  <button type="submit" className="ng-btn-primary">Send to Team</button>
                  <button type="button" className="ng-btn-secondary" onClick={() => setShowPrivate(false)}>
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ════════ COOKIE & AUTO-PASTE PERMISSION BANNER ════════ */}
      {!cookieConsent && (
        <div className="ng-cookie-bar" role="region" aria-label="Auto-paste permission">
          <div className="ng-cookie-content">
            <span className="ng-cookie-emoji">🍪</span>
            <div className="ng-cookie-msg">
              <strong>Auto-Paste Enabled</strong>: Allow cookies & clipboard to automatically load your selected review so you can paste into Google with 1 tap.
            </div>
          </div>
          <button
            type="button"
            className="ng-cookie-btn"
            onClick={handleAcceptConsent}
          >
            Allow Auto-Paste ✓
          </button>
        </div>
      )}
    </div>
  );
}
