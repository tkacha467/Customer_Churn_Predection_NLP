"""
Regression tests for Phase A5.0.49 Critical Security Defect Remediation:
- SEC-GAP-01: Turnstile dummy-token bypass prohibited in non-dev environments
- SEC-GAP-02: Dummy site-key and secret-key startup & runtime enforcement
- SEC-GAP-03: CIDR-aware trusted proxy traversal and wildcard rejection
"""
import os
import pytest
from unittest.mock import AsyncMock, patch
from starlette.requests import Request
from backend.app.main import validate_environment_config
from backend.app.core.auth.security_store import (
    verify_turnstile_token,
    CF_DUMMY_PASS_SITEKEY,
    CF_DUMMY_FAIL_SITEKEY,
    CF_DUMMY_PASS_SECRET,
    CF_DUMMY_FAIL_SECRET,
)
from backend.app.api.routes import get_client_ip


# =========================================================================
# 1. SEC-GAP-01: TURNSTILE DUMMY-TOKEN BYPASS REMEDIATION
# =========================================================================

@pytest.mark.anyio
async def test_turnstile_dev_test_dummy_pass_accepted(monkeypatch):
    """Development and test environments permit dummy-pass tokens for local testing."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "dummy_or_empty")

    ok, reason = await verify_turnstile_token("XXXX.DUMMY.TOKEN.PASS", "127.0.0.1")
    assert ok is True
    assert reason == "test_pass"

    ok, reason = await verify_turnstile_token(CF_DUMMY_PASS_SITEKEY, "127.0.0.1")
    assert ok is True
    assert reason == "test_pass"


@pytest.mark.anyio
@pytest.mark.parametrize("env_name", ["staging", "production", "unknown_custom_env"])
@pytest.mark.parametrize("dummy_token", [
    "XXXX.DUMMY.TOKEN.PASS",
    CF_DUMMY_PASS_SITEKEY,
    "test-token-valid",
    "test_pass_token_12345",
])
async def test_turnstile_staging_and_prod_reject_every_dummy_pass_token(monkeypatch, env_name, dummy_token):
    """In staging and production, all test/dummy pass tokens must be rejected without calling Cloudflare."""
    monkeypatch.setenv("ENVIRONMENT", env_name)
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAGenuineSecretKey32CharsLong!")

    ok, reason = await verify_turnstile_token(dummy_token, "203.0.113.5")
    assert ok is False
    assert reason == "dummy_token_forbidden_in_production"


@pytest.mark.anyio
@pytest.mark.parametrize("env_name", ["development", "test", "staging", "production"])
async def test_turnstile_dummy_fail_tokens_rejected(monkeypatch, env_name):
    """Dummy fail tokens are rejected across all environments."""
    monkeypatch.setenv("ENVIRONMENT", env_name)
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAGenuineSecretKey32CharsLong!")

    ok, reason = await verify_turnstile_token("XXXX.DUMMY.TOKEN.FAIL", "127.0.0.1")
    assert ok is False

    ok, reason = await verify_turnstile_token(CF_DUMMY_FAIL_SITEKEY, "127.0.0.1")
    assert ok is False


@pytest.mark.anyio
async def test_turnstile_genuine_siteverify_success(monkeypatch):
    """Genuine tokens are verified via mocked Cloudflare Siteverify and accepted when valid."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAGenuineStagingSecretKey123")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "staging.nastaghar.com")

    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "action": "owner_login",
        "hostname": "staging.nastaghar.com",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        ok, reason = await verify_turnstile_token("genuine-turnstile-response-token", "203.0.113.10")
        assert ok is True
        assert reason == "ok"


@pytest.mark.anyio
async def test_turnstile_siteverify_timeout_and_http_errors_fail_closed(monkeypatch):
    """Siteverify network timeouts and upstream 5xx errors fail closed."""
    import httpx
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAGenuineProdSecretKey123")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")

    # 1. Timeout failure
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectTimeout("Cloudflare unreachable")):
        ok, reason = await verify_turnstile_token("genuine-token", "203.0.113.10")
        assert ok is False
        assert reason == "provider_timeout"

    # 2. Upstream 502 Bad Gateway
    mock_resp = AsyncMock()
    mock_resp.status_code = 502
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        ok, reason = await verify_turnstile_token("genuine-token", "203.0.113.10")
        assert ok is False
        assert reason == "upstream_status_502"


# =========================================================================
# 2. SEC-GAP-02: DUMMY SITE-KEY & SECRET-KEY VALIDATION
# =========================================================================

