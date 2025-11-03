"""
Lightweight filesystem storage abstraction used for local Parquet files and uploads.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import shutil

from config import settings


class FileStore:
    """
    Simple wrapper that mirrors the subset of the previous cloud storage interface using the local filesystem.
    """

    def __init__(self, root_dir: str | None = None):
        self.root_dir = Path(root_dir or settings.data_root).expanduser().resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """
        Convert a logical storage key (e.g. sentiment/year=2024/data.parquet)
        into an absolute path under the configured root directory.
        """
        relative = Path(key.strip("/"))
        resolved = (self.root_dir / relative).resolve()
        if not str(resolved).startswith(str(self.root_dir)):
            raise ValueError("Storage key resolves outside of the storage root")
        return resolved

    def upload_file(self, local_path: str, key: str) -> bool:
        """
        Copy a local file into the storage root.
        """
        destination = self._resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_path, destination)
        return True

    def download_file(self, key: str, local_path: str) -> bool:
        """
        Copy a file from storage into the provided local path.
        """
        source = self._resolve(key)
        if not source.exists():
            return False
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, local_path)
        return True

    def file_exists(self, key: str) -> bool:
        """
        Check if a key exists in storage.
        """
        return self._resolve(key).exists()

    def list_files(self, prefix: str = "") -> List[str]:
        """
        Return a list of keys underneath the prefix.
        """
        base = self._resolve(prefix) if prefix else self.root_dir
        if not base.exists():
            return []

        files: List[str] = []
        for path in base.rglob("*"):
            if path.is_file():
                files.append(str(path.relative_to(self.root_dir)))
        return files

    def get_path(self, key: str) -> Path:
        """
        Return the absolute path for a given key.
        """
        return self._resolve(key)

    def ensure_directories(self, keys: Iterable[str]) -> None:
        """
        Ensure directories for a collection of keys exist.
        """
        for key in keys:
            self._resolve(key).parent.mkdir(parents=True, exist_ok=True)
