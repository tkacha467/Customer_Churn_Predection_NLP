"""
VRAJA AI Security Shield Package (Phase A6).
Enterprise structured security event logging, incident response,
and notification pipeline.
"""

from backend.app.core.security.security_shield import (
    SecurityEventType,
    SecuritySeverity,
    SecurityShield,
    security_shield,
    emit_security_event,
    SecurityAuditRecord,
)
from backend.app.core.security.security_store import SecurityStore
from backend.app.core.security.alert_mailer import AlertMailer, alert_mailer, alert_dispatcher, AlertDispatcherWorker

__all__ = [
    "SecurityEventType",
    "SecuritySeverity",
    "SecurityShield",
    "security_shield",
    "emit_security_event",
    "SecurityAuditRecord",
    "SecurityStore",
    "AlertMailer",
    "alert_mailer",
    "alert_dispatcher",
    "AlertDispatcherWorker",
]
