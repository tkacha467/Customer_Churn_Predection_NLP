import { useState } from 'react';
import './index.css';
import ReviewAssistant from './components/ReviewAssistant';
import IntegrityPlayground from './components/IntegrityPlayground';
import BusinessConsole from './components/BusinessConsole';

function App() {
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant' | 'business' | 'integrity'
  const [selectedBranch, setSelectedBranch] = useState('flagship');
  const businessId = 'default_business';

  return (
    <div className="app-container">
      {/* Top Enterprise Brand Bar */}
      <header className="enterprise-header">
        <div className="header-top-row">
          <div className="brand-group">
            <span className="brand-icon">☕</span>
            <div>
              <div className="brand-title">ChurnLens <span className="highlight-gold">Hospitality</span></div>
              <div className="brand-subtext">AI Guest Reviews & Reputation Intelligence for Cafes & Restaurants</div>
            </div>
          </div>

          <div className="header-right-controls">
            <div className="branch-selector-pill">
              <span style={{ fontSize: '0.85rem' }}>📍</span>
              <select
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                className="branch-select"
              >
                <option value="flagship">Cuore Roastery • Downtown Flagship</option>
                <option value="uptown">Cuore Bistro • Uptown West</option>
                <option value="airport">Cuore Express • Terminal 2</option>
              </select>
            </div>

            <div className="system-status-pill">
              <span className="live-dot">●</span>
              <span>NLP Engine Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main SaaS Navigation Tabs */}
      <nav className="nav-tab-container">
        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('assistant')}
        >
          <span>☕</span>
          <span>Guest Table Review</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'business' ? 'active' : ''}`}
          onClick={() => setActiveTab('business')}
        >
          <span>📊</span>
          <span>General Manager Portal</span>
        </button>

        <button
          type="button"
          className={`nav-tab-btn ${activeTab === 'integrity' ? 'active' : ''}`}
          onClick={() => setActiveTab('integrity')}
        >
          <span>🛡️</span>
          <span>NLP Integrity Lab</span>
        </button>
      </nav>

      {/* Main Workspace View */}
      <main>
        {activeTab === 'assistant' && (
          <ReviewAssistant businessId={businessId} />
        )}

        {activeTab === 'business' && (
          <BusinessConsole businessId={businessId} />
        )}

        {activeTab === 'integrity' && (
          <IntegrityPlayground />
        )}
      </main>

      {/* Enterprise Hospitality Footer */}
      <footer className="enterprise-footer">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <strong>ChurnLens Hospitality AI Platform</strong> • Enterprise Guest Experience & Google Review Handoff
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', color: 'var(--text-muted)' }}>
            <span>Compliant with Google Business Profile Policies</span>
            <span>Zero Hallucination Guaranteed</span>
            <span>Table QR Deep-linking Enabled</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
