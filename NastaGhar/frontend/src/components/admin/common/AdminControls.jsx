/**
 * Reusable Admin Controls: Buttons, TextInputs, SelectDropdowns, and Segmented Filters
 */

export function AdminButton({
  children,
  variant = 'primary', // primary, secondary, outline, gold, danger
  size = 'md',        // sm, md, lg
  icon = null,
  disabled = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) {
  const variantClass = `vraja-btn-${variant}`;
  const sizeClass = size !== 'md' ? `vraja-btn-${size}` : '';

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`vraja-btn ${variantClass} ${sizeClass} ${className}`.trim()}
      {...props}
    >
      {icon && <span className="vraja-btn-icon">{icon}</span>}
      {children}
    </button>
  );
}

export function AdminInput({
  label,
  id,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  helperText,
  disabled = false,
  className = '',
  prefixIcon,
  ...props
}) {
  return (
    <div className={`vraja-form-group ${className}`.trim()}>
      {label && (
        <label htmlFor={id} className="vraja-form-label">
          {label}
        </label>
      )}
      <div style={{ position: 'relative', width: '100%' }}>
        {prefixIcon && (
          <span
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#718078',
              pointerEvents: 'none',
              display: 'flex',
            }}
          >
            {prefixIcon}
          </span>
        )}
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          className="vraja-input"
          style={prefixIcon ? { paddingLeft: '36px' } : undefined}
          {...props}
        />
      </div>
      {error && <span style={{ fontSize: '12px', color: '#B42318' }}>{error}</span>}
      {helperText && !error && (
        <span style={{ fontSize: '12px', color: '#718078' }}>{helperText}</span>
      )}
    </div>
  );
}

export function AdminSelect({
  label,
  id,
  value,
  onChange,
  options = [],
  disabled = false,
  className = '',
  ...props
}) {
  return (
    <div className={`vraja-form-group ${className}`.trim()}>
      {label && (
        <label htmlFor={id} className="vraja-form-label">
          {label}
        </label>
      )}
      <select
        id={id}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="vraja-select"
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function AdminSegmentedControl({
  options = [],
  value,
  onChange,
  className = '',
}) {
  return (
    <div className={`vraja-segmented-control ${className}`.trim()} role="tablist">
      {options.map((opt) => {
        const isActive = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(opt.value)}
            className={`vraja-segment-btn ${isActive ? 'active' : ''}`.trim()}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
