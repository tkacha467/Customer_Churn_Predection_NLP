"""
Multi-Tenant Authentication & Role-Based Authorization for ChurnLens / NastaGhar.
Implements scrypt password hashing, cryptographically random server-side sessions,
tenant-membership binding, and role-based access control.
"""

import hashlib
import hmac
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException, Request

from api.review_assistant.storage import ReviewStore

OWNER_COOKIE = "nasta_owner_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
_login_attempts = defaultdict(deque)
_login_lock = threading.Lock()

_stores: dict[str, ReviewStore] = {}

def get_store() -> ReviewStore:
    db_path = os.getenv("REVIEW_DB_PATH", "")
    if db_path not in _stores:
        _stores[db_path] = ReviewStore()
    return _stores[db_path]


# ---------------------------------------------------------
# Password Hashing & Verification (scrypt - RFC 7914)
# ---------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes password using Python's standard library scrypt with OWASP-recommended parameters."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        maxmem=32 * 1024 * 1024
    )
    return f"scrypt$16384$8$1${salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies password against stored scrypt hash in constant time."""
    if not password or not stored_hash or not isinstance(stored_hash, str):
        return False
    parts = stored_hash.split("$")
    if len(parts) == 6 and parts[0] == "scrypt":
        try:
            n = int(parts[1])
            r = int(parts[2])
            p = int(parts[3])
            salt = bytes.fromhex(parts[4])
            expected_key = bytes.fromhex(parts[5])
            computed_key = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=n,
                r=r,
                p=p,
                maxmem=32 * 1024 * 1024
            )
            return hmac.compare_digest(computed_key, expected_key)
        except Exception:
            return False
    return False


# ---------------------------------------------------------
# Session Token Generation & Hashing
# ---------------------------------------------------------
def generate_session_token() -> str:
    """Generates a cryptographically secure 256-bit URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Hashes the raw session token with SHA-256 before database lookup/storage."""
    return hashlib.sha256(raw_token.encode("ascii")).hexdigest()


def _sign(val: str) -> str:
    """Compatibility signing helper."""
    return hashlib.sha256(val.encode("ascii")).hexdigest()


def make_session(user_id: Optional[str] = None, tenant_id: str = "default_business") -> str:
    """Creates a valid server-side session token (used for backward compatibility and testing)."""
    store = get_store()
    if not user_id:
        user = store.get_or_create_legacy_owner()
        user_id = user["id"]
    # Ensure tenant exists and user has membership
    if not store.tenant_exists(tenant_id):
        store.upsert_tenant({"id": tenant_id, "business_name": tenant_id})
    if not store.get_membership(user_id, tenant_id):
        store.add_membership(user_id, tenant_id, role="owner")

    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    store.create_session(
        token_hash=token_hash,
        user_id=user_id,
        active_tenant_id=tenant_id,
        expires_at=time.time() + SESSION_TTL_SECONDS
    )
    return raw_token


# ---------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------
def check_login_rate_limit(client_ip: str, now: float | None = None) -> bool:
    """Allow at most 10 login attempts per IP per minute."""
    now = time.time() if now is None else now
    with _login_lock:
        attempts = _login_attempts[client_ip]
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= 10:
            return False
        attempts.append(now)
        return True


# ---------------------------------------------------------
# Tenant Authorization Context
# ---------------------------------------------------------
@dataclass
class TenantContext:
    user_id: str
    email: str
    display_name: str
    tenant_id: str
    role: str  # 'owner', 'manager', 'staff'
    is_platform_admin: bool = False


def is_cookie_secure() -> bool:
    """Returns True if session cookies should be marked Secure (HTTPS)."""
    explicit = os.getenv("COOKIE_SECURE", "").strip().lower()
    if explicit in ("true", "1", "yes"):
        return True
    if explicit in ("false", "0", "no"):
        return False
    return os.getenv("ENVIRONMENT", "development").strip().lower() == "production"


def check_csrf_origin(request: Request) -> None:
    """Validates request origin on mutating HTTP methods against allowed CORS origins."""
    if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
        origin = request.headers.get("origin")
        if not origin:
            ref = request.headers.get("referer", "")
            match = re.match(r"^(https?://[^/]+)", ref)
            if match:
                origin = match.group(1)

        allowed = {
            value.strip().rstrip("/")
            for value in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if value.strip()
        }

        if origin:
            if origin.rstrip("/") not in allowed:
                raise HTTPException(status_code=403, detail="Request origin is not allowed")
        elif OWNER_COOKIE in request.cookies and os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise HTTPException(status_code=403, detail="Missing origin header on authenticated mutation")


