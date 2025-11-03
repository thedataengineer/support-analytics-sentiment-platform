from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import shutil

from config import settings

logger = logging.getLogger(__name__)


class UploadService:
    """
    Lightweight upload service that stores files on the local filesystem.
    """

    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = Path(upload_dir or settings.upload_dir).expanduser().resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("UploadService initialized with directory: %s", self.upload_dir)

    def save_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Persist uploaded content to disk and return metadata.
        """
        safe_name = Path(filename).name
        unique_id = uuid.uuid4()
        timestamp = datetime.utcnow()
        relative_path = Path(
            timestamp.strftime("%Y/%m/%d")
        ) / f"{unique_id}/{safe_name}"

        destination = self.upload_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(file_bytes)

        logger.info("Stored upload %s at %s", filename, destination)
        return {
            "path": str(destination),
            "relative_path": str(relative_path),
            "size": len(file_bytes),
            "stored_at": timestamp.isoformat(),
        }

    def get_file_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a stored file.
        """
        file_path = Path(path)
        if not file_path.exists():
            return None

        stats = file_path.stat()
        return {
            "path": str(file_path),
            "size": stats.st_size,
            "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        }

    def delete_file(self, path: str) -> bool:
        """
        Delete a stored file or directory tree.
        """
        file_path = Path(path)
        if not file_path.exists():
            return False

        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()

        logger.info("Deleted stored file: %s", file_path)
        return True


# Global instance
upload_service = UploadService()
