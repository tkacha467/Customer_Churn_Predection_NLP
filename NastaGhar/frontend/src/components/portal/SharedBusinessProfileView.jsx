import { useState, useEffect, useRef, useCallback } from 'react';
import { usePortalSession } from './PortalSessionContext';
import { apiFetch } from '../../lib/api';

const COMMON_TIMEZONES = [
  { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST +5:30)' },
  { value: 'Asia/Dubai', label: 'Asia/Dubai (GST +4:00)' },
  { value: 'Asia/Singapore', label: 'Asia/Singapore (SGT +8:00)' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST +9:00)' },
  { value: 'Europe/London', label: 'Europe/London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Europe/Paris (CET +1:00)' },
  { value: 'America/New_York', label: 'America/New_York (EST/EDT)' },
  { value: 'America/Chicago', label: 'America/Chicago (CST/CDT)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT)' },
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
];

const PRESET_ACCENTS = [
  '#174D3A', // Deep Emerald
  '#C6A66B', // Muted Gold
  '#078BFF', // Royal Blue
  '#F97316', // Sunset Orange
  '#D94841', // Crimson
  '#6366F1', // Indigo
  '#0D9488', // Teal
  '#26352D', // Charcoal
];

export function SharedBusinessProfileView() {
  const {
    activeTenant,
    user,
    sharedProfile,
    updateSharedProfileState,
  } = usePortalSession();

  const businessId = activeTenant?.id || 'default_business';
  const isOwnerOrAdmin = activeTenant?.role === 'owner' || !!user?.is_platform_admin;
  const isReadOnly = !isOwnerOrAdmin;

  // Form state
  const [displayName, setDisplayName] = useState('');
  const [category, setCategory] = useState('');
  const [branchName, setBranchName] = useState('');
  const [description, setDescription] = useState('');
  const [tagline, setTagline] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [address, setAddress] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [openingHours, setOpeningHours] = useState('');
  const [mapUrl, setMapUrl] = useState('');
  const [brandAccent, setBrandAccent] = useState('#174D3A');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [logoPath, setLogoPath] = useState('');

  // UI state
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState('');
  const [saveError, setSaveError] = useState('');

  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [logoSuccess, setLogoSuccess] = useState('');
  const [logoError, setLogoError] = useState('');
  const [logoTimestamp, setLogoTimestamp] = useState(Date.now());

  const fileInputRef = useRef(null);

  // Initialize form state from sharedProfile
  const populateFields = useCallback((profile) => {
    if (!profile) return;
    setDisplayName(profile.display_name || '');
    setCategory(profile.category || '');
    setBranchName(profile.branch_name || '');
    setDescription(profile.description || '');
    setTagline(profile.tagline || '');
    setPhoneNumber(profile.phone_number || '');
    setEmail(profile.email || '');
    setAddress(profile.address || '');
    setWebsiteUrl(profile.website_url || '');
    setOpeningHours(profile.opening_hours || '');
    setMapUrl(profile.map_url || '');
    setBrandAccent(profile.brand_accent || '#174D3A');
    setTimezone(profile.timezone || 'Asia/Kolkata');
    setLogoPath(profile.logo_path || '');
  }, []);

  useEffect(() => {
    // Only populate if form is not dirty (prevents clobbering unsaved edits)
    if (!isDirty && sharedProfile) {
      populateFields(sharedProfile);
    }
  }, [sharedProfile, isDirty, populateFields]);

  // Handle text field changes
  const handleFieldChange = (setter) => (e) => {
    setter(e.target.value);
    setIsDirty(true);
    setSaveSuccess('');
    setSaveError('');
  };

  // Save profile updates
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (isReadOnly) return;

    if (!displayName.trim()) {
      setSaveError('Business display name is required.');
      return;
    }

    setIsSaving(true);
    setSaveSuccess('');
    setSaveError('');

    try {
      const payload = {
        display_name: displayName.trim(),
        category: category.trim(),
        branch_name: branchName.trim(),
        description: description.trim(),
        tagline: tagline.trim(),
        phone_number: phoneNumber.trim(),
        email: email.trim(),
        address: address.trim(),
        website_url: websiteUrl.trim(),
        opening_hours: openingHours.trim(),
        map_url: mapUrl.trim(),
        brand_accent: brandAccent.trim() || null,
        timezone: timezone.trim() || 'Asia/Kolkata',
      };

      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/shared-profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to save shared profile.');
      }

      const updated = await res.json();
      updateSharedProfileState(updated);
      populateFields(updated);
      setIsDirty(false);
      setSaveSuccess('Shared profile saved and synchronized across all active products.');
    } catch (err) {
      setSaveError(err.message || 'An unexpected error occurred while saving.');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle Logo Upload
  const handleLogoFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Client-side validations
    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setLogoError('Supported formats: PNG, JPEG, or WebP. SVG/executable images are rejected.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setLogoError('Logo image exceeds maximum allowed size of 5 MiB.');
      return;
    }

    setIsUploadingLogo(true);
    setLogoSuccess('');
    setLogoError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/shared-profile/logo`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to upload shared business logo.');
      }

      const data = await res.json();
      setLogoPath(data.logo_path);
      setLogoTimestamp(Date.now());
      setLogoSuccess(`Logo updated successfully (${data.dimensions?.width}×${data.dimensions?.height}px).`);

      // Update context profile
      if (sharedProfile) {
        updateSharedProfileState({
          ...sharedProfile,
          logo_path: data.logo_path,
        });
      }
    } catch (err) {
      setLogoError(err.message || 'Error uploading business logo.');
    } finally {
      setIsUploadingLogo(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const activeLogoEndpoint = `/api/businesses/${encodeURIComponent(businessId)}/shared-profile/logo?t=${logoTimestamp}`;

  return (
    <div className="vraja-portal-view-container">
      {/* Top Header & Save Actions */}
      <div className="vraja-view-header-with-actions">
        <div className="header-info">
          <h1 className="vraja-view-title">Shared Business Profile</h1>
          <p className="vraja-view-subtitle">
            Authoritative common business identity across Google Review Manager and Digital Business Card.
          </p>
        </div>

        <div className="header-actions">
          {isDirty && <span className="vraja-dirty-pill">● Unsaved Changes</span>}

          {!isReadOnly && (
            <button
              type="button"
              className="vraja-save-profile-btn"
              onClick={handleSaveProfile}
              disabled={isSaving || !isDirty}
            >
              {isSaving ? (
                <>
                  <span className="btn-spinner" />
                  <span>Saving...</span>
                </>
              ) : (
                'Save Profile Changes'
              )}
            </button>
          )}
        </div>
      </div>

      {/* Read-Only Mode Banner */}
      {isReadOnly && (
        <div className="vraja-readonly-notice" role="alert">
          <span className="notice-icon">🔒</span>
          <div className="notice-content">
            <strong>Read-Only Mode:</strong> Signed in as <em>{activeTenant?.role?.toUpperCase()}</em>.
            Only Owners and Platform Administrators can modify common business profile fields and upload logos.
          </div>
        </div>
      )}

      {/* Alerts */}
      {saveSuccess && (
        <div className="vraja-portal-alert success" role="status">
          ✓ {saveSuccess}
        </div>
      )}
      {saveError && (
        <div className="vraja-portal-alert error" role="alert">
          ⚠️ {saveError}
        </div>
      )}

      <form onSubmit={handleSaveProfile} className="vraja-profile-grid-form">
        {/* -------------------------------------------------------------
         * Section 1: Shared Logo Management
         * ----------------------------------------------------------- */}
        <div className="vraja-profile-section-card logo-card">
          <div className="section-header">
            <span className="section-icon">🖼️</span>
            <div>
              <h3 className="section-title">Shared Business Logo</h3>
              <p className="section-desc">Uploaded once, consumed by both Product A and Product B.</p>
            </div>
          </div>

          <div className="logo-management-block">
            <div className="logo-preview-box">
              {logoPath ? (
                <img
                  src={activeLogoEndpoint}
                  alt="Business Logo"
                  className="current-logo-img"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    if (e.currentTarget.nextElementSibling) {
                      e.currentTarget.nextElementSibling.style.display = 'flex';
                    }
                  }}
                />
              ) : null}
              <div className="fallback-logo-emblem" style={{ display: logoPath ? 'none' : 'flex' }}>
                🏢
              </div>
            </div>

            <div className="logo-upload-controls">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                style={{ display: 'none' }}
                onChange={handleLogoFileSelect}
                disabled={isReadOnly || isUploadingLogo}
              />

              {!isReadOnly && (
                <button
                  type="button"
                  className="vraja-upload-logo-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploadingLogo}
                >
                  {isUploadingLogo ? (
                    <>
                      <span className="btn-spinner dark" />
                      <span>Uploading Logo...</span>
                    </>
                  ) : (
                    'Upload New Logo'
                  )}
                </button>
              )}

              <span className="logo-help-text">
                Supports PNG, JPEG, WebP (max 5 MiB, up to 4096×4096px). SVG is strictly rejected for security.
              </span>

              {logoSuccess && <div className="logo-feedback success">✓ {logoSuccess}</div>}
              {logoError && <div className="logo-feedback error">⚠️ {logoError}</div>}
            </div>
          </div>
        </div>

        {/* -------------------------------------------------------------
         * Section 2: Business Core Identity
         * ----------------------------------------------------------- */}
        <div className="vraja-profile-section-card">
          <div className="section-header">
            <span className="section-icon">🏢</span>
            <div>
              <h3 className="section-title">Business Identity</h3>
              <p className="section-desc">Essential business identification and presentation details.</p>
            </div>
          </div>

          <div className="form-fields-grid">
            <div className="field-group full-width">
              <label htmlFor="display_name">
                Business Display Name <span className="req">*</span>
              </label>
              <input
                id="display_name"
                type="text"
                value={displayName}
                onChange={handleFieldChange(setDisplayName)}
                placeholder="e.g. Nasta Ghar"
                disabled={isReadOnly || isSaving}
                maxLength={150}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="category">Business Category</label>
              <input
                id="category"
                type="text"
                value={category}
                onChange={handleFieldChange(setCategory)}
                placeholder="e.g. Authentic Gujarati Dining"
                disabled={isReadOnly || isSaving}
                maxLength={100}
              />
            </div>

            <div className="field-group">
              <label htmlFor="branch_name">Branch / Location Name</label>
              <input
                id="branch_name"
                type="text"
                value={branchName}
                onChange={handleFieldChange(setBranchName)}
                placeholder="e.g. Navrangpura Branch"
                disabled={isReadOnly || isSaving}
                maxLength={100}
              />
            </div>

            <div className="field-group full-width">
              <label htmlFor="tagline">Tagline / Slogan</label>
              <input
                id="tagline"
                type="text"
                value={tagline}
                onChange={handleFieldChange(setTagline)}
                placeholder="e.g. Pure authentic taste, freshly prepared daily"
                disabled={isReadOnly || isSaving}
                maxLength={300}
              />
            </div>

            <div className="field-group full-width">
              <label htmlFor="description">About / Bio Description</label>
              <textarea
                id="description"
                rows={3}
                value={description}
                onChange={handleFieldChange(setDescription)}
                placeholder="Describe your dining experience, specialties, or brand mission..."
                disabled={isReadOnly || isSaving}
                maxLength={5000}
              />
            </div>
          </div>
        </div>

        {/* -------------------------------------------------------------
         * Section 3: Contact Coordinates
         * ----------------------------------------------------------- */}
        <div className="vraja-profile-section-card">
          <div className="section-header">
            <span className="section-icon">📞</span>
            <div>
              <h3 className="section-title">Contact Information</h3>
              <p className="section-desc">Public communication channels shared across digital touchpoints.</p>
            </div>
          </div>

          <div className="form-fields-grid">
            <div className="field-group">
              <label htmlFor="phone_number">Public Phone Number</label>
              <input
                id="phone_number"
                type="tel"
                value={phoneNumber}
                onChange={handleFieldChange(setPhoneNumber)}
                placeholder="e.g. +91 98765 43210"
                disabled={isReadOnly || isSaving}
                maxLength={40}
              />
            </div>

            <div className="field-group">
              <label htmlFor="email">Public Contact Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={handleFieldChange(setEmail)}
                placeholder="e.g. contact@nastaghar.com"
                disabled={isReadOnly || isSaving}
                maxLength={255}
              />
            </div>

            <div className="field-group full-width">
              <label htmlFor="website_url">Official Website URL</label>
              <input
                id="website_url"
                type="url"
                value={websiteUrl}
                onChange={handleFieldChange(setWebsiteUrl)}
                placeholder="e.g. https://www.nastaghar.com"
                disabled={isReadOnly || isSaving}
                maxLength={500}
              />
            </div>
          </div>
        </div>

        {/* -------------------------------------------------------------
         * Section 4: Location & Operating Hours
         * ----------------------------------------------------------- */}
        <div className="vraja-profile-section-card">
          <div className="section-header">
            <span className="section-icon">📍</span>
            <div>
              <h3 className="section-title">Location & Operating Hours</h3>
              <p className="section-desc">Physical store coordinates and working schedule.</p>
            </div>
          </div>

          <div className="form-fields-grid">
            <div className="field-group full-width">
              <label htmlFor="address">Physical Street Address</label>
              <textarea
                id="address"
                rows={2}
                value={address}
                onChange={handleFieldChange(setAddress)}
                placeholder="e.g. Shop 4, Heritage Plaza, Navrangpura, Ahmedabad, Gujarat 380009"
                disabled={isReadOnly || isSaving}
                maxLength={500}
              />
            </div>

            <div className="field-group">
              <label htmlFor="map_url">Google Maps / Directions Link</label>
              <input
                id="map_url"
                type="url"
                value={mapUrl}
                onChange={handleFieldChange(setMapUrl)}
                placeholder="e.g. https://maps.google.com/?cid=..."
                disabled={isReadOnly || isSaving}
                maxLength={500}
              />
            </div>

            <div className="field-group">
              <label htmlFor="opening_hours">Operating Hours</label>
              <input
                id="opening_hours"
                type="text"
                value={openingHours}
                onChange={handleFieldChange(setOpeningHours)}
                placeholder="e.g. Mon - Sun: 07:00 AM - 11:00 PM"
                disabled={isReadOnly || isSaving}
                maxLength={250}
              />
            </div>
          </div>
        </div>

        {/* -------------------------------------------------------------
         * Section 5: Brand Styling & Timezone
         * ----------------------------------------------------------- */}
        <div className="vraja-profile-section-card">
          <div className="section-header">
            <span className="section-icon">🎨</span>
            <div>
              <h3 className="section-title">Branding Accent & Timezone</h3>
              <p className="section-desc">Canonical brand color and analytics reporting timezone.</p>
            </div>
          </div>

          <div className="form-fields-grid">
            <div className="field-group">
              <label htmlFor="brand_accent">Brand Accent Color</label>
              <div className="color-picker-row">
                <input
                  id="brand_accent_picker"
                  type="color"
                  value={brandAccent || '#174D3A'}
                  onChange={handleFieldChange(setBrandAccent)}
                  disabled={isReadOnly || isSaving}
                  className="color-input"
                />
                <input
                  id="brand_accent"
                  type="text"
                  value={brandAccent || ''}
                  onChange={handleFieldChange(setBrandAccent)}
                  placeholder="#174D3A"
                  disabled={isReadOnly || isSaving}
                  maxLength={7}
                  className="hex-input"
                />
              </div>
              <div className="preset-swatches">
                {PRESET_ACCENTS.map((hex) => (
                  <button
                    key={hex}
                    type="button"
                    className="swatch-btn"
                    style={{ backgroundColor: hex }}
                    onClick={() => {
                      if (!isReadOnly) {
                        setBrandAccent(hex);
                        setIsDirty(true);
                      }
                    }}
                    title={hex}
                  />
                ))}
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="timezone">Operational Timezone</label>
              <select
                id="timezone"
                value={timezone}
                onChange={handleFieldChange(setTimezone)}
                disabled={isReadOnly || isSaving}
              >
                {COMMON_TIMEZONES.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
              <span className="field-hint">
                All hourly review charts and private feedback timestamps calculate in this timezone.
              </span>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

export default SharedBusinessProfileView;
