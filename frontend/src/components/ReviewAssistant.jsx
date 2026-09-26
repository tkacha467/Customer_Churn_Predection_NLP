import { useState, useEffect } from 'react';

const ASPECT_OPTIONS = [
  { id: 'Food', label: 'Food', icon: '🍽️' },
  { id: 'Taste', label: 'Taste', icon: '😋' },
  { id: 'Quality', label: 'Quality', icon: '⭐' },
  { id: 'Ambiance', label: 'Ambiance', icon: '🕯️' },
  { id: 'Service', label: 'Service', icon: '🛎️' },
  { id: 'Staff', label: 'Staff', icon: '👥' },
  { id: 'Cleanliness', label: 'Cleanliness', icon: '✨' },
  { id: 'Waiting Time', label: 'Waiting Time', icon: '⏳' },
  { id: 'Value for Money', label: 'Value for Money', icon: '💰' },
  { id: 'Location', label: 'Location', icon: '📍' },
  { id: 'Overall Experience', label: 'Overall Experience', icon: '🌟' },
];

const TONE_OPTIONS = [
  { id: 'natural', label: 'Natural & Authentic' },
  { id: 'casual', label: 'Casual & Friendly' },
  { id: 'professional', label: 'Professional & Courteous' },
  { id: 'short', label: 'Short & Concise' },
  { id: 'detailed', label: 'Detailed & Thorough' },
];

