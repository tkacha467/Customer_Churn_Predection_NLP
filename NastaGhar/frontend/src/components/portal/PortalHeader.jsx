import { usePortalSession } from './PortalSessionContext';

const TAB_TITLES = {
  overview: 'Dashboard Overview',
  profile: 'Shared Business Profile & Logo',
  'reviews-setup': 'Review Setup & Keyword Aspects',
  'reviews-analytics': 'Review Activity & Authentic Analytics',
  'reviews-inbox': 'Private Feedback Management Inbox',
  'card-editor': 'Digital Business Card Studio',
  'card-links': 'Documents & Custom Action Links',
  'card-publish': 'Card Visibility & QR Publication',
  settings: 'Account Settings & Credentials',
};

export function PortalHeader({
  activeTab = 'overview',
  onOpenMobileNav,
  onPreviewReview,
  onPreviewCard,
}) {
  const {
    activeTenant,
    sharedProfile,
    hasEntitlement,
  } = usePortalSession();

  const businessName = sharedProfile?.display_name || activeTenant?.business_name || 'Business Portal';
  const branchName = sharedProfile?.branch_name || '';
  const userRole = (activeTenant?.role || 'owner').toUpperCase();
  const currentTitle = TAB_TITLES[activeTab] || 'Client Portal';

  return (
    <header className="vraja-portal-header">
      <div className="vraja-header-left-col">
        {/* Mobile menu trigger */}
        <button
          type="button"
          className="vraja-mobile-nav-toggle"
          onClick={onOpenMobileNav}
          aria-label="Open portal navigation"
        >
          <span className="hamburger-bar" />
          <span className="hamburger-bar" />
          <span className="hamburger-bar" />
        </button>

        {/* Dynamic Breadcrumbs */}
        <nav className="vraja-portal-breadcrumbs" aria-label="Breadcrumb">
          <span className="breadcrumb-root">VRAJA AI</span>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-tenant">
            {businessName}
            {branchName && <span className="breadcrumb-branch">({branchName})</span>}
          </span>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">{currentTitle}</span>
        </nav>
      </div>

      <div className="vraja-header-right-col">
        {/* Role Badge */}
        <div className={`vraja-header-role-pill role-${userRole.toLowerCase()}`}>
          <span className="role-dot" />
          <span className="role-text">{userRole}</span>
        </div>

        {/* Quick Preview Actions (Rendered strictly for entitled products) */}
        <div className="vraja-header-quick-actions">
          {hasEntitlement('review_manager') && (
            <button
              type="button"
              className="vraja-header-preview-btn btn-review"
              onClick={onPreviewReview}
              title="Launch Public Review Experience"
            >
              <span className="btn-icon">👁️</span>
              <span className="btn-label">Preview Review Flow</span>
            </button>
          )}

          {hasEntitlement('digital_card') && (
            <button
              type="button"
              className="vraja-header-preview-btn btn-card"
              onClick={onPreviewCard}
              title="Launch Public Digital Business Card"
            >
              <span className="btn-icon">🪪</span>
              <span className="btn-label">Preview Digital Card</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default PortalHeader;
