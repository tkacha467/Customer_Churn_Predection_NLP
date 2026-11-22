"""
VRAJA AI Security Shield — Alert Mailer & Notification Pipeline (Phase A6.1).
Delivers structured, PII-safe security notifications to platform administrators.

Target Preferred Recipient: vajra.techworks@gmail.com
"""

import os
import smtplib
import time
import uuid
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, List, Tuple


DEFAULT_ALERT_EMAIL = "vajra.techworks@gmail.com"


class AlertMailer:
    """Manages secure notification dispatch, SMTP transport, retry backoff, and outbox processing."""

    def __init__(self):
        pass

    @property
    def recipient(self) -> str:
        return os.getenv("ALERT_RECIPIENT_EMAIL", DEFAULT_ALERT_EMAIL).strip()

    @property
    def is_configured(self) -> bool:
        host = os.getenv("SMTP_HOST", "").strip()
        user = os.getenv("SMTP_USER", "").strip()
        pwd = os.getenv("SMTP_PASSWORD", "").strip()
        return bool(host and user and pwd)

    @property
    def is_mock_transport(self) -> bool:
        mock_env = os.getenv("MOCK_EMAIL_TRANSPORT", "").strip().lower()
        if mock_env in ("0", "false", "no"):
            return False
        if mock_env in ("1", "true", "yes"):
            return True
        return not self.is_configured

    @property
    def allow_live_smtp_test(self) -> bool:
        """Explicit authorization flag required for real outbound SMTP test dispatch."""
        return os.getenv("ALLOW_LIVE_SMTP_TEST", "").strip().lower() in ("1", "true", "yes")

    @property
    def is_incident_dispatch_paused(self) -> bool:
        """Explicit flag to pause regular incident outbox processing (e.g. during staging synthetic tests)."""
        return os.getenv("PAUSE_INCIDENT_DISPATCH", "").strip().lower() in ("1", "true", "yes")

    def get_status(self) -> Dict[str, Any]:
        """Returns non-sensitive SMTP configuration state."""
        return {
            "status": "CONFIGURED" if self.is_configured else "NOT CONFIGURED",
            "transport": "mock" if self.is_mock_transport else "smtp",
            "allow_live_smtp_test": self.allow_live_smtp_test,
            "target_recipient": self.recipient,
            "smtp_host": os.getenv("SMTP_HOST", "none"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
            "smtp_from": os.getenv("SMTP_FROM", "security@vraja.ai"),
            "incident_dispatch_paused": self.is_incident_dispatch_paused
        }

    def send_synthetic_test_alert(
        self,
        initiated_by: str,
        store: Optional[Any] = None,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches exactly ONE synthetic security notification to the approved recipient (vajra.techworks@gmail.com).
        Does NOT touch, retry, or alter unrelated production incidents in the outbox.
        Enforces fail-closed live testing authorization via ALLOW_LIVE_SMTP_TEST=true.
        Queues durable synthetic test jobs without blocking HTTP worker threads on live network calls.
        """
        target_recip = recipient or self.recipient
        if target_recip != DEFAULT_ALERT_EMAIL:
            return {
                "status": "REJECTED_UNAUTHORIZED_RECIPIENT",
                "message": f"Recipient '{target_recip}' is not authorized. Must be {DEFAULT_ALERT_EMAIL}.",
                "recipient": target_recip,
                "target_recipient": DEFAULT_ALERT_EMAIL,
                "is_synthetic": True,
            }

        sec_store = store
        if sec_store is None:
            try:
                from backend.app.core.security.security_store import SecurityStore
                sec_store = SecurityStore()
            except Exception:
                sec_store = None

        test_id = f"syn_test_{uuid.uuid4().hex[:8]}"
        synthetic_incident = {
            "incident_id": test_id,
            "event_type": "SYNTHETIC_SECURITY_TEST",
            "severity": "HIGH",
            "title": "Synthetic Staging Alert Verification",
            "affected_tenant": "staging-validation",
            "event_count": 1,
            "last_observed_at": time.time(),
            "description": f"Authorized synthetic security test alert initiated by platform admin {initiated_by} to verify notification transport.",
        }

        subject, text_body, html_body = self.format_incident_email(synthetic_incident)
        full_subject = f"[VRAJA AI STAGING TEST] {subject}"

        # 1. Unconfigured credentials check (when mock mode disabled)
        if not self.is_configured and not self.is_mock_transport:
            if sec_store:
                sec_store.record_synthetic_test(
                    test_id=test_id,
                    recipient=target_recip,
                    subject=full_subject,
                    body_text=text_body,
                    body_html=html_body,
                    status="not_configured",
                    initiated_by=initiated_by,
                    last_error="Live SMTP credentials are not configured"
                )
            return {
                "status": "NOT CONFIGURED",
                "message": "Live SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) are not configured.",
                "test_id": test_id,
                "incident_id": test_id,
                "recipient": target_recip,
                "target_recipient": DEFAULT_ALERT_EMAIL,
                "is_synthetic": True,
            }

        # 2. Mock Transport Delivery (Instantaneous, PII-safe simulation)
        if self.is_mock_transport:
            if sec_store:
                sec_store.record_synthetic_test(
                    test_id=test_id,
                    recipient=target_recip,
                    subject=full_subject,
                    body_text=text_body,
                    body_html=html_body,
                    status="mock_sent",
                    initiated_by=initiated_by
                )
            return {
                "status": "MOCK_SENT",
                "delivery_mode": "mock_sent",
                "test_id": test_id,
                "incident_id": test_id,
                "recipient": target_recip,
                "target_recipient": DEFAULT_ALERT_EMAIL,
                "is_synthetic": True,
                "message": "Synthetic alert sent successfully via mock transport.",
                "timestamp": time.time(),
            }

        # 3. Live SMTP Authorization Guard (Fail-Closed)
        if not self.allow_live_smtp_test:
            if sec_store:
                sec_store.record_synthetic_test(
                    test_id=test_id,
                    recipient=target_recip,
                    subject=full_subject,
                    body_text=text_body,
                    body_html=html_body,
                    status="rejected_missing_live_flag",
                    initiated_by=initiated_by,
                    last_error="ALLOW_LIVE_SMTP_TEST=true is not set"
                )
            return {
                "status": "REJECTED_MISSING_LIVE_FLAG",
                "message": "Live SMTP test is disabled. Explicit configuration ALLOW_LIVE_SMTP_TEST=true is required.",
                "test_id": test_id,
                "incident_id": test_id,
                "recipient": target_recip,
                "target_recipient": DEFAULT_ALERT_EMAIL,
                "is_synthetic": True,
            }

        # 3b. Staging Single-Email Hardening Guard (Fail-Closed if Incident Dispatch is not paused)
        if not self.is_mock_transport and os.getenv("ENVIRONMENT", "").strip().lower() == "staging" and not self.is_incident_dispatch_paused:
            if sec_store:
                sec_store.record_synthetic_test(
                    test_id=test_id,
                    recipient=target_recip,
                    subject=full_subject,
                    body_text=text_body,
                    body_html=html_body,
                    status="rejected_incident_dispatch_not_paused",
                    initiated_by=initiated_by,
                    last_error="PAUSE_INCIDENT_DISPATCH=true is required in staging before live synthetic test"
                )
            return {
                "status": "REJECTED_INCIDENT_DISPATCH_NOT_PAUSED",
                "message": "Live synthetic SMTP test rejected: regular incident dispatch must be explicitly paused via PAUSE_INCIDENT_DISPATCH=true in staging to prevent uncontrolled regular incident emails.",
                "test_id": test_id,
                "incident_id": test_id,
                "recipient": target_recip,
                "target_recipient": DEFAULT_ALERT_EMAIL,
                "is_synthetic": True,
            }

        # 4. Authorized Live SMTP Dispatch (Durable Queueing with Non-Blocking Asynchronous Background Delivery)
        queued_at = time.time()
        if sec_store:
            sec_store.record_synthetic_test(
                test_id=test_id,
                recipient=target_recip,
                subject=full_subject,
                body_text=text_body,
                body_html=html_body,
                status="queued",
                initiated_by=initiated_by
            )

        def _async_live_dispatch():
            # Dispatch-time authorization check (fail-closed)
            now = time.time()
            if now - queued_at > 300.0:
                if sec_store:
                    sec_store.update_synthetic_test_status(
                        test_id=test_id,
                        status="expired",
                        completed_at=now,
                        last_error="Synthetic test expired (TTL 300s exceeded before dispatch)."
                    )
                return

            if not self.allow_live_smtp_test:
                if sec_store:
                    sec_store.update_synthetic_test_status(
                        test_id=test_id,
                        status="cancelled_missing_live_flag",
                        completed_at=now,
                        last_error="Live SMTP test authorization was revoked or inactive at dispatch time."
                    )
                return

            if os.getenv("ENVIRONMENT", "").strip().lower() == "staging" and not self.is_incident_dispatch_paused:
                if sec_store:
                    sec_store.update_synthetic_test_status(
                        test_id=test_id,
                        status="cancelled_incident_dispatch_not_paused",
                        completed_at=now,
                        last_error="Live synthetic test aborted: PAUSE_INCIDENT_DISPATCH=true is not set in staging."
                    )
                return

            if not self.is_configured:
                if sec_store:
                    sec_store.update_synthetic_test_status(
                        test_id=test_id,
                        status="not_configured",
                        completed_at=now,
                        last_error="Live SMTP credentials missing at dispatch time."
                    )
                return

            if target_recip != DEFAULT_ALERT_EMAIL:
                if sec_store:
                    sec_store.update_synthetic_test_status(
                        test_id=test_id,
                        status="rejected_unauthorized_recipient",
                        completed_at=now,
                        last_error=f"Unauthorized recipient '{target_recip}' at dispatch time."
                    )
                return

            success, err = self.send_email_sync(
                recipient=target_recip,
                subject=full_subject,
                text_body=text_body,
                html_body=html_body,
            )
            if sec_store:
                sec_store.update_synthetic_test_status(
                    test_id=test_id,
                    status="sent" if success else "failed",
                    completed_at=time.time(),
                    last_error=err
                )

        # Trigger background delivery thread so HTTP request returns immediately
        dispatch_thread = threading.Thread(target=_async_live_dispatch, daemon=True, name=f"SyntheticDispatch-{test_id}")
        dispatch_thread.start()

        return {
            "status": "QUEUED",
            "delivery_mode": "queued",
            "test_id": test_id,
            "incident_id": test_id,
            "recipient": target_recip,
            "target_recipient": DEFAULT_ALERT_EMAIL,
            "is_synthetic": True,
            "message": "Synthetic test alert queued for background delivery without blocking HTTP worker.",
            "timestamp": time.time(),
        }

    def process_synthetic_tests(self, store: Any, ttl_seconds: float = 300.0) -> Dict[str, int]:
        """
        Recovers and processes pending/queued synthetic test alerts without touching incident outbox.
        Enforces dispatch-time authorization, recipient allowlist, and strict TTL expiry (300s).
        """
        claimed = store.claim_pending_synthetic_tests(limit=10, ttl_seconds=ttl_seconds)
        sent = 0
        failed = 0
        now = time.time()
        for item in claimed:
            test_id = item["test_id"]

            # 1. Dispatch-time TTL Expiry check
            if now - item.get("created_at", now) > ttl_seconds:
                store.update_synthetic_test_status(
                    test_id,
                    "expired",
                    completed_at=now,
                    last_error=f"Synthetic test expired (created > {ttl_seconds}s ago)."
                )
                failed += 1
                continue

            # 2. Dispatch-time credential check
            if not self.is_configured:
                store.update_synthetic_test_status(
                    test_id,
                    "not_configured",
                    completed_at=now,
                    last_error="Credentials not configured at dispatch time"
                )
                failed += 1
                continue

            # 3. Dispatch-time live authorization flag check
            if not self.allow_live_smtp_test:
                store.update_synthetic_test_status(
                    test_id,
                    "cancelled_missing_live_flag",
                    completed_at=now,
                    last_error="ALLOW_LIVE_SMTP_TEST not enabled at dispatch time"
                )
                failed += 1
                continue

            # 3b. Dispatch-time staging pause check: in staging, fail closed if incident dispatch is not paused
            if not self.is_mock_transport and os.getenv("ENVIRONMENT", "").strip().lower() == "staging" and not self.is_incident_dispatch_paused:
                store.update_synthetic_test_status(
                    test_id,
                    "cancelled_incident_dispatch_not_paused",
                    completed_at=now,
                    last_error="PAUSE_INCIDENT_DISPATCH=true is required in staging at worker execution time"
                )
                failed += 1
                continue

            # 4. Dispatch-time recipient allowlist check
            if item.get("recipient") != DEFAULT_ALERT_EMAIL:
                store.update_synthetic_test_status(
                    test_id,
                    "rejected_unauthorized_recipient",
                    completed_at=now,
                    last_error=f"Unauthorized recipient {item.get('recipient')} at dispatch time"
                )
                failed += 1
                continue

            # 5. Outbound transport execution
            success, err = self.send_email_sync(
                recipient=item["recipient"],
                subject=item["subject"],
                text_body=item["body_text"],
                html_body=item["body_html"]
            )
            store.update_synthetic_test_status(test_id, "sent" if success else "failed", completed_at=time.time(), last_error=err)
            if success:
                sent += 1
            else:
                failed += 1
        return {"processed": len(claimed), "sent": sent, "failed": failed}

    def format_incident_email(self, incident: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Creates clean, PII-free plaintext and HTML email notifications.
        Returns (subject, text_body, html_body).
        """
        severity = incident.get("severity", "HIGH").upper()
        event_type = incident.get("event_type", "SECURITY_ALERT")
        title = incident.get("title") or event_type.replace("_", " ").title()
        inc_id = incident.get("incident_id", "unknown")
        tenant = incident.get("affected_tenant") or "Global Platform"
        count = incident.get("event_count", 1)
        last_seen = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(incident.get("last_observed_at", time.time())))

        subject = f"[VRAJA AI SECURITY] {severity} — {title}"

        text_body = f"""
VRAJA AI SECURITY SHIELD INCIDENT ALERT
========================================
Severity:     {severity}
Incident ID:  {inc_id}
Event Type:   {event_type}
Tenant:       {tenant}
Total Events: {count}
Last Seen:    {last_seen}

Description:
{incident.get("description", "A security anomaly was detected and blocked by VRAJA AI Security Shield.")}

Action Taken:
Request blocked and logged in the immutable security audit buffer.

Security Center Dashboard:
https://app.vraja.ai/admin (or http://localhost:5173/admin)

Note: This automated notification contains sanitized operational metadata only.
Raw passwords, authentication cookies, tokens, and customer review contents
are strictly redacted by Security Shield.
""".strip()

        severity_color = "#DC2626" if severity == "CRITICAL" else ("#EA580C" if severity == "HIGH" else "#D97706")

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F9FAFB; padding: 24px; color: #1F2937;">
  <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; border: 1px solid #E5E7EB; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
    <div style="background-color: #174D3A; padding: 20px 24px; border-bottom: 3px solid {severity_color};">
      <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700;">🛡️ VRAJA AI Security Shield</h2>
      <p style="color: #A7F3D0; margin: 4px 0 0 0; font-size: 13px;">Security Operations Center • Automated Alert</p>
    </div>

    <div style="padding: 24px;">
      <div style="display: inline-block; background-color: {severity_color}; color: #FFFFFF; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 4px; margin-bottom: 16px;">
        {severity} SEVERITY
      </div>

      <h3 style="margin: 0 0 12px 0; font-size: 18px; color: #111827;">{title}</h3>
      <p style="color: #4B5563; font-size: 14px; line-height: 1.5; margin: 0 0 20px 0;">
        {incident.get("description", "A security incident was intercepted and prevented by the security engine.")}
      </p>

      <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 24px;">
        <tr style="border-bottom: 1px solid #F3F4F6;">
          <td style="padding: 8px 0; color: #6B7280; font-weight: 600; width: 140px;">Incident ID</td>
          <td style="padding: 8px 0; color: #111827; font-family: monospace;">{inc_id}</td>
        </tr>
        <tr style="border-bottom: 1px solid #F3F4F6;">
          <td style="padding: 8px 0; color: #6B7280; font-weight: 600;">Event Type</td>
          <td style="padding: 8px 0; color: #111827;">{event_type}</td>
        </tr>
        <tr style="border-bottom: 1px solid #F3F4F6;">
          <td style="padding: 8px 0; color: #6B7280; font-weight: 600;">Affected Tenant</td>
          <td style="padding: 8px 0; color: #111827;">{tenant}</td>
        </tr>
        <tr style="border-bottom: 1px solid #F3F4F6;">
          <td style="padding: 8px 0; color: #6B7280; font-weight: 600;">Total Interceptions</td>
          <td style="padding: 8px 0; color: #111827;">{count}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6B7280; font-weight: 600;">Timestamp</td>
          <td style="padding: 8px 0; color: #111827;">{last_seen}</td>
        </tr>
      </table>

      <div style="background-color: #F3F4F6; border-radius: 6px; padding: 12px 16px; margin-bottom: 24px; font-size: 13px; color: #374151;">
        <strong>Action Taken:</strong> Malicious attempt was immediately rejected (HTTP 401/403/429) and logged. No data leaked.
      </div>

      <div style="text-align: center; margin-top: 24px;">
        <a href="http://localhost:5173/admin" style="background-color: #174D3A; color: #FFFFFF; text-decoration: none; font-size: 14px; font-weight: 600; padding: 10px 24px; border-radius: 6px; display: inline-block;">
          Open Security Center Dashboard
        </a>
      </div>
    </div>

    <div style="background-color: #F9FAFB; padding: 16px 24px; border-top: 1px solid #E5E7EB; font-size: 11px; color: #9CA3AF; text-align: center;">
      VRAJA AI Enterprise Security Shield • PII Redaction Guaranteed • Vajra Techworks
    </div>
  </div>
</body>
</html>
""".strip()

        return subject, text_body, html_body

    def send_email_sync(
        self,
        recipient: str,
        subject: str,
        text_body: str,
        html_body: str
    ) -> Tuple[bool, Optional[str]]:
        """Sends an email synchronously via SMTP or Mock Transport."""
        if self.is_mock_transport:
            # Mock transport: records simulated delivery without external network call
            return True, None

        # Live SMTP delivery
        host = os.getenv("SMTP_HOST", "")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER", "")
        pwd = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("SMTP_FROM", "security@vraja.ai")
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = recipient
        msg["Message-ID"] = f"<vraja-{uuid.uuid4().hex}@vraja.ai>"
        msg["X-Vraja-Incident-Type"] = "SECURITY_NOTIFICATION"

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=10.0)
            else:
                server = smtplib.SMTP(host, port, timeout=10.0)
                if use_tls:
                    server.starttls()

            if user and pwd:
                server.login(user, pwd)

            server.sendmail(from_email, [recipient], msg.as_string())
            server.quit()
            return True, None
        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e)}"
            return False, err_msg

    def process_outbox(
        self,
        store: Any,
        worker_id: Optional[str] = None,
        max_batch: int = 10
    ) -> Dict[str, int]:
        """
        Atomically leases and processes outbox alert items.
        Differentiates between 'mock_sent' (simulation) and 'sent' (live SMTP delivery).
        Retries failed attempts with exponential backoff (30s, 120s, 600s),
        dead-lettering after 3 failed attempts.
        """
        if self.is_incident_dispatch_paused:
            return {
                "processed": 0,
                "sent": 0,
                "mock_sent": 0,
                "failed": 0,
                "dead_letter": 0,
                "paused": True
            }

        w_id = worker_id or f"worker_{uuid.uuid4().hex[:6]}"
        claimed_items = store.claim_outbox_items(worker_id=w_id, limit=max_batch, lease_seconds=300.0)

        sent_count = 0
        mock_sent_count = 0
        failed_count = 0
        dead_count = 0

        now = time.time()
        for item in claimed_items:
            is_mock = self.is_mock_transport
            success, err = self.send_email_sync(
                recipient=item["recipient"],
                subject=item["subject"],
                text_body=item["body_text"],
                html_body=item["body_html"]
            )

            if success:
                target_status = "mock_sent" if is_mock else "sent"
                store.update_outbox_status(item["id"], status=target_status)
                if is_mock:
                    mock_sent_count += 1
                else:
                    sent_count += 1
            else:
                attempts = item.get("attempts", 0) + 1
                if attempts >= item.get("max_attempts", 3):
                    store.update_outbox_status(item["id"], status="dead_letter", last_error=err)
                    dead_count += 1
                else:
                    # Exponential backoff: attempt 1 -> 30s, attempt 2 -> 120s, attempt 3 -> 600s
                    backoff = 30.0 if attempts == 1 else (120.0 if attempts == 2 else 600.0)
                    next_retry = now + backoff
                    store.update_outbox_status(
                        item["id"],
                        status="pending",
                        last_error=err,
                        next_retry_at=next_retry
                    )
                    failed_count += 1

        return {
            "processed": len(claimed_items),
            "sent": sent_count,
            "mock_sent": mock_sent_count,
            "failed": failed_count,
            "dead_letter": dead_count
        }


class AlertDispatcherWorker:
    """Decoupled asynchronous daemon worker for dispatching outbox security alerts."""

    def __init__(self, store: Any = None, mailer: Optional[AlertMailer] = None, poll_interval: float = 5.0):
        self._store = store
        self.mailer = mailer or alert_mailer
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_run_at: Optional[float] = None
        self._last_error: Optional[str] = None
        self._total_processed: int = 0

    @property
    def store(self):
        if self._store is None:
            from backend.app.core.security.security_store import SecurityStore
            self._store = SecurityStore()
        return self._store

    def start(self):
        """Starts the background worker thread if not already running."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="AlertDispatcherWorker")
        self._thread.start()

    def stop(self, timeout: float = 2.0):
        """Signals the worker to stop and waits for exit."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def get_health(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running(),
            "poll_interval_seconds": self.poll_interval,
            "last_run_at": self._last_run_at,
            "last_error": self._last_error,
            "total_processed": self._total_processed,
            "worker_thread_alive": bool(self._thread and self._thread.is_alive())
        }

    def _run(self):
        worker_id = f"worker_{uuid.uuid4().hex[:6]}"
        while not self._stop_event.is_set():
            try:
                res = self.mailer.process_outbox(self.store, worker_id=worker_id, max_batch=10)
                syn_res = self.mailer.process_synthetic_tests(self.store)
                self._last_run_at = time.time()
                self._last_error = None
                self._total_processed += (res.get("processed", 0) + syn_res.get("processed", 0))
            except Exception as e:
                self._last_run_at = time.time()
                self._last_error = f"{type(e).__name__}: {str(e)}"
                print(f"[AlertDispatcherWorker WARNING] Error in outbox processing: {e}")
            self._stop_event.wait(self.poll_interval)


alert_mailer = AlertMailer()
alert_dispatcher = AlertDispatcherWorker(mailer=alert_mailer)