export default function ReviewAssistant({ businessId = 'default_business' }) {
  const [rating, setRating] = useState(5);
  const [selectedAspects, setSelectedAspects] = useState(['Food', 'Service']);
  const [userNote, setUserNote] = useState('');
  const [tone, setTone] = useState('natural');
  const [length, setLength] = useState('medium');

  // Generation & Review State
  const [draftReview, setDraftReview] = useState('');
  const [sentiment, setSentiment] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [ratingConsistent, setRatingConsistent] = useState(true);
  const [warnings, setWarnings] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [provider, setProvider] = useState('');
  
  // Consent & Google Link State
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [googleReviewUrl, setGoogleReviewUrl] = useState('');
  const [isUrlConfigured, setIsUrlConfigured] = useState(false);
  const [businessName, setBusinessName] = useState('Business');
  const [copied, setCopied] = useState(false);
  const [sessionId, setSessionId] = useState('');

  // Fetch configured Google review link on mount
  useEffect(() => {
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
      body: JSON.stringify({ business_id: businessId })
    })
      .then(res => res.json())
      .then(data => setSessionId(data.session_id))
      .catch(err => console.error('Error initializing review session:', err));
  }, [businessId]);

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
          session_id: sessionId
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to generate review draft.');
      }

      const data = await response.json();
      setDraftReview(data.review);
      setSentiment(data.sentiment);
      setConfidence(data.sentiment_confidence);
      setRatingConsistent(data.rating_consistent);
      setWarnings(data.warnings || []);
      setProvider(data.generation_provider);
    } catch (error) {
      console.error('Review generation failed:', error);
      alert(error.message || 'Generation failed. Please ensure the backend is running.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Re-validate review if customer manually edited the text
  const handleValidateDraft = async () => {
    if (!draftReview.trim()) return;
    setIsValidating(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/reviews/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating,
          review: draftReview
        })
      });

      const data = await response.json();
      setSentiment(data.sentiment);
      setConfidence(data.confidence);
      setRatingConsistent(data.rating_consistent);
      setWarnings(data.warnings || []);

      // Log manual edit event
      fetch('http://127.0.0.1:8000/api/reviews/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          event_name: 'review_edited',
          metadata: { rating, consistent: data.rating_consistent }
        })
      }).catch(() => {});
    } catch (err) {
      console.error('Validation error:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const handleCopyReview = () => {
    if (!draftReview) return;
    navigator.clipboard.writeText(draftReview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleOpenGoogle = () => {
    // Record analytics event
    fetch('http://127.0.0.1:8000/api/reviews/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        event_name: 'google_review_link_clicked',
        metadata: { rating, sentiment, is_configured: isUrlConfigured }
      })
    }).catch(() => {});

    // Always copy to clipboard for convenience
    navigator.clipboard.writeText(draftReview);

    // Open official Google link in a new tab
    if (googleReviewUrl) {
      window.open(googleReviewUrl, '_blank', 'noopener,noreferrer');
    }
    setShowConsentModal(false);
  };

  const ratingDescriptions = {
    5: 'Exceptional (5 Stars)',
    4: 'Very Good (4 Stars)',
    3: 'Average / Neutral (3 Stars)',
    2: 'Needs Improvement (2 Stars)',
    1: 'Disappointing (1 Star)'
  };

  return (
    <div className="review-assistant-wrapper">
      <div className="grid-2">
        {/* STEP 1: Interactive Customer Feedback Form */}
        <div className="glass-panel">
          <div className="section-badge">Customer Journey</div>
          <h2 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '1.6rem' }}>
            How was your experience?
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Share your authentic feedback. Our AI assistant will help turn your thoughts into a polished review draft.
          </p>

          <form onSubmit={handleGenerate}>
            {/* Rating Selector */}
            <div className="input-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label>Overall Rating</label>
                <span style={{ fontSize: '0.85rem', color: '#fbbf24', fontWeight: '600' }}>
                  {ratingDescriptions[rating]}
                </span>
              </div>
              <div className="star-rating" style={{ marginTop: '0.25rem' }}>
                {[1, 2, 3, 4, 5].map(star => (
                  <button
                    type="button"
                    key={star}
                    className={`star-btn ${rating >= star ? 'active' : ''}`}
                    onClick={() => setRating(star)}
                    title={`${star} Star${star > 1 ? 's' : ''}`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            {/* Experience Aspects Multi-Select */}
            <div className="input-group">
              <label>What specific aspects stood out? (Optional)</label>
              <div className="aspect-chips">
                {ASPECT_OPTIONS.map(asp => {
                  const isSelected = selectedAspects.includes(asp.id);
                  return (
                    <button
                      type="button"
                      key={asp.id}
                      className={`aspect-chip ${isSelected ? 'selected' : ''}`}
                      onClick={() => toggleAspect(asp.id)}
                    >
                      <span className="chip-icon">{asp.icon}</span>
                      <span>{asp.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Customer Personal Note */}
            <div className="input-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label>Tell us more in your own words (Optional)</label>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Strict anti-hallucination active
                </span>
              </div>
              <textarea
                rows="3"
                placeholder="E.g., Really liked the pasta and the staff was very friendly."
                value={userNote}
                onChange={(e) => setUserNote(e.target.value)}
              />
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                ℹ️ The AI will never invent unmentioned dishes, staff names, or events.
              </div>
            </div>

            {/* Tone & Style Options */}
            <div className="grid-2" style={{ gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="input-group" style={{ marginBottom: 0 }}>
                <label>Review Style</label>
                <select value={tone} onChange={(e) => setTone(e.target.value)}>
                  {TONE_OPTIONS.map(t => (
                    <option key={t.id} value={t.id}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div className="input-group" style={{ marginBottom: 0 }}>
                <label>Length</label>
                <select value={length} onChange={(e) => setLength(e.target.value)}>
                  <option value="short">Short (1-2 sentences)</option>
                  <option value="medium">Medium (2-3 sentences)</option>
                  <option value="detailed">Detailed (3-4 sentences)</option>
                </select>
              </div>
            </div>

            {/* Generate Action */}
            <button
              type="submit"
              className="btn-primary"
              disabled={isGenerating}
              style={{ width: '100%' }}
            >
              {isGenerating ? (
                <>
                  <span className="spinner-inline"></span>
                  Crafting & Validating Review...
                </>
              ) : (
                '✨ Generate Review Draft'
              )}
            </button>
          </form>
        </div>

        {/* STEP 2: AI Suggested Review Draft & Live Validation */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="section-badge" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8' }}>
            Review Workspace
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem', fontSize: '1.6rem' }}>
            AI Suggested Review
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Edit anything directly. Our built-in NLP engine validates sentiment consistency in real-time.
          </p>

          {!draftReview && !isGenerating ? (
            <div className="result-card" style={{ opacity: 0.6, flex: 1 }}>
              <div className="status-icon">✍️</div>
              <h3>Your Draft Will Appear Here</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '340px' }}>
                Select your star rating and experience aspects on the left, then click <strong>Generate Review Draft</strong>.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '1rem' }}>
              {/* Editable Review Textarea */}
              <div className="review-editor-container">
                <textarea
                  className="review-textarea"
                  rows="6"
                  value={draftReview}
                  onChange={(e) => setDraftReview(e.target.value)}
                  onBlur={handleValidateDraft}
                  placeholder="Your generated review text..."
                />
                <button
                  type="button"
                  className="copy-chip-btn"
                  onClick={handleCopyReview}
                  title="Copy review to clipboard"
                >
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>

              {/* Real-time NLP Validation Indicators */}
              <div className="validation-bar">
                <div className="val-item">
                  <span className="val-label">Sentiment</span>
                  <span className={`val-tag ${sentiment?.toLowerCase() || 'neutral'}`}>
                    {sentiment || 'Evaluating'} {confidence ? `(${Math.round(confidence * 100)}%)` : ''}
                  </span>
                </div>

                <div className="val-item">
                  <span className="val-label">Rating Consistency</span>
                  <span className={`val-tag ${ratingConsistent ? 'match' : 'mismatch'}`}>
                    {ratingConsistent ? '✓ Consistent' : '⚠️ Potential Mismatch'}
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

              {/* Warnings / Guidance */}
              {warnings.length > 0 && (
                <div className="warning-box">
                  {warnings.map((w, idx) => (
                    <div key={idx}>⚠️ {w}</div>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
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
                  🚀 Continue to Google →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* STEP 3: Customer Approval & Consent Modal */}
      {showConsentModal && (
        <div className="modal-backdrop">
          <div className="glass-panel modal-card">
            <div className="modal-header">
              <span className="modal-icon">🌟</span>
              <h3>Your Review is Ready</h3>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: '1rem 0' }}>
              Please review the draft below and ensure it accurately reflects your honest experience with <strong>{businessName}</strong> before submitting it.
            </p>

            <div className="modal-review-preview">
              "{draftReview}"
            </div>

            {!isUrlConfigured && (
              <div className="config-notice">
                ℹ️ The business has not set an official Google Business review link yet. Clicking Continue will open Google Maps where you can search and submit.
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowConsentModal(false)}
              >
                ✏️ Edit Review
              </button>

              <button
                type="button"
                className="btn-primary"
                onClick={handleOpenGoogle}
              >
                📋 Copy & Open Google Review Link ↗
              </button>
            </div>
            
            <div style={{ textAlign: 'center', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              ChurnLens does not submit reviews directly. You will perform the final submission on Google.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
