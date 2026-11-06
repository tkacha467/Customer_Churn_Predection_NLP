/**
 * Top Application Header Navigation
 */

export function AdminHeader({
  activeTitle = 'Dashboard',
  breadcrumbs = ['VRAJA AI', 'Platform Admin'],
  onOpenMobileMenu,
  adminUser = null,
  notificationCount = 2,
  onOpenNotifications,
  searchValue = '',
  onSearchChange,
  primaryAction = null,
}) {
  return (
    <header className="vraja-admin-header">
      <div className="vraja-header-left">
        {/* Mobile menu trigger */}
        <button
          type="button"
          className="vraja-mobile-menu-btn"
          onClick={onOpenMobileMenu}
          aria-label="Open navigation menu"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
          </svg>
        </button>

        {/* Dynamic Breadcrumbs */}
        <nav className="vraja-breadcrumbs" aria-label="Breadcrumb">
          {breadcrumbs.map((crumb, idx) => (
            <span key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="vraja-breadcrumb-root">{crumb}</span>
              <span className="vraja-breadcrumb-separator">/</span>
            </span>
          ))}
          <span className="vraja-breadcrumb-current">{activeTitle}</span>
        </nav>
      </div>

      <div className="vraja-header-right">
        {/* Global Search Bar */}
        <div className="vraja-header-search-wrap">
          <span className="vraja-header-search-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
          </span>
          <input
            type="search"
            value={searchValue}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            placeholder="Search platform resources..."
            className="vraja-header-search-input"
          />
        </div>

        {/* Notification Bell */}
        <button
          type="button"
          className="vraja-header-action-btn"
          onClick={onOpenNotifications}
          title="Platform Alerts"
          aria-label="View notifications"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
            <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
          </svg>
          {notificationCount > 0 && <span className="vraja-notification-dot" />}
        </button>

        {/* Primary Action Button (Optional) */}
        {primaryAction}

        {/* Administrator Quick Profile */}
        <div className="vraja-header-profile-trigger">
          <div className="vraja-header-avatar">
            {(adminUser?.display_name || adminUser?.email || 'SA')[0].toUpperCase()}
          </div>
          <span className="vraja-header-profile-name">
            {adminUser?.display_name || 'Admin'}
          </span>
        </div>
      </div>
    </header>
  );
}

export default AdminHeader;
