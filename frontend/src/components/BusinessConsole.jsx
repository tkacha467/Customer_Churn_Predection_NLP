import { useState, useEffect } from 'react';
import QRCode from 'qrcode';

export default function BusinessConsole({ businessId = 'default_business' }) {
  // Navigation Sub-tab inside Management Portal
  const [subTab, setSubTab] = useState('overview'); // 'overview' | 'qr_studio' | 'reply_studio' | 'tickets' | 'settings'

  // Business Configuration State
  const [googleUrl, setGoogleUrl] = useState('');
  const [businessName, setBusinessName] = useState('Cuore Cafe & Artisan Roastery');
  const [category, setCategory] = useState('Specialty Coffee & All-Day Dining');
  const [isConfigured, setIsConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // Analytics State
  const [analytics, setAnalytics] = useState(null);

  // Table QR Studio State
  const [selectedTable, setSelectedTable] = useState('Table 4');
  const [qrDiningType, setQrDiningType] = useState('coffee_break');
  const [qrDataUrl, setQrDataUrl] = useState('');

  // Manager Review Reply Studio State
  const [guestName, setGuestName] = useState('Alexander');
  const [replyRating, setReplyRating] = useState(5);
  const [guestReviewText, setGuestReviewText] = useState('The oat flat white and almond croissant were outstanding! Wonderful service from the team.');
  const [replyTone, setReplyTone] = useState('gracious');
  const [generatedReply, setGeneratedReply] = useState('');
  const [isGeneratingReply, setIsGeneratingReply] = useState(false);
  const [copiedReply, setCopiedReply] = useState(false);

  // Private Resolution Tickets State
  const [privateTickets, setPrivateTickets] = useState([]);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/businesses/${businessId}/review-link`);
      const data = await res.json();
      setGoogleUrl(data.review_url);
      setIsConfigured(data.is_configured);
      if (data.business_name) setBusinessName(data.business_name);
      if (data.category) setCategory(data.category);
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

  const fetchTickets = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/private-tickets');
      const data = await res.json();
      setPrivateTickets(data);
    } catch (err) {
      console.error('Failed to load private tickets:', err);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchAnalytics();
    fetchTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId]);

  // Generate Table QR Code whenever table or dining type changes
  useEffect(() => {
    const tableUrl = `${window.location.origin}/?table=${encodeURIComponent(selectedTable)}&dining=${encodeURIComponent(qrDiningType)}`;
    QRCode.toDataURL(tableUrl, {
      width: 260,
      margin: 2,
      color: {
        dark: '#0f172a',
        light: '#ffffff'
      }
    })
      .then(url => setQrDataUrl(url))
      .catch(err => console.error('QR generation error:', err));
  }, [selectedTable, qrDiningType]);

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
          google_review_url: googleUrl,
          category
        })
      });

      if (res.ok) {
        setSaveStatus('Hospitality settings successfully updated!');
        setIsConfigured(true);
        setTimeout(() => setSaveStatus(''), 4000);
      } else {
        setSaveStatus('Failed to update settings.');
      }
    } catch (err) {
      console.error('Error saving config:', err);
      setSaveStatus('Error connecting to backend.');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateReply = async (e) => {
    e.preventDefault();
    if (!guestReviewText.trim()) return;

    setIsGeneratingReply(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reviews/manager-reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guest_review: guestReviewText,
          rating: replyRating,
          guest_name: guestName,
          manager_name: `${businessName} Management`,
          tone: replyTone
        })
      });

      const data = await res.json();
      setGeneratedReply(data.reply);
    } catch (err) {
      console.error('Reply generation failed:', err);
    } finally {
      setIsGeneratingReply(false);
    }
  };

  const handleCopyReply = () => {
    navigator.clipboard.writeText(generatedReply);
    setCopiedReply(true);
    setTimeout(() => setCopiedReply(false), 2500);
  };

  const handlePrintStandee = () => {
    window.print();
  };

  return (
    <div className="business-console-wrapper">
      {/* Management Navigation Tabs */}
      <div className="subnav-container">
        <button
          type="button"
          className={`subnav-btn ${subTab === 'overview' ? 'active' : ''}`}
          onClick={() => setSubTab('overview')}
        >
          📊 Hospitality Overview
        </button>
        <button
          type="button"
          className={`subnav-btn ${subTab === 'qr_studio' ? 'active' : ''}`}
          onClick={() => setSubTab('qr_studio')}
        >
          📱 Table QR Standee Studio
        </button>
        <button
          type="button"
          className={`subnav-btn ${subTab === 'reply_studio' ? 'active' : ''}`}
          onClick={() => setSubTab('reply_studio')}
        >
          ✍️ AI Google Review Replies
        </button>
        <button
          type="button"
          className={`subnav-btn ${subTab === 'tickets' ? 'active' : ''}`}
          onClick={() => setSubTab('tickets')}
        >
          🛎️ Private Guest Tickets ({privateTickets.length})
        </button>
        <button
          type="button"
          className={`subnav-btn ${subTab === 'settings' ? 'active' : ''}`}
          onClick={() => setSubTab('settings')}
        >
          ⚙️ Google Profile Settings
        </button>
      </div>

      {/* 1. OVERVIEW: EXECUTIVE HOSPITALITY METRICS */}
      {subTab === 'overview' && (
        <div className="animate-fade">
          {/* Hero KPI Matrix */}
          <div className="analytics-metrics-grid">
            <div className="stat-card">
              <div className="stat-val" style={{ color: '#10b981' }}>
                {analytics?.csat_score || '96.2'}%
              </div>
              <div className="stat-title">Guest Satisfaction Index (CSAT)</div>
              <div className="stat-subtitle">Derived from table feedback</div>
            </div>

            <div className="stat-card">
              <div className="stat-val" style={{ color: '#3b82f6' }}>
                {analytics?.total_generations || 0}
              </div>
              <div className="stat-title">Table Drafts Generated</div>
              <div className="stat-subtitle">30-day verified volume</div>
            </div>

            <div className="stat-card">
              <div className="stat-val" style={{ color: '#fbbf24' }}>
                {analytics?.conversion_rate_percent || 0}%
              </div>
              <div className="stat-title">Table-to-Google Conversion</div>
              <div className="stat-subtitle">Diners who opened Google Maps</div>
            </div>

            <div className="stat-card">
              <div className="stat-val" style={{ color: '#a855f7' }}>
                {analytics?.private_tickets_count || privateTickets.length}
              </div>
              <div className="stat-title">1-Star Reviews Deflected</div>
              <div className="stat-subtitle">Resolved privately in-house</div>
            </div>
          </div>

          {/* Aspect Health & Operational Matrix */}
          <div className="grid-2" style={{ marginTop: '2rem' }}>
            <div className="glass-panel">
              <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>
                Dining & Kitchen Aspect Health
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                Real-time sentiment score across key operational touchpoints.
              </p>

              <div className="aspect-health-list">
                {(analytics?.aspect_health || []).map((item, idx) => (
                  <div key={idx} className="aspect-health-row">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 600 }}>{item.aspect}</span>
                      <span style={{ color: item.satisfaction >= 90 ? '#34d399' : '#fbbf24' }}>
                        {item.satisfaction}% Positive ({item.volume} mentions)
                      </span>
                    </div>
                    <div className="progress-track">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${item.satisfaction}%`,
                          background: item.satisfaction >= 90 ? 'linear-gradient(90deg, #10b981, #34d399)' : 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Operational Events */}
            <div className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ color: 'var(--text-main)' }}>Live Table Events Stream</h3>
                <button type="button" className="btn-secondary" onClick={fetchAnalytics} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                  🔄 Refresh
                </button>
              </div>

              <div className="event-stream" style={{ maxHeight: '340px' }}>
                {analytics?.recent_events && analytics.recent_events.length > 0 ? (
                  analytics.recent_events.slice().reverse().map(ev => (
                    <div key={ev.event_id} className="event-row">
                      <span className="event-badge">{ev.event_name.replace(/_/g, ' ')}</span>
                      <span className="event-time">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
                      <span className="event-meta">{JSON.stringify(ev.metadata)}</span>
                    </div>
                  ))
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No table activity recorded yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. TABLE QR STANDEE STUDIO */}
      {subTab === 'qr_studio' && (
        <div className="glass-panel animate-fade">
          <div className="section-badge" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' }}>
            Hospitality Marketing & Operations
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Table Standee & Bill Folder QR Generator
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
            Print luxury table tents, bill folder cards, or counter displays. When guests scan this code at their table, it opens the streamlined mobile review assistant pre-configured for their specific table number.
          </p>

          <div className="grid-2">
            <div>
              <div className="input-group">
                <label>Select Table / Seating Area</label>
                <select value={selectedTable} onChange={(e) => setSelectedTable(e.target.value)}>
                  {[...Array(20)].map((_, i) => (
                    <option key={i + 1} value={`Table ${i + 1}`}>Table {i + 1}</option>
                  ))}
                  <option value="Bar & Counter">Bar & Counter Area</option>
                  <option value="Patio Table A">Patio Table A</option>
                  <option value="Patio Table B">Patio Table B</option>
                  <option value="Takeaway Counter">Takeaway Pickup Counter</option>
                </select>
              </div>

              <div className="input-group">
                <label>Default Dining Context for this QR</label>
                <select value={qrDiningType} onChange={(e) => setQrDiningType(e.target.value)}>
                  <option value="coffee_break">Coffee & Work</option>
                  <option value="brunch">Brunch & Pastries</option>
                  <option value="lunch_dinner">Lunch & Dinner</option>
                  <option value="takeaway">Takeaway Express</option>
                </select>
              </div>

              <div className="input-group">
                <label>Generated Guest Direct URL</label>
                <input
                  type="text"
                  readOnly
                  value={`${window.location.origin}/?table=${encodeURIComponent(selectedTable)}&dining=${encodeURIComponent(qrDiningType)}`}
                  style={{ background: 'rgba(15, 23, 42, 0.4)', fontSize: '0.85rem', color: '#94a3b8' }}
                />
              </div>

              <button type="button" className="btn-primary" onClick={handlePrintStandee} style={{ marginTop: '1rem' }}>
                🖨️ Print Luxury Table Standee
              </button>
            </div>

            {/* Printable Luxury Table Standee Preview */}
            <div className="printable-standee-container">
              <div className="standee-card">
                <div className="standee-brand">{businessName}</div>
                <div className="standee-tagline">Artisan Coffee & Culinary Hospitality</div>
                
                {qrDataUrl && (
                  <div className="qr-wrapper">
                    <img src={qrDataUrl} alt="Table QR Code" className="qr-image" />
                  </div>
                )}

                <div className="standee-table-badge">{selectedTable}</div>
                <div className="standee-cta">Scan to share your experience</div>
                <div className="standee-subcta">Takes less than 45 seconds • AI-assisted</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. MANAGER AI REVIEW REPLY STUDIO */}
      {subTab === 'reply_studio' && (
        <div className="glass-panel animate-fade">
          <div className="section-badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24' }}>
            Reputation Management
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Manager AI Response Studio (Google Maps)
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Responding graciously to every Google review boosts SEO and guest loyalty. Paste incoming Google reviews below to generate Michelin-standard manager responses tailored to guest sentiment.
          </p>

          <div className="grid-2">
            <form onSubmit={handleGenerateReply}>
              <div className="grid-2" style={{ gap: '1rem', marginBottom: '1rem' }}>
                <div className="input-group" style={{ marginBottom: 0 }}>
                  <label>Guest Name</label>
                  <input
                    type="text"
                    value={guestName}
                    onChange={(e) => setGuestName(e.target.value)}
                    placeholder="E.g. Samantha M."
                    required
                  />
                </div>

                <div className="input-group" style={{ marginBottom: 0 }}>
                  <label>Rating Received</label>
                  <select value={replyRating} onChange={(e) => setReplyRating(Number(e.target.value))}>
                    <option value={5}>5 Stars (Exceptional)</option>
                    <option value={4}>4 Stars (Very Good)</option>
                    <option value={3}>3 Stars (Average / Mixed)</option>
                    <option value={2}>2 Stars (Critical Complaint)</option>
                    <option value={1}>1 Star (Severe Complaint)</option>
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label>Guest Review Text from Google</label>
                <textarea
                  rows="4"
                  value={guestReviewText}
                  onChange={(e) => setGuestReviewText(e.target.value)}
                  placeholder="Paste guest's review from Google Business Profile..."
                  required
                />
              </div>

              <div className="input-group">
                <label>Response Tone</label>
                <select value={replyTone} onChange={(e) => setReplyTone(e.target.value)}>
                  <option value="gracious">Gracious & Warm (Premier Hospitality)</option>
                  <option value="apologetic">Direct Accountability & Resolution (For Complaints)</option>
                  <option value="professional">Courteous & Concise</option>
                </select>
              </div>

              <button type="submit" className="btn-primary" disabled={isGeneratingReply}>
                {isGeneratingReply ? 'Crafting Manager Response...' : '✨ Generate Hospitality Response'}
              </button>
            </form>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="section-badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
                GM Ready-to-Post Reply
              </div>

              <div className="review-editor-container" style={{ flex: 1 }}>
                <textarea
                  className="review-textarea"
                  rows="8"
                  value={generatedReply}
                  onChange={(e) => setGeneratedReply(e.target.value)}
                  placeholder="Generated response will appear here..."
                />
                {generatedReply && (
                  <button
                    type="button"
                    className="copy-chip-btn"
                    onClick={handleCopyReply}
                  >
                    {copiedReply ? '✓ Copied!' : '📋 Copy to Clipboard'}
                  </button>
                )}
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
                💡 Tip: Copy and paste this directly into your Google Business Profile reply window.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. PRIVATE TICKETS (NEGATIVE FEEDBACK DEFLECTION) */}
      {subTab === 'tickets' && (
        <div className="glass-panel animate-fade">
          <div className="section-badge" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' }}>
            Direct General Manager Resolution
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Private Guest Resolution Tickets
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            When a diner experiences an issue and gives 1-2 stars, ChurnLens offers them direct GM resolution. These private tickets allow management to contact the guest and resolve complaints before they become public Google reviews.
          </p>

          {privateTickets.length > 0 ? (
            <div className="tickets-grid">
              {privateTickets.slice().reverse().map(ticket => (
                <div key={ticket.ticket_id} className="ticket-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span className="ticket-id">{ticket.ticket_id}</span>
                    <span className="ticket-table">{ticket.table_number}</span>
                  </div>
                  <div className="ticket-rating">
                    Rating: {'★'.repeat(ticket.rating)}{'☆'.repeat(5 - ticket.rating)}
                  </div>
                  <div className="ticket-note">"{ticket.diner_note}"</div>
                  <div className="ticket-contact">
                    <strong>Guest Contact:</strong> {ticket.guest_contact || 'None provided'}
                  </div>
                  <div className="ticket-time">
                    {new Date(ticket.timestamp * 1000).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '0.5rem' }}>🎉</span>
              <h3>No unresolved guest complaints!</h3>
              <p style={{ fontSize: '0.9rem' }}>All dining tables are reporting positive experiences.</p>
            </div>
          )}
        </div>
      )}

      {/* 5. GOOGLE SETTINGS */}
      {subTab === 'settings' && (
        <div className="glass-panel animate-fade">
          <div className="section-badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#34d399' }}>
            Merchant Setup
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Google Business Profile Integration
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Configure your cafe/restaurant Google Business Profile review request link.
          </p>

          <form onSubmit={handleSaveConfig} style={{ maxWidth: '600px' }}>
            <div className="input-group">
              <label>Business / Brand Name</label>
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="E.g., Cuore Cafe & Artisan Roastery"
                required
              />
            </div>

            <div className="input-group">
              <label>Hospitality Category</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="E.g., Specialty Coffee & All-Day Dining"
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
                placeholder="https://search.google.com/local/writereview?placeid=... or https://g.page/r/.../review"
                required
              />
            </div>

            {saveStatus && (
              <div style={{ color: saveStatus.includes('success') ? 'var(--success)' : 'var(--danger)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                {saveStatus}
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Saving...' : '💾 Save Google Review Settings'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
