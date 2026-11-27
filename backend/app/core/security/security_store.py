"""
VRAJA AI Security Shield — Durable Security Store (Phase A6.1).
Isolated SQLite persistence layer for enterprise security audit logs, incidents,
alert queues, and server-authorized preview sessions.

Constraints:
- Isolated from production database reviews.sqlite3.
- Process-restart surviving, multi-worker safe (WAL mode + BEGIN IMMEDIATE transactions).
- Atomic outbox leasing prevents duplicate email dispatches.
- Multi-dimensional incident fingerprinting prevents false incident conflation.
- Retention pruning NEVER removes active or investigating incidents.
- Fail-safe: database errors are gracefully handled without crashing customer HTTP requests.
"""

import os
import time
import uuid
import json
import sqlite3
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


_REPO_ROOT = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists() or (p / "backend").exists() or (p / "Backend").exists()), Path(__file__).resolve().parents[4])
DEFAULT_SECURITY_DB = _REPO_ROOT / "Project_Files" / "Data" / "security_shield.sqlite3"


def get_security_db_path() -> str:
    explicit = os.getenv("SECURITY_DB_PATH", "").strip()
    if explicit:
        return explicit

    is_test_mode = (
        os.getenv("ENVIRONMENT", "").strip().lower() == "test"
        or "PYTEST_CURRENT_TEST" in os.environ
    )
    if is_test_mode:
        import tempfile
        return str(Path(tempfile.gettempdir()) / "test_security_shield_default.sqlite3")

    DEFAULT_SECURITY_DB.parent.mkdir(parents=True, exist_ok=True)
    return str(DEFAULT_SECURITY_DB)


