"""
VRAJA AI Security Shield — Core Module (Phase A6).
Enterprise-grade structured security audit event logger, incident manager,
and alert dispatcher.

Key Capabilities:
- Stable, typed security event taxonomy.
- PII-safe sanitization (strictly strips credentials, tokens, cookies, secrets, and review drafts).
- Durable multi-worker SQLite audit persistence (survives process restarts).
- Thread-safe in-memory fast ring buffer.
- Incident aggregation (groups correlated bursts into single incidents).
- Multi-channel notification pipeline with durable outbox and retry backoff.
- Target Alert Recipient: vajra.techworks@gmail.com
"""

import time
import uuid
import threading
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

from backend.app.core.security.security_store import SecurityStore
from backend.app.core.security.alert_mailer import alert_mailer, alert_dispatcher


class SecurityEventType(str, Enum):
    AUTH_FAILED_LOGIN = "AUTH_FAILED_LOGIN"
    AUTH_BRUTE_FORCE_LOCKOUT = "AUTH_BRUTE_FORCE_LOCKOUT"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    AUTH_SESSION_REVOKED = "AUTH_SESSION_REVOKED"
    ACCESS_UNAUTHORIZED_ADMIN = "ACCESS_UNAUTHORIZED_ADMIN"
    ACCESS_CROSS_TENANT_DENIAL = "ACCESS_CROSS_TENANT_DENIAL"
    ACCESS_HEALTHCARE_RESTRICTION = "ACCESS_HEALTHCARE_RESTRICTION"
    ACCESS_UNKNOWN_TENANT = "ACCESS_UNKNOWN_TENANT"
    ACCESS_SUSPENDED_TENANT = "ACCESS_SUSPENDED_TENANT"
    TENANT_ENTITLEMENT_VIOLATION = "TENANT_ENTITLEMENT_VIOLATION"
    ABUSE_RATE_LIMIT_EXCEEDED = "ABUSE_RATE_LIMIT_EXCEEDED"
    ABUSE_PREVIEW_SPOOF_ATTEMPT = "ABUSE_PREVIEW_SPOOF_ATTEMPT"
    AI_INJECTION_NEUTRALIZED = "AI_INJECTION_NEUTRALIZED"
    FILE_UNAUTHORIZED_ACCESS = "FILE_UNAUTHORIZED_ACCESS"
    CSRF_ORIGIN_VIOLATION = "CSRF_ORIGIN_VIOLATION"
    SECURITY_INCIDENT_MUTATED = "SECURITY_INCIDENT_MUTATED"
    CODE_INTEGRITY_TAMPER_DETECTED = "CODE_INTEGRITY_TAMPER_DETECTED"
    DATABASE_SCHEMA_TAMPER_DETECTED = "DATABASE_SCHEMA_TAMPER_DETECTED"


class SecuritySeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityAuditRecord:
    event_id: str
    event_type: str
    severity: str
    timestamp: float
    actor_id: Optional[str]
    tenant_id: Optional[str]
    correlation_id: str
    action_taken: str
    outcome: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Sensitive fields that MUST NEVER appear in audit logs or notification emails
FORBIDDEN_DETAIL_KEYS = {
    "password", "password_hash", "token", "raw_token", "cookie",
    "secret", "api_key", "guest_review", "diner_note", "user_note",
    "authorization", "smtp_password"
}


