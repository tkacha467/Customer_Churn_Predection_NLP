import { useState, useEffect } from 'react';

export default function CustomerReview({
  businessId = 'default_business',
  onSwitchToOwner = null,
  isPreview = false
}) {
  // Query parameters: e.g. ?table=Table+4&dining=dine_in&preview=true
  const urlParams = new URLSearchParams(window.location.search);
  const tableParam = urlParams.get('table') || 'Table 4';
  const isPreviewMode = isPreview || urlParams.get('preview') === 'true';

  // Step state: 1 (rating) -> 2 (topics) -> 3 (ideas) -> 4 (editor)
  const [currentStep, setCurrentStep] = useState(1);

  // Business config state
  const [restaurantName, setRestaurantName] = useState('Nasta Ghar');
  const [branchName, setBranchName] = useState('');
  const [category, setCategory] = useState('Breakfast & Snacks');
  const [googleReviewUrl, setGoogleReviewUrl] = useState('https://maps.google.com');
  const [isUrlConfigured, setIsUrlConfigured] = useState(false);
  const [availableTopics, setAvailableTopics] = useState([
    'Breakfast', 'Chai & Beverages', 'Snacks', 'Taste & Flavour', 'Friendly Staff', 'Cleanliness', 'Value for Money', 'Quick Service'
  ]);

  // Customer choices
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [selectedTopics, setSelectedTopics] = useState(['Breakfast', 'Chai & Beverages']);
  const [nothingSpecific, setNothingSpecific] = useState(false);
  const [personalNote, setPersonalNote] = useState('');

  // Ideas state
  const [ideas, setIdeas] = useState([]);
  const [isLoadingIdeas, setIsLoadingIdeas] = useState(false);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);

  // Editor state
  const [draftReview, setDraftReview] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Session & Telemetry
  const [sessionId, setSessionId] = useState('');
  const [isHandoffOpen, setIsHandoffOpen] = useState(false);
  const [copiedSuccess, setCopiedSuccess] = useState(false);

  // Optional Private Feedback
  const [showPrivateModal, setShowPrivateModal] = useState(false);
  const [privateNote, setPrivateNote] = useState('');
  const [privateContact, setPrivateContact] = useState('');
  const [privateSent, setPrivateSent] = useState(false);

  // Fetch restaurant details
  useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/businesses/${businessId}/review-link`)
      .then(res => res.json())
      .then(data => {
        if (data.business_name) setRestaurantName(data.business_name);
        if (data.branch) setBranchName(data.branch);
        if (data.category) setCategory(data.category);
        if (data.review_url) setGoogleReviewUrl(data.review_url);
        setIsUrlConfigured(Boolean(data.is_configured));
        if (data.topics && data.topics.length > 0) {
          setAvailableTopics(data.topics);
          // Preselect first two by default
          setSelectedTopics(data.topics.slice(0, 2));
        }
      })
      .catch(err => console.error('Failed to load restaurant config:', err));

    // Initialize session
    fetch('http://127.0.0.1:8000/api/reviews/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        business_id: businessId,
        table_number: tableParam,
        dining_type: 'dine_in'
      })
    })
      .then(res => res.json())
      .then(data => setSessionId(data.session_id))
      .catch(err => console.error('Failed to initialize review session:', err));
  }, [businessId, tableParam]);

  // Log analytics event
  const logEvent = (eventName, metadata = {}) => {
    fetch('http://127.0.0.1:8000/api/reviews/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        event_name: eventName,
        metadata: {
          business_id: businessId,
          table: tableParam,
          rating,
          ...metadata
        }
      })
    }).catch(err => console.error('Failed logging event:', err));
  };

  // Step 1: Select Rating
  const handleRatingSelect = (stars) => {
    setRating(stars);
    logEvent('rating_selected', { rating: stars });
  };

  const getRatingDescriptor = (stars) => {
    switch (stars) {
      case 5: return 'Loved it! ⭐';
      case 4: return 'Really good 😊';
      case 3: return 'It was okay 🙂';
      case 2: return 'Disappointed 🙁';
      case 1: return 'Not good 😞';
      default: return '';
    }
  };

  // Step 2: Toggle Topics
  const toggleTopic = (topic) => {
    if (nothingSpecific) {
      setNothingSpecific(false);
    }
    if (selectedTopics.includes(topic)) {
      setSelectedTopics(selectedTopics.filter(t => t !== topic));
    } else {
      setSelectedTopics([...selectedTopics, topic]);
    }
  };

  const handleSelectNothingSpecific = () => {
    setNothingSpecific(true);
    setSelectedTopics([]);
  };

  // Move from Step 2 to Step 3: Fetch review ideas
  const handleProceedToIdeas = async () => {
    setIsLoadingIdeas(true);
    setCurrentStep(3);
    logEvent('aspects_selected', {
      aspects: nothingSpecific ? [] : selectedTopics,
      has_note: Boolean(personalNote.trim())
    });

    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: nothingSpecific ? [] : selectedTopics,
          user_note: personalNote.trim()
        })
      });
      const data = await res.json();
      if (data.ideas && data.ideas.length > 0) {
        setIdeas(data.ideas);
      }
    } catch (err) {
      console.error('Failed fetching review ideas:', err);
      // Fallback idea
      setIdeas([
        {
          id: 'idea_fallback',
          focus: 'Overall',
          text: rating >= 4
            ? `Really enjoyed my visit to ${restaurantName}! Great service and lovely food.`
            : `Visited ${restaurantName} today. Service took a while, but hoping for a smoother visit next time.`
        }
      ]);
    } finally {
      setIsLoadingIdeas(false);
    }
  };

  // Step 3: Pick an idea card
  const handleSelectIdea = (idea) => {
    setSelectedIdeaId(idea.id);
    setDraftReview(idea.text);
    logEvent('idea_selected', { idea_id: idea.id, focus: idea.focus });
    setCurrentStep(4);
  };

  const handleWriteMyOwn = () => {
    setSelectedIdeaId('custom');
    setDraftReview('');
    logEvent('write_my_own_selected');
    setCurrentStep(4);
  };

  // Step 4: Make it more natural / regenerate
  const handleMakeMoreNatural = async () => {
    setIsRegenerating(true);
    logEvent('make_more_natural_clicked');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: nothingSpecific ? [] : selectedTopics,
          user_note: personalNote.trim(),
          selected_idea: draftReview || undefined,
          emoji_preference: 'light'
        })
      });
      const data = await res.json();
      if (data.review) {
        setDraftReview(data.review);
      }
    } catch (err) {
      console.error('Regeneration failed:', err);
    } finally {
      setIsRegenerating(false);
    }
  };

  // Step 5: Google Handoff
  const handleContinueToGoogle = async () => {
    logEvent('review_approved', { length: draftReview.length });
    
    // Copy review to clipboard
    try {
      await navigator.clipboard.writeText(draftReview);
      setCopiedSuccess(true);
      logEvent('review_copied');
    } catch (err) {
      console.warn('Clipboard write fallback:', err);
      setCopiedSuccess(true);
    }

    logEvent('google_review_link_opened');

    // Open official Google link in new tab
    const targetUrl = googleReviewUrl || 'https://maps.google.com';
    window.open(targetUrl, '_blank', 'noopener,noreferrer');

    // Display confirmation modal
    setIsHandoffOpen(true);
  };

  // Submit optional private feedback
  const handleSendPrivateFeedback = async (e) => {
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
          guest_contact: privateContact
        })
      });
      setPrivateSent(true);
      logEvent('private_feedback_sent');
    } catch (err) {
      console.error('Failed submitting private feedback:', err);
    }
  };

  return (
    <div className="customer-page-wrapper">
      {/* Optional Preview Bar for Restaurant Owner */}
      {isPreviewMode && (
        <div className="preview-top-banner">
          <span>👁️ Restaurant Owner Preview Mode</span>
          {onSwitchToOwner && (
            <button
              type="button"
              className="preview-exit-btn"
              onClick={onSwitchToOwner}
            >
              ← Back to Owner Dashboard
            </button>
          )}
        </div>
      )}

      <div className="customer-card">
        {/* Brand Header */}
        <header className="customer-header">
          <div className="customer-logo-badge ng-logo">🍳</div>
          <h1 className="customer-restaurant-name ng-name">{restaurantName}</h1>
          <div className="customer-restaurant-sub">
            <span>{category}</span>
            {branchName && <span> • {branchName}</span>}
            {tableParam && <span className="table-badge">📍 {tableParam}</span>}
          </div>
        </header>

        {/* STEP 1: WELCOME & RATING */}
        {currentStep === 1 && (
          <div className="customer-step-container step-fade-in">
            <h2 className="step-title">How was your visit? ☀️</h2>
            <p className="step-subtitle">Tap a star to rate your experience</p>

            <div className="star-rating-row" role="radiogroup" aria-label="Rating">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  className={`star-button ${((hoverRating || rating) >= star) ? 'active' : ''}`}
                  onClick={() => handleRatingSelect(star)}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  aria-label={`${star} star${star > 1 ? 's' : ''}`}
                >
                  ★
                </button>
              ))}
            </div>

            <div className="rating-feedback-badge">
              {getRatingDescriptor(rating)}
            </div>

            <div className="step-action-footer">
              <button
                type="button"
                className="btn-customer-primary"
                onClick={() => setCurrentStep(2)}
              >
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: WHAT STOOD OUT */}
        {currentStep === 2 && (
          <div className="customer-step-container step-fade-in">
            <h2 className="step-title">What stood out? 🌟</h2>
            <p className="step-subtitle">Pick anything that matched your visit</p>

            <div className="topics-chip-grid">
              {availableTopics.map((topic) => {
                const isSelected = selectedTopics.includes(topic);
                return (
                  <button
                    key={topic}
                    type="button"
                    className={`topic-chip ${isSelected ? 'selected' : ''}`}
                    onClick={() => toggleTopic(topic)}
                  >
                    <span className="chip-indicator">{isSelected ? '✓' : '+'}</span>
                    <span>{topic}</span>
                  </button>
                );
              })}

              <button
                type="button"
                className={`topic-chip topic-chip-neutral ${nothingSpecific ? 'selected' : ''}`}
                onClick={handleSelectNothingSpecific}
              >
                <span className="chip-indicator">{nothingSpecific ? '✓' : '—'}</span>
                <span>Nothing specific</span>
              </button>
            </div>

            <div className="personal-note-section">
              <label htmlFor="user-note-input" className="note-label">
                Add a personal note <span className="text-optional">(optional)</span>
              </label>
              <input
                id="user-note-input"
                type="text"
                className="note-input"
                placeholder="e.g. The poha was absolutely perfect! 😋"
                value={personalNote}
                onChange={(e) => setPersonalNote(e.target.value)}
                maxLength={100}
              />
            </div>

            <div className="step-action-row">
              <button
                type="button"
                className="btn-customer-secondary"
                onClick={() => setCurrentStep(1)}
              >
                ← Back
              </button>
              <button
                type="button"
                className="btn-customer-primary"
                onClick={handleProceedToIdeas}
              >
                See Review Ideas →
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: REVIEW IDEA CARDS (MAJOR FEATURE) */}
        {currentStep === 3 && (
          <div className="customer-step-container step-fade-in">
            <h2 className="step-title">Your review ideas ✨</h2>
            <p className="step-subtitle">Pick the one that feels right — you can edit it before posting!</p>

            {isLoadingIdeas ? (
              <div className="loading-ideas-box">
                <div className="loading-spinner">🍳</div>
                <p className="loading-text">Crafting honest review ideas for you...</p>
              </div>
            ) : (
              <div className="ideas-card-list">
                {ideas.map((idea, idx) => (
                  <div key={idea.id || idx} className={`review-idea-card ${selectedIdeaId === idea.id ? 'active' : ''}`}>
                    <div className="idea-card-header">
                      <span className="idea-badge">⭐ Option {idx + 1}</span>
                      <span className="idea-focus-tag">{idea.focus}</span>
                    </div>
                    <p className="idea-card-text">“{idea.text}”</p>
                    <button
                      type="button"
                      className="btn-pick-idea"
                      onClick={() => handleSelectIdea(idea)}
                    >
                      Use this idea →
                    </button>
                  </div>
                ))}

                <div className="write-own-divider">
                  <span>or</span>
                </div>

                <button
                  type="button"
                  className="btn-write-own"
                  onClick={handleWriteMyOwn}
                >
                  ✍️ Write my own review
                </button>
              </div>
            )}

            <div className="step-action-row" style={{ marginTop: '1rem' }}>
              <button
                type="button"
                className="btn-customer-secondary"
                onClick={() => setCurrentStep(2)}
              >
                ← Change Highlights
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: CUSTOMER EDITOR */}
        {currentStep === 4 && (
          <div className="customer-step-container step-fade-in">
            <div className="editor-header-row">
              <h2 className="step-title" style={{ margin: 0 }}>Your review</h2>
              <span className="char-count-pill">{draftReview.length} chars</span>
            </div>
            <p className="step-subtitle">Feel free to personalize or edit anything before continuing</p>

            <div className="customer-editor-box">
              <textarea
                className="customer-textarea"
                rows="5"
                value={draftReview}
                onChange={(e) => setDraftReview(e.target.value)}
                placeholder="Type your review here..."
              />
            </div>

            <div className="editor-action-row">
              <button
                type="button"
                className="btn-editor-tool"
                onClick={handleMakeMoreNatural}
                disabled={isRegenerating || !draftReview.trim()}
              >
                {isRegenerating ? '✨ Refining...' : '✨ Make it more natural'}
              </button>

              <button
                type="button"
                className="btn-editor-tool"
                onClick={() => setCurrentStep(3)}
              >
                🔄 Try another idea
              </button>
            </div>

            {/* Notice explaining Google direct authorship */}
            <div className="google-author-notice">
              <span>✅ You post directly on Google — your words, your review.</span>
            </div>

            {/* Primary Action Button */}
            <div className="step-action-footer">
              <button
                type="button"
                className="btn-customer-primary btn-cta-large"
                onClick={handleContinueToGoogle}
                disabled={!draftReview.trim()}
              >
                📋 Copy & Open Google Maps
              </button>
            </div>

            {/* Optional Private Feedback Prompt */}
            <div className="private-feedback-prompt">
              <span>Want to tell the restaurant privately too? </span>
              <button
                type="button"
                className="link-btn"
                onClick={() => setShowPrivateModal(true)}
              >
                Share private feedback
              </button>
            </div>
          </div>
        )}
      </div>

      {/* STEP 5: GOOGLE HANDOFF CONFIRMATION MODAL */}
      {isHandoffOpen && (
        <div className="customer-modal-backdrop">
          <div className="customer-modal-card modal-bounce-in">
            <div className="modal-icon-circle">🎉</div>
            <h3 className="modal-title">
              {copiedSuccess ? 'Your review has been copied!' : 'Ready for Google!'}
            </h3>
            <p className="modal-body-text">
              Google Maps is opening in a new tab for <strong>{restaurantName}</strong>.
              {!isUrlConfigured && (
                <span style={{ display: 'block', fontSize: '0.8rem', color: '#f59e0b', marginTop: '0.25rem' }}>
                  (Default Google search link active)
                </span>
              )}
            </p>

            <div className="modal-instruction-box">
              <div className="inst-step">
                <span className="inst-num">1</span>
                <span>Select your <strong>{rating} stars</strong> on Google</span>
              </div>
              <div className="inst-step">
                <span className="inst-num">2</span>
                <span><strong>Paste</strong> your review text</span>
              </div>
              <div className="inst-step">
                <span className="inst-num">3</span>
                <span>Click <strong>Post</strong> on Google!</span>
              </div>
            </div>

            <div className="copied-text-preview">
              "{draftReview}"
            </div>

            <div className="modal-button-stack">
              <button
                type="button"
                className="btn-customer-primary"
                onClick={() => {
                  window.open(googleReviewUrl || 'https://maps.google.com', '_blank', 'noopener,noreferrer');
                }}
              >
                ↗ Re-open Google Maps
              </button>

              <button
                type="button"
                className="btn-customer-secondary"
                onClick={() => setIsHandoffOpen(false)}
              >
                Done ✓
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OPTIONAL PRIVATE FEEDBACK MODAL */}
      {showPrivateModal && (
        <div className="customer-modal-backdrop">
          <div className="customer-modal-card modal-bounce-in">
            <h3 className="modal-title">Direct Note to Management</h3>
            <p className="modal-body-text">
              Share anything you'd like the team at {restaurantName} to know directly.
            </p>

            {privateSent ? (
              <div className="private-success-box">
                <span style={{ fontSize: '2rem' }}>💌</span>
                <h4>Thank you!</h4>
                <p>Your message has been sent directly to the restaurant management.</p>
                <button
                  type="button"
                  className="btn-customer-primary"
                  onClick={() => setShowPrivateModal(false)}
                  style={{ marginTop: '1rem' }}
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleSendPrivateFeedback} className="private-form">
                <textarea
                  className="customer-textarea"
                  rows="4"
                  placeholder="Share private thoughts, suggestions, or experiences..."
                  value={privateNote}
                  onChange={(e) => setPrivateNote(e.target.value)}
                  required
                />
                <input
                  type="text"
                  className="note-input"
                  placeholder="Optional contact info (email or phone) for reply"
                  value={privateContact}
                  onChange={(e) => setPrivateContact(e.target.value)}
                  style={{ marginTop: '0.75rem' }}
                />

                <div className="modal-button-stack" style={{ marginTop: '1.25rem' }}>
                  <button type="submit" className="btn-customer-primary">
                    Send to Restaurant
                  </button>
                  <button
                    type="button"
                    className="btn-customer-secondary"
                    onClick={() => setShowPrivateModal(false)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
