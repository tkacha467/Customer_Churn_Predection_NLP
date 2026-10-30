import { useState, useEffect, useRef, useCallback } from 'react';
import QRCode from 'qrcode';
import { apiFetch } from '../lib/api';
import DigitalCard from './DigitalCard';
import { BACKGROUND_PRESETS, ACCENT_PRESETS } from '../lib/appearancePresets';

const DOCUMENT_CATEGORIES = [
  { id: 'food_menu', label: 'Food Menu', icon: '🍽️' },
  { id: 'drinks_menu', label: 'Drinks & Bar Menu', icon: '🍷' },
  { id: 'dessert_menu', label: 'Dessert Menu', icon: '🍰' },
  { id: 'brochure', label: 'Brochure / Flyer', icon: '📄' },
  { id: 'catalogue', label: 'Product Catalogue', icon: '📖' },
  { id: 'other', label: 'Other PDF Document', icon: '📎' },
];

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function DigitalCardEditor({
  businessId = 'default_business',
  onPreviewCard = null,
  onBackToReviews = null,
}) {
  // Session & Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [isSigningIn, setIsSigningIn] = useState(false);

  // Tenant & Entitlement info
  const [tenantName, setTenantName] = useState(businessId);
  const [hasCardEntitlement, setHasCardEntitlement] = useState(true);
  const [entitlements, setEntitlements] = useState(['digital_card']);

  // Editor Section Tabs: 'details' | 'appearance' | 'contact' | 'social' | 'documents' | 'publish'
  const [activeSection, setActiveSection] = useState('details');

  // Form State: Identity
  const [displayName, setDisplayName] = useState('');
  const [category, setCategory] = useState('');
  const [openingHours, setOpeningHours] = useState('');
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [email, setEmail] = useState('');
  const [tagline, setTagline] = useState('');
  const [logoPath, setLogoPath] = useState('');
  const [coverImagePath, setCoverImagePath] = useState('');
  const [showReviewButton, setShowReviewButton] = useState(true);
  const [isPublished, setIsPublished] = useState(false);

  // Form State: Appearance Customization
  const [backgroundPreset, setBackgroundPreset] = useState('default_navy');
  const [overlayOpacity, setOverlayOpacity] = useState(0.75);
  const [primaryAccent, setPrimaryAccent] = useState('#078BFF');

  // Form State: Contact
  const [phoneNumber, setPhoneNumber] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [address, setAddress] = useState('');
  const [mapUrl, setMapUrl] = useState('');

  // Form State: Social & Links
  const [whatsappUrl, setWhatsappUrl] = useState('');
  const [whatsappGroupUrl, setWhatsappGroupUrl] = useState('');
  const [instagramUrl, setInstagramUrl] = useState('');
  const [facebookUrl, setFacebookUrl] = useState('');
  const [youtubeUrl, setYouTubeUrl] = useState('');
  const [customLinks, setCustomLinks] = useState([]);
  const [newLinkTitle, setNewLinkTitle] = useState('');
  const [newLinkUrl, setNewLinkUrl] = useState('');

  // Brand Image Upload State
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [isUploadingCover, setIsUploadingCover] = useState(false);
  const [imageUploadError, setImageUploadError] = useState('');

  // Documents State
  const [documents, setDocuments] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadCategory, setUploadCategory] = useState('food_menu');
  const [uploadDisplayName, setUploadDisplayName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  // Document Rename Modal / Edit State
  const [editingDocId, setEditingDocId] = useState(null);
  const [editDocName, setEditDocName] = useState('');
  const [editDocCategory, setEditDocCategory] = useState('food_menu');

  // Saving & Feedback
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');
  const [saveErrorMsg, setSaveErrorMsg] = useState('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Live Preview Modal
  const [showLivePreview, setShowLivePreview] = useState(false);

  // Card QR code state & styling
  const [qrForegroundColor, setQrForegroundColor] = useState('#061329');
  const [cardQrDataUrl, setCardQrDataUrl] = useState('');
  const [cardCopiedToast, setCardCopiedToast] = useState(false);

  // ─── 1. CHECK SESSION ───────────────────────────────────────────────────────
  useEffect(() => {
    let active = true;
    setIsCheckingSession(true);
    apiFetch('/api/auth/session')
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      })
      .catch(() => { if (active) setIsAuthenticated(false); })
      .finally(() => { if (active) setIsCheckingSession(false); });

    return () => { active = false; };
  }, []);

  const loadDocuments = useCallback(() => {
    setIsLoadingDocs(true);
    apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/documents`)
      .then(async (res) => {
        if (res.ok) {
          const docs = await res.json();
          setDocuments(docs);
        }
      })
      .catch(() => {})
      .finally(() => setIsLoadingDocs(false));
  }, [businessId]);

  // ─── 2. LOAD PROFILE & TENANT DATA ──────────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;

    // Fetch tenant entitlements & business config
    apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/review-link`)
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          const t = await res.json();
          setTenantName(t.business_name || businessId);
          const ent = Array.isArray(t.entitlements) ? t.entitlements : ['digital_card'];
          setEntitlements(ent);
          setHasCardEntitlement(ent.includes('digital_card'));
        }
      })
      .catch(() => {});

    // Fetch profile
    apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/profile`)
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          const p = await res.json();
          setDisplayName(p.display_name || '');
          setCategory(p.category || '');
          setOpeningHours(p.opening_hours || '');
          setWelcomeMessage(p.welcome_message || '');
          setEmail(p.email || '');
          setTagline(p.tagline || '');
          setLogoPath(p.logo_path || '');
          setCoverImagePath(p.cover_image_path || '');
          setBackgroundPreset(p.background_preset || 'default_navy');
          setOverlayOpacity(typeof p.overlay_opacity === 'number' ? p.overlay_opacity : 0.75);
          setPrimaryAccent(p.primary_accent || '#078BFF');
          setShowReviewButton(p.show_review_button !== false);
          setIsPublished(Boolean(p.is_published));
          setPhoneNumber(p.phone_number || '');
          setWebsiteUrl(p.website_url || '');
          setAddress(p.address || '');
          setMapUrl(p.map_url || '');
          setWhatsappUrl(p.whatsapp_url || '');
          setWhatsappGroupUrl(p.whatsapp_group_url || '');
          setInstagramUrl(p.instagram_url || '');
          setFacebookUrl(p.facebook_url || '');
          setYouTubeUrl(p.youtube_url || '');
          setCustomLinks(Array.isArray(p.custom_links) ? p.custom_links : []);
          setHasUnsavedChanges(false);
        }
      })
      .catch(() => {});

    // Fetch documents
    loadDocuments();

    return () => { active = false; };
  }, [isAuthenticated, businessId, loadDocuments]);

  // ─── 3. GENERATE CARD QR CODE ──────────────────────────────────────────────
  const canonicalCardUrl = `${window.location.origin}/b/${encodeURIComponent(businessId)}/card`;

  useEffect(() => {
    if (!canonicalCardUrl) return;
    QRCode.toDataURL(canonicalCardUrl, {
      width: 320,
      margin: 2,
      color: {
        dark: qrForegroundColor || '#061329',
        light: '#ffffff',
      },
    })
      .then((url) => setCardQrDataUrl(url))
      .catch((err) => console.error('Failed generating Card QR:', err));
  }, [canonicalCardUrl, qrForegroundColor]);

  // ─── 4. UNSAVED CHANGES WARNING ─────────────────────────────────────────────
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  const markDirty = () => {
    setHasUnsavedChanges(true);
    setSaveSuccessMsg('');
    setSaveErrorMsg('');
  };

  // ─── 5. OWNER LOGIN HANDLER ─────────────────────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsSigningIn(true);
    try {
      const payload = {
        password: ownerPassword,
        tenant_id: businessId !== 'default_business' ? businessId : undefined,
      };
      if (ownerEmail.trim()) {
        payload.email = ownerEmail.trim();
      }
      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Sign-in failed. Please check your credentials.');
      }
      setOwnerPassword('');
      setIsAuthenticated(true);
    } catch (err) {
      setAuthError(err.message || 'Could not sign in.');
    } finally {
      setIsSigningIn(false);
    }
  };

  // ─── 6. SAVE PROFILE ────────────────────────────────────────────────────────
  const handleSaveProfile = async (overridePublished = null) => {
    setIsSaving(true);
    setSaveSuccessMsg('');
    setSaveErrorMsg('');

    const targetPublished = overridePublished !== null ? overridePublished : isPublished;

    const payload = {
      tagline: tagline.trim(),
      display_name: displayName.trim(),
      category: category.trim(),
      opening_hours: openingHours.trim(),
      welcome_message: welcomeMessage.trim(),
      email: email.trim(),
      phone_number: phoneNumber.trim(),
      website_url: websiteUrl.trim(),
      address: address.trim(),
      map_url: mapUrl.trim(),
      whatsapp_url: whatsappUrl.trim(),
      whatsapp_group_url: whatsappGroupUrl.trim(),
      instagram_url: instagramUrl.trim(),
      facebook_url: facebookUrl.trim(),
      youtube_url: youtubeUrl.trim(),
      logo_path: logoPath.trim(),
      cover_image_path: coverImagePath.trim(),
      background_preset: backgroundPreset.trim(),
      overlay_opacity: Number(overlayOpacity),
      primary_accent: primaryAccent.trim(),
      custom_links: customLinks,
      show_review_button: Boolean(showReviewButton),
      is_published: Boolean(targetPublished),
    };

    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to save business profile.');
      }

      const updated = await res.json();
      setIsPublished(Boolean(updated.is_published));
      setHasUnsavedChanges(false);
      setSaveSuccessMsg(
        overridePublished !== null
          ? overridePublished
            ? '🎉 Business Card published successfully!'
            : '🔒 Business Card unpublished (now private draft).'
          : '✅ Changes saved successfully!'
      );
    } catch (err) {
      setSaveErrorMsg(err.message || 'Could not save changes.');
    } finally {
      setIsSaving(false);
    }
  };

  // ─── 6b. BRAND IMAGE UPLOAD HANDLER (LOGO & COVER) ─────────────────────────
  const handleImageUpload = async (e, imageType) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageUploadError('');
    if (file.size > 5 * 1024 * 1024) {
      setImageUploadError('Image size exceeds 5 MiB maximum limit.');
      return;
    }

    const isLogo = imageType === 'logo';
    if (isLogo) setIsUploadingLogo(true);
    else setIsUploadingCover(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('image_type', imageType);

    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/images`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to upload ${imageType} image.`);
      }

      const data = await res.json();
      if (isLogo) {
        setLogoPath(data.image_url);
      } else {
        setCoverImagePath(data.image_url);
      }
      markDirty();
      setSaveSuccessMsg(`✅ ${isLogo ? 'Logo' : 'Cover photo'} uploaded and saved!`);
    } catch (err) {
      setImageUploadError(err.message || 'Image upload failed.');
    } finally {
      if (isLogo) setIsUploadingLogo(false);
      else setIsUploadingCover(false);
      e.target.value = '';
    }
  };

  // ─── 7. DOCUMENT UPLOAD HANDLER ─────────────────────────────────────────────
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    setUploadError('');
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Invalid file type: Please select a valid PDF file.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File exceeds 10 MiB limit. Please compress your PDF before uploading.');
      return;
    }

    setUploadFile(file);
    if (!uploadDisplayName.trim()) {
      setUploadDisplayName(file.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError('Please select a PDF file first.');
      return;
    }

    setIsUploading(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('document_type', uploadCategory);
    formData.append('display_name', uploadDisplayName.trim() || uploadFile.name);
    formData.append('is_published', 'true');

    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/documents`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to upload document.');
      }

      setUploadFile(null);
      setUploadDisplayName('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      loadDocuments();
      setSaveSuccessMsg('📄 Document uploaded successfully!');
    } catch (err) {
      setUploadError(err.message || 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  // ─── 8. DOCUMENT MUTATIONS (Toggle, Rename, Delete) ─────────────────────────
  const handleToggleDocPublish = async (doc) => {
    const newStatus = !doc.is_published;
    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/documents/${doc.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_published: newStatus }),
      });
      if (res.ok) {
        setDocuments((prev) =>
          prev.map((d) => (d.id === doc.id ? { ...d, is_published: newStatus } : d))
        );
      }
    } catch {
      // Handle error gracefully
    }
  };

  const handleDeleteDoc = async (doc) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${doc.display_name}"? This cannot be undone.`);
    if (!confirmed) return;

    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/documents/${doc.id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
        setSaveSuccessMsg('🗑️ Document deleted.');
      }
    } catch {
      setSaveErrorMsg('Could not delete document.');
    }
  };

  const handleSaveDocRename = async () => {
    if (!editingDocId) return;
    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/documents/${editingDocId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          display_name: editDocName.trim(),
          document_type: editDocCategory,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setDocuments((prev) =>
          prev.map((d) => (d.id === editingDocId ? { ...d, ...updated } : d))
        );
        setEditingDocId(null);
      }
    } catch {
      // Handle error gracefully
    }
  };

  // ─── 9. CUSTOM LINKS MANAGEMENT ─────────────────────────────────────────────
  const handleAddCustomLink = () => {
    if (!newLinkTitle.trim() || !newLinkUrl.trim()) return;
    const formattedUrl = newLinkUrl.trim().startsWith('http')
      ? newLinkUrl.trim()
      : `https://${newLinkUrl.trim()}`;

    setCustomLinks((prev) => [
      ...prev,
      { title: newLinkTitle.trim(), url: formattedUrl, icon: 'link' },
    ]);
    setNewLinkTitle('');
    setNewLinkUrl('');
    markDirty();
  };

  const handleRemoveCustomLink = (index) => {
    setCustomLinks((prev) => prev.filter((_, i) => i !== index));
    markDirty();
  };

  const handleCopyCardUrl = () => {
    navigator.clipboard.writeText(canonicalCardUrl);
    setCardCopiedToast(true);
    setTimeout(() => setCardCopiedToast(false), 3000);
  };

  const handleDownloadCardQr = () => {
    if (!cardQrDataUrl) return;
    const a = document.createElement('a');
    a.href = cardQrDataUrl;
    a.download = `${businessId}-card-qr.png`;
    a.click();
  };

  // ─── 10. AUTH LOADING / LOGIN SCREEN ────────────────────────────────────────
  if (isCheckingSession) {
    return (
      <div className="editor-loading-state">
        <div className="editor-spinner" />
        <span>Checking access credentials...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="owner-login-panel">
        <div className="owner-login-card">
          <div className="login-badge-icon">🪪</div>
          <h1 className="login-card-title">VRAJA AI &bull; Card Studio</h1>
          <p className="login-card-sub">
            Sign in to customize your digital business card, appearance presets, menus, and contact links for{' '}
            <strong>{businessId}</strong>.
          </p>

          {authError && (
            <div className="login-error-msg" role="alert">
              ⚠️ {authError}
            </div>
          )}

          <form onSubmit={handleLogin} className="login-form">
            <div className="login-field">
              <label htmlFor="card-editor-email">Owner Email</label>
              <input
                id="card-editor-email"
                type="email"
                value={ownerEmail}
                onChange={(e) => setOwnerEmail(e.target.value)}
                placeholder="owner@yourbusiness.com"
                autoComplete="email"
                required
              />
            </div>

            <div className="login-field">
              <label htmlFor="card-editor-pass">Password</label>
              <input
                id="card-editor-pass"
                type="password"
                value={ownerPassword}
                onChange={(e) => setOwnerPassword(e.target.value)}
                placeholder="••••••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            <button type="submit" className="login-submit-btn" disabled={isSigningIn}>
              {isSigningIn ? 'Signing in...' : 'Sign In to Card Studio →'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ─── 11. ENTITLEMENT LOCK SCREEN ────────────────────────────────────────────
  if (!hasCardEntitlement) {
    return (
      <div className="editor-lock-panel">
        <div className="editor-lock-card">
          <div className="lock-icon">🔒</div>
          <h2 className="lock-title">Digital Business Card Not Enabled</h2>
          <p className="lock-desc">
            The Digital Business Card module is currently not included in the active subscription
            for <strong>{tenantName}</strong>.
          </p>
          <div className="lock-entitlements-list">
            <span>Active modules: {entitlements.join(', ')}</span>
          </div>
          {onBackToReviews && (
            <button type="button" className="lock-return-btn" onClick={onBackToReviews}>
              ← Return to Review Assistant
            </button>
          )}
        </div>
      </div>
    );
  }

  // Current draft preview data object (synced in real-time with all editor inputs)
  const livePreviewData = {
    tenant_id: businessId,
    business_name: tenantName,
    display_name: displayName || tenantName,
    category: category || '',
    opening_hours: openingHours || '',
    welcome_message: welcomeMessage || '',
    email: email || '',
    tagline,
    logo_path: logoPath,
    cover_image_path: coverImagePath,
    background_preset: backgroundPreset,
    overlay_opacity: overlayOpacity,
    primary_accent: primaryAccent,
    phone_number: phoneNumber,
    website_url: websiteUrl,
    address,
    map_url: mapUrl,
    whatsapp_url: whatsappUrl,
    whatsapp_group_url: whatsappGroupUrl,
    instagram_url: instagramUrl,
    facebook_url: facebookUrl,
    youtube_url: youtubeUrl,
    custom_links: customLinks,
    show_review_button: Boolean(showReviewButton),
    documents: documents.map((d) => ({
      id: d.id,
      document_type: d.document_type,
      display_name: d.display_name,
      file_size_bytes: d.file_size_bytes,
      download_url: d.download_url,
      is_published: d.is_published,
    })),
  };

  return (
    <div className="card-editor-layout">
      {/* Top Header & Publication Bar */}
      <header className="editor-top-bar">
        <div className="editor-title-block">
          <span className="editor-badge">VRAJA AI &bull; Card Studio</span>
          <h1 className="editor-heading">{tenantName}</h1>
        </div>

        <div className="editor-status-actions">
          <div className={`status-pill ${isPublished ? 'published' : 'draft'}`}>
            <span className="status-dot" />
            <span>{isPublished ? 'Published Live' : 'Draft Mode (Hidden)'}</span>
          </div>

          {hasUnsavedChanges && (
            <span className="unsaved-badge" title="You have unsaved changes">
              ● Unsaved
            </span>
          )}

          <button
            type="button"
            className="editor-btn preview"
            onClick={() => {
              if (onPreviewCard) onPreviewCard();
              else setShowLivePreview(true);
            }}
            title="Preview how visitors see your card"
          >
            👁️ Preview
          </button>

          <button
            type="button"
            className="editor-btn save"
            onClick={() => handleSaveProfile()}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : '💾 Save Changes'}
          </button>
        </div>
      </header>

      {/* Notifications */}
      {saveSuccessMsg && (
        <div className="editor-alert success" role="alert">
          {saveSuccessMsg}
        </div>
      )}
      {saveErrorMsg && (
        <div className="editor-alert error" role="alert">
          ⚠️ {saveErrorMsg}
        </div>
      )}

      {/* Responsive Studio Workspace: Left = Form Tabs, Right = Real-Time Device Preview */}
      <div className="card-studio-workspace">
        <div className="card-studio-controls">
          {/* Editor Navigation Tabs */}
          <nav className="editor-nav-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeSection === 'details'}
              className={`editor-tab-btn ${activeSection === 'details' ? 'active' : ''}`}
              onClick={() => setActiveSection('details')}
            >
              <span>🏷️</span>
              <span>1. Identity</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeSection === 'appearance'}
              className={`editor-tab-btn ${activeSection === 'appearance' ? 'active' : ''}`}
              onClick={() => setActiveSection('appearance')}
            >
              <span>🎨</span>
              <span>2. Appearance</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeSection === 'contact'}
              className={`editor-tab-btn ${activeSection === 'contact' ? 'active' : ''}`}
              onClick={() => setActiveSection('contact')}
            >
              <span>📍</span>
              <span>3. Contact</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeSection === 'social'}
              className={`editor-tab-btn ${activeSection === 'social' ? 'active' : ''}`}
              onClick={() => setActiveSection('social')}
            >
              <span>🌐</span>
              <span>4. Social</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeSection === 'documents'}
              className={`editor-tab-btn ${activeSection === 'documents' ? 'active' : ''}`}
              onClick={() => setActiveSection('documents')}
            >
              <span>📑</span>
              <span>5. PDF Menus ({documents.length})</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeSection === 'publish'}
              className={`editor-tab-btn ${activeSection === 'publish' ? 'active' : ''}`}
              onClick={() => setActiveSection('publish')}
            >
              <span>🚀</span>
              <span>6. QR & Publish</span>
            </button>
          </nav>

          {/* Main Tab Content */}
          <main className="editor-main-panel">
            {/* SECTION 1: BUSINESS IDENTITY */}
            {activeSection === 'details' && (
              <section className="editor-section" aria-label="Business details">
                <div className="section-header">
                  <h2>Brand Presentation</h2>
                  <p className="section-sub">
                    Configure your business name, trade category, opening hours, and personal welcome greeting.
                  </p>
                </div>

                <div className="form-group-grid">
                  <div className="form-field">
                    <label htmlFor="card-display-name">Public Business Name</label>
                    <input
                      id="card-display-name"
                      type="text"
                      value={displayName}
                      onChange={(e) => { setDisplayName(e.target.value); markDirty(); }}
                      placeholder={tenantName}
                      maxLength={150}
                    />
                    <span className="field-hint">Displayed prominently at top of your digital card.</span>
                  </div>

                  <div className="form-field">
                    <label htmlFor="card-category">Business Category / Tagline</label>
                    <input
                      id="card-category"
                      type="text"
                      value={category}
                      onChange={(e) => { setCategory(e.target.value); markDirty(); }}
                      placeholder="e.g. Gourmet Dining, Fitness Club, Legal Advisory"
                      maxLength={100}
                    />
                    <span className="field-hint">Defines your service category badge and icon style.</span>
                  </div>
                </div>

                <div className="form-group-grid">
                  <div className="form-field">
                    <label htmlFor="card-opening-hours">Opening / Operating Hours</label>
                    <input
                      id="card-opening-hours"
                      type="text"
                      value={openingHours}
                      onChange={(e) => { setOpeningHours(e.target.value); markDirty(); }}
                      placeholder="e.g. Mon - Sun: 7:00 AM - 11:00 PM"
                      maxLength={150}
                    />
                    <span className="field-hint">Displayed in a prominent hours pill badge.</span>
                  </div>

                  <div className="form-field">
                    <label htmlFor="card-tagline">Short Tagline</label>
                    <input
                      id="card-tagline"
                      type="text"
                      value={tagline}
                      onChange={(e) => { setTagline(e.target.value); markDirty(); }}
                      placeholder="e.g. Pure authentic taste, freshly prepared"
                      maxLength={250}
                    />
                    <span className="field-hint">Used in vCard metadata notes and link shares.</span>
                  </div>
                </div>

                <div className="form-field full-width">
                  <label htmlFor="card-welcome-msg">Personal Welcome Greeting</label>
                  <textarea
                    id="card-welcome-msg"
                    rows={3}
                    value={welcomeMessage}
                    onChange={(e) => { setWelcomeMessage(e.target.value); markDirty(); }}
                    placeholder="e.g. Welcome to our official digital portal! Tap any action below to connect directly with our team."
                    maxLength={1000}
                  />
                  <span className="field-hint">Centered greeting displayed right above your action grid.</span>
                </div>

                <div className="brand-media-block">
                  <h3>Brand Logo</h3>
                  <div className="image-upload-dropzone">
                    <div
                      className="image-preview-thumb"
                      style={{ borderColor: primaryAccent }}
                    >
                      {logoPath ? (
                        <img src={logoPath} alt="Logo preview" className="thumb-img" />
                      ) : (
                        <div className="thumb-placeholder">{businessId.charAt(0).toUpperCase()}</div>
                      )}
                    </div>
                    <div className="upload-input-wrap">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => handleImageUpload(e, 'logo')}
                        disabled={isUploadingLogo}
                        className="file-select-control"
                      />
                      <span className="input-hint">Square format recommended. Max 5 MiB (PNG, JPEG, WebP).</span>
                      <div className="url-fallback-row">
                        <span className="fallback-label">Or URL:</span>
                        <input
                          type="url"
                          value={logoPath}
                          onChange={(e) => { setLogoPath(e.target.value); markDirty(); }}
                          placeholder="https://example.com/logo.png"
                          className="url-fallback-input"
                        />
                      </div>
                    </div>
                  </div>
                  {imageUploadError && <div className="field-error-msg">{imageUploadError}</div>}
                </div>
              </section>
            )}

            {/* SECTION 2: APPEARANCE STUDIO (NEW) */}
            {activeSection === 'appearance' && (
              <section className="editor-section" aria-label="Appearance Studio">
                <div className="section-header">
                  <h2>Background & Appearance Studio</h2>
                  <p className="section-sub">
                    Customize your card's visual identity with curated industry background presets,
                    custom cover photography, dark overlay intensity, and accent colors.
                  </p>
                </div>

                {/* Curated Background Presets */}
                <div className="form-group-block">
                  <div className="block-header">
                    <label className="block-label">Curated Background Presets</label>
                    <span className="block-hint">Professional presets crafted specifically for modern dining, fitness, and services.</span>
                  </div>
                  <div className="presets-grid">
                    {BACKGROUND_PRESETS.map((preset) => {
                      const isSelected = backgroundPreset === preset.id && !coverImagePath;
                      return (
                        <button
                          key={preset.id}
                          type="button"
                          className={`preset-card ${isSelected ? 'selected' : ''}`}
                          onClick={() => {
                            setBackgroundPreset(preset.id);
                            setCoverImagePath('');
                            markDirty();
                          }}
                        >
                          <div
                            className="preset-preview-thumb"
                            style={{ background: preset.previewGradient }}
                          >
                            {isSelected && <span className="preset-check-badge">✓</span>}
                          </div>
                          <div className="preset-meta">
                            <div className="preset-name">{preset.name}</div>
                            <div className="preset-cat">{preset.category}</div>
                            <div className="preset-desc">{preset.description}</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Cover Photo */}
                <div className="form-group-block">
                  <div className="block-header">
                    <label className="block-label">Custom Cover Photo (Optional)</label>
                    <span className="block-hint">Upload your own storefront, interior, or atmosphere photo. Overrides preset when set.</span>
                  </div>

                  <div className="image-upload-dropzone">
                    <div className="image-preview-thumb banner">
                      {coverImagePath ? (
                        <img src={coverImagePath} alt="Cover preview" className="thumb-img" />
                      ) : (
                        <div className="thumb-placeholder">🖼️ No Photo</div>
                      )}
                    </div>

                    <div className="upload-input-wrap">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => handleImageUpload(e, 'cover')}
                        disabled={isUploadingCover}
                        className="file-select-control"
                      />
                      <span className="input-hint">Max 5 MiB (PNG, JPEG, WebP).</span>

                      {coverImagePath && (
                        <button
                          type="button"
                          className="btn-remove-photo"
                          onClick={() => {
                            setCoverImagePath('');
                            markDirty();
                          }}
                        >
                          ✕ Remove Photo (Use Preset)
                        </button>
                      )}

                      <div className="url-fallback-row">
                        <span className="fallback-label">Or Image URL:</span>
                        <input
                          type="url"
                          value={coverImagePath}
                          onChange={(e) => {
                            setCoverImagePath(e.target.value);
                            markDirty();
                          }}
                          placeholder="https://images.unsplash.com/..."
                          className="url-fallback-input"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Dark Overlay Intensity */}
                <div className="form-group-block">
                  <div className="block-header">
                    <div className="slider-label-row">
                      <label className="block-label" htmlFor="overlay-slider">Dark Overlay Intensity</label>
                      <span className="slider-val-badge">{Math.round(overlayOpacity * 100)}%</span>
                    </div>
                    <span className="block-hint">
                      Controls dark gradient intensity over photos to guarantee 100% readable text and high contrast.
                    </span>
                  </div>

                  <div className="slider-control-row">
                    <span className="slider-bound">20% (Light)</span>
                    <input
                      id="overlay-slider"
                      type="range"
                      min="0.20"
                      max="0.95"
                      step="0.05"
                      value={overlayOpacity}
                      onChange={(e) => {
                        setOverlayOpacity(parseFloat(e.target.value));
                        markDirty();
                      }}
                      className="range-slider"
                    />
                    <span className="slider-bound">95% (Deep)</span>
                  </div>
                </div>

                {/* Brand Accent Color */}
                <div className="form-group-block">
                  <div className="block-header">
                    <label className="block-label">Brand Accent Color</label>
                    <span className="block-hint">Applies highlight rings, category badges, and active button glow.</span>
                  </div>

                  <div className="accent-palette-row">
                    {ACCENT_PRESETS.map((acc) => {
                      const isSelected = primaryAccent.toLowerCase() === acc.hex.toLowerCase();
                      return (
                        <button
                          key={acc.id}
                          type="button"
                          className={`accent-swatch-btn ${isSelected ? 'selected' : ''}`}
                          style={{ backgroundColor: acc.hex }}
                          title={acc.label}
                          onClick={() => {
                            setPrimaryAccent(acc.hex);
                            markDirty();
                          }}
                        >
                          {isSelected && <span className="swatch-check">✓</span>}
                        </button>
                      );
                    })}

                    <div className="custom-color-wrap">
                      <input
                        type="color"
                        value={primaryAccent}
                        onChange={(e) => {
                          setPrimaryAccent(e.target.value);
                          markDirty();
                        }}
                        className="accent-color-picker"
                        title="Custom Accent Color"
                      />
                      <span className="accent-color-hex">{primaryAccent.toUpperCase()}</span>
                    </div>
                  </div>
                </div>

                {/* Reset to Professional Default */}
                <div className="form-actions-bar">
                  <button
                    type="button"
                    className="btn-reset-default"
                    onClick={() => {
                      setBackgroundPreset('default_navy');
                      setCoverImagePath('');
                      setOverlayOpacity(0.75);
                      setPrimaryAccent('#078BFF');
                      markDirty();
                    }}
                  >
                    ↺ Reset to VRAJA Default
                  </button>
                </div>
              </section>
            )}

            {/* SECTION 3: CONTACT & LOCATION */}
            {activeSection === 'contact' && (
              <section className="editor-section" aria-label="Contact and maps">
                <div className="section-header">
                  <h2>Direct Contact & Physical Location</h2>
                  <p className="section-sub">
                    Configure your business phone, official email, website, and Google Maps directions link.
                  </p>
                </div>

                <div className="form-group-grid">
                  <div className="form-field">
                    <label htmlFor="card-phone">Business Phone Number</label>
                    <input
                      id="card-phone"
                      type="tel"
                      value={phoneNumber}
                      onChange={(e) => { setPhoneNumber(e.target.value); markDirty(); }}
                      placeholder="e.g. +91 94282 12345"
                      maxLength={25}
                    />
                    <span className="field-hint">Enables 1-tap call button and vCard contact saving.</span>
                  </div>

                  <div className="form-field">
                    <label htmlFor="card-email">Official Email Address</label>
                    <input
                      id="card-email"
                      type="email"
                      value={email}
                      onChange={(e) => { setEmail(e.target.value); markDirty(); }}
                      placeholder="contact@yourbusiness.com"
                      maxLength={256}
                    />
                    <span className="field-hint">Enables direct mailto link on your public card.</span>
                  </div>
                </div>

                <div className="form-field full-width">
                  <label htmlFor="card-website">Official Website URL</label>
                  <input
                    id="card-website"
                    type="url"
                    value={websiteUrl}
                    onChange={(e) => { setWebsiteUrl(e.target.value); markDirty(); }}
                    placeholder="https://www.yourbusiness.com"
                    maxLength={500}
                  />
                  <span className="field-hint">Opens your website in a new secure browser tab.</span>
                </div>

                <div className="form-field full-width">
                  <label htmlFor="card-address">Physical Street Address</label>
                  <textarea
                    id="card-address"
                    rows={2}
                    value={address}
                    onChange={(e) => { setAddress(e.target.value); markDirty(); }}
                    placeholder="e.g. Near Race Course Ground, Rajkot, Gujarat 360001"
                    maxLength={500}
                  />
                  <span className="field-hint">Displayed under your business name with location pin.</span>
                </div>

                <div className="form-field full-width">
                  <label htmlFor="card-map-url">Google Maps / Directions URL</label>
                  <input
                    id="card-map-url"
                    type="url"
                    value={mapUrl}
                    onChange={(e) => { setMapUrl(e.target.value); markDirty(); }}
                    placeholder="https://maps.google.com/?q=..."
                    maxLength={2000}
                  />
                  <span className="field-hint">Powers the 1-tap Google Maps navigation tile.</span>
                </div>
              </section>
            )}

            {/* SECTION 4: SOCIAL & MESSAGING */}
            {activeSection === 'social' && (
              <section className="editor-section" aria-label="Social and messaging links">
                <div className="section-header">
                  <h2>Social & Instant Messaging Channels</h2>
                  <p className="section-sub">
                    Connect customers directly to WhatsApp chat, community channels, and verified social media profiles.
                  </p>
                </div>

                <div className="form-group-grid">
                  <div className="form-field">
                    <label htmlFor="card-whatsapp">WhatsApp Direct Chat Number / Link</label>
                    <input
                      id="card-whatsapp"
                      type="text"
                      value={whatsappUrl}
                      onChange={(e) => { setWhatsappUrl(e.target.value); markDirty(); }}
                      placeholder="e.g. +91 94282 12345 or https://wa.me/919428212345"
                      maxLength={500}
                    />
                    <span className="field-hint">Automatically normalized to secure WhatsApp direct chat.</span>
                  </div>

                  <div className="form-field">
                    <label htmlFor="card-whatsapp-group">WhatsApp Community / Group Invite</label>
                    <input
                      id="card-whatsapp-group"
                      type="url"
                      value={whatsappGroupUrl}
                      onChange={(e) => { setWhatsappGroupUrl(e.target.value); markDirty(); }}
                      placeholder="https://chat.whatsapp.com/..."
                      maxLength={500}
                    />
                    <span className="field-hint">For VIP customer broadcasts or member communities.</span>
                  </div>
                </div>

                <div className="form-group-grid">
                  <div className="form-field">
                    <label htmlFor="card-instagram">Instagram Profile URL</label>
                    <input
                      id="card-instagram"
                      type="url"
                      value={instagramUrl}
                      onChange={(e) => { setInstagramUrl(e.target.value); markDirty(); }}
                      placeholder="https://instagram.com/yourhandle"
                      maxLength={500}
                    />
                  </div>

                  <div className="form-field">
                    <label htmlFor="card-facebook">Facebook Page URL</label>
                    <input
                      id="card-facebook"
                      type="url"
                      value={facebookUrl}
                      onChange={(e) => { setFacebookUrl(e.target.value); markDirty(); }}
                      placeholder="https://facebook.com/yourpage"
                      maxLength={500}
                    />
                  </div>
                </div>

                <div className="form-field full-width">
                  <label htmlFor="card-youtube">YouTube Channel / Video URL</label>
                  <input
                    id="card-youtube"
                    type="url"
                    value={youtubeUrl}
                    onChange={(e) => { setYouTubeUrl(e.target.value); markDirty(); }}
                    placeholder="https://youtube.com/@yourchannel"
                    maxLength={500}
                  />
                </div>

                <div className="custom-links-block">
                  <h3>Custom Links</h3>
                  <p className="custom-links-sub">
                    Add custom destinations such as Table Booking, Event Registration, or Order Online.
                  </p>

                  <div className="custom-links-list">
                    {customLinks.map((link, idx) => (
                      <div key={idx} className="custom-link-row">
                        <span className="link-idx">#{idx + 1}</span>
                        <span className="link-title">{link.title}</span>
                        <span className="link-url-text">{link.url}</span>
                        <button
                          type="button"
                          className="link-delete-btn"
                          onClick={() => handleRemoveCustomLink(idx)}
                          aria-label={`Remove ${link.title}`}
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                    {customLinks.length === 0 && (
                      <div className="empty-links-hint">No custom links added yet.</div>
                    )}
                  </div>

                  <div className="add-link-form">
                    <input
                      type="text"
                      placeholder="Link Title (e.g. Book Table)"
                      value={newLinkTitle}
                      onChange={(e) => setNewLinkTitle(e.target.value)}
                      maxLength={50}
                      className="add-link-title"
                    />
                    <input
                      type="url"
                      placeholder="Destination URL (https://...)"
                      value={newLinkUrl}
                      onChange={(e) => setNewLinkUrl(e.target.value)}
                      maxLength={500}
                      className="add-link-url"
                    />
                    <button
                      type="button"
                      className="add-link-btn"
                      onClick={handleAddCustomLink}
                      disabled={!newLinkTitle.trim() || !newLinkUrl.trim()}
                    >
                      + Add Link
                    </button>
                  </div>
                </div>
              </section>
            )}

            {/* SECTION 5: MENUS & DOCUMENTS */}
            {activeSection === 'documents' && (
              <section className="editor-section" aria-label="Menus and documents">
                <div className="section-header">
                  <h2>Digital Menus, Brochures & Documents</h2>
                  <p className="section-sub">
                    Upload official PDF documents. When configured, your digital card features a dedicated 1-tap Menu button.
                  </p>
                </div>

                <form onSubmit={handleUploadDocument} className="upload-doc-card">
                  <h3 className="upload-title">Upload New Document (PDF)</h3>

                  {uploadError && (
                    <div className="upload-error-msg" role="alert">
                      ⚠️ {uploadError}
                    </div>
                  )}

                  <div className="upload-fields-grid">
                    <div className="form-field">
                      <label htmlFor="doc-upload-file">Select PDF File (Max 10 MiB)</label>
                      <input
                        id="doc-upload-file"
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileSelect}
                        ref={fileInputRef}
                        required
                      />
                    </div>

                    <div className="form-field">
                      <label htmlFor="doc-upload-category">Document Category</label>
                      <select
                        id="doc-upload-category"
                        value={uploadCategory}
                        onChange={(e) => setUploadCategory(e.target.value)}
                      >
                        {DOCUMENT_CATEGORIES.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.icon} {cat.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-field full-width">
                      <label htmlFor="doc-upload-name">Display Name on Card</label>
                      <input
                        id="doc-upload-name"
                        type="text"
                        value={uploadDisplayName}
                        onChange={(e) => setUploadDisplayName(e.target.value)}
                        placeholder="e.g. Tasting Menu 2026, Summer Drink Specials"
                        maxLength={100}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="doc-upload-btn"
                    disabled={isUploading || !uploadFile}
                  >
                    {isUploading ? 'Uploading & Encrypting...' : '📤 Upload & Attach to Card'}
                  </button>
                </form>

                <div className="docs-management-list">
                  <h3>Active Documents ({documents.length})</h3>

                  {isLoadingDocs ? (
                    <div className="docs-loading-hint">Loading documents...</div>
                  ) : documents.length === 0 ? (
                    <div className="empty-docs-box">
                      <span className="empty-docs-icon">📑</span>
                      <p>No PDF documents attached yet. Upload a menu or brochure above.</p>
                    </div>
                  ) : (
                    <div className="doc-cards-grid">
                      {documents.map((doc) => (
                        <div key={doc.id} className="doc-item-card">
                          <div className="doc-item-header">
                            <span className="doc-category-badge">
                              {DOCUMENT_CATEGORIES.find((c) => c.id === doc.document_type)?.icon || '📄'}{' '}
                              {DOCUMENT_CATEGORIES.find((c) => c.id === doc.document_type)?.label || doc.document_type}
                            </span>
                            <div className="doc-actions-cluster">
                              <button
                                type="button"
                                className={`doc-toggle-btn ${doc.is_published ? 'pub' : 'unpub'}`}
                                onClick={() => handleToggleDocPublish(doc)}
                                title={doc.is_published ? 'Click to hide from public card' : 'Click to show on public card'}
                              >
                                {doc.is_published ? 'Live' : 'Hidden'}
                              </button>
                              <button
                                type="button"
                                className="doc-edit-btn"
                                onClick={() => {
                                  setEditingDocId(doc.id);
                                  setEditDocName(doc.display_name);
                                  setEditDocCategory(doc.document_type);
                                }}
                                title="Rename document"
                              >
                                ✏️
                              </button>
                              <button
                                type="button"
                                className="doc-del-btn"
                                onClick={() => handleDeleteDoc(doc)}
                                title="Delete document"
                              >
                                🗑️
                              </button>
                            </div>
                          </div>

                          <div className="doc-item-body">
                            <div className="doc-item-title">{doc.display_name}</div>
                            <div className="doc-item-filename">{doc.original_filename}</div>
                            <div className="doc-item-meta">
                              <span>{formatBytes(doc.file_size_bytes)}</span>
                              <span>&bull;</span>
                              <span>SHA-256: {doc.sha256_hash ? doc.sha256_hash.substring(0, 8) : 'verified'}...</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {editingDocId && (
                  <div className="doc-edit-modal-backdrop" onClick={() => setEditingDocId(null)}>
                    <div className="doc-edit-modal" onClick={(e) => e.stopPropagation()}>
                      <h4>Edit Document Details</h4>
                      <div className="form-field">
                        <label>Display Name</label>
                        <input
                          type="text"
                          value={editDocName}
                          onChange={(e) => setEditDocName(e.target.value)}
                          maxLength={100}
                        />
                      </div>
                      <div className="form-field">
                        <label>Category</label>
                        <select
                          value={editDocCategory}
                          onChange={(e) => setEditDocCategory(e.target.value)}
                        >
                          {DOCUMENT_CATEGORIES.map((cat) => (
                            <option key={cat.id} value={cat.id}>
                              {cat.icon} {cat.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="modal-actions">
                        <button type="button" className="btn-cancel" onClick={() => setEditingDocId(null)}>
                          Cancel
                        </button>
                        <button type="button" className="btn-save-rename" onClick={handleSaveDocRename}>
                          Save Changes
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}

            {/* SECTION 6: QR & PUBLICATION */}
            {activeSection === 'publish' && (
              <section className="editor-section" aria-label="Publish and share card">
                <div className="section-header">
                  <h2>Publication & Brand QR Generator</h2>
                  <p className="section-sub">
                    Control public availability and download customized QR codes for table stands, flyers, and storefronts.
                  </p>
                </div>

                <div className="publish-toggle-box">
                  <div className="publish-toggle-info">
                    <span className="toggle-label">Public Card Status</span>
                    <span className="toggle-sub">
                      {isPublished
                        ? 'Your digital card is live and accessible to anyone via direct link or QR scan.'
                        : 'Your digital card is hidden in draft mode. Visitors will see a private card notice.'}
                    </span>
                  </div>

                  <button
                    type="button"
                    className={`btn-publish-switch ${isPublished ? 'published' : 'draft'}`}
                    onClick={() => {
                      const newStatus = !isPublished;
                      setIsPublished(newStatus);
                      handleSaveProfile(newStatus);
                    }}
                  >
                    {isPublished ? '✓ Published (Click to Unpublish)' : '🚀 Publish Live Now'}
                  </button>
                </div>

                <div className="share-link-box">
                  <label>Canonical Public Card URL</label>
                  <div className="share-link-input-group">
                    <input
                      type="text"
                      readOnly
                      value={canonicalCardUrl}
                      className="share-link-display"
                    />
                    <button
                      type="button"
                      className="share-link-copy-btn"
                      onClick={handleCopyCardUrl}
                    >
                      {cardCopiedToast ? 'Copied! ✓' : '📋 Copy Link'}
                    </button>
                  </div>
                </div>

                <div className="qr-customization-box">
                  <label className="qr-color-label">QR Code Foreground Styling</label>
                  <div className="qr-palette-row">
                    {[
                      { id: 'vnavy', hex: '#061329', label: 'VRAJA Midnight' },
                      { id: 'vblue', hex: '#078BFF', label: 'Electric Blue' },
                      { id: 'vcyan', hex: '#12C8F5', label: 'Electric Cyan' },
                      { id: 'vgold', hex: '#E7BD59', label: 'Champagne Gold' },
                      { id: 'black', hex: '#000000', label: 'Pure Black' },
                    ].map((c) => (
                      <button
                        key={c.id}
                        type="button"
                        className={`qr-swatch-btn ${qrForegroundColor === c.hex ? 'selected' : ''}`}
                        style={{ backgroundColor: c.hex }}
                        title={c.label}
                        onClick={() => setQrForegroundColor(c.hex)}
                      />
                    ))}
                    <div className="custom-color-wrap">
                      <input
                        type="color"
                        value={qrForegroundColor}
                        onChange={(e) => setQrForegroundColor(e.target.value)}
                        className="qr-color-input"
                      />
                      <span className="qr-color-hex">{qrForegroundColor.toUpperCase()}</span>
                    </div>
                  </div>
                </div>

                <div className="qr-render-preview">
                  {cardQrDataUrl ? (
                    <div className="qr-display-frame">
                      <img
                        src={cardQrDataUrl}
                        alt={`QR code for ${businessId}`}
                        className="qr-image"
                      />
                      <button
                        type="button"
                        className="qr-download-btn"
                        onClick={handleDownloadCardQr}
                      >
                        ⬇️ Download High-Res PNG (Print Ready)
                      </button>
                    </div>
                  ) : (
                    <div className="qr-loading-placeholder">Generating QR code...</div>
                  )}
                </div>
              </section>
            )}
          </main>
        </div>

        {/* Real-time Sticky Live Preview Pane (Desktop Split View) */}
        <aside className="card-studio-preview-pane" aria-label="Live card preview">
          <div className="preview-pane-header">
            <span className="preview-pane-title">📱 Live Card Preview</span>
            <span className="preview-pane-pill">Live Sync</span>
          </div>
          <div className="preview-device-shell">
            <DigitalCard
              businessId={businessId}
              isPreview={true}
              previewData={livePreviewData}
            />
          </div>
        </aside>
      </div>

      {/* Floating Preview Modal (For mobile screens or dedicated preview toggle) */}
      {showLivePreview && (
        <div className="editor-preview-modal-backdrop" onClick={() => setShowLivePreview(false)}>
          <div className="editor-preview-modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="editor-preview-modal-header">
              <span className="preview-modal-title">Live Preview &bull; {displayName || tenantName}</span>
              <button
                type="button"
                className="preview-modal-close"
                onClick={() => setShowLivePreview(false)}
              >
                ✕ Close Preview
              </button>
            </div>
            <div className="editor-preview-modal-body">
              <DigitalCard
                businessId={businessId}
                isPreview={true}
                previewData={livePreviewData}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
