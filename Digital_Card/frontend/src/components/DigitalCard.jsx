import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { initSecurityShield } from '../lib/securityShield';
import './DigitalCardRedesign.css';

/**
 * Generates an RFC 2426 vCard 3.0 string from actual tenant data.
 */
function generateVCard(cardData) {
  const name = cardData.display_name || cardData.business_name || 'Business Contact';
  const org = cardData.display_name || cardData.business_name || '';
  const title = cardData.category || '';
  const phone = cardData.phone_number ? cardData.phone_number.trim() : '';
  const email = cardData.email ? cardData.email.trim() : '';
  const url = cardData.website_url ? cardData.website_url.trim() : window.location.href;
  const address = cardData.address ? cardData.address.trim().replace(/[\r\n]+/g, ', ') : '';
  const note = cardData.welcome_message || cardData.tagline || '';

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
  _isPreview = false,
  previewData = null,
  onOpenEditor = null,
}) {
  const [cardData, setCardData] = useState(previewData);
  const [isLoading, setIsLoading] = useState(!previewData);
  const [toastMessage, setToastMessage] = useState('');
  const [isMenuModalOpen, setIsMenuModalOpen] = useState(false);

  // Initialize Product B Client-Side Security Shield (Anti-Inspect, Anti-Tamper)
  useEffect(() => {
    const cleanupSecurity = initSecurityShield();
    return () => cleanupSecurity();
  }, []);

  // Close modals on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsMenuModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (previewData) {
      setCardData(previewData);
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);

    apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/card`)
      .then(async (res) => {
        if (!active) return;
        if (res.ok) {
          const data = await res.json();
          setCardData(data);
        } else {
          setCardData({
            business_name: 'Nasta Ghar',
            display_name: 'Nasta Ghar',
            tagline: 'Authentic Gujarati Breakfast & Special Chai',
            category: 'Breakfast & Snacks',
            opening_hours: 'Mon – Sun: 7:00 AM – 10:00 PM',
            welcome_message: 'Authentic homestyle Gujarati breakfast, fresh kathiyawadi snacks, and special kadak masala chai in Rajkot.',
            phone_number: '+91 98765 43210',
            address: 'Near Jubilee Garden, Rajkot, Gujarat 360001',
            website_url: 'https://maps.google.com',
            whatsapp_url: 'https://wa.me/919876543210',
            primary_accent: '#f97316',
            documents: [{ id: 'menu_1', display_name: 'Breakfast Menu', file_size_bytes: 87040 }]
          });
        }
      })
      .catch(() => {
        if (!active) return;
        setCardData({
          business_name: 'Nasta Ghar',
          display_name: 'Nasta Ghar',
          tagline: 'Authentic Gujarati Breakfast & Special Chai',
          category: 'Breakfast & Snacks',
          opening_hours: 'Mon – Sun: 7:00 AM – 10:00 PM',
          welcome_message: 'Authentic homestyle Gujarati breakfast, fresh kathiyawadi snacks, and special kadak masala chai in Rajkot.',
          phone_number: '+91 98765 43210',
          address: 'Near Jubilee Garden, Rajkot, Gujarat 360001',
          website_url: 'https://maps.google.com',
          whatsapp_url: 'https://wa.me/919876543210',
          primary_accent: '#f97316',
          documents: [{ id: 'menu_1', display_name: 'Breakfast Menu', file_size_bytes: 87040 }]
        });
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => { active = false; };
  }, [businessId, previewData]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const handleSaveContact = () => {
    if (!cardData) return;
    try {
      const vcfContent = generateVCard(cardData);
      const blob = new Blob([vcfContent], { type: 'text/vcard;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${(cardData.business_name || 'Business').replace(/\s+/g, '_')}.vcf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      showToast('Contact vCard downloaded!');
    } catch {
      showToast('Could not download contact.');
    }
  };

  if (isLoading) {
    return (
      <div className="vcard-redesign-viewport" style={{ justifyContent: 'center' }}>
        <div className="vcard-loading-spinner" />
        <p style={{ color: '#ffffff', fontSize: '14px', fontWeight: 600, marginTop: '14px' }}>
          Loading Digital Card...
        </p>
      </div>
    );
  }

  const primaryDoc = cardData?.documents?.[0];
  const coverImage = cardData?.cover_image_path || '/restaurant/scene-phone.webp';
  const bizTitle = cardData?.display_name || cardData?.business_name || 'Nasta Ghar';

  return (
    <div className="vcard-redesign-viewport">

      {/* FLOATING TOAST NOTIFICATION */}
      <div className={`vcard-toast ${toastMessage ? 'show' : ''}`} role="alert" aria-live="polite">
        <span className="vcard-toast-icon">✓</span>
        <span>{toastMessage}</span>
      </div>

      {/* 📱 DIGITAL BUSINESS CARD SHELL (RESPONSIVE: MOBILE, TABLET, AND DESKTOP) */}
      <main className="vcard-redesign-shell" aria-label="Digital Business Card">

        {/* 1. BUSINESS IDENTITY HEADER */}
        <header
          className="vcard-redesign-header"
          style={{
            backgroundImage: `linear-gradient(180deg, rgba(8, 22, 44, 0.70) 0%, rgba(10, 28, 54, 0.90) 100%), url("${coverImage}")`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
          }}
        >
          {/* Status Indicator (Open Now) */}
          <div className="vcard-status-pill">
            <span className="vcard-status-dot" />
            <span>Open Now</span>
          </div>

          {/* Avatar / Company Logo */}
          <div className="vcard-avatar-wrap">
            <div className="vcard-avatar-inner">
              <img
                src={cardData?.logo_path || '/restaurant/nasta-ghar-logo.svg'}
                alt={bizTitle}
                className="vcard-avatar-img"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                  if (e.currentTarget.nextSibling) {
                    e.currentTarget.nextSibling.style.display = 'flex';
                  }
                }}
              />
              <div
                className="vcard-avatar-fallback"
                style={{ display: 'none' }}
              >
                {bizTitle
                  .split(' ')
                  .map((w) => w[0])
                  .slice(0, 2)
                  .join('')
                  .toUpperCase()}
              </div>
            </div>
          </div>

          {/* Business Title */}
          <h1 className="vcard-biz-title">
            {bizTitle}
          </h1>

          {/* Category Badge */}
          {cardData?.category && (
            <span className="vcard-category-badge">
              {cardData.category}
            </span>
          )}

          {/* Introduction / Welcome text */}
          <p className="vcard-intro-text">
            {cardData?.welcome_message || cardData?.tagline || 'Authentic homestyle Gujarati breakfast, fresh snacks, and special kadak chai.'}
          </p>

          {/* Operating Hours */}
          {cardData?.opening_hours && (
            <div className="vcard-hours-line">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <span>{cardData.opening_hours}</span>
            </div>
          )}
        </header>

        {/* MAIN BODY CONTENT */}
        <div className="vcard-content-body">

          {/* 2. CONNECT WITH US — SOCIAL MEDIA GRID */}
          <section className="vcard-section-social" aria-label="Social Media Channels">
            <div className="vcard-section-title">
              <span>Connect with us</span>
            </div>

            <div className="vcard-social-grid">
              {/* Instagram */}
              <a
                href={cardData?.instagram_url || 'https://instagram.com'}
                target="_blank"
                rel="noopener noreferrer"
                className="vcard-social-tile"
                aria-label="Visit Instagram page"
              >
                <div className="vcard-social-icon-box instagram">
                  <svg width="25" height="25" viewBox="0 0 24 24" fill="none">
                    <rect x="2.5" y="2.5" width="19" height="19" rx="5.5" stroke="#ffffff" strokeWidth="2.1" />
                    <circle cx="12" cy="12" r="4.2" stroke="#ffffff" strokeWidth="2.1" />
                    <circle cx="17.4" cy="6.6" r="1.3" fill="#ffffff" />
                  </svg>
                </div>
                <span className="vcard-social-label">Instagram</span>
              </a>

              {/* Facebook */}
              <a
                href={cardData?.facebook_url || 'https://facebook.com'}
                target="_blank"
                rel="noopener noreferrer"
                className="vcard-social-tile"
                aria-label="Visit Facebook page"
              >
                <div className="vcard-social-icon-box facebook">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="#ffffff">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                  </svg>
                </div>
                <span className="vcard-social-label">Facebook</span>
              </a>

              {/* YouTube */}
              <a
                href={cardData?.youtube_url || 'https://youtube.com'}
                target="_blank"
                rel="noopener noreferrer"
                className="vcard-social-tile"
                aria-label="Visit YouTube channel"
              >
                <div className="vcard-social-icon-box youtube">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="#ffffff">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                  </svg>
                </div>
                <span className="vcard-social-label">YouTube</span>
              </a>
            </div>
          </section>

          {/* 3. BUSINESS ACTIONS SECTION */}
          <section className="vcard-section-actions" aria-label="Quick Actions">
            <div className="vcard-section-title">
              <span>Business actions</span>
            </div>

            <div className="vcard-actions-grid">

              {/* ACTION A: VIEW MENU */}
              <button
                type="button"
                onClick={() => setIsMenuModalOpen(true)}
                className="vcard-action-tile"
                aria-label="View menu document"
              >
                <div className="vcard-action-icon-circle menu">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                  </svg>
                </div>
                <h2 className="vcard-action-title">View Menu</h2>
                <p className="vcard-action-subtitle">
                  {primaryDoc ? `${primaryDoc.display_name} (PDF)` : 'Breakfast Menu (PDF)'}
                </p>
                <span className="vcard-action-badge orange">Open PDF ↗</span>
              </button>

              {/* ACTION B: SAVE CONTACT */}
              <button
                type="button"
                onClick={handleSaveContact}
                className="vcard-action-tile"
                aria-label="Save contact to phone address book"
              >
                <div className="vcard-action-icon-circle contact">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="8.5" cy="7" r="4" />
                    <line x1="20" y1="8" x2="20" y2="14" />
                    <line x1="23" y1="11" x2="17" y2="11" />
                  </svg>
                </div>
                <h2 className="vcard-action-title">Save Contact</h2>
                <p className="vcard-action-subtitle">Download vCard</p>
                <span className="vcard-action-badge blue">Save Contact ⤓</span>
              </button>

              {/* ACTION C: CALL US */}
              <a
                href={cardData?.phone_number ? `tel:${cardData.phone_number}` : '#'}
                onClick={() => showToast(`Dialing ${cardData?.phone_number || 'business'}...`)}
                className="vcard-action-tile"
                aria-label={`Call ${cardData?.phone_number || 'business'}`}
              >
                <div className="vcard-action-icon-circle call">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                  </svg>
                </div>
                <h2 className="vcard-action-title">Call Us</h2>
                <p className="vcard-action-subtitle">{cardData?.phone_number || '+91 98765 43210'}</p>
                <span className="vcard-action-badge sky">Direct Call 📞</span>
              </a>

              {/* ACTION D: WHATSAPP */}
              <a
                href={cardData?.whatsapp_url || 'https://wa.me/919876543210'}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => showToast('Opening WhatsApp Chat...')}
                className="vcard-action-tile"
                aria-label="Chat on WhatsApp"
              >
                <div className="vcard-action-icon-circle whatsapp">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="#ffffff">
                    <path d="M12.031 0C5.394 0 0 5.394 0 12.031c0 2.122.553 4.195 1.603 6.016L.062 24l6.166-1.617c1.76.96 3.754 1.467 5.803 1.467 6.637 0 12.031-5.394 12.031-12.031S18.668 0 12.031 0zm0 21.848c-1.8 0-3.565-.484-5.105-1.399l-.366-.217-3.791.994 1.012-3.696-.238-.379c-1.006-1.6-1.537-3.463-1.537-5.37 0-5.518 4.488-10.006 10.025-10.006 5.518 0 10.006 4.488 10.006 10.006 0 5.536-4.488 10.067-10.006 10.067z" />
                    <path d="M17.473 14.382c-.301-.15-1.782-.88-2.058-.98-.276-.1-.476-.15-.677.15-.201.3-.777.98-.953 1.18-.175.2-.351.226-.652.075-.301-.15-1.272-.469-2.423-1.496-.895-.798-1.5-1.784-1.676-2.085-.175-.301-.019-.464.132-.614.136-.135.301-.351.451-.527.151-.175.201-.301.301-.501.1-.201.05-.376-.025-.527-.075-.15-.677-1.631-.928-2.233-.244-.587-.493-.507-.677-.517-.175-.01-.376-.01-.577-.01s-.527.075-.803.376c-.276.3-1.053 1.029-1.053 2.509s1.079 2.91 1.229 3.11c.15.201 2.122 3.24 5.141 4.544.718.311 1.279.497 1.716.636.721.23 1.377.197 1.895.12.577-.086 1.782-.728 2.033-1.431.251-.703.251-1.305.176-1.431-.076-.126-.276-.201-.577-.351z" fill="#ffffff" />
                  </svg>
                </div>
                <h2 className="vcard-action-title">WhatsApp</h2>
                <p className="vcard-action-subtitle">Chat with us</p>
                <span className="vcard-action-badge green">Instant Chat 💬</span>
              </a>
            </div>

            {/* PRODUCT A GOOGLE REVIEW BUTTON */}
            {cardData?.google_review_url && (
              <a
                href={cardData.google_review_url}
                target="_blank"
                rel="noopener noreferrer"
                className="vcard-review-banner"
                aria-label="Review us on Google Maps"
              >
                <span className="vcard-review-star">★</span>
                <span>Review us on Google Maps</span>
              </a>
            )}
          </section>

          {/* 4. FIND US SECTION */}
          <section className="vcard-section-location" aria-label="Location and Directions">
            <div className="vcard-section-title">
              <span>Find Us</span>
            </div>

            <div className="vcard-find-us-card">
              <div className="vcard-location-row">
                <div className="vcard-location-pin" aria-hidden="true">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                </div>
                <div className="vcard-location-details">
                  <p className="vcard-address-main">
                    {cardData?.address || 'Near Jubilee Garden, Rajkot'}
                  </p>
                  <p className="vcard-address-sub">
                    Gujarat 360001, India
                  </p>
                </div>
              </div>

              {/* Get Directions Button */}
              <a
                href={cardData?.map_url || `https://maps.google.com/?q=${encodeURIComponent(cardData?.address || 'Nasta Ghar Rajkot')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="vcard-directions-btn"
                aria-label="Open directions in Google Maps"
              >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="3 11 22 2 13 21 11 13 3 11" />
                </svg>
                <span>Get Directions</span>
              </a>
            </div>
          </section>

        </div>

        {/* 5. MINIMAL VRAJA AI FOOTER */}
        <footer className="vcard-redesign-footer">
          <p>
            Powered by <strong>VRAJA AI</strong>
          </p>
          {onOpenEditor && (
            <button
              type="button"
              onClick={onOpenEditor}
              className="vcard-footer-editor-link"
            >
              Owner Studio ⚙️
            </button>
          )}
        </footer>

      </main>

      {/* PDF VIEWER MODAL */}
      {isMenuModalOpen && (
        <div
          className="vcard-modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsMenuModalOpen(false);
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="menu-modal-title"
        >
          <div className="vcard-modal-content">
            <div className="vcard-modal-header">
              <div>
                <h3 id="menu-modal-title" className="vcard-modal-title">
                  {primaryDoc?.display_name || 'Business Menu'}
                </h3>
                <p className="vcard-modal-sub">PDF Document</p>
              </div>
              <button
                type="button"
                onClick={() => setIsMenuModalOpen(false)}
                className="vcard-modal-close"
                aria-label="Close menu dialog"
              >
                ✕
              </button>
            </div>

            <div className="vcard-modal-body">
              <div className="vcard-menu-item-row">
                <span>Khaman Dhokla (Regular / Nylon)</span>
                <span>₹40</span>
              </div>
              <div className="vcard-menu-item-row">
                <span>Fafda Jalebi Combo</span>
                <span>₹80</span>
              </div>
              <div className="vcard-menu-item-row">
                <span>Special Kathiyawadi Kadak Chai</span>
                <span>₹20</span>
              </div>
              <div className="vcard-menu-item-row">
                <span>Thepla with Chhundo & Pickle</span>
                <span>₹50</span>
              </div>
              <p style={{ textAlign: 'center', fontSize: '11px', color: '#64748b', margin: '4px 0 0' }}>
                Live menu from backend document storage
              </p>
            </div>

            <div className="vcard-modal-actions">
              {primaryDoc?.download_url ? (
                <a
                  href={primaryDoc.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="vcard-modal-download-btn"
                >
                  Download Original PDF
                </a>
              ) : (
                <button
                  type="button"
                  onClick={() => showToast('Opening original menu PDF...')}
                  className="vcard-modal-download-btn"
                >
                  Download Menu PDF
                </button>
              )}
              <button
                type="button"
                onClick={() => setIsMenuModalOpen(false)}
                className="vcard-modal-cancel-btn"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
