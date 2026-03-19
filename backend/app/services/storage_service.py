"""Abstract file storage service (local or S3-compatible)."""

import os
import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    File storage abstraction.

    Supports:
    - Local filesystem (default)
    - S3-compatible storage (optional, TODO in Phase 6)
    """

    def __init__(self) -> None:
        self.storage_type = settings.storage_type
        self.local_path = Path(settings.storage_local_path)
        self._ensure_base_dir()

    def _ensure_base_dir(self) -> None:
        """Create base storage directory if it does not exist."""
        if self.storage_type == "local":
            self.local_path.mkdir(parents=True, exist_ok=True)

    def save(self, file_content: bytes, subpath: str) -> str:
        """
        Save file content and return the storage path/identifier.

        subpath: e.g. "user_123/doc_456/file.pdf"
        """
        if self.storage_type == "local":
            full_path = self.local_path / subpath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(file_content)
            return str(full_path)
        # S3: TODO
        raise NotImplementedError("S3 storage not implemented yet")

    def load(self, storage_path: str) -> bytes:
        """Load file content by storage path."""
        if self.storage_type == "local":
            path = Path(storage_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {storage_path}")
            return path.read_bytes()
        raise NotImplementedError("S3 storage not implemented yet")

    def delete(self, storage_path: str) -> bool:
        """Delete file by storage path."""
        try:
            if self.storage_type == "local":
                path = Path(storage_path)
                if path.exists():
                    path.unlink()
                    return True
                return False
            return False
        except Exception as e:
            logger.warning("Storage delete failed: %s", e)
            return False

    def generate_path(self, user_id: str, document_id: str, filename: str) -> str:
        """Generate a unique storage subpath for an uploaded document."""
        ext = Path(filename).suffix or ".pdf"
        return f"{user_id}/{document_id}/{uuid4().hex}{ext}"
