"""
VRAJA AI — SEC-04 Genuine Multi-Process Shared Security State Verification.

Adversarial test suite executing across independent operating-system processes:
- Spawns true OS processes using multiprocessing.get_context("spawn")
- Verifies state visibility and cross-process atomicity against live Valkey
- Proves composite pair cooldown enforcement across independent workers
- Validates distributed risk tracking across separate backend worker processes
- Validates dual-key HMAC rotation across independent processes
- Validates HTTP multi-worker server integration across separate ports
- Validates Valkey outage fail-closed behavior
"""

import asyncio
import multiprocessing as mp
import os
import sys
import time
import traceback
import uuid
from typing import Dict, Any

import httpx
import pytest

# Ensure repository root is in sys.path and inherited by spawned child processes
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "../.."))

if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _TEST_DIR not in sys.path:
    sys.path.append(_TEST_DIR)

_existing_pp = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = f"{_REPO_ROOT}:{_TEST_DIR}:{_existing_pp}".rstrip(":")

# Module Constants
TEST_REDIS_URL = "redis://127.0.0.1:6379/0"
TEST_HMAC_SECRET = "production-grade-hmac-secret-at-least-32-chars-long-multiprocess-test"
TEST_HMAC_KEY_ID = "k1"
TEST_SESSION_SECRET = "production-grade-session-signing-secret-32-chars-long"


# ==============================================================================
# TOP-LEVEL MODULE-SCOPE WORKER FUNCTIONS
# (Must be top-level module functions for macOS 'spawn' pickling)
# ==============================================================================

def worker_record_failure(
    result_queue: mp.Queue,
    redis_url: str,
    hmac_secret: str,
    key_id: str,
    client_ip: str,
    email: str
) -> None:
    """Worker process: records a single login failure in Valkey."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        os.environ["SECURITY_HMAC_KEY_ID"] = key_id
        from backend.app.core.auth.security_store import (
            SecurityStore,
            close_redis_client,
            reset_redis_client,
        )
        reset_redis_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            cooldown, step = loop.run_until_complete(
                SecurityStore.record_login_failure(client_ip, email)
            )
            result_queue.put({
                "success": True,
                "cooldown": cooldown,
                "step": step,
                "pid": os.getpid()
            })
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        result_queue.put({
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "pid": os.getpid()
        })


def worker_evaluate_pre_auth(
    result_queue: mp.Queue,
    redis_url: str,
    hmac_secret: str,
    key_id: str,
    client_ip: str,
    email: str,
    prev_secret: str = "",
    prev_key_id: str = ""
) -> None:
    """Worker process: evaluates pre-authentication gate in Valkey."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        os.environ["SECURITY_HMAC_KEY_ID"] = key_id
        if prev_secret:
            os.environ["SECURITY_HMAC_SECRET_PREVIOUS"] = prev_secret
            os.environ["SECURITY_HMAC_KEY_ID_PREVIOUS"] = prev_key_id or "k0"
        else:
            os.environ.pop("SECURITY_HMAC_SECRET_PREVIOUS", None)
            os.environ.pop("SECURITY_HMAC_KEY_ID_PREVIOUS", None)

        from backend.app.core.auth.security_store import (
            SecurityStore,
            close_redis_client,
            reset_redis_client,
        )
        reset_redis_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            is_allowed, status_code, wait_seconds, challenge_required = loop.run_until_complete(
                SecurityStore.evaluate_pre_auth(client_ip, email)
            )
            result_queue.put({
                "success": True,
                "is_allowed": is_allowed,
                "status_code": status_code,
                "wait_seconds": wait_seconds,
                "challenge_required": challenge_required,
                "pid": os.getpid()
            })
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        result_queue.put({
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "pid": os.getpid()
        })


