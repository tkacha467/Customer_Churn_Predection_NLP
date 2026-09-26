import { useState, useEffect } from 'react';

export default function BusinessConsole({ businessId = 'default_business' }) {
  const [googleUrl, setGoogleUrl] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [isConfigured, setIsConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // Analytics
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/businesses/${businessId}/review-link`);
      const data = await res.json();
      setGoogleUrl(data.review_url);
      setIsConfigured(data.is_configured);
      if (data.business_name) setBusinessName(data.business_name);
    } catch (err) {
      console.error('Failed to load business config:', err);
    }
  };

  const fetchAnalytics = async () => {
    setLoadingAnalytics(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/analytics');
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoadingAnalytics(false);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId]);

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveStatus('');

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/businesses/${businessId}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_name: businessName,
          google_review_url: googleUrl
        })
      });

      if (res.ok) {
        setSaveStatus('Settings successfully saved!');
        setIsConfigured(true);
        setTimeout(() => setSaveStatus(''), 4000);
      } else {
        setSaveStatus('Failed to update configuration.');
      }
    } catch (err) {
      console.error('Error updating config:', err);
      setSaveStatus('Error connecting to backend.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="business-console-wrapper">
      <div className="grid-2">
        {/* Google Link Configuration */}
        <div className="glass-panel">
          <div className="section-badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#34d399' }}>
            Merchant Configuration
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem', fontSize: '1.6rem' }}>
            Google Review Link Setup
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Configure the official Google Business review request URL for your customers. When a customer finishes crafting their review, ChurnLens redirects them to this link.
          </p>

          <form onSubmit={handleSaveConfig}>
            <div className="input-group">
              <label>Business Name</label>
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="E.g., Artisan Cafe & Roastery"
                required
              />
            </div>

            <div className="input-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label>Official Google Review Link</label>
                <span className={`status-pill ${isConfigured ? 'status-pill-ok' : 'status-pill-warn'}`}>
                  {isConfigured ? '● Active' : '● Needs Setup'}
                </span>
              </div>
              <input
                type="url"
                value={googleUrl}
                onChange={(e) => setGoogleUrl(e.target.value)}
                placeholder="https://g.page/r/.../review or https://search.google.com/local/writereview?placeid=..."
                required
              />
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                💡 Tip: Find this in your Google Business Profile under "Ask for reviews" → "Get more reviews".
              </div>
            </div>

            {saveStatus && (
              <div style={{ color: saveStatus.includes('success') ? 'var(--success)' : 'var(--danger)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                {saveStatus}
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Saving...' : '💾 Save Google Review Link'}
            </button>
          </form>
        </div>

        {/* Security & Architecture Info */}
        <div className="glass-panel">
          <div className="section-badge" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' }}>
            Google Policy Compliant
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem', fontSize: '1.6rem' }}>
            Submission Architecture
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            ChurnLens adheres to Google Business Profile policies and API guidelines:
          </p>

          <ul className="info-list">
            <li>
              <strong>Customer-Controlled:</strong> The user explicitly edits and approves their draft before submission. ChurnLens never posts automatically.
            </li>
            <li>
              <strong>Direct Handoff:</strong> Reviews are completed on Google Maps using official review deep-links.
            </li>
            <li>
              <strong>No Fabrications:</strong> The AI acts strictly as a writing assistant based on real customer feedback.
            </li>
            <li>
              <strong>Future OAuth Ready:</strong> Ready for merchant-authorized retrieval and response analytics once credentials are provisioned.
            </li>
          </ul>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="glass-panel" style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ color: 'var(--primary)' }}>Review Generation Analytics</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Real-time funnel metrics and sentiment consistency tracking.
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary"
            onClick={fetchAnalytics}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            🔄 Refresh Metrics
          </button>
        </div>

        {analytics ? (
          <div>
            <div className="analytics-metrics-grid">
              <div className="stat-card">
                <div className="stat-val">{analytics.total_generations}</div>
                <div className="stat-title">Reviews Generated</div>
              </div>
              <div className="stat-card">
                <div className="stat-val">{analytics.google_clicks}</div>
                <div className="stat-title">Google Clicks</div>
              </div>
              <div className="stat-card">
                <div className="stat-val">{analytics.conversion_rate_percent}%</div>
                <div className="stat-title">Funnel Conversion</div>
              </div>
              <div className="stat-card">
                <div className="stat-val">{analytics.regenerations}</div>
                <div className="stat-title">Regenerations</div>
              </div>
              <div className="stat-card">
                <div className="stat-val">{analytics.validations_passed}</div>
                <div className="stat-title">Integrity Validated</div>
              </div>
            </div>

            {/* Event Log Preview */}
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-main)' }}>
                Recent Operational Events (Privacy Preserved)
              </h3>
              <div className="event-stream">
                {analytics.recent_events && analytics.recent_events.length > 0 ? (
                  analytics.recent_events.slice().reverse().map((ev) => (
                    <div key={ev.event_id} className="event-row">
                      <span className="event-badge">{ev.event_name}</span>
                      <span className="event-time">
                        {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                      </span>
                      <span className="event-meta">
                        {ev.metadata ? JSON.stringify(ev.metadata) : ''}
                      </span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>
                    No events recorded yet. Generate your first review to see real-time events!
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            {loadingAnalytics ? 'Loading analytics...' : 'No analytics data available.'}
          </div>
        )}
      </div>
    </div>
  );
}
