import { useState, useEffect, useCallback } from 'react';
import { usePortalSession } from './PortalSessionContext';
import PortalSidebar from './PortalSidebar';
import PortalHeader from './PortalHeader';
import SharedBusinessProfileView from './SharedBusinessProfileView';
import { ProductAReviewSetup } from './product_a/ProductAReviewSetup';
import { ProductAReviewAnalytics } from './product_a/ProductAReviewAnalytics';
import { ProductAPrivateInbox } from './product_a/ProductAPrivateInbox';
import { apiFetch } from '../../lib/api';
import {
  AdminCard,
  AdminButton,
  AdminInput,
  AdminNotification,
} from '../admin/common';
import './UnifiedPortal.css';

export function UnifiedClientPortal({
  onPreviewReview,
  onPreviewCard,
}) {
  const {
    user,
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

  // Password management state for Settings section
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordStatus, setPasswordStatus] = useState({ type: '', text: '' });

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
                  Proactive customer feedback capture, AI-assisted review drafting, and authentic Google review analytics.
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

    // 3. Product A Views (Mounted in Phase 4)
    if (activeTab === 'reviews-setup') {
      return <ProductAReviewSetup businessId={activeTenant?.id} />;
    }
    if (activeTab === 'reviews-analytics') {
      return <ProductAReviewAnalytics businessId={activeTenant?.id} />;
    }
    if (activeTab === 'reviews-inbox') {
      return <ProductAPrivateInbox businessId={activeTenant?.id} />;
    }

    // 4. Product B Views (Phase 5 target)
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
              Product B embedded component integration (Phase 5 target). Live card mockup, appearance controls, and document storage.
            </p>
          </div>
        </div>
      );
    }

    // 5. Settings Tab (Section 5 Standard)
    if (activeTab === 'settings') {
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

      return (
        <div className="vraja-portal-view-container">
          <div className="vraja-view-header">
            <h1 className="vraja-view-title">Account Settings & Security</h1>
            <p className="vraja-view-subtitle">
              Manage credentials, authorized memberships, and canonical shared business profile.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            {/* Account & Tenant Identity Card */}
            <AdminCard
              title="Business Account & Identity"
              subtitle="Tenant metadata and authorized membership credentials"
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                <div style={{ backgroundColor: '#FAF9F6', padding: '14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                  <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', fontWeight: 600 }}>
                    Tenant Identifier
                  </span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#26352D', marginTop: '4px' }}>
                    {activeTenant?.id || 'default_business'}
                  </div>
                </div>

                <div style={{ backgroundColor: '#FAF9F6', padding: '14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                  <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', fontWeight: 600 }}>
                    Account Email
                  </span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#26352D', marginTop: '4px' }}>
                    {user?.email || 'N/A'}
                  </div>
                </div>

                <div style={{ backgroundColor: '#FAF9F6', padding: '14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                  <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', fontWeight: 600 }}>
                    Membership Role
                  </span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#174D3A', marginTop: '4px', textTransform: 'capitalize' }}>
                    {activeTenant?.role || 'Member'}
                  </div>
                </div>
              </div>

              {onPreviewReview && hasEntitlement('review_manager') && (
                <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #E3E8E3', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <strong style={{ color: '#26352D' }}>Customer Review Experience Preview</strong>
                    <p style={{ margin: '2px 0 0 0', fontSize: '13px', color: '#718078' }}>
                      Preview the customer review flow as a diner would experience it.
                    </p>
                  </div>
                  <AdminButton
                    type="button"
                    variant="secondary"
                    onClick={onPreviewReview}
                  >
                    Open Review Flow Preview ↗
                  </AdminButton>
                </div>
              )}
            </AdminCard>

            {/* Shared Business Profile Navigation inside Settings */}
            <AdminCard
              title="Canonical Shared Business Profile"
              subtitle="Business name, branch location, contact details, operating hours, and logo"
              actions={
                <AdminButton
                  type="button"
                  variant="primary"
                  onClick={() => handleSelectTab('profile')}
                >
                  🏢 Open Shared Profile & Logo →
                </AdminButton>
              }
            >
              <p style={{ margin: 0, fontSize: '13.5px', color: '#718078', lineHeight: '1.6' }}>
                Your business profile defines the authoritative brand identity across all enabled VRAJA AI products.
                Any updates made to your name, contact details, opening hours, or logo automatically propagate across Product A and Product B.
              </p>
            </AdminCard>

            {/* Password Management Card */}
            <AdminCard
              title="Password Management"
              subtitle="Update your business account password securely"
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
                  id="portal-current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />

                <AdminInput
                  label="New Password (min 8 characters)"
                  id="portal-new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />

                <AdminInput
                  label="Confirm New Password"
                  id="portal-confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />

                <div>
                  <AdminButton
                    type="submit"
                    variant="primary"
                    disabled={isChangingPassword}
                  >
                    {isChangingPassword ? 'Updating Password...' : '🔒 Change Password'}
                  </AdminButton>
                </div>
              </form>
            </AdminCard>
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