def test_boot_validation_rejects_dummy_site_key(monkeypatch):
    """Staging and production reject Cloudflare dummy site keys at startup."""
    for env in ("staging", "production"):
        monkeypatch.setenv("ENVIRONMENT", env)
        monkeypatch.setenv("OWNER_SESSION_SECRET", "session-secret-at-least-32-characters-long")
        monkeypatch.setenv("REDIS_URL", "rediss://valkey.internal:6379/0")
        monkeypatch.setenv("SECURITY_HMAC_SECRET", "hmac-secret-at-least-32-characters-long")
        monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
        monkeypatch.setenv("TURNSTILE_ENABLED", "true")
        monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAValidSecretKey1234567890")
        monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")
        if env == "production":
            monkeypatch.setenv("OWNER_PASSWORD", "SuperSecurePassword1234567890!")
            monkeypatch.setenv("CORS_ORIGINS", "https://app.nastaghar.com")
            monkeypatch.setenv("REVIEW_DB_PATH", "/data/reviews.sqlite3")
            monkeypatch.setenv("BUSINESS_LINKS_PATH", "/data/links.json")

        # Test pass dummy sitekey rejected
        monkeypatch.setenv("TURNSTILE_SITE_KEY", CF_DUMMY_PASS_SITEKEY)
        with pytest.raises(RuntimeError, match="cannot use Cloudflare dummy test keys"):
            validate_environment_config(env)

        # Test fail dummy sitekey rejected
        monkeypatch.setenv("TURNSTILE_SITE_KEY", CF_DUMMY_FAIL_SITEKEY)
        with pytest.raises(RuntimeError, match="cannot use Cloudflare dummy test keys"):
            validate_environment_config(env)


def test_boot_validation_rejects_dummy_secret_key(monkeypatch):
    """Staging and production reject Cloudflare dummy secret keys at startup."""
    for env in ("staging", "production"):
        monkeypatch.setenv("ENVIRONMENT", env)
        monkeypatch.setenv("OWNER_SESSION_SECRET", "session-secret-at-least-32-characters-long")
        monkeypatch.setenv("REDIS_URL", "rediss://valkey.internal:6379/0")
        monkeypatch.setenv("SECURITY_HMAC_SECRET", "hmac-secret-at-least-32-characters-long")
        monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
        monkeypatch.setenv("TURNSTILE_ENABLED", "true")
        monkeypatch.setenv("TURNSTILE_SITE_KEY", "0x4AAAAAAAValidSiteKey1234567890")
        monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")
        if env == "production":
            monkeypatch.setenv("OWNER_PASSWORD", "SuperSecurePassword1234567890!")
            monkeypatch.setenv("CORS_ORIGINS", "https://app.nastaghar.com")
            monkeypatch.setenv("REVIEW_DB_PATH", "/data/reviews.sqlite3")
            monkeypatch.setenv("BUSINESS_LINKS_PATH", "/data/links.json")

        # Test pass dummy secret rejected
        monkeypatch.setenv("TURNSTILE_SECRET_KEY", CF_DUMMY_PASS_SECRET)
        with pytest.raises(RuntimeError, match="cannot use Cloudflare dummy test keys"):
            validate_environment_config(env)

        # Test fail dummy secret rejected
        monkeypatch.setenv("TURNSTILE_SECRET_KEY", CF_DUMMY_FAIL_SECRET)
        with pytest.raises(RuntimeError, match="cannot use Cloudflare dummy test keys"):
            validate_environment_config(env)


