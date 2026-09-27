import { useState, useEffect } from 'react';

const DINING_OCCASIONS = [
  { id: 'coffee_break', label: 'Coffee & Work', icon: '☕' },
  { id: 'brunch', label: 'Brunch & Pastries', icon: '🥐' },
  { id: 'lunch_dinner', label: 'Lunch / Dinner', icon: '🍽️' },
  { id: 'takeaway', label: 'Takeaway / Express', icon: '🥡' },
];

const HOSPITALITY_ASPECTS = [
  { id: 'Specialty Coffee', label: 'Specialty Coffee', icon: '☕' },
  { id: 'Food & Flavor', label: 'Food & Flavor', icon: '🍽️' },
  { id: 'Bakery & Pastries', label: 'Bakery & Pastries', icon: '🥐' },
  { id: 'Service & Hospitality', label: 'Service & Hospitality', icon: '🛎️' },
  { id: 'Vibe & Playlist', label: 'Vibe & Playlist', icon: '🕯️' },
  { id: 'Table Cleanliness', label: 'Cleanliness', icon: '✨' },
  { id: 'Order Wait Time', label: 'Order Wait Time', icon: '⏳' },
  { id: 'Value for Money', label: 'Value for Money', icon: '💰' },
  { id: 'Patio & Seating', label: 'Patio & Seating', icon: '🌿' },
];

const TONE_PERSONAS = [
  { id: 'natural', label: 'Natural Cafe Patron', icon: '☕' },
  { id: 'foodie', label: 'Foodie & Connoisseur', icon: '🍽️' },
  { id: 'casual', label: 'Casual & Upbeat', icon: '💬' },
  { id: 'short', label: 'Short & Punchy', icon: '⚡' },
];

