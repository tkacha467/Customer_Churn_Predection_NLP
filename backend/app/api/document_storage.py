"""
Secure Document Storage Module for Vraja Multi-Product Platform.
Manages tenant-isolated PDF documents (menus, brochures, catalogs) with signature validation,
atomic writes, path traversal prevention, and metadata tracking.
"""

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from Backend.app.core.database.storage import ReviewStore

# Allowed document categories
VALID_DOCUMENT_TYPES = {
    "food_menu",
    "dessert_menu",
    "drinks_menu",
    "brochure",
    "catalogue",
    "other",
}

# Strict 10 MiB upload limit per document
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024

# Tenant identifier validation pattern
TENANT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,100}$")

# Default relative documents root
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists() or (p / "Backend").exists()), Path(__file__).resolve().parents[4])
_candidate_docs = [
    _repo_root / "Project_Files" / "Data" / "documents",
    _repo_root / "data" / "documents",
]
DEFAULT_DOCUMENTS_DIR = next((p for p in _candidate_docs if p.exists()), _candidate_docs[0])


def sanitize_filename(filename: str) -> str:
    """Sanitizes user-provided filename for safe display and metadata storage."""
    base = os.path.basename(filename.strip())
    # Replace non-whitelisted characters with underscores
    clean = re.sub(r"[^a-zA-Z0-9_.\- ]", "_", base)
    return clean[:150] or "document.pdf"


