"""
Tests for SEC-04 boot-time security environment validation.
Verifies strict startup validation for staging and production, and safe development fallback.
"""
import pytest
from backend.app.main import validate_environment_config


def test_dev_and_test_environments_bypass_strict_checks(monkeypatch):
    """Development and test environments should not fail even with minimal config."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    validate_environment_config("development")

    monkeypatch.setenv("ENVIRONMENT", "test")
    validate_environment_config("test")


def test_valid_staging_configuration_passes(monkeypatch):
    """A fully configured staging environment passes startup validation."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "0x4AAAAAAAValidStagingSiteKey")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAValidStagingSecretKey")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "staging.nastaghar.com")
    monkeypatch.setenv("TURNSTILE_VERIFY_URL", "https://challenges.cloudflare.com/turnstile/v0/siteverify")

    validate_environment_config("staging")


def test_valid_production_configuration_passes(monkeypatch):
    """A fully configured production environment passes startup validation."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "production-session-key-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_URL", "rediss://prod-valkey-cluster.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "production-hmac-secret-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "0x4AAAAAAAValidProdSiteKey")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAValidProdSecretKey")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")
    monkeypatch.setenv("TURNSTILE_VERIFY_URL", "https://challenges.cloudflare.com/turnstile/v0/siteverify")
    monkeypatch.setenv("OWNER_PASSWORD", "SuperSecureLongProductionPassword123!")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.nastaghar.com")
    monkeypatch.setenv("REVIEW_DB_PATH", "/data/prod/reviews.sqlite3")
    monkeypatch.setenv("BUSINESS_LINKS_PATH", "/data/prod/links.json")

    validate_environment_config("production")


def test_staging_missing_session_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "short")
    with pytest.raises(RuntimeError, match="OWNER_SESSION_SECRET must contain at least 32 characters"):
        validate_environment_config("staging")


def test_staging_missing_redis_url(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("VALKEY_URL", raising=False)
    with pytest.raises(RuntimeError, match="REDIS_URL must be configured"):
        validate_environment_config("staging")


def test_staging_missing_hmac_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.delenv("SECURITY_HMAC_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="SECURITY_HMAC_SECRET must contain at least 32 characters"):
        validate_environment_config("staging")


def test_staging_rejects_fail_open_redis_policy(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_open")
    with pytest.raises(RuntimeError, match="REDIS_FAILURE_POLICY must be set to 'fail_closed'"):
        validate_environment_config("staging")


def test_staging_rejects_disabled_turnstile(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "false")
    with pytest.raises(RuntimeError, match="TURNSTILE_ENABLED must be explicitly enabled"):
        validate_environment_config("staging")


def test_staging_missing_turnstile_site_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.delenv("TURNSTILE_SITE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="TURNSTILE_SITE_KEY must be configured"):
        validate_environment_config("staging")


def test_staging_missing_turnstile_secret_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "valid-site-key")
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="TURNSTILE_SECRET_KEY must be configured"):
        validate_environment_config("staging")


def test_staging_missing_turnstile_hostnames(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "valid-site-key")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "valid-secret-key")
    monkeypatch.delenv("TURNSTILE_ALLOWED_HOSTNAMES", raising=False)
    with pytest.raises(RuntimeError, match="TURNSTILE_ALLOWED_HOSTNAMES must be configured"):
        validate_environment_config("staging")


def test_staging_insecure_turnstile_verify_url(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "super-secret-session-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_URL", "redis://staging-valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "super-secret-hmac-key-at-least-32-chars-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "valid-site-key")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "valid-secret-key")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "staging.nastaghar.com")
    monkeypatch.setenv("TURNSTILE_VERIFY_URL", "http://insecure-attacker.com/siteverify")
    with pytest.raises(RuntimeError, match="TURNSTILE_VERIFY_URL must use HTTPS"):
        validate_environment_config("staging")


def test_production_localhost_redis_rejected(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "production-session-key-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "production-hmac-secret-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "valid-site-key")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "valid-secret-key")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")
    monkeypatch.delenv("ALLOW_LOCALHOST_REDIS_IN_PRODUCTION", raising=False)
    with pytest.raises(RuntimeError, match="Production REDIS_URL cannot point to localhost/127.0.0.1"):
        validate_environment_config("production")
