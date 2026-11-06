/**
 * Reusable Content Card Component
 */

export function AdminCard({
  title,
  subtitle,
  actions,
  children,
  footer,
  className = '',
  bodyStyle = {},
}) {
  const hasHeader = Boolean(title || subtitle || actions);

  return (
    <div className={`vraja-card ${className}`.trim()}>
      {hasHeader && (
        <div className="vraja-card-header">
          <div className="vraja-card-title-group">
            {title && <h3 className="vraja-card-title">{title}</h3>}
            {subtitle && <p className="vraja-card-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="vraja-card-actions">{actions}</div>}
        </div>
      )}
      <div className="vraja-card-body" style={bodyStyle}>
        {children}
      </div>
      {footer && <div className="vraja-card-footer">{footer}</div>}
    </div>
  );
}

export default AdminCard;
