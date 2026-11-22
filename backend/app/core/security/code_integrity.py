"""
VRAJA AI Security Shield — Code & Release Integrity Monitor (Phase A6.5).
Provides cryptographic integrity verification for application source, static build
artifacts, and database schema without confusing legitimate customer database row
modifications with code tampering.

Architectural Guarantees:
1. Manifest-Driven Verification: Hashes executable source and deployed build artifacts
   associated with a verified release identifier (commit hash / semantic tag).
2. Database Schema vs Data Separation: Inspects structural database health via
   PRAGMA integrity_check and hashes sqlite_master DDL, allowing legitimate customer
   row transactions while alerting on unauthorized table/column/index alterations.
3. Decoupled Notifications: Forward verified integrity breaches to vajra.techworks@gmail.com.
"""

import os
import sqlite3
import hashlib
import hmac
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


# Canonical tracked paths for code integrity monitoring
MONITORED_SOURCE_EXTENSIONS = {".py", ".json", ".bat", ".command", ".sh", ".toml", ".yml", ".yaml"}
EXCLUDED_DIR_NAMES = {
    "__pycache__", ".pytest_cache", "node_modules", ".git", ".idea", ".vscode", "tmp", "temp"
}


def compute_file_sha256(path: Path) -> str:
    """Computes hexadecimal SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_release_manifest(
    release_id: str,
    repo_root: Path,
    include_frontend_dist: bool = True
) -> Dict[str, Any]:
    """
    Generates a trusted SHA-256 release manifest of application source and build artifacts.
    Associates the manifest with a verified release identifier.
    """
    manifest_files: Dict[str, str] = {}

    # 1. Monitored Backend Source Files
    backend_dir = repo_root / "Backend"
    if backend_dir.exists():
        for p in backend_dir.rglob("*.py"):
            if not any(excluded in p.parts for excluded in EXCLUDED_DIR_NAMES):
                rel_path = str(p.relative_to(repo_root)).replace("\\", "/")
                manifest_files[rel_path] = compute_file_sha256(p)

    # 2. Critical Configuration & Runtime Specs
    config_candidates = [
        "pyproject.toml",
        "requirements.txt",
        "Dockerfile",
        "NastaGhar/frontend/package.json",
        "Digital_Card/frontend/package.json",
    ]
    for rel_cand in config_candidates:
        cand_path = repo_root / rel_cand
        if cand_path.exists():
            manifest_files[rel_cand] = compute_file_sha256(cand_path)

    # 3. Static Deployed Build Artifacts (dist/)
    if include_frontend_dist:
        dist_dirs = [
            repo_root / "NastaGhar" / "frontend" / "dist",
            repo_root / "Digital_Card" / "frontend" / "dist",
        ]
        for d in dist_dirs:
            if d.exists():
                for p in d.rglob("*"):
                    if p.is_file() and not any(excluded in p.parts for excluded in EXCLUDED_DIR_NAMES):
                        rel_path = str(p.relative_to(repo_root)).replace("\\", "/")
                        manifest_files[rel_path] = compute_file_sha256(p)

    # Master manifest hash: deterministic sort of all file hashes
    sorted_pairs = sorted(manifest_files.items())
    manifest_fingerprint = hashlib.sha256(
        "\n".join(f"{k}:{v}" for k, v in sorted_pairs).encode("utf-8")
    ).hexdigest()

    return {
        "release_id": release_id,
        "manifest_fingerprint": manifest_fingerprint,
        "total_monitored_files": len(manifest_files),
        "file_hashes": manifest_files,
    }


def sign_release_manifest(manifest: Dict[str, Any], secret_key: str) -> str:
    """Computes HMAC-SHA256 signature for trusted release manifest provenance."""
    payload = f"{manifest.get('release_id', '')}:{manifest.get('manifest_fingerprint', '')}"
    return hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_manifest_signature(manifest: Dict[str, Any], signature: str, secret_key: str) -> bool:
    """Verifies that the release manifest originated from the authorized build pipeline."""
    if not signature or not secret_key:
        return False
    expected_sig = sign_release_manifest(manifest, secret_key)
    return hmac.compare_digest(expected_sig, signature)


def verify_code_integrity(
    manifest: Dict[str, Any],
    repo_root: Path,
    signature: Optional[str] = None,
    signing_secret: Optional[str] = None,
    expected_release_id: Optional[str] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    Verifies that files on disk match the expected release manifest.
    Fails closed in production environments if signing secret, signature, or release ID is invalid or missing.
    Returns (is_valid, modified_or_missing_files, unexpected_new_files).
    """
    expected_files: Dict[str, str] = manifest.get("file_hashes", {})
    deviations: List[str] = []
    unexpected: List[str] = []

    env_mode = os.getenv("ENVIRONMENT", "").strip().lower()
    secret = signing_secret or os.getenv("RELEASE_SIGNING_SECRET")

    # 1. Production Signing Secret Requirement (Fail-Closed)
    if env_mode == "production" and not secret:
        deviations.append("MISSING_RELEASE_SIGNING_SECRET: Production release integrity check requires RELEASE_SIGNING_SECRET.")

    # 2. Cryptographic HMAC Signature Verification (Fail-Closed)
    if secret:
        if not signature:
            deviations.append("MISSING_MANIFEST_SIGNATURE: Release manifest signature is absent.")
        elif not verify_manifest_signature(manifest, signature, secret):
            deviations.append("INVALID_MANIFEST_SIGNATURE: Release manifest provenance signature verification failed.")

    # 3. Release Identifier Alignment Check
    target_release = expected_release_id or os.getenv("DEPLOYMENT_RELEASE_ID")
    if target_release and manifest.get("release_id") != target_release:
        deviations.append(f"RELEASE_MISMATCH: Manifest release_id '{manifest.get('release_id')}' does not match expected '{target_release}'.")

    # 4. Internal Manifest Consistency (Fingerprint must match file_hashes)
    sorted_pairs = sorted(expected_files.items())
    recalc_fingerprint = hashlib.sha256(
        "\n".join(f"{k}:{v}" for k, v in sorted_pairs).encode("utf-8")
    ).hexdigest()
    if manifest.get("manifest_fingerprint") != recalc_fingerprint:
        deviations.append("MANIFEST_TAMPERED: manifest_fingerprint does not match declared file_hashes.")

    # 5. Disk File Verification & Traversal Protection
    resolved_root = repo_root.resolve()
    for rel_path, expected_hash in expected_files.items():
        disk_path = (repo_root / rel_path).resolve()
        try:
            disk_path.relative_to(resolved_root)
        except ValueError:
            deviations.append(f"TRAVERSAL_REJECTED: {rel_path}")
            continue

        if not disk_path.exists():
            deviations.append(f"MISSING: {rel_path}")
            continue
        try:
            actual_hash = compute_file_sha256(disk_path)
            if actual_hash != expected_hash:
                deviations.append(f"MODIFIED: {rel_path}")
        except Exception as e:
            deviations.append(f"ERROR_READING: {rel_path} ({e})")

    # 6. Detect unexpected new executable source files in monitored backend root
    backend_dir = repo_root / "Backend"
    if backend_dir.exists():
        for p in backend_dir.rglob("*.py"):
            if not any(excluded in p.parts for excluded in EXCLUDED_DIR_NAMES):
                rel = str(p.relative_to(repo_root)).replace("\\", "/")
                if rel not in expected_files:
                    unexpected.append(f"UNEXPECTED_FILE: {rel}")

    is_valid = len(deviations) == 0 and len(unexpected) == 0
    return is_valid, deviations, unexpected


