/**
 * Reusable Admin Notification and Feedback Banner
 */

export function AdminNotification({
  type = 'info', // success, warning, error, info
  title,
  message,
  onClose,
  className = '',
}) {
  const icons = {
    success: '✓',
    warning: '⚠',
    error: '✕',
    info: 'ℹ',
  };

  return (
    <div className={`vraja-notification ${type} ${className}`.trim()} role="alert">
      <span
        style={{
          width: '20px',
          height: '20px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: 'bold',
          flexShrink: 0,
        }}
      >
        {icons[type] || 'ℹ'}
      </span>

      <div style={{ flex: 1 }}>
        {title && <div style={{ fontWeight: 600, marginBottom: '2px' }}>{title}</div>}
        <div>{message}</div>
      </div>

      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="vraja-notification-close"
          aria-label="Dismiss notification"
        >
          ✕
        </button>
      )}
    </div>
  );
}

export default AdminNotification;
