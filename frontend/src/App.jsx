import { useState } from 'react';
import './index.css';
import ReviewAssistant from './components/ReviewAssistant';
import IntegrityPlayground from './components/IntegrityPlayground';
import BusinessConsole from './components/BusinessConsole';

function App() {
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant' | 'integrity' | 'business'
  const businessId = 'default_business';

  return (
    <div className="app-container">
      {/* Header & Brand */}
      <header>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '2.5rem' }}>🔮</span>
          <h1>ChurnLens AI</h1>
        </div>
        <p>
          AI-Assisted Customer Review & Intelligence Platform — turning customer experiences into verified Google reviews and actionable retention insights.
        </p>
      </header>

      {/* Mode Selector Tabs */}
      <nav className="nav-tab-container">
        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('assistant')}
        >
          <span>🌟</span>
          <span>AI Review Assistant</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'integrity' ? 'active' : ''}`}
          onClick={() => setActiveTab('integrity')}
        >
          <span>🛡️</span>
          <span>Integrity & Risk Engine</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'business' ? 'active' : ''}`}
          onClick={() => setActiveTab('business')}
        >
          <span>⚙️</span>
          <span>Business Portal</span>
        </button>
      </nav>

      {/* Main Tab Content */}
      <main>
        {activeTab === 'assistant' && (
          <ReviewAssistant businessId={businessId} />
        )}

        {activeTab === 'integrity' && (
          <IntegrityPlayground />
        )}

        {activeTab === 'business' && (
          <BusinessConsole businessId={businessId} />
        )}
      </main>

      {/* Footer */}
      <footer style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', padding: '2rem 0', borderTop: '1px solid rgba(255, 255, 255, 0.05)', marginTop: '2rem' }}>
        <p>ChurnLens AI Platform • Multi-Modal Customer Intelligence & Verified Google Review Handoff</p>
      </footer>
    </div>
  );
}

export default App;
