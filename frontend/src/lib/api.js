const configuredBase = import.meta.env.VITE_API_BASE_URL || '';
export const API_BASE = configuredBase.replace(/\/+$/, '');

export function apiFetch(path, options = {}) {
  return fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
  });
}
