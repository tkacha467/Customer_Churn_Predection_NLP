import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { getHeaderBackgroundStyle } from '../lib/appearancePresets';

/**
 * Format bytes to readable string (e.g. 1.2 MB, 450 KB).
 */
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function isNonEmptyString(val) {
  return typeof val === 'string' && val.trim().length > 0;
}

function isValidPhone(val) {
  if (!val || typeof val !== 'string') return false;
  const digits = val.replace(/[^\d+]/g, '');
  return digits.length >= 5;
}

function isValidEmail(val) {
  if (!val || typeof val !== 'string') return false;
  const s = val.trim().toLowerCase();
  return s.length >= 5 && s.includes('@') && s.includes('.') && !s.includes(' ');
}

function isValidUrl(val) {
  if (!val || typeof val !== 'string') return false;
  const s = val.trim().toLowerCase();
  return s.startsWith('http://') || s.startsWith('https://');
}

function normalizeUrl(val) {
  if (!val || typeof val !== 'string') return '';
  const s = val.trim();
  if (s.startsWith('http://') || s.startsWith('https://')) return s;
  return `https://${s}`;
}

function normalizeWhatsAppUrl(val) {
  if (!val || typeof val !== 'string') return '';
  const s = val.trim();
  if (s.startsWith('http://') || s.startsWith('https://')) return s;
  const digits = s.replace(/[^\d]/g, '');
  return digits.length >= 7 ? `https://wa.me/${digits}` : '';
}

/**
 * Generates an RFC 2426 vCard 3.0 string from actual tenant data.
 */
function generateVCard(cardData) {
  const name = cardData.display_name || cardData.business_name || 'Business Contact';
  const org = cardData.display_name || cardData.business_name || '';
  const title = cardData.category || '';
  const phone = isNonEmptyString(cardData.phone_number) ? cardData.phone_number.trim() : '';
  const email = isNonEmptyString(cardData.email) ? cardData.email.trim() : '';
  const url = isNonEmptyString(cardData.website_url) ? normalizeUrl(cardData.website_url) : window.location.href;
  const address = isNonEmptyString(cardData.address) ? cardData.address.trim().replace(/[\r\n]+/g, ', ') : '';
  const note = isNonEmptyString(cardData.welcome_message)
    ? cardData.welcome_message.trim()
    : isNonEmptyString(cardData.tagline)
      ? cardData.tagline.trim()
      : '';

  const lines = [
    'BEGIN:VCARD',
    'VERSION:3.0',
    `FN;CHARSET=UTF-8:${name}`,
    `ORG;CHARSET=UTF-8:${org}`,
  ];
  if (title) lines.push(`TITLE;CHARSET=UTF-8:${title}`);
  if (phone) lines.push(`TEL;TYPE=WORK,VOICE:${phone}`);
  if (email) lines.push(`EMAIL;TYPE=WORK:${email}`);
  if (url) lines.push(`URL;TYPE=WORK:${url}`);
  if (address) lines.push(`ADR;TYPE=WORK:;;${address};;;;`);
  if (note) lines.push(`NOTE;CHARSET=UTF-8:${note.replace(/[\r\n]+/g, ' ')}`);
  lines.push('END:VCARD');

  return lines.join('\r\n');
}

