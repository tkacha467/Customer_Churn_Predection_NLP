import { useState, useEffect } from 'react';
import './index.css';
import CustomerReview from './components/CustomerReview';
import OwnerPortal from './components/OwnerPortal';
import VrajaAdmin from './components/VrajaAdmin';

function App() {
  // Route detection:
  // - Admin Console: /admin or ?view=admin
  // - Review Guest View: /b/:tenant/review or /review or ?view=review
  // - Owner Portal: /owner or /owner/:tenant or ?view=owner
  const getInitialView = () => {
    const path = window.location.pathname.toLowerCase();
    const params = new URLSearchParams(window.location.search);
    const view = params.get('view');

    // Admin Console
    if (path === '/admin' || path.startsWith('/admin') || view === 'admin') {
      return 'admin';
    }

    // General Owner Portal
    if (path.startsWith('/owner') || path.includes('/owner') || view === 'owner') {
      return 'owner';
    }

    // Customer Review Page
    return 'customer';
  };

  const getInitialBusinessId = () => {
    const params = new URLSearchParams(window.location.search);
    const queryId = params.get('business_id') || params.get('business') || params.get('b');
    if (queryId && queryId.trim()) return queryId.trim();

    const pathParts = window.location.pathname.split('/').filter(Boolean);
    // e.g. /b/:business_id/review or /b/:business_id
    if (pathParts[0] === 'b' && pathParts[1]) {
      return pathParts[1].trim();
    }
    // e.g. /owner/:business_id
    if (pathParts[0] === 'owner' && pathParts[1]) {
      return pathParts[1].trim();
    }
    // e.g. /review/:business_id
    if (pathParts[0] === 'review' && pathParts[1]) {
      return pathParts[1].trim();
    }

    // Custom client subdomain resolution (e.g. cafealpha.nastaghar.com)
    const hostname = window.location.hostname.toLowerCase();
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      const parts = hostname.split('.');
      if (parts.length > 2 && parts[0] !== 'www' && parts[0] !== 'app') {
        return parts[0].trim();
      }
    }

    return 'default_business';
  };

  const [activeView, setActiveView] = useState(getInitialView);
  const [businessId, setBusinessId] = useState(getInitialBusinessId);
  const [isPreviewMode, setIsPreviewMode] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('preview') === 'true';
  });

  // Handle browser back/forward
  useEffect(() => {
    const handlePopState = () => {
      setActiveView(getInitialView());
      setBusinessId(getInitialBusinessId());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateToProductB = (tenantId, editor = false) => {
    const base = (import.meta.env.VITE_PRODUCT_B_BASE_URL || window.location.origin).replace(/\/+$/, '');
    const route = editor ? `/owner/${encodeURIComponent(tenantId)}/card` : `/b/${encodeURIComponent(tenantId)}/card`;
    window.location.assign(`${base}${route}`);
  };

  const navigateToView = (view, preview = false) => {
    if (view === 'card' || view === 'card-editor') {
      navigateToProductB(businessId, view === 'card-editor');
      return;
    }
    setActiveView(view);
    setIsPreviewMode(preview);

    let newPath = '/';
    if (view === 'admin') {
      newPath = '/admin';
    } else if (view === 'owner') {
      newPath = businessId !== 'default_business' ? `/owner/${encodeURIComponent(businessId)}` : '/owner';
    } else {
      newPath = businessId !== 'default_business' ? `/b/${encodeURIComponent(businessId)}/review` : '/review';
    }

    const params = new URLSearchParams();
    if (preview) params.set('preview', 'true');
    const queryString = params.toString() ? `?${params.toString()}` : '';

    window.history.pushState({}, '', `${newPath}${queryString}`);
  };

  // ─── 0. INTERNAL PLATFORM ADMIN (/admin) ────────────────────────────────────
  if (activeView === 'admin') {
    return (
      <VrajaAdmin
        onNavigateToOwner={(tid) => {
          setBusinessId(tid);
          navigateToView('owner');
        }}
        onNavigateToCard={(tid) => navigateToProductB(tid)}
        onNavigateToReview={(tid) => {
          setBusinessId(tid);
          navigateToView('customer');
        }}
      />
    );
  }

  // ─── 3. CUSTOMER REVIEW EXPERIENCE (/b/:tenant/review or /review) ───────────
  if (activeView === 'customer') {
    return (
      <div className="ng-app-root">
        <CustomerReview
          businessId={businessId}
          isPreview={isPreviewMode}
          onSwitchToOwner={() => navigateToView('owner')}
        />
        <footer className="ng-footer">
          <span>Powered by ChurnLens • Google Review Assistant</span>
        </footer>
      </div>
    );
  }

  // ─── 4. OWNER PORTAL (/owner or /owner/:tenant) ─────────────────────────────
  return (
    <div className="product-layout">
      <div className="app-mode-bar">
        <div className="mode-bar-brand">
          <span className="mode-logo">🍳</span>
          <span className="mode-title">Nasta Ghar</span>
          <span className="mode-badge">Owner Dashboard</span>
        </div>
        <div className="mode-toggle-group">
          <button
            type="button"
            className="mode-btn"
            onClick={() => navigateToView('customer', true)}
          >
            👁️ Preview Guest Experience
          </button>
          <button
            type="button"
            className="mode-btn active"
          >
            💼 Owner Portal
          </button>
        </div>
      </div>

      <main className="product-main-content">
        <OwnerPortal
          businessId={businessId}
          onPreviewCustomer={() => navigateToView('customer', true)}
        />
      </main>

      <footer className="product-footer">
        <div className="footer-content">
          <span>Nasta Ghar • ChurnLens AI Review Assistant</span>
          <span>Google Business Profile Compliant • Zero Fabrication</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