def worker_record_success(
    result_queue: mp.Queue,
    redis_url: str,
    hmac_secret: str,
    key_id: str,
    client_ip: str,
    email: str
) -> None:
    """Worker process: clears pair cooldown upon successful login."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        os.environ["SECURITY_HMAC_KEY_ID"] = key_id
        from backend.app.core.auth.security_store import (
            SecurityStore,
            close_redis_client,
            reset_redis_client,
        )
        reset_redis_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                SecurityStore.record_login_success(client_ip, email)
            )
            result_queue.put({"success": True, "pid": os.getpid()})
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        result_queue.put({
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "pid": os.getpid()
        })


def worker_batch_record_failures(
    result_queue: mp.Queue,
    redis_url: str,
    hmac_secret: str,
    key_id: str,
    client_ip: str,
    email: str,
    count: int
) -> None:
    """Worker process: records multiple failures consecutively."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        os.environ["SECURITY_HMAC_KEY_ID"] = key_id
        from backend.app.core.auth.security_store import (
            SecurityStore,
            close_redis_client,
            reset_redis_client,
        )
        reset_redis_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            last_cooldown, last_step = 0, 0
            for _ in range(count):
                last_cooldown, last_step = loop.run_until_complete(
                    SecurityStore.record_login_failure(client_ip, email)
                )
            result_queue.put({
                "success": True,
                "last_cooldown": last_cooldown,
                "last_step": last_step,
                "pid": os.getpid()
            })
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        result_queue.put({
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "pid": os.getpid()
        })


def worker_hmac_derivation(
    result_queue: mp.Queue,
    hmac_secret: str,
    email: str
) -> None:
    """Worker process: computes account HMAC identifier."""
    try:
        from backend.app.core.auth.security_store import compute_account_hmac
        account_hmac = compute_account_hmac(email, hmac_secret.encode("utf-8"))
        result_queue.put({
            "success": True,
            "hmac": account_hmac,
            "pid": os.getpid()
        })
    except Exception as exc:
        result_queue.put({
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "pid": os.getpid()
        })


def worker_run_uvicorn_server(
    ready_queue: mp.Queue,
    host: str,
    port: int,
    db_path: str,
    redis_url: str,
    hmac_secret: str,
    key_id: str,
    session_secret: str
) -> None:
    """Worker process: runs a standalone Uvicorn HTTP server."""
    try:
        os.environ["ENVIRONMENT"] = "test"
        os.environ["REVIEW_DB_PATH"] = db_path
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        os.environ["SECURITY_HMAC_KEY_ID"] = key_id
        os.environ["OWNER_SESSION_SECRET"] = session_secret
        os.environ["TRUSTED_PROXIES"] = "*"
        os.environ["TURNSTILE_ENABLED"] = "true"
        os.environ["TURNSTILE_SECRET_KEY"] = "1x0000000000000000000000000000000AA"
        os.environ["REDIS_FAILURE_POLICY"] = "fail_closed"

        from backend.app.core.auth.security_store import reset_redis_client
        reset_redis_client()

        import uvicorn
        from backend.app.main import app

        ready_queue.put({"started": True, "pid": os.getpid()})
        config = uvicorn.Config(app, host=host, port=port, log_level="error")
        server = uvicorn.Server(config)
        server.run()
    except Exception as exc:
        ready_queue.put({"started": False, "error": str(exc), "pid": os.getpid()})


# ==============================================================================
# PYTEST TEST FIXTURE & ISOLATION HELPERS
# ==============================================================================