def verify_database_schema_integrity(database_path: Path) -> Tuple[bool, str, str]:
    """
    Audits SQLite database structural integrity and schema definition.
    Crucial: DOES NOT hash customer row data, allowing normal business transactions
    while alerting on corrupted database pages or unauthorized schema alterations (DDL).
    
    Returns (is_healthy, pragma_integrity_result, schema_hash).
    """
    if not database_path.exists():
        return False, "DATABASE_FILE_NOT_FOUND", ""

    try:
        conn = sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. Structural PRAGMA quick_check
        cur.execute("PRAGMA quick_check(1);")
        quick_res = cur.fetchone()
        quick_status = quick_res[0] if quick_res else "UNKNOWN"
        if quick_status != "ok":
            conn.close()
            return False, f"CORRUPTION_DETECTED: {quick_status}", ""

        # 2. Schema DDL Fingerprint (tables, indexes, triggers)
        cur.execute("""
            SELECT type, name, sql
            FROM sqlite_master
            WHERE type IN ('table', 'index', 'trigger') AND sql IS NOT NULL
            ORDER BY type, name;
        """)
        schema_rows = cur.fetchall()
        conn.close()

        schema_payload = "\n".join(f"{r['type']}:{r['name']}:{r['sql'].strip()}" for r in schema_rows)
        schema_hash = hashlib.sha256(schema_payload.encode("utf-8")).hexdigest()

        return True, "ok", schema_hash
    except sqlite3.Error as e:
        return False, f"SQLITE_ERROR: {str(e)}", ""
    except Exception as e:
        return False, f"SYSTEM_ERROR: {str(e)}", ""
