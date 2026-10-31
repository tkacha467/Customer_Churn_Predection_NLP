#!/usr/bin/env python3
"""Build and verify a clean release with one backend and separate product frontends."""

import argparse
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ROOT_DIR = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists() or (p / "Backend").exists()), Path(__file__).resolve().parents[2])
VERSION = "2.0.0-staging"
OUTPUT_DIR = ROOT_DIR / "Project_Files" / "Releases" if (ROOT_DIR / "Project_Files" / "Releases").exists() else ROOT_DIR / "releases"
PRODUCTS = ("NastaGhar", "Digital_Card")
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "tests", "data", "releases", "dist", "backups", "uploads", "documents", ".cache", ".vite"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".sqlite", ".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".db", ".log", ".tmp", ".bak", ".pem", ".key", ".p12", ".pfx")


def ignore_release_items(directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        path = Path(directory) / name
        lower = name.lower()
        if name in EXCLUDED_DIRS or name.startswith(".venv"):
            ignored.add(name)
        elif lower == ".env" or (lower.startswith(".env.") and not lower.endswith(".example")):
            ignored.add(name)
        elif path.is_file() and lower.endswith(EXCLUDED_SUFFIXES):
            ignored.add(name)
    return ignored


def compute_sha256(filepath: Path) -> str:
    digest = hashlib.sha256()
    with filepath.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_frontend(product: str) -> None:
    frontend = ROOT_DIR / product / "frontend"
    npm_cmd = shutil.which("npm") or ("npm.cmd" if sys.platform == "win32" else "npm")
    result = subprocess.run([npm_cmd, "--prefix", str(frontend), "run", "build"], text=True, capture_output=True, shell=(sys.platform == "win32"))
    if result.returncode:
        raise RuntimeError(f"{product} frontend build failed:\n{result.stdout}\n{result.stderr}")


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=ignore_release_items)


