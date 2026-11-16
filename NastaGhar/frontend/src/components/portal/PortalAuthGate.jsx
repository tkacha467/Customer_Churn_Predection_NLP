import { useState } from 'react';
import { usePortalSession } from './PortalSessionContext';

export function PortalAuthGate({ children, initialBusinessId = 'default_business' }) {
  const {
    isLoading,
    isSigningIn,
    isAuthenticated,
    authError,
    setAuthError,
    login,
  } = usePortalSession();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tenantId, setTenantId] = useState(
    initialBusinessId !== 'default_business' ? initialBusinessId : ''
  );
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      setAuthError('Please enter your password.');
      return;
    }
    await login({
      email: email.trim(),
      password,
      tenantId: tenantId.trim() || initialBusinessId,
    });
  };

  if (isLoading) {
    return (
      <div className="vraja-portal-loading-gate" role="status" aria-live="polite">
        <div className="vraja-portal-loading-card">
          <div className="vraja-portal-loading-emblem">✨</div>
          <div className="vraja-portal-spinner" />
          <h2 className="vraja-portal-loading-title">VRAJA AI</h2>
          <p className="vraja-portal-loading-sub">Verifying secure portal session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="vraja-portal-login-viewport">
        <div className="vraja-portal-login-card">
          <div className="vraja-portal-brand-badge">
            <span className="vraja-brand-icon">✨</span>
            <span className="vraja-brand-name">VRAJA AI</span>
            <span className="vraja-brand-pill">Client Portal</span>
          </div>

          <h1 className="vraja-portal-login-heading">Business Sign In</h1>
          <p className="vraja-portal-login-desc">
            Access your unified client dashboard for Google Review Manager and Digital Business Card.
          </p>

          {authError && (
            <div className="vraja-portal-login-alert" role="alert">
              <span className="alert-icon">⚠️</span>
              <span className="alert-text">{authError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="vraja-portal-login-form">
            <div className="vraja-portal-field">
              <label htmlFor="portal-email">Account Email</label>
              <input
                id="portal-email"
                type="email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="owner@restaurant.com"
                autoComplete="username"
                disabled={isSigningIn}
              />
              <span className="field-hint">
                Multi-tenant accounts require email. Single-location owners can leave blank.
              </span>
            </div>

            <div className="vraja-portal-field">
              <label htmlFor="portal-password">Password</label>
              <input
                id="portal-password"
                type="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                autoComplete="current-password"
                required
                disabled={isSigningIn}
              />
            </div>

            <div className="vraja-portal-advanced-toggle">
              <button
                type="button"
                className="advanced-toggle-btn"
                onClick={() => setShowAdvanced((v) => !v)}
              >
                {showAdvanced ? '▴ Hide location settings' : '▾ Specific branch / business ID'}
              </button>
            </div>

            {showAdvanced && (
              <div className="vraja-portal-field">
                <label htmlFor="portal-tenant-id">Business / Branch Identifier</label>
                <input
                  id="portal-tenant-id"
                  type="text"
                  name="tenantId"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  placeholder="e.g. nasta-ghar or cafe-alpha"
                  disabled={isSigningIn}
                />
              </div>
            )}

            <button
              type="submit"
              className="vraja-portal-submit-btn"
              disabled={isSigningIn}
            >
              {isSigningIn ? (
                <>
                  <span className="btn-spinner" />
                  <span>Signing In...</span>
                </>
              ) : (
                'Sign In to Client Portal'
              )}
            </button>
          </form>

          <div className="vraja-portal-security-footer">
            <span>🔒 256-Bit TLS • Role Guarded • Factual Analytics</span>
          </div>
        </div>
      </div>
    );
  }

  return children;
}

export default PortalAuthGate;
