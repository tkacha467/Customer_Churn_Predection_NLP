import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../lib/api';

const PortalSessionContext = createContext(null);

export function usePortalSession() {
  const ctx = useContext(PortalSessionContext);
  if (!ctx) {
    throw new Error('usePortalSession must be used within a PortalSessionProvider');
  }
  return ctx;
}

export function PortalSessionProvider({ children, initialBusinessId = 'default_business' }) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [activeTenant, setActiveTenant] = useState(null);
  const [availableTenants, setAvailableTenants] = useState([]);
  const [sharedProfile, setSharedProfile] = useState(null);
  const [entitlements, setEntitlements] = useState([]);
  const [authError, setAuthError] = useState('');
  const [isSigningIn, setIsSigningIn] = useState(false);

  /**
   * Stage 2: Fetches canonical shared profile & authoritative entitlements for the active tenant.
   * If the profile returns 404 (e.g. unmigrated or newly initialized bare tenant),
   * falls back safely to empty entitlements without throwing errors.
   */
  const loadSharedProfile = useCallback(async (tenantId) => {
    if (!tenantId) return null;
    try {
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(tenantId)}/shared-profile`);
      if (res.status === 401) {
        handleSessionExpired();
        return null;
      }
      if (res.ok) {
        const profile = await res.json();
        setSharedProfile(profile);
        const ents = Array.isArray(profile.entitlements) ? profile.entitlements : [];
        setEntitlements(ents);
        return profile;
      }
      // If shared profile doesn't exist yet, fall back safely
      setSharedProfile(null);
      setEntitlements([]);
      return null;
    } catch (err) {
      console.warn('[PortalSession] Failed to load shared profile for tenant:', tenantId, err);
      setSharedProfile(null);
      setEntitlements([]);
      return null;
    }
  }, []);

  /**
   * Stage 1: Verifies session cookie against GET /api/auth/session.
   * On HTTP 200, proceeds to Stage 2 with active_tenant.id.
   */
  const checkSession = useCallback(async () => {
    setIsLoading(true);
    setAuthError('');
    try {
      const res = await apiFetch('/api/auth/session');
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          setIsAuthenticated(true);
          setUser(data.user);
          setActiveTenant(data.active_tenant || null);
          setAvailableTenants(data.available_tenants || []);

          const currentTenantId = data.active_tenant?.id || initialBusinessId;
          await loadSharedProfile(currentTenantId);
          return true;
        }
      }
      // Unauthenticated
      setIsAuthenticated(false);
      setUser(null);
      setActiveTenant(null);
      setAvailableTenants([]);
      setSharedProfile(null);
      setEntitlements([]);
      return false;
    } catch (err) {
      console.warn('[PortalSession] Session verification error:', err);
      setIsAuthenticated(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [initialBusinessId, loadSharedProfile]);

  // Initial session check on mount
  useEffect(() => {
    checkSession();
  }, [checkSession]);

  /**
   * Handles user login via POST /api/auth/login.
   */
  const login = async ({ email = '', password = '', tenantId = '' }) => {
    setIsSigningIn(true);
    setAuthError('');
    try {
      const payload = { password };
      if (email && email.trim()) payload.email = email.trim();
      const targetTenant = tenantId || initialBusinessId;
      if (targetTenant && targetTenant !== 'default_business') {
        payload.tenant_id = targetTenant.trim();
      }

      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const msg = errData.detail || 'Sign-in failed. Please verify credentials.';
        setAuthError(msg);
        return { success: false, error: msg };
      }

      const data = await res.json();
      setIsAuthenticated(true);
      setUser(data.user);
      setActiveTenant(data.active_tenant || null);
      setAvailableTenants(data.available_tenants || []);

      const activeId = data.active_tenant?.id || payload.tenant_id || 'default_business';
      await loadSharedProfile(activeId);
      return { success: true };
    } catch {
      const msg = 'Network connection failed during sign-in.';
      setAuthError(msg);
      return { success: false, error: msg };
    } finally {
      setIsSigningIn(false);
    }
  };

  /**
   * Handles user logout via POST /api/auth/logout.
   */
  const logout = async () => {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' });
    } catch (err) {
      console.warn('[PortalSession] Logout request failed:', err);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setActiveTenant(null);
      setAvailableTenants([]);
      setSharedProfile(null);
      setEntitlements([]);
      setAuthError('');
    }
  };

  /**
   * Switches the active tenant for multi-tenant accounts via POST /api/auth/switch-tenant.
   */
  const switchTenant = async (newTenantId) => {
    if (!newTenantId || newTenantId === activeTenant?.id) return true;
    setIsLoading(true);
    try {
      const res = await apiFetch('/api/auth/switch-tenant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: newTenantId }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAuthError(err.detail || 'Failed to switch business.');
        return false;
      }

      const data = await res.json();
      setActiveTenant(data.active_tenant || null);
      setAvailableTenants(data.available_tenants || []);
      await loadSharedProfile(newTenantId);
      return true;
    } catch {
      setAuthError('Network error while switching business.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Intercepts 401 Unauthorized API responses across the portal.
   */
  const handleSessionExpired = useCallback(() => {
    setIsAuthenticated(false);
    setUser(null);
    setActiveTenant(null);
    setAvailableTenants([]);
    setSharedProfile(null);
    setEntitlements([]);
    setAuthError('Your session has expired. Please sign in again.');
  }, []);

  /**
   * Manually refreshes both session and shared profile.
   */
  const refreshSession = useCallback(async () => {
    return checkSession();
  }, [checkSession]);

  /**
   * Helper to check specific module entitlement.
   */
  const hasEntitlement = useCallback((moduleKey) => {
    return entitlements.includes(moduleKey);
  }, [entitlements]);

  /**
   * Updates local shared profile state immediately after successful save.
   */
  const updateSharedProfileState = useCallback((updatedProfile) => {
    if (!updatedProfile) return;
    setSharedProfile(updatedProfile);
    if (Array.isArray(updatedProfile.entitlements)) {
      setEntitlements(updatedProfile.entitlements);
    }
    if (updatedProfile.display_name && activeTenant) {
      setActiveTenant((prev) => ({
        ...prev,
        business_name: updatedProfile.display_name,
      }));
    }
  }, [activeTenant]);

  const value = {
    isLoading,
    isSigningIn,
    isAuthenticated,
    user,
    activeTenant,
    availableTenants,
    sharedProfile,
    entitlements,
    authError,
    setAuthError,
    login,
    logout,
    switchTenant,
    refreshSession,
    handleSessionExpired,
    hasEntitlement,
    updateSharedProfileState,
  };

  return (
    <PortalSessionContext.Provider value={value}>
      {children}
    </PortalSessionContext.Provider>
  );
}

export default PortalSessionContext;
