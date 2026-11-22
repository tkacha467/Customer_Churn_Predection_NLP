"""
SEC-04 Multi-Process Synchronization Verification Suite.

Validates that independent OS processes using multiprocessing `spawn` start method
atomically read and write shared authentication security state in Valkey/Redis.

Tests:
- Test A: Cross-process failure visibility (Worker 1 fails -> Worker 2 evaluates)
- Test B: Cross-process IP protection (Worker 1 activates IP rate limit -> Worker 2 blocked)
- Test C: Cross-process account risk (Multiple workers distributed attack -> Worker detects challenge threshold)
- Test D: Concurrent atomic updates (Multiple concurrent workers -> exact ZSET counts verified)
- Test E: Worker isolation (State persists after Worker 1 terminates; Worker 2 observes state)
"""
import asyncio
import multiprocessing as mp
import os
import sys
import time
import uuid
import pytest

# Ensure repository root is in sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from backend.app.core.auth.security_store import (
    SecurityStore,
    close_redis_client,
    reset_redis_client,
    get_redis_client,
)

TEST_REDIS_URL = "redis://127.0.0.1:6379/0"
TEST_HMAC_SECRET = "production-grade-hmac-secret-at-least-32-chars-long-sec04-test"


# ==============================================================================
# TOP-LEVEL MODULE-SCOPED WORKER FUNCTIONS (Must be pickle-serializable for spawn)
# ==============================================================================

def worker_record_failure(queue: mp.Queue, email: str, ip: str, redis_url: str, hmac_secret: str) -> None:
    """Worker: Records a single login failure in Valkey, then terminates."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        reset_redis_client()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            cooldown, step = loop.run_until_complete(
                SecurityStore.record_login_failure(ip, email)
            )
            queue.put({
                "success": True,
                "pid": os.getpid(),
                "cooldown": cooldown,
                "step": step,
            })
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        queue.put({"success": False, "pid": os.getpid(), "error": str(exc)})


def worker_record_n_failures(queue: mp.Queue, email: str, ip: str, count: int, redis_url: str, hmac_secret: str) -> None:
    """Worker: Records N consecutive login failures for a specific IP/email pair."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        reset_redis_client()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            last_cooldown = 0
            last_step = 0
            for _ in range(count):
                cooldown, step = loop.run_until_complete(
                    SecurityStore.record_login_failure(ip, email)
                )
                last_cooldown = cooldown
                last_step = step
            queue.put({
                "success": True,
                "pid": os.getpid(),
                "count": count,
                "cooldown": last_cooldown,
                "step": last_step,
            })
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        queue.put({"success": False, "pid": os.getpid(), "error": str(exc)})


def worker_evaluate_pre_auth(queue: mp.Queue, email: str, ip: str, redis_url: str, hmac_secret: str) -> None:
    """Worker: Evaluates pre-auth gate status in Valkey without prior process memory."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        reset_redis_client()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            allowed, status_code, wait_seconds, challenge_required = loop.run_until_complete(
                SecurityStore.evaluate_pre_auth(ip, email)
            )
            queue.put({
                "success": True,
                "pid": os.getpid(),
                "allowed": allowed,
                "status_code": status_code,
                "wait_seconds": wait_seconds,
                "challenge_required": challenge_required,
            })
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        queue.put({"success": False, "pid": os.getpid(), "error": str(exc)})


def worker_fill_ip_quota(queue: mp.Queue, ip: str, email: str, count: int, redis_url: str, hmac_secret: str) -> None:
    """Worker: Evaluates pre-auth N times to fill IP rate limit window."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        reset_redis_client()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            for _ in range(count):
                loop.run_until_complete(SecurityStore.evaluate_pre_auth(ip, email))
            queue.put({"success": True, "pid": os.getpid()})
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        queue.put({"success": False, "pid": os.getpid(), "error": str(exc)})


def worker_record_success(queue: mp.Queue, email: str, ip: str, redis_url: str, hmac_secret: str) -> None:
    """Worker: Records login success, clearing pair cooldown in Valkey."""
    try:
        os.environ["REDIS_URL"] = redis_url
        os.environ["SECURITY_HMAC_SECRET"] = hmac_secret
        reset_redis_client()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(SecurityStore.record_login_success(ip, email))
            queue.put({"success": True, "pid": os.getpid()})
        finally:
            loop.run_until_complete(close_redis_client())
            loop.close()
    except Exception as exc:
        queue.put({"success": False, "pid": os.getpid(), "error": str(exc)})


