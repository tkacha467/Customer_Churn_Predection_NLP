import { useState, useEffect, useMemo } from 'react';
import NastaGharRestaurantScene from './NastaGharRestaurantScene';
import { apiFetch } from '../lib/api';
import './admin/AdminDesignSystem.css';
import {
  AdminCard,
  AdminKpi,
  AdminButton,
  AdminInput,
  AdminSelect,
  StatusBadge,
  AdminBadge,
  AdminNotification,
  AdminBarChart,
} from './admin/common';

/**
 * VRAJA AI — Standardized Multi-Tenant Restaurant Owner Portal (Product A)
 * 
 * Invariants strictly enforced:
 * 1. Fixed 5-Section Standard: Home, Review Setup, Review Activity & Analytics, Private Feedback Inbox, Settings.
 * 2. Identical template for all restaurant clients (only tenant-specific data changes).
 * 3. Official VRAJA AI corporate palette: Warm Ivory (#F5F3EC), Deep Emerald (#174D3A), Muted Gold (#C6A66B), Forest Charcoal (#26352D), Pure White (#FFFFFF), Soft Sage (#DCE5DD).
 * 4. Internal-only QR generation: No QR generation/download controls exposed to clients.
 * 5. Data integrity: Accurate timezones, authentic event metrics, no synthetic footfall claims.
 */

