import { useState, useEffect, useCallback, useMemo } from 'react';
import { usePortalSession } from '../PortalSessionContext';
import { useIndustryConfig } from '../useIndustryConfig';
import { apiFetch } from '../../../lib/api';
import {
  AdminCard,
  AdminButton,
  StatusBadge,
  AdminBadge,
} from '../../admin/common';

/**
 * Product A: Private Feedback Management Inbox Component (Multi-Industry Foundation)
 * Displays direct customer feedback notes, ratings, selected aspects, and touchpoint markers.
 * 
 * Enforces role-based permissions:
 * - Manager / Owner / Platform Admin: Can view and update ticket status.
 * - Staff: Restricted from inbox (per backend `require_tenant_access('manager')`).
 */
export function ProductAPrivateInbox({ businessId: propBusinessId }) {
  const {
    activeTenant,
    user,
    handleSessionExpired,
  } = usePortalSession();

  const businessId = propBusinessId || activeTenant?.id || 'default_business';
  const { terminology } = useIndustryConfig(businessId);
  const userRole = (activeTenant?.role || 'member').toLowerCase();
  const isStaff = userRole === 'staff';
  const canAccess = userRole === 'owner' || userRole === 'manager' || !!user?.is_platform_admin;

  const [privateTickets, setPrivateTickets] = useState([]);
  const [isLoadingTickets, setIsLoadingTickets] = useState(true);
  const [ticketFilter, setTicketFilter] = useState('all'); // 'all' | 'open' | 'escalated' | 'resolved'
  const [isUpdatingTicketId, setIsUpdatingTicketId] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchPrivateTickets = useCallback(async () => {
    if (!canAccess) {
      setIsLoadingTickets(false);
      return;
    }
    setIsLoadingTickets(true);
    setErrorMsg('');
    try {
      const query = businessId ? `?business_id=${encodeURIComponent(businessId)}` : '';
      const res = await apiFetch(`/api/reviews/private-tickets${query}`);
      if (res.status === 401) {
        handleSessionExpired?.();
        return;
      }
      if (res.status === 403) {
        const errJson = await res.json().catch(() => ({}));
        setErrorMsg(errJson.detail || 'Access restricted: Manager role is required to view private tickets.');
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setPrivateTickets(Array.isArray(data) ? data : []);
      } else {
        throw new Error('Failed to load private feedback tickets.');
      }
    } catch (err) {
      console.warn('[ProductAPrivateInbox] Fetch error:', err);
      setErrorMsg(err.message || 'Network error fetching private tickets.');
    } finally {
      setIsLoadingTickets(false);
    }
  }, [businessId, canAccess, handleSessionExpired]);

  useEffect(() => {
    fetchPrivateTickets();
  }, [fetchPrivateTickets]);

  const handleUpdateTicketStatus = async (ticketId, newStatus) => {
    if (!canAccess) return;
    setIsUpdatingTicketId(ticketId);
    try {
      const res = await apiFetch(`/api/reviews/private-tickets/${encodeURIComponent(ticketId)}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.status === 401) {
        handleSessionExpired?.();
        return;
      }

      if (res.ok) {
        setPrivateTickets((prev) =>
          prev.map((t) => (t.ticket_id === ticketId ? { ...t, status: newStatus } : t))
        );
      } else {
        const errJson = await res.json().catch(() => ({}));
        alert(errJson.detail || 'Could not update ticket status.');
      }
    } catch (err) {
      console.error('[ProductAPrivateInbox] Update error:', err);
      alert('Network error updating ticket status.');
    } finally {
      setIsUpdatingTicketId(null);
    }
  };

  const filteredTickets = useMemo(() => {
    if (ticketFilter === 'all') return privateTickets;
    return privateTickets.filter(
      (t) => (t.status || 'OPEN').toLowerCase() === ticketFilter.toLowerCase()
    );
  }, [privateTickets, ticketFilter]);

  if (isStaff) {
    return (
      <div className="vraja-portal-view-container">
        <div className="vraja-view-header">
          <h1 className="vraja-view-title">Private Feedback Management Inbox</h1>
          <p className="vraja-view-subtitle">Direct {terminology.customer_noun_plural.toLowerCase()} feedback and customer complaint management.</p>
        </div>
        <div className="vraja-portal-empty-card">
          <div className="empty-state-emblem">🔒</div>
          <h2 className="empty-state-title">Manager Access Required</h2>
          <p className="empty-state-desc">
            The Private Feedback Management Inbox is restricted to Managers and Owners. Your current membership role is <strong>Staff</strong>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="vraja-portal-view-container">
      <div className="vraja-view-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 className="vraja-view-title">Private Feedback Inbox</h1>
            <p className="vraja-view-subtitle">
              Direct {terminology.customer_noun_plural.toLowerCase()} feedback, notes and complaints submitted to management.
            </p>
          </div>
          <AdminButton
            type="button"
            variant="outline"
            size="sm"
            onClick={fetchPrivateTickets}
            disabled={isLoadingTickets}
          >
            {isLoadingTickets ? 'Loading…' : '🔄 Refresh Inbox'}
          </AdminButton>
        </div>
      </div>

      {errorMsg && (
        <div style={{ marginBottom: '18px', padding: '12px 16px', backgroundColor: '#FEE4E2', border: '1px solid #FECDCA', borderRadius: '8px', color: '#B42318', fontSize: '13.5px' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      <AdminCard
        title="Customer Feedback Tickets"
        subtitle={`Manage ${terminology.customer_noun_plural.toLowerCase()} issues, investigate operational aspects, and record resolutions`}
      >
        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
          {[
            { id: 'all', label: 'All Tickets' },
            { id: 'open', label: 'Open' },
            { id: 'escalated', label: 'Escalated' },
            { id: 'resolved', label: 'Resolved' },
          ].map((f) => {
            const isActive = ticketFilter === f.id;
            return (
              <button
                key={f.id}
                type="button"
                onClick={() => setTicketFilter(f.id)}
                className={`vraja-btn ${isActive ? 'vraja-btn-secondary' : 'vraja-btn-outline'} vraja-btn-sm`}
                style={isActive ? { fontWeight: 700 } : undefined}
              >
                {f.label}
              </button>
            );
          })}
        </div>

        {/* Tickets List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredTickets.length > 0 ? (
            filteredTickets.map((ticket) => {
              const st = (ticket.status || 'OPEN').toUpperCase();
              const isUpdating = isUpdatingTicketId === ticket.ticket_id;

              return (
                <div key={ticket.ticket_id} className="vraja-ticket-card">
                  <div className="vraja-ticket-top">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <strong style={{ color: '#26352D', fontSize: '14px' }}>{ticket.ticket_id}</strong>
                      <AdminBadge variant="neutral">
                        📍 {ticket.table_number || 'General Visit'}
                      </AdminBadge>
                      <span style={{ color: '#C6A66B', fontSize: '13px' }}>
                        {'★'.repeat(ticket.rating || 3)}
                      </span>
                    </div>

                    <StatusBadge status={st} />
                  </div>

                    <p className="vraja-ticket-quote">
                    "{ticket.diner_note || ticket.customer_note || 'No detailed note provided.'}"
                  </p>

                  {ticket.aspects && ticket.aspects.length > 0 && (
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {ticket.aspects.map((asp, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: '11.5px',
                            backgroundColor: '#EBEFEA',
                            color: '#26352D',
                            padding: '2px 8px',
                            borderRadius: '4px',
                          }}
                        >
                          {asp}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="vraja-ticket-footer">
                    <span style={{ fontSize: '12px', color: '#718078' }}>
                      Guest Contact: <strong>{ticket.guest_contact || 'Anonymous'}</strong>
                    </span>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      {st !== 'RESOLVED' && (
                        <AdminButton
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleUpdateTicketStatus(ticket.ticket_id, 'RESOLVED')}
                          disabled={isUpdating}
                          style={{ color: '#1D7A4D' }}
                        >
                          ✓ Mark Resolved
                        </AdminButton>
                      )}
                      {st !== 'ESCALATED' && (
                        <AdminButton
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleUpdateTicketStatus(ticket.ticket_id, 'ESCALATED')}
                          disabled={isUpdating}
                          style={{ color: '#B42318' }}
                        >
                          ⚠️ Escalate
                        </AdminButton>
                      )}
                      {st === 'RESOLVED' && (
                        <AdminButton
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleUpdateTicketStatus(ticket.ticket_id, 'OPEN')}
                          disabled={isUpdating}
                        >
                          🔄 Re-open
                        </AdminButton>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{ padding: '36px', textAlign: 'center', color: '#718078', fontSize: '13.5px' }}>
              No private feedback tickets matching the "{ticketFilter}" filter.
            </div>
          )}
        </div>
      </AdminCard>
    </div>
  );
}

export default ProductAPrivateInbox;
