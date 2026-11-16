import { usePortalSession } from './PortalSessionContext';

export function PortalSidebar({
  activeTab = 'overview',
  onSelectTab,
  isOpen = false,
  onClose,
}) {
  const {
    activeTenant,
    availableTenants,
    switchTenant,
    user,
    hasEntitlement,
    logout,
  } = usePortalSession();

  const handleTabClick = (tabId) => {
    onSelectTab(tabId);
    if (onClose) onClose();
  };

  const handleTenantSelect = (e) => {
    const tid = e.target.value;
    if (tid && tid !== activeTenant?.id) {
      switchTenant(tid);
    }
  };

  const userRole = (activeTenant?.role || 'member').toUpperCase();
  const userName = user?.display_name || user?.email?.split('@')[0] || 'Client User';
  const userInitial = (userName[0] || 'U').toUpperCase();

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="vraja-portal-drawer-overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside className={`vraja-portal-sidebar ${isOpen ? 'open' : ''}`}>
        {/* Brand Header */}
        <div className="vraja-sidebar-brand-block">
          <div className="vraja-sidebar-brand-lockup">
            <span className="vraja-sidebar-logo">✨</span>
            <div className="vraja-sidebar-brand-text">
              <span className="vraja-brand-title">VRAJA AI</span>
              <span className="vraja-brand-subtitle">Unified Client Portal</span>
            </div>
          </div>
          {onClose && (
            <button
              type="button"
              className="vraja-sidebar-close-btn"
              onClick={onClose}
              aria-label="Close navigation menu"
            >
              ✕
            </button>
          )}
        </div>

        {/* Tenant Switcher / Identity Badge */}
        <div className="vraja-sidebar-tenant-section">
          {availableTenants && availableTenants.length > 1 ? (
            <div className="vraja-tenant-selector-wrap">
              <label htmlFor="vraja-tenant-picker" className="vraja-tenant-label">
                Active Business
              </label>
              <select
                id="vraja-tenant-picker"
                value={activeTenant?.id || ''}
                onChange={handleTenantSelect}
                className="vraja-tenant-select"
              >
                {availableTenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.business_name} ({t.role})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="vraja-single-tenant-badge">
              <span className="tenant-icon">🏢</span>
              <div className="tenant-info">
                <span className="tenant-name">
                  {activeTenant?.business_name || 'Business Location'}
                </span>
                <span className="tenant-id-pill">ID: {activeTenant?.id || 'default'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Sections */}
        <nav className="vraja-sidebar-nav" aria-label="Portal Navigation">
          {/* Group 1: General Overview & Identity */}
          <div className="vraja-nav-group">
            <span className="vraja-nav-group-title">OVERVIEW</span>
            <ul className="vraja-nav-list">
              <li>
                <button
                  type="button"
                  className={`vraja-nav-item ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => handleTabClick('overview')}
                >
                  <span className="nav-icon">📊</span>
                  <span className="nav-label">Dashboard Overview</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`vraja-nav-item ${activeTab === 'profile' ? 'active' : ''}`}
                  onClick={() => handleTabClick('profile')}
                >
                  <span className="nav-icon">🏢</span>
                  <span className="nav-label">Shared Profile & Logo</span>
                </button>
              </li>
            </ul>
          </div>

          {/* Group 2: Product A — Google Review Manager */}
          {hasEntitlement('review_manager') && (
            <div className="vraja-nav-group">
              <div className="vraja-nav-group-header">
                <span className="vraja-nav-group-title">GOOGLE REVIEW MANAGER</span>
                <span className="nav-product-tag">Product A</span>
              </div>
              <ul className="vraja-nav-list">
                <li>
                  <button
                    type="button"
                    className={`vraja-nav-item ${activeTab === 'reviews-setup' ? 'active' : ''}`}
                    onClick={() => handleTabClick('reviews-setup')}
                  >
                    <span className="nav-icon">⚙️</span>
                    <span className="nav-label">Review Setup</span>
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className={`vraja-nav-item ${activeTab === 'reviews-analytics' ? 'active' : ''}`}
                    onClick={() => handleTabClick('reviews-analytics')}
                  >
                    <span className="nav-icon">📈</span>
                    <span className="nav-label">Activity & Analytics</span>
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className={`vraja-nav-item ${activeTab === 'reviews-inbox' ? 'active' : ''}`}
                    onClick={() => handleTabClick('reviews-inbox')}
                  >
                    <span className="nav-icon">📥</span>
                    <span className="nav-label">Private Feedback Inbox</span>
                  </button>
                </li>
              </ul>
            </div>
          )}

          {/* Group 3: Product B — Digital Business Card */}
          {hasEntitlement('digital_card') && (
            <div className="vraja-nav-group">
              <div className="vraja-nav-group-header">
                <span className="vraja-nav-group-title">DIGITAL BUSINESS CARD</span>
                <span className="nav-product-tag">Product B</span>
              </div>
              <ul className="vraja-nav-list">
                <li>
                  <button
                    type="button"
                    className={`vraja-nav-item ${activeTab === 'card-editor' ? 'active' : ''}`}
                    onClick={() => handleTabClick('card-editor')}
                  >
                    <span className="nav-icon">🪪</span>
                    <span className="nav-label">Card Studio</span>
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className={`vraja-nav-item ${activeTab === 'card-links' ? 'active' : ''}`}
                    onClick={() => handleTabClick('card-links')}
                  >
                    <span className="nav-icon">📁</span>
                    <span className="nav-label">Documents & Links</span>
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className={`vraja-nav-item ${activeTab === 'card-publish' ? 'active' : ''}`}
                    onClick={() => handleTabClick('card-publish')}
                  >
                    <span className="nav-icon">🌐</span>
                    <span className="nav-label">QR & Publication</span>
                  </button>
                </li>
              </ul>
            </div>
          )}

          {/* Group 4: Account & System Settings */}
          <div className="vraja-nav-group">
            <span className="vraja-nav-group-title">ACCOUNT</span>
            <ul className="vraja-nav-list">
              <li>
                <button
                  type="button"
                  className={`vraja-nav-item ${activeTab === 'settings' ? 'active' : ''}`}
                  onClick={() => handleTabClick('settings')}
                >
                  <span className="nav-icon">🔒</span>
                  <span className="nav-label">Settings & Security</span>
                </button>
              </li>
            </ul>
          </div>
        </nav>

        {/* User Card & Sign Out */}
        <div className="vraja-sidebar-footer">
          <div className="vraja-user-card">
            <div className="vraja-user-avatar">{userInitial}</div>
            <div className="vraja-user-details">
              <span className="vraja-user-name" title={userName}>
                {userName}
              </span>
              <span className="vraja-user-role-badge">{userRole}</span>
            </div>
            <button
              type="button"
              className="vraja-logout-btn"
              onClick={logout}
              title="Sign Out"
              aria-label="Sign Out"
            >
              ⎋
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

export default PortalSidebar;