export default function DigitalCard({
  businessId = 'default_business',
  isPreview = false,
  previewData = null,
  onOpenEditor = null,
  onSwitchToEditor = null,
}) {
  const [cardData, setCardData] = useState(previewData);
  const [isLoading, setIsLoading] = useState(!previewData);
  const [notFound, setNotFound] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [toastMessage, setToastMessage] = useState('');
  const [isDocsModalOpen, setIsDocsModalOpen] = useState(false);

  const openEditorHandler = onOpenEditor || onSwitchToEditor;

  useEffect(() => {
    if (previewData) {
      setCardData(previewData);
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);
    setNotFound(false);
    setErrorMessage('');

    const endpoint = isPreview
      ? `/api/businesses/${encodeURIComponent(businessId)}/profile`
      : `/api/businesses/${encodeURIComponent(businessId)}/card`;

    apiFetch(endpoint)
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          const data = await res.json();
          if (isPreview) {
            try {
              const [docsRes, tenantRes] = await Promise.all([
                apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/documents`),
                apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/review-link`),
              ]);
              const docs = docsRes.ok ? await docsRes.json() : [];
              const tenant = tenantRes.ok ? await tenantRes.json() : {};
              if (!data.display_name && tenant.business_name) {
                data.business_name = tenant.business_name;
              } else if (data.display_name) {
                data.business_name = data.display_name;
              }
              if (!data.category && tenant.category) {
                data.category = tenant.category;
              }
              data.primary_accent = data.primary_accent || tenant.primary_accent || '#078BFF';
              data.google_review_url = tenant.review_url || '';
              data.documents = docs.map((d) => ({
                id: d.id,
                document_type: d.document_type,
                display_name: d.display_name,
                file_size_bytes: d.file_size_bytes,
                download_url: d.download_url || `/api/businesses/${encodeURIComponent(businessId)}/documents/${d.id}/file`,
                is_published: d.is_published,
              }));
            } catch {
              // fallback gracefully
            }
          }
          setCardData(data);
        } else if (res.status === 404 || res.status === 403) {
          setNotFound(true);
        } else {
          const err = await res.json().catch(() => ({}));
          setErrorMessage(err.detail || 'Could not load business card.');
        }
      })
      .catch(() => {
        if (active) setErrorMessage('Network connection error. Please refresh.');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => { active = false; };
  }, [businessId, isPreview, previewData]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const handleSaveContact = () => {
    if (!cardData) return;
    try {
      const vcfContent = generateVCard(cardData);
      const blob = new Blob([vcfContent], { type: 'text/vcard;charset=utf-8' });
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      const rawName = cardData.display_name || cardData.business_name || 'contact';
      const safeFilename = rawName.toLowerCase().replace(/[^a-z0-9_-]+/g, '_');
      link.download = `${safeFilename}.vcf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);
      showToast('📇 Contact card downloaded');
    } catch (err) {
      console.error('Failed generating vCard:', err);
      showToast('❌ Could not save contact');
    }
  };

  const handleShare = async () => {
    const cardUrl = `${window.location.origin}/b/${encodeURIComponent(businessId)}/card`;
    const shareTitle = cardData?.display_name || cardData?.business_name || 'Digital Business Card';
    const shareText = cardData?.welcome_message || cardData?.tagline || `Check out ${shareTitle}!`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          url: cardUrl,
        });
        return;
      } catch (err) {
        if (err.name === 'AbortError') return;
      }
    }

    try {
      await navigator.clipboard.writeText(cardUrl);
      showToast('✅ Link copied to clipboard!');
    } catch {
      showToast('Could not copy link');
    }
  };

  // ─── LOADING STATE ──────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="vcard-app-viewport">
        <div className="vcard-phone-shell">
          <div className="vcard-skeleton-header">
            <div className="vcard-skeleton-avatar" />
            <div className="vcard-skeleton-text-group">
              <div className="vcard-skeleton-line short" />
              <div className="vcard-skeleton-line" />
              <div className="vcard-skeleton-line small" />
            </div>
          </div>
          <div className="vcard-skeleton-body">
            <div className="vcard-skeleton-line center" />
            <div className="vcard-skeleton-pill" />
            <div className="vcard-skeleton-grid">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="vcard-skeleton-tile" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ─── NOT FOUND / UNPUBLISHED STATE ──────────────────────────────────────────
  if (notFound || !cardData) {
    return (
      <div className="vcard-app-viewport">
        <div className="vcard-phone-shell">
          <div className="vcard-empty-panel">
            <div className="vcard-empty-icon">🪪</div>
            <h1 className="vcard-empty-title">Business Card Not Available</h1>
            <p className="vcard-empty-desc">
              The digital business card for <strong>{businessId}</strong> is either unpublished,
              does not exist, or digital card features have not been activated.
            </p>
            {openEditorHandler && (
              <button
                type="button"
                className="vcard-empty-btn"
                onClick={openEditorHandler}
              >
                ✏️ Open Owner Editor
              </button>
            )}
            <div className="vcard-empty-footer">
              <span>Powered by VRAJA AI</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="vcard-app-viewport">
        <div className="vcard-phone-shell">
          <div className="vcard-empty-panel">
            <div className="vcard-empty-icon">⚠️</div>
            <h2 className="vcard-empty-title">Could Not Load Card</h2>
            <p className="vcard-empty-desc">{errorMessage}</p>
            <button
              type="button"
              className="vcard-empty-btn"
              onClick={() => window.location.reload()}
            >
              🔄 Refresh Page
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract tenant fields strictly from data (no reference defaults)
  const businessName = cardData.display_name || cardData.business_name || businessId || 'Business Card';
  const category = (cardData.category || '').trim();
  const address = (cardData.address || '').trim();
  const phone = (cardData.phone_number || '').trim();
  const email = (cardData.email || '').trim();
  const website = (cardData.website_url || '').trim();
  const mapUrl = (cardData.map_url || '').trim();
  const whatsappUrl = (cardData.whatsapp_url || '').trim();
  const whatsappGroupUrl = (cardData.whatsapp_group_url || '').trim();
  const instagramUrl = (cardData.instagram_url || '').trim();
  const facebookUrl = (cardData.facebook_url || '').trim();
  const youtubeUrl = (cardData.youtube_url || '').trim();
  const openingHours = (cardData.opening_hours || '').trim();
  const welcomeMessage = (cardData.welcome_message || '').trim();

  // Appearance fields
  const primaryAccent = cardData.primary_accent || '#078BFF';
  const coverImagePath = cardData.cover_image_path || '/restaurant/scene-phone.webp';
  const backgroundPreset = cardData.background_preset || 'default_navy';
  const overlayOpacity = typeof cardData.overlay_opacity === 'number' ? cardData.overlay_opacity : 0.75;

  // Compute dynamic hero background style
  const headerStyle = getHeaderBackgroundStyle(coverImagePath, backgroundPreset, overlayOpacity);

  // Published Documents
  const rawDocs = Array.isArray(cardData.documents) ? cardData.documents : [];
  const publishedDocs = isPreview ? rawDocs : rawDocs.filter((d) => d.is_published !== false);
  const primaryDoc = publishedDocs.length > 0 ? publishedDocs[0] : null;

  // Review URL destination
  const reviewDestination = isNonEmptyString(cardData.google_review_url)
    ? normalizeUrl(cardData.google_review_url)
    : '';
  const showReviewAction = Boolean(cardData.show_review_button) && Boolean(reviewDestination);

  // WhatsApp normalized URL
  const validWhatsAppChatUrl = normalizeWhatsAppUrl(whatsappUrl);

  const handleMenuClick = () => {
    if (publishedDocs.length === 1 && primaryDoc?.download_url) {
      window.open(primaryDoc.download_url, '_blank', 'noopener,noreferrer');
    } else if (publishedDocs.length > 1) {
      setIsDocsModalOpen(true);
    }
  };

  // Document metadata formatting
  const categoryLower = category.toLowerCase();
  const isFoodBiz = /restaurant|cafe|bistro|dining|food|snack|bakery|bar|kitchen/.test(categoryLower);

  let docLabel = 'Document';
  let docColorClass = 'pdf-red';
  if (primaryDoc) {
    const docType = (primaryDoc.document_type || '').toLowerCase();
    if (docType.includes('menu') || (isFoodBiz && !docType.includes('brochure') && !docType.includes('catalogue'))) {
      docLabel = (primaryDoc.display_name && primaryDoc.display_name.length <= 14) ? primaryDoc.display_name : 'Menu';
      docColorClass = 'pdf-red';
    } else if (docType === 'brochure') {
      docLabel = (primaryDoc.display_name && primaryDoc.display_name.length <= 14) ? primaryDoc.display_name : 'Brochure';
      docColorClass = 'doc-purple';
    } else if (docType === 'catalogue') {
      docLabel = (primaryDoc.display_name && primaryDoc.display_name.length <= 14) ? primaryDoc.display_name : 'Catalogue';
      docColorClass = 'doc-cyan';
    } else {
      docLabel = (primaryDoc.display_name && primaryDoc.display_name.length <= 14) ? primaryDoc.display_name : 'Document';
      docColorClass = 'pdf-red';
    }
  }
  const multiDocLabel = isFoodBiz ? 'Menus & Docs' : 'Documents';

  // ─── DYNAMIC ACTIONS ARRAY (Render only valid, configured actions) ───────────
  const actions = [];

  // 1. Save Contact: only if contact info exists
  if (phone || email || address || website) {
    actions.push({
      id: 'save_contact',
      label: 'Save Contact',
      type: 'button',
      onClick: handleSaveContact,
      colorClass: 'contact-blue',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-icon-svg">
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="8.5" cy="7" r="4" />
          <line x1="20" y1="8" x2="20" y2="14" />
          <line x1="23" y1="11" x2="17" y2="11" />
        </svg>
      ),
      ariaLabel: 'Save contact to phone',
    });
  }

  // 2. Call: only if phone is valid
  if (isValidPhone(phone)) {
    actions.push({
      id: 'call',
      label: 'Call',
      type: 'link',
      href: `tel:${phone}`,
      colorClass: 'phone-green',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-icon-svg">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
        </svg>
      ),
      ariaLabel: `Call ${phone}`,
    });
  }

  // 3. WhatsApp Direct Chat: only if whatsappUrl is valid
  if (validWhatsAppChatUrl) {
    actions.push({
      id: 'whatsapp_chat',
      label: 'WhatsApp',
      type: 'link',
      href: validWhatsAppChatUrl,
      colorClass: 'whatsapp-green',
      icon: (
        <svg viewBox="0 0 24 24" fill="#ffffff" className="vcard-icon-svg">
          <path d="M12.031 0C5.394 0 0 5.394 0 12.031c0 2.122.553 4.195 1.603 6.016L.062 24l6.166-1.617c1.76.96 3.754 1.467 5.803 1.467 6.637 0 12.031-5.394 12.031-12.031S18.668 0 12.031 0zm0 21.848c-1.8 0-3.565-.484-5.105-1.399l-.366-.217-3.791.994 1.012-3.696-.238-.379c-1.006-1.6-1.537-3.463-1.537-5.37 0-5.518 4.488-10.006 10.025-10.006 5.518 0 10.006 4.488 10.006 10.006 0 5.536-4.488 10.067-10.006 10.067z" />
        </svg>
      ),
      ariaLabel: 'Chat on WhatsApp',
    });
  }

  // 4. WhatsApp Group / Community: only if whatsappGroupUrl is valid
  if (isValidUrl(whatsappGroupUrl)) {
    actions.push({
      id: 'whatsapp_group',
      label: 'WhatsApp Group',
      type: 'link',
      href: whatsappGroupUrl,
      colorClass: 'whatsapp-group-teal',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" className="vcard-icon-svg">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      ),
      ariaLabel: 'Join WhatsApp Group or Community',
    });
  }

  // 5. Email: only if valid email
  if (isValidEmail(email)) {
    actions.push({
      id: 'email',
      label: 'Email',
      type: 'link',
      href: `mailto:${email}`,
      colorClass: 'email-red',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-icon-svg">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
          <polyline points="22,6 12,13 2,6" />
        </svg>
      ),
      ariaLabel: `Send email to ${email}`,
    });
  }

  // 6. Website: only if valid website
  if (isValidUrl(website)) {
    actions.push({
      id: 'website',
      label: 'Website',
      type: 'link',
      href: normalizeUrl(website),
      colorClass: 'website-blue',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-icon-svg">
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      ),
      ariaLabel: 'Visit website',
    });
  }

  // 7. Review Us: only if showReviewAction is true and reviewDestination is valid
  if (showReviewAction) {
    actions.push({
      id: 'review_us',
      label: 'Review Us',
      type: 'link',
      href: reviewDestination,
      colorClass: 'google-blue',
      icon: (
        <svg viewBox="0 0 24 24" fill="currentColor" className="vcard-icon-svg">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z" />
        </svg>
      ),
      ariaLabel: 'Review us on Google',
    });
  }

  // 8. Documents (Menu / Brochure / Catalog / Docs): only if publishedDocs exist
  if (publishedDocs.length > 0) {
    actions.push({
      id: 'document',
      label: publishedDocs.length === 1 ? docLabel : multiDocLabel,
      type: 'button',
      onClick: handleMenuClick,
      colorClass: publishedDocs.length === 1 ? docColorClass : 'doc-slate',
      icon: (
        <svg viewBox="0 0 24 24" fill="currentColor" className="vcard-icon-svg">
          {publishedDocs.length === 1 && docColorClass === 'pdf-red' ? (
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 9h-2v1h2a1 1 0 0 1 0 2h-2v2H9v-7h4a1.5 1.5 0 0 1 0 3zm5 5h-3.5v-7H18a1.5 1.5 0 0 1 0 3h-1.5v1H18a1 1 0 0 1 0 2v1zm-5-14 5 5h-5V2z" />
          ) : (
            <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z" />
          )}
        </svg>
      ),
      ariaLabel: publishedDocs.length === 1 ? `Open ${docLabel}` : 'View documents',
    });
  }

  // 9. Instagram: only if valid instagramUrl
  if (isValidUrl(instagramUrl)) {
    actions.push({
      id: 'instagram',
      label: 'Instagram',
      type: 'link',
      href: normalizeUrl(instagramUrl),
      colorClass: 'instagram-gradient',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="vcard-icon-svg">
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
          <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
          <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
        </svg>
      ),
      ariaLabel: 'Open Instagram profile',
    });
  }

  // 10. Facebook: only if valid facebookUrl
  if (isValidUrl(facebookUrl)) {
    actions.push({
      id: 'facebook',
      label: 'Facebook',
      type: 'link',
      href: normalizeUrl(facebookUrl),
      colorClass: 'facebook-blue',
      icon: (
        <svg viewBox="0 0 24 24" fill="#ffffff" className="vcard-icon-svg">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
        </svg>
      ),
      ariaLabel: 'Open Facebook page',
    });
  }

  // 11. YouTube: only if valid youtubeUrl
  if (isValidUrl(youtubeUrl)) {
    actions.push({
      id: 'youtube',
      label: 'YouTube',
      type: 'link',
      href: normalizeUrl(youtubeUrl),
      colorClass: 'youtube-red',
      icon: (
        <svg viewBox="0 0 24 24" fill="#ffffff" className="vcard-icon-svg">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
      ),
      ariaLabel: 'Open YouTube channel',
    });
  }

  // 12. Google Maps: only if valid mapUrl
  if (isValidUrl(mapUrl)) {
    actions.push({
      id: 'map',
      label: 'Google Maps',
      type: 'link',
      href: normalizeUrl(mapUrl),
      colorClass: 'maps-color',
      icon: (
        <svg viewBox="0 0 24 24" fill="#ea4335" className="vcard-icon-svg">
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z" />
        </svg>
      ),
      ariaLabel: 'Open directions in Google Maps',
    });
  }

  // 13. Custom Links: valid custom links only
  if (Array.isArray(cardData.custom_links)) {
    cardData.custom_links.forEach((link, idx) => {
      if (isNonEmptyString(link?.title) && isValidUrl(link?.url)) {
        actions.push({
          id: `custom_${idx}`,
          label: link.title.trim(),
          type: 'link',
          href: normalizeUrl(link.url),
          colorClass: 'custom-gold',
          icon: <span className="vcard-custom-symbol">🔗</span>,
          ariaLabel: link.title.trim(),
        });
      }
    });
  }

  // ─── DYNAMIC BOTTOM DOCK (Call, WhatsApp, Email, Website) ───────────────────
  const dockActions = [];

  if (isValidPhone(phone)) {
    dockActions.push({
      id: 'dock_call',
      label: 'Call',
      href: `tel:${phone}`,
      colorClass: 'dock-green',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-dock-svg">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
        </svg>
      ),
      ariaLabel: 'Call business',
    });
  }

  if (validWhatsAppChatUrl) {
    dockActions.push({
      id: 'dock_whatsapp',
      label: 'WhatsApp',
      href: validWhatsAppChatUrl,
      colorClass: 'dock-whatsapp',
      icon: (
        <svg viewBox="0 0 24 24" fill="#ffffff" className="vcard-dock-svg">
          <path d="M12.031 0C5.394 0 0 5.394 0 12.031c0 2.122.553 4.195 1.603 6.016L.062 24l6.166-1.617c1.76.96 3.754 1.467 5.803 1.467 6.637 0 12.031-5.394 12.031-12.031S18.668 0 12.031 0zm0 21.848c-1.8 0-3.565-.484-5.105-1.399l-.366-.217-3.791.994 1.012-3.696-.238-.379c-1.006-1.6-1.537-3.463-1.537-5.37 0-5.518 4.488-10.006 10.025-10.006 5.518 0 10.006 4.488 10.006 10.006 0 5.536-4.488 10.067-10.006 10.067z" />
        </svg>
      ),
      ariaLabel: 'Chat on WhatsApp',
    });
  }

  if (isValidEmail(email)) {
    dockActions.push({
      id: 'dock_email',
      label: 'Email',
      href: `mailto:${email}`,
      colorClass: 'dock-email',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-dock-svg">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
          <polyline points="22,6 12,13 2,6" />
        </svg>
      ),
      ariaLabel: 'Send email',
    });
  }

  if (isValidUrl(website)) {
    dockActions.push({
      id: 'dock_website',
      label: 'Website',
      href: normalizeUrl(website),
      colorClass: 'dock-web',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="vcard-dock-svg">
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      ),
      ariaLabel: 'Visit website',
    });
  }

  const gridCountClass = `vcard-grid-count-${Math.min(actions.length, 6)}`;
  const shellHasDock = dockActions.length > 0;

  return (
    <div className="vcard-app-viewport">
      {isPreview && (
        <div className="vcard-preview-ribbon">
          <span className="vcard-preview-badge">👁️ Owner Preview Mode</span>
          {openEditorHandler && (
            <button
              type="button"
              className="vcard-preview-btn"
              onClick={openEditorHandler}
            >
              ✏️ Editor
            </button>
          )}
        </div>
      )}

      {toastMessage && (
        <div className="vcard-toast" role="status" aria-live="polite">
          {toastMessage}
        </div>
      )}

      {/* Main Single-Page Shell with VRAJA Deep Navy & Electric Identity */}
      <main className={`vcard-phone-shell ${shellHasDock ? 'has-dock' : 'no-dock'}`}>
        {/* 1. HERO HEADER WITH CUSTOMIZABLE BACKGROUND & OVERLAY */}
        <header
          className="vcard-header"
          style={headerStyle}
        >
          <div className="vcard-header-top">
            {/* Circular Logo Badge with Tenant Accent Ring */}
            <div
              className="vcard-logo-ring"
              style={{
                borderColor: primaryAccent,
                boxShadow: `0 0 16px ${primaryAccent}40, 0 4px 14px rgba(0, 0, 0, 0.45)`,
              }}
            >
              {cardData.logo_path ? (
                <img
                  src={cardData.logo_path}
                  alt={`${businessName} logo`}
                  className="vcard-logo-img"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    if (e.currentTarget.nextSibling) {
                      e.currentTarget.nextSibling.style.display = 'flex';
                    }
                  }}
                />
              ) : null}
              <div
                className="vcard-logo-fallback"
                style={{
                  display: cardData.logo_path ? 'none' : 'flex',
                  color: primaryAccent,
                }}
              >
                {businessName.charAt(0).toUpperCase()}
              </div>
            </div>

            {/* Business Identity */}
            <div className="vcard-identity">
              <h1 className="vcard-business-name">{businessName}</h1>
              {category && (
                <span
                  className="vcard-category-tag"
                  style={{
                    color: primaryAccent,
                    borderColor: `${primaryAccent}4d`,
                    background: `${primaryAccent}1a`,
                  }}
                >
                  {category.toUpperCase()}
                </span>
              )}
              {address && (
                <div className="vcard-address-row">
                  <span className="vcard-pin-icon" aria-hidden="true" style={{ color: primaryAccent }}>📍</span>
                  <span className="vcard-address-text">{address}</span>
                </div>
              )}
            </div>

            {/* Quick Share Top Button */}
            <button
              type="button"
              className="vcard-share-btn"
              onClick={handleShare}
              aria-label="Share card"
              title="Share or copy card link"
            >
              ↗
            </button>
          </div>
        </header>

        {/* 2. LAYERED DEEP NAVY CONTENT PANEL WITH CURVED HEADER TRANSITION */}
        <section className="vcard-content-panel">
          {/* Centered Welcome Message / Tagline */}
          {welcomeMessage && (
            <p className="vcard-welcome-message">{welcomeMessage}</p>
          )}

          {/* Opening-Hours Strip (if set by tenant) */}
          {openingHours && (
            <div className="vcard-hours-pill" aria-label="Operating hours">
              <span className="vcard-hours-icon" aria-hidden="true">🕒</span>
              <span className="vcard-hours-text">{openingHours}</span>
            </div>
          )}

          {/* 3. DYNAMICALLY BALANCED GRID OF BUSINESS ACTIONS */}
          {actions.length > 0 ? (
            <div
              className={`vcard-action-grid ${gridCountClass}`}
              data-count={actions.length}
              role="region"
              aria-label="Business Actions"
            >
              {actions.map((act) => {
                if (act.type === 'link') {
                  return (
                    <a
                      key={act.id}
                      href={act.href}
                      target={act.href.startsWith('http') ? '_blank' : undefined}
                      rel={act.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                      className="vcard-grid-tile"
                      aria-label={act.ariaLabel || act.label}
                    >
                      <div className={`vcard-tile-icon-box ${act.colorClass}`}>
                        {act.icon}
                      </div>
                      <span className="vcard-tile-label">{act.label}</span>
                    </a>
                  );
                }
                return (
                  <button
                    key={act.id}
                    type="button"
                    className="vcard-grid-tile"
                    onClick={act.onClick}
                    aria-label={act.ariaLabel || act.label}
                  >
                    <div className={`vcard-tile-icon-box ${act.colorClass}`}>
                      {act.icon}
                    </div>
                    <span className="vcard-tile-label">{act.label}</span>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="vcard-no-actions-panel">
              <span className="vcard-no-actions-icon">✨</span>
              <p className="vcard-no-actions-text">Connect with us on our verified channels.</p>
            </div>
          )}
        </section>

        {/* 4. FIXED BOTTOM ACTION RIBBON (Call, WhatsApp, Email, Website) */}
        <nav className="vcard-bottom-ribbon" aria-label="Quick Contact Dock">
          {dockActions.length > 0 && (
            <div className={`vcard-dock-actions vcard-dock-count-${dockActions.length}`}>
              {dockActions.map((dock) => (
                <a
                  key={dock.id}
                  href={dock.href}
                  target={dock.href.startsWith('http') ? '_blank' : undefined}
                  rel={dock.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="vcard-dock-item"
                  aria-label={dock.ariaLabel}
                >
                  <div className={`vcard-dock-circle ${dock.colorClass}`}>
                    {dock.icon}
                  </div>
                  <span className="vcard-dock-label">{dock.label}</span>
                </a>
              ))}
            </div>
          )}

          {/* Platform Branding */}
          <div className="vcard-dock-footer">
            <span>Powered by VRAJA AI</span>
          </div>
        </nav>
      </main>

      {/* MODAL FOR MULTIPLE DOCUMENTS (IF PRESENT) */}
      {isDocsModalOpen && (
        <div className="vcard-modal-backdrop" onClick={() => setIsDocsModalOpen(false)}>
          <div className="vcard-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="vcard-modal-header">
              <h3 className="vcard-modal-title">Documents & Catalogues</h3>
              <button
                type="button"
                className="vcard-modal-close"
                onClick={() => setIsDocsModalOpen(false)}
              >
                ✕
              </button>
            </div>
            <div className="vcard-modal-list">
              {publishedDocs.map((doc) => (
                <a
                  key={doc.id}
                  href={doc.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="vcard-modal-doc-item"
                >
                  <div className="vcard-modal-doc-icon">📄</div>
                  <div className="vcard-modal-doc-info">
                    <div className="vcard-modal-doc-name">{doc.display_name}</div>
                    <div className="vcard-modal-doc-size">{formatBytes(doc.file_size_bytes)} • PDF</div>
                  </div>
                  <span className="vcard-modal-doc-download">View →</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
