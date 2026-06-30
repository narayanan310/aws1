"""Local storage adapter with AWS S3-compatible service boundaries."""

from __future__ import annotations

import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class LocalStorageService:
    """Store user-owned image derivatives under isolated directories."""

    def user_root(self, user_uuid: str) -> Path:
        return current_app.config["UPLOAD_ROOT"] / "users" / user_uuid

    def ensure_user_dirs(self, user_uuid: str) -> dict[str, Path]:
        root = self.user_root(user_uuid)
        paths = {
            "original": root / "original",
            "preview": root / "preview",
            "thumbnail": root / "thumbnail",
            "compressed": root / "compressed",
        }
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        return paths

    def save_original(self, user_uuid: str, upload: FileStorage) -> tuple[str, Path]:
        dirs = self.ensure_user_dirs(user_uuid)
        safe_name = secure_filename(upload.filename or "upload")
        suffix = Path(safe_name).suffix.lower()
        stored_name = f"{uuid.uuid4()}{suffix}"
        destination = dirs["original"] / stored_name
        upload.save(destination)
        return stored_name, destination

    def derivative_path(self, user_uuid: str, kind: str, stem: str, suffix: str = ".jpg") -> Path:
        dirs = self.ensure_user_dirs(user_uuid)
        return dirs[kind] / f"{stem}_{kind}{suffix}"

    def remove_paths(self, paths: list[str | None]) -> None:
        for value in paths:
            if not value:
                continue
            path = Path(value)
            if path.exists():
                path.unlink()

    def public_storage_path(self, path: Path) -> str:
        """Return a relative path for authorized Flask serving routes."""

        return str(path.relative_to(current_app.config["UPLOAD_ROOT"]))

