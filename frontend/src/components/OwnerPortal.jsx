import { useState, useEffect } from 'react';
import QRCode from 'qrcode';
import NastaGharRestaurantScene from './NastaGharRestaurantScene';
import { apiFetch } from '../lib/api';

export default function OwnerPortal({
  businessId = 'default_business',
  onPreviewCustomer = null
}) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [ownerPassword, setOwnerPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [isSigningIn, setIsSigningIn] = useState(false);
  // Navigation tabs: 'home' | 'setup' | 'qr' | 'activity' | 'settings'
  const [activeTab, setActiveTab] = useState('home');

  // Business config state
  const [businessName, setBusinessName] = useState('Nasta Ghar');
  const [branch, setBranch] = useState('');
  const [category, setCategory] = useState('Breakfast & Snacks');
  const [description, setDescription] = useState('Authentic homestyle breakfast, chai, and snacks in Rajkot.');
  const [googleReviewUrl, setGoogleReviewUrl] = useState('');
  const [isUrlConfigured, setIsUrlConfigured] = useState(false);
  const [topics, setTopics] = useState([
    'Breakfast', 'Chai & Beverages', 'Snacks', 'Taste & Flavour', 'Friendly Staff', 'Cleanliness', 'Value for Money', 'Quick Service'
  ]);
  const [newTopicInput, setNewTopicInput] = useState('');
  const [primaryAccent, setPrimaryAccent] = useState('#f97316');

  // Setup / Save status
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  // Analytics state
  const [analytics, setAnalytics] = useState({
    total_generations: 0,
    google_clicks: 0,
    reviews_copied: 0,
    top_topics: [],
    recent_activity: []
  });
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  // QR Studio state
  const [qrLocationType, setQrLocationType] = useState('table'); // 'table' | 'counter' | 'receipt' | 'general'
  const [qrTableNumber, setQrTableNumber] = useState('4');
  const [qrBaseUrl, setQrBaseUrl] = useState(window.location.origin);
  const [generatedQrDataUrl, setGeneratedQrDataUrl] = useState('');

  useEffect(() => {
    let active = true;
    apiFetch('/api/auth/session')
      .then((res) => { if (active) setIsAuthenticated(res.ok); })
      .catch(() => { if (active) setIsAuthenticated(false); })
      .finally(() => { if (active) setIsCheckingSession(false); });
    return () => { active = false; };
  }, []);

  const handleOwnerLogin = async (event) => {
    event.preventDefault();
    setAuthError('');
    setIsSigningIn(true);
    try {
      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: ownerPassword }),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Sign-in failed. Please try again.');
      }
      setOwnerPassword('');
      setIsAuthenticated(true);
    } catch (error) {
      setAuthError(error.message || 'Could not sign in. Check the API connection and try again.');
    } finally {
      setIsSigningIn(false);
    }
  };

  const handleOwnerLogout = async () => {
    try { await apiFetch('/api/auth/logout', { method: 'POST' }); }
    finally { setIsAuthenticated(false); }
  };

  // Fetch business config
  const fetchConfig = async () => {
    try {
      const res = await apiFetch(`/api/businesses/${businessId}/review-link`);
      if (res.status === 401) setIsAuthenticated(false);
      if (!res.ok) throw new Error('Could not load restaurant configuration');
      const data = await res.json();
      if (data.business_name) setBusinessName(data.business_name);
      if (data.branch) setBranch(data.branch);
      if (data.category) setCategory(data.category);
      if (data.description) setDescription(data.description);
      if (data.review_url) setGoogleReviewUrl(data.review_url);
      setIsUrlConfigured(Boolean(data.is_configured));
      if (data.topics && data.topics.length > 0) setTopics(data.topics);
      if (data.primary_accent) setPrimaryAccent(data.primary_accent);
    } catch (err) {
      console.error('Failed fetching business config:', err);
    }
  };

  // Fetch real analytics
  const fetchAnalytics = async () => {
    setIsLoadingAnalytics(true);
    try {
      const res = await apiFetch('/api/reviews/analytics');
      if (res.status === 401) setIsAuthenticated(false);
      if (!res.ok) throw new Error('Could not load restaurant activity');
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed fetching analytics:', err);
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchConfig();
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, isAuthenticated]);

  // Generate QR Code dynamically
  useEffect(() => {
    let locationLabel = '';
    if (qrLocationType === 'table') locationLabel = `Table ${qrTableNumber}`;
    else if (qrLocationType === 'counter') locationLabel = 'Counter';
    else if (qrLocationType === 'receipt') locationLabel = 'Receipt';
    else locationLabel = 'General';

    const targetUrl = `${qrBaseUrl}/review?table=${encodeURIComponent(locationLabel)}`;
    QRCode.toDataURL(targetUrl, {
      width: 320,
      margin: 2,
      color: {
        dark: '#0f172a',
        light: '#ffffff'
      }
    })
      .then(url => setGeneratedQrDataUrl(url))
      .catch(err => console.error('Failed generating QR code:', err));
  }, [qrLocationType, qrTableNumber, qrBaseUrl]);

  // Save configuration
  const handleSaveConfig = async (e) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    setSaveSuccessMsg('');

    try {
      const res = await apiFetch(`/api/businesses/${businessId}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_name: businessName,
          branch,
          category,
          description,
          google_review_url: googleReviewUrl,
          topics,
          primary_accent: primaryAccent
        })
      });
      if (res.status === 401) setIsAuthenticated(false);
      if (!res.ok) throw new Error('Could not save configuration');
      const data = await res.json();
      setIsUrlConfigured(Boolean(data.is_configured));
      setSaveSuccessMsg('✓ Restaurant setup saved successfully!');
      setTimeout(() => setSaveSuccessMsg(''), 4000);
    } catch (err) {
      console.error('Error saving config:', err);
      alert('Could not save configuration. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Add custom review topic
  const handleAddTopic = () => {
    const trimmed = newTopicInput.trim();
    if (trimmed && !topics.includes(trimmed)) {
      setTopics([...topics, trimmed]);
      setNewTopicInput('');
    }
  };

  // Remove topic
  const handleRemoveTopic = (t) => {
    setTopics(topics.filter(item => item !== t));
  };

  // Download QR Code image
  const handleDownloadQr = (label = 'Review-QR') => {
    if (!generatedQrDataUrl) return;
    const a = document.createElement('a');
    a.href = generatedQrDataUrl;
    a.download = `${businessName.replace(/\s+/g, '_')}_${label}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (isCheckingSession) {
    return <section className="owner-login-panel" role="status">Checking owner session…</section>;
  }

  if (!isAuthenticated) {
    return (
      <section className="owner-login-panel">
        <form className="owner-login-card" onSubmit={handleOwnerLogin}>
          <h1>Owner sign-in</h1>
          <p>Sign in to manage the review link and view restaurant activity.</p>
          <label htmlFor="owner-password">Owner password</label>
          <input
            id="owner-password"
            type="password"
            autoComplete="current-password"
            value={ownerPassword}
            onChange={(event) => setOwnerPassword(event.target.value)}
            required
          />
          {authError && <p className="warning-box" role="alert">{authError}</p>}
          <button type="submit" disabled={isSigningIn}>
            {isSigningIn ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </section>
    );
  }

  return (
    <div className="owner-portal-wrapper">
      {/* Top Owner Header */}
      <header className="owner-top-bar">
        <div className="owner-brand-info">
          <div className="owner-logo-circle">☕</div>
          <div>
            <h1 className="owner-brand-title">
              {businessName} <span className="branch-tag">{branch}</span>
            </h1>
            <p className="owner-brand-sub">Restaurant Owner Portal</p>
          </div>
        </div>

        <div className="owner-top-actions">
          <button
            type="button"
            className="btn-preview-customer"
            onClick={onPreviewCustomer}
            title="Experience the review flow as a guest"
          >
            👁️ Preview Customer Experience
          </button>
          <button type="button" className="btn-owner-secondary" onClick={handleOwnerLogout}>
            Sign out
          </button>
        </div>
      </header>

      {/* Owner Navigation Tabs */}
      <nav className="owner-tab-nav" aria-label="Owner Navigation">
        <button
          type="button"
          className={`owner-tab-btn ${activeTab === 'home' ? 'active' : ''}`}
          onClick={() => setActiveTab('home')}
        >
          <span>🏠</span>
          <span>Home</span>
        </button>

        <button
          type="button"
          className={`owner-tab-btn ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => setActiveTab('setup')}
        >
          <span>⚙️</span>
          <span>Review Setup</span>
        </button>

        <button
          type="button"
          className={`owner-tab-btn ${activeTab === 'qr' ? 'active' : ''}`}
          onClick={() => setActiveTab('qr')}
        >
          <span>📱</span>
          <span>QR Codes</span>
        </button>

        <button
          type="button"
          className={`owner-tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          <span>📈</span>
          <span>Review Activity</span>
        </button>

        <button
          type="button"
          className={`owner-tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <span>🔧</span>
          <span>Settings</span>
        </button>
      </nav>

      {/* TAB 1: HOME */}
      {activeTab === 'home' && (
        <div className="owner-view-container tab-fade-in">
          {/* Welcome Card */}
          <div className="owner-hero-card">
            <div className="hero-text-side">
              <span className="greeting-badge">Good afternoon 👋</span>
              <h2 className="hero-heading">Your review assistant is ready.</h2>
              <p className="hero-subtext">
                Guests scan your QR code at their table, select what they loved, choose a natural review idea, and post it to Google in seconds.
              </p>
            </div>

            <div className="hero-actions-row">
              <button
                type="button"
                className="btn-owner-primary"
                onClick={() => setActiveTab('qr')}
              >
                📱 View & Print QR Codes
              </button>
              <button
                type="button"
                className="btn-owner-secondary"
                onClick={onPreviewCustomer}
              >
                👁️ Test Customer Flow
              </button>
            </div>
          </div>

          {/* Animated Restaurant Scene Preview for Owner */}
          <div style={{ marginBottom: '1.5rem' }}>
            <NastaGharRestaurantScene compact={true} />
          </div>

          {/* Quick Status Cards */}
          <div className="owner-status-grid">
            <div className="status-card">
              <div className="status-card-icon">⭐</div>
              <div className="status-card-details">
                <span className="status-label">Google Review Link</span>
                <span className={`status-value ${isUrlConfigured ? 'status-green' : 'status-amber'}`}>
                  {isUrlConfigured ? '✓ Connected' : 'Setup Required'}
                </span>
              </div>
              <button
                type="button"
                className="card-quick-link"
                onClick={() => setActiveTab('setup')}
              >
                Configure →
              </button>
            </div>

            <div className="status-card">
              <div className="status-card-icon">🟢</div>
              <div className="status-card-details">
                <span className="status-label">QR System</span>
                <span className="status-value status-green">✓ Active</span>
              </div>
              <button
                type="button"
                className="card-quick-link"
                onClick={() => setActiveTab('qr')}
              >
                Manage QR →
              </button>
            </div>

            <div className="status-card">
              <div className="status-card-icon">🏷️</div>
              <div className="status-card-details">
                <span className="status-label">Review Topics</span>
                <span className="status-value status-green">{topics.length} Configured</span>
              </div>
              <button
                type="button"
                className="card-quick-link"
                onClick={() => setActiveTab('setup')}
              >
                Edit Topics →
              </button>
            </div>
          </div>

          {/* Monthly Activity Summary */}
          <div className="owner-section-box">
            <div className="section-box-header">
              <h3 className="section-box-title">Activity This Month</h3>
              <button
                type="button"
                className="btn-text-action"
                onClick={fetchAnalytics}
              >
                🔄 Refresh
              </button>
            </div>

            <div className="stats-metric-row">
              <div className="metric-pill">
                <span className="metric-number">{analytics.total_generations || 0}</span>
                <span className="metric-label">Review drafts created</span>
              </div>

              <div className="metric-pill">
                <span className="metric-number">{analytics.google_clicks || 0}</span>
                <span className="metric-label">Customers opened Google</span>
              </div>

              <div className="metric-pill">
                <span className="metric-number">{analytics.reviews_copied || 0}</span>
                <span className="metric-label">Reviews copied to clipboard</span>
              </div>
            </div>
          </div>

          {/* Quick Setup Checklist */}
          <div className="checklist-box">
            <h3 className="checklist-title">Restaurant Setup Status</h3>
            <div className="checklist-items">
              <div className="check-item">
                <span className="check-icon">✓</span>
                <span className="check-text">Restaurant details configured ({businessName})</span>
              </div>
              <div className="check-item">
                <span className={`check-icon ${isUrlConfigured ? 'icon-green' : 'icon-amber'}`}>
                  {isUrlConfigured ? '✓' : '○'}
                </span>
                <span className="check-text">
                  Official Google Review link {isUrlConfigured ? 'connected' : 'needs to be pasted in Setup'}
                </span>
              </div>
              <div className="check-item">
                <span className="check-icon">✓</span>
                <span className="check-text">Review topics ({topics.slice(0, 4).join(', ')}...)</span>
              </div>
              <div className="check-item">
                <span className="check-icon">✓</span>
                <span className="check-text">Table QR deep-links enabled for rapid scanning</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REVIEW SETUP */}
      {activeTab === 'setup' && (
        <div className="owner-view-container tab-fade-in">
          <div className="owner-section-box">
            <h2 className="setup-title">Restaurant & Review Setup</h2>
            <p className="setup-subtitle">
              Configure what customers see when they scan your QR code.
            </p>

            {saveSuccessMsg && (
              <div className="success-banner">{saveSuccessMsg}</div>
            )}

            <form onSubmit={handleSaveConfig} className="setup-form">
              {/* Step 1: Restaurant Info */}
              <div className="form-group-block">
                <h3 className="form-block-title">1. Restaurant Details</h3>
                <div className="input-grid-2">
                  <div className="input-field">
                    <label>Restaurant Name</label>
                    <input
                      type="text"
                      value={businessName}
                      onChange={(e) => setBusinessName(e.target.value)}
                      placeholder="e.g. Cuore Cafe"
                      required
                    />
                  </div>

                  <div className="input-field">
                    <label>Branch / Location Name</label>
                    <input
                      type="text"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      placeholder="e.g. Downtown"
                    />
                  </div>
                </div>

                <div className="input-grid-2" style={{ marginTop: '1rem' }}>
                  <div className="input-field">
                    <label>Restaurant Type / Category</label>
                    <input
                      type="text"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      placeholder="e.g. Cafe, Italian Bistro, Bakery"
                    />
                  </div>

                  <div className="input-field">
                    <label>Short Description</label>
                    <input
                      type="text"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g. Artisan cafe and specialty coffee"
                    />
                  </div>
                </div>
              </div>

              {/* Step 2: Google Review Link */}
              <div className="form-group-block">
                <h3 className="form-block-title">2. Google Review Link</h3>
                <p className="form-block-desc">
                  Paste the official link customers use to leave a review on Google.
                </p>

                <div className="link-input-row">
                  <input
                    type="url"
                    value={googleReviewUrl}
                    onChange={(e) => setGoogleReviewUrl(e.target.value)}
                    placeholder="https://g.page/r/.../review or https://maps.google.com"
                    required
                  />
                  <button
                    type="button"
                    className="btn-test-link"
                    onClick={() => {
                      if (googleReviewUrl) window.open(googleReviewUrl, '_blank', 'noopener,noreferrer');
                      else alert('Please enter a Google review URL first.');
                    }}
                  >
                    Test Link ↗
                  </button>
                </div>

                <div className="compliance-note">
                  ℹ️ Customers review your restaurant directly on Google. ChurnLens helps them prepare their review and copies it for them.
                </div>
              </div>

              {/* Step 3: Review Topics */}
              <div className="form-group-block">
                <h3 className="form-block-title">3. What can customers mention?</h3>
                <p className="form-block-desc">
                  Select and customize the highlights customers can choose from. The AI assistant will only mention what the customer selects.
                </p>

                <div className="topics-management-grid">
                  {topics.map((t) => (
                    <div key={t} className="managed-topic-pill">
                      <span>{t}</span>
                      <button
                        type="button"
                        className="btn-remove-topic"
                        onClick={() => handleRemoveTopic(t)}
                        title="Remove topic"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>

                <div className="add-topic-row">
                  <input
                    type="text"
                    placeholder="+ Add custom topic (e.g. Live music, Rooftop view)"
                    value={newTopicInput}
                    onChange={(e) => setNewTopicInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTopic();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn-add-topic"
                    onClick={handleAddTopic}
                  >
                    Add Topic
                  </button>
                </div>
              </div>

              <div className="form-save-footer">
                <button
                  type="submit"
                  className="btn-owner-primary"
                  disabled={isSaving}
                >
                  {isSaving ? 'Saving...' : 'Save & Update Setup ✓'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TAB 3: QR CODES */}
      {activeTab === 'qr' && (
        <div className="owner-view-container tab-fade-in">
          <div className="owner-section-box">
            <h2 className="setup-title">Your Review QR Codes</h2>
            <p className="setup-subtitle">
              Print and place these QR codes on tables, receipt holders, or counters.
            </p>

            <div className="qr-creator-layout">
              {/* QR Options */}
              <div className="qr-options-panel">
                <label className="field-label">Where will this QR be used?</label>
                <div className="qr-type-selector">
                  {[
                    { id: 'table', label: 'Table' },
                    { id: 'counter', label: 'Counter' },
                    { id: 'receipt', label: 'Receipt' },
                    { id: 'general', label: 'General' }
                  ].map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={`qr-type-btn ${qrLocationType === item.id ? 'active' : ''}`}
                      onClick={() => setQrLocationType(item.id)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>

                {qrLocationType === 'table' && (
                  <div className="input-field" style={{ marginTop: '1.25rem' }}>
                    <label>Table Number / Name</label>
                    <input
                      type="text"
                      value={qrTableNumber}
                      onChange={(e) => setQrTableNumber(e.target.value)}
                      placeholder="e.g. 4, Patio 2, Booth A"
                    />
                  </div>
                )}

                <div className="input-field" style={{ marginTop: '1.25rem' }}>
                  <label>Frontend Base URL</label>
                  <input
                    type="text"
                    value={qrBaseUrl}
                    onChange={(e) => setQrBaseUrl(e.target.value)}
                    placeholder="https://yourdomain.com"
                  />
                  <span className="field-hint">
                    QR links point to: {qrBaseUrl}/review?table={qrLocationType === 'table' ? `Table+${qrTableNumber}` : qrLocationType}
                  </span>
                </div>

                <div className="qr-action-buttons" style={{ marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="btn-owner-primary"
                    onClick={() => handleDownloadQr(qrLocationType === 'table' ? `Table_${qrTableNumber}` : qrLocationType)}
                  >
                    💾 Download QR (PNG)
                  </button>

                  <button
                    type="button"
                    className="btn-owner-secondary"
                    onClick={() => {
                      const link = `${qrBaseUrl}/review?table=${encodeURIComponent(qrLocationType === 'table' ? `Table ${qrTableNumber}` : qrLocationType)}&preview=true`;
                      window.open(link, '_blank');
                    }}
                  >
                    ↗ Test Link in New Tab
                  </button>
                </div>
              </div>

              {/* QR Preview Card */}
              <div className="qr-preview-card">
                <div className="table-stand-frame">
                  <div className="stand-header">
                    <span className="stand-logo">☕</span>
                    <h4 className="stand-name">{businessName}</h4>
                    <span className="stand-table-tag">
                      {qrLocationType === 'table' ? `Table ${qrTableNumber}` : qrLocationType.toUpperCase()}
                    </span>
                  </div>

                  {generatedQrDataUrl ? (
                    <img
                      src={generatedQrDataUrl}
                      alt="Generated QR Code"
                      className="stand-qr-img"
                    />
                  ) : (
                    <div className="stand-qr-placeholder">Generating...</div>
                  )}

                  <div className="stand-footer">
                    <span>Scan to share your feedback & Google review ⭐</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Table Directory */}
            <div className="quick-tables-box" style={{ marginTop: '2.5rem' }}>
              <h3 className="section-box-title">Quick Download for Common Tables</h3>
              <div className="table-badges-grid">
                {['1', '2', '3', '4', '5', '6', '7', '8', 'Counter', 'Receipt'].map((t) => (
                  <button
                    key={t}
                    type="button"
                    className="table-download-chip"
                    onClick={() => {
                      if (t === 'Counter' || t === 'Receipt') {
                        setQrLocationType(t.toLowerCase());
                      } else {
                        setQrLocationType('table');
                        setQrTableNumber(t);
                      }
                    }}
                  >
                    <span>{t.includes('Counter') || t.includes('Receipt') ? t : `Table ${t}`}</span>
                    <span className="chip-action">View & Download</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: REVIEW ACTIVITY */}
      {activeTab === 'activity' && (
        <div className="owner-view-container tab-fade-in">
          <div className="owner-section-box">
            <div className="section-box-header">
              <div>
                <h2 className="setup-title">Review Activity & Engagement</h2>
                <p className="setup-subtitle">
                  Real-time metrics from customer QR scans and review journeys.
                </p>
              </div>

              <button
                type="button"
                className="btn-owner-secondary"
                onClick={fetchAnalytics}
                disabled={isLoadingAnalytics}
              >
                {isLoadingAnalytics ? 'Refreshing...' : '🔄 Refresh Activity'}
              </button>
            </div>

            {/* Metric counters */}
            <div className="stats-metric-row">
              <div className="metric-pill">
                <span className="metric-number">{analytics.total_generations || 0}</span>
                <span className="metric-label">Review drafts created</span>
              </div>

              <div className="metric-pill">
                <span className="metric-number">{analytics.google_clicks || 0}</span>
                <span className="metric-label">Google review journeys started</span>
              </div>

              <div className="metric-pill">
                <span className="metric-number">{analytics.reviews_copied || 0}</span>
                <span className="metric-label">Reviews copied by guests</span>
              </div>
            </div>

            {/* Top appreciated aspects */}
            {analytics.top_topics && analytics.top_topics.length > 0 && (
              <div className="appreciated-topics-section" style={{ marginTop: '2rem' }}>
                <h3 className="section-box-title">Most Appreciated Highlights</h3>
                <div className="topic-bar-list">
                  {analytics.top_topics.map((item, idx) => (
                    <div key={idx} className="topic-bar-row">
                      <span className="topic-name">{item.topic}</span>
                      <span className="topic-count">{item.count} mentions</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Timeline Activity */}
            <div className="timeline-section" style={{ marginTop: '2rem' }}>
              <h3 className="section-box-title">Recent Activity Feed</h3>
              {analytics.recent_activity && analytics.recent_activity.length > 0 ? (
                <div className="activity-feed-list">
                  {analytics.recent_activity.map((entry, idx) => (
                    <div key={idx} className="feed-item">
                      <span className="feed-dot">●</span>
                      <span className="feed-text">{entry}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-feed-notice">
                  <span>No recent activity recorded yet. Try scanning your QR code or previewing the customer experience.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: SETTINGS */}
      {activeTab === 'settings' && (
        <div className="owner-view-container tab-fade-in">
          <div className="owner-section-box">
            <h2 className="setup-title">Settings & Configuration</h2>
            <div className="settings-card-stack">
              <div className="settings-row">
                <div>
                  <strong>Restaurant Identifier</strong>
                  <p className="setting-desc">Unique identifier for this location in ChurnLens.</p>
                </div>
                <span className="settings-value-pill">{businessId}</span>
              </div>

              <div className="settings-row">
                <div>
                  <strong>Google Review Link</strong>
                  <p className="setting-desc">Official Google Business Profile review URL.</p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span className="settings-value-pill">
                    {googleReviewUrl ? 'Connected' : 'Not set'}
                  </span>
                  <button
                    type="button"
                    className="btn-owner-secondary"
                    onClick={() => setActiveTab('setup')}
                  >
                    Edit
                  </button>
                </div>
              </div>

              <div className="settings-row">
                <div>
                  <strong>Customer Experience Preview</strong>
                  <p className="setting-desc">Preview what guests see when scanning table QR codes.</p>
                </div>
                <button
                  type="button"
                  className="btn-owner-secondary"
                  onClick={onPreviewCustomer}
                >
                  Open Preview ↗
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