class SecurityStore:
    """Thread-safe, multi-worker resilient SQLite storage for security telemetry."""

    _instances: Dict[str, "SecurityStore"] = {}
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[str] = None):
        target_path = db_path or get_security_db_path()
        is_test_mode = (
            os.getenv("ENVIRONMENT", "").strip().lower() == "test"
            or "PYTEST_CURRENT_TEST" in os.environ
        )
        _repo_root = _REPO_ROOT
        _protected_dbs = [
            DEFAULT_SECURITY_DB.resolve(),
            (_repo_root / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3").resolve(),
            (_repo_root / "data" / "nasta-ghar" / "reviews.sqlite3").resolve(),
        ]
        if is_test_mode and Path(target_path).resolve() in _protected_dbs:
            raise RuntimeError(
                f"TEST-ENVIRONMENT DATABASE SAFETY GUARD TRIGGERED: "
                f"SecurityStore attempted to connect to production database '{target_path}' during test execution. "
                f"Automated tests must explicitly provide an isolated security database path via tmp_path or SECURITY_DB_PATH."
            )

        with cls._lock:
            if target_path not in cls._instances:
                instance = super().__new__(cls)
                instance._db_path = target_path
                instance._local = threading.local()
                instance._init_schema()
                cls._instances[target_path] = instance
            return cls._instances[target_path]

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high-concurrency multi-worker reads/writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_schema(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            # 1. Security Events Audit Trail
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    actor_id TEXT,
                    tenant_id TEXT,
                    correlation_id TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sec_events_ts ON security_events(timestamp DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sec_events_type ON security_events(event_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sec_events_sev ON security_events(severity);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sec_events_tenant ON security_events(tenant_id);")

            # 2. Security Incidents (Aggregated Event Incidents with Multi-Dimensional Fingerprint)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_incidents (
                    incident_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_tenant TEXT,
                    actor_id TEXT,
                    status TEXT NOT NULL DEFAULT 'open', -- open, investigating, resolved
                    event_count INTEGER NOT NULL DEFAULT 1,
                    first_observed_at REAL NOT NULL,
                    last_observed_at REAL NOT NULL,
                    acknowledged_by TEXT,
                    acknowledged_at REAL,
                    resolution_note TEXT,
                    resolved_at REAL,
                    fingerprint TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_sev ON security_incidents(severity);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_last ON security_incidents(last_observed_at DESC);")

            # Backwards-compatible column upgrade for incidents
            try:
                conn.execute("ALTER TABLE security_incidents ADD COLUMN fingerprint TEXT;")
            except Exception:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_fp ON security_incidents(fingerprint);")

            # 3. Security Alert Outbox (Durable Email Notification Queue with Atomic Leases)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_alert_outbox (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body_text TEXT NOT NULL,
                    body_html TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending', -- pending, claimed, sent, mock_sent, failed, dead_letter
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    last_error TEXT,
                    created_at REAL NOT NULL,
                    sent_at REAL,
                    next_retry_at REAL,
                    claimed_by TEXT,
                    claimed_at REAL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outbox_status ON security_alert_outbox(status);")

            # Backwards-compatible column upgrades for outbox
            try:
                conn.execute("ALTER TABLE security_alert_outbox ADD COLUMN claimed_by TEXT;")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE security_alert_outbox ADD COLUMN claimed_at REAL;")
            except Exception:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outbox_claim ON security_alert_outbox(status, claimed_at);")

            # 4. Authenticated Server-Issued Preview Sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preview_sessions (
                    session_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    created_by_user_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_preview_expires ON preview_sessions(expires_at);")

            # 5. Isolated Durable Synthetic Security Test Queue (Decoupled from Incident Outbox)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_synthetic_tests (
                    test_id TEXT PRIMARY KEY,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body_text TEXT NOT NULL,
                    body_html TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    initiated_by TEXT NOT NULL,
                    is_synthetic INTEGER NOT NULL DEFAULT 1,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    last_error TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_syn_tests_status ON security_synthetic_tests(status);")

    # --------------------------------------------------------------------------
    # EVENT AUDIT TRAIL OPERATIONS
    # --------------------------------------------------------------------------
    def record_event(self, record_dict: Dict[str, Any]) -> str:
        """Atomically persists a sanitized security event record."""
        event_id = record_dict.get("event_id") or str(uuid.uuid4())
        ts = record_dict.get("timestamp") or time.time()
        details_json = json.dumps(record_dict.get("details", {}), ensure_ascii=False)

        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT INTO security_events (
                        event_id, event_type, severity, timestamp, actor_id,
                        tenant_id, correlation_id, action_taken, outcome, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    record_dict.get("event_type", "UNKNOWN"),
                    record_dict.get("severity", "LOW"),
                    ts,
                    record_dict.get("actor_id"),
                    record_dict.get("tenant_id"),
                    record_dict.get("correlation_id") or str(uuid.uuid4()),
                    record_dict.get("action_taken", "BLOCKED"),
                    record_dict.get("outcome", "ATTACK_PREVENTED"),
                    details_json
                ))
            return event_id
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] record_event failed: {e}")
            return event_id

    def list_events(
        self,
        limit: int = 100,
        offset: int = 0,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        since_timestamp: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Lists events with server-side pagination and filters, returning (events, total_count)."""
        where_clauses = []
        params: List[Any] = []

        if severity:
            where_clauses.append("severity = ?")
            params.append(severity)
        if event_type:
            where_clauses.append("event_type = ?")
            params.append(event_type)
        if tenant_id:
            where_clauses.append("tenant_id = ?")
            params.append(tenant_id)
        if since_timestamp:
            where_clauses.append("timestamp >= ?")
            params.append(since_timestamp)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        try:
            with self._connect() as conn:
                count_row = conn.execute(f"SELECT COUNT(*) FROM security_events {where_sql}", params).fetchone()
                total_count = count_row[0] if count_row else 0

                query_sql = f"""
                    SELECT * FROM security_events
                    {where_sql}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """
                rows = conn.execute(query_sql, params + [limit, offset]).fetchall()

                events = []
                for r in rows:
                    item = dict(r)
                    try:
                        item["details"] = json.loads(item["details_json"])
                    except Exception:
                        item["details"] = {}
                    del item["details_json"]
                    events.append(item)

                return events, total_count
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] list_events failed: {e}")
            return [], 0

    def count_events_summary(self) -> Dict[str, Any]:
        """Aggregates security metrics for platform overview dashboard."""
        now = time.time()
        last_24h = now - 86400.0

        try:
            with self._connect() as conn:
                total_events = conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
                events_24h = conn.execute("SELECT COUNT(*) FROM security_events WHERE timestamp >= ?", (last_24h,)).fetchone()[0]

                open_incidents = conn.execute("SELECT COUNT(*) FROM security_incidents WHERE status = 'open'").fetchone()[0]
                investigating_incidents = conn.execute("SELECT COUNT(*) FROM security_incidents WHERE status = 'investigating'").fetchone()[0]
                high_critical_incidents = conn.execute(
                    "SELECT COUNT(*) FROM security_incidents WHERE status IN ('open', 'investigating') AND severity IN ('HIGH', 'CRITICAL')"
                ).fetchone()[0]

                outbox_pending = conn.execute("SELECT COUNT(*) FROM security_alert_outbox WHERE status IN ('pending', 'claimed')").fetchone()[0]
                outbox_failed = conn.execute("SELECT COUNT(*) FROM security_alert_outbox WHERE status IN ('failed', 'dead_letter')").fetchone()[0]

                sev_rows = conn.execute("""
                    SELECT severity, COUNT(*) FROM security_events
                    WHERE timestamp >= ? GROUP BY severity
                """, (last_24h,)).fetchall()
                sev_dist = {r[0]: r[1] for r in sev_rows}

                return {
                    "total_events": total_events,
                    "events_last_24h": events_24h,
                    "open_incidents": open_incidents,
                    "investigating_incidents": investigating_incidents,
                    "high_critical_incidents": high_critical_incidents,
                    "outbox_pending": outbox_pending,
                    "outbox_failed": outbox_failed,
                    "severity_distribution_24h": sev_dist,
                }
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] count_events_summary failed: {e}")
            return {
                "total_events": 0, "events_last_24h": 0, "open_incidents": 0,
                "investigating_incidents": 0, "high_critical_incidents": 0,
                "outbox_pending": 0, "outbox_failed": 0, "severity_distribution_24h": {}
            }

    # --------------------------------------------------------------------------
    # INCIDENT MANAGEMENT & MULTI-DIMENSIONAL FINGERPRINTING
    # --------------------------------------------------------------------------
    @staticmethod
    def compute_fingerprint(
        event_type: str,
        affected_tenant: Optional[str] = None,
        actor_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> str:
        """Computes a collision-resistant multi-dimensional fingerprint for incident grouping."""
        components = [
            str(event_type).strip(),
            str(affected_tenant or "").strip(),
            str(actor_id or "").strip(),
            str(endpoint or "").strip(),
        ]
        return hashlib.sha256(":".join(components).encode("utf-8")).hexdigest()[:16]

    def aggregate_event_into_incident(
        self,
        event_type: str,
        severity: str,
        affected_tenant: Optional[str],
        actor_id: Optional[str],
        title: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        window_seconds: float = 900.0  # 15 minutes
    ) -> Tuple[str, bool]:
        """
        Groups repeated security events into a single incident to prevent notification storms.
        Multi-dimensional grouping separates different endpoints, tenants, and actors.
        Resolved incidents are NEVER updated (a new incident is opened).
        Concurrent worker calls are safely synchronized via BEGIN IMMEDIATE.
        Returns (incident_id, is_new_incident).
        """
        now = time.time()
        threshold_time = now - window_seconds
        endpoint = ""
        if isinstance(details, dict):
            endpoint = str(details.get("endpoint") or details.get("path") or "")

        fingerprint = self.compute_fingerprint(event_type, affected_tenant, actor_id, endpoint)

        try:
            with self._connect() as conn:
                conn.execute("BEGIN IMMEDIATE")

                # Match only ACTIVE (open or investigating) incidents with matching fingerprint within window
                row = conn.execute("""
                    SELECT incident_id, event_count, severity FROM security_incidents
                    WHERE fingerprint = ?
                      AND status IN ('open', 'investigating')
                      AND last_observed_at >= ?
                    ORDER BY last_observed_at DESC
                    LIMIT 1
                """, (fingerprint, threshold_time)).fetchone()

                if row:
                    incident_id = row["incident_id"]
                    conn.execute("""
                        UPDATE security_incidents
                        SET event_count = event_count + 1,
                            last_observed_at = ?,
                            severity = CASE
                                WHEN ? = 'CRITICAL' THEN 'CRITICAL'
                                WHEN ? = 'HIGH' AND severity != 'CRITICAL' THEN 'HIGH'
                                ELSE severity
                            END
                        WHERE incident_id = ?
                    """, (now, severity, severity, incident_id))
                    conn.commit()
                    return incident_id, False
                else:
                    new_id = f"inc_{uuid.uuid4().hex[:10]}"
                    conn.execute("""
                        INSERT INTO security_incidents (
                            incident_id, event_type, severity, title, description,
                            affected_tenant, actor_id, status, event_count,
                            first_observed_at, last_observed_at, fingerprint
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', 1, ?, ?, ?)
                    """, (
                        new_id, event_type, severity, title, description,
                        affected_tenant, actor_id, now, now, fingerprint
                    ))
                    conn.commit()
                    return new_id, True
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] aggregate_event_into_incident failed: {e}")
            fallback_id = f"inc_{uuid.uuid4().hex[:10]}"
            return fallback_id, True

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Returns paginated incidents list with total count."""
        where_clauses = []
        params: List[Any] = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if severity:
            where_clauses.append("severity = ?")
            params.append(severity)
        if tenant_id:
            where_clauses.append("affected_tenant = ?")
            params.append(tenant_id)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        try:
            with self._connect() as conn:
                count = conn.execute(f"SELECT COUNT(*) FROM security_incidents {where_sql}", params).fetchone()[0]

                rows = conn.execute(f"""
                    SELECT * FROM security_incidents
                    {where_sql}
                    ORDER BY last_observed_at DESC
                    LIMIT ? OFFSET ?
                """, params + [limit, offset]).fetchall()

                return [dict(r) for r in rows], count
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] list_incidents failed: {e}")
            return [], 0

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM security_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] get_incident failed: {e}")
            return None

    def update_incident(
        self,
        incident_id: str,
        status: Optional[str] = None,
        acknowledged_by: Optional[str] = None,
        resolution_note: Optional[str] = None,
        resolved_by: Optional[str] = None
    ) -> bool:
        """Updates lifecycle status of a security incident."""
        now = time.time()
        updates = []
        params: List[Any] = []

        if status:
            updates.append("status = ?")
            params.append(status)
        if acknowledged_by:
            updates.append("acknowledged_by = ?")
            updates.append("acknowledged_at = ?")
            params.extend([acknowledged_by, now])
        if resolution_note:
            updates.append("resolution_note = ?")
            params.append(resolution_note)
        if status == "resolved":
            updates.append("resolved_at = ?")
            params.append(now)

        if not updates:
            return False

        params.append(incident_id)
        try:
            with self._connect() as conn:
                cur = conn.execute(f"UPDATE security_incidents SET {', '.join(updates)} WHERE incident_id = ?", params)
                return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] update_incident failed: {e}")
            return False

    # --------------------------------------------------------------------------
    # OUTBOX / EMAIL NOTIFICATION QUEUE & ATOMIC WORKER CLAIMING
    # --------------------------------------------------------------------------
    def queue_alert(
        self,
        incident_id: str,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: str,
        severity: str
    ) -> str:
        """Enqueues a security incident alert in the durable outbox."""
        outbox_id = f"out_{uuid.uuid4().hex[:10]}"
        now = time.time()
        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT INTO security_alert_outbox (
                        id, incident_id, recipient, subject, body_text,
                        body_html, severity, status, attempts, created_at, next_retry_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)
                """, (outbox_id, incident_id, recipient, subject, body_text, body_html, severity, now, now))
            return outbox_id
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] queue_alert failed: {e}")
            return outbox_id

    def claim_outbox_items(
        self,
        worker_id: str,
        limit: int = 10,
        lease_seconds: float = 300.0
    ) -> List[Dict[str, Any]]:
        """
        Atomically leases pending or expired-lease outbox items to a specific worker.
        Guarantees that multiple concurrent workers never process the same email.
        """
        now = time.time()
        try:
            with self._connect() as conn:
                conn.execute("BEGIN IMMEDIATE")

                rows = conn.execute("""
                    SELECT id FROM security_alert_outbox
                    WHERE (
                        (status = 'pending' AND (next_retry_at IS NULL OR next_retry_at <= ?))
                        OR (status = 'claimed' AND claimed_at IS NOT NULL AND claimed_at <= ?)
                    )
                    ORDER BY created_at ASC
                    LIMIT ?
                """, (now, now - lease_seconds, limit)).fetchall()

                ids = [r["id"] for r in rows]
                if not ids:
                    return []

                placeholders = ",".join("?" for _ in ids)
                conn.execute(f"""
                    UPDATE security_alert_outbox
                    SET status = 'claimed',
                        claimed_by = ?,
                        claimed_at = ?
                    WHERE id IN ({placeholders})
                """, [worker_id, now] + ids)

                claimed_rows = conn.execute(f"""
                    SELECT * FROM security_alert_outbox
                    WHERE id IN ({placeholders})
                """, ids).fetchall()

                conn.commit()
                return [dict(r) for r in claimed_rows]
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] claim_outbox_items failed: {e}")
            return []

    def list_outbox(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        where_sql = "WHERE status = ?" if status else ""
        params = [status] if status else []

        try:
            with self._connect() as conn:
                count = conn.execute(f"SELECT COUNT(*) FROM security_alert_outbox {where_sql}", params).fetchone()[0]
                rows = conn.execute(f"""
                    SELECT * FROM security_alert_outbox
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, params + [limit, offset]).fetchall()
                return [dict(r) for r in rows], count
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] list_outbox failed: {e}")
            return [], 0

    def update_outbox_status(
        self,
        outbox_id: str,
        status: str,
        last_error: Optional[str] = None,
        next_retry_at: Optional[float] = None
    ) -> bool:
        now = time.time()
        try:
            with self._connect() as conn:
                cur = conn.execute("""
                    UPDATE security_alert_outbox
                    SET status = ?,
                        attempts = attempts + 1,
                        last_error = ?,
                        sent_at = CASE WHEN ? IN ('sent', 'mock_sent') THEN ? ELSE sent_at END,
                        next_retry_at = ?,
                        claimed_by = NULL,
                        claimed_at = NULL
                    WHERE id = ?
                """, (status, last_error, status, now, next_retry_at, outbox_id))
                return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] update_outbox_status failed: {e}")
            return False

    # --------------------------------------------------------------------------
    # SERVER-AUTHORITATIVE PREVIEW SESSIONS
    # --------------------------------------------------------------------------
    def register_preview_session(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str,
        ttl_seconds: float = 7200.0
    ) -> None:
        """Stores a server-issued preview session with absolute expiration."""
        now = time.time()
        expires = now + ttl_seconds
        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO preview_sessions (session_id, tenant_id, created_by_user_id, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, tenant_id, user_id, now, expires))
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] register_preview_session failed: {e}")

    def is_valid_preview_session(self, session_id: str) -> bool:
        """Verifies if session is legitimately registered by an authenticated manager."""
        if not session_id:
            return False
        now = time.time()
        try:
            with self._connect() as conn:
                row = conn.execute("""
                    SELECT 1 FROM preview_sessions
                    WHERE session_id = ? AND expires_at > ?
                    LIMIT 1
                """, (session_id, now)).fetchone()
                return row is not None
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] is_valid_preview_session failed: {e}")
            return False

    # --------------------------------------------------------------------------
    # MAINTENANCE & BOUNDED ROTATION (SAFE RETENTION)
    # --------------------------------------------------------------------------
    def prune_retention(self, max_events: int = 50000, retention_days: int = 90) -> Dict[str, int]:
        """
        Safely bounds storage and prunes expired records.
        CRITICAL SAFETY RULE: Open or investigating incidents are NEVER deleted.
        Only resolved incidents older than 180 days can be pruned.
        """
        cutoff_ts = time.time() - (retention_days * 86400.0)
        resolved_incidents_cutoff = time.time() - (180.0 * 86400.0)
        try:
            with self._connect() as conn:
                # 1. Delete events beyond retention window
                cur1 = conn.execute("DELETE FROM security_events WHERE timestamp < ?", (cutoff_ts,))
                deleted_by_age = cur1.rowcount

                # 2. Bound total events to max_events
                cur2 = conn.execute("""
                    DELETE FROM security_events
                    WHERE event_id IN (
                        SELECT event_id FROM security_events
                        ORDER BY timestamp DESC
                        LIMIT -1 OFFSET ?
                    )
                """, (max_events,))
                deleted_by_cap = cur2.rowcount

                # 3. Prune ONLY resolved incidents older than 180 days (NEVER open or investigating)
                cur_inc = conn.execute("""
                    DELETE FROM security_incidents
                    WHERE status = 'resolved'
                      AND resolved_at IS NOT NULL
                      AND resolved_at < ?
                """, (resolved_incidents_cutoff,))
                incidents_pruned = cur_inc.rowcount

                # 4. Delete expired preview sessions
                cur3 = conn.execute("DELETE FROM preview_sessions WHERE expires_at < ?", (time.time(),))
                deleted_previews = cur3.rowcount

                return {
                    "events_deleted_by_age": deleted_by_age,
                    "events_deleted_by_cap": deleted_by_cap,
                    "incidents_pruned": incidents_pruned,
                    "previews_pruned": deleted_previews
                }
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] prune_retention failed: {e}")
            return {"events_deleted_by_age": 0, "events_deleted_by_cap": 0, "incidents_pruned": 0, "previews_pruned": 0}

    # --------------------------------------------------------------------------
    # ISOLATED SYNTHETIC TEST NOTIFICATIONS
    # --------------------------------------------------------------------------
    def record_synthetic_test(
        self,
        test_id: str,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: str,
        status: str,
        initiated_by: str,
        last_error: Optional[str] = None
    ) -> str:
        """Atomically stores a synthetic security test record in the isolated queue."""
        now = time.time()
        completed = now if status in ("sent", "mock_sent", "not_configured", "rejected_missing_live_flag", "failed") else None
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO security_synthetic_tests (
                    test_id, recipient, subject, body_text, body_html, status,
                    initiated_by, is_synthetic, attempts, created_at, completed_at, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?)
            """, (test_id, recipient, subject, body_text, body_html, status, initiated_by, now, completed, last_error))
        return test_id

    def update_synthetic_test_status(
        self,
        test_id: str,
        status: str,
        completed_at: Optional[float] = None,
        last_error: Optional[str] = None
    ):
        """Updates delivery state of a synthetic test alert."""
        with self._connect() as conn:
            conn.execute("""
                UPDATE security_synthetic_tests
                SET status = ?, completed_at = ?, last_error = ?, attempts = attempts + 1
                WHERE test_id = ?
            """, (status, completed_at or time.time(), last_error, test_id))

    def get_synthetic_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an isolated synthetic test by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM security_synthetic_tests WHERE test_id = ?", (test_id,)).fetchone()
            return dict(row) if row else None

    def list_synthetic_tests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists synthetic test history."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM security_synthetic_tests ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def claim_pending_synthetic_tests(self, limit: int = 10, ttl_seconds: float = 300.0) -> List[Dict[str, Any]]:
        """
        Claims pending/queued synthetic tests for worker recovery.
        Automatically expires stale tests exceeding TTL (default 300s) to prevent unexpected delayed delivery.
        """
        now = time.time()
        expiry_cutoff = now - ttl_seconds
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            # 1. Expire stale queued or stuck processing tests (> ttl_seconds)
            conn.execute("""
                UPDATE security_synthetic_tests
                SET status = 'expired', completed_at = ?, last_error = 'Synthetic test expired before dispatch.'
                WHERE status IN ('queued', 'processing') AND created_at < ?
            """, (now, expiry_cutoff))

            # 2. Dead-letter tests exceeding maximum retry attempts (max 2 attempts)
            conn.execute("""
                UPDATE security_synthetic_tests
                SET status = 'failed', completed_at = ?, last_error = 'Synthetic test maximum attempts (2) exceeded.'
                WHERE status IN ('queued', 'processing') AND attempts >= 2
            """, (now,))

            # 3. Claim active queued tests
            rows = conn.execute("""
                SELECT * FROM security_synthetic_tests
                WHERE status = 'queued' AND attempts < 2
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,)).fetchall()
            items = [dict(r) for r in rows]
            for item in items:
                conn.execute("""
                    UPDATE security_synthetic_tests
                    SET status = 'processing'
                    WHERE test_id = ?
                """, (item["test_id"],))
            conn.commit()
            return items

    def clear(self):
        """Testing utility to clear isolated test security database."""
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM security_events;")
                conn.execute("DELETE FROM security_incidents;")
                conn.execute("DELETE FROM security_alert_outbox;")
                conn.execute("DELETE FROM preview_sessions;")
                conn.execute("DELETE FROM security_synthetic_tests;")
        except sqlite3.Error as e:
            print(f"[SecurityStore ERROR] clear failed: {e}")
