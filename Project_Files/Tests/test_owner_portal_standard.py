"""Automated tests for Product A Owner Portal Standard & Analytics Architecture."""

import time
import pytest
from fastapi.testclient import TestClient

from Backend.app.main import app
from Backend.app.core.database.storage import ReviewStore
from Backend.app.api.service import review_service


@pytest.fixture
def client():
    return TestClient(app)


def test_ticket_status_lifecycle_and_tenant_scoping(tmp_path):
    """Test private ticket status transition and tenant boundary isolation."""
    db_path = tmp_path / "ticket_lifecycle.sqlite3"
    store = ReviewStore(str(db_path))

    ticket = {
        "ticket_id": "TICK-TEST-001",
        "business_id": "tenant_alpha",
        "table_number": "Table 4",
        "rating": 2,
        "diner_note": "Soup was lukewarm",
        "aspects": ["Taste & Flavour"],
        "guest_contact": "+91 99999 11111",
        "timestamp": time.time(),
        "status": "OPEN"
    }
    store.add_ticket(ticket, tenant_id="tenant_alpha")

    # Initial status
    tickets = store.list_tickets(business_id="tenant_alpha")
    assert len(tickets) == 1
    assert tickets[0]["status"] == "OPEN"

    # Update to ESCALATED
    ok = store.update_ticket_status("TICK-TEST-001", "ESCALATED", tenant_id="tenant_alpha")
    assert ok is True
    tickets = store.list_tickets(business_id="tenant_alpha")
    assert tickets[0]["status"] == "ESCALATED"

    # Cross-tenant update must fail
    ok_cross = store.update_ticket_status("TICK-TEST-001", "RESOLVED", tenant_id="tenant_beta")
    assert ok_cross is False
    assert store.list_tickets(business_id="tenant_alpha")[0]["status"] == "ESCALATED"

    # Update to RESOLVED
    ok = store.update_ticket_status("TICK-TEST-001", "RESOLVED", tenant_id="tenant_alpha")
    assert ok is True
    assert store.list_tickets(business_id="tenant_alpha")[0]["status"] == "RESOLVED"

    # Invalid status rejection
    with pytest.raises(ValueError):
        store.update_ticket_status("TICK-TEST-001", "INVALID_STATUS", tenant_id="tenant_alpha")


def test_analytics_timezone_and_time_series_integrity():
    """Verify timezone-aware hourly, weekly, seasonal, and festival analysis."""
    summary = review_service.get_analytics_summary("default_business", timezone_str="Asia/Kolkata")

    # Verify 24 hours represented
    assert len(summary["hourly_distribution"]) == 24
    assert "00:00" in summary["hourly_distribution"]
    assert "13:00" in summary["hourly_distribution"]
    assert "23:00" in summary["hourly_distribution"]

    # Verify 7 days of week represented
    assert len(summary["weekly_distribution"]) == 7
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        assert day in summary["weekly_distribution"]

    # Verify busiest day and peak usage time exist
    assert isinstance(summary["busiest_day"], str)
    assert isinstance(summary["peak_usage_time"], str)

    # Verify seasonal analysis contains all four seasons
    seasons = summary["seasonal_analysis"]
    assert "Summer (Mar-Jun)" in seasons
    assert "Monsoon (Jul-Sep)" in seasons
    assert "Autumn & Festive (Oct-Nov)" in seasons
    assert "Winter (Dec-Feb)" in seasons

    # Verify festival analysis has year-specific dates and baseline disclosures
    festivals = summary["festival_analysis"]
    assert isinstance(festivals, list)
    for fest in festivals:
        assert "festival" in fest
        assert "year" in fest
        assert "period" in fest
        assert "insufficient_historical_data" in fest
        assert "notice" in fest

    # Verify data integrity fields
    assert "qr_scans" in summary
    assert "total_generations" in summary
    assert "google_clicks" in summary
    assert "conversion_rate_percent" in summary
    assert "rating_overview" in summary
    assert "business_insights" in summary


def test_password_change_endpoint_enforces_rules(client):
    """Test that password change requires authentication, validates current password, and enforces length."""
    # 1. Unauthenticated attempt
    res = client.post("/api/auth/change-password", json={
        "current_password": "WrongPassword",
        "new_password": "NewValidPassword123!"
    })
    assert res.status_code in (401, 403)

    # 2. Login as default owner
    login_res = client.post("/api/auth/login", json={
        "email": "owner@nastaghar.com",
        "password": "Owner123!",
        "tenant_id": "default_business"
    })
    assert login_res.status_code == 200

    # 3. Short password rejection
    res_short = client.post("/api/auth/change-password", json={
        "current_password": "Owner123!",
        "new_password": "short"
    })
    assert res_short.status_code == 400
    assert "at least 8 characters" in res_short.json()["detail"]

    # 4. Incorrect current password rejection
    res_wrong = client.post("/api/auth/change-password", json={
        "current_password": "CompletelyWrongPassword!",
        "new_password": "NewValidPassword123!"
    })
    assert res_wrong.status_code == 400
    assert "Current password is incorrect" in res_wrong.json()["detail"]
