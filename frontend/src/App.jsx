import { useState, useEffect } from 'react';
import './index.css';
import CustomerReview from './components/CustomerReview';
import OwnerPortal from './components/OwnerPortal';

function App() {
  // Route detection: customers get clean review page; owners access /owner
  const getInitialView = () => {
    const path = window.location.pathname.toLowerCase();
    const params = new URLSearchParams(window.location.search);
    const view = params.get('view');
    if (path.startsWith('/owner') || path.includes('/owner') || view === 'owner') return 'owner';
    return 'customer';
  };

  const getInitialBusinessId = () => {
    const params = new URLSearchParams(window.location.search);
    const queryId = params.get('business_id') || params.get('business') || params.get('b');
    if (queryId && queryId.trim()) return queryId.trim();

    const pathParts = window.location.pathname.split('/').filter(Boolean);
    // e.g. /b/:business_id or /b/:business_id/review or /b/:business_id/owner
    if (pathParts[0] === 'b' && pathParts[1]) {
      return pathParts[1].trim();
    }
    // e.g. /review/:business_id or /owner/:business_id
    if ((pathParts[0] === 'review' || pathParts[0] === 'owner') && pathParts[1]) {
      return pathParts[1].trim();
    }

    // Custom client subdomain resolution (e.g. cafealpha.nastaghar.com or client.domain)
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

  const navigateToView = (view, preview = false) => {
    setActiveView(view);
    setIsPreviewMode(preview);
    const newPath = view === 'owner' ? '/owner' : '/review';
    const params = new URLSearchParams(window.location.search);
    if (view === 'owner') params.delete('preview');
    else if (preview) params.set('preview', 'true');
    if (businessId && businessId !== 'default_business') {
      params.set('business_id', businessId);
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    window.history.pushState({}, '', `${newPath}${queryString}`);
  };

  // Customer QR experience: full-screen, no top bar
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

  // Owner portal: branded top bar + full dashboard
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
