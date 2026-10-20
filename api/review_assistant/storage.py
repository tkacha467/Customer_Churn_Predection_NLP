"""SQLite persistence for multi-tenant identity, review analytics, and private diner feedback."""

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Dict, List


class ReviewStore:
    def __init__(self, database_path: str | None = None):
        default_path = Path(__file__).resolve().parents[2] / "data" / "nasta-ghar" / "reviews.sqlite3"
        self.path = Path(database_path or os.getenv("REVIEW_DB_PATH", str(default_path))).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    event_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    payload TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS private_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    payload TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    business_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    platform TEXT NOT NULL DEFAULT 'google',
                    review_url TEXT NOT NULL DEFAULT '',
                    branch TEXT DEFAULT '',
                    category TEXT DEFAULT 'Breakfast & Snacks',
                    description TEXT DEFAULT '',
                    topics_json TEXT DEFAULT '[]',
                    primary_accent TEXT DEFAULT '#f97316',
                    domain TEXT DEFAULT '',
                    entitlements_json TEXT DEFAULT '["review_manager", "digital_card"]',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    is_platform_admin INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS tenant_memberships (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    role TEXT NOT NULL DEFAULT 'manager',
                    created_at REAL NOT NULL,
                    UNIQUE(user_id, tenant_id)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    active_tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    revoked_at REAL,
                    ip_address TEXT DEFAULT '',
                    user_agent TEXT DEFAULT ''
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_memberships_user ON tenant_memberships(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON tenant_memberships(tenant_id)")

            # Upgrade existing schemas safely
            for stmt in (
                "ALTER TABLE tenants ADD COLUMN domain TEXT DEFAULT ''",
                "ALTER TABLE tenants ADD COLUMN entitlements_json TEXT DEFAULT '[\"review_manager\", \"digital_card\"]'",
                "ALTER TABLE users ADD COLUMN is_platform_admin INTEGER NOT NULL DEFAULT 0",
            ):
                try:
                    db.execute(stmt)
                except sqlite3.OperationalError:
                    pass

            # Auto-seed initial tenants from business_links.json if database is newly initialized
            count = db.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
            if count == 0:
                self._seed_initial_tenants(db)

    def _seed_initial_tenants(self, db):
        from api.review_assistant.google_reviews import DEFAULT_TOPICS
        now = time.time()
        initial_tenants = [
            ("default_business", "Nasta Ghar", "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro", "Breakfast & Snacks", "Authentic homestyle breakfast, chai, and snacks in Rajkot.", "#f97316"),
            ("test_cafe", "Test Cafe", "https://g.page/r/test-cafe/review", "Cafe", "Test Cafe in Rajkot", "#0ea5e9"),
        ]
        for b_id, name, url, category, desc, accent in initial_tenants:
            db.execute("""
                INSERT OR IGNORE INTO tenants (
                    id, business_name, status, platform, review_url, branch,
                    category, description, topics_json, primary_accent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b_id, name, "active", "google", url, "", category, desc,
                json.dumps(DEFAULT_TOPICS), accent, now, now
            ))


    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    # ---------------------------------------------------------
    # Tenant Operations
    # ---------------------------------------------------------
    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        # Resolve aliases
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar") else tenant_id
        with self._connect() as db:
            row = db.execute("SELECT * FROM tenants WHERE id = ?", (target_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["topics"] = json.loads(data.get("topics_json") or "[]")
            data["entitlements"] = json.loads(data.get("entitlements_json") or '["review_manager", "digital_card"]')
            return data

    def get_tenant_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        if not domain:
            return None
        with self._connect() as db:
            row = db.execute("SELECT * FROM tenants WHERE domain = ? AND status = 'active'", (domain.strip().lower(),)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["topics"] = json.loads(data.get("topics_json") or "[]")
            data["entitlements"] = json.loads(data.get("entitlements_json") or '["review_manager", "digital_card"]')
            return data

    def tenant_exists(self, tenant_id: str) -> bool:
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar") else tenant_id
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM tenants WHERE id = ?", (target_id,)).fetchone()
            return row is not None

    def list_tenants(self) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM tenants ORDER BY created_at ASC").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["topics"] = json.loads(d.get("topics_json") or "[]")
                d["entitlements"] = json.loads(d.get("entitlements_json") or '["review_manager", "digital_card"]')
                result.append(d)
            return result

    def upsert_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = tenant_data["id"]
        # Normalize aliases
        if tenant_id in ("default_business", "nasta_ghar"):
            tenant_id = "default_business"

        now = time.time()
        topics_json = json.dumps(tenant_data.get("topics", []))
        entitlements_json = json.dumps(tenant_data.get("entitlements", ["review_manager", "digital_card"]))
        domain = tenant_data.get("domain", "").strip().lower()

        with self._connect() as db:
            existing = db.execute("SELECT created_at FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
            created_at = existing["created_at"] if existing else now
            db.execute("""
                INSERT INTO tenants (
                    id, business_name, status, platform, review_url, branch,
                    category, description, topics_json, primary_accent, domain,
                    entitlements_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    business_name = excluded.business_name,
                    status = excluded.status,
                    platform = excluded.platform,
                    review_url = excluded.review_url,
                    branch = excluded.branch,
                    category = excluded.category,
                    description = excluded.description,
                    topics_json = excluded.topics_json,
                    primary_accent = excluded.primary_accent,
                    domain = excluded.domain,
                    entitlements_json = excluded.entitlements_json,
                    updated_at = excluded.updated_at
            """, (
                tenant_id,
                tenant_data.get("business_name", "Nasta Ghar"),
                tenant_data.get("status", "active"),
                tenant_data.get("platform", "google"),
                tenant_data.get("review_url", ""),
                tenant_data.get("branch", ""),
                tenant_data.get("category", "Breakfast & Snacks"),
                tenant_data.get("description", ""),
                topics_json,
                tenant_data.get("primary_accent", "#f97316"),
                domain,
                entitlements_json,
                created_at,
                now,
            ))
        return self.get_tenant(tenant_id)

    # ---------------------------------------------------------
    # User Operations
    # ---------------------------------------------------------
    def create_user(
        self,
        email: str,
        password_hash: str,
        display_name: str = "",
        is_active: int = 1,
        is_platform_admin: int = 0
    ) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        normalized_email = email.strip().lower()
        now = time.time()
        with self._connect() as db:
            db.execute("""
                INSERT INTO users (id, email, password_hash, display_name, is_active, is_platform_admin, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, normalized_email, password_hash, display_name.strip(), is_active, is_platform_admin, now, now))
        return self.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        normalized_email = email.strip().lower()
        with self._connect() as db:
            row = db.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        now = time.time()
        with self._connect() as db:
            cur = db.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (new_password_hash, now, user_id)
            )
            return cur.rowcount > 0

    def set_user_active(self, user_id: str, is_active: bool) -> bool:
        now = time.time()
        val = 1 if is_active else 0
        with self._connect() as db:
            cur = db.execute(
                "UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?",
                (val, now, user_id)
            )
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # Membership Operations
    # ---------------------------------------------------------
    def add_membership(self, user_id: str, tenant_id: str, role: str = "manager") -> Dict[str, Any]:
        # Normalize tenant alias
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar") else tenant_id
        membership_id = str(uuid.uuid4())
        now = time.time()
        with self._connect() as db:
            db.execute("""
                INSERT INTO tenant_memberships (id, user_id, tenant_id, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, tenant_id) DO UPDATE SET
                    role = excluded.role
            """, (membership_id, user_id, target_tenant, role, now))
        return self.get_membership(user_id, target_tenant)

    def get_membership(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar") else tenant_id
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM tenant_memberships WHERE user_id = ? AND tenant_id = ?",
                (user_id, target_tenant)
            ).fetchone()
            return dict(row) if row else None

    def list_user_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT m.id, m.user_id, m.tenant_id, m.role, m.created_at,
                       t.business_name, t.status, t.category, t.primary_accent
                FROM tenant_memberships m
                JOIN tenants t ON m.tenant_id = t.id
                WHERE m.user_id = ? AND t.status = 'active'
                ORDER BY m.created_at ASC
            """, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    def remove_membership(self, user_id: str, tenant_id: str) -> bool:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar") else tenant_id
        with self._connect() as db:
            cur = db.execute(
                "DELETE FROM tenant_memberships WHERE user_id = ? AND tenant_id = ?",
                (user_id, target_tenant)
            )
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # Server-Side Session Operations
    # ---------------------------------------------------------
    def create_session(
        self,
        token_hash: str,
        user_id: str,
        active_tenant_id: str,
        expires_at: float,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Dict[str, Any]:
        target_tenant = "default_business" if active_tenant_id in ("default_business", "nasta_ghar") else active_tenant_id
        now = time.time()
        with self._connect() as db:
            db.execute("""
                INSERT INTO sessions (
                    token_hash, user_id, active_tenant_id, created_at, expires_at,
                    revoked_at, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
            """, (token_hash, user_id, target_tenant, now, expires_at, ip_address, user_agent))
        return self.get_session(token_hash)

    def get_session(self, token_hash: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE token_hash = ?",
                (token_hash,)
            ).fetchone()
            return dict(row) if row else None

    def update_session_active_tenant(self, token_hash: str, new_tenant_id: str) -> bool:
        target_tenant = "default_business" if new_tenant_id in ("default_business", "nasta_ghar") else new_tenant_id
        with self._connect() as db:
            cur = db.execute(
                "UPDATE sessions SET active_tenant_id = ? WHERE token_hash = ? AND revoked_at IS NULL",
                (target_tenant, token_hash)
            )
            return cur.rowcount > 0

    def revoke_session(self, token_hash: str) -> bool:
        now = time.time()
        with self._connect() as db:
            cur = db.execute(
                "UPDATE sessions SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
                (now, token_hash)
            )
            return cur.rowcount > 0

    def revoke_all_user_sessions(self, user_id: str) -> int:
        now = time.time()
        with self._connect() as db:
            cur = db.execute(
                "UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
                (now, user_id)
            )
            return cur.rowcount

    def clean_expired_sessions(self) -> int:
        now = time.time()
        with self._connect() as db:
            cur = db.execute("DELETE FROM sessions WHERE expires_at < ? OR revoked_at IS NOT NULL", (now,))
            return cur.rowcount

    # ---------------------------------------------------------
    # Legacy Bootstrap Owner Compatibility
    # ---------------------------------------------------------
    def get_or_create_legacy_owner(self) -> Dict[str, Any]:
        """Creates or returns the scoped legacy owner user bound strictly to default_business."""
        # Ensure default_business exists
        if not self.tenant_exists("default_business"):
            self.upsert_tenant({
                "id": "default_business",
                "business_name": "Nasta Ghar",
                "review_url": "https://maps.google.com",
                "branch": "",
                "category": "Breakfast & Snacks",
                "description": "Authentic homestyle breakfast, chai, and snacks in Rajkot.",
                "topics": ["Breakfast", "Chai & Beverages", "Snacks", "Taste & Flavour", "Friendly Staff", "Cleanliness", "Value for Money", "Quick Service"],
                "primary_accent": "#f97316"
            })

        legacy_email = "legacy_owner@nastaghar.local"
        user = self.get_user_by_email(legacy_email)
        if not user:
            # Create user with a dummy non-usable password hash since legacy login matches OWNER_PASSWORD directly
            user = self.create_user(
                email=legacy_email,
                password_hash="legacy$disabled_direct_login",
                display_name="Platform Administrator",
                is_active=1,
                is_platform_admin=1
            )
        else:
            with self._connect() as db:
                db.execute("UPDATE users SET is_platform_admin = 1 WHERE id = ?", (user["id"],))
            user = self.get_user_by_id(user["id"])

        # Ensure membership in default_business
        membership = self.get_membership(user["id"], "default_business")
        if not membership:
            self.add_membership(user["id"], "default_business", role="owner")

        return user

    # ---------------------------------------------------------
    # Analytics & Private Tickets (Preserved)
    # ---------------------------------------------------------
    def add_event(self, event: dict[str, Any]) -> None:
        b_id = event.get("metadata", {}).get("business_id", "default_business")
        with self._connect() as db:
            db.execute(
                "INSERT INTO analytics_events(event_id, created_at, payload) VALUES (?, ?, ?)",
                (event["event_id"], event["timestamp"], json.dumps(event, ensure_ascii=False)),
            )
            # Per-tenant retention: prune only events for THIS business if exceeding 2000
            db.execute("""
                DELETE FROM analytics_events WHERE event_id IN (
                    SELECT event_id FROM analytics_events
                    WHERE json_extract(payload, '$.metadata.business_id') = ?
                       OR (? = 'default_business' AND json_extract(payload, '$.metadata.business_id') IS NULL)
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT -1 OFFSET 2000
                )
            """, (b_id, b_id))

    def list_events(self, business_id: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as db:
            if business_id:
                rows = db.execute("""
                    SELECT payload FROM analytics_events
                    WHERE json_extract(payload, '$.metadata.business_id') = ?
                       OR (? = 'default_business' AND json_extract(payload, '$.metadata.business_id') IS NULL)
                    ORDER BY created_at DESC, rowid DESC LIMIT 2000
                """, (business_id, business_id)).fetchall()
            else:
                rows = db.execute(
                    "SELECT payload FROM analytics_events ORDER BY created_at DESC, rowid DESC LIMIT 2000"
                ).fetchall()
        return [json.loads(row["payload"]) for row in reversed(rows)]

    def add_ticket(self, ticket: dict[str, Any]) -> None:
        b_id = ticket.get("business_id", "default_business")
        with self._connect() as db:
            db.execute(
                "INSERT INTO private_tickets(ticket_id, created_at, payload) VALUES (?, ?, ?)",
                (ticket["ticket_id"], ticket["timestamp"], json.dumps(ticket, ensure_ascii=False)),
            )
            # Per-tenant retention: prune only tickets for THIS business if exceeding 5000
            db.execute("""
                DELETE FROM private_tickets WHERE ticket_id IN (
                    SELECT ticket_id FROM private_tickets
                    WHERE json_extract(payload, '$.business_id') = ?
                       OR (? = 'default_business' AND json_extract(payload, '$.business_id') IS NULL)
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT -1 OFFSET 5000
                )
            """, (b_id, b_id))

    def list_tickets(self, business_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            if business_id:
                rows = db.execute("""
                    SELECT payload FROM private_tickets
                    WHERE json_extract(payload, '$.business_id') = ?
                       OR (? = 'default_business' AND json_extract(payload, '$.business_id') IS NULL)
                    ORDER BY created_at DESC, rowid DESC LIMIT ?
                """, (business_id, business_id, limit)).fetchall()
            else:
                rows = db.execute(
                    "SELECT payload FROM private_tickets ORDER BY created_at DESC, rowid DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [json.loads(row["payload"]) for row in reversed(rows)]

    def ticket_count(self, business_id: str | None = None) -> int:
        with self._connect() as db:
            if business_id:
                row = db.execute("""
                    SELECT COUNT(*) FROM private_tickets
                    WHERE json_extract(payload, '$.business_id') = ?
                       OR (? = 'default_business' AND json_extract(payload, '$.business_id') IS NULL)
                """, (business_id, business_id)).fetchone()
                return int(row[0]) if row else 0
            return int(db.execute("SELECT COUNT(*) FROM private_tickets").fetchone()[0])
