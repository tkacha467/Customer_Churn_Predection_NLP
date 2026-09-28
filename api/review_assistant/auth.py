"""Small, signed owner sessions for the single-restaurant owner portal."""

import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi import HTTPException, Request

OWNER_COOKIE = "nasta_owner_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
_login_attempts = defaultdict(deque)
_login_lock = threading.Lock()


@lru_cache(maxsize=1)
def _session_secret() -> bytes:
    configured = os.getenv("OWNER_SESSION_SECRET")
    if configured:
        return configured.encode("utf-8")
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("OWNER_SESSION_SECRET is required in production")
    # Local sessions remain signed but are invalidated whenever the API restarts.
    return secrets.token_bytes(32)


def _sign(expiry: str) -> str:
    return hmac.new(_session_secret(), expiry.encode("ascii"), hashlib.sha256).hexdigest()


def make_session() -> str:
    expiry = str(int(time.time()) + SESSION_TTL_SECONDS)
    return f"{expiry}.{_sign(expiry)}"


def valid_session(token: str | None) -> bool:
    if not token:
        return False
    try:
        expiry, signature = token.split(".", 1)
        return int(expiry) > int(time.time()) and hmac.compare_digest(signature, _sign(expiry))
    except (ValueError, RuntimeError):
        return False


def check_login_rate_limit(client_ip: str, now: float | None = None) -> bool:
    """Allow at most 10 failed or successful login attempts per IP per minute."""
    now = time.time() if now is None else now
    with _login_lock:
        attempts = _login_attempts[client_ip]
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= 10:
            return False
        attempts.append(now)
        return True


async def require_owner(request: Request) -> None:
    if not valid_session(request.cookies.get(OWNER_COOKIE)):
        raise HTTPException(status_code=401, detail="Owner sign-in required")

    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin:
            allowed = {
                value.strip().rstrip("/")
                for value in os.getenv(
                    "CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
                if value.strip()
            }
            if origin.rstrip("/") not in allowed:
                raise HTTPException(status_code=403, detail="Request origin is not allowed")
