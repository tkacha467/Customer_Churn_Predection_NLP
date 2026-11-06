/**
 * Reusable KPI Metric Card Component
 */

export function AdminKpi({
  label,
  value,
  trend,
  trendDirection = 'positive', // positive, negative, neutral
  subtext,
  icon,
  goldIcon = false,
  className = '',
}) {
  return (
    <div className={`vraja-kpi-card ${className}`.trim()}>
      <div className="vraja-kpi-top">
        <span className="vraja-kpi-label">{label}</span>
        {icon && (
          <div className={`vraja-kpi-icon-wrap ${goldIcon ? 'gold' : ''}`}>
            {icon}
          </div>
        )}
      </div>

      <div className="vraja-kpi-value-row">
        <div className="vraja-kpi-value">{value}</div>
        {trend && (
          <span className={`vraja-kpi-trend ${trendDirection}`}>
            {trendDirection === 'positive' && '▲ '}
            {trendDirection === 'negative' && '▼ '}
            {trend}
          </span>
        )}
      </div>

      {subtext && <div className="vraja-kpi-subtext">{subtext}</div>}
    </div>
  );
}

export default AdminKpi;