async def require_auth_context(request: Request) -> TenantContext:
    """
    Extracts and validates the server-side session from cookie or Authorization header.
    Verifies user status, active tenant membership, and CSRF origin.
    """
    # 1. Extract raw token
    token = request.cookies.get(OWNER_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 2. Lookup session by SHA-256 hash
    store = get_store()
    token_hash = hash_token(token)
    session = store.get_session(token_hash)
    now = time.time()

    if not session or session.get("revoked_at") is not None or session.get("expires_at", 0) < now:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in again.")

    # 3. Lookup user & verify active status
    user = store.get_user_by_id(session["user_id"])
    if not user or user.get("is_active") != 1:
        raise HTTPException(status_code=401, detail="User account is deactivated or not found.")

    # 4. Verify membership in active tenant
    active_tenant_id = session["active_tenant_id"]
    is_admin = bool(user.get("is_platform_admin", 0))
    membership = store.get_membership(user["id"], active_tenant_id)
    if not membership and not is_admin:
        raise HTTPException(status_code=403, detail="Active tenant access is revoked.")

    # Immediately invalidate sessions for suspended tenants (unless platform admin)
    active_tenant = store.get_tenant(active_tenant_id)
    if not is_admin and active_tenant and active_tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Business '{active_tenant_id}' is inactive or suspended.")

    effective_role = membership["role"] if membership else ("owner" if is_admin else "staff")

    # 5. Check CSRF Origin
    check_csrf_origin(request)

    return TenantContext(
        user_id=user["id"],
        email=user["email"],
        display_name=user.get("display_name", ""),
        tenant_id=active_tenant_id,
        role=effective_role,
        is_platform_admin=is_admin
    )


ROLE_RANKS = {
    "staff": 1,
    "manager": 2,
    "owner": 3
}


def require_tenant_access(required_role: str = "manager", required_entitlement: Optional[str] = None):
    """
    FastAPI dependency factory enforcing tenant boundaries and role levels.
    If the endpoint receives a specific business_id (in path or query parameters),
    this dependency asserts that the authenticated user has an active membership
    in that specific business_id with the required role.
    """
    async def dependency(request: Request) -> TenantContext:
        ctx = await require_auth_context(request)
        store = get_store()

        # Check for requested tenant from path or query params
        target_id = request.path_params.get("business_id") or request.query_params.get("business_id")

        if target_id in ("default_business", "nasta_ghar"):
            target_id = "default_business"

        effective_tenant = ctx.tenant_id
        effective_role = ctx.role

        if target_id and target_id != ctx.tenant_id:
            # Caller explicitly requested a business different from session active tenant
            if ctx.is_platform_admin:
                # Platform administrator can manage any tenant or onboard new tenants
                target_tenant = store.get_tenant(target_id)
                if not target_tenant and request.method in {"POST", "PUT"} and "config" in request.url.path:
                    store.upsert_tenant({"id": target_id, "business_name": target_id})
                    store.add_membership(ctx.user_id, target_id, role="owner")
                elif not target_tenant:
                    raise HTTPException(status_code=404, detail=f"Business '{target_id}' not found.")
                effective_tenant = target_id
                effective_role = "owner"
            else:
                # Ordinary owner or staff MUST have an existing membership in target_id
                target_membership = store.get_membership(ctx.user_id, target_id)
                if not target_membership:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied: You do not have an authorized membership for business '{target_id}'."
                    )
                # Verify tenant is active
                target_tenant = store.get_tenant(target_id)
                if not target_tenant or target_tenant.get("status") != "active":
                    raise HTTPException(
                        status_code=403,
                        detail=f"Business '{target_id}' is inactive or suspended."
                    )
                effective_tenant = target_id
                effective_role = target_membership["role"]

        # Validate role hierarchy
        if ROLE_RANKS.get(effective_role, 0) < ROLE_RANKS.get(required_role, 2):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for this operation. Requires '{required_role}' role (current role: '{effective_role}')."
            )

        # Verify that the effective tenant is active
        effective_record = store.get_tenant(effective_tenant)
        if not effective_record or effective_record.get("status") != "active":
            raise HTTPException(
                status_code=403,
                detail=f"Business '{effective_tenant}' is inactive or suspended."
            )

        if required_entitlement:
            from api.review_assistant.entitlements import check_tenant_entitlement
            if not check_tenant_entitlement(effective_tenant, required_entitlement):
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature module '{required_entitlement}' is not enabled for business '{effective_tenant}'."
                )

        return TenantContext(
            user_id=ctx.user_id,
            email=ctx.email,
            display_name=ctx.display_name,
            tenant_id=effective_tenant,
            role=effective_role,
            is_platform_admin=ctx.is_platform_admin
        )

    return dependency


async def require_platform_admin(request: Request) -> TenantContext:
    """FastAPI dependency requiring an active platform administrator session."""
    ctx = await require_auth_context(request)
    if not ctx.is_platform_admin:
        raise HTTPException(
            status_code=403,
            detail="Platform administrator privileges required."
        )
    return ctx


# Backward-compatible alias for owner operations
require_owner = require_tenant_access("owner")