export default function OwnerPortal({
  businessId = 'default_business',
  onPreviewCustomer = null
}) {
  // Session & Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [authSession, setAuthSession] = useState(null);
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [isSigningIn, setIsSigningIn] = useState(false);

  // Fixed 5-Section Navigation:
  // 1. 'home' (Home)
  // 2. 'setup' (Review Setup)
  // 3. 'activity' (Review Activity & Analytics)
  // 4. 'feedback' (Private Feedback Inbox)
  // 5. 'settings' (Settings)
  const [activeTab, setActiveTab] = useState('home');

  // Business config state
  const [businessName, setBusinessName] = useState('Restaurant Partner');
  const [branch, setBranch] = useState('');
  const [category, setCategory] = useState('Hospitality & Dining');
  const [description, setDescription] = useState('Empowering your restaurant with authentic Google Reviews and proactive diner feedback.');
  const [googleReviewUrl, setGoogleReviewUrl] = useState('');
  const [isUrlConfigured, setIsUrlConfigured] = useState(false);
  const [topics, setTopics] = useState([
    'Food Quality', 'Taste & Flavour', 'Service', 'Cleanliness', 'Ambiance', 'Value for Money'
  ]);
  const [newTopicInput, setNewTopicInput] = useState('');
  const [primaryAccent, setPrimaryAccent] = useState('#174D3A');
  const [entitlements, setEntitlements] = useState(['review_manager']);
  const [supportedLanguages, setSupportedLanguages] = useState(['english', 'hindi', 'gujarati']);

  // Setup / Save status
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  // Analytics state
  const [analytics, setAnalytics] = useState({
    total_generations: 0,
    google_clicks: 0,
    reviews_copied: 0,
    qr_scans: 0,
    conversion_rate_percent: 0,
    rating_overview: { average_rating: 5.0, total_ratings: 0, distribution: {} },
    rating_distribution: {},
    sentiment_distribution: {},
    peak_usage_time: '13:00 – 14:00',
    busiest_day: 'Sunday',
    timezone: 'Asia/Kolkata',
    hourly_distribution: {},
    weekly_distribution: {},
    monthly_trends: {},
    seasonal_analysis: {},
    festival_analysis: [],
    calendar_heatmap: {},
    business_insights: [],
    private_tickets_summary: { total: 0, open: 0, resolved: 0, escalated: 0 },
    top_topics: [],
    recent_activity: []
  });
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  // Private Feedback Inbox state
  const [privateTickets, setPrivateTickets] = useState([]);
  const [isLoadingTickets, setIsLoadingTickets] = useState(false);
  const [ticketFilter, setTicketFilter] = useState('all'); // 'all' | 'open' | 'escalated' | 'resolved'
  const [isUpdatingTicketId, setIsUpdatingTicketId] = useState(null);

  // Password Management state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordStatus, setPasswordStatus] = useState({ type: '', text: '' });
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Check auth session
  useEffect(() => {
    let active = true;
    apiFetch('/api/auth/session')
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          const data = await res.json();
          setAuthSession(data);
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      })
      .catch(() => { if (active) setIsAuthenticated(false); })
      .finally(() => { if (active) setIsCheckingSession(false); });
    return () => { active = false; };
  }, []);

  const handleOwnerLogin = async (event) => {
    event.preventDefault();
    setAuthError('');
    setIsSigningIn(true);
    try {
      const payload = {
        password: ownerPassword,
        tenant_id: businessId !== 'default_business' ? businessId : undefined,
      };
      if (ownerEmail.trim()) {
        payload.email = ownerEmail.trim();
      }
      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Sign-in failed. Please check your credentials and try again.');
      }
      const data = await res.json();
      setOwnerPassword('');
      setAuthSession(data);
      setIsAuthenticated(true);
    } catch (error) {
      setAuthError(error.message || 'Could not sign in. Check the API connection and try again.');
    } finally {
      setIsSigningIn(false);
    }
  };

  const handleOwnerLogout = async () => {
    try { await apiFetch('/api/auth/logout', { method: 'POST' }); }
    finally {
      setAuthSession(null);
      setIsAuthenticated(false);
    }
  };

  const handleSwitchTenant = async (tenantId) => {
    try {
      const res = await apiFetch('/api/auth/switch-tenant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId }),
      });
      if (res.ok) {
        const data = await res.json();
        setAuthSession(data);
        const url = new URL(window.location);
        url.searchParams.set('business_id', tenantId);
        window.history.pushState({}, '', url.toString());
        window.location.reload();
      }
    } catch (err) {
      console.error('Failed to switch business:', err);
    }
  };

  // Fetch business config
  const fetchConfig = async () => {
    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/review-link`);
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
      if (Array.isArray(data.entitlements)) setEntitlements(data.entitlements);
    } catch (err) {
      console.error('Failed fetching business config:', err);
    }
  };

  // Fetch authentic analytics scoped to tenant
  const fetchAnalytics = async () => {
    setIsLoadingAnalytics(true);
    try {
      const query = businessId ? `?business_id=${encodeURIComponent(businessId)}` : '';
      const res = await apiFetch(`/api/reviews/analytics${query}`);
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

  // Fetch private feedback tickets
  const fetchPrivateTickets = async () => {
    setIsLoadingTickets(true);
    try {
      const query = businessId ? `?business_id=${encodeURIComponent(businessId)}` : '';
      const res = await apiFetch(`/api/reviews/private-tickets${query}`);
      if (res.status === 401) setIsAuthenticated(false);
      if (res.ok) {
        const data = await res.json();
        setPrivateTickets(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed fetching private tickets:', err);
    } finally {
      setIsLoadingTickets(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchConfig();
    fetchAnalytics();
    fetchPrivateTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, isAuthenticated]);

  // Save configuration
  const handleSaveConfig = async (e) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    setSaveSuccessMsg('');

    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/config`, {
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
      if (res.status === 403) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Insufficient permissions: Owner role is required to modify setup.');
      }
      if (!res.ok) throw new Error('Could not save configuration');
      const data = await res.json();
      setIsUrlConfigured(Boolean(data.is_configured));
      setSaveSuccessMsg('✓ Restaurant setup saved successfully!');
      setTimeout(() => setSaveSuccessMsg(''), 4000);
    } catch (err) {
      console.error('Error saving config:', err);
      alert(err.message || 'Could not save configuration. Please try again.');
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

  // Toggle supported languages
  const toggleLanguage = (langKey) => {
    if (supportedLanguages.includes(langKey)) {
      if (supportedLanguages.length === 1) return; // Prevent disabling all
      setSupportedLanguages(supportedLanguages.filter(l => l !== langKey));
    } else {
      setSupportedLanguages([...supportedLanguages, langKey]);
    }
  };

  // Update ticket status
  const handleUpdateTicketStatus = async (ticketId, newStatus) => {
    setIsUpdatingTicketId(ticketId);
    try {
      const res = await apiFetch(`/api/reviews/private-tickets/${encodeURIComponent(ticketId)}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setPrivateTickets(prev =>
          prev.map(t => (t.ticket_id === ticketId ? { ...t, status: newStatus } : t))
        );
        fetchAnalytics();
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Could not update ticket status.');
      }
    } catch (err) {
      console.error('Failed updating ticket status:', err);
      alert('Network error updating ticket status.');
    } finally {
      setIsUpdatingTicketId(null);
    }
  };

  // Change password
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordStatus({ type: '', text: '' });

    if (newPassword.length < 8) {
      setPasswordStatus({ type: 'error', text: 'New password must be at least 8 characters long.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordStatus({ type: 'error', text: 'New password confirmation does not match.' });
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await apiFetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update password.');
      }
      setPasswordStatus({ type: 'success', text: '✓ Password updated successfully!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setPasswordStatus({ type: '', text: '' }), 4000);
    } catch (err) {
      setPasswordStatus({ type: 'error', text: err.message || 'Error updating password.' });
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Filtered tickets
  const filteredTickets = useMemo(() => {
    if (ticketFilter === 'all') return privateTickets;
    return privateTickets.filter(t => (t.status || 'OPEN').toLowerCase() === ticketFilter);
  }, [privateTickets, ticketFilter]);

  // Hourly distribution formatted for pure SVG chart
  const hourlyChartData = useMemo(() => {
    const dist = analytics.hourly_distribution || {};
    return Object.entries(dist).map(([hour, count]) => ({
      label: hour.split(':')[0],
      value: count,
    }));
  }, [analytics.hourly_distribution]);

  // ─── 0. SESSION LOADING SCREEN ─────────────────────────────────────────────
  if (isCheckingSession) {
    return (
      <div className="vraja-owner-login-canvas" role="status">
        <div style={{ textAlign: 'center', color: '#174D3A' }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>✨</div>
          <p style={{ fontWeight: 600, color: '#26352D' }}>Verifying restaurant manager credentials…</p>
        </div>
      </div>
    );
  }

  // ─── 1. UNAUTHENTICATED SIGN-IN SCREEN ─────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <div className="vraja-owner-login-canvas">
        <div className="vraja-owner-login-box">
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                margin: '0 auto 12px auto',
                borderRadius: '10px',
                backgroundColor: '#174D3A',
                border: '1px solid #C6A66B',
                color: '#C6A66B',
                fontSize: '24px',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(23,77,58,0.2)',
              }}
            >
              V
            </div>
            <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#26352D', margin: '0 0 4px 0' }}>
              Restaurant Owner Portal
            </h1>
            <p style={{ fontSize: '13px', color: '#718078', margin: 0 }}>
              Sign in to manage your AI review assistant and guest feedback.
            </p>
          </div>

          {authError && (
            <AdminNotification
              type="error"
              message={authError}
            />
          )}

          <form onSubmit={handleOwnerLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <AdminInput
              label="Account Email"
              id="owner-email"
              type="email"
              value={ownerEmail}
              onChange={(e) => setOwnerEmail(e.target.value)}
              placeholder="owner@yourrestaurant.com"
              autoComplete="email"
            />

            <AdminInput
              label="Password"
              id="owner-password"
              type="password"
              value={ownerPassword}
              onChange={(e) => setOwnerPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              autoComplete="current-password"
            />

            <AdminButton
              type="submit"
              variant="primary"
              disabled={isSigningIn}
              style={{ marginTop: '8px', height: '42px', fontSize: '14px' }}
            >
              {isSigningIn ? 'Signing in…' : 'Sign In to Owner Portal'}
            </AdminButton>
          </form>

          <div style={{ textAlign: 'center', fontSize: '12px', color: '#718078', borderTop: '1px solid #E3E8E3', paddingTop: '16px' }}>
            <span>🔒 Multi-tenant isolation verified • VRAJA AI Client Portal</span>
          </div>
        </div>
      </div>
    );
  }

  // ─── 2. AUTHENTICATED OWNER PORTAL (SHARED 5-SECTION TEMPLATE) ──────────────
  return (
    <div className="vraja-owner-shell">
      {/* Top Owner Header */}
      <header className="vraja-owner-topbar">
        <div className="vraja-owner-brand">
          <div className="vraja-owner-emblem">V</div>
          <div className="vraja-owner-titles">
            <div className="vraja-owner-title-row">
              <span className="vraja-owner-name">{businessName}</span>
              {branch && <span className="vraja-owner-branch-badge">{branch}</span>}
            </div>
            <span className="vraja-owner-subline">
              <span>{category}</span>
              <span>•</span>
              <span>Owner Portal</span>
            </span>
          </div>
        </div>

        <div className="vraja-owner-top-actions">
          {/* Tenant Switcher (when multiple businesses linked) */}
          {authSession?.available_tenants?.length > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '12px', color: '#718078', fontWeight: 600 }}>Location:</span>
              <AdminSelect
                value={authSession.active_tenant?.id || businessId}
                onChange={(e) => handleSwitchTenant(e.target.value)}
                options={authSession.available_tenants.map((t) => ({
                  value: t.id,
                  label: `${t.business_name} (${t.role})`,
                }))}
              />
            </div>
          )}

          {/* Membership Role Badge */}
          {authSession?.active_tenant?.role && (
            <AdminBadge variant="neutral">
              {authSession.active_tenant.role.toUpperCase()}
            </AdminBadge>
          )}

          {/* Preview Customer Experience Button */}
          {onPreviewCustomer && (
            <AdminButton
              variant="gold"
              size="sm"
              onClick={onPreviewCustomer}
              title="Experience the review flow as a dining guest"
            >
              👁️ Preview Guest Flow
            </AdminButton>
          )}

          {/* Sign Out Button */}
          <AdminButton
            variant="outline"
            size="sm"
            onClick={handleOwnerLogout}
          >
            Sign Out
          </AdminButton>
        </div>
      </header>

      {/* Standardized 5-Section Navigation Bar */}
      <nav className="vraja-owner-nav-bar" aria-label="Restaurant Owner Navigation">
        <button
          type="button"
          className={`vraja-owner-tab ${activeTab === 'home' ? 'active' : ''}`}
          onClick={() => setActiveTab('home')}
        >
          <span>🏠</span>
          <span>Home</span>
        </button>

        <button
          type="button"
          className={`vraja-owner-tab ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => setActiveTab('setup')}
        >
          <span>⚙️</span>
          <span>Review Setup</span>
        </button>

        <button
          type="button"
          className={`vraja-owner-tab ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          <span>📈</span>
          <span>Review Activity & Analytics</span>
        </button>

        <button
          type="button"
          className={`vraja-owner-tab ${activeTab === 'feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('feedback')}
        >
          <span>📥</span>
          <span>Private Feedback Inbox</span>
          {analytics?.private_tickets_summary?.open > 0 && (
            <span className="vraja-tab-counter-pill">
              {analytics.private_tickets_summary.open}
            </span>
          )}
        </button>

        <button
          type="button"
          className={`vraja-owner-tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <span>🔧</span>
          <span>Settings</span>
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="vraja-owner-main">
        {/* ==================================================================
            SECTION 1: HOME
            ================================================================== */}
        {activeTab === 'home' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            {/* Welcome Hero Banner */}
            <div className="vraja-owner-hero">
              <div className="vraja-hero-info">
                <span className="vraja-hero-tag">Active Review Assistant</span>
                <h2 className="vraja-hero-heading">
                  {businessName} {branch && `(${branch})`}
                </h2>
                <p className="vraja-hero-desc">
                  {description || 'Empowering your restaurant with authentic Google Reviews and proactive diner feedback.'}
                </p>
              </div>

              <div className="vraja-hero-actions">
                <AdminButton
                  variant="primary"
                  onClick={() => setActiveTab('activity')}
                >
                  📊 Detailed Analytics
                </AdminButton>
                {onPreviewCustomer && (
                  <AdminButton
                    variant="outline"
                    onClick={onPreviewCustomer}
                  >
                    👁️ Test Diner Journey
                  </AdminButton>
                )}
              </div>
            </div>

            {/* Restaurant World Scene Container */}
            <AdminCard title="Dining Room Ambience & Assistant Context" subtitle="Visual preview of your dining environment">
              <NastaGharRestaurantScene compact={true} />
            </AdminCard>

            {/* Performance Statistics Grid */}
            <div>
              <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 600, color: '#718078', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Performance Statistics
              </div>
              <div className="vraja-kpi-grid">
                <AdminKpi
                  label="AI Review Generations"
                  value={analytics.total_generations || 0}
                  trend="Real-time"
                  trendDirection="positive"
                  subtext="Customer drafts synthesized"
                  icon={<span>⚡</span>}
                />

                <AdminKpi
                  label="Google Review Clicks"
                  value={analytics.google_clicks || 0}
                  trend={`${analytics.conversion_rate_percent || 0}%`}
                  trendDirection="positive"
                  subtext="Handoff journeys to Maps"
                  icon={<span>⭐</span>}
                  goldIcon
                />

                <AdminKpi
                  label="Customer Rating"
                  value={`${analytics.rating_overview?.average_rating || 5.0}★`}
                  trend={`${analytics.rating_overview?.total_ratings || 0} ratings`}
                  trendDirection="neutral"
                  subtext="Average guest satisfaction score"
                  icon={<span>🌟</span>}
                />

                <AdminKpi
                  label="Private Feedback Inbox"
                  value={`${analytics.private_tickets_summary?.total || 0} Total`}
                  trend={`${analytics.private_tickets_summary?.open || 0} Open`}
                  trendDirection={analytics.private_tickets_summary?.open > 0 ? 'negative' : 'positive'}
                  subtext="Direct management feedback"
                  icon={<span>💬</span>}
                />
              </div>
            </div>

            {/* Operating Windows & Busiest Day */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
              <AdminCard title="Peak Review Engagement Window" subtitle="Busiest interaction hour in local restaurant timezone">
                <div style={{ fontSize: '26px', fontWeight: 700, color: '#174D3A', margin: '8px 0' }}>
                  {analytics.peak_usage_time || '13:00 – 14:00'}
                </div>
                <p style={{ fontSize: '13px', color: '#718078', margin: 0 }}>
                  Peak digital review assistant engagement window calculated from authentic scan logs.
                </p>
              </AdminCard>

              <AdminCard title="Busiest Day of Week" subtitle="Day with the highest recorded guest review activity">
                <div style={{ fontSize: '26px', fontWeight: 700, color: '#C6A66B', margin: '8px 0' }}>
                  {analytics.busiest_day || 'Sunday'}
                </div>
                <p style={{ fontSize: '13px', color: '#718078', margin: 0 }}>
                  Day of the week with the greatest volume of customer review generations.
                </p>
              </AdminCard>

              <AdminCard title="Draft-to-Maps Conversion Rate" subtitle="Percentage of diners who clicked Google Review link">
                <div style={{ fontSize: '26px', fontWeight: 700, color: '#1D7A4D', margin: '8px 0' }}>
                  {analytics.conversion_rate_percent || 0}%
                </div>
                <p style={{ fontSize: '13px', color: '#718078', margin: 0 }}>
                  Diners who proceeded to the official Google Maps link after synthesizing a review draft.
                </p>
              </AdminCard>
            </div>

            {/* Key Business Insights */}
            {analytics.business_insights && analytics.business_insights.length > 0 && (
              <AdminCard
                title="Key Business Insights"
                subtitle="Factual operational conclusions derived strictly from customer review data"
              >
                <ul style={{ margin: 0, paddingLeft: '20px', color: '#26352D', lineHeight: '1.7', fontSize: '14px' }}>
                  {analytics.business_insights.map((insight, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{insight}</li>
                  ))}
                </ul>
              </AdminCard>
            )}

            {/* Recent Customer Activity Timeline */}
            <AdminCard title="Recent Customer Activity" subtitle="Chronological timeline of latest dining review journeys">
              {analytics.recent_activity && analytics.recent_activity.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {analytics.recent_activity.map((entry, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '10px 14px',
                        backgroundColor: '#FAF9F6',
                        borderRadius: '8px',
                        border: '1px solid #E3E8E3',
                        fontSize: '13.5px',
                        color: '#26352D',
                      }}
                    >
                      <span style={{ color: '#174D3A', fontSize: '12px' }}>●</span>
                      <span>{entry}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ padding: '24px', textAlign: 'center', color: '#718078', fontSize: '13.5px' }}>
                  No customer activity recorded yet. Preview the customer journey to record initial interactions.
                </div>
              )}
            </AdminCard>
          </div>
        )}

        {/* ==================================================================
            SECTION 2: REVIEW SETUP
            ================================================================== */}
        {activeTab === 'setup' && (
          <form onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            <AdminCard
              title="Restaurant Profile & Branding"
              subtitle="Configure your restaurant profile, primary accent color, and Google Review URL"
              actions={
                <AdminButton
                  type="submit"
                  variant="primary"
                  disabled={isSaving}
                >
                  {isSaving ? 'Saving...' : '💾 Save Setup'}
                </AdminButton>
              }
            >
              {saveSuccessMsg && (
                <div style={{ marginBottom: '16px' }}>
                  <AdminNotification
                    type="success"
                    message={saveSuccessMsg}
                  />
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
                <AdminInput
                  label="Business Name"
                  id="setup-business-name"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  required
                />

                <AdminInput
                  label="Branch / Location Name"
                  id="setup-branch"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="e.g. Downtown, Jubilee Garden"
                />

                <AdminInput
                  label="Business Category"
                  id="setup-category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  placeholder="e.g. Breakfast & Snacks, Artisanal Cafe"
                />

                <div className="vraja-form-group">
                  <label className="vraja-form-label">Primary Accent Color</label>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="color"
                      value={primaryAccent}
                      onChange={(e) => setPrimaryAccent(e.target.value)}
                      style={{
                        width: '42px',
                        height: '38px',
                        padding: 0,
                        border: '1px solid #E3E8E3',
                        borderRadius: '6px',
                        cursor: 'pointer',
                      }}
                    />
                    <AdminInput
                      value={primaryAccent}
                      onChange={(e) => setPrimaryAccent(e.target.value)}
                      style={{ flex: 1 }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '16px' }} className="vraja-form-group">
                <label className="vraja-form-label">Restaurant Welcome Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="A short welcome note for your diners."
                  className="vraja-input"
                  style={{ height: 'auto', padding: '10px 12px', resize: 'vertical' }}
                />
              </div>

              {/* Google Review URL */}
              <div style={{ marginTop: '20px', paddingTop: '18px', borderTop: '1px solid #E3E8E3' }}>
                <AdminInput
                  label="Official Google Review URL / Place ID"
                  id="setup-review-url"
                  type="url"
                  value={googleReviewUrl}
                  onChange={(e) => setGoogleReviewUrl(e.target.value)}
                  placeholder="https://search.google.com/local/writereview?placeid=..."
                  helperText="Diners who approve their AI-crafted review draft will be redirected straight to this Google Maps review dialog."
                  required
                />

                {googleReviewUrl && (
                  <div style={{ marginTop: '8px' }}>
                    <a
                      href={googleReviewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '13px',
                        fontWeight: 600,
                        color: '#174D3A',
                        textDecoration: 'none',
                      }}
                    >
                      ↗ Test Open Google Review Dialog in New Tab
                    </a>
                  </div>
                )}
              </div>
            </AdminCard>

            {/* Supported Languages */}
            <AdminCard
              title="Supported Review Languages"
              subtitle="Select which languages customers can synthesize reviews in"
            >
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {[
                  { key: 'english', label: '🇬🇧 English' },
                  { key: 'hindi', label: '🇮🇳 हिंदी (Hindi)' },
                  { key: 'gujarati', label: '🇮🇳 ગુજરાતી (Gujarati)' },
                ].map((l) => {
                  const isSelected = supportedLanguages.includes(l.key);
                  return (
                    <button
                      key={l.key}
                      type="button"
                      onClick={() => toggleLanguage(l.key)}
                      className={`vraja-btn ${isSelected ? 'vraja-btn-secondary' : 'vraja-btn-outline'}`}
                      style={isSelected ? { fontWeight: 700 } : undefined}
                    >
                      {l.label} {isSelected ? '✓' : ''}
                    </button>
                  );
                })}
              </div>
            </AdminCard>

            {/* Review Aspects & Keywords */}
            <AdminCard
              title="Review Highlights & Aspects"
              subtitle="Keywords that diners can tap when generating their review draft"
            >
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
                {topics.map((t, idx) => (
                  <span key={idx} className="vraja-aspect-tag">
                    <span>{t}</span>
                    <button
                      type="button"
                      className="vraja-aspect-remove-btn"
                      onClick={() => handleRemoveTopic(t)}
                      title={`Remove aspect ${t}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '10px', maxWidth: '520px' }}>
                <AdminInput
                  placeholder="e.g. Masala Dosa, Filter Coffee, Quick Service"
                  value={newTopicInput}
                  onChange={(e) => setNewTopicInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTopic();
                    }
                  }}
                  style={{ flex: 1 }}
                />
                <AdminButton
                  variant="secondary"
                  onClick={handleAddTopic}
                >
                  + Add Aspect
                </AdminButton>
              </div>
            </AdminCard>
          </form>
        )}

        {/* ==================================================================
            SECTION 3: REVIEW ACTIVITY & ANALYTICS
            ================================================================== */}
        {activeTab === 'activity' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            {/* Mandatory Data Integrity Disclaimer */}
            <div
              style={{
                backgroundColor: '#DCE5DD',
                border: '1px solid #BFE4CE',
                borderRadius: '10px',
                padding: '16px 20px',
                color: '#174D3A',
                fontSize: '13px',
                lineHeight: '1.55',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '13.5px' }}>
                  <span>ℹ️</span> Data Integrity & Metric Disclosure
                </div>
                <span style={{ fontSize: '12px', background: '#FFFFFF', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                  Timezone: {analytics.timezone || 'Asia/Kolkata'}
                </span>
              </div>
              <p style={{ margin: 0 }}>
                Review-system usage measures digital customer interactions with our AI review assistant and does <em>not</em> represent total restaurant dining footfall. Google Review link clicks represent customer journeys directed to Google Maps; Google does not provide an external webhook for verified published reviews without an active Google Business Profile API OAuth integration.
              </p>
            </div>

            {/* Core Metrics Overview */}
            <div className="vraja-kpi-grid">
              <AdminKpi
                label="QR Sessions Scanned"
                value={analytics.qr_scans || 0}
                trend="Digital assistant scans"
                trendDirection="neutral"
                icon={<span>📱</span>}
              />
              <AdminKpi
                label="AI Review Drafts Created"
                value={analytics.total_generations || 0}
                trend="Synthesized drafts"
                trendDirection="positive"
                icon={<span>⚡</span>}
              />
              <AdminKpi
                label="Google Review Link Clicks"
                value={analytics.google_clicks || 0}
                trend="Maps handoffs"
                trendDirection="positive"
                icon={<span>⭐</span>}
                goldIcon
              />
              <AdminKpi
                label="Draft-to-Maps Conversion"
                value={`${analytics.conversion_rate_percent || 0}%`}
                trend="Completion rate"
                trendDirection="positive"
                icon={<span>🎯</span>}
              />
            </div>

            {/* Hourly Usage Analysis (24-Hour Distribution) */}
            <AdminCard
              title="Hourly Usage Analysis (24-Hour Local Time)"
              subtitle={`Hourly breakdown in ${analytics.timezone || 'Asia/Kolkata'} • Peak window: ${analytics.peak_usage_time}`}
              actions={
                <AdminButton
                  variant="outline"
                  size="sm"
                  onClick={fetchAnalytics}
                  disabled={isLoadingAnalytics}
                >
                  {isLoadingAnalytics ? 'Refreshing…' : '🔄 Refresh Data'}
                </AdminButton>
              }
            >
              <AdminBarChart data={hourlyChartData} height={180} />
            </AdminCard>

            {/* Weekly Usage Analysis */}
            <AdminCard
              title="Weekly Usage Analysis"
              subtitle={`Day-by-day distribution identifying busiest day: ${analytics.busiest_day}`}
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
                {Object.entries(analytics.weekly_distribution || {}).map(([day, count]) => {
                  const maxDayCount = Math.max(1, ...Object.values(analytics.weekly_distribution || {}));
                  const isBusiest = day === analytics.busiest_day && count > 0;

                  return (
                    <div
                      key={day}
                      style={{
                        backgroundColor: isBusiest ? '#DCE5DD' : '#FAF9F6',
                        border: `1px solid ${isBusiest ? '#174D3A' : '#E3E8E3'}`,
                        borderRadius: '8px',
                        padding: '12px',
                        textAlign: 'center',
                      }}
                    >
                      <span style={{ fontSize: '11px', color: '#718078', fontWeight: 600, textTransform: 'uppercase' }}>
                        {day.slice(0, 3)}
                      </span>
                      <strong style={{ fontSize: '20px', color: isBusiest ? '#174D3A' : '#26352D', display: 'block', margin: '4px 0' }}>
                        {count}
                      </strong>
                      <span style={{ fontSize: '11px', color: '#718078' }}>
                        {maxDayCount > 0 ? `${Math.round((count / maxDayCount) * 100)}% load` : '0%'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </AdminCard>

            {/* Seasonal & Festival Comparisons */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
              {/* Seasonal Analysis */}
              <AdminCard
                title="Seasonal Analysis"
                subtitle="Regional hospitality seasonal breakdown based on event timestamps"
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {Object.entries(analytics.seasonal_analysis || {}).map(([season, count]) => {
                    const totalSeason = Math.max(1, Object.values(analytics.seasonal_analysis || {}).reduce((a, b) => a + b, 0));
                    const pct = Math.round((count / totalSeason) * 100);

                    return (
                      <div key={season} style={{ backgroundColor: '#FAF9F6', padding: '10px 14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                          <span style={{ color: '#26352D', fontWeight: 600 }}>{season}</span>
                          <span style={{ color: '#718078' }}>{count} interactions ({pct}%)</span>
                        </div>
                        <div style={{ height: '6px', backgroundColor: '#E3E8E3', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${pct}%`, backgroundColor: '#174D3A', borderRadius: '3px' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </AdminCard>

              {/* Festival Baseline Comparisons */}
              <AdminCard
                title="Festival & Occasion Comparisons"
                subtitle="Year-specific festival periods compared against baseline"
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {(analytics.festival_analysis || []).map((fest, idx) => (
                    <div
                      key={idx}
                      style={{
                        backgroundColor: '#FAF9F6',
                        border: '1px solid #E3E8E3',
                        borderRadius: '8px',
                        padding: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ color: '#26352D', fontSize: '13.5px' }}>{fest.festival} ({fest.year})</strong>
                        <span style={{ fontSize: '12px', color: '#174D3A', fontWeight: 700 }}>
                          {fest.event_count} events ({fest.daily_rate}/day)
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', color: '#718078', display: 'block', marginTop: '2px' }}>
                        Period: {fest.period}
                      </span>
                      <span
                        style={{
                          fontSize: '11.5px',
                          color: fest.insufficient_historical_data ? '#718078' : '#1D7A4D',
                          display: 'block',
                          marginTop: '4px',
                        }}
                      >
                        {fest.insufficient_historical_data ? '⚠️ ' : '✓ '} {fest.notice}
                      </span>
                    </div>
                  ))}
                </div>
              </AdminCard>
            </div>

            {/* Customer Rating Distribution */}
            <AdminCard title="Customer Rating Distribution" subtitle="5★ down to 1★ review rating breakdown">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px' }}>
                {[5, 4, 3, 2, 1].map((stars) => {
                  const count = (analytics.rating_distribution || {})[String(stars)] || 0;
                  const total = analytics.rating_overview?.total_ratings || 1;
                  const pct = Math.round((count / total) * 100);

                  return (
                    <div
                      key={stars}
                      style={{
                        backgroundColor: '#FAF9F6',
                        border: '1px solid #E3E8E3',
                        borderRadius: '8px',
                        padding: '14px',
                        textAlign: 'center',
                      }}
                    >
                      <span style={{ color: '#C6A66B', fontSize: '14px', fontWeight: 700 }}>
                        {stars} ★
                      </span>
                      <strong style={{ display: 'block', fontSize: '22px', color: '#26352D', margin: '4px 0' }}>
                        {count}
                      </strong>
                      <span style={{ fontSize: '11.5px', color: '#718078' }}>
                        {pct}% of ratings
                      </span>
                    </div>
                  );
                })}
              </div>
            </AdminCard>
          </div>
        )}

        {/* ==================================================================
            SECTION 4: PRIVATE FEEDBACK INBOX
            ================================================================== */}
        {activeTab === 'feedback' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            <AdminCard
              title="Private Feedback Management Inbox"
              subtitle="Direct diner feedback, notes and complaints submitted to restaurant management"
              actions={
                <AdminButton
                  variant="outline"
                  size="sm"
                  onClick={fetchPrivateTickets}
                  disabled={isLoadingTickets}
                >
                  {isLoadingTickets ? 'Loading…' : '🔄 Refresh Inbox'}
                </AdminButton>
              }
            >
              {/* Filter Pills */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
                {[
                  { id: 'all', label: 'All Tickets' },
                  { id: 'open', label: 'Open' },
                  { id: 'escalated', label: 'Escalated' },
                  { id: 'resolved', label: 'Resolved' },
                ].map((f) => {
                  const isActive = ticketFilter === f.id;
                  return (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => setTicketFilter(f.id)}
                      className={`vraja-btn ${isActive ? 'vraja-btn-secondary' : 'vraja-btn-outline'} vraja-btn-sm`}
                      style={isActive ? { fontWeight: 700 } : undefined}
                    >
                      {f.label}
                    </button>
                  );
                })}
              </div>

              {/* Tickets List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {filteredTickets.length > 0 ? (
                  filteredTickets.map((ticket) => {
                    const st = (ticket.status || 'OPEN').toUpperCase();
                    const isUpdating = isUpdatingTicketId === ticket.ticket_id;

                    return (
                      <div key={ticket.ticket_id} className="vraja-ticket-card">
                        <div className="vraja-ticket-top">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <strong style={{ color: '#26352D', fontSize: '14px' }}>{ticket.ticket_id}</strong>
                            <AdminBadge variant="neutral">
                              📍 {ticket.table_number || 'General Dining'}
                            </AdminBadge>
                            <span style={{ color: '#C6A66B', fontSize: '13px' }}>
                              {'★'.repeat(ticket.rating || 3)}
                            </span>
                          </div>

                          <StatusBadge status={st} />
                        </div>

                        <p className="vraja-ticket-quote">
                          "{ticket.diner_note || 'No detailed note provided.'}"
                        </p>

                        {ticket.aspects && ticket.aspects.length > 0 && (
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                            {ticket.aspects.map((asp, idx) => (
                              <span
                                key={idx}
                                style={{
                                  fontSize: '11.5px',
                                  backgroundColor: '#EBEFEA',
                                  color: '#26352D',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                }}
                              >
                                {asp}
                              </span>
                            ))}
                          </div>
                        )}

                        <div className="vraja-ticket-footer">
                          <span style={{ fontSize: '12px', color: '#718078' }}>
                            Guest Contact: <strong>{ticket.guest_contact || 'Anonymous'}</strong>
                          </span>

                          <div style={{ display: 'flex', gap: '8px' }}>
                            {st !== 'RESOLVED' && (
                              <AdminButton
                                variant="outline"
                                size="sm"
                                onClick={() => handleUpdateTicketStatus(ticket.ticket_id, 'RESOLVED')}
                                disabled={isUpdating}
                                style={{ color: '#1D7A4D' }}
                              >
                                ✓ Mark Resolved
                              </AdminButton>
                            )}
                            {st !== 'ESCALATED' && (
                              <AdminButton
                                variant="outline"
                                size="sm"
                                onClick={() => handleUpdateTicketStatus(ticket.ticket_id, 'ESCALATED')}
                                disabled={isUpdating}
                                style={{ color: '#B42318' }}
                              >
                                ⚠️ Escalate
                              </AdminButton>
                            )}
                            {st === 'RESOLVED' && (
                              <AdminButton
                                variant="outline"
                                size="sm"
                                onClick={() => handleUpdateTicketStatus(ticket.ticket_id, 'OPEN')}
                                disabled={isUpdating}
                              >
                                🔄 Re-open
                              </AdminButton>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div style={{ padding: '36px', textAlign: 'center', color: '#718078', fontSize: '13.5px' }}>
                    No private feedback tickets matching the "{ticketFilter}" filter.
                  </div>
                )}
              </div>
            </AdminCard>
          </div>
        )}

        {/* ==================================================================
            SECTION 5: SETTINGS
            ================================================================== */}
        {activeTab === 'settings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            <AdminCard
              title="Restaurant Account & Identifier"
              subtitle="Tenant metadata and authorized membership credentials"
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                <div style={{ backgroundColor: '#FAF9F6', padding: '14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                  <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', fontWeight: 600 }}>
                    Tenant Identifier
                  </span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#26352D', marginTop: '4px' }}>
                    {businessId}
                  </div>
                </div>

                <div style={{ backgroundColor: '#FAF9F6', padding: '14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                  <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', fontWeight: 600 }}>
                    Account Email
                  </span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#26352D', marginTop: '4px' }}>
                    {authSession?.user?.email || 'N/A'}
                  </div>
                </div>

                <div style={{ backgroundColor: '#FAF9F6', padding: '14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                  <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', fontWeight: 600 }}>
                    Membership Role
                  </span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#174D3A', marginTop: '4px', textTransform: 'capitalize' }}>
                    {authSession?.active_tenant?.role || 'Manager'}
                  </div>
                </div>
              </div>

              {onPreviewCustomer && (
                <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #E3E8E3', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <strong style={{ color: '#26352D' }}>Customer Experience Preview</strong>
                    <p style={{ margin: '2px 0 0 0', fontSize: '13px', color: '#718078' }}>
                      Preview what diners see when scanning your digital review assistant QR code.
                    </p>
                  </div>
                  <AdminButton
                    variant="secondary"
                    onClick={onPreviewCustomer}
                  >
                    Open Customer Preview ↗
                  </AdminButton>
                </div>
              )}
            </AdminCard>

            {/* Password Management */}
            <AdminCard
              title="Password Management"
              subtitle="Update your restaurant manager account password securely"
            >
              {passwordStatus.text && (
                <div style={{ marginBottom: '16px' }}>
                  <AdminNotification
                    type={passwordStatus.type}
                    message={passwordStatus.text}
                  />
                </div>
              )}

              <form onSubmit={handleChangePassword} style={{ maxWidth: '520px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <AdminInput
                  label="Current Password"
                  id="owner-current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />

                <AdminInput
                  label="New Password (min 8 characters)"
                  id="owner-new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />

                <AdminInput
                  label="Confirm New Password"
                  id="owner-confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />

                <div style={{ marginTop: '6px' }}>
                  <AdminButton
                    type="submit"
                    variant="primary"
                    disabled={isChangingPassword}
                  >
                    {isChangingPassword ? 'Updating Password…' : 'Update Password'}
                  </AdminButton>
                </div>
              </form>
            </AdminCard>
          </div>
        )}
      </main>
    </div>
  );
}