def build_release_package(output_tar: Path | None = None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target_tar = (output_tar or OUTPUT_DIR / f"vraja-{VERSION}.tar.gz").resolve()
    if target_tar.exists() or target_tar.with_name(target_tar.name + ".sha256").exists():
        raise FileExistsError(f"Refusing to overwrite an existing release artifact: {target_tar}")

    for product in PRODUCTS[:2]:
        build_frontend(product)

    release_name = f"vraja-{VERSION}"
    timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with tempfile.TemporaryDirectory(prefix="vraja_pkg_") as tmp:
        stage = Path(tmp) / release_name
        stage.mkdir()
        copy_tree(ROOT_DIR / "Backend", stage / "Backend")
        for product in PRODUCTS:
            copy_tree(ROOT_DIR / product, stage / product)
        for product in PRODUCTS[:2]:
            shutil.copytree(ROOT_DIR / product / "frontend" / "dist", stage / product / "frontend" / "dist")
        (stage / "scripts").mkdir()
        scripts_source = ROOT_DIR / "Project_Files" / "Scripts" if (ROOT_DIR / "Project_Files" / "Scripts").exists() else ROOT_DIR / "scripts"
        for script_name in ("backup_restore.py", "create_tenant_owner.py"):
            shutil.copy2(scripts_source / script_name, stage / "scripts" / script_name)
        for name in ("pyproject.toml", "requirements.txt", "staging.env.example", ".env.example", "Dockerfile", ".dockerignore", "README.md"):
            source = ROOT_DIR / name
            if source.is_file():
                shutil.copy2(source, stage / name)

        files = []
        for path in sorted(stage.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(stage).as_posix()
            files.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": compute_sha256(path)})

        manifest = {
            "name": "vraja",
            "version": VERSION,
            "created_at_iso": timestamp_iso,
            "runtime": {"python": ">=3.11", "node": ">=20.0"},
            "backend_entrypoint": "Backend.app.main:app",
            "database": {"engine": "sqlite3", "wal_mode": True, "auto_migration": True},
            "frontends": [f"{product}/frontend/dist" for product in PRODUCTS[:2]],
            "health_check": {"endpoint": "/healthz", "expected_status": 200},
            "files_count": len(files),
            "files": files,
        }
        (stage / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        lines = [f"# Vraja Release Artifact — {VERSION}", "", f"Created: `{timestamp_iso}`", "", "## Start the shared backend", "", "```bash", "python -m venv .venv && source .venv/bin/activate", "pip install -r requirements.txt", "uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000", "```", "", "## Product frontends", "", "Build and run each Vite app from its product `frontend/` directory. Both use the shared backend and same-origin `/api` paths by default.", "", "## File checksums", "", "| Path | Bytes | SHA-256 |", "|---|---:|---|"]
        lines.extend(f"| `{item['path']}` | {item['size_bytes']} | `{item['sha256']}` |" for item in files)
        (stage / "RELEASE_MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        target_tar.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(target_tar, "w:gz") as archive:
            archive.add(stage, arcname=release_name)
    target_tar.with_name(target_tar.name + ".sha256").write_text(f"{compute_sha256(target_tar)}  {target_tar.name}\n", encoding="utf-8")
    return target_tar


def verify_release_package(tar_path: Path) -> bool:
    tar_path = tar_path.resolve()
    if not tar_path.is_file():
        return False
    checksum_file = tar_path.with_name(tar_path.name + ".sha256")
    if not checksum_file.is_file() or checksum_file.read_text(encoding="utf-8").strip() != f"{compute_sha256(tar_path)}  {tar_path.name}":
        return False
    with tempfile.TemporaryDirectory(prefix="vraja_verify_") as tmp:
        with tarfile.open(tar_path, "r:gz") as archive:
            members = archive.getmembers()
            for member in members:
                rel = Path(member.name)
                lower = member.name.lower()
                if rel.is_absolute() or ".." in rel.parts or not (member.isdir() or member.isfile()):
                    return False
                if any(part in (EXCLUDED_DIRS - {"dist"}) for part in rel.parts):
                    return False
                name = rel.name.lower()
                if name.endswith(EXCLUDED_SUFFIXES):
                    return False
                if name == ".env" or (name.startswith(".env.") and not name.endswith(".example")):
                    return False
            if "filter" in inspect.signature(tarfile.TarFile.extractall).parameters:
                archive.extractall(tmp, members=members, filter="data")
            else:
                archive.extractall(tmp, members=members)
        roots = [p for p in Path(tmp).iterdir() if p.is_dir()]
        if len(roots) != 1:
            return False
        root = roots[0]
        manifest_path = root / "RELEASE_MANIFEST.json"
        if not manifest_path.is_file():
            return False
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("files_count") != len(manifest.get("files", [])):
            return False
        listed = {item["path"] for item in manifest["files"]}
        archive_files = {Path(member.name).relative_to(roots[0].name).as_posix() for member in members if member.isfile() and Path(member.name).name not in {"RELEASE_MANIFEST.json", "RELEASE_MANIFEST.md"}}
        if archive_files != listed:
            return False
        for item in manifest["files"]:
            path = root / item["path"]
            lower = path.name.lower()
            if not path.is_file() or compute_sha256(path) != item["sha256"]:
                return False
            if lower.endswith((".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".db", ".pyc", ".pyo", ".log")):
                return False
            if lower == ".env" or (lower.startswith(".env.") and not lower.endswith(".example")):
                return False
        for product in PRODUCTS[:2]:
            if not (root / product / "frontend" / "dist" / "index.html").is_file():
                return False
        result = subprocess.run([sys.executable, "-m", "compileall", "-q", str(root / "Backend")], capture_output=True)
        return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write a new archive to this path (existing files are never overwritten)")
    parser.add_argument("--verify", help="Verify an existing archive")
    args = parser.parse_args()
    if args.verify:
        ok = verify_release_package(Path(args.verify))
    else:
        archive = build_release_package(Path(args.output) if args.output else None)
        print(f"Archive: {archive}\nSHA-256: {compute_sha256(archive)}")
        ok = verify_release_package(archive)
    if not ok:
        raise SystemExit(1)
    print("Release archive verified.")


if __name__ == "__main__":
    main()