# ==============================================================================
# SAFE WORKER PROCESS LIFECYCLE CONTROLLER
# ==============================================================================

def run_worker_process(target_func, args, timeout: float = 10.0) -> dict:
    """
    Executes target_func inside an isolated OS process via multiprocessing spawn context.
    Guarantees bounded join, termination on hung process, and clean queue extraction.
    """
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()

    # Pass queue as first arg, followed by provided args
    full_args = (queue,) + tuple(args)
    proc = ctx.Process(target=target_func, args=full_args)
    proc.start()

    proc.join(timeout=timeout)
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=2.0)
        raise TimeoutError(f"Worker process {proc.pid} hung and was forcefully terminated.")

    assert proc.exitcode == 0, f"Worker process {proc.pid} exited with non-zero code {proc.exitcode}"

    try:
        res = queue.get(timeout=5.0)
    except Exception as exc:
        raise RuntimeError(f"Failed to read result from worker queue: {exc}")

    assert res.get("success") is True, f"Worker failed with error: {res.get('error')}"
    return res


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

@pytest.fixture(autouse=True)
def clean_valkey_keys():
    """Flushes Valkey authentication keys before and after every test."""
    os.environ["REDIS_URL"] = TEST_REDIS_URL
    os.environ["SECURITY_HMAC_SECRET"] = TEST_HMAC_SECRET
    reset_redis_client()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(SecurityStore.clear_all_security_keys())
    finally:
        loop.run_until_complete(close_redis_client())
        loop.close()

    yield

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(SecurityStore.clear_all_security_keys())
    finally:
        loop.run_until_complete(close_redis_client())
        loop.close()


# ==============================================================================
# TEST CASES: A THROUGH E
# ==============================================================================

