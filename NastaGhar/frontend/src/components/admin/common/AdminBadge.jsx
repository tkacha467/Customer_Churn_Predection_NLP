/**
 * Reusable Status Badges and Pills
 */

export function AdminBadge({
  children,
  variant = 'neutral', // success, warning, critical, neutral, gold
  dot = false,
  className = '',
}) {
  const variantClass = `vraja-badge-${variant}`;
  return (
    <span className={`vraja-badge ${variantClass} ${className}`.trim()}>
      {dot && <span className="vraja-badge-dot" />}
      {children}
    </span>
  );
}

export function StatusBadge({ status }) {
  const norm = String(status || '').toLowerCase();
  if (norm === 'active' || norm === 'published' || norm === 'resolved') {
    return (
      <AdminBadge variant="success" dot>
        Active
      </AdminBadge>
    );
  }
  if (norm === 'suspended' || norm === 'revoked' || norm === 'critical') {
    return (
      <AdminBadge variant="critical" dot>
        Suspended
      </AdminBadge>
    );
  }
  if (norm === 'escalated' || norm === 'warning' || norm === 'pending') {
    return (
      <AdminBadge variant="warning" dot>
        Escalated
      </AdminBadge>
    );
  }
  return (
    <AdminBadge variant="neutral" dot>
      {status || 'Unknown'}
    </AdminBadge>
  );
}

export function EntitlementBadge({ entitlement }) {
  if (entitlement === 'review_manager') {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '11.5px',
          fontWeight: 600,
          backgroundColor: '#E8F5EE',
          color: '#1D7A4D',
          border: '1px solid #BFE4CE',
        }}
      >
        ★ Review Assistant
      </span>
    );
  }
  if (entitlement === 'digital_card') {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '11.5px',
          fontWeight: 600,
          backgroundColor: '#F7F3E9',
          color: '#8C6A2C',
          border: '1px solid #EDD9B1',
        }}
      >
        🪪 Digital Card
      </span>
    );
  }
  return (
    <AdminBadge variant="neutral">
      {entitlement}
    </AdminBadge>
  );
}