def sanitize_details(raw_details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitizes metadata to prevent accidental credential, token, or customer PII leakage."""
    if not raw_details:
        return {}
    sanitized = {}
    for k, v in raw_details.items():
        k_lower = k.lower()
        if k_lower in FORBIDDEN_DETAIL_KEYS or "secret" in k_lower or "pass" in k_lower or "token" in k_lower:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, str) and len(v) > 500:
            sanitized[k] = v[:500] + "... [TRUNCATED]"
        else:
            sanitized[k] = v
    return sanitized


class SecurityShield:
    """Enterprise security monitoring, durable audit logging, and incident response engine."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._buffer: List[SecurityAuditRecord] = []
                cls._instance._max_size = 2000
                cls._instance._buf_lock = threading.Lock()
                cls._instance._admin_email = "vajra.techworks@gmail.com"
                cls._instance._store = SecurityStore()
                cls._instance._mailer = alert_mailer
        return cls._instance

    @property
    def store(self) -> SecurityStore:
        return self._store

    @property
    def mailer(self):
        return self._mailer

    def emit(
        self,
        event_type: SecurityEventType | str,
        severity: SecuritySeverity | str,
        actor_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        action_taken: str = "BLOCKED",
        outcome: str = "ATTACK_PREVENTED",
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityAuditRecord:
        """
        Records a structured security event into both the in-memory fast ring buffer
        and the durable, multi-worker resilient SQLite storage.
        Evaluates detection rules and groups incidents for notification dispatch.
        """
        ev_type_str = str(event_type.value if isinstance(event_type, SecurityEventType) else event_type)
        sev_str = str(severity.value if isinstance(severity, SecuritySeverity) else severity).upper()
        now_ts = time.time()
        c_id = correlation_id or str(uuid.uuid4())
        sanitized = sanitize_details(details)

        record = SecurityAuditRecord(
            event_id=str(uuid.uuid4()),
            event_type=ev_type_str,
            severity=sev_str,
            timestamp=now_ts,
            actor_id=actor_id,
            tenant_id=tenant_id,
            correlation_id=c_id,
            action_taken=action_taken,
            outcome=outcome,
            details=sanitized
        )

        # 1. Update in-memory ring buffer (fast read cache)
        with self._buf_lock:
            self._buffer.append(record)
            if len(self._buffer) > self._max_size:
                self._buffer = self._buffer[-self._max_size:]

        # 2. Persist to durable SQLite storage
        try:
            self._store.record_event(record.to_dict())
        except Exception as e:
            print(f"[SecurityShield ERROR] Failed to persist event {record.event_id}: {e}")

        # 3. Incident Aggregation & Notification Dispatch
        self._evaluate_incident_and_notify(record)

        return record

    def _evaluate_incident_and_notify(self, record: SecurityAuditRecord):
        """Groups repeated events into security incidents and queues notifications."""
        sev = record.severity
        ev_type = record.event_type

        # Generate descriptive title
        title_map = {
            SecurityEventType.CSRF_ORIGIN_VIOLATION.value: "Cross-Site Request Forgery (CSRF) Attempt Blocked",
            SecurityEventType.ACCESS_CROSS_TENANT_DENIAL.value: "Unauthorized Cross-Tenant Access Attempt (BOLA/IDOR)",
            SecurityEventType.ACCESS_UNAUTHORIZED_ADMIN.value: "Privileged Platform Admin Access Attempt Denied",
            SecurityEventType.ACCESS_HEALTHCARE_RESTRICTION.value: "Restricted Healthcare AI Review Attempt Blocked",
            SecurityEventType.AUTH_BRUTE_FORCE_LOCKOUT.value: "Brute-Force Login Threshold Triggered",
            SecurityEventType.AUTH_FAILED_LOGIN.value: "Failed Authentication Attempt",
            SecurityEventType.AI_INJECTION_NEUTRALIZED.value: "Malicious AI Prompt Injection Neutralized",
            SecurityEventType.ABUSE_RATE_LIMIT_EXCEEDED.value: "API Rate-Limit Threshold Exceeded",
            SecurityEventType.ABUSE_PREVIEW_SPOOF_ATTEMPT.value: "Client Telemetry Preview Spoofing Attempt",
            SecurityEventType.ACCESS_UNKNOWN_TENANT.value: "Unknown Tenant Identifier Requested",
            SecurityEventType.ACCESS_SUSPENDED_TENANT.value: "Access Attempt on Inactive/Suspended Tenant",
            SecurityEventType.TENANT_ENTITLEMENT_VIOLATION.value: "Unentitled Product Module Invocation Attempt",
            SecurityEventType.FILE_UNAUTHORIZED_ACCESS.value: "Unauthorized Document Access Attempt",
        }
        title = title_map.get(ev_type, f"Security Alert: {ev_type}")
        desc = (
            f"Anomalous activity of type {ev_type} was intercepted for tenant "
            f"'{record.tenant_id or 'global'}'. Action: {record.action_taken}. Outcome: {record.outcome}."
        )

        try:
            incident_id, is_new = self._store.aggregate_event_into_incident(
                event_type=ev_type,
                severity=sev,
                affected_tenant=record.tenant_id,
                actor_id=record.actor_id,
                title=title,
                description=desc,
                details=record.details,
                window_seconds=900.0  # 15 minute grouping window
            )

            # Notification policy:
            # - CRITICAL: queue alert on every new incident or every 10 repeated events
            # - HIGH: queue alert on new incident (deduplicated within window)
            # - MEDIUM: queue alert only if incident event count reaches threshold 5
            # - LOW/INFO: tracked in dashboard, no immediate email
            should_alert = False
            incident = self._store.get_incident(incident_id)

            if incident:
                cnt = incident.get("event_count", 1)
                if sev == SecuritySeverity.CRITICAL.value:
                    if is_new or (cnt % 10 == 0):
                        should_alert = True
                elif sev == SecuritySeverity.HIGH.value:
                    if is_new:
                        should_alert = True
                elif sev == SecuritySeverity.MEDIUM.value:
                    if cnt == 5:
                        should_alert = True

            if should_alert and incident:
                subject, text_b, html_b = self._mailer.format_incident_email(incident)
                self._store.queue_alert(
                    incident_id=incident_id,
                    recipient=self._mailer.recipient,
                    subject=subject,
                    body_text=text_b,
                    body_html=html_b,
                    severity=sev
                )
                # Decoupled: Customer request threads do not execute network SMTP calls.
                # Alerts are persisted in the SQLite outbox and processed by AlertDispatcherWorker.

        except Exception as e:
            print(f"[SecurityShield ERROR] Failed in incident aggregation: {e}")

    # --------------------------------------------------------------------------
    # QUERY & MANAGEMENT INTERFACES (PLATFORM ADMIN)
    # --------------------------------------------------------------------------
    def list_events(
        self,
        limit: int = 100,
        offset: int = 0,
        severity_filter: Optional[str] = None,
        event_type_filter: Optional[str] = None,
        tenant_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns paginated, sanitized audit records from durable store."""
        events, _ = self._store.list_events(
            limit=limit,
            offset=offset,
            severity=severity_filter,
            event_type=event_type_filter,
            tenant_id=tenant_filter
        )
        return events

    def list_events_paginated(
        self,
        limit: int = 100,
        offset: int = 0,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        since_timestamp: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self._store.list_events(
            limit=limit,
            offset=offset,
            severity=severity,
            event_type=event_type,
            tenant_id=tenant_id,
            since_timestamp=since_timestamp
        )

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self._store.list_incidents(
            status=status,
            severity=severity,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset
        )

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get_incident(incident_id)

    def update_incident(
        self,
        incident_id: str,
        status: Optional[str] = None,
        acknowledged_by: Optional[str] = None,
        resolution_note: Optional[str] = None,
        resolved_by: Optional[str] = None
    ) -> bool:
        return self._store.update_incident(
            incident_id=incident_id,
            status=status,
            acknowledged_by=acknowledged_by,
            resolution_note=resolution_note,
            resolved_by=resolved_by
        )

    def get_overview_metrics(self) -> Dict[str, Any]:
        """Synthesizes high-level statistics for platform Security Shield center."""
        counts = self._store.count_events_summary()
        smtp_status = self._mailer.get_status()
        return {
            **counts,
            "smtp": smtp_status,
            "target_alert_email": self._mailer.recipient,
            "dispatcher_running": alert_dispatcher.is_running(),
            "dispatcher_health": alert_dispatcher.get_health(),
            "shield_version": "v1.2.0-a6.2",
            "active_rules_count": 15,
            "incident_grouping_window_minutes": 15
        }

    # --------------------------------------------------------------------------
    # SERVER-AUTHORITATIVE PREVIEW SESSIONS
    # --------------------------------------------------------------------------
    def register_preview_session(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str = "system"
    ) -> None:
        self._store.register_preview_session(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id
        )

    def is_preview_session(self, session_id: str) -> bool:
        return self._store.is_valid_preview_session(session_id)

    def clear(self):
        """Testing utility to clear both in-memory buffer and isolated database."""
        with self._buf_lock:
            self._buffer.clear()
        self._store.clear()


# Global singleton instance
security_shield = SecurityShield()


def emit_security_event(
    event_type: SecurityEventType | str,
    severity: SecuritySeverity | str,
    actor_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    action_taken: str = "BLOCKED",
    outcome: str = "ATTACK_PREVENTED",
    details: Optional[Dict[str, Any]] = None,
) -> SecurityAuditRecord:
    """Convenience helper to emit a security audit event."""
    return security_shield.emit(
        event_type=event_type,
        severity=severity,
        actor_id=actor_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        action_taken=action_taken,
        outcome=outcome,
        details=details
    )
