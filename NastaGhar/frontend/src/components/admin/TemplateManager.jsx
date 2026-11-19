import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../lib/api';

export default function TemplateManager({ tenants = [], onAssignmentSuccess, onPreviewCustomer }) {
  const [industries, setIndustries] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedIndustry, setSelectedIndustry] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Assign Modal state
  const [assignModalTemplate, setAssignModalTemplate] = useState(null);
  const [targetBusinessId, setTargetBusinessId] = useState(tenants[0]?.id || 'default_business');
  const [isAssigning, setIsAssigning] = useState(false);
  const [assignMessage, setAssignMessage] = useState({ type: '', text: '' });

  // Preview Modal state
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [previewViewport, setPreviewViewport] = useState('mobile'); // mobile, tablet, desktop

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [indRes, tplRes] = await Promise.all([
        apiFetch('/api/platform/industries'),
        apiFetch('/api/platform/templates'),
      ]);

      if (indRes.ok && tplRes.ok) {
        const indData = await indRes.json();
        const tplData = await tplRes.json();
        setIndustries(Array.isArray(indData) ? indData : []);
        setTemplates(Array.isArray(tplData) ? tplData : []);
      } else {
        setError('Failed to fetch template catalog from server.');
      }
    } catch {
      setError('Network error while connecting to template engine.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredTemplates = selectedIndustry === 'all'
    ? templates
    : templates.filter(t => t.industry_slug === selectedIndustry);

  const handleOpenAssignModal = (tpl) => {
    setAssignModalTemplate(tpl);
    setTargetBusinessId(tenants[0]?.id || 'default_business');
    setAssignMessage({ type: '', text: '' });
  };

  const handleExecuteAssignment = async () => {
    if (!assignModalTemplate || !targetBusinessId) return;
    setIsAssigning(true);
    setAssignMessage({ type: '', text: '' });
    try {
      const res = await apiFetch(`/api/platform/businesses/${encodeURIComponent(targetBusinessId)}/assign-template`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: assignModalTemplate.id,
          version_id: assignModalTemplate.active_version_id,
        }),
      });

      if (res.ok) {
        setAssignMessage({ type: 'success', text: `Template "${assignModalTemplate.name}" successfully assigned to ${targetBusinessId}!` });
        if (onAssignmentSuccess) onAssignmentSuccess(targetBusinessId, assignModalTemplate);
        setTimeout(() => {
          setAssignModalTemplate(null);
        }, 1200);
      } else {
        const err = await res.json().catch(() => ({}));
        setAssignMessage({ type: 'danger', text: err.detail || 'Failed to assign template.' });
      }
    } catch {
      setAssignMessage({ type: 'danger', text: 'Network error executing template assignment.' });
    } finally {
      setIsAssigning(false);
    }
  };

  return (
    <div className="template-manager-root">
      {/* Header and Controls */}
      <div className="tm-header">
        <div>
          <h2 className="tm-title">🎨 Dynamic Industry Template Library</h2>
          <p className="tm-subtitle">
            Controlled, database-driven templates across Restaurant, Hotel, Salon, and Clinic industries.
          </p>
        </div>
        <button
          type="button"
          className="admin-btn admin-btn-secondary"
          onClick={loadData}
          disabled={loading}
        >
          🔄 Refresh Catalog
        </button>
      </div>

      {error && (
        <div className="admin-alert admin-alert-danger" role="alert">
          ⚠️ {error}
        </div>
      )}

      {/* Industry Tabs */}
      <div className="tm-industry-tabs" role="tablist" aria-label="Industries">
        <button
          type="button"
          className={`tm-tab ${selectedIndustry === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedIndustry('all')}
        >
          ✨ All Industries ({templates.length})
        </button>
        {industries.map((ind) => {
          const count = templates.filter(t => t.industry_id === ind.id).length;
          return (
            <button
              key={ind.id}
              type="button"
              className={`tm-tab ${selectedIndustry === ind.slug ? 'active' : ''}`}
              onClick={() => setSelectedIndustry(ind.slug)}
            >
              <span className="tm-tab-icon">{ind.icon}</span>
              <span>{ind.name}</span>
              <span className="tm-tab-badge">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Template Grid */}
      {loading ? (
        <div className="admin-empty-state">
          <div className="admin-spinner" />
          <p>Loading published industry templates…</p>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="admin-empty-state">
          <p>No templates found for this industry.</p>
        </div>
      ) : (
        <div className="tm-grid">
          {filteredTemplates.map((tpl) => {
            const config = tpl.configuration || {};
            const theme = config.theme || {};
            const topics = config.topics || [];
            const isAssignedToDefault = tpl.slug === 'restaurant_classic';

            return (
              <div key={tpl.id} className="tm-card">
                <div className="tm-card-header">
                  <div className="tm-card-industry-tag">
                    <span>{tpl.industry_icon}</span>
                    <span>{tpl.industry_name}</span>
                  </div>
                  <span className="tm-version-tag">v{tpl.active_version || '1.0.0'}</span>
                </div>

                <h3 className="tm-card-title">{tpl.name}</h3>
                <p className="tm-card-desc">{tpl.description}</p>

                {/* Color Palette Preview */}
                <div className="tm-palette-section">
                  <span className="tm-palette-label">Theme Palette:</span>
                  <div className="tm-palette-pills">
                    <span
                      className="tm-color-circle"
                      style={{ backgroundColor: theme.primaryAccent || '#f97316' }}
                      title={`Primary Accent: ${theme.primaryAccent}`}
                    />
                    <span
                      className="tm-color-circle"
                      style={{ backgroundColor: theme.secondaryAccent || '#c9ff00' }}
                      title={`Secondary Accent: ${theme.secondaryAccent}`}
                    />
                    <span
                      className="tm-color-circle"
                      style={{ backgroundColor: theme.cardBackground || '#162017', border: '1px solid #444' }}
                      title={`Card Background: ${theme.cardBackground}`}
                    />
                    <span className="tm-palette-name">{theme.variant}</span>
                  </div>
                </div>

                {/* Topics Preview */}
                <div className="tm-topics-preview">
                  <span className="tm-palette-label">Default Highlights ({topics.length}):</span>
                  <div className="tm-chips-row">
                    {topics.slice(0, 4).map((top, idx) => (
                      <span key={idx} className="tm-mini-chip">
                        {top.icon} {top.label}
                      </span>
                    ))}
                    {topics.length > 4 && (
                      <span className="tm-mini-chip tm-mini-chip-more">+{topics.length - 4} more</span>
                    )}
                  </div>
                </div>

                {/* Footer Actions */}
                <div className="tm-card-footer">
                  <button
                    type="button"
                    className="admin-btn admin-btn-secondary"
                    onClick={() => setPreviewTemplate(tpl)}
                  >
                    👁️ Live Preview
                  </button>
                  <button
                    type="button"
                    className="admin-btn admin-btn-primary"
                    onClick={() => handleOpenAssignModal(tpl)}
                  >
                    🚀 Assign to Business
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ─── LIVE PREVIEW MODAL ──────────────────────────────────────────────── */}
      {previewTemplate && (
        <div className="admin-modal-backdrop" onClick={() => setPreviewTemplate(null)}>
          <div
            className={`tm-preview-modal tm-preview-${previewViewport}`}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="tm-preview-header">
              <div className="tm-preview-title-box">
                <span className="tm-preview-icon">{previewTemplate.industry_icon}</span>
                <div>
                  <h4>{previewTemplate.name}</h4>
                  <span>Industry: {previewTemplate.industry_name} • v{previewTemplate.active_version}</span>
                </div>
              </div>

              {/* Viewport Switcher */}
              <div className="tm-viewport-switcher">
                <button
                  type="button"
                  className={`tm-vp-btn ${previewViewport === 'mobile' ? 'active' : ''}`}
                  onClick={() => setPreviewViewport('mobile')}
                  title="Mobile Viewport (390px)"
                >
                  📱 Mobile
                </button>
                <button
                  type="button"
                  className={`tm-vp-btn ${previewViewport === 'tablet' ? 'active' : ''}`}
                  onClick={() => setPreviewViewport('tablet')}
                  title="Tablet Viewport (768px)"
                >
                  📱 Tablet
                </button>
                <button
                  type="button"
                  className={`tm-vp-btn ${previewViewport === 'desktop' ? 'active' : ''}`}
                  onClick={() => setPreviewViewport('desktop')}
                  title="Desktop Viewport"
                >
                  💻 Desktop
                </button>
              </div>

              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setPreviewTemplate(null)}
              >
                ✕
              </button>
            </div>

            <div className="tm-preview-body">
              {/* Mock Rendered Frame */}
              <div
                className="tm-preview-frame"
                style={{
                  backgroundColor: previewTemplate.configuration?.theme?.backgroundColor || '#0d130e',
                  color: previewTemplate.configuration?.theme?.textColor || '#f8fafc',
                }}
              >
                {/* Hero preview */}
                <div
                  className="tm-preview-hero"
                  style={{
                    backgroundColor: previewTemplate.configuration?.theme?.cardBackground || '#162017',
                    borderBottom: `2px solid ${previewTemplate.configuration?.theme?.primaryAccent || '#f97316'}`,
                  }}
                >
                  <div className="tm-preview-badge" style={{ backgroundColor: previewTemplate.configuration?.theme?.primaryAccent || '#f97316' }}>
                    {previewTemplate.configuration?.theme?.badgeText || 'Vraja Experience'}
                  </div>
                  <h3>Sample Business Experience</h3>
                  <p>Customer review & feedback assistant</p>
                </div>

                {/* Rating Stars Mock */}
                <div className="tm-preview-stars">
                  <span className="tm-star-mock">★</span>
                  <span className="tm-star-mock">★</span>
                  <span className="tm-star-mock">★</span>
                  <span className="tm-star-mock">★</span>
                  <span className="tm-star-mock active" style={{ color: previewTemplate.configuration?.theme?.primaryAccent || '#f97316' }}>★</span>
                  <div className="tm-star-caption">Loved it! 🤩</div>
                </div>

                {/* Topic Chips Mock */}
                <div className="tm-preview-chips-box">
                  <div className="tm-preview-sub">
                    {previewTemplate.configuration?.experienceLabels?.whatStoodOut || 'What stood out?'}
                  </div>
                  <div className="tm-preview-chips-grid">
                    {(previewTemplate.configuration?.topics || []).map((top, i) => (
                      <div
                        key={i}
                        className={`tm-preview-chip ${i === 0 ? 'selected' : ''}`}
                        style={i === 0 ? { borderColor: previewTemplate.configuration?.theme?.primaryAccent, background: 'rgba(255,255,255,0.08)' } : {}}
                      >
                        <span>{top.icon}</span>
                        <span>{top.label}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action CTA Mock */}
                <div className="tm-preview-actions">
                  <button
                    type="button"
                    className="tm-preview-cta"
                    style={{ backgroundColor: previewTemplate.configuration?.theme?.primaryAccent || '#f97316' }}
                  >
                    Copy & Open Google Review →
                  </button>
                  <div className="tm-preview-antigating">
                    🔒 Google Anti-Gating Compliant: Direct Google Maps access on all ratings
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── ASSIGN TEMPLATE MODAL ─────────────────────────────────────────── */}
      {assignModalTemplate && (
        <div className="admin-modal-backdrop" onClick={() => setAssignModalTemplate(null)}>
          <div
            className="admin-modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="admin-modal-header">
              <h3>🚀 Assign Template to Business</h3>
              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setAssignModalTemplate(null)}
              >
                ✕
              </button>
            </div>

            <div className="admin-modal-body">
              <div className="admin-info-banner">
                Assigning <strong>{assignModalTemplate.name}</strong> ({assignModalTemplate.industry_name}) to an active tenant.
              </div>

              {assignMessage.text && (
                <div className={`admin-alert admin-alert-${assignMessage.type}`} role="alert">
                  {assignMessage.type === 'success' ? '✅' : '⚠️'} {assignMessage.text}
                </div>
              )}

              <div className="admin-form-group">
                <label className="admin-label-text">Select Target Business Tenant</label>
                <select
                  className="admin-select"
                  value={targetBusinessId}
                  onChange={(e) => setTargetBusinessId(e.target.value)}
                >
                  {tenants.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.business_name || t.id} ({t.id}) — {t.category || 'Business'}
                    </option>
                  ))}
                  {!tenants.some(t => t.id === 'default_business') && (
                    <option value="default_business">Nasta Ghar (default_business)</option>
                  )}
                </select>
              </div>

              <div className="admin-form-group">
                <label className="admin-label-text">Template Version</label>
                <input
                  type="text"
                  className="admin-input"
                  value={`v${assignModalTemplate.active_version || '1.0.0'} (Published & Immutable)`}
                  disabled
                />
              </div>

              <div className="admin-btn-row" style={{ marginTop: '20px' }}>
                <button
                  type="button"
                  className="admin-btn admin-btn-secondary"
                  onClick={() => setAssignModalTemplate(null)}
                  disabled={isAssigning}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="admin-btn admin-btn-primary"
                  onClick={handleExecuteAssignment}
                  disabled={isAssigning}
                >
                  {isAssigning ? 'Applying Assignment…' : 'Confirm & Apply Template'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
