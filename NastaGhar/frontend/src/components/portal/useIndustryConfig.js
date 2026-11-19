import { useState, useEffect, useCallback, useRef } from 'react';
import { apiFetch } from '../../lib/api';

const DEFAULT_FALLBACK_TERMINOLOGY = {
  customer_noun_singular: 'Customer',
  customer_noun_plural: 'Customers',
  touchpoint_noun: 'Table / Location',
  touchpoint_placeholder: 'Table 4 / Service Point',
  disclaimer_noun: 'physical business visits',
  private_feedback_title: 'Direct Customer Feedback'
};

export function useIndustryConfig(businessId) {
  const [industryConfig, setIndustryConfig] = useState(null);
  const [availableIndustries, setAvailableIndustries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const activeFetchIdRef = useRef(0);

  const fetchConfig = useCallback(async (targetId) => {
    if (!targetId) return;
    const fetchId = ++activeFetchIdRef.current;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch resolved tenant industry config
      const res = await apiFetch(`/api/businesses/${encodeURIComponent(targetId)}/industry-config`);
      if (fetchId !== activeFetchIdRef.current) return;

      if (res.ok) {
        const data = await res.json();
        setIndustryConfig(data);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Could not load industry configuration.');
      }

      // 2. Fetch available industries catalog for dropdown selection if not loaded yet
      const indRes = await apiFetch('/api/industries');
      if (fetchId !== activeFetchIdRef.current) return;

      if (indRes.ok) {
        const indData = await indRes.json();
        setAvailableIndustries(indData.industries || []);
      }
    } catch (err) {
      if (fetchId === activeFetchIdRef.current) {
        console.warn('[useIndustryConfig] Network error loading config:', err);
        setError('Network error loading industry configuration.');
      }
    } finally {
      if (fetchId === activeFetchIdRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchConfig(businessId);
  }, [businessId, fetchConfig]);

  const refreshIndustryConfig = useCallback(() => {
    return fetchConfig(businessId);
  }, [businessId, fetchConfig]);

  const terminology = industryConfig?.terminology || DEFAULT_FALLBACK_TERMINOLOGY;
  const effectiveTopics = industryConfig?.effective_topics || [];
  const defaultTopics = industryConfig?.default_topics || [];
  const hasCustomTopics = Boolean(industryConfig?.has_custom_topics);

  return {
    industryConfig,
    terminology,
    effectiveTopics,
    defaultTopics,
    hasCustomTopics,
    availableIndustries,
    isLoading,
    error,
    refreshIndustryConfig
  };
}