export default function ReviewAssistant({ businessId = 'default_business' }) {
  // Read URL query params if diner scanned table QR (e.g. ?table=4&dining=coffee_break)
  const urlParams = new URLSearchParams(window.location.search);
  const initialTable = urlParams.get('table') || 'Table 4';
  const initialDining = urlParams.get('dining') || 'coffee_break';

  const [tableNumber, setTableNumber] = useState(initialTable);
  const [diningType, setDiningType] = useState(initialDining);
  const [rating, setRating] = useState(5);
  const [selectedAspects, setSelectedAspects] = useState(['Specialty Coffee', 'Service & Hospitality']);
  const [userNote, setUserNote] = useState('');
  const [tone, setTone] = useState('natural');
  const [length, setLength] = useState('medium');

  // Generation & NLP State
  const [draftReview, setDraftReview] = useState('');
  const [sentiment, setSentiment] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [ratingConsistent, setRatingConsistent] = useState(true);
  const [warnings, setWarnings] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [provider, setProvider] = useState('');

  // Private Manager Resolution Mode (for 1-2 star ratings)
  const [preferPrivateResolution, setPreferPrivateResolution] = useState(true);
  const [guestContact, setGuestContact] = useState('');
  const [privateSubmittedTicket, setPrivateSubmittedTicket] = useState(null);
  const [isSubmittingPrivate, setIsSubmittingPrivate] = useState(false);

  // Business & Google Link State
  const [businessName, setBusinessName] = useState('Cuore Cafe & Artisan Roastery');
  const [googleReviewUrl, setGoogleReviewUrl] = useState('');
  const [isUrlConfigured, setIsUrlConfigured] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Fetch business details
    fetch(`http://127.0.0.1:8000/api/businesses/${businessId}/review-link`)
      .then(res => res.json())
      .then(data => {
        setGoogleReviewUrl(data.review_url);
        setIsUrlConfigured(data.is_configured);
        if (data.business_name) setBusinessName(data.business_name);
      })
      .catch(err => console.error('Error fetching Google review link:', err));

    // Initialize session
    fetch('http://127.0.0.1:8000/api/reviews/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        business_id: businessId,
        table_number: tableNumber,
        dining_type: diningType
      })
    })
      .then(res => res.json())
      .then(data => setSessionId(data.session_id))
      .catch(err => console.error('Error initializing session:', err));
  }, [businessId, tableNumber, diningType]);

  const toggleAspect = (aspectId) => {
    if (selectedAspects.includes(aspectId)) {
      setSelectedAspects(selectedAspects.filter(a => a !== aspectId));
    } else {
      setSelectedAspects([...selectedAspects, aspectId]);
    }
  };

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    setIsGenerating(true);
    setWarnings([]);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/reviews/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: selectedAspects,
          user_note: userNote,
          tone,
          length,
          dining_type: diningType,
          table_number: tableNumber,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to draft review.');
      }

      const data = await response.json();
      setDraftReview(data.review);
      setSentiment(data.sentiment);
      setConfidence(data.sentiment_confidence);
      setRatingConsistent(data.rating_consistent);
      setWarnings(data.warnings || []);
      setProvider(data.generation_provider);
    } catch (error) {
      console.error('Generation failed:', error);
      alert(error.message || 'Generation failed. Please verify the backend is active.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleValidateDraft = async () => {
    if (!draftReview.trim()) return;
    setIsValidating(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/reviews/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, review: draftReview })
      });

      const data = await response.json();
      setSentiment(data.sentiment);
      setConfidence(data.confidence);
      setRatingConsistent(data.rating_consistent);
      setWarnings(data.warnings || []);
    } catch (err) {
      console.error('Validation error:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const handlePrivateFeedbackSubmit = async (e) => {
    e.preventDefault();
    if (!userNote.trim()) return;

    setIsSubmittingPrivate(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/reviews/private-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          table_number: tableNumber,
          rating,
          diner_note: userNote,
          aspects: selectedAspects,
          guest_contact: guestContact
        })
      });

      const data = await response.json();
      setPrivateSubmittedTicket(data);
    } catch (err) {
      console.error('Failed to submit private resolution:', err);
      alert('Error contacting management. Please notify your floor server.');
    } finally {
      setIsSubmittingPrivate(false);
    }
  };

  const handleCopyReview = () => {
    if (!draftReview) return;
    navigator.clipboard.writeText(draftReview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleOpenGoogle = () => {
    fetch('http://127.0.0.1:8000/api/reviews/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        event_name: 'google_review_link_clicked',
        metadata: { rating, sentiment, dining_type: diningType, table: tableNumber }
      })
    }).catch(() => {});

    navigator.clipboard.writeText(draftReview);
    if (googleReviewUrl) {
      window.open(googleReviewUrl, '_blank', 'noopener,noreferrer');
    }
    setShowConsentModal(false);
  };

  const ratingCaptions = {
    5: '✨ Exceptional Experience — Truly Memorable!',
    4: '👍 Very Good Experience — Lots to love!',
    3: '👌 Decent Visit — Standard with room to improve',
    2: '⚠️ Fell Below Expectations — Needs Operational Work',
    1: '❌ Subpar Experience — Failed on Standards'
  };

  return (
    <div className="review-assistant-wrapper">
      {/* Hospitality Banner */}
      <div className="hospitality-hero-card glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div className="section-badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' }}>
              Table QR Guest Experience
            </div>
            <h2 style={{ fontSize: '1.8rem', color: '#fff', margin: '0.25rem 0' }}>
              {businessName}
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Your feedback shapes our culinary craft and hospitality. Takes less than 45 seconds.
            </p>
          </div>

          <div className="table-badge-container">
            <span className="table-badge-icon">📍</span>
            <input
              type="text"
              className="table-input"
              value={tableNumber}
              onChange={(e) => setTableNumber(e.target.value)}
              placeholder="Table #"
              title="Click to edit table number"
            />
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        {/* STEP 1: Dine-In Review Configuration */}
        <div className="glass-panel">
          <div className="section-badge">Step 1 • Your Experience</div>
          <h3 style={{ fontSize: '1.4rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>
            How was your table today?
          </h3>

          {/* Dining Occasion Selector */}
          <div className="input-group" style={{ marginBottom: '1.25rem' }}>
            <label>Dining Occasion</label>
            <div className="occasion-grid">
              {DINING_OCCASIONS.map(occ => (
                <button
                  type="button"
                  key={occ.id}
                  className={`occasion-btn ${diningType === occ.id ? 'active' : ''}`}
                  onClick={() => setDiningType(occ.id)}
                >
                  <span style={{ fontSize: '1.2rem' }}>{occ.icon}</span>
                  <span>{occ.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 5-Star Interactive Rating */}
          <div className="input-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label>Star Rating</label>
              <span style={{ fontSize: '0.85rem', color: rating >= 4 ? '#fbbf24' : rating === 3 ? '#94a3b8' : '#f87171', fontWeight: 600 }}>
                {ratingCaptions[rating]}
              </span>
            </div>
            <div className="star-rating">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  type="button"
                  key={star}
                  className={`star-btn ${rating >= star ? 'active' : ''}`}
                  onClick={() => setRating(star)}
                >
                  ★
                </button>
              ))}
            </div>
          </div>

          {/* NEGATIVE FEEDBACK DEFLECTION CARD: Real-world restaurant manager resolution */}
          {rating <= 2 && preferPrivateResolution && !privateSubmittedTicket && (
            <div className="manager-resolution-card animate-fade">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.4rem' }}>🛎️</span>
                <h4 style={{ color: '#fbbf24', fontSize: '1.05rem', margin: 0 }}>
                  We Want to Make This Right Immediately
                </h4>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '0.75rem' }}>
                Our hospitality standard was not met. Send your feedback directly to our <strong>General Manager</strong> before posting publicly so we can personally follow up and resolve this.
              </p>

              <form onSubmit={handlePrivateFeedbackSubmit}>
                <textarea
                  rows="3"
                  className="resolution-textarea"
                  placeholder="Tell our General Manager what went wrong (e.g. coffee was cold, table wait was excessive)..."
                  value={userNote}
                  onChange={(e) => setUserNote(e.target.value)}
                  required
                />
                <input
                  type="text"
                  className="resolution-input"
                  placeholder="Your Email or Phone (so GM can reach out)"
                  value={guestContact}
                  onChange={(e) => setGuestContact(e.target.value)}
                  required
                  style={{ marginTop: '0.5rem' }}
                />
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                  <button type="submit" className="btn-primary" disabled={isSubmittingPrivate}>
                    {isSubmittingPrivate ? 'Routing to GM...' : '📩 Send Directly to General Manager'}
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setPreferPrivateResolution(false)}
                    style={{ fontSize: '0.8rem' }}
                  >
                    Draft Public Review Anyway
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Confirmation if private ticket sent */}
          {privateSubmittedTicket && (
            <div className="manager-ticket-success animate-fade">
              <span style={{ fontSize: '1.8rem' }}>✅</span>
              <div>
                <h4 style={{ color: '#34d399', margin: '0 0 0.25rem 0' }}>Ticket Logged: {privateSubmittedTicket.ticket_id}</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                  {privateSubmittedTicket.message}
                </p>
              </div>
            </div>
          )}

          {/* Standard Review Generator Workflow */}
          {(rating >= 3 || !preferPrivateResolution) && (
            <form onSubmit={handleGenerate}>
              {/* Hospitality Aspects Chips */}
              <div className="input-group">
                <label>What specific highlights stood out?</label>
                <div className="aspect-chips">
                  {HOSPITALITY_ASPECTS.map(asp => {
                    const isSelected = selectedAspects.includes(asp.id);
                    return (
                      <button
                        type="button"
                        key={asp.id}
                        className={`aspect-chip ${isSelected ? 'selected' : ''}`}
                        onClick={() => toggleAspect(asp.id)}
                      >
                        <span>{asp.icon}</span>
                        <span>{asp.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Personal Guest Note */}
              <div className="input-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label>Dishes, drinks, or details you'd like to highlight</label>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Anti-Hallucination active
                  </span>
                </div>
                <textarea
                  rows="3"
                  placeholder={
                    diningType === 'coffee_break'
                      ? "E.g., The oat flat white was silky and the baristas were very welcoming!"
                      : "E.g., Loved the truffle pasta and the tiramisu was incredible!"
                  }
                  value={userNote}
                  onChange={(e) => setUserNote(e.target.value)}
                />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                  🔒 <em>We will never invent dishes, drinks, or facts you didn't mention.</em>
                </div>
              </div>

              {/* Persona / Tone Selector */}
              <div className="grid-2" style={{ gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="input-group" style={{ marginBottom: 0 }}>
                  <label>Review Style</label>
                  <select value={tone} onChange={(e) => setTone(e.target.value)}>
                    {TONE_PERSONAS.map(p => (
                      <option key={p.id} value={p.id}>{p.label}</option>
                    ))}
                  </select>
                </div>

                <div className="input-group" style={{ marginBottom: 0 }}>
                  <label>Target Length</label>
                  <select value={length} onChange={(e) => setLength(e.target.value)}>
                    <option value="short">Short (1-2 sentences)</option>
                    <option value="medium">Medium (2-3 sentences)</option>
                    <option value="detailed">Detailed (3-4 sentences)</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={isGenerating}
                style={{ width: '100%' }}
              >
                {isGenerating ? (
                  <>
                    <span className="spinner-inline"></span>
                    Polishing Draft with Hospitality NLP...
                  </>
                ) : (
                  '✨ Generate Verified Review Draft'
                )}
              </button>
            </form>
          )}
        </div>

        {/* STEP 2: Real-time AI Suggested Review & Verification */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="section-badge" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8' }}>
            Step 2 • Review Studio
          </div>
          <h3 style={{ fontSize: '1.4rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            AI Suggested Review Draft
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            You have full editorial control. Edit anything in the box below before posting to Google.
          </p>

          {!draftReview && !isGenerating ? (
            <div className="result-card" style={{ opacity: 0.6, flex: 1 }}>
              <div className="status-icon">☕</div>
              <h3>Draft Preview Awaiting Details</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '340px' }}>
                Select your dining highlights on the left and click <strong>Generate Verified Review Draft</strong>.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '1rem' }}>
              <div className="review-editor-container">
                <textarea
                  className="review-textarea"
                  rows="6"
                  value={draftReview}
                  onChange={(e) => setDraftReview(e.target.value)}
                  onBlur={handleValidateDraft}
                  placeholder="Your review draft..."
                />
                <button
                  type="button"
                  className="copy-chip-btn"
                  onClick={handleCopyReview}
                  title="Copy text to clipboard"
                >
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>

              {/* Real-Time Sentiment & Consistency Tag */}
              <div className="validation-bar">
                <div className="val-item">
                  <span className="val-label">Analyzed Sentiment</span>
                  <span className={`val-tag ${sentiment?.toLowerCase() || 'neutral'}`}>
                    {sentiment || 'Evaluating'} {confidence ? `(${Math.round(confidence * 100)}%)` : ''}
                  </span>
                </div>

                <div className="val-item">
                  <span className="val-label">Rating Consistency</span>
                  <span className={`val-tag ${ratingConsistent ? 'match' : 'mismatch'}`}>
                    {ratingConsistent ? '✓ Consistent with Stars' : '⚠️ Potential Mismatch'}
                  </span>
                </div>

                {provider && (
                  <div className="val-item" style={{ marginLeft: 'auto' }}>
                    <span className="val-label">Engine</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {provider.replace('-', ' ')}
                    </span>
                  </div>
                )}
              </div>

              {warnings.length > 0 && (
                <div className="warning-box">
                  {warnings.map((w, idx) => (
                    <div key={idx}>⚠️ {w}</div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="review-action-row" style={{ marginTop: 'auto', paddingTop: '1rem' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                >
                  🔄 Regenerate
                </button>

                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleValidateDraft}
                  disabled={isValidating || !draftReview.trim()}
                >
                  {isValidating ? 'Validating...' : '🔍 Re-Check Sentiment'}
                </button>

                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => setShowConsentModal(true)}
                  disabled={!draftReview.trim()}
                  style={{ flex: 1.2 }}
                >
                  🚀 Continue to Google Maps →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Customer Approval Modal */}
      {showConsentModal && (
        <div className="modal-backdrop">
          <div className="glass-panel modal-card">
            <div className="modal-header">
              <span className="modal-icon">🌟</span>
              <div>
                <h3 style={{ margin: 0 }}>Review Ready for Google Maps</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{businessName}</span>
              </div>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: '1rem 0' }}>
              Please confirm that this review genuinely reflects your experience at {businessName}:
            </p>

            <div className="modal-review-preview">
              "{draftReview}"
            </div>

            {!isUrlConfigured && (
              <div className="config-notice" style={{ margin: '0.75rem 0' }}>
                ℹ️ Official Google link is being set up by management. Clicking continue will open Google Maps for {businessName}.
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowConsentModal(false)}
              >
                ✏️ Edit Further
              </button>

              <button
                type="button"
                className="btn-primary"
                onClick={handleOpenGoogle}
              >
                📋 Copy Text & Open Google Review Link ↗
              </button>
            </div>

            <div style={{ textAlign: 'center', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              ChurnLens ensures ethical submission: you perform the final review submission on Google.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
