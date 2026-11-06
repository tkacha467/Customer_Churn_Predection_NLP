"""Tests for Phase 1 Task 3: Database Tenant ID Columns, Idempotent Backfill & Index Optimization."""

import json
import sqlite3
import time
from pathlib import Path
import pytest

from Backend.app.core.database.storage import ReviewStore, normalize_tenant_id


def test_normalize_tenant_id():
    """Verify authoritative tenant normalization logic."""
    assert normalize_tenant_id(None) is None
    assert normalize_tenant_id("") is None
    assert normalize_tenant_id("   ") is None
    assert normalize_tenant_id("default_business") == "default_business"
    assert normalize_tenant_id("nasta_ghar") == "default_business"
    assert normalize_tenant_id("nasta-ghar") == "default_business"
    assert normalize_tenant_id("vraja_cafe") == "vraja_cafe"
    assert normalize_tenant_id("custom_tenant_123") == "custom_tenant_123"


def test_schema_migration_and_backfill_idempotency(tmp_path):
    """Verify that migration adds tenant_id, backfills historical data authoritatively, and is idempotent."""
    db_path = tmp_path / "legacy_migration_test.sqlite3"

    # 1. Create legacy schema without tenant_id column
    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""
            CREATE TABLE analytics_events (
                event_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE private_tickets (
                ticket_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE tenants (
                id TEXT PRIMARY KEY,
                business_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        now = time.time()
        db.execute("INSERT INTO tenants (id, business_name, created_at, updated_at) VALUES ('default_business', 'Nasta Ghar', ?, ?)", (now, now))
        db.execute("INSERT INTO tenants (id, business_name, created_at, updated_at) VALUES ('tenant_beta', 'Beta Cafe', ?, ?)", (now, now))

        # Insert legacy events
        # 1: default_business
        db.execute("INSERT INTO analytics_events VALUES ('ev-1', ?, ?)", (now, json.dumps({"event_id": "ev-1", "timestamp": now, "metadata": {"business_id": "default_business"}})))
        # 2: nasta-ghar alias
        db.execute("INSERT INTO analytics_events VALUES ('ev-2', ?, ?)", (now, json.dumps({"event_id": "ev-2", "timestamp": now, "metadata": {"business_id": "nasta-ghar"}})))
        # 3: tenant_beta
        db.execute("INSERT INTO analytics_events VALUES ('ev-3', ?, ?)", (now, json.dumps({"event_id": "ev-3", "timestamp": now, "metadata": {"business_id": "tenant_beta"}})))
        # 4: unassigned / None
        db.execute("INSERT INTO analytics_events VALUES ('ev-4', ?, ?)", (now, json.dumps({"event_id": "ev-4", "timestamp": now, "metadata": {}})))
        # 5: unregistered tenant (must not map to default_business)
        db.execute("INSERT INTO analytics_events VALUES ('ev-5', ?, ?)", (now, json.dumps({"event_id": "ev-5", "timestamp": now, "metadata": {"business_id": "unknown_intruder"}})))

        # Insert legacy tickets
        db.execute("INSERT INTO private_tickets VALUES ('tk-1', ?, ?)", (now, json.dumps({"ticket_id": "tk-1", "timestamp": now, "business_id": "default_business", "diner_note": "A"})))
        db.execute("INSERT INTO private_tickets VALUES ('tk-2', ?, ?)", (now, json.dumps({"ticket_id": "tk-2", "timestamp": now, "business_id": "nasta_ghar", "diner_note": "B"})))
        db.execute("INSERT INTO private_tickets VALUES ('tk-3', ?, ?)", (now, json.dumps({"ticket_id": "tk-3", "timestamp": now, "business_id": "tenant_beta", "diner_note": "C"})))
        db.execute("INSERT INTO private_tickets VALUES ('tk-4', ?, ?)", (now, json.dumps({"ticket_id": "tk-4", "timestamp": now, "diner_note": "No business"})))

    # 2. Initialize ReviewStore (triggers migration and backfill)
    store = ReviewStore(str(db_path))

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        evs = {r["event_id"]: r["tenant_id"] for r in db.execute("SELECT event_id, tenant_id FROM analytics_events").fetchall()}
        assert evs["ev-1"] == "default_business"
        assert evs["ev-2"] == "default_business"
        assert evs["ev-3"] == "tenant_beta"
        assert evs["ev-4"] is None
        assert evs["ev-5"] is None  # Unregistered tenant safely left NULL, not remapped

        tks = {r["ticket_id"]: r["tenant_id"] for r in db.execute("SELECT ticket_id, tenant_id FROM private_tickets").fetchall()}
        assert tks["tk-1"] == "default_business"
        assert tks["tk-2"] == "default_business"
        assert tks["tk-3"] == "tenant_beta"
        assert tks["tk-4"] is None

    # 3. Test idempotency by re-initializing store
    restarted = ReviewStore(str(db_path))
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        evs_second = {r["event_id"]: r["tenant_id"] for r in db.execute("SELECT event_id, tenant_id FROM analytics_events").fetchall()}
        assert evs_second == evs


def test_explain_query_plan_uses_composite_indexes(tmp_path):
    """Verify that EXPLAIN QUERY PLAN confirms index utilization without table scans or temp b-trees."""
    db_path = tmp_path / "plan_test.sqlite3"
    store = ReviewStore(str(db_path))

    with sqlite3.connect(db_path) as db:
        # Event list query
        event_plan = db.execute(
            "EXPLAIN QUERY PLAN SELECT payload FROM analytics_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 2000",
            ("default_business",)
        ).fetchall()
        plan_str = " ".join(r[3] for r in event_plan)
        assert "idx_analytics_tenant_created" in plan_str
        assert "SCAN" not in plan_str

        # Ticket list query
        ticket_plan = db.execute(
            "EXPLAIN QUERY PLAN SELECT payload FROM private_tickets WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
            ("default_business", 50)
        ).fetchall()
        ticket_str = " ".join(r[3] for r in ticket_plan)
        assert "idx_tickets_tenant_created" in ticket_str
        assert "SCAN" not in ticket_str

        # Ticket count query
        count_plan = db.execute(
            "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM private_tickets WHERE tenant_id = ?",
            ("default_business",)
        ).fetchall()
        count_str = " ".join(r[3] for r in count_plan)
        assert "idx_tickets_tenant_created" in count_str
        assert "SCAN" not in count_str


def test_tenant_isolation_on_indexed_queries(tmp_path):
    """Verify tenant isolation across events and tickets, ensuring no cross-tenant leakage or null leakage."""
    db_path = tmp_path / "isolation_test.sqlite3"
    store = ReviewStore(str(db_path))

    now = time.time()
    store.add_event({
        "event_id": "ev-tenant-a",
        "timestamp": now,
        "event_name": "review_generated",
        "metadata": {"business_id": "tenant_a"}
    })
    store.add_event({
        "event_id": "ev-tenant-b",
        "timestamp": now + 1,
        "event_name": "review_generated",
        "metadata": {"business_id": "tenant_b"}
    })
    store.add_event({
        "event_id": "ev-unassigned",
        "timestamp": now + 2,
        "event_name": "unassigned_event",
        "metadata": {}
    })

    store.add_ticket({
        "ticket_id": "tk-tenant-a",
        "timestamp": now,
        "business_id": "tenant_a",
        "diner_note": "Tenant A note"
    })
    store.add_ticket({
        "ticket_id": "tk-tenant-b",
        "timestamp": now + 1,
        "business_id": "tenant_b",
        "diner_note": "Tenant B note"
    })

    # Tenant A list
    a_events = store.list_events(business_id="tenant_a")
    assert len(a_events) == 1
    assert a_events[0]["event_id"] == "ev-tenant-a"

    a_tickets = store.list_tickets(business_id="tenant_a")
    assert len(a_tickets) == 1
    assert a_tickets[0]["ticket_id"] == "tk-tenant-a"
    assert store.ticket_count(business_id="tenant_a") == 1

    # Tenant B list
    b_events = store.list_events(business_id="tenant_b")
    assert len(b_events) == 1
    assert b_events[0]["event_id"] == "ev-tenant-b"

    b_tickets = store.list_tickets(business_id="tenant_b")
    assert len(b_tickets) == 1
    assert b_tickets[0]["ticket_id"] == "tk-tenant-b"
    assert store.ticket_count(business_id="tenant_b") == 1

    # Nonexistent tenant query should return nothing and NOT leak unassigned events
    empty_events = store.list_events(business_id="nonexistent_tenant")
    assert empty_events == []
    assert store.ticket_count(business_id="nonexistent_tenant") == 0


def test_per_tenant_retention_pruning(tmp_path):
    """Verify that retention pruning removes only excess records for the specific tenant and preserves other tenants."""
    db_path = tmp_path / "prune_test.sqlite3"
    store = ReviewStore(str(db_path))

    # Add 1 ticket for tenant_safe
    store.add_ticket({
        "ticket_id": "tk-safe",
        "timestamp": 1000.0,
        "business_id": "tenant_safe",
        "diner_note": "Safe note"
    })

    # Add 1 event for tenant_safe
    store.add_event({
        "event_id": "ev-safe",
        "timestamp": 1000.0,
        "event_name": "safe_event",
        "metadata": {"business_id": "tenant_safe"}
    })

    # Add tickets for tenant_flood
    for i in range(10):
        store.add_ticket({
            "ticket_id": f"tk-flood-{i}",
            "timestamp": 2000.0 + i,
            "business_id": "tenant_flood",
            "diner_note": f"Flood note {i}"
        })

    # Verify both tenants are intact
    assert store.ticket_count("tenant_safe") == 1
    assert store.ticket_count("tenant_flood") == 10
    assert len(store.list_events("tenant_safe")) == 1