def test_a_cross_process_failure_visibility():
    """
    Test A — Cross-process failure visibility:
    Worker 1 records a failed login for a test account and IP, then exits.
    Worker 2 evaluates pre-authentication for the same account/IP in a new process.
    Worker 2 must observe the shared state in Valkey (not inherited memory).
    """
    test_email = f"user_vis_{uuid.uuid4().hex[:8]}@example.com"
    test_ip = "198.51.100.51"

    # Step 1: Worker 1 records failure
    res_w1 = run_worker_process(
        worker_record_failure,
        (test_email, test_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w1["step"] == 0
    assert res_w1["cooldown"] == 0
    w1_pid = res_w1["pid"]

    # Step 2: Worker 2 evaluates pre-auth (completely fresh process)
    res_w2 = run_worker_process(
        worker_evaluate_pre_auth,
        (test_email, test_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    w2_pid = res_w2["pid"]

    assert w1_pid != w2_pid, "Workers must run in distinct OS processes"
    assert res_w2["allowed"] is True
    assert res_w2["status_code"] == "admitted"
    assert res_w2["challenge_required"] is False


def test_b_cross_process_ip_protection():
    """
    Test B — Cross-process IP protection:
    Worker 1 records enough pre-auth attempts (>= 10) to activate the IP velocity limit.
    Worker 2 attempts authentication from the same IP.
    Worker 2 must observe the shared IP restriction (status_code == 'ip_rate_limited').
    """
    test_ip = "198.51.100.77"
    dummy_email = f"ip_test_{uuid.uuid4().hex[:8]}@example.com"

    # Worker 1 evaluates pre-auth 10 times to consume the IP velocity quota
    res_w1 = run_worker_process(
        worker_fill_ip_quota,
        (test_ip, dummy_email, 10, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w1["success"] is True

    # Worker 2 now attempts pre-auth from the same IP
    res_w2 = run_worker_process(
        worker_evaluate_pre_auth,
        (f"different_user_{uuid.uuid4().hex[:8]}@example.com", test_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w2["allowed"] is False
    assert res_w2["status_code"] == "ip_rate_limited"
    assert res_w2["wait_seconds"] > 0


def test_c_cross_process_account_risk():
    """
    Test C — Cross-process account risk:
    Multiple workers record failures for the same test account from different IP addresses (distributed attack).
    A separate worker evaluates the account and must observe the combined distributed risk
    exceeding the threshold (ACCOUNT_DISTRIBUTED_THRESHOLD = 20), enforcing challenge_required = True.
    """
    victim_email = f"victim_dist_{uuid.uuid4().hex[:8]}@example.com"

    # Spawn 4 workers, each recording 5 failures from unique IPs (total 20 failures across 4 IPs)
    ctx = mp.get_context("spawn")
    workers = []
    queues = []

    for i in range(4):
        q = ctx.Queue()
        queues.append(q)
        ip = f"198.51.100.{100 + i}"
        p = ctx.Process(
            target=worker_record_n_failures,
            args=(q, victim_email, ip, 5, TEST_REDIS_URL, TEST_HMAC_SECRET)
        )
        workers.append(p)
        p.start()

    for p in workers:
        p.join(timeout=10.0)
        assert p.exitcode == 0

    for q in queues:
        res = q.get(timeout=5.0)
        assert res["success"] is True

    # Fresh Worker evaluates pre-auth from a new clean IP
    clean_ip = "198.51.100.200"
    res_eval = run_worker_process(
        worker_evaluate_pre_auth,
        (victim_email, clean_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    # Total failures >= 20, so challenge_required must be True!
    assert res_eval["allowed"] is True
    assert res_eval["challenge_required"] is True


def test_d_concurrent_atomic_updates():
    """
    Test D — Concurrent atomic updates:
    Multiple processes concurrently record failures against the same account.
    Verify that the final Redis counters and sorted-set state match the exact number
    of total writes without lost updates or race conditions.
    """
    shared_email = f"atomic_target_{uuid.uuid4().hex[:8]}@example.com"
    num_concurrent_workers = 6

    ctx = mp.get_context("spawn")
    processes = []
    queues = []

    for i in range(num_concurrent_workers):
        q = ctx.Queue()
        queues.append(q)
        ip = f"198.51.100.{120 + i}"
        p = ctx.Process(
            target=worker_record_failure,
            args=(q, shared_email, ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
        )
        processes.append(p)

    # Launch all workers concurrently
    for p in processes:
        p.start()

    # Collect outcomes
    for p in processes:
        p.join(timeout=10.0)
        assert p.exitcode == 0

    for q in queues:
        res = q.get(timeout=5.0)
        assert res["success"] is True

    # Verify atomic state directly in Valkey
    loop = asyncio.new_event_loop()
    try:
        from backend.app.core.auth.security_store import get_hmac_secrets, compute_account_hmac
        primary_sec, primary_id, _, _ = get_hmac_secrets()
        acct_hmac = compute_account_hmac(shared_email, primary_sec)
        risk_key = f"v1:auth:risk:{primary_id}:{acct_hmac}:failures"

        client = get_redis_client()
        total_risk_entries = loop.run_until_complete(client.zcard(risk_key))
        assert total_risk_entries == num_concurrent_workers, (
            f"Expected {num_concurrent_workers} atomic entries in ZSET, found {total_risk_entries}"
        )
    finally:
        loop.run_until_complete(close_redis_client())
        loop.close()


def test_e_worker_isolation():
    """
    Test E — Worker isolation:
    A cooldown created by Worker 1 must persist in Valkey after Worker 1 terminates.
    Worker 2 confirms cooldown; Worker 3 clears cooldown; Worker 4 confirms recovery.
    """
    test_email = f"isolation_{uuid.uuid4().hex[:8]}@example.com"
    test_ip = "198.51.100.88"

    # Worker 1 records 5 failures to trigger pair cooldown, then terminates
    res_w1 = run_worker_process(
        worker_record_n_failures,
        (test_email, test_ip, 5, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w1["cooldown"] > 0
    assert res_w1["step"] == 1

    # Worker 2: Fresh process inspects pre-auth
    res_w2 = run_worker_process(
        worker_evaluate_pre_auth,
        (test_email, test_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w2["allowed"] is False
    assert res_w2["status_code"] == "pair_cooldown_active"
    assert res_w2["wait_seconds"] > 0

    # Worker 3: Simulates successful login from that IP
    res_w3 = run_worker_process(
        worker_record_success,
        (test_email, test_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w3["success"] is True

    # Worker 4: Confirms cooldown was atomically cleared
    res_w4 = run_worker_process(
        worker_evaluate_pre_auth,
        (test_email, test_ip, TEST_REDIS_URL, TEST_HMAC_SECRET)
    )
    assert res_w4["allowed"] is True
    assert res_w4["status_code"] == "admitted"
    assert res_w4["wait_seconds"] == 0
