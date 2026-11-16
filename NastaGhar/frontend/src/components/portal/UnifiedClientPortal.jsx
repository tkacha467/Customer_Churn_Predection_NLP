import { useState, useEffect, useCallback } from 'react';
import { usePortalSession } from './PortalSessionContext';
import PortalSidebar from './PortalSidebar';
import PortalHeader from './PortalHeader';
import SharedBusinessProfileView from './SharedBusinessProfileView';
import './UnifiedPortal.css';

export function UnifiedClientPortal({
  onPreviewReview,
  onPreviewCard,
}) {
  const {
    activeTenant,
    sharedProfile,
    entitlements,
    hasEntitlement,
  } = usePortalSession();

  // Read initial active tab from URL query params
  const getInitialTab = () => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    if (tabParam) return tabParam.toLowerCase();
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [guardNotice, setGuardNotice] = useState('');

  // Synchronize tab changes to URL search params
  const handleSelectTab = useCallback((newTab) => {
    setActiveTab(newTab);
    setGuardNotice('');

    const url = new URL(window.location.href);
    if (newTab === 'overview') {
      url.searchParams.delete('tab');
    } else {
      url.searchParams.set('tab', newTab);
    }
    window.history.pushState({}, '', url.toString());
  }, []);

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      setActiveTab(getInitialTab());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Entitlement route guard: verify caller can view the selected tab
  useEffect(() => {
    const productATabs = ['reviews-setup', 'reviews-analytics', 'reviews-inbox'];
    const productBTabs = ['card-editor', 'card-links', 'card-publish'];

    if (productATabs.includes(activeTab) && !hasEntitlement('review_manager')) {
      setGuardNotice('Google Review Manager is not enabled for this business.');
      handleSelectTab('overview');
    } else if (productBTabs.includes(activeTab) && !hasEntitlement('digital_card')) {
      setGuardNotice('Digital Business Card is not enabled for this business.');
      handleSelectTab('overview');
    }
  }, [activeTab, hasEntitlement, handleSelectTab]);

  const businessName = sharedProfile?.display_name || activeTenant?.business_name || 'Business Portal';
  const branchName = sharedProfile?.branch_name || '';

  const renderContent = () => {
    // 0. Zero Entitlements State
    if (entitlements.length === 0) {
      return (
        <div className="vraja-portal-empty-card">
          <div className="empty-state-emblem">🔒</div>
          <h2 className="empty-state-title">No Active Product Modules</h2>
          <p className="empty-state-desc">
            Your business account <strong>{businessName}</strong> currently has no active product entitlements assigned.
          </p>
          <div className="empty-state-details">
            <div className="detail-item">
              <span className="detail-bullet">•</span>
              <span><strong>Google Review Manager (Product A)</strong> — Boost authentic customer reviews & private feedback.</span>
            </div>
            <div className="detail-item">
              <span className="detail-bullet">•</span>
              <span><strong>Digital Business Card (Product B)</strong> — NFC & QR interactive digital business identity.</span>
            </div>
          </div>
          <p className="empty-state-footer">
            Please contact your VRAJA AI representative or platform administrator to activate your product modules.
          </p>
        </div>
      );
    }

    // 1. Overview Tab
    if (activeTab === 'overview') {
      return (
        <div className="vraja-portal-view-container">
          <div className="vraja-view-header">
            <h1 className="vraja-view-title">Welcome to {businessName}</h1>
            <p className="vraja-view-subtitle">
              Unified command center for your digital customer touchpoints.
              {branchName && <span className="branch-tag">Branch: {branchName}</span>}
            </p>
          </div>

          {/* Module Availability Cards */}
          <div className="vraja-overview-grid">
            {hasEntitlement('review_manager') && (
              <div className="vraja-overview-card product-a">
                <div className="card-top">
                  <span className="card-badge">Product A</span>
                  <span className="card-status active">Active License</span>
                </div>
                <h3 className="card-title">Google Review Manager</h3>
                <p className="card-desc">
                  Proactive diner feedback capture, AI-assisted review drafting, and authentic Google review analytics.
                </p>
                <div className="card-actions">
                  <button
                    type="button"
                    className="card-action-btn"
                    onClick={() => handleSelectTab('reviews-analytics')}
                  >
                    View Analytics →
                  </button>
                  <button
                    type="button"
                    className="card-action-btn secondary"
                    onClick={() => handleSelectTab('reviews-inbox')}
                  >
                    Feedback Inbox →
                  </button>
                </div>
              </div>
            )}

            {hasEntitlement('digital_card') && (
              <div className="vraja-overview-card product-b">
                <div className="card-top">
                  <span className="card-badge">Product B</span>
                  <span className="card-status active">Active License</span>
                </div>
                <h3 className="card-title">Digital Business Card</h3>
                <p className="card-desc">
                  Customizable digital business card, contactless NFC/QR sharing, menu and brochure PDF publishing.
                </p>
                <div className="card-actions">
                  <button
                    type="button"
                    className="card-action-btn"
                    onClick={() => handleSelectTab('card-editor')}
                  >
                    Launch Card Studio →
                  </button>
                  <button
                    type="button"
                    className="card-action-btn secondary"
                    onClick={() => handleSelectTab('card-links')}
                  >
                    Manage Links & Menus →
                  </button>
                </div>
              </div>
            )}

            <div className="vraja-overview-card shared-identity">
              <div className="card-top">
                <span className="card-badge shared">Shared Core</span>
                <span className="card-status verified">Canonical</span>
              </div>
              <h3 className="card-title">Shared Business Profile</h3>
              <p className="card-desc">
                Single authoritative record for business name, logo, contact information, hours, and branch location.
              </p>
              <div className="card-actions">
                <button
                  type="button"
                  className="card-action-btn"
                  onClick={() => handleSelectTab('profile')}
                >
                  Edit Shared Profile →
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // 2. Shared Profile (Wired in Phase 3.3)
    if (activeTab === 'profile') {
      return <SharedBusinessProfileView />;
    }

    // 3. Product A Views (Wired in Phase 3.4)
    if (activeTab.startsWith('reviews-')) {
      const titles = {
        'reviews-setup': 'Review Setup & Keyword Configuration',
        'reviews-analytics': 'Authentic Review Activity & Timezone Analytics',
        'reviews-inbox': 'Private Feedback Management Inbox',
      };
      return (
        <div className="vraja-portal-view-container">
          <div className="vraja-view-header">
            <h1 className="vraja-view-title">{titles[activeTab] || 'Google Review Manager'}</h1>
            <p className="vraja-view-subtitle">
              Product A module integrated into the unified client portal shell.
            </p>
          </div>
          <div className="vraja-placeholder-panel">
            <span className="placeholder-icon">⭐</span>
            <h3>{titles[activeTab]}</h3>
            <p>
              Product A embedded component integration (Phase 3.4 target). Preserves the 5-section invariant standard.
            </p>
          </div>
        </div>
      );
    }

    // 4. Product B Views (Wired in Phase 3.5)
    if (activeTab.startsWith('card-')) {
      const titles = {
        'card-editor': 'Digital Business Card Studio',
        'card-links': 'Documents & Custom Action Links',
        'card-publish': 'Card Visibility & QR Publication',
      };
      return (
        <div className="vraja-portal-view-container">
          <div className="vraja-view-header">
            <h1 className="vraja-view-title">{titles[activeTab] || 'Digital Business Card'}</h1>
            <p className="vraja-view-subtitle">
              Product B module integrated into the unified client portal shell.
            </p>
          </div>
          <div className="vraja-placeholder-panel">
            <span className="placeholder-icon">🪪</span>
            <h3>{titles[activeTab]}</h3>
            <p>
              Product B embedded component integration (Phase 3.5 target). Live card mockup, appearance controls, and document storage.
            </p>
          </div>
        </div>
      );
    }

    // 5. Settings Tab (Wired in Phase 3.6)
    if (activeTab === 'settings') {
      return (
        <div className="vraja-portal-view-container">
          <div className="vraja-view-header">
            <h1 className="vraja-view-title">Account Settings & Security</h1>
            <p className="vraja-view-subtitle">
              Manage your credentials, membership role, and tenant metadata.
            </p>
          </div>
          <div className="vraja-placeholder-panel">
            <span className="placeholder-icon">🔒</span>
            <h3>Account Settings & Password Management</h3>
            <p>
              Shared portal settings integration (Phase 3.6 target). Self-service password change, active memberships, and role verification.
            </p>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="vraja-portal-shell">
      <PortalSidebar
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      />

      <div className="vraja-portal-main-wrapper">
        <PortalHeader
          activeTab={activeTab}
          onOpenMobileNav={() => setMobileNavOpen(true)}
          onPreviewReview={onPreviewReview}
          onPreviewCard={onPreviewCard}
        />

        {guardNotice && (
          <div className="vraja-portal-guard-banner" role="alert">
            <span className="banner-icon">ℹ️</span>
            <span className="banner-text">{guardNotice}</span>
          </div>
        )}

        <main className="vraja-portal-content" id="portal-main-content">
          {renderContent()}
        </main>

        <footer className="vraja-portal-footer">
          <div className="footer-left">
            <span>✨ <strong>VRAJA AI</strong> • Unified Multi-Product Client Portal</span>
          </div>
          <div className="footer-right">
            <span>Factual Analytics • Zero Synthesis • Tenant Guarded</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default UnifiedClientPortal;
