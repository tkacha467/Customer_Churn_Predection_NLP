import { useState, useEffect, useRef } from 'react';
import RestaurantWorld from './RestaurantWorld';
import { apiFetch } from '../lib/api';

// ─── NASTA GHAR BRAND CONSTANTS ──────────────────────────────────────────────
// These are hardcoded. The API enriches config but NEVER overrides the name.
const BRAND = {
  name: 'Nasta Ghar',
  googleMapUrl:
    'https://www.google.com/maps/place/Nasta+ghar/@22.2876495,70.7565735,15z/data=!4m8!3m7!1s0x3959cb0037bbe265:0xba2e639db7b193d6!8m2!3d22.2875481!4d70.7565747!9m1!1b1!16s%2Fg%2F11yk9xk25r?entry=ttu&g_ep=EgoyMDI2MDkyMy4wIKXMDSoASAFQAw%3D%3D',
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
  const reviewCardRef = useRef(null);

  useEffect(() => {
    requestAnimationFrame(() => {
      if (step > 1) reviewCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      else document.querySelector('.ng-page')?.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }, [step]);

  // Rating
  const [rating, setRating] = useState(() => {
    try {
      const savedRating = Number(sessionStorage.getItem('nastaGharSelectedRating'));
      return savedRating >= 1 && savedRating <= 5 ? savedRating : 5;
    } catch {
      return 5;
    }
  });
  const [hoverRating, setHoverRating] = useState(0);

  // Topics
  const [availableTopics, setAvailableTopics] = useState(DEFAULT_TOPICS);
  const [selectedTopics, setSelectedTopics] = useState(['Breakfast', 'Chai & Tea']);
  const [nothingSpecific, setNothingSpecific] = useState(false);
  const [personalNote, setPersonalNote] = useState('');

  // Keep Google Maps pointed at the restaurant's selected destination.
  const [googleReviewUrl, setGoogleReviewUrl] = useState(BRAND.googleMapUrl);

  // Ideas
  const [ideas, setIdeas] = useState([]);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const carouselRef = useRef(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);

  const handleCarouselScroll = () => {
    if (!carouselRef.current) return;
    const { scrollLeft } = carouselRef.current;
    const cardWidth = 320;
    const idx = Math.min(ideas.length - 1, Math.max(0, Math.round(scrollLeft / cardWidth)));
    setCurrentCardIndex(idx);
  };

  const scrollCarousel = (direction) => {
    if (!carouselRef.current) return;
    const offset = direction === 'left' ? -320 : 320;
    carouselRef.current.scrollBy({ left: offset, behavior: 'smooth' });
  };

  const getFallbackIdeas = (r, note) => {
    const noteText = note && note.trim() ? ` ${note.trim().replace(/[.!]+$/, '')}.` : '';
    if (r === 5) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Amazing breakfast and best chai in town!${noteText} Loved it 🍳☕` },
        { id: 'opt2', focus: 'Food & Tea', text: `The food was fresh and the tea was super tasty.${noteText} Quick service too ☕😋` },
        { id: 'opt3', focus: 'Staff & Place', text: `Very friendly staff and clean place.${noteText} We had a great time here 😊✨` },
        { id: 'opt4', focus: 'Taste & Value', text: `Everything was hot, fresh and full of flavour. The snacks and chai were really good and the price is also fair.${noteText} Must try 👌🍲` },
        { id: 'opt5', focus: 'Family Visit', text: `Had a wonderful breakfast with family at ${BRAND.name}. Great food, friendly people, and relaxed vibe.${noteText} Will surely visit again! 👨‍👩‍👧‍👦❤️` },
      ];
    } else if (r === 4) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Good food and tasty chai!${noteText} Nice start to the morning 🍳` },
        { id: 'opt2', focus: 'Food & Service', text: `Fresh breakfast and quick service.${noteText} Staff was polite and helpful 👍☕` },
        { id: 'opt3', focus: 'Clean & Fair', text: `Clean sitting area and good food quality.${noteText} Prices are also reasonable 😊` },
        { id: 'opt4', focus: 'Snacks & Tea', text: `Enjoyed the snacks and hot tea. Food was served quickly and tasted nice.${noteText} Worth a visit for a quick bite 🥪🍲` },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall a very pleasant visit. Good taste, clean tables, and friendly service.${noteText} Will definitely come back again 🌟👍` },
      ];
    } else if (r === 3) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Decent food, but the service was a bit slow today.${noteText} 🙂` },
        { id: 'opt2', focus: 'Food & Tea', text: `The chai was nice, but the snacks could have been hotter.${noteText} Okay experience overall 🙂☕` },
        { id: 'opt3', focus: 'Wait Time', text: `Staff was polite, but we had to wait some time for our order.${noteText} Average visit 🙂` },
        { id: 'opt4', focus: 'Busy Hours', text: `The place was quite crowded today. Food taste was fine, but table cleaning took longer than expected.${noteText} Hope it gets faster next time 🙂🥪` },
        { id: 'opt5', focus: 'Overall Visit', text: `Fair experience overall. Tea was good and seating is comfortable, but service needs a little improvement.${noteText} It was an okay visit 🙂` },
      ];
    } else if (r === 2) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Food was okay, but wait time was too long today.${noteText} 😕` },
        { id: 'opt2', focus: 'Order Delay', text: `Not satisfied with the service today.${noteText} Order was delayed and food was lukewarm 😕` },
        { id: 'opt3', focus: 'Attention', text: `The place was noisy and staff was not paying attention.${noteText} Expected better service 😕` },
        { id: 'opt4', focus: 'Slow Service', text: `We had to wait a long time to get our food and tables were not cleaned quickly.${noteText} Need to improve customer service 😕⏳` },
        { id: 'opt5', focus: 'Overall Visit', text: `Disappointing visit today. The chai was fine but snacks were not fresh and service was very slow.${noteText} Hope management fixes this 😕` },
      ];
    } else {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Very slow service and cold food today.{noteText} 😞` },
        { id: 'opt2', focus: 'Order Issue', text: `Bad experience today.{noteText} Waited very long and our order was wrong 😞` },
        { id: 'opt3', focus: 'Cleanliness', text: `Staff was unorganized and tables were not clean.{noteText} Very poor service 😞` },
        { id: 'opt4', focus: 'Food & Wait', text: `Disappointed with the visit. Food took forever to arrive and tasted stale.{noteText} Nobody came to attend us properly 😞👎` },
        { id: 'opt5', focus: 'Overall Visit', text: `Extremely poor experience today. Long waiting time, cold food, and careless staff.{noteText} Needs major improvement in service 😞` },
      ];
    }
  };

  // Editor
  const [draftReview, setDraftReview] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Session & analytics
  const [sessionId, setSessionId] = useState('');

  // Handoff
  const [handoffOpen, setHandoffOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copyingReview, setCopyingReview] = useState(false);
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [copyAgainSuccess, setCopyAgainSuccess] = useState(false);

  // Private feedback
  const [showPrivate, setShowPrivate] = useState(false);
  const [privateNote, setPrivateNote] = useState('');
  const [privateContact, setPrivateContact] = useState('');
  const [privateSent, setPrivateSent] = useState(false);
  const [privateError, setPrivateError] = useState('');

  useEffect(() => {
    try {
      const savedReview = sessionStorage.getItem('nastaGharSelectedReview');
      const savedBusinessId = sessionStorage.getItem('nastaGharBusinessId');
      if (!savedReview || savedBusinessId !== businessId) return;
      setDraftReview(savedReview);
      setSelectedIdeaId(sessionStorage.getItem('nastaGharSelectedReviewId'));
      setRating(Number(sessionStorage.getItem('nastaGharSelectedRating')) || 5);
      setCopied(sessionStorage.getItem('nastaGharClipboardCopied') === 'true');
      setHandoffOpen(true);
    } catch {
      // Session storage can be unavailable in restricted browser contexts.
    }
  }, [businessId]);

  // Acknowledgement for the clipboard handoff instructions.
  const [cookieConsent, setCookieConsent] = useState(() => {
    try {
      return localStorage.getItem('ng_clipboard_notice_seen') === 'true';
    } catch {
      return false;
    }
  });

  const handleAcceptConsent = () => {
    try {
      localStorage.setItem('ng_clipboard_notice_seen', 'true');
    } catch {}
    setCookieConsent(true);
  };

  // ─── FETCH CONFIG (optional enrichment, never overrides brand name) ─────────
  useEffect(() => {
    apiFetch(`/api/businesses/${businessId}/review-link`)
      .then((r) => r.json())
      .then((d) => {
        if (d.review_url && d.is_configured) setGoogleReviewUrl(d.review_url);
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
    apiFetch(`/api/reviews/session`, {
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
  }, [businessId, tableParam]);

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
    apiFetch(`/api/reviews/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
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
      let ta;
      try {
        ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '-9999px';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        ok = document.execCommand('copy');
      } catch (e) {
        console.error('execCommand copy failed:', e);
      } finally {
        ta?.remove();
      }
    }
    return ok;
  };

  // ─── HANDLERS ───────────────────────────────────────────────────────────────
  const handleRating = (s) => {
    setRating(s);
    try { sessionStorage.setItem('nastaGharSelectedRating', String(s)); } catch {}
    logEvent('rating_selected', { rating: s });
  };

  const toggleTopic = (label) => {
    setNothingSpecific(false);
    setSelectedTopics((prev) =>
      prev.includes(label) ? prev.filter((t) => t !== label) : [...prev, label]
    );
  };

  const handleProceedToIdeas = async () => {
    setLoadingIdeas(true);
    setStep(3);
    setCurrentCardIndex(0);
    logEvent('aspects_selected', { aspects: selectedTopics });
    try {
      const res = await apiFetch(`/api/reviews/ideas`, {
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
      if (data.ideas && data.ideas.length >= 5) {
        setIdeas(data.ideas);
      } else {
        setIdeas(getFallbackIdeas(rating, personalNote));
      }
    } catch {
      setIdeas(getFallbackIdeas(rating, personalNote));
    } finally {
      setLoadingIdeas(false);
    }
  };

  // Begin the handoff from the customer's tap; clipboard access is requested immediately.
  const handlePostDirectly = async (idea) => {
    await startReviewHandoff(idea.text, idea.id);
  };

  const startReviewHandoff = async (reviewText, reviewId) => {
    if (!reviewText?.trim()) return;
    setSelectedIdeaId(reviewId);
    setDraftReview(reviewText);
    setHandoffOpen(true);
    setCopyingReview(true);
    setShowCopyToast(false);
    logEvent('review_selected', { review_id: reviewId });
    logEvent('idea_selected', { idea_id: reviewId });
    logEvent('review_approved', { length: reviewText.length, direct_post: true });
    logEvent('google_review_handoff_started', { review_id: reviewId });

    try {
      sessionStorage.setItem('nastaGharSelectedReview', reviewText);
      sessionStorage.setItem('nastaGharSelectedRating', String(rating));
      sessionStorage.setItem('nastaGharSelectedReviewId', String(reviewId ?? ''));
      sessionStorage.setItem('nastaGharSelectedAt', new Date().toISOString());
      sessionStorage.setItem('nastaGharBusinessId', businessId);
      sessionStorage.setItem('nastaGharGoogleMapsDestination', googleReviewUrl);
    } catch {
      // Continue the handoff even when session storage is unavailable.
    }

    const copiedSuccessfully = await copyTextToClipboard(reviewText);
    setCopyingReview(false);
    setCopied(copiedSuccessfully);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3500);
    try { sessionStorage.setItem('nastaGharClipboardCopied', String(copiedSuccessfully)); } catch {}
    logEvent(copiedSuccessfully ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: reviewId });

    if (copiedSuccessfully) {
      logEvent('google_maps_redirect', { destination: googleReviewUrl });
      logEvent('google_review_link_opened');
      window.location.href = googleReviewUrl;
      return;
    }

    // Keep the exact review visible with a retry and an explicit Maps fallback CTA.
    setHandoffOpen(true);
  };

  const handleMakeNatural = async () => {
    setIsRegenerating(true);
    try {
      const res = await apiFetch(`/api/reviews/generate`, {
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
    await startReviewHandoff(draftReview, selectedIdeaId);
  };

  const handlePrivateFeedback = async (e) => {
    e.preventDefault();
    if (!privateNote.trim()) return;
    setPrivateError('');
    try {
      const response = await apiFetch(`/api/reviews/private-feedback`, {
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
      if (!response.ok) throw new Error('Feedback request failed');
      setPrivateSent(true);
      logEvent('private_feedback_sent');
    } catch {
      setPrivateError('We couldn’t send your message right now. Please try again.');
    }
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

      <RestaurantWorld />

      <div ref={reviewCardRef} className={`ng-card ${step === 1 ? 'ng-rating-card' : ''}`}>
        {/* ── HEADER ─────────────────────────────────────────────────────── */}
        <header className="ng-header">
          <h1 className="ng-brand-name">નાસ્તા ઘર</h1>
          {tableParam && (
            <span className="ng-table-pill">📍 {tableParam}</span>
          )}
        </header>



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
            STEP 3 — HORIZONTAL IDEA CAROUSEL (5 OPTIONS)
        ════════════════════════════════════════════════════════════════ */}
        {step === 3 && (
          <div className="ng-step ng-fade-in">
            <h2 className="ng-step-title">Your review ideas</h2>
            <p className="ng-step-sub">Swipe left/right (1 to 5) & tap your favourite to post on Google Maps!</p>

            {loadingIdeas ? (
              <div className="ng-loading-box">
                <div className="ng-loading-spinner">🍳</div>
                <p className="ng-loading-text">Crafting 5 honest ideas for you...</p>
              </div>
            ) : (
              <>
                <div className="ng-carousel-indicator">
                  <span className="ng-carousel-count">
                    Review {currentCardIndex + 1} of {ideas.length}
                  </span>
                </div>

                <div className="ng-ideas-carousel-wrapper">
                  <button
                    type="button"
                    className="ng-carousel-nav-btn ng-nav-left"
                    onClick={() => scrollCarousel('left')}
                    aria-label="Previous review option"
                  >
                    ‹
                  </button>

                  <div
                    className="ng-ideas-carousel"
                    ref={carouselRef}
                    onScroll={handleCarouselScroll}
                  >
                    {ideas.map((idea, i) => (
                      <div
                        key={idea.id || i}
                        className={`ng-idea-card ${selectedIdeaId === idea.id ? 'picked' : ''}`}
                        onClick={() => handlePostDirectly(idea)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handlePostDirectly(idea);
                          }
                        }}
                      >
                        <div className="ng-idea-meta">
                          <span className="ng-idea-num">Option {i + 1}</span>
                          <span className="ng-idea-stars">{'★'.repeat(rating)}{'☆'.repeat(5 - rating)}</span>
                        </div>
                        <p className="ng-idea-text">"{idea.text}"</p>
                        <div className="ng-idea-tap-hint">
                          <span>📋 Tap to Copy & Open Google Maps →</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button
                    type="button"
                    className="ng-carousel-nav-btn ng-nav-right"
                    onClick={() => scrollCarousel('right')}
                    aria-label="Next review option"
                  >
                    ›
                  </button>
                </div>

                <div className="ng-divider"><span>or</span></div>

                <button
                  type="button"
                  className="ng-btn-write-own"
                  onClick={() => { setSelectedIdeaId('custom'); setDraftReview(''); setStep(4); }}
                >
                  ✍️ Write my own custom review
                </button>
              </>
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
              Your words, your review. Paste the copy into Google and post it yourself.
            </div>

            <button
              type="button"
              className="ng-btn-primary ng-btn-cta"
              onClick={handleContinueToGoogle}
              disabled={!draftReview.trim()}
            >
              Copy & open Google Maps
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
          <span className="ng-toast-msg">
            {copied
                ? "તમારો review તૈયાર છે ✓ Google Maps માં 'Write a review' tap કરો, same stars select કરીને Paste કરો."
                : 'Review copy na thayu. Tap Copy Review to try again.'}
          </span>
        </div>
      )}

      {/* ════════ HANDOFF MODAL ════════ */}
      {handoffOpen && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <div className="ng-modal-icon">📋</div>
            <h3 className="ng-modal-title">
              {copyingReview ? 'Preparing your review…' : copied ? 'Review Copied to Clipboard' : 'Copy Your Review to Continue'}
            </h3>
            <p className="ng-modal-body">
              {copyingReview
                ? <>તમારો review તૈયાર છે. Copy કરી રહ્યા છીએ અને Google Maps ખોલી રહ્યા છીએ…</>
                : copied
                ? <>તમારો review તૈયાર છે ✓ You selected {rating}★ here. On Google Maps, tap <strong>Write a review</strong>, select the same rating, then paste your review.</>
                : <>Review copy na thayu. Your selected review is saved for this browser session; copy it below and try again. You selected {rating}★ here, so choose the same rating on Google Maps.</>}
            </p>

            <div className="ng-modal-steps">
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">1</span>
                <span>Choose the rating that reflects your visit on Google (you selected <strong>{rating} stars</strong> here)</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">2</span>
                <span>{copyingReview ? 'Copying selected review…' : copied ? <><strong>Paste</strong> the copied review (use your device's Paste command, or long-press → Paste on mobile)</> : <>Copy the review below, then <strong>paste</strong> it into Google</>}</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">3</span>
                <span>Review it, then tap Google's <strong>Post</strong> button when you're ready.</span>
              </div>
            </div>

            <div className="ng-preview-box">
              <p className="ng-preview-text">"{draftReview}"</p>
              <button
                type="button"
                className="ng-btn-copy-mini"
                disabled={copyingReview}
                onClick={async () => {
                  const ok = await copyTextToClipboard(draftReview);
                  setCopied(ok);
                  setCopyAgainSuccess(ok);
                  try { sessionStorage.setItem('nastaGharClipboardCopied', String(ok)); } catch {}
                  logEvent(ok ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: selectedIdeaId });
                  if (ok) setTimeout(() => setCopyAgainSuccess(false), 2000);
                }}
              >
                {copyAgainSuccess ? '✓ Copied!' : copied ? '📋 Copy Again' : '📋 Copy Review'}
              </button>
            </div>

            <div className="ng-modal-actions">
              <button
                type="button"
                className="ng-btn-primary"
                disabled={copyingReview}
                onClick={() => {
                  logEvent('google_maps_redirect', { destination: googleReviewUrl });
                  logEvent('google_review_link_opened');
                  window.location.href = googleReviewUrl;
                }}
              >
                ↗ Continue to Google Maps
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
                {privateError && <p className="warning-box" role="alert">{privateError}</p>}
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

      {/* ════════ CLIPBOARD INFORMATION ════════ */}
      {!cookieConsent && step > 1 && (
          <div className="ng-cookie-bar" role="region" aria-label="Review and clipboard information">
          <div className="ng-cookie-content">
            <span className="ng-cookie-emoji">🍪</span>
            <div className="ng-cookie-msg">
              <strong>Your review is copied when you choose it.</strong> Paste it into Google and submit it yourself.
            </div>
          </div>
          <button
            type="button"
            className="ng-cookie-btn"
            onClick={handleAcceptConsent}
          >
            Got it ✓
          </button>
        </div>
      )}
    </div>
  );
}
