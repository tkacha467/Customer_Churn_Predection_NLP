import { useState, useEffect, useCallback, useMemo } from 'react';
import { apiFetch } from '../lib/api';

const PACKAGE_OPTIONS = [
  { id: 'both', label: 'Full Suite (Reviews + Digital Card)', entitlements: ['review_manager', 'digital_card'], icon: '🌟' },
  { id: 'review', label: 'Review System Only', entitlements: ['review_manager'], icon: '⭐' },
  { id: 'card', label: 'Digital Business Card Only', entitlements: ['digital_card'], icon: '🪪' },
];

export default function VrajaAdmin({ onNavigateToOwner, onNavigateToCard, onNavigateToReview }) {
  // Session & Auth state
  const [authSession, setAuthSession] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Tenant list state
  const [tenants, setTenants] = useState([]);
  const [isLoadingTenants, setIsLoadingTenants] = useState(false);
  const [tenantError, setTenantError] = useState('');

  // Filtering & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // all, active, suspended
  const [packageFilter, setPackageFilter] = useState('all'); // all, both, review, card

  // Action states (status/entitlement update)
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [actionMessage, setActionMessage] = useState({ type: '', text: '' });

  // Detail Modal / Drawer
  const [selectedTenant, setSelectedTenant] = useState(null);

  // Onboarding Modal state
  const [showOnboardModal, setShowOnboardModal] = useState(false);
  const [onboardForm, setOnboardForm] = useState({
    tenant_id: '',
    business_name: '',
    owner_email: '',
    owner_password: '',
    owner_name: '',
    package_type: 'both',
    category: 'Cafe',
    review_url: '',
    branch: '',
  });
  const [isOnboarding, setIsOnboarding] = useState(false);
  const [onboardError, setOnboardError] = useState('');
  const [onboardSuccess, setOnboardSuccess] = useState(null);

  // Check auth session
  const verifySession = useCallback(async () => {
    setIsCheckingSession(true);
    try {
      const res = await apiFetch('/api/auth/session');
      if (res.ok) {
        const data = await res.json();
        setAuthSession(data);
      } else {
        setAuthSession(null);
      }
    } catch {
      setAuthSession(null);
    } finally {
      setIsCheckingSession(false);
    }
  }, []);

  useEffect(() => {
    verifySession();
  }, [verifySession]);

  // Load tenants when authenticated as platform admin
  const fetchTenants = useCallback(async () => {
    if (!authSession?.user?.is_platform_admin) return;
    setIsLoadingTenants(true);
    setTenantError('');
    try {
      const res = await apiFetch('/api/platform/tenants');
      if (res.ok) {
        const data = await res.json();
        setTenants(Array.isArray(data) ? data : []);
      } else {
        const err = await res.json().catch(() => ({}));
        setTenantError(err.detail || 'Failed to load tenants list.');
      }
    } catch {
      setTenantError('Network error while loading tenants list.');
    } finally {
      setIsLoadingTenants(false);
    }
  }, [authSession]);

  useEffect(() => {
    if (authSession?.user?.is_platform_admin) {
      fetchTenants();
    }
  }, [authSession, fetchTenants]);

  // Handle Admin Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setIsLoggingIn(true);
    try {
      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setAuthSession(data);
        setLoginEmail('');
        setLoginPassword('');
      } else {
        setLoginError(data.detail || 'Login failed. Please check your credentials.');
      }
    } catch {
      setLoginError('Unable to connect to authentication service.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Handle Admin Logout
  const handleLogout = async () => {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' });
    } catch {
      // ignore
    }
    setAuthSession(null);
    setTenants([]);
  };

  // Handle Status Toggle (active <-> suspended)
  const handleToggleStatus = async (tenant) => {
    const nextStatus = tenant.status === 'active' ? 'suspended' : 'active';
    setActionLoadingId(tenant.id);
    setActionMessage({ type: '', text: '' });
    try {
      const res = await apiFetch(`/api/platform/tenants/${encodeURIComponent(tenant.id)}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (res.ok) {
        setTenants((prev) =>
          prev.map((t) => (t.id === tenant.id ? { ...t, status: nextStatus } : t))
        );
        if (selectedTenant?.id === tenant.id) {
          setSelectedTenant((prev) => ({ ...prev, status: nextStatus }));
        }
        setActionMessage({
          type: 'success',
          text: `Tenant '${tenant.id}' status changed to ${nextStatus.toUpperCase()}. Immediate effect applied.`,
        });
      } else {
        const err = await res.json().catch(() => ({}));
        setActionMessage({ type: 'error', text: err.detail || 'Failed to update tenant status.' });
      }
    } catch {
      setActionMessage({ type: 'error', text: 'Network error updating tenant status.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  // Handle Entitlement Package Update
  const handleUpdateEntitlements = async (tenant, targetEntitlements) => {
    setActionLoadingId(tenant.id);
    setActionMessage({ type: '', text: '' });
    try {
      const res = await apiFetch(`/api/platform/tenants/${encodeURIComponent(tenant.id)}/entitlements`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entitlements: targetEntitlements }),
      });
      if (res.ok) {
        const updated = await res.json();
        setTenants((prev) =>
          prev.map((t) => (t.id === tenant.id ? { ...t, entitlements: updated.entitlements } : t))
        );
        if (selectedTenant?.id === tenant.id) {
          setSelectedTenant((prev) => ({ ...prev, entitlements: updated.entitlements }));
        }
        setActionMessage({
          type: 'success',
          text: `Updated entitlements for '${tenant.id}'. Active features: [${targetEntitlements.join(', ')}].`,
        });
      } else {
        const err = await res.json().catch(() => ({}));
        setActionMessage({ type: 'error', text: err.detail || 'Failed to update entitlements.' });
      }
    } catch {
      setActionMessage({ type: 'error', text: 'Network error updating entitlements.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  // Fetch Tenant Admin Details
  const handleViewTenantDetails = async (tenantId) => {
    setActionMessage({ type: '', text: '' });
    try {
      const res = await apiFetch(`/api/platform/tenants/${encodeURIComponent(tenantId)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedTenant(data);
      } else {
        const err = await res.json().catch(() => ({}));
        setActionMessage({ type: 'error', text: err.detail || 'Failed to load tenant details.' });
      }
    } catch {
      setActionMessage({ type: 'error', text: 'Network error loading tenant details.' });
    }
  };

  // Handle Onboarding New Tenant
  const handleOnboardSubmit = async (e) => {
    e.preventDefault();
    setOnboardError('');
    setOnboardSuccess(null);
    setIsOnboarding(true);

    const chosenPkg = PACKAGE_OPTIONS.find((p) => p.id === onboardForm.package_type);
    const entitlements = chosenPkg ? chosenPkg.entitlements : ['review_manager', 'digital_card'];

    const payload = {
      tenant_id: onboardForm.tenant_id.trim().toLowerCase(),
      business_name: onboardForm.business_name.trim(),
      owner_email: onboardForm.owner_email.trim().toLowerCase(),
      owner_password: onboardForm.owner_password,
      owner_name: onboardForm.owner_name.trim() || undefined,
      category: onboardForm.category.trim() || 'Cafe',
      review_url: onboardForm.review_url.trim() || undefined,
      branch: onboardForm.branch.trim() || undefined,
      entitlements,
      status: 'active',
    };

    try {
      const res = await apiFetch('/api/platform/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setOnboardSuccess(data);
        fetchTenants();
        // Reset form
        setOnboardForm({
          tenant_id: '',
          business_name: '',
          owner_email: '',
          owner_password: '',
          owner_name: '',
          package_type: 'both',
          category: 'Cafe',
          review_url: '',
          branch: '',
        });
      } else {
        setOnboardError(data.detail || 'Tenant onboarding failed.');
      }
    } catch {
      setOnboardError('Network error during tenant onboarding.');
    } finally {
      setIsOnboarding(false);
    }
  };

  // Helper to categorize tenant package
  const getPackageKey = (ents) => {
    const list = Array.isArray(ents) ? ents : [];
    const hasRev = list.includes('review_manager');
    const hasCard = list.includes('digital_card');
    if (hasRev && hasCard) return 'both';
    if (hasRev) return 'review';
    if (hasCard) return 'card';
    return 'none';
  };

  // Filtered tenants calculation
  const filteredTenants = useMemo(() => {
    return tenants.filter((t) => {
      // Search match
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        t.id?.toLowerCase().includes(q) ||
        t.business_name?.toLowerCase().includes(q) ||
        t.owner_email?.toLowerCase().includes(q);

      // Status match
      const matchStatus =
        statusFilter === 'all' || t.status === statusFilter;

      // Package match
      const pkgKey = getPackageKey(t.entitlements);
      const matchPackage =
        packageFilter === 'all' || pkgKey === packageFilter;

      return matchSearch && matchStatus && matchPackage;
    });
  }, [tenants, searchQuery, statusFilter, packageFilter]);

  // Overall metrics calculation
  const metrics = useMemo(() => {
    let active = 0;
    let suspended = 0;
    let both = 0;
    let reviewOnly = 0;
    let cardOnly = 0;

    tenants.forEach((t) => {
      if (t.status === 'active') active += 1;
      if (t.status === 'suspended') suspended += 1;
      const pkg = getPackageKey(t.entitlements);
      if (pkg === 'both') both += 1;
      else if (pkg === 'review') reviewOnly += 1;
      else if (pkg === 'card') cardOnly += 1;
    });

    return {
      total: tenants.length,
      active,
      suspended,
      both,
      reviewOnly,
      cardOnly,
    };
  }, [tenants]);

  // ─── LOADING SCREEN ────────────────────────────────────────────────────────
  if (isCheckingSession) {
    return (
      <div className="admin-loading-container" role="status">
        <div className="admin-spinner" />
        <p>Verifying platform administrative credentials…</p>
      </div>
    );
  }

  // ─── UNAUTHENTICATED SCREEN (ADMIN LOGIN) ───────────────────────────────────
  if (!authSession?.authenticated) {
    return (
      <div className="admin-login-layout">
        <div className="admin-login-card">
          <div className="admin-login-header">
            <span className="admin-shield-icon">🛡️</span>
            <h1>Vraja Platform Admin</h1>
            <p className="admin-login-subtitle">Internal platform management and tenant provisioning</p>
          </div>

          {loginError && (
            <div className="admin-alert admin-alert-danger" role="alert">
              ⚠️ {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} className="admin-login-form">
            <label className="admin-form-group">
              <span className="admin-label-text">Platform Admin Email</span>
              <input
                type="email"
                required
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                placeholder="admin@platform.vraja"
                className="admin-input"
                autoComplete="email"
              />
            </label>

            <label className="admin-form-group">
              <span className="admin-label-text">Password</span>
              <input
                type="password"
                required
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="••••••••••••"
                className="admin-input"
                autoComplete="current-password"
              />
            </label>

            <button
              type="submit"
              disabled={isLoggingIn}
              className="admin-btn admin-btn-primary"
            >
              {isLoggingIn ? 'Authenticating…' : 'Sign In as Platform Admin'}
            </button>
          </form>

          <div className="admin-login-footer">
            <span>🔒 Restrictive platform access only. Unauthorized attempts are logged.</span>
          </div>
        </div>
      </div>
    );
  }

  // ─── 403 FORBIDDEN: AUTHENTICATED BUT NOT A PLATFORM ADMIN ─────────────────
  if (!authSession.user?.is_platform_admin) {
    return (
      <div className="admin-login-layout">
        <div className="admin-login-card admin-forbidden-card">
          <div className="admin-login-header">
            <span className="admin-shield-icon">🚫</span>
            <h1>Access Restricted</h1>
            <p className="admin-login-subtitle">
              Account <strong>{authSession.user.email}</strong> is not authorized for platform administration.
            </p>
          </div>
          <div className="admin-alert admin-alert-warning">
            This console is reserved strictly for authorized Vraja platform operators. Tenant owners and staff cannot access internal administration tools.
          </div>
          <div className="admin-btn-row">
            <button
              type="button"
              className="admin-btn admin-btn-secondary"
              onClick={() => {
                if (onNavigateToOwner) onNavigateToOwner(authSession.active_tenant_id || 'default_business');
              }}
            >
              Go to Business Owner Portal
            </button>
            <button
              type="button"
              className="admin-btn admin-btn-outline"
              onClick={handleLogout}
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─── AUTHORIZED PLATFORM ADMIN INTERFACE ───────────────────────────────────
  return (
    <div className="admin-root">
      {/* Top Navigation Bar */}
      <header className="admin-topbar">
        <div className="admin-brand">
          <span className="admin-brand-icon">🛡️</span>
          <div>
            <h1 className="admin-brand-title">Vraja Platform Admin</h1>
            <span className="admin-brand-env">Management Console • Local Staging</span>
          </div>
        </div>

        <div className="admin-user-pill">
          <span className="admin-user-email">👤 {authSession.user.email}</span>
          <span className="admin-badge admin-badge-admin">Superadmin</span>
          <button
            type="button"
            className="admin-btn-logout"
            onClick={handleLogout}
            title="Sign out of platform admin"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="admin-main">
        {/* Action / Notification Banner */}
        {actionMessage.text && (
          <div className={`admin-notification admin-notification-${actionMessage.type}`} role="status">
            <span>{actionMessage.type === 'success' ? '✅' : '⚠️'} {actionMessage.text}</span>
            <button
              type="button"
              className="admin-notification-close"
              onClick={() => setActionMessage({ type: '', text: '' })}
            >
              ×
            </button>
          </div>
        )}

        {/* Overview KPI Metrics */}
        <section className="admin-metrics-grid" aria-label="Platform Overview">
          <div className="admin-metric-card">
            <span className="metric-label">Total Tenants</span>
            <span className="metric-value">{metrics.total}</span>
            <span className="metric-sub">Across all packages</span>
          </div>
          <div className="admin-metric-card metric-card-active">
            <span className="metric-label">Active Tenants</span>
            <span className="metric-value">{metrics.active}</span>
            <span className="metric-sub">Operational & accessible</span>
          </div>
          <div className="admin-metric-card metric-card-suspended">
            <span className="metric-label">Suspended</span>
            <span className="metric-value">{metrics.suspended}</span>
            <span className="metric-sub">Blocked from dashboard & public</span>
          </div>
          <div className="admin-metric-card metric-card-both">
            <span className="metric-label">🌟 Full Suite</span>
            <span className="metric-value">{metrics.both}</span>
            <span className="metric-sub">Reviews + Digital Card</span>
          </div>
          <div className="admin-metric-card metric-card-review">
            <span className="metric-label">⭐ Review Only</span>
            <span className="metric-value">{metrics.reviewOnly}</span>
            <span className="metric-sub">Reviews & private feedback</span>
          </div>
          <div className="admin-metric-card metric-card-card">
            <span className="metric-label">🪪 Card Only</span>
            <span className="metric-value">{metrics.cardOnly}</span>
            <span className="metric-sub">Digital Business Card</span>
          </div>
        </section>

        {/* Tenant Management Header & Controls */}
        <div className="admin-table-header-row">
          <div className="admin-search-filter-group">
            <div className="admin-search-box">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="Search by tenant ID, business name, or owner email…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="admin-search-input"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear-btn"
                  onClick={() => setSearchQuery('')}
                >
                  ×
                </button>
              )}
            </div>

            {/* Filter by Status */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="admin-select-filter"
              aria-label="Filter by Status"
            >
              <option value="all">All Statuses ({metrics.total})</option>
              <option value="active">Active Only ({metrics.active})</option>
              <option value="suspended">Suspended Only ({metrics.suspended})</option>
            </select>

            {/* Filter by Package */}
            <select
              value={packageFilter}
              onChange={(e) => setPackageFilter(e.target.value)}
              className="admin-select-filter"
              aria-label="Filter by Package"
            >
              <option value="all">All Packages</option>
              <option value="both">Full Suite (Reviews + Card)</option>
              <option value="review">Review System Only</option>
              <option value="card">Digital Card Only</option>
            </select>
          </div>

          <div className="admin-top-actions">
            <button
              type="button"
              className="admin-btn admin-btn-refresh"
              onClick={fetchTenants}
              disabled={isLoadingTenants}
              title="Refresh tenant list"
            >
              🔄 {isLoadingTenants ? 'Refreshing…' : 'Refresh'}
            </button>
            <button
              type="button"
              className="admin-btn admin-btn-primary"
              onClick={() => {
                setShowOnboardModal(true);
                setOnboardError('');
                setOnboardSuccess(null);
              }}
            >
              ➕ Onboard New Tenant
            </button>
          </div>
        </div>

        {/* Tenants Table */}
        {tenantError && (
          <div className="admin-alert admin-alert-danger" role="alert">
            ⚠️ {tenantError}
          </div>
        )}

        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Tenant ID & Name</th>
                <th>Owner Account</th>
                <th>Status</th>
                <th>Assigned Package</th>
                <th>Package Actions</th>
                <th>Quick Links & Tools</th>
              </tr>
            </thead>
            <tbody>
              {isLoadingTenants && tenants.length === 0 ? (
                <tr>
                  <td colSpan="6" className="admin-table-empty">
                    <div className="admin-spinner" />
                    <span>Loading tenants…</span>
                  </td>
                </tr>
              ) : filteredTenants.length === 0 ? (
                <tr>
                  <td colSpan="6" className="admin-table-empty">
                    <span>No tenants match your current search and filter criteria.</span>
                  </td>
                </tr>
              ) : (
                filteredTenants.map((t) => {
                  const pkgKey = getPackageKey(t.entitlements);
                  const isSuspended = t.status === 'suspended';
                  const isActionLoading = actionLoadingId === t.id;

                  return (
                    <tr key={t.id} className={isSuspended ? 'tenant-row-suspended' : ''}>
                      {/* Tenant Identity */}
                      <td className="tenant-id-col">
                        <div className="tenant-name-row">
                          <strong className="tenant-business-name">{t.business_name}</strong>
                          {t.category && <span className="tenant-category-tag">{t.category}</span>}
                        </div>
                        <div className="tenant-id-sub">
                          <code>{t.id}</code>
                          {t.branch && <span className="tenant-branch"> • {t.branch}</span>}
                        </div>
                      </td>

                      {/* Owner Account */}
                      <td className="tenant-owner-col">
                        <div className="owner-email">{t.owner_email || '—'}</div>
                        {t.owner_name && <div className="owner-name-sub">{t.owner_name}</div>}
                      </td>

                      {/* Status & Toggle */}
                      <td className="tenant-status-col">
                        <div className="status-badge-row">
                          <span className={`status-pill status-${t.status}`}>
                            {t.status === 'active' ? '● Active' : '■ Suspended'}
                          </span>
                        </div>
                        <button
                          type="button"
                          className={`btn-status-toggle ${isSuspended ? 'btn-status-reactivate' : 'btn-status-suspend'}`}
                          disabled={isActionLoading}
                          onClick={() => handleToggleStatus(t)}
                          title={isSuspended ? 'Reactivate tenant' : 'Suspend tenant'}
                        >
                          {isActionLoading ? 'Updating…' : isSuspended ? 'Reactivate' : 'Suspend'}
                        </button>
                      </td>

                      {/* Assigned Package Badge */}
                      <td className="tenant-pkg-col">
                        {pkgKey === 'both' && (
                          <span className="pkg-badge pkg-badge-both">
                            🌟 Full Suite
                            <small>Reviews + Card</small>
                          </span>
                        )}
                        {pkgKey === 'review' && (
                          <span className="pkg-badge pkg-badge-review">
                            ⭐ Review System
                            <small>Reviews Only</small>
                          </span>
                        )}
                        {pkgKey === 'card' && (
                          <span className="pkg-badge pkg-badge-card">
                            🪪 Digital Card
                            <small>Card Only</small>
                          </span>
                        )}
                        {pkgKey === 'none' && (
                          <span className="pkg-badge pkg-badge-none">
                            ⚠️ No Entitlements
                          </span>
                        )}
                      </td>

                      {/* Package Actions / Switcher */}
                      <td className="tenant-pkg-actions-col">
                        <div className="pkg-quick-buttons">
                          <button
                            type="button"
                            className={`pkg-btn ${pkgKey === 'both' ? 'pkg-btn-active' : ''}`}
                            disabled={isActionLoading || pkgKey === 'both'}
                            onClick={() => handleUpdateEntitlements(t, ['review_manager', 'digital_card'])}
                            title="Assign Full Suite (Reviews + Digital Card)"
                          >
                            🌟 Both
                          </button>
                          <button
                            type="button"
                            className={`pkg-btn ${pkgKey === 'review' ? 'pkg-btn-active' : ''}`}
                            disabled={isActionLoading || pkgKey === 'review'}
                            onClick={() => handleUpdateEntitlements(t, ['review_manager'])}
                            title="Assign Review System Only"
                          >
                            ⭐ Reviews
                          </button>
                          <button
                            type="button"
                            className={`pkg-btn ${pkgKey === 'card' ? 'pkg-btn-active' : ''}`}
                            disabled={isActionLoading || pkgKey === 'card'}
                            onClick={() => handleUpdateEntitlements(t, ['digital_card'])}
                            title="Assign Digital Card Only"
                          >
                            🪪 Card
                          </button>
                        </div>
                      </td>

                      {/* Quick Links & Details */}
                      <td className="tenant-tools-col">
                        <div className="tenant-tools-row">
                          <button
                            type="button"
                            className="tool-btn"
                            onClick={() => handleViewTenantDetails(t.id)}
                            title="Inspect details and profile configuration"
                          >
                            🔍 Details
                          </button>
                          {t.entitlements?.includes('review_manager') && (
                            <button
                              type="button"
                              className="tool-btn tool-btn-launch"
                              onClick={() => onNavigateToReview && onNavigateToReview(t.id)}
                              title="Open public review page"
                            >
                              ⭐ Reviews
                            </button>
                          )}
                          {t.entitlements?.includes('digital_card') && (
                            <button
                              type="button"
                              className="tool-btn tool-btn-launch"
                              onClick={() => onNavigateToCard && onNavigateToCard(t.id)}
                              title="Open public digital business card"
                            >
                              🪪 Card
                            </button>
                          )}
                          <button
                            type="button"
                            className="tool-btn tool-btn-owner"
                            onClick={() => onNavigateToOwner && onNavigateToOwner(t.id)}
                            title="Open Business Owner Portal"
                          >
                            💼 Portal
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </main>

      {/* ─── ONBOARDING MODAL ──────────────────────────────────────────────── */}
      {showOnboardModal && (
        <div className="admin-modal-backdrop" onClick={() => !isOnboarding && setShowOnboardModal(false)}>
          <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <div>
                <h2>Onboard New Tenant</h2>
                <p className="admin-modal-sub">Create a new customer tenant and assign their product package</p>
              </div>
              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setShowOnboardModal(false)}
                disabled={isOnboarding}
              >
                ×
              </button>
            </div>

            {onboardSuccess ? (
              <div className="onboard-success-box">
                <div className="success-icon">🎉</div>
                <h3>Tenant Created Successfully!</h3>
                <p>
                  Tenant <code>{onboardSuccess.tenant_id}</code> (
                  <strong>{onboardSuccess.business_name}</strong>) has been provisioned.
                </p>
                <div className="onboard-details-summary">
                  <div><strong>Owner Email:</strong> {onboardSuccess.owner_email}</div>
                  <div><strong>Status:</strong> {onboardSuccess.status}</div>
                  <div><strong>Entitlements:</strong> {onboardSuccess.entitlements?.join(', ')}</div>
                </div>
                <div className="admin-btn-row">
                  <button
                    type="button"
                    className="admin-btn admin-btn-primary"
                    onClick={() => {
                      setShowOnboardModal(false);
                      if (onNavigateToOwner) onNavigateToOwner(onboardSuccess.tenant_id);
                    }}
                  >
                    Open Owner Portal
                  </button>
                  <button
                    type="button"
                    className="admin-btn admin-btn-secondary"
                    onClick={() => {
                      setOnboardSuccess(null);
                    }}
                  >
                    Onboard Another Tenant
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleOnboardSubmit} className="onboard-form">
                {onboardError && (
                  <div className="admin-alert admin-alert-danger" role="alert">
                    ⚠️ {onboardError}
                  </div>
                )}

                <div className="form-grid-2">
                  <label className="admin-form-group">
                    <span className="admin-label-text">Tenant Identifier (Slug) *</span>
                    <input
                      type="text"
                      required
                      pattern="^[a-zA-Z0-9_\-]+$"
                      title="Letters, numbers, underscores, and hyphens only"
                      placeholder="e.g. cafe-de-paris"
                      value={onboardForm.tenant_id}
                      onChange={(e) =>
                        setOnboardForm({ ...onboardForm, tenant_id: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '') })
                      }
                      className="admin-input"
                    />
                    <small className="admin-hint">Unique identifier used in URLs (/b/slug/card)</small>
                  </label>

                  <label className="admin-form-group">
                    <span className="admin-label-text">Business Name *</span>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Cafe De Paris"
                      value={onboardForm.business_name}
                      onChange={(e) => setOnboardForm({ ...onboardForm, business_name: e.target.value })}
                      className="admin-input"
                    />
                  </label>
                </div>

                <div className="form-grid-2">
                  <label className="admin-form-group">
                    <span className="admin-label-text">Owner Email *</span>
                    <input
                      type="email"
                      required
                      placeholder="owner@cafedeparis.com"
                      value={onboardForm.owner_email}
                      onChange={(e) => setOnboardForm({ ...onboardForm, owner_email: e.target.value })}
                      className="admin-input"
                    />
                  </label>

                  <label className="admin-form-group">
                    <span className="admin-label-text">Owner Password * (min 10 chars)</span>
                    <input
                      type="password"
                      required
                      minLength={10}
                      placeholder="Minimum 10 characters"
                      value={onboardForm.owner_password}
                      onChange={(e) => setOnboardForm({ ...onboardForm, owner_password: e.target.value })}
                      className="admin-input"
                    />
                  </label>
                </div>

                {/* Product Packaging Selector */}
                <div className="admin-form-group">
                  <span className="admin-label-text">Assigned Product Package *</span>
                  <div className="package-selector-grid">
                    {PACKAGE_OPTIONS.map((pkg) => (
                      <label
                        key={pkg.id}
                        className={`pkg-select-option ${onboardForm.package_type === pkg.id ? 'pkg-select-active' : ''}`}
                      >
                        <input
                          type="radio"
                          name="package_type"
                          value={pkg.id}
                          checked={onboardForm.package_type === pkg.id}
                          onChange={(e) => setOnboardForm({ ...onboardForm, package_type: e.target.value })}
                          className="pkg-radio"
                        />
                        <div className="pkg-option-content">
                          <span className="pkg-opt-icon">{pkg.icon}</span>
                          <strong>{pkg.label}</strong>
                          <span className="pkg-opt-desc">
                            Modules: {pkg.entitlements.join(', ')}
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-grid-2">
                  <label className="admin-form-group">
                    <span className="admin-label-text">Category</span>
                    <input
                      type="text"
                      placeholder="Cafe, Restaurant, Salon, etc."
                      value={onboardForm.category}
                      onChange={(e) => setOnboardForm({ ...onboardForm, category: e.target.value })}
                      className="admin-input"
                    />
                  </label>

                  <label className="admin-form-group">
                    <span className="admin-label-text">Branch / Location (optional)</span>
                    <input
                      type="text"
                      placeholder="Downtown, Westside, etc."
                      value={onboardForm.branch}
                      onChange={(e) => setOnboardForm({ ...onboardForm, branch: e.target.value })}
                      className="admin-input"
                    />
                  </label>
                </div>

                {/* Review Destination URL (Optional if reviews enabled) */}
                {onboardForm.package_type !== 'card' && (
                  <label className="admin-form-group">
                    <span className="admin-label-text">Google Review Destination URL (optional)</span>
                    <input
                      type="url"
                      placeholder="https://g.page/r/..."
                      value={onboardForm.review_url}
                      onChange={(e) => setOnboardForm({ ...onboardForm, review_url: e.target.value })}
                      className="admin-input"
                    />
                    <small className="admin-hint">Where 4-5 star positive diners will be directed</small>
                  </label>
                )}

                <div className="admin-modal-footer">
                  <button
                    type="button"
                    className="admin-btn admin-btn-secondary"
                    onClick={() => setShowOnboardModal(false)}
                    disabled={isOnboarding}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="admin-btn admin-btn-primary"
                    disabled={isOnboarding}
                  >
                    {isOnboarding ? 'Provisioning Tenant…' : 'Provision Customer Tenant'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ─── TENANT DETAILS DRAWER / MODAL ─────────────────────────────────── */}
      {selectedTenant && (
        <div className="admin-modal-backdrop" onClick={() => setSelectedTenant(null)}>
          <div className="admin-modal admin-detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <div>
                <h2>{selectedTenant.business_name}</h2>
                <p className="admin-modal-sub">Tenant Identity: <code>{selectedTenant.id}</code></p>
              </div>
              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setSelectedTenant(null)}
              >
                ×
              </button>
            </div>

            <div className="detail-modal-body">
              <div className="detail-section">
                <h3>Tenant Status & Entitlements</h3>
                <div className="detail-grid">
                  <div><strong>Status:</strong> <span className={`status-pill status-${selectedTenant.status}`}>{selectedTenant.status}</span></div>
                  <div><strong>Package:</strong> {selectedTenant.entitlements?.join(', ')}</div>
                  <div><strong>Category:</strong> {selectedTenant.category || 'None'}</div>
                  <div><strong>Branch:</strong> {selectedTenant.branch || 'None'}</div>
                  <div><strong>Custom Domain:</strong> {selectedTenant.domain || 'None configured'}</div>
                  <div><strong>Uploaded Documents:</strong> {selectedTenant.document_count || 0} PDF(s)</div>
                </div>
              </div>

              <div className="detail-section">
                <h3>Primary Owner</h3>
                <div className="detail-grid">
                  <div><strong>Email:</strong> {selectedTenant.owner_email || 'No owner assigned'}</div>
                  <div><strong>Name:</strong> {selectedTenant.owner_name || '—'}</div>
                  <div><strong>User ID:</strong> <code>{selectedTenant.owner_user_id || '—'}</code></div>
                </div>
              </div>

              {selectedTenant.profile && (
                <div className="detail-section">
                  <h3>Published Profile Card Info</h3>
                  <div className="detail-grid">
                    <div><strong>Tagline:</strong> {selectedTenant.profile.tagline || '—'}</div>
                    <div><strong>Phone:</strong> {selectedTenant.profile.phone || '—'}</div>
                    <div><strong>WhatsApp:</strong> {selectedTenant.profile.whatsapp || '—'}</div>
                    <div><strong>Website:</strong> {selectedTenant.profile.website || '—'}</div>
                    <div><strong>Address:</strong> {selectedTenant.profile.address || '—'}</div>
                    <div><strong>Card Review CTA:</strong> {selectedTenant.profile.enable_review_cta ? 'Enabled' : 'Disabled'}</div>
                  </div>
                </div>
              )}

              <div className="detail-modal-actions">
                <button
                  type="button"
                  className="admin-btn admin-btn-secondary"
                  onClick={() => setSelectedTenant(null)}
                >
                  Close
                </button>
                {selectedTenant.entitlements?.includes('review_manager') && (
                  <button
                    type="button"
                    className="admin-btn admin-btn-outline"
                    onClick={() => {
                      if (onNavigateToReview) onNavigateToReview(selectedTenant.id);
                    }}
                  >
                    ⭐ Review Page
                  </button>
                )}
                {selectedTenant.entitlements?.includes('digital_card') && (
                  <button
                    type="button"
                    className="admin-btn admin-btn-outline"
                    onClick={() => {
                      if (onNavigateToCard) onNavigateToCard(selectedTenant.id);
                    }}
                  >
                    🪪 Digital Card
                  </button>
                )}
                <button
                  type="button"
                  className="admin-btn admin-btn-primary"
                  onClick={() => {
                    if (onNavigateToOwner) onNavigateToOwner(selectedTenant.id);
                  }}
                >
                  💼 Owner Portal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
