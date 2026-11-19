import { useState, useEffect, useCallback, useMemo } from 'react';
import { usePortalSession } from '../PortalSessionContext';
import { useIndustryConfig } from '../useIndustryConfig';
import { apiFetch } from '../../../lib/api';
import {
  AdminCard,
  AdminKpi,
  AdminButton,
  AdminBarChart,
} from '../../admin/common';

/**
 * Product A: Review Activity & Analytics Component (Multi-Industry Foundation)
 * Displays 24-hr local timezone hourly usage, busiest day of the week,
 * monthly historical trends, seasonal analysis, year-specific festival periods,
 * and 5-star to 1-star rating breakdown.
 * 
 * Enforces data integrity:
 * - Review-system interactions are strictly labeled as digital assistant usage, not physical footfall.
 * - Dynamic disclaimer noun adapts to tenant industry (e.g. dining footfall, guest occupancy, member check-ins).
 * - Google Review link clicks are accurately presented as Maps redirects, not verified published reviews.
 * - Local tenant timezone is displayed and respected.
 */
export function ProductAReviewAnalytics({ businessId: propBusinessId, startDate, endDate }) {
  const {
    activeTenant,
    handleSessionExpired,
  } = usePortalSession();

  const businessId = propBusinessId || activeTenant?.id || 'default_business';
  const { terminology } = useIndustryConfig(businessId);

  const [analytics, setAnalytics] = useState({
    total_generations: 0,
    google_clicks: 0,
    reviews_copied: 0,
    qr_scans: 0,
    conversion_rate_percent: 0,
    rating_overview: { average_rating: 5.0, total_ratings: 0, distribution: {} },
    rating_distribution: {},
    sentiment_distribution: {},
    peak_usage_time: '13:00 – 14:00',
    busiest_day: 'Sunday',
    timezone: 'Asia/Kolkata',
    hourly_distribution: {},
    weekly_distribution: {},
    monthly_trends: {},
    seasonal_analysis: {},
    festival_analysis: [],
    calendar_heatmap: {},
    business_insights: [],
    recent_activity: [],
  });

  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Date Range Filter State (Phase A5.0.5)
  const [startDateInput, setStartDateInput] = useState(startDate || '');
  const [endDateInput, setEndDateInput] = useState(endDate || '');
  const [appliedStartDate, setAppliedStartDate] = useState(startDate || '');
  const [appliedEndDate, setAppliedEndDate] = useState(endDate || '');
  const [dateValidationError, setDateValidationError] = useState('');

  const activeStart = appliedStartDate || startDate || '';
  const activeEnd = appliedEndDate || endDate || '';

  const handleApplyFilter = (e) => {
    e?.preventDefault();
    setDateValidationError('');
    if (startDateInput && endDateInput && endDateInput < startDateInput) {
      setDateValidationError('End date cannot be earlier than start date.');
      return;
    }
    setAppliedStartDate(startDateInput);
    setAppliedEndDate(endDateInput);
  };

  const handleClearFilter = () => {
    setStartDateInput('');
    setEndDateInput('');
    setAppliedStartDate('');
    setAppliedEndDate('');
    setDateValidationError('');
  };

  const activePeriodLabel = useMemo(() => {
    const tz = analytics.timezone || 'Asia/Kolkata';
    if (activeStart && activeEnd) {
      if (activeStart === activeEnd) {
        return `${activeStart} (${tz})`;
      }
      return `${activeStart} to ${activeEnd} (${tz})`;
    }
    if (activeStart) {
      return `From ${activeStart} (${tz})`;
    }
    if (activeEnd) {
      return `Up to ${activeEnd} (${tz})`;
    }
    return `Lifetime (All Time • ${tz})`;
  }, [activeStart, activeEnd, analytics.timezone]);

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const params = new URLSearchParams();
      if (businessId) params.append('business_id', businessId);
      if (activeStart) params.append('start_date', activeStart);
      if (activeEnd) params.append('end_date', activeEnd);
      const query = params.toString() ? `?${params.toString()}` : '';
      const res = await apiFetch(`/api/reviews/analytics${query}`);
      if (res.status === 401) {
        handleSessionExpired?.();
        return;
      }
      if (!res.ok) {
        throw new Error('Could not load authentic review activity.');
      }
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.warn('[ProductAReviewAnalytics] Fetch error:', err);
      setErrorMsg(err.message || 'Failed to load analytics.');
    } finally {
      setIsLoading(false);
    }
  }, [businessId, activeStart, activeEnd, handleSessionExpired]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const hourlyChartData = useMemo(() => {
    const dist = analytics.hourly_distribution || {};
    return Object.entries(dist).map(([hour, count]) => ({
      label: hour.split(':')[0],
      value: count,
    }));
  }, [analytics.hourly_distribution]);

  return (
    <div className="vraja-portal-view-container">
      <div className="vraja-view-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 className="vraja-view-title">Review Activity & Analytics</h1>
            <p className="vraja-view-subtitle">
              Timezone-accurate interaction metrics, engagement patterns, and rating breakdowns.
            </p>
          </div>
          <AdminButton
            type="button"
            variant="outline"
            size="sm"
            onClick={fetchAnalytics}
            disabled={isLoading}
          >
            {isLoading ? 'Refreshing…' : '🔄 Refresh Data'}
          </AdminButton>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
        {/* Mandatory Data Integrity & Metric Disclosure */}
        <div
          style={{
            backgroundColor: '#DCE5DD',
            border: '1px solid #BFE4CE',
            borderRadius: '10px',
            padding: '16px 20px',
            color: '#174D3A',
            fontSize: '13px',
            lineHeight: '1.55',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '13.5px' }}>
              <span>ℹ️</span> Data Integrity & Metric Disclosure
            </div>
            <span style={{ fontSize: '12px', background: '#FFFFFF', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
              Timezone: {analytics.timezone || 'Asia/Kolkata'}
            </span>
          </div>
          <p style={{ margin: 0 }}>
            Review-system usage measures digital customer interactions with our AI review assistant and does <em>not</em> represent total physical {terminology.disclaimer_noun}. Google Review link clicks represent customer journeys directed to Google Maps; external verification of published reviews requires direct Google Business Profile API OAuth integration.
          </p>
        </div>

        {/* Interactive Reporting Period Selector */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '10px',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '14px', color: '#1F2937' }}>
              <span>📅</span> Reporting Period:
              <span
                style={{
                  backgroundColor: activeStart || activeEnd ? '#EFF6FF' : '#F3F4F6',
                  color: activeStart || activeEnd ? '#1D4ED8' : '#374151',
                  border: `1px solid ${activeStart || activeEnd ? '#BFDBFE' : '#D1D5DB'}`,
                  borderRadius: '6px',
                  padding: '2px 10px',
                  fontSize: '12.5px',
                  fontWeight: 600,
                }}
              >
                {activePeriodLabel}
              </span>
            </div>
            {isLoading && (
              <span style={{ fontSize: '12.5px', color: '#6B7280', fontStyle: 'italic' }}>
                Updating data…
              </span>
            )}
          </div>

          <form
            onSubmit={handleApplyFilter}
            style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="analytics-start-date" style={{ fontSize: '13px', fontWeight: 500, color: '#4B5563' }}>
                From:
              </label>
              <input
                id="analytics-start-date"
                type="date"
                value={startDateInput}
                onChange={(e) => {
                  setStartDateInput(e.target.value);
                  setDateValidationError('');
                }}
                className="vraja-input"
                style={{ padding: '6px 10px', fontSize: '13px', borderRadius: '6px', border: '1px solid #D1D5DB' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="analytics-end-date" style={{ fontSize: '13px', fontWeight: 500, color: '#4B5563' }}>
                To:
              </label>
              <input
                id="analytics-end-date"
                type="date"
                value={endDateInput}
                onChange={(e) => {
                  setEndDateInput(e.target.value);
                  setDateValidationError('');
                }}
                className="vraja-input"
                style={{ padding: '6px 10px', fontSize: '13px', borderRadius: '6px', border: '1px solid #D1D5DB' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <AdminButton
                type="submit"
                variant="primary"
                size="sm"
                disabled={isLoading}
              >
                Apply Filter
              </AdminButton>
              {(startDateInput || endDateInput || activeStart || activeEnd) && (
                <AdminButton
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleClearFilter}
                  disabled={isLoading}
                >
                  Clear
                </AdminButton>
              )}
            </div>
          </form>

          {dateValidationError && (
            <div style={{ fontSize: '12.5px', color: '#DC2626', fontWeight: 500 }}>
              ⚠️ {dateValidationError}
            </div>
          )}
        </div>

        {errorMsg && (
          <div style={{ padding: '12px 16px', backgroundColor: '#FEE4E2', border: '1px solid #FECDCA', borderRadius: '8px', color: '#B42318', fontSize: '13.5px' }}>
            ⚠️ {errorMsg}
          </div>
        )}

        {/* Core Metrics Overview */}
        <div className="vraja-kpi-grid">
          <AdminKpi
            label="QR Sessions Scanned"
            value={analytics.qr_scans || 0}
            trend="Digital assistant scans"
            trendDirection="neutral"
            icon={<span>📱</span>}
          />
          <AdminKpi
            label="AI Review Drafts Created"
            value={analytics.total_generations || 0}
            trend="Synthesized drafts"
            trendDirection="positive"
            icon={<span>⚡</span>}
          />
          <AdminKpi
            label="Google Review Link Clicks"
            value={analytics.google_clicks || 0}
            trend="Maps handoffs"
            trendDirection="positive"
            icon={<span>⭐</span>}
            goldIcon
          />
          <AdminKpi
            label="Draft-to-Maps Conversion"
            value={`${analytics.conversion_rate_percent || 0}%`}
            trend="Completion rate"
            trendDirection="positive"
            icon={<span>🎯</span>}
          />
        </div>

        {/* Hourly Usage Analysis (24-Hour Distribution) */}
        <AdminCard
          title="Hourly Usage Analysis (24-Hour Local Time)"
          subtitle={`Hourly breakdown in ${analytics.timezone || 'Asia/Kolkata'} • Peak window: ${analytics.peak_usage_time}`}
        >
          <AdminBarChart data={hourlyChartData} height={180} />
        </AdminCard>

        {/* Weekly Usage Analysis */}
        <AdminCard
          title="Weekly Usage Analysis"
          subtitle={`Day-by-day distribution identifying busiest day: ${analytics.busiest_day}`}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
            {Object.entries(analytics.weekly_distribution || {}).map(([day, count]) => {
              const maxDayCount = Math.max(1, ...Object.values(analytics.weekly_distribution || {}));
              const isBusiest = day === analytics.busiest_day && count > 0;

              return (
                <div
                  key={day}
                  style={{
                    backgroundColor: isBusiest ? '#DCE5DD' : '#FAF9F6',
                    border: `1px solid ${isBusiest ? '#174D3A' : '#E3E8E3'}`,
                    borderRadius: '8px',
                    padding: '12px',
                    textAlign: 'center',
                  }}
                >
                  <span style={{ fontSize: '11px', color: '#718078', fontWeight: 600, textTransform: 'uppercase' }}>
                    {day.slice(0, 3)}
                  </span>
                  <strong style={{ fontSize: '20px', color: isBusiest ? '#174D3A' : '#26352D', display: 'block', margin: '4px 0' }}>
                    {count}
                  </strong>
                  <span style={{ fontSize: '11px', color: '#718078' }}>
                    {maxDayCount > 0 ? `${Math.round((count / maxDayCount) * 100)}% load` : '0%'}
                  </span>
                </div>
              );
            })}
          </div>
        </AdminCard>

        {/* Seasonal & Festival Comparisons */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
          {/* Seasonal Analysis */}
          <AdminCard
            title="Seasonal Analysis"
            subtitle="Regional seasonal engagement breakdown based on event timestamps"
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {Object.entries(analytics.seasonal_analysis || {}).map(([season, count]) => {
                const totalSeason = Math.max(1, Object.values(analytics.seasonal_analysis || {}).reduce((a, b) => a + b, 0));
                const pct = Math.round((count / totalSeason) * 100);

                return (
                  <div key={season} style={{ backgroundColor: '#FAF9F6', padding: '10px 14px', borderRadius: '8px', border: '1px solid #E3E8E3' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                      <span style={{ color: '#26352D', fontWeight: 600 }}>{season}</span>
                      <span style={{ color: '#718078' }}>{count} interactions ({pct}%)</span>
                    </div>
                    <div style={{ height: '6px', backgroundColor: '#E3E8E3', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, backgroundColor: '#174D3A', borderRadius: '3px' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </AdminCard>

          {/* Festival Baseline Comparisons */}
          <AdminCard
            title="Festival & Occasion Comparisons"
            subtitle="Year-specific festival periods compared against baseline"
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(analytics.festival_analysis || []).map((fest, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: '#FAF9F6',
                    border: '1px solid #E3E8E3',
                    borderRadius: '8px',
                    padding: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ color: '#26352D', fontSize: '13.5px' }}>{fest.festival} ({fest.year})</strong>
                    <span style={{ fontSize: '12px', color: '#174D3A', fontWeight: 700 }}>
                      {fest.event_count} events ({fest.daily_rate}/day)
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: '#718078', display: 'block', marginTop: '2px' }}>
                    Period: {fest.period}
                  </span>
                  <span
                    style={{
                      fontSize: '11.5px',
                      color: fest.insufficient_historical_data ? '#718078' : '#1D7A4D',
                      display: 'block',
                      marginTop: '4px',
                    }}
                  >
                    {fest.insufficient_historical_data ? '⚠️ ' : '✓ '} {fest.notice}
                  </span>
                </div>
              ))}
            </div>
          </AdminCard>
        </div>

        {/* Customer Rating Distribution */}
        <AdminCard title="Customer Rating Distribution" subtitle="5★ down to 1★ review rating breakdown">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px' }}>
            {[5, 4, 3, 2, 1].map((stars) => {
              const count = (analytics.rating_distribution || {})[String(stars)] || 0;
              const total = analytics.rating_overview?.total_ratings || 1;
              const pct = Math.round((count / total) * 100);

              return (
                <div
                  key={stars}
                  style={{
                    backgroundColor: '#FAF9F6',
                    border: '1px solid #E3E8E3',
                    borderRadius: '8px',
                    padding: '14px',
                    textAlign: 'center',
                  }}
                >
                  <span style={{ color: '#C6A66B', fontSize: '14px', fontWeight: 700 }}>
                    {stars} ★
                  </span>
                  <strong style={{ display: 'block', fontSize: '22px', color: '#26352D', margin: '4px 0' }}>
                    {count}
                  </strong>
                  <span style={{ fontSize: '11.5px', color: '#718078' }}>
                    {pct}% of ratings
                  </span>
                </div>
              );
            })}
          </div>
        </AdminCard>
      </div>
    </div>
  );
}

export default ProductAReviewAnalytics;