def test_boot_validation_accepts_genuine_staging_keys(monkeypatch):
    """Staging startup succeeds with genuine site and secret keys."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "session-secret-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_URL", "rediss://valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "hmac-secret-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "0x4AAAAAAAGenuineStagingSiteKey")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAGenuineStagingSecretKey")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "staging.nastaghar.com")

    validate_environment_config("staging")


# =========================================================================
# 3. SEC-GAP-03: TRUSTED PROXY VALIDATION (CIDR & SPOOFING)
# =========================================================================

def _make_dummy_request(client_host: str, headers: dict = None) -> Request:
    scope = {
        "type": "http",
        "client": (client_host, 12345),
        "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in (headers or {}).items()],
    }
    return Request(scope)


def test_trusted_proxy_exact_ipv4(monkeypatch):
    """Exact trusted IPv4 peer allows X-Forwarded-For client IP extraction."""
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.5")
    req = _make_dummy_request("10.0.0.5", {"x-forwarded-for": "198.51.100.42"})
    assert get_client_ip(req) == "198.51.100.42"


def test_trusted_proxy_ipv4_cidr(monkeypatch):
    """Trusted IPv4 CIDR subnet allows peer match and extracts correct client IP."""
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.0/8, 172.16.0.0/12")
    # Ingress proxy peer IP falls inside 10.0.0.0/8
    req = _make_dummy_request("10.12.34.56", {"x-forwarded-for": "203.0.113.88"})
    assert get_client_ip(req) == "203.0.113.88"


def test_trusted_proxy_ipv6_exact_and_cidr(monkeypatch):
    """Trusted IPv6 exact address and IPv6 CIDR subnet extraction."""
    monkeypatch.setenv("TRUSTED_PROXIES", "2001:db8::1, 2001:db8:abcd::/48")

    # Exact IPv6 proxy
    req1 = _make_dummy_request("2001:db8::1", {"x-forwarded-for": "203.0.113.99"})
    assert get_client_ip(req1) == "203.0.113.99"

    # Subnet IPv6 proxy
    req2 = _make_dummy_request("2001:db8:abcd:1234::5", {"x-forwarded-for": "203.0.113.100"})
    assert get_client_ip(req2) == "203.0.113.100"


def test_untrusted_direct_peer_cannot_spoof_forwarded_for(monkeypatch):
    """Untrusted direct peer IP ignores X-Forwarded-For header completely."""
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1")
    # Peer is an attacker IP not in trusted proxies
    req = _make_dummy_request("198.51.100.99", {"x-forwarded-for": "1.1.1.1, 8.8.8.8"})
    assert get_client_ip(req) == "198.51.100.99"


def test_multiple_trusted_proxy_hops_reverse_traversal(monkeypatch):
    """Reverse traversal correctly identifies the first non-trusted upstream IP."""
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1, 10.0.0.2, 172.16.0.0/12")
    # Client 203.0.113.50 connects via proxy 172.16.5.5 -> proxy 10.0.0.2 -> proxy 10.0.0.1 (peer)
    req = _make_dummy_request(
        "10.0.0.1",
        {"x-forwarded-for": "spoofed.untrusted.attacker, 203.0.113.50, 172.16.5.5, 10.0.0.2"}
    )
    assert get_client_ip(req) == "203.0.113.50"


def test_malformed_forwarded_ip_fails_safely(monkeypatch):
    """Malformed forwarded IP headers fall back safely to peer IP."""
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1")
    req = _make_dummy_request("10.0.0.1", {"x-forwarded-for": "not-a-valid-ip, 999.999.999.999"})
    assert get_client_ip(req) == "10.0.0.1"


def test_wildcard_trusted_proxies_rejected_in_staging_and_prod(monkeypatch):
    """Wildcard '*' in TRUSTED_PROXIES is strictly rejected in staging and production."""
    for env in ("staging", "production"):
        monkeypatch.setenv("ENVIRONMENT", env)
        monkeypatch.setenv("OWNER_SESSION_SECRET", "session-secret-at-least-32-characters-long")
        monkeypatch.setenv("REDIS_URL", "rediss://valkey.internal:6379/0")
        monkeypatch.setenv("SECURITY_HMAC_SECRET", "hmac-secret-at-least-32-characters-long")
        monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
        monkeypatch.setenv("TURNSTILE_ENABLED", "true")
        monkeypatch.setenv("TURNSTILE_SITE_KEY", "0x4AAAAAAAValidSiteKey1234567890")
        monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAValidSecretKey1234567890")
        monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")
        if env == "production":
            monkeypatch.setenv("OWNER_PASSWORD", "SuperSecurePassword1234567890!")
            monkeypatch.setenv("CORS_ORIGINS", "https://app.nastaghar.com")
            monkeypatch.setenv("REVIEW_DB_PATH", "/data/reviews.sqlite3")
            monkeypatch.setenv("BUSINESS_LINKS_PATH", "/data/links.json")

        monkeypatch.setenv("TRUSTED_PROXIES", "*")
        with pytest.raises(RuntimeError, match="cannot contain wildcard"):
            validate_environment_config(env)


def test_malformed_trusted_proxy_configuration_rejected_at_boot(monkeypatch):
    """Malformed IP/CIDR in TRUSTED_PROXIES is rejected at boot in staging."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OWNER_SESSION_SECRET", "session-secret-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_URL", "rediss://valkey.internal:6379/0")
    monkeypatch.setenv("SECURITY_HMAC_SECRET", "hmac-secret-at-least-32-characters-long")
    monkeypatch.setenv("REDIS_FAILURE_POLICY", "fail_closed")
    monkeypatch.setenv("TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("TURNSTILE_SITE_KEY", "0x4AAAAAAAValidSiteKey1234567890")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAAValidSecretKey1234567890")
    monkeypatch.setenv("TURNSTILE_ALLOWED_HOSTNAMES", "app.nastaghar.com")

    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1, not-a-cidr-or-ip/99")
    with pytest.raises(RuntimeError, match="Invalid IP address or CIDR network in TRUSTED_PROXIES"):
        validate_environment_config("staging")
