import { useEffect } from 'react';
import { AdminButton } from './AdminControls';

/**
 * Standard Enterprise Modal Dialog
 */
export function AdminModal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  maxWidth = '560px',
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="vraja-modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
    >
      <div className="vraja-modal-card" style={{ maxWidth }}>
        <div className="vraja-modal-header">
          <h2 className="vraja-modal-title">{title}</h2>
          <button
            type="button"
            className="vraja-modal-close-btn"
            onClick={onClose}
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        <div className="vraja-modal-body">{children}</div>

        {footer && <div className="vraja-modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

/**
 * High-Stakes Confirmation Dialog
 */
export function AdminConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Critical Action',
  description = 'Are you sure you want to proceed with this operation? This change takes effect immediately across the tenant platform.',
  confirmLabel = 'Confirm & Proceed',
  cancelLabel = 'Cancel',
  isDestructive = true,
  isLoading = false,
}) {
  if (!isOpen) return null;

  return (
    <div className="vraja-modal-overlay" role="alertdialog" aria-modal="true">
      <div className="vraja-modal-card vraja-confirm-dialog">
        <div className="vraja-confirm-icon-wrap">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>

        <h3 className="vraja-confirm-title">{title}</h3>
        <p className="vraja-confirm-desc">{description}</p>

        <div className="vraja-confirm-actions">
          <AdminButton
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelLabel}
          </AdminButton>
          <AdminButton
            variant={isDestructive ? 'danger' : 'primary'}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Processing…' : confirmLabel}
          </AdminButton>
        </div>
      </div>
    </div>
  );
}
