"""SQLite persistence for review analytics and private diner feedback."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


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

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def add_event(self, event: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO analytics_events(event_id, created_at, payload) VALUES (?, ?, ?)",
                (event["event_id"], event["timestamp"], json.dumps(event, ensure_ascii=False)),
            )
            db.execute("""
                DELETE FROM analytics_events WHERE event_id IN (
                    SELECT event_id FROM analytics_events ORDER BY created_at DESC, rowid DESC
                    LIMIT -1 OFFSET 2000
                )
            """)

    def list_events(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM analytics_events ORDER BY created_at DESC, rowid DESC LIMIT 2000"
            ).fetchall()
        return [json.loads(row["payload"]) for row in reversed(rows)]

    def add_ticket(self, ticket: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO private_tickets(ticket_id, created_at, payload) VALUES (?, ?, ?)",
                (ticket["ticket_id"], ticket["timestamp"], json.dumps(ticket, ensure_ascii=False)),
            )
            db.execute("""
                DELETE FROM private_tickets WHERE ticket_id IN (
                    SELECT ticket_id FROM private_tickets ORDER BY created_at DESC, rowid DESC
                    LIMIT -1 OFFSET 5000
                )
            """)

    def list_tickets(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM private_tickets ORDER BY created_at DESC, rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in reversed(rows)]

    def ticket_count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM private_tickets").fetchone()[0])