@pytest.fixture(autouse=True)
def setup_valkey_isolation(monkeypatch):
    """Sets environment variables and cleans Valkey security keys before and after each test."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("REDIS_URL", TEST_REDIS_URL)
    monkeypatch.setenv("SECURITY_HMAC_SECRET", TEST_HMAC_SECRET)
    monkeypatch.setenv("SECURITY_HMAC_KEY_ID", TEST_HMAC_KEY_ID)

    from backend.app.core.auth.security_store import SecurityStore, reset_redis_client
    reset_redis_client()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(SecurityStore.clear_all_security_keys())
    except Exception:
        pass
    finally:
        loop.close()
        reset_redis_client()

    yield

    reset_redis_client()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(SecurityStore.clear_all_security_keys())
    except Exception:
        pass
    finally:
        loop.close()
        reset_redis_client()


# ==============================================================================
# SCENARIOS 1, 2, 3: PROCESS A FAILS, PROCESS B READS STATE & OBSERVES COOLDOWN
# ==============================================================================
def test_scenario_01_to_03_process_a_fails_process_b_reads_cooldown():
    """
    1. Process A records failed login attempts.
    2. Process B independently reads the same account/IP security state.
    3. Process B observes the cooldown created by Process A.
    """
    ctx = mp.get_context("spawn")
    test_ip = "198.51.100.11"
    test_email = f"handshake_{uuid.uuid4().hex[:8]}@example.com"

    # 1. Process A records 5 failed attempts (triggers 30-second cooldown)
    q_a1 = ctx.Queue()
    p_a1 = ctx.Process(
        target=worker_batch_record_failures,
        args=(q_a1, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email, 5),
    )
    p_a1.start()
    p_a1.join(timeout=10.0)
    assert p_a1.exitcode == 0
    res_a1 = q_a1.get(timeout=5.0)
    assert res_a1["success"] is True
    assert res_a1["last_cooldown"] == 30
    assert res_a1["last_step"] == 1
    pid_a1 = res_a1["pid"]

    # 2 & 3. Process B independently reads the state and observes the active cooldown
    q_b1 = ctx.Queue()
    p_b1 = ctx.Process(
        target=worker_evaluate_pre_auth,
        args=(q_b1, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email),
    )
    p_b1.start()
    p_b1.join(timeout=10.0)
    assert p_b1.exitcode == 0
    res_b1 = q_b1.get(timeout=5.0)
    assert res_b1["success"] is True
    assert res_b1["is_allowed"] is False
    assert res_b1["status_code"] == "pair_cooldown_active"
    assert res_b1["wait_seconds"] > 0
    pid_b1 = res_b1["pid"]
    assert pid_a1 != pid_b1, "Process A and Process B must run in separate OS processes"


# ==============================================================================
# SCENARIOS 4, 5: PROCESS B RECORDS FAILURE, PROCESS A OBSERVES ESCALATION
# ==============================================================================
def test_scenario_04_to_05_process_b_fails_process_a_observes_escalation():
    """
    4. Process B records another failure.
    5. Process A observes the updated shared state.
    """
    ctx = mp.get_context("spawn")
    test_ip = "198.51.100.12"
    test_email = f"escalate_{uuid.uuid4().hex[:8]}@example.com"

    # Setup: 5 failures incurred first
    q_init = ctx.Queue()
    p_init = ctx.Process(
        target=worker_batch_record_failures,
        args=(q_init, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email, 5),
    )
    p_init.start()
    p_init.join(timeout=10.0)
    assert p_init.exitcode == 0
    res_init = q_init.get(timeout=5.0)
    assert res_init["last_cooldown"] == 30

    # 4. Process B records another failure (step escalates to 2, cooldown increases to 60s)
    q_b2 = ctx.Queue()
    p_b2 = ctx.Process(
        target=worker_record_failure,
        args=(q_b2, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email),
    )
    p_b2.start()
    p_b2.join(timeout=10.0)
    assert p_b2.exitcode == 0
    res_b2 = q_b2.get(timeout=5.0)
    assert res_b2["success"] is True
    assert res_b2["step"] == 2
    assert res_b2["cooldown"] == 60

    # 5. Process A (spawned fresh process) observes the updated shared state
    q_a2 = ctx.Queue()
    p_a2 = ctx.Process(
        target=worker_evaluate_pre_auth,
        args=(q_a2, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email),
    )
    p_a2.start()
    p_a2.join(timeout=10.0)
    assert p_a2.exitcode == 0
    res_a2 = q_a2.get(timeout=5.0)
    assert res_a2["success"] is True
    assert res_a2["is_allowed"] is False
    assert res_a2["status_code"] == "pair_cooldown_active"
    assert res_a2["wait_seconds"] > 30, f"Expected escalated wait > 30s, got {res_a2['wait_seconds']}"


# ==============================================================================
# SCENARIO 6: SUCCESSFUL LOGIN SHARED CLEANUP
# ==============================================================================
def test_scenario_06_successful_authentication_cleanup_visible_cross_process():
    """
    6. Successful authentication cleanup is visible to another process
       (removes pair cooldown in Valkey) while preserving distributed risk evidence.
    """
    ctx = mp.get_context("spawn")
    test_ip = "198.51.100.22"
    test_email = f"clean_{uuid.uuid4().hex[:8]}@example.com"

    # Worker A triggers cooldown
    q1 = ctx.Queue()
    p1 = ctx.Process(
        target=worker_batch_record_failures,
        args=(q1, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email, 5),
    )
    p1.start()
    p1.join(timeout=10.0)
    assert p1.exitcode == 0
    res1 = q1.get(timeout=5.0)
    assert res1["last_cooldown"] > 0

    # Worker B records successful login
    q2 = ctx.Queue()
    p2 = ctx.Process(
        target=worker_record_success,
        args=(q2, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email),
    )
    p2.start()
    p2.join(timeout=10.0)
    assert p2.exitcode == 0
    res2 = q2.get(timeout=5.0)
    assert res2["success"] is True

    # Worker C evaluates pre-auth and verifies cooldown is lifted
    q3 = ctx.Queue()
    p3 = ctx.Process(
        target=worker_evaluate_pre_auth,
        args=(q3, TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email),
    )
    p3.start()
    p3.join(timeout=10.0)
    assert p3.exitcode == 0
    res3 = q3.get(timeout=5.0)
    assert res3["is_allowed"] is True
    assert res3["status_code"] == "admitted"
    assert res3["wait_seconds"] == 0

    # Direct Valkey check: Confirm risk ZSET still retains the 5 failure entries
    from backend.app.core.auth.security_store import get_redis_client, compute_account_hmac, close_redis_client
    loop = asyncio.new_event_loop()
    try:
        r = get_redis_client()
        acct_hmac = compute_account_hmac(test_email, TEST_HMAC_SECRET.encode("utf-8"))
        risk_key = f"v1:auth:risk:{TEST_HMAC_KEY_ID}:{acct_hmac}:failures"
        card = loop.run_until_complete(r.zcard(risk_key))
        assert card == 5, f"Risk evidence must be preserved! Expected 5, found {card}"
    finally:
        loop.run_until_complete(close_redis_client())
        loop.close()


# ==============================================================================
# SCENARIO 7: HMAC ACCOUNT IDENTIFIER CONSISTENCY & ISOLATION
# ==============================================================================
def test_scenario_07_hmac_account_identifiers_identical_across_processes():
    """
    7. HMAC account identifiers remain identical across processes using the same configured key,
       and distinct across processes with different keys.
    """
    ctx = mp.get_context("spawn")
    test_email = "owner@consistent-bistro.com"
    secret_k1 = "super-secret-hmac-key-at-least-32-chars-long-k1"
    secret_k2 = "super-secret-hmac-key-at-least-32-chars-long-k2"

    q1, q2, q3 = ctx.Queue(), ctx.Queue(), ctx.Queue()

    p1 = ctx.Process(target=worker_hmac_derivation, args=(q1, secret_k1, test_email))
    p2 = ctx.Process(target=worker_hmac_derivation, args=(q2, secret_k1, test_email))
    p3 = ctx.Process(target=worker_hmac_derivation, args=(q3, secret_k2, test_email))

    for p in (p1, p2, p3):
        p.start()
    for p in (p1, p2, p3):
        p.join(timeout=10.0)
        assert p.exitcode == 0

    res1 = q1.get(timeout=5.0)
    res2 = q2.get(timeout=5.0)
    res3 = q3.get(timeout=5.0)

    assert res1["success"] and res2["success"] and res3["success"]
    assert res1["hmac"] == res2["hmac"], "HMACs derived with same secret must match across processes"
    assert len(res1["hmac"]) == 32
    assert res1["hmac"] != res3["hmac"], "HMACs derived with different secrets must differ"


# ==============================================================================
# SCENARIO 8: DUAL-KEY ROTATION PRESERVES ACTIVE COOLDOWN
# ==============================================================================
def test_scenario_08_key_rotation_preserves_active_cooldown():
    """
    8. Key rotation preserves the intended active cooldown behavior:
       Worker A incurs cooldown under key k1.
       Worker B evaluates pre-auth configured with primary=k2, previous=k1.
       Proves Worker B still enforces the active cooldown created under k1.
    """
    ctx = mp.get_context("spawn")
    test_ip = "198.51.100.99"
    test_email = f"rotation_{uuid.uuid4().hex[:8]}@example.com"
    secret_k1 = "initial-secret-at-least-32-chars-long-k1"
    secret_k2 = "promoted-secret-at-least-32-chars-long-k2"

    # Worker A triggers cooldown under k1
    q1 = ctx.Queue()
    p1 = ctx.Process(
        target=worker_batch_record_failures,
        args=(q1, TEST_REDIS_URL, secret_k1, "k1", test_ip, test_email, 5),
    )
    p1.start()
    p1.join(timeout=10.0)
    assert p1.exitcode == 0
    res1 = q1.get(timeout=5.0)
    assert res1["last_cooldown"] > 0

    # Worker B evaluates pre-auth under rotated configuration: primary=k2, previous=k1
    q2 = ctx.Queue()
    p2 = ctx.Process(
        target=worker_evaluate_pre_auth,
        args=(q2, TEST_REDIS_URL, secret_k2, "k2", test_ip, test_email, secret_k1, "k1"),
    )
    p2.start()
    p2.join(timeout=10.0)
    assert p2.exitcode == 0
    res2 = q2.get(timeout=5.0)
    assert res2["is_allowed"] is False
    assert res2["status_code"] == "pair_cooldown_active"
    assert res2["wait_seconds"] > 0


# ==============================================================================
# SCENARIO 9: SIMULTANEOUS REQUESTS ATOMIC ADMISSION CHECKS (NO BYPASS)
# ==============================================================================
def test_scenario_09_simultaneous_requests_atomic_admission_no_bypass():
    """
    9. Simultaneous requests from multiple processes do not bypass atomic admission controls.
       All concurrent writes increment the shared risk ZSET atomically without dropped updates.
    """
    ctx = mp.get_context("spawn")
    test_email = f"atomic_{uuid.uuid4().hex[:8]}@example.com"
    num_workers = 6

    queues = [ctx.Queue() for _ in range(num_workers)]
    processes = []
    pids = set()

    for i in range(num_workers):
        ip = f"198.51.100.{40 + i}"
        p = ctx.Process(
            target=worker_record_failure,
            args=(queues[i], TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, ip, test_email),
        )
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join(timeout=10.0)
        assert p.exitcode == 0

    for q in queues:
        res = q.get(timeout=5.0)
        assert res["success"] is True
        pids.add(res["pid"])

    assert len(pids) == num_workers, "All workers must run as distinct OS processes"

    # Confirm Valkey risk ZSET has exactly 6 entries
    from backend.app.core.auth.security_store import get_redis_client, compute_account_hmac, close_redis_client
    loop = asyncio.new_event_loop()
    try:
        r = get_redis_client()
        acct_hmac = compute_account_hmac(test_email, TEST_HMAC_SECRET.encode("utf-8"))
        risk_key = f"v1:auth:risk:{TEST_HMAC_KEY_ID}:{acct_hmac}:failures"
        card = loop.run_until_complete(r.zcard(risk_key))
        assert card == num_workers, f"Expected {num_workers} atomic entries, found {card}"
    finally:
        loop.run_until_complete(close_redis_client())
        loop.close()


# ==============================================================================
# SCENARIO 10: REDIS OUTAGE PRODUCES FAIL-CLOSED RESPONSE
# ==============================================================================
def test_scenario_10_redis_outage_produces_fail_closed_response():
    """
    10. Redis outage produces the configured fail-closed response:
        Pre-auth against unreachable Valkey returns status_code == 'valkey_unavailable' (HTTP 503).
    """
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    test_ip = "198.51.100.123"
    test_email = "outage@example.com"
    dead_redis_url = "redis://127.0.0.1:9999/0"

    p = ctx.Process(
        target=worker_evaluate_pre_auth,
        args=(q, dead_redis_url, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, test_ip, test_email),
    )
    p.start()
    p.join(timeout=10.0)
    assert p.exitcode == 0
    res = q.get(timeout=5.0)
    assert res["success"] is True
    assert res["is_allowed"] is False
    assert res["status_code"] == "valkey_unavailable"
    assert res["wait_seconds"] == 30


# ==============================================================================
# SCENARIO 11: HTTP MULTI-WORKER SERVER INTEGRATION TEST
# ==============================================================================
def test_scenario_11_http_multi_worker_server_integration(tmp_path):
    """
    Starts two independent Uvicorn server processes on separate localhost ports
    (8921 and 8922) sharing the same Valkey security store and isolated test database.
    Sends login requests across both servers to prove:
    - Distributed risk tracking across independent server processes.
    - IP/Pair cooldowns created on Server 1 are enforced by Server 2.
    - Distributed failure accumulation triggers Turnstile challenge on Server 2.
    - Successful authentication on Server 1 and session verification on Server 2.
    """
    db_file = tmp_path / "multi_worker_http.sqlite3"
    from backend.app.core.database.storage import ReviewStore
    from backend.app.core.auth.auth import hash_password

    os.environ["ENVIRONMENT"] = "test"
    store = ReviewStore(str(db_file))
    store.upsert_tenant({"id": "multi_tenant_bistro", "business_name": "Multi Tenant Bistro"})
    correct_password = "SuperSecurePassword123!"
    store.create_user(
        email="multi_owner@bistro.com",
        password_hash=hash_password(correct_password),
        display_name="Bistro Owner",
    )
    u = store.get_user_by_email("multi_owner@bistro.com")
    store.add_membership(u["id"], "multi_tenant_bistro", "owner")

    ctx = mp.get_context("spawn")
    q_s1, q_s2 = ctx.Queue(), ctx.Queue()

    p_s1 = ctx.Process(
        target=worker_run_uvicorn_server,
        args=(q_s1, "127.0.0.1", 8921, str(db_file), TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, TEST_SESSION_SECRET),
    )
    p_s2 = ctx.Process(
        target=worker_run_uvicorn_server,
        args=(q_s2, "127.0.0.1", 8922, str(db_file), TEST_REDIS_URL, TEST_HMAC_SECRET, TEST_HMAC_KEY_ID, TEST_SESSION_SECRET),
    )

    try:
        p_s1.start()
        p_s2.start()

        # Wait for both servers to be ready via health check
        for port in (8921, 8922):
            ready = False
            for _ in range(60):
                try:
                    r = httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=1.0)
                    if r.status_code == 200:
                        ready = True
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            assert ready, f"Server on port {port} failed to start"

        client_ip = "198.51.100.80"
        headers_ip = {"X-Forwarded-For": client_ip}

        # Step 1: Send 5 failed login attempts to Server 1
        with httpx.Client(timeout=5.0) as client:
            for i in range(5):
                r = client.post(
                    "http://127.0.0.1:8921/api/auth/login",
                    json={"email": "multi_owner@bistro.com", "password": f"wrong-pass-{i}"},
                    headers=headers_ip,
                )
                assert r.status_code == 401

            # Step 2: Send request to Server 2 with correct password from same IP
            # Server 2 must enforce the cooldown created by Server 1!
            r_blocked = client.post(
                "http://127.0.0.1:8922/api/auth/login",
                json={"email": "multi_owner@bistro.com", "password": correct_password},
                headers=headers_ip,
            )
            assert r_blocked.status_code == 429
            assert "Too many sign-in attempts for this account" in r_blocked.json()["detail"]
            assert int(r_blocked.headers.get("Retry-After", 0)) > 0

            # Step 3: Trigger distributed attack across both servers (15 more failures from 15 IPs)
            for i in range(15):
                target_port = 8921 if i % 2 == 0 else 8922
                client.post(
                    f"http://127.0.0.1:{target_port}/api/auth/login",
                    json={"email": "multi_owner@bistro.com", "password": f"dist-bad-{i}"},
                    headers={"X-Forwarded-For": f"198.51.100.{110 + i}"},
                )

            # Step 4: Clean IP on Server 2 requires Turnstile challenge before scrypt
            r_challenge = client.post(
                "http://127.0.0.1:8922/api/auth/login",
                json={"email": "multi_owner@bistro.com", "password": correct_password},
                headers={"X-Forwarded-For": "198.51.100.222"},
            )
            assert r_challenge.status_code == 403
            assert r_challenge.headers.get("X-Challenge-Required") == "true"

            # Step 5: Send valid Turnstile token to Server 1 -> successful login!
            r_success = client.post(
                "http://127.0.0.1:8921/api/auth/login",
                json={
                    "email": "multi_owner@bistro.com",
                    "password": correct_password,
                    "turnstile_token": "XXXX.DUMMY.TOKEN.PASS",
                },
                headers={"X-Forwarded-For": "198.51.100.222"},
            )
            assert r_success.status_code == 200
            session_data = r_success.json()
            assert session_data["authenticated"] is True
            assert session_data["user"]["email"] == "multi_owner@bistro.com"
            assert session_data["active_tenant"]["id"] == "multi_tenant_bistro"

            # Step 6: Verify session on Server 2 (multi-tenant authorization intact across processes)
            session_cookie = r_success.cookies.get("owner_session")
            headers_auth = {"Cookie": f"owner_session={session_cookie}"} if session_cookie else {}
            r_session = client.get("http://127.0.0.1:8922/api/auth/session", headers=headers_auth)
            assert r_session.status_code == 200
            assert r_session.json()["authenticated"] is True
            assert r_session.json()["user"]["email"] == "multi_owner@bistro.com"
            assert r_session.json()["active_tenant"]["id"] == "multi_tenant_bistro"

    finally:
        for p in (p_s1, p_s2):
            if p.is_alive():
                p.terminate()
                p.join(timeout=3.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
