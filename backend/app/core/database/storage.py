"""SQLite persistence for multi-tenant identity, review analytics, and private diner feedback."""

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Dict, List


def _normalize_profile_url(url: Optional[str]) -> str:
    if not url:
        return ""
    s = str(url).strip()
    if not s:
        return ""
    if not s.startswith(("http://", "https://")):
        return f"https://{s}"
    return s


class ReviewStore:
    def __init__(self, database_path: str | None = None):
        _repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists() or (p / "Backend").exists()), Path(__file__).resolve().parents[5])
        _candidate_dbs = [
            _repo_root / "Project_Files" / "Data" / "nasta-ghar" / "reviews.sqlite3",
            _repo_root / "data" / "nasta-ghar" / "reviews.sqlite3",
        ]
        default_path = next((p for p in _candidate_dbs if p.exists()), _candidate_dbs[0])
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
                    entitlements_json TEXT DEFAULT '["review_manager"]',
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

            # Shared Business Profile & Tenant Documents (Vraja Multi-Product Foundation)
            db.execute("""
                CREATE TABLE IF NOT EXISTS business_profiles (
                    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                    tagline TEXT DEFAULT '',
                    display_name TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    opening_hours TEXT DEFAULT '',
                    welcome_message TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    phone_number TEXT DEFAULT '',
                    website_url TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    map_url TEXT DEFAULT '',
                    whatsapp_url TEXT DEFAULT '',
                    whatsapp_group_url TEXT DEFAULT '',
                    instagram_url TEXT DEFAULT '',
                    facebook_url TEXT DEFAULT '',
                    youtube_url TEXT DEFAULT '',
                    logo_path TEXT DEFAULT '',
                    cover_image_path TEXT DEFAULT '',
                    background_preset TEXT DEFAULT '',
                    overlay_opacity REAL DEFAULT 0.75,
                    primary_accent TEXT DEFAULT '#078BFF',
                    custom_links_json TEXT DEFAULT '[]',
                    is_published INTEGER NOT NULL DEFAULT 0,
                    show_review_button INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS tenant_documents (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    document_type TEXT NOT NULL DEFAULT 'food_menu',
                    display_name TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    mime_type TEXT NOT NULL DEFAULT 'application/pdf',
                    sha256_hash TEXT NOT NULL,
                    is_published INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_business_profiles_published ON business_profiles(is_published)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_tenant_documents_tenant ON tenant_documents(tenant_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_tenant_documents_published ON tenant_documents(is_published)")

            # Upgrade existing schemas safely
            for stmt in (
                "ALTER TABLE tenants ADD COLUMN domain TEXT DEFAULT ''",
                "ALTER TABLE tenants ADD COLUMN entitlements_json TEXT DEFAULT '[\"review_manager\"]'",
                "ALTER TABLE users ADD COLUMN is_platform_admin INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE business_profiles ADD COLUMN display_name TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN category TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN opening_hours TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN welcome_message TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN email TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN whatsapp_group_url TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN background_preset TEXT DEFAULT ''",
                "ALTER TABLE business_profiles ADD COLUMN overlay_opacity REAL DEFAULT 0.75",
                "ALTER TABLE business_profiles ADD COLUMN primary_accent TEXT DEFAULT '#078BFF'",
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
        from Backend.app.core.tenants.google_reviews import DEFAULT_TOPICS
        now = time.time()
        initial_tenants = [
            ("default_business", "Nasta Ghar", "https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro", "Breakfast & Snacks", "Authentic homestyle breakfast, chai, and snacks in Rajkot.", "#f97316"),
            ("test_cafe", "Test Cafe", "https://g.page/r/test-cafe/review", "Cafe", "Test Cafe in Rajkot", "#0ea5e9"),
        ]
        for b_id, name, url, category, desc, accent in initial_tenants:
            ents = json.dumps(["review_manager", "digital_card"] if b_id == "default_business" else ["review_manager"])
            db.execute("""
                INSERT OR IGNORE INTO tenants (
                    id, business_name, status, platform, review_url, branch,
                    category, description, topics_json, primary_accent, entitlements_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b_id, name, "active", "google", url, "", category, desc,
                json.dumps(DEFAULT_TOPICS), accent, ents, now, now
            ))

        db.execute("""
            INSERT OR IGNORE INTO business_profiles (
                tenant_id, tagline, display_name, category, opening_hours, welcome_message,
                phone_number, address, website_url, primary_accent, background_preset,
                is_published, show_review_button, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
        """, (
            "default_business",
            "Authentic Gujarati Breakfast & Chai",
            "Nasta Ghar",
            "Breakfast & Snacks",
            "Mon - Sun: 7:00 AM - 10:00 PM",
            "Welcome to Nasta Ghar! Enjoy authentic Gujarati breakfast, fresh snacks, and special chai.",
            "+91 98765 43210",
            "Near Jubilee Garden, Rajkot, Gujarat, India",
            "https://maps.google.com",
            "#f97316",
            "amber",
            now, now
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
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            row = db.execute("SELECT * FROM tenants WHERE id = ?", (target_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["topics"] = json.loads(data.get("topics_json") or "[]")
            data["entitlements"] = json.loads(data.get("entitlements_json") or '["review_manager"]')
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
            data["entitlements"] = json.loads(data.get("entitlements_json") or '["review_manager"]')
            return data

    def tenant_exists(self, tenant_id: str) -> bool:
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM tenants WHERE id = ?", (target_id,)).fetchone()
            return row is not None

    def list_tenants(self) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT t.*, 
                       (SELECT u.email FROM tenant_memberships tm JOIN users u ON u.id = tm.user_id WHERE tm.tenant_id = t.id AND tm.role = 'owner' LIMIT 1) AS owner_email,
                       (SELECT u.display_name FROM tenant_memberships tm JOIN users u ON u.id = tm.user_id WHERE tm.tenant_id = t.id AND tm.role = 'owner' LIMIT 1) AS owner_name,
                       (SELECT COUNT(*) FROM tenant_documents td WHERE td.tenant_id = t.id) AS document_count
                FROM tenants t 
                ORDER BY t.created_at ASC
            """).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["topics"] = json.loads(d.get("topics_json") or "[]")
                d["entitlements"] = json.loads(d.get("entitlements_json") or '["review_manager"]')
                result.append(d)
            return result

    def get_tenant_admin_details(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            row = db.execute("""
                SELECT t.*, 
                       (SELECT u.email FROM tenant_memberships tm JOIN users u ON u.id = tm.user_id WHERE tm.tenant_id = t.id AND tm.role = 'owner' LIMIT 1) AS owner_email,
                       (SELECT u.display_name FROM tenant_memberships tm JOIN users u ON u.id = tm.user_id WHERE tm.tenant_id = t.id AND tm.role = 'owner' LIMIT 1) AS owner_name,
                       (SELECT u.id FROM tenant_memberships tm JOIN users u ON u.id = tm.user_id WHERE tm.tenant_id = t.id AND tm.role = 'owner' LIMIT 1) AS owner_user_id,
                       (SELECT COUNT(*) FROM tenant_documents td WHERE td.tenant_id = t.id) AS document_count
                FROM tenants t 
                WHERE t.id = ?
            """, (target_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["topics"] = json.loads(d.get("topics_json") or "[]")
            d["entitlements"] = json.loads(d.get("entitlements_json") or '["review_manager"]')
            return d

    def upsert_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = tenant_data["id"]
        # Normalize aliases
        if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar"):
            tenant_id = "default_business"

        now = time.time()
        topics_json = json.dumps(tenant_data.get("topics", []))
        entitlements_json = json.dumps(tenant_data.get("entitlements", ["review_manager"]))
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
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
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
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
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
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
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
        target_tenant = "default_business" if active_tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else active_tenant_id
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
        target_tenant = "default_business" if new_tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else new_tenant_id
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

    # ---------------------------------------------------------
    # Shared Business Profile Operations (Product 2 & Combined)
    # ---------------------------------------------------------
    def get_business_profile(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            row = db.execute("SELECT * FROM business_profiles WHERE tenant_id = ?", (target_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            try:
                data["custom_links"] = json.loads(data.get("custom_links_json") or "[]")
            except Exception:
                data["custom_links"] = []
            data["is_published"] = bool(data.get("is_published", 0))
            data["show_review_button"] = bool(data.get("show_review_button", 1))
            data["display_name"] = data.get("display_name") or ""
            data["category"] = data.get("category") or ""
            data["opening_hours"] = data.get("opening_hours") or ""
            data["welcome_message"] = data.get("welcome_message") or ""
            data["email"] = data.get("email") or ""
            data["whatsapp_group_url"] = data.get("whatsapp_group_url") or ""
            data["background_preset"] = data.get("background_preset") or ""
            data["overlay_opacity"] = float(data.get("overlay_opacity") if data.get("overlay_opacity") is not None else 0.75)
            data["primary_accent"] = data.get("primary_accent") or "#078BFF"
            return data

    def upsert_business_profile(self, tenant_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        if not self.tenant_exists(target_id):
            raise KeyError(f"Cannot manage business profile: Tenant '{target_id}' does not exist.")

        now = time.time()
        existing = self.get_business_profile(target_id)

        # Merge updates with existing values to safely preserve omitted fields
        if existing:
            tagline = profile_data.get("tagline") if profile_data.get("tagline") is not None else existing.get("tagline", "")
            display_name = str(profile_data.get("display_name")).strip() if profile_data.get("display_name") is not None else existing.get("display_name", "")
            category = str(profile_data.get("category")).strip() if profile_data.get("category") is not None else existing.get("category", "")
            opening_hours = str(profile_data.get("opening_hours")).strip() if profile_data.get("opening_hours") is not None else existing.get("opening_hours", "")
            welcome_message = str(profile_data.get("welcome_message")).strip() if profile_data.get("welcome_message") is not None else existing.get("welcome_message", "")
            email = str(profile_data.get("email")).strip().lower() if profile_data.get("email") is not None else existing.get("email", "")
            phone_number = profile_data.get("phone_number") if profile_data.get("phone_number") is not None else existing.get("phone_number", "")
            website_url = _normalize_profile_url(profile_data.get("website_url") if profile_data.get("website_url") is not None else existing.get("website_url", ""))
            address = profile_data.get("address") if profile_data.get("address") is not None else existing.get("address", "")
            map_url = _normalize_profile_url(profile_data.get("map_url") if profile_data.get("map_url") is not None else existing.get("map_url", ""))
            whatsapp_url = _normalize_profile_url(profile_data.get("whatsapp_url") if profile_data.get("whatsapp_url") is not None else existing.get("whatsapp_url", ""))
            whatsapp_group_url = _normalize_profile_url(profile_data.get("whatsapp_group_url") if profile_data.get("whatsapp_group_url") is not None else existing.get("whatsapp_group_url", ""))
            instagram_url = _normalize_profile_url(profile_data.get("instagram_url") if profile_data.get("instagram_url") is not None else existing.get("instagram_url", ""))
            facebook_url = _normalize_profile_url(profile_data.get("facebook_url") if profile_data.get("facebook_url") is not None else existing.get("facebook_url", ""))
            youtube_url = _normalize_profile_url(profile_data.get("youtube_url") if profile_data.get("youtube_url") is not None else existing.get("youtube_url", ""))
            logo_path = profile_data.get("logo_path") if profile_data.get("logo_path") is not None else existing.get("logo_path", "")
            cover_image_path = profile_data.get("cover_image_path") if profile_data.get("cover_image_path") is not None else existing.get("cover_image_path", "")
            background_preset = str(profile_data.get("background_preset") or "").strip() if profile_data.get("background_preset") is not None else existing.get("background_preset", "")
            overlay_opacity = float(profile_data["overlay_opacity"]) if profile_data.get("overlay_opacity") is not None else float(existing.get("overlay_opacity", 0.75))
            primary_accent = str(profile_data.get("primary_accent") or "").strip() if profile_data.get("primary_accent") is not None else existing.get("primary_accent", "#078BFF")

            if "custom_links" in profile_data and profile_data["custom_links"] is not None:
                custom_links_json = json.dumps(profile_data["custom_links"])
            else:
                custom_links_json = json.dumps(existing.get("custom_links", []))

            is_published = int(profile_data["is_published"]) if profile_data.get("is_published") is not None else int(existing.get("is_published", 0))
            show_review_button = int(profile_data["show_review_button"]) if profile_data.get("show_review_button") is not None else int(existing.get("show_review_button", 1))
            created_at = existing["created_at"]
        else:
            tagline = profile_data.get("tagline") or ""
            display_name = str(profile_data.get("display_name") or "").strip()
            category = str(profile_data.get("category") or "").strip()
            opening_hours = str(profile_data.get("opening_hours") or "").strip()
            welcome_message = str(profile_data.get("welcome_message") or "").strip()
            email = str(profile_data.get("email") or "").strip().lower()
            phone_number = profile_data.get("phone_number") or ""
            website_url = _normalize_profile_url(profile_data.get("website_url") or "")
            address = profile_data.get("address") or ""
            map_url = _normalize_profile_url(profile_data.get("map_url") or "")
            whatsapp_url = _normalize_profile_url(profile_data.get("whatsapp_url") or "")
            whatsapp_group_url = _normalize_profile_url(profile_data.get("whatsapp_group_url") or "")
            instagram_url = _normalize_profile_url(profile_data.get("instagram_url") or "")
            facebook_url = _normalize_profile_url(profile_data.get("facebook_url") or "")
            youtube_url = _normalize_profile_url(profile_data.get("youtube_url") or "")
            logo_path = profile_data.get("logo_path") or ""
            cover_image_path = profile_data.get("cover_image_path") or ""
            background_preset = str(profile_data.get("background_preset") or "").strip()
            overlay_opacity = float(profile_data.get("overlay_opacity", 0.75))
            primary_accent = str(profile_data.get("primary_accent") or "#078BFF").strip()
            custom_links_json = json.dumps(profile_data.get("custom_links") or [])
            is_published = int(profile_data.get("is_published", 0))
            show_review_button = int(profile_data.get("show_review_button", 1))
            created_at = now

        with self._connect() as db:
            db.execute("""
                INSERT INTO business_profiles (
                    tenant_id, tagline, display_name, category, opening_hours, welcome_message,
                    email, phone_number, website_url, address, map_url,
                    whatsapp_url, whatsapp_group_url, instagram_url, facebook_url, youtube_url,
                    logo_path, cover_image_path, background_preset, overlay_opacity, primary_accent,
                    custom_links_json, is_published, show_review_button, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id) DO UPDATE SET
                    tagline = excluded.tagline,
                    display_name = excluded.display_name,
                    category = excluded.category,
                    opening_hours = excluded.opening_hours,
                    welcome_message = excluded.welcome_message,
                    email = excluded.email,
                    phone_number = excluded.phone_number,
                    website_url = excluded.website_url,
                    address = excluded.address,
                    map_url = excluded.map_url,
                    whatsapp_url = excluded.whatsapp_url,
                    whatsapp_group_url = excluded.whatsapp_group_url,
                    instagram_url = excluded.instagram_url,
                    facebook_url = excluded.facebook_url,
                    youtube_url = excluded.youtube_url,
                    logo_path = excluded.logo_path,
                    cover_image_path = excluded.cover_image_path,
                    background_preset = excluded.background_preset,
                    overlay_opacity = excluded.overlay_opacity,
                    primary_accent = excluded.primary_accent,
                    custom_links_json = excluded.custom_links_json,
                    is_published = excluded.is_published,
                    show_review_button = excluded.show_review_button,
                    updated_at = excluded.updated_at
            """, (
                target_id, tagline, display_name, category, opening_hours, welcome_message,
                email, phone_number, website_url, address, map_url,
                whatsapp_url, whatsapp_group_url, instagram_url, facebook_url, youtube_url,
                logo_path, cover_image_path, background_preset, overlay_opacity, primary_accent,
                custom_links_json, is_published, show_review_button, created_at, now
            ))

        return self.get_business_profile(target_id)

    def set_profile_published(self, tenant_id: str, is_published: bool) -> bool:
        target_id = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        now = time.time()
        with self._connect() as db:
            cur = db.execute(
                "UPDATE business_profiles SET is_published = ?, updated_at = ? WHERE tenant_id = ?",
                (1 if is_published else 0, now, target_id)
            )
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # Tenant Document Metadata Operations (Product 2 & Menus)
    # ---------------------------------------------------------
    def add_tenant_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        target_tenant = "default_business" if doc_data["tenant_id"] in ("default_business", "nasta_ghar", "nasta-ghar") else doc_data["tenant_id"]
        if not self.tenant_exists(target_tenant):
            raise KeyError(f"Cannot add document: Tenant '{target_tenant}' does not exist.")

        now = time.time()
        doc_id = doc_data["id"]
        with self._connect() as db:
            db.execute("""
                INSERT INTO tenant_documents (
                    id, tenant_id, document_type, display_name, original_filename,
                    stored_filename, file_size_bytes, mime_type, sha256_hash,
                    is_published, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                target_tenant,
                doc_data.get("document_type", "food_menu"),
                doc_data.get("display_name", "Menu"),
                doc_data.get("original_filename", "menu.pdf"),
                doc_data.get("stored_filename", f"{doc_id}.pdf"),
                int(doc_data.get("file_size_bytes", 0)),
                doc_data.get("mime_type", "application/pdf"),
                doc_data.get("sha256_hash", ""),
                1 if doc_data.get("is_published", True) else 0,
                doc_data.get("created_at", now),
                now
            ))
        return self.get_tenant_document(target_tenant, doc_id)

    def get_tenant_document(self, tenant_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM tenant_documents WHERE tenant_id = ? AND id = ?",
                (target_tenant, document_id)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["is_published"] = bool(d.get("is_published", 0))
            return d

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tenant_documents WHERE id = ?", (document_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["is_published"] = bool(d.get("is_published", 0))
            return d

    def list_tenant_documents(self, tenant_id: str, published_only: bool = False) -> List[Dict[str, Any]]:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            if published_only:
                rows = db.execute(
                    "SELECT * FROM tenant_documents WHERE tenant_id = ? AND is_published = 1 ORDER BY created_at ASC",
                    (target_tenant,)
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM tenant_documents WHERE tenant_id = ? ORDER BY created_at ASC",
                    (target_tenant,)
                ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["is_published"] = bool(d.get("is_published", 0))
                result.append(d)
            return result

    def delete_tenant_document(self, tenant_id: str, document_id: str) -> bool:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        with self._connect() as db:
            cur = db.execute(
                "DELETE FROM tenant_documents WHERE tenant_id = ? AND id = ?",
                (target_tenant, document_id)
            )
            return cur.rowcount > 0

    def set_document_published(self, tenant_id: str, document_id: str, is_published: bool) -> bool:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        now = time.time()
        with self._connect() as db:
            cur = db.execute(
                "UPDATE tenant_documents SET is_published = ?, updated_at = ? WHERE tenant_id = ? AND id = ?",
                (1 if is_published else 0, now, target_tenant, document_id)
            )
            return cur.rowcount > 0

    def update_tenant_document(
        self,
        tenant_id: str,
        document_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        target_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        existing = self.get_tenant_document(target_tenant, document_id)
        if not existing:
            return None

        display_name = updates.get("display_name") if updates.get("display_name") is not None else existing["display_name"]
        document_type = updates.get("document_type") if updates.get("document_type") is not None else existing["document_type"]
        is_published = int(updates["is_published"]) if updates.get("is_published") is not None else (1 if existing["is_published"] else 0)
        now = time.time()

        with self._connect() as db:
            cur = db.execute("""
                UPDATE tenant_documents
                SET display_name = ?, document_type = ?, is_published = ?, updated_at = ?
                WHERE tenant_id = ? AND id = ?
            """, (display_name, document_type, is_published, now, target_tenant, document_id))
            if cur.rowcount == 0:
                return None

        return self.get_tenant_document(target_tenant, document_id)