def compute_sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hash of binary content."""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


class DocumentStorageService:
    """
    Manages tenant-isolated file storage on disk and coordinates with ReviewStore metadata.
    Designed with an injectable storage root to enable isolated automated testing.
    """

    def __init__(
        self,
        storage_root: str | Path | None = None,
        store: Optional[ReviewStore] = None
    ):
        raw_root = storage_root or os.getenv("DOCUMENTS_PATH", str(DEFAULT_DOCUMENTS_DIR))
        self.storage_root = Path(raw_root).expanduser().resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.store = store or ReviewStore()

    def _resolve_tenant_dir(self, tenant_id: str) -> Path:
        """Resolves tenant directory and asserts no path traversal escape."""
        clean_tenant = "default_business" if tenant_id in ("default_business", "nasta_ghar", "nasta-ghar") else tenant_id
        if not TENANT_ID_PATTERN.match(clean_tenant):
            raise ValueError(f"Invalid tenant identifier: '{tenant_id}'")

        target_dir = (self.storage_root / clean_tenant).resolve()
        if not target_dir.is_relative_to(self.storage_root):
            raise PermissionError("Path traversal violation: tenant directory escapes storage root.")
        return target_dir

    def save_document(
        self,
        tenant_id: str,
        content: bytes,
        original_filename: str,
        document_type: str = "food_menu",
        display_name: Optional[str] = None,
        is_published: bool = True
    ) -> Dict[str, Any]:
        """
        Validates, atomically writes, and registers a tenant PDF document.
        
        Security Notice:
        Validating the '%PDF-' header signature confirms standard PDF structure,
        but does not execute deep static analysis for embedded JavaScript.
        Documents must always be served with 'X-Content-Type-Options: nosniff'
        and strict 'Content-Type: application/pdf' to prevent browser script execution.
        """
        # 1. Size & signature validation
        if not content or len(content) < 10:
            raise ValueError("Document file is empty or corrupted.")

        if len(content) > MAX_DOCUMENT_SIZE_BYTES:
            raise ValueError(
                f"File size ({len(content)} bytes) exceeds the maximum allowed limit of {MAX_DOCUMENT_SIZE_BYTES} bytes (10 MiB)."
            )

        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid document signature: File must be a valid PDF document starting with '%PDF-'.")

        norm_type = document_type.strip().lower()
        if norm_type not in VALID_DOCUMENT_TYPES:
            norm_type = "other"

        # 2. Directory & filename preparation
        tenant_dir = self._resolve_tenant_dir(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)

        clean_original = sanitize_filename(original_filename)
        clean_display = (display_name or Path(clean_original).stem or "Menu").strip()[:150]

        # Server-generated unique ID and filename (never use original filename on disk)
        doc_id = str(uuid.uuid4())
        stored_filename = f"{doc_id}.pdf"
        final_file_path = (tenant_dir / stored_filename).resolve()

        if not final_file_path.is_relative_to(self.storage_root):
            raise PermissionError("Path traversal violation: Target file escapes storage root.")

        # 3. Atomic write with hash calculation
        temp_file_path = final_file_path.with_suffix(".tmp")
        try:
            temp_file_path.write_bytes(content)
            sha256_hash = compute_sha256_bytes(content)
            # Atomic swap
            os.replace(temp_file_path, final_file_path)
        except Exception:
            if temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except OSError:
                    pass
            raise

        # 4. Register metadata in ReviewStore
        doc_metadata = {
            "id": doc_id,
            "tenant_id": tenant_id,
            "document_type": norm_type,
            "display_name": clean_display,
            "original_filename": clean_original,
            "stored_filename": stored_filename,
            "file_size_bytes": len(content),
            "mime_type": "application/pdf",
            "sha256_hash": sha256_hash,
            "is_published": is_published,
        }

        try:
            record = self.store.add_tenant_document(doc_metadata)
            return record
        except Exception:
            # Clean up orphaned file on metadata insertion failure
            if final_file_path.exists():
                try:
                    final_file_path.unlink()
                except OSError:
                    pass
            raise

    def get_document_path(self, tenant_id: str, document_id: str) -> Optional[Path]:
        """
        Retrieves the verified filesystem Path of a tenant document.
        Enforces tenant ownership before returning the path.
        """
        record = self.store.get_tenant_document(tenant_id, document_id)
        if not record:
            return None

        tenant_dir = self._resolve_tenant_dir(tenant_id)
        file_path = (tenant_dir / record["stored_filename"]).resolve()

        if not file_path.is_relative_to(self.storage_root) or not file_path.is_file() or file_path.is_symlink():
            return None

        return file_path

    def get_public_document_path(self, document_id: str) -> Optional[Path]:
        """
        Retrieves filesystem path for a publicly published document.
        Returns None if document does not exist or is marked unpublished.
        """
        record = self.store.get_document_by_id(document_id)
        if not record or not record.get("is_published"):
            return None

        tenant_dir = self._resolve_tenant_dir(record["tenant_id"])
        file_path = (tenant_dir / record["stored_filename"]).resolve()

        if not file_path.is_relative_to(self.storage_root) or not file_path.is_file() or file_path.is_symlink():
            return None

        return file_path

    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """
        Deletes a tenant document from both disk and the metadata database.
        Enforces tenant ownership strictly.
        """
        record = self.store.get_tenant_document(tenant_id, document_id)
        if not record:
            return False

        tenant_dir = self._resolve_tenant_dir(tenant_id)
        file_path = (tenant_dir / record["stored_filename"]).resolve()

        # Delete database record first
        deleted_from_db = self.store.delete_tenant_document(tenant_id, document_id)

        # Remove file from disk
        if file_path.exists() and file_path.is_relative_to(self.storage_root) and not file_path.is_symlink():
            try:
                file_path.unlink()
            except OSError:
                pass

        return deleted_from_db

    def list_documents(self, tenant_id: str, published_only: bool = False) -> List[Dict[str, Any]]:
        """Lists document metadata belonging to a specific tenant."""
        return self.store.list_tenant_documents(tenant_id, published_only=published_only)


# ---------------------------------------------------------
# Singleton Factory for Dependency Injection
# ---------------------------------------------------------
_document_services: dict[str, DocumentStorageService] = {}


def get_document_storage() -> DocumentStorageService:
    from Backend.app.core.auth.auth import get_store
    docs_path = os.getenv("DOCUMENTS_PATH", "")
    db_path = os.getenv("REVIEW_DB_PATH", "")
    key = f"{docs_path}:{db_path}"
    if key not in _document_services:
        _document_services[key] = DocumentStorageService(
            storage_root=docs_path or None,
            store=get_store()
        )
    return _document_services[key]

