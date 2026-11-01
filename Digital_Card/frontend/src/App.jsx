import { useState, useEffect } from 'react';
import './index.css';
import DigitalCard from './components/DigitalCard';
import DigitalCardEditor from './components/DigitalCardEditor';
import DigitalCardRedesignDemo from './components/DigitalCardRedesignDemo';

function App() {
  const getInitialView = () => {
    const path = window.location.pathname.toLowerCase();
    const params = new URLSearchParams(window.location.search);
    const view = params.get('view');

    // Redesign Demo preview: /demo or ?view=demo
    if (path.includes('/demo') || view === 'demo') {
      return 'demo';
    }

    // Editor view: /owner or /card-editor or view === 'card-editor' or view === 'editor'
    if (path.includes('/owner') || path.includes('/editor') || view === 'card-editor' || view === 'editor') {
      return 'card-editor';
    }

    // Default to public card view
    return 'card';
  };

  const getInitialBusinessId = () => {
    const params = new URLSearchParams(window.location.search);
    const queryId = params.get('business_id') || params.get('business') || params.get('b') || params.get('tenant');
    if (queryId && queryId.trim()) return queryId.trim();

    const pathParts = window.location.pathname.split('/').filter(Boolean);
    // Matching /b/:tenant/card
    if (pathParts.length >= 2 && pathParts[0].toLowerCase() === 'b') {
      return pathParts[1];
    }
    // Matching /owner/:tenant/card
    if (pathParts.length >= 2 && pathParts[0].toLowerCase() === 'owner') {
      return pathParts[1];
    }
    // Matching /card/:tenant
    if (pathParts.length >= 2 && pathParts[0].toLowerCase() === 'card') {
      return pathParts[1];
    }
    return 'default_business';
  };

  const [view, setView] = useState(getInitialView);
  const [businessId, setBusinessId] = useState(getInitialBusinessId);

  useEffect(() => {
    const handlePopState = () => {
      setView(getInitialView());
      setBusinessId(getInitialBusinessId());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
      {view === 'demo' ? (
        <DigitalCardRedesignDemo
          businessId={businessId}
        />
      ) : view === 'card-editor' ? (
        <DigitalCardEditor
          businessId={businessId}
          onSwitchTenant={(newId) => setBusinessId(newId)}
        />
      ) : (
        <DigitalCardRedesignDemo
          businessId={businessId}
          onOpenEditor={() => setView('card-editor')}
        />
      )}
    </div>
  );
}

export default App;
