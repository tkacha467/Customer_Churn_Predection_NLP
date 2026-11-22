import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../lib/api';

const SEVERITY_COLORS = {
  CRITICAL: { bg: '#FEECEB', text: '#B42318', border: '#F7C6C3' },
  HIGH: { bg: '#FFF1E8', text: '#EA580C', border: '#FDBA74' },
  MEDIUM: { bg: '#FEF7E6', text: '#945B09', border: '#F9DF9C' },
  LOW: { bg: '#F1F4F1', text: '#4B5563', border: '#DCE5DD' },
  INFO: { bg: '#EBF5FF', text: '#1E40AF', border: '#BFDBFE' },
};

const STATUS_COLORS = {
  open: { bg: '#FEECEB', text: '#B42318' },
  investigating: { bg: '#FEF7E6', text: '#945B09' },
  resolved: { bg: '#E8F5EE', text: '#1D7A4D' },
};

export default function SecurityShieldDashboard() {
  const [activeSection, setActiveSection] = useState('incidents'); // 'incidents' | 'events' | 'outbox'
  const [overview, setOverview] = useState(null);
  const [isLoadingOverview, setIsLoadingOverview] = useState(true);

  // Incidents state
  const [incidents, setIncidents] = useState([]);
  const [incidentCount, setIncidentCount] = useState(0);
  const [incidentFilterStatus, setIncidentFilterStatus] = useState('all');
  const [incidentFilterSeverity, setIncidentFilterSeverity] = useState('all');
  const [isLoadingIncidents, setIsLoadingIncidents] = useState(false);

  // Events state
  const [events, setEvents] = useState([]);
  const [eventsCount, setEventsCount] = useState(0);
  const [eventFilterSeverity, setEventFilterSeverity] = useState('all');
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);

  // Outbox state
  const [outboxItems, setOutboxItems] = useState([]);
  const [outboxCount, setOutboxCount] = useState(0);
  const [isFlushingOutbox, setIsFlushingOutbox] = useState(false);

  // Modals & Notifications
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [resolutionNote, setResolutionNote] = useState('');
  const [isUpdatingIncident, setIsUpdatingIncident] = useState(false);
  const [notification, setNotification] = useState({ type: '', text: '' });

  // 1. Fetch Overview Metrics
  const fetchOverview = useCallback(async () => {
    setIsLoadingOverview(true);
    try {
      const res = await apiFetch('/api/platform/security-shield/overview');
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      }
    } catch (e) {
      console.error('[SecurityShield] Failed to load overview', e);
    } finally {
      setIsLoadingOverview(false);
    }
  }, []);

  // 2. Fetch Incidents
  const fetchIncidents = useCallback(async () => {
    setIsLoadingIncidents(true);
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (incidentFilterStatus !== 'all') params.set('status', incidentFilterStatus);
      if (incidentFilterSeverity !== 'all') params.set('severity', incidentFilterSeverity);

      const res = await apiFetch(`/api/platform/security-shield/incidents?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data.incidents || []);
        setIncidentCount(data.total_count || 0);
      }
    } catch (e) {
      console.error('[SecurityShield] Failed to load incidents', e);
    } finally {
      setIsLoadingIncidents(false);
    }
  }, [incidentFilterStatus, incidentFilterSeverity]);

  // 3. Fetch Events
  const fetchEvents = useCallback(async () => {
    setIsLoadingEvents(true);
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (eventFilterSeverity !== 'all') params.set('severity', eventFilterSeverity);

      const res = await apiFetch(`/api/platform/security-shield/events?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
        setEventsCount(data.total_count || 0);
      }
    } catch (e) {
      console.error('[SecurityShield] Failed to load events', e);
    } finally {
      setIsLoadingEvents(false);
    }
  }, [eventFilterSeverity]);

  // 4. Fetch Outbox
  const fetchOutbox = useCallback(async () => {
    try {
      const res = await apiFetch('/api/platform/security-shield/outbox?limit=50');
      if (res.ok) {
        const data = await res.json();
        setOutboxItems(data.items || []);
        setOutboxCount(data.total_count || 0);
      }
    } catch (e) {
      console.error('[SecurityShield] Failed to load outbox', e);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  useEffect(() => {
    if (activeSection === 'incidents') fetchIncidents();
    if (activeSection === 'events') fetchEvents();
    if (activeSection === 'outbox') fetchOutbox();
  }, [activeSection, fetchIncidents, fetchEvents, fetchOutbox]);

  // Handle Incident Status Update
  const handleUpdateIncidentStatus = async (incidentId, newStatus, note = '') => {
    setIsUpdatingIncident(true);
    try {
      const res = await apiFetch(`/api/platform/security-shield/incidents/${encodeURIComponent(incidentId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus, resolution_note: note }),
      });
      if (res.ok) {
        setNotification({ type: 'success', text: `Incident ${incidentId} marked as ${newStatus}.` });
        setSelectedIncident(null);
        setResolutionNote('');
        fetchIncidents();
        fetchOverview();
      } else {
        const err = await res.json();
        setNotification({ type: 'error', text: err.detail || 'Could not update incident.' });
      }
    } catch (e) {
      setNotification({ type: 'error', text: 'Network error updating incident.' });
    } finally {
      setIsUpdatingIncident(false);
    }
  };

  // Handle Outbox Retry
  const handleFlushOutbox = async () => {
    setIsFlushingOutbox(true);
    try {
      const res = await apiFetch('/api/platform/security-shield/outbox/retry', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setNotification({
          type: 'success',
          text: `Outbox processed: ${data.result?.sent || 0} sent, ${data.result?.failed || 0} pending.`,
        });
        fetchOutbox();
        fetchOverview();
      }
    } catch (e) {
      setNotification({ type: 'error', text: 'Failed to process outbox.' });
    } finally {
      setIsFlushingOutbox(false);
    }
  };

  // Export Events JSON
  const handleExportEvents = async () => {
    try {
      const res = await apiFetch('/api/platform/security-shield/export', { method: 'POST' });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security_audit_export_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      setNotification({ type: 'error', text: 'Failed to export audit logs.' });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner / Notification */}
      {notification.text && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: notification.type === 'success' ? '#E8F5EE' : '#FEECEB',
            color: notification.type === 'success' ? '#1D7A4D' : '#B42318',
            border: `1px solid ${notification.type === 'success' ? '#BFE4CE' : '#F7C6C3'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '14px',
          }}
        >
          <span>{notification.type === 'success' ? '✅' : '⚠️'} {notification.text}</span>
          <button
            type="button"
            onClick={() => setNotification({ type: '', text: '' })}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px', color: 'inherit' }}
          >
            ×
          </button>
        </div>
      )}

      {/* KPI Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        {/* Card 1: Open Incidents */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '10px',
            padding: '18px 20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#6B7280', fontWeight: 600 }}>Active Incidents</span>
            <span style={{ fontSize: '18px' }}>🚨</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: (overview?.open_incidents || 0) > 0 ? '#B42318' : '#1D7A4D', margin: '8px 0' }}>
            {isLoadingOverview ? '…' : overview?.open_incidents || 0}
          </div>
          <span style={{ fontSize: '12px', color: '#6B7280' }}>
            {overview?.investigating_incidents || 0} under active investigation
          </span>
        </div>

        {/* Card 2: High/Critical Threats */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '10px',
            padding: '18px 20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#6B7280', fontWeight: 600 }}>High / Critical Threats</span>
            <span style={{ fontSize: '18px' }}>⚠️</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: (overview?.high_critical_incidents || 0) > 0 ? '#EA580C' : '#1D7A4D', margin: '8px 0' }}>
            {isLoadingOverview ? '…' : overview?.high_critical_incidents || 0}
          </div>
          <span style={{ fontSize: '12px', color: '#6B7280' }}>
            Requires priority security response
          </span>
        </div>

        {/* Card 3: Events Intercepted (24h) */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '10px',
            padding: '18px 20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#6B7280', fontWeight: 600 }}>Attacks Intercepted (24h)</span>
            <span style={{ fontSize: '18px' }}>🛡️</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#174D3A', margin: '8px 0' }}>
            {isLoadingOverview ? '…' : overview?.events_last_24h || 0}
          </div>
          <span style={{ fontSize: '12px', color: '#6B7280' }}>
            {overview?.total_events || 0} total lifetime audit records
          </span>
        </div>

        {/* Card 4: Email Notification Engine */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '10px',
            padding: '18px 20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#6B7280', fontWeight: 600 }}>Email Alert Pipeline</span>
            <span style={{ fontSize: '18px' }}>📬</span>
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: '#174D3A', margin: '12px 0 6px 0' }}>
            {overview?.target_alert_email || 'vajra.techworks@gmail.com'}
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                backgroundColor: overview?.smtp?.status === 'CONFIGURED' ? '#E8F5EE' : '#FEF7E6',
                color: overview?.smtp?.status === 'CONFIGURED' ? '#1D7A4D' : '#945B09',
              }}
            >
              SMTP: {overview?.smtp?.status || 'NOT CONFIGURED'}
            </span>
            <span style={{ fontSize: '12px', color: '#6B7280' }}>
              ({overview?.smtp?.transport || 'mock'} transport)
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs & Actions Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #E5E7EB',
          paddingBottom: '12px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setActiveSection('incidents')}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: activeSection === 'incidents' ? '#174D3A' : '#F3F4F6',
              color: activeSection === 'incidents' ? '#FFFFFF' : '#374151',
            }}
          >
            🚨 Security Incidents ({incidentCount})
          </button>
          <button
            type="button"
            onClick={() => setActiveSection('events')}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: activeSection === 'events' ? '#174D3A' : '#F3F4F6',
              color: activeSection === 'events' ? '#FFFFFF' : '#374151',
            }}
          >
            📜 Audit Events Stream ({eventsCount})
          </button>
          <button
            type="button"
            onClick={() => setActiveSection('outbox')}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: activeSection === 'outbox' ? '#174D3A' : '#F3F4F6',
              color: activeSection === 'outbox' ? '#FFFFFF' : '#374151',
            }}
          >
            📬 Alert Outbox ({outboxCount})
          </button>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={handleExportEvents}
            style={{
              padding: '8px 14px',
              borderRadius: '6px',
              border: '1px solid #D1D5DB',
              backgroundColor: '#FFFFFF',
              color: '#374151',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            📥 Export Audit JSON
          </button>
          <button
            type="button"
            onClick={() => {
              fetchOverview();
              if (activeSection === 'incidents') fetchIncidents();
              if (activeSection === 'events') fetchEvents();
              if (activeSection === 'outbox') fetchOutbox();
            }}
            style={{
              padding: '8px 14px',
              borderRadius: '6px',
              border: '1px solid #174D3A',
              backgroundColor: '#FFFFFF',
              color: '#174D3A',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* ==================================================================
          SECTION 1: INCIDENTS MANAGEMENT
          ================================================================== */}
      {activeSection === 'incidents' && (
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '10px', border: '1px solid #E5E7EB', overflow: 'hidden' }}>
          {/* Filters Bar */}
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #E5E7EB', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#4B5563' }}>Status:</span>
              <select
                value={incidentFilterStatus}
                onChange={(e) => setIncidentFilterStatus(e.target.value)}
                style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #D1D5DB', fontSize: '13px' }}
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="investigating">Investigating</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#4B5563' }}>Severity:</span>
              <select
                value={incidentFilterSeverity}
                onChange={(e) => setIncidentFilterSeverity(e.target.value)}
                style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #D1D5DB', fontSize: '13px' }}
              >
                <option value="all">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>

          {/* Table */}
          {isLoadingIncidents ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6B7280' }}>Loading security incidents…</div>
          ) : incidents.length === 0 ? (
            <div style={{ padding: '48px', textAlign: 'center', color: '#6B7280' }}>
              <div style={{ fontSize: '36px', marginBottom: '8px' }}>🛡️</div>
              <h4 style={{ margin: '0 0 4px 0', color: '#111827' }}>No security incidents matching criteria</h4>
              <p style={{ margin: 0, fontSize: '13px' }}>The system is operating securely with zero unhandled attacks.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead style={{ backgroundColor: '#F9FAFB', borderBottom: '1px solid #E5E7EB', color: '#6B7280', fontWeight: 600 }}>
                  <tr>
                    <th style={{ padding: '12px 16px' }}>Incident ID</th>
                    <th style={{ padding: '12px 16px' }}>Type & Description</th>
                    <th style={{ padding: '12px 16px' }}>Severity</th>
                    <th style={{ padding: '12px 16px' }}>Affected Tenant</th>
                    <th style={{ padding: '12px 16px' }}>Count</th>
                    <th style={{ padding: '12px 16px' }}>Status</th>
                    <th style={{ padding: '12px 16px' }}>Last Seen</th>
                    <th style={{ padding: '12px 16px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((inc) => {
                    const sevStyle = SEVERITY_COLORS[inc.severity] || SEVERITY_COLORS.LOW;
                    const statStyle = STATUS_COLORS[inc.status] || STATUS_COLORS.open;

                    return (
                      <tr key={inc.incident_id} style={{ borderBottom: '1px solid #F3F4F6' }}>
                        <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontWeight: 600, color: '#174D3A' }}>
                          {inc.incident_id}
                        </td>
                        <td style={{ padding: '12px 16px', maxWidth: '300px' }}>
                          <div style={{ fontWeight: 600, color: '#111827' }}>{inc.title}</div>
                          <div style={{ fontSize: '12px', color: '#6B7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {inc.description}
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 700,
                              backgroundColor: sevStyle.bg,
                              color: sevStyle.text,
                              border: `1px solid ${sevStyle.border}`,
                            }}
                          >
                            {inc.severity}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: '#374151' }}>
                          {inc.affected_tenant || 'Global Platform'}
                        </td>
                        <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                          {inc.event_count}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              backgroundColor: statStyle.bg,
                              color: statStyle.text,
                            }}
                          >
                            {inc.status}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: '#6B7280', fontSize: '12px' }}>
                          {new Date(inc.last_observed_at * 1000).toLocaleString()}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            {inc.status === 'open' && (
                              <button
                                type="button"
                                onClick={() => handleUpdateIncidentStatus(inc.incident_id, 'investigating')}
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  fontSize: '11px',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                  backgroundColor: '#FEF7E6',
                                  color: '#945B09',
                                  border: '1px solid #F9DF9C',
                                }}
                              >
                                Acknowledge
                              </button>
                            )}
                            {inc.status !== 'resolved' && (
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedIncident(inc);
                                  setResolutionNote(inc.resolution_note || '');
                                }}
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  fontSize: '11px',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                  backgroundColor: '#E8F5EE',
                                  color: '#1D7A4D',
                                  border: '1px solid #BFE4CE',
                                }}
                              >
                                Resolve…
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================
          SECTION 2: CORRELATED AUDIT EVENTS STREAM
          ================================================================== */}
      {activeSection === 'events' && (
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '10px', border: '1px solid #E5E7EB', overflow: 'hidden' }}>
          {/* Filter */}
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #E5E7EB', display: 'flex', gap: '16px', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#4B5563' }}>Severity:</span>
            <select
              value={eventFilterSeverity}
              onChange={(e) => setEventFilterSeverity(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #D1D5DB', fontSize: '13px' }}
            >
              <option value="all">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>
          </div>

          {isLoadingEvents ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6B7280' }}>Loading security event stream…</div>
          ) : events.length === 0 ? (
            <div style={{ padding: '48px', textAlign: 'center', color: '#6B7280' }}>
              No security events recorded matching criteria.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead style={{ backgroundColor: '#F9FAFB', borderBottom: '1px solid #E5E7EB', color: '#6B7280', fontWeight: 600 }}>
                  <tr>
                    <th style={{ padding: '12px 16px' }}>Timestamp (UTC)</th>
                    <th style={{ padding: '12px 16px' }}>Event Type</th>
                    <th style={{ padding: '12px 16px' }}>Severity</th>
                    <th style={{ padding: '12px 16px' }}>Tenant ID</th>
                    <th style={{ padding: '12px 16px' }}>Actor ID</th>
                    <th style={{ padding: '12px 16px' }}>Action Taken</th>
                    <th style={{ padding: '12px 16px' }}>Outcome</th>
                    <th style={{ padding: '12px 16px' }}>Correlation ID</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((ev) => {
                    const sevStyle = SEVERITY_COLORS[ev.severity] || SEVERITY_COLORS.LOW;

                    return (
                      <tr key={ev.event_id} style={{ borderBottom: '1px solid #F3F4F6' }}>
                        <td style={{ padding: '12px 16px', color: '#6B7280', fontSize: '12px', fontFamily: 'monospace' }}>
                          {new Date(ev.timestamp * 1000).toISOString().replace('T', ' ').slice(0, 19)}
                        </td>
                        <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>
                          {ev.event_type}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 700,
                              backgroundColor: sevStyle.bg,
                              color: sevStyle.text,
                              border: `1px solid ${sevStyle.border}`,
                            }}
                          >
                            {ev.severity}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: '#374151' }}>
                          {ev.tenant_id || '—'}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#374151', fontFamily: 'monospace', fontSize: '12px' }}>
                          {ev.actor_id || 'anonymous'}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#B42318', fontWeight: 600 }}>
                          {ev.action_taken}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#1D7A4D', fontWeight: 600 }}>
                          {ev.outcome}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#9CA3AF', fontFamily: 'monospace', fontSize: '11px' }}>
                          {ev.correlation_id ? ev.correlation_id.slice(0, 8) + '…' : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================
          SECTION 3: ALERT OUTBOX & DISPATCH LOG
          ================================================================== */}
      {activeSection === 'outbox' && (
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '10px', border: '1px solid #E5E7EB', overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#111827' }}>
              Pending and Dispatched Email Alerts ({outboxCount})
            </span>
            <button
              type="button"
              disabled={isFlushingOutbox}
              onClick={handleFlushOutbox}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: '#174D3A',
                color: '#FFFFFF',
                fontSize: '13px',
                fontWeight: 600,
                cursor: isFlushingOutbox ? 'not-allowed' : 'pointer',
              }}
            >
              {isFlushingOutbox ? 'Flushing…' : '⚡ Flush & Send Outbox'}
            </button>
          </div>

          {outboxItems.length === 0 ? (
            <div style={{ padding: '48px', textAlign: 'center', color: '#6B7280' }}>
              Outbox is clean. All high/critical alert emails have been dispatched.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead style={{ backgroundColor: '#F9FAFB', borderBottom: '1px solid #E5E7EB', color: '#6B7280', fontWeight: 600 }}>
                  <tr>
                    <th style={{ padding: '12px 16px' }}>Outbox ID</th>
                    <th style={{ padding: '12px 16px' }}>Recipient</th>
                    <th style={{ padding: '12px 16px' }}>Subject</th>
                    <th style={{ padding: '12px 16px' }}>Severity</th>
                    <th style={{ padding: '12px 16px' }}>Status</th>
                    <th style={{ padding: '12px 16px' }}>Attempts</th>
                    <th style={{ padding: '12px 16px' }}>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {outboxItems.map((item) => (
                    <tr key={item.id} style={{ borderBottom: '1px solid #F3F4F6' }}>
                      <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>{item.id}</td>
                      <td style={{ padding: '12px 16px', fontWeight: 600 }}>{item.recipient}</td>
                      <td style={{ padding: '12px 16px' }}>{item.subject}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontWeight: 700, fontSize: '11px', color: item.severity === 'CRITICAL' ? '#B42318' : '#EA580C' }}>
                          {item.severity}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor:
                              item.status === 'sent' ? '#E8F5EE' :
                              item.status === 'mock_sent' ? '#EFF6FF' :
                              item.status === 'claimed' ? '#F5F3FF' :
                              item.status === 'pending' ? '#FEF7E6' : '#FEECEB',
                            color:
                              item.status === 'sent' ? '#1D7A4D' :
                              item.status === 'mock_sent' ? '#1D4ED8' :
                              item.status === 'claimed' ? '#6D28D9' :
                              item.status === 'pending' ? '#945B09' : '#B42318',
                          }}
                        >
                          {item.status.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px' }}>{item.attempts} / {item.max_attempts}</td>
                      <td style={{ padding: '12px 16px', color: '#6B7280', fontSize: '12px' }}>
                        {new Date(item.created_at * 1000).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================
          INCIDENT RESOLUTION MODAL
          ================================================================== */}
      {selectedIncident && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '10px',
              maxWidth: '540px',
              width: '100%',
              padding: '24px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#111827' }}>
              Resolve Incident {selectedIncident.incident_id}
            </h3>
            <p style={{ fontSize: '13px', color: '#4B5563', margin: '0 0 16px 0' }}>
              <strong>Type:</strong> {selectedIncident.event_type} &bull; <strong>Tenant:</strong> {selectedIncident.affected_tenant || 'Global'}
            </p>

            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>
              Resolution Notes & Root Cause Mitigation:
            </label>
            <textarea
              value={resolutionNote}
              onChange={(e) => setResolutionNote(e.target.value)}
              placeholder="e.g. Origin whitelisted / Client IP temporarily throttled / Tenant entitlement reviewed."
              rows={4}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid #D1D5DB',
                fontSize: '13px',
                fontFamily: 'inherit',
                marginBottom: '20px',
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setSelectedIncident(null)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: '1px solid #D1D5DB',
                  backgroundColor: '#FFFFFF',
                  color: '#374151',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isUpdatingIncident}
                onClick={() => handleUpdateIncidentStatus(selectedIncident.incident_id, 'resolved', resolutionNote)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: '#174D3A',
                  color: '#FFFFFF',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: isUpdatingIncident ? 'not-allowed' : 'pointer',
                }}
              >
                {isUpdatingIncident ? 'Saving…' : 'Mark Resolved'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
