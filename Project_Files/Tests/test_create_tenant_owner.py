"""
Unit and integration tests for scripts/create_tenant_owner.py bootstrap utility.
Verifies validation rules, safe secret ingestion methods, and platform-admin privilege boundaries.
"""

import io
import os
import pytest
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

from scripts.create_tenant_owner import (
    validate_email_format,
    validate_tenant_identifier,
    resolve_password,
)
from Backend.app.core.database.storage import ReviewStore


def test_validate_email_format():
    assert validate_email_format("Admin@Staging.Local") == "admin@staging.local"
    assert validate_email_format("owner.branch@hospitality-group.com") == "owner.branch@hospitality-group.com"

    with pytest.raises(ValueError, match="Invalid email address format"):
        validate_email_format("invalid-email-address")

    with pytest.raises(ValueError, match="Invalid email address format"):
        validate_email_format("admin@")

    with pytest.raises(ValueError, match="Invalid email address format"):
        validate_email_format("@domain.com")


def test_validate_tenant_identifier():
    assert validate_tenant_identifier("grand_hotel") == "grand_hotel"
    assert validate_tenant_identifier("cafe-101") == "cafe-101"
    assert validate_tenant_identifier("BISTRO_PARIS") == "bistro_paris"

    with pytest.raises(ValueError, match="Invalid tenant ID"):
        validate_tenant_identifier("a")  # Too short (< 2 chars)

    with pytest.raises(ValueError, match="Invalid tenant ID"):
        validate_tenant_identifier("cafe 101")  # Space forbidden

    with pytest.raises(ValueError, match="Invalid tenant ID"):
        validate_tenant_identifier("tenant/path")  # Path traversal chars forbidden

    with pytest.raises(ValueError, match="Invalid tenant ID"):
        validate_tenant_identifier("tenant;DROP TABLE")  # SQL chars forbidden


def test_resolve_password_stdin(monkeypatch):
    class DummyArgs:
        password_stdin = True
        password = ""

    monkeypatch.setattr(sys, "stdin", io.StringIO("SecretPassword123!\n"))
    pwd = resolve_password(DummyArgs())
    assert pwd == "SecretPassword123!"


def test_resolve_password_env_var(monkeypatch):
    class DummyArgs:
        password_stdin = False
        password = ""

    monkeypatch.setenv("OWNER_BOOTSTRAP_PASSWORD", "EnvSecretPass12345!")
    pwd = resolve_password(DummyArgs())
    assert pwd == "EnvSecretPass12345!"


def test_resolve_password_cli_warning(capsys, monkeypatch):
    class DummyArgs:
        password_stdin = False
        password = "CliSuppliedPass123!"

    monkeypatch.delenv("OWNER_BOOTSTRAP_PASSWORD", raising=False)
    pwd = resolve_password(DummyArgs())
    assert pwd == "CliSuppliedPass123!"
    captured = capsys.readouterr()
    assert "[!] Security Warning:" in captured.err


def test_bootstrap_privilege_boundary_isolation(tmp_path, monkeypatch):
    """
    Verifies that normal owner creation does NOT grant platform admin,
    and only explicit --platform-admin flags can elevate privileges.
    """
    db_file = tmp_path / "test_bootstrap.sqlite3"
    monkeypatch.setenv("REVIEW_DB_PATH", str(db_file))

    store = ReviewStore(database_path=str(db_file))
    store.upsert_tenant({"id": "cafe_test", "business_name": "Test Cafe"})

    # 1. Run main() to create normal tenant owner
    test_args_normal = [
        "create_tenant_owner.py",
        "--email", "owner@cafetest.local",
        "--tenant", "cafe_test",
        "--role", "owner",
        "--password", "RegularOwnerPass123!",
        "--auto-create-tenant"
    ]
    with patch.object(sys, "argv", test_args_normal):
        from scripts.create_tenant_owner import main
        main()

    user_normal = store.get_user_by_email("owner@cafetest.local")
    assert user_normal is not None
    assert user_normal["is_platform_admin"] == 0, "Regular owner MUST NOT have platform admin privilege"

    # 2. Subsequent runs without --platform-admin must NOT elevate existing normal user
    test_args_update = [
        "create_tenant_owner.py",
        "--email", "owner@cafetest.local",
        "--tenant", "cafe_test",
        "--role", "owner",
        "--auto-create-tenant"
    ]
    with patch.object(sys, "argv", test_args_update):
        main()

    user_still_normal = store.get_user_by_email("owner@cafetest.local")
    assert user_still_normal["is_platform_admin"] == 0, "Re-running without --platform-admin must not elevate privileges"

    # 3. Explicit bootstrap with --platform-admin creates superadmin
    test_args_admin = [
        "create_tenant_owner.py",
        "--email", "superadmin@vraja.local",
        "--tenant", "cafe_test",
        "--role", "owner",
        "--password", "SuperAdminPass123!",
        "--platform-admin",
        "--auto-create-tenant"
    ]
    with patch.object(sys, "argv", test_args_admin):
        main()

    user_admin = store.get_user_by_email("superadmin@vraja.local")
    assert user_admin is not None
    assert user_admin["is_platform_admin"] == 1, "Platform admin user MUST have is_platform_admin == 1"
