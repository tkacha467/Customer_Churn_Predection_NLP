import { useState, useEffect, useCallback, useMemo } from 'react';
import { usePortalSession } from '../PortalSessionContext';
import { useIndustryConfig } from '../useIndustryConfig';
import { apiFetch } from '../../../lib/api';
import {
  AdminCard,
  AdminButton,
  AdminInput,
  AdminNotification,
} from '../../admin/common';

/**
 * Product A: Review Setup Component (Multi-Industry Foundation)
 * Allows tenant owners to configure Google Review destination link,
 * industry classification, business subcategories, touchpoint metadata,
 * and review topic keywords.
 * 
 * Enforces:
 * - Data-driven terminology from Backend Industry Registry.
 * - Owner role required to edit setup or switch industry.
 * - Zero loss of custom tenant topics.
 * - Automatic customer language detection per Decision 2.1.
 */
export function ProductAReviewSetup({ businessId: propBusinessId }) {
  const {
    activeTenant,
    user,
    handleSessionExpired,
  } = usePortalSession();

  const businessId = propBusinessId || activeTenant?.id || 'default_business';
  const userRole = (activeTenant?.role || 'member').toLowerCase();
  const isOwnerOrAdmin = userRole === 'owner' || !!user?.is_platform_admin;
  const canEdit = isOwnerOrAdmin;

  const {
    industryConfig,
    terminology,
    defaultTopics,
    availableIndustries,
    refreshIndustryConfig,
  } = useIndustryConfig(businessId);

  // Form state
  const [businessName, setBusinessName] = useState('');
  const [branch, setBranch] = useState('');
  const [category, setCategory] = useState('Breakfast & Snacks');
  const [industryId, setIndustryId] = useState('restaurant');
  const [description, setDescription] = useState('');
  const [googleReviewUrl, setGoogleReviewUrl] = useState('');
  const [isUrlConfigured, setIsUrlConfigured] = useState(false);
  const [topics, setTopics] = useState([
    'Food Quality', 'Taste & Flavour', 'Service', 'Cleanliness', 'Ambiance', 'Value for Money'
  ]);
  const [newTopicInput, setNewTopicInput] = useState('');
  const [primaryAccent, setPrimaryAccent] = useState('#174D3A');

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');
  const [saveErrorMsg, setSaveErrorMsg] = useState('');

  // Fetch business review configuration
  const fetchConfig = useCallback(async () => {
    setIsLoading(true);
    setSaveErrorMsg('');
    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/review-link`);
      if (res.status === 401) {
        handleSessionExpired?.();
        return;
      }
      if (!res.ok) {
        throw new Error('Could not load review configuration.');
      }
      const data = await res.json();
      if (data.business_name) setBusinessName(data.business_name);
      if (data.branch) setBranch(data.branch);
      if (data.category) setCategory(data.category);
      if (data.industry_id) setIndustryId(data.industry_id);
      if (data.description) setDescription(data.description);
      if (data.review_url) setGoogleReviewUrl(data.review_url);
      setIsUrlConfigured(Boolean(data.is_configured));
      if (Array.isArray(data.topics) && data.topics.length > 0) {
        setTopics(data.topics);
      }
      if (data.primary_accent) setPrimaryAccent(data.primary_accent);
    } catch (err) {
      console.warn('[ProductAReviewSetup] Fetch error:', err);
      setSaveErrorMsg(err.message || 'Failed to load configuration.');
    } finally {
      setIsLoading(false);
    }
  }, [businessId, handleSessionExpired]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Sync industryId from industryConfig if available and not yet set
  useEffect(() => {
    if (industryConfig?.industry_id && !industryId) {
      setIndustryId(industryConfig.industry_id);
    }
  }, [industryConfig, industryId]);

  const currentIndustry = useMemo(() => {
    return availableIndustries.find((i) => i.industry_id === industryId) || null;
  }, [availableIndustries, industryId]);

  const handleIndustryChange = (newIndId) => {
    if (!canEdit) return;
    setIndustryId(newIndId);
    const chosen = availableIndustries.find((i) => i.industry_id === newIndId);
    if (chosen && chosen.default_subcategory) {
      setCategory(chosen.default_subcategory);
    }
  };

  const handleResetTopicsToDefault = () => {
    if (!canEdit) return;
    const defaults = currentIndustry?.default_topics || defaultTopics;
    if (defaults && defaults.length > 0) {
      setTopics([...defaults]);
      setSaveSuccessMsg(`✓ Loaded ${currentIndustry?.display_name || 'industry'} default topics.`);
      setTimeout(() => setSaveSuccessMsg(''), 3500);
    }
  };

  // Handle configuration save
  const handleSaveConfig = async (e) => {
    if (e) e.preventDefault();
    if (!canEdit) return;

    setIsSaving(true);
    setSaveSuccessMsg('');
    setSaveErrorMsg('');

    try {
      const payload = {
        business_name: businessName,
        branch,
        category,
        industry_id: industryId,
        description,
        google_review_url: googleReviewUrl,
        topics,
        primary_accent: primaryAccent,
      };

      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.status === 401) {
        handleSessionExpired?.();
        return;
      }

      if (res.status === 403) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Insufficient permissions: Owner role is required to modify setup.');
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Could not save review configuration.');
      }

      const data = await res.json();
      setIsUrlConfigured(Boolean(data.is_configured));
      await refreshIndustryConfig();
      setSaveSuccessMsg('✓ Review Setup saved successfully!');
      setTimeout(() => setSaveSuccessMsg(''), 4000);
    } catch (err) {
      console.error('[ProductAReviewSetup] Save error:', err);
      setSaveErrorMsg(err.message || 'Could not save configuration. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Add custom review aspect chip
  const handleAddTopic = () => {
    if (!canEdit) return;
    const trimmed = newTopicInput.trim();
    if (trimmed && !topics.includes(trimmed)) {
      setTopics([...topics, trimmed]);
      setNewTopicInput('');
    }
  };

  // Remove aspect chip
  const handleRemoveTopic = (t) => {
    if (!canEdit) return;
    setTopics(topics.filter((item) => item !== t));
  };

  if (isLoading) {
    return (
      <div className="vraja-portal-view-container">
        <div style={{ padding: '36px', textAlign: 'center', color: '#718078' }}>
          Loading Review Setup configuration...
        </div>
      </div>
    );
  }

  return (
    <div className="vraja-portal-view-container">
      <div className="vraja-view-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 className="vraja-view-title">Review Setup & Topics</h1>
            <p className="vraja-view-subtitle">
              Configure your business industry, Google Review destination URL, topic chips, and theme accent.
            </p>
          </div>
          {!canEdit && (
            <div style={{ fontSize: '12.5px', color: '#718078', backgroundColor: '#FAF9F6', padding: '6px 12px', borderRadius: '6px', border: '1px solid #E3E8E3' }}>
              🔒 Read-only view (Owner role required to modify setup)
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
        <AdminCard
          title="Business Review Profile"
          subtitle="Customer-facing profile, industry classification, and Google Review destination link"
          actions={
            canEdit && (
              <AdminButton
                type="submit"
                variant="primary"
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : '💾 Save Setup'}
              </AdminButton>
            )
          }
        >
          {saveSuccessMsg && (
            <div style={{ marginBottom: '16px' }}>
              <AdminNotification type="success" message={saveSuccessMsg} />
            </div>
          )}

          {saveErrorMsg && (
            <div style={{ marginBottom: '16px' }}>
              <AdminNotification type="error" message={saveErrorMsg} />
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
            <AdminInput
              label="Business Display Name"
              id="setup-business-name"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              disabled={!canEdit}
              required
            />

            <AdminInput
              label="Branch / Location Name"
              id="setup-branch"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="e.g. Downtown, Ring Road"
              disabled={!canEdit}
            />

            {/* Industry Classification Selector */}
            <div className="vraja-form-group">
              <label className="vraja-form-label" htmlFor="setup-industry">Industry Classification</label>
              {canEdit ? (
                <select
                  id="setup-industry"
                  className="vraja-input"
                  value={industryId}
                  onChange={(e) => handleIndustryChange(e.target.value)}
                  disabled={!canEdit || isSaving}
                  style={{ height: '42px', padding: '0 12px' }}
                >
                  {availableIndustries.map((ind) => (
                    <option key={ind.industry_id} value={ind.industry_id}>
                      {ind.display_name}
                    </option>
                  ))}
                  {industryId === 'unclassified' && (
                    <option value="unclassified">Unclassified Business</option>
                  )}
                </select>
              ) : (
                <input
                  type="text"
                  className="vraja-input"
                  value={industryConfig?.industry_name || 'Business'}
                  disabled
                />
              )}
              <span style={{ fontSize: '11.5px', color: '#718078', marginTop: '4px', display: 'block' }}>
                Touchpoint: {terminology.touchpoint_noun} ({terminology.touchpoint_placeholder})
              </span>
            </div>

            {/* Business Subcategory */}
            <div className="vraja-form-group">
              <label className="vraja-form-label" htmlFor="setup-category">Business Subcategory</label>
              <input
                id="setup-category"
                type="text"
                className="vraja-input"
                list="subcategory-options"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder={currentIndustry?.default_subcategory || 'e.g. Casual Dining, Fitness Club'}
                disabled={!canEdit}
              />
              <datalist id="subcategory-options">
                {currentIndustry?.subcategories?.map((sc) => (
                  <option key={sc} value={sc} />
                ))}
              </datalist>
            </div>

            <div className="vraja-form-group">
              <label className="vraja-form-label">Primary Accent Color</label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="color"
                  value={primaryAccent}
                  onChange={(e) => setPrimaryAccent(e.target.value)}
                  disabled={!canEdit}
                  style={{
                    width: '42px',
                    height: '38px',
                    padding: 0,
                    border: '1px solid #E3E8E3',
                    borderRadius: '6px',
                    cursor: canEdit ? 'pointer' : 'default',
                  }}
                />
                <AdminInput
                  value={primaryAccent}
                  onChange={(e) => setPrimaryAccent(e.target.value)}
                  disabled={!canEdit}
                  style={{ flex: 1 }}
                />
              </div>
            </div>
          </div>

          <div style={{ marginTop: '16px' }} className="vraja-form-group">
            <label className="vraja-form-label">Business Welcome Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={`A short welcome note for your ${terminology.customer_noun_plural.toLowerCase()}.`}
              disabled={!canEdit}
              className="vraja-input"
              style={{ height: 'auto', padding: '10px 12px', resize: 'vertical' }}
            />
          </div>

          {/* Google Review Destination URL */}
          <div style={{ marginTop: '20px', paddingTop: '18px', borderTop: '1px solid #E3E8E3' }}>
            <AdminInput
              label="Official Google Review URL / Place ID"
              id="setup-review-url"
              type="url"
              value={googleReviewUrl}
              onChange={(e) => setGoogleReviewUrl(e.target.value)}
              placeholder="https://search.google.com/local/writereview?placeid=..."
              helperText={`${terminology.customer_noun_plural} who approve their AI-crafted review draft will be redirected straight to this Google Maps review dialog.`}
              disabled={!canEdit}
              required
            />

            {googleReviewUrl && (
              <div style={{ marginTop: '8px' }}>
                <a
                  href={googleReviewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: '#174D3A',
                    textDecoration: 'none',
                  }}
                >
                  ↗ Test Open Google Review Dialog in New Tab
                </a>
              </div>
            )}
          </div>
        </AdminCard>

        {/* Review Highlights & Topic Aspects */}
        <AdminCard
          title="Review Highlights & Aspects"
          subtitle={`Keywords that ${terminology.customer_noun_plural.toLowerCase()} can tap when generating their review draft`}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ fontSize: '12.5px', color: '#718078' }}>
              {topics.length > 0 ? `${topics.length} aspect keywords configured` : 'No aspects configured'}
            </div>
            {canEdit && (
              <button
                type="button"
                onClick={handleResetTopicsToDefault}
                className="vraja-btn vraja-btn-outline vraja-btn-sm"
                style={{ fontSize: '11.5px', padding: '4px 10px' }}
                title="Populate aspects with recommended industry defaults"
              >
                ↺ Load Industry Defaults
              </button>
            )}
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
            {topics.map((t, idx) => (
              <span key={idx} className="vraja-aspect-tag">
                <span>{t}</span>
                {canEdit && (
                  <button
                    type="button"
                    className="vraja-aspect-remove-btn"
                    onClick={() => handleRemoveTopic(t)}
                    title={`Remove aspect ${t}`}
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>

          {canEdit && (
            <div style={{ display: 'flex', gap: '10px', maxWidth: '520px' }}>
              <AdminInput
                placeholder="e.g. Friendly Staff, Cleanliness, Quick Service"
                value={newTopicInput}
                onChange={(e) => setNewTopicInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTopic();
                  }
                }}
                style={{ flex: 1 }}
              />
              <AdminButton
                type="button"
                variant="secondary"
                onClick={handleAddTopic}
              >
                + Add Aspect
              </AdminButton>
            </div>
          )}
        </AdminCard>
      </form>
    </div>
  );
}

export default ProductAReviewSetup;
