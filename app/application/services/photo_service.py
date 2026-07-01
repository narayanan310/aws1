"""Photo catalog use cases."""

from __future__ import annotations

from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage

from app.application.dto.photo_dto import PhotoUploadResult, SearchFilters
from app.application.services.audit_service import ActivityService, AuditService
from app.domain.entities.enums import ActivityType, QueueTaskType
from app.domain.exceptions.domain_exceptions import AuthorizationError, NotFoundError, ValidationError
from app.extensions import db
from app.infrastructure.database.models import Favorite, Photo, Trash, User
from app.infrastructure.repositories.photo_repository import PhotoRepository
from app.infrastructure.repositories.queue_repository import QueueRepository
from app.infrastructure.security.upload_validator import UploadValidator
from app.infrastructure.storage.local_storage import LocalStorageService
from app.utils.files import sha256_file


class PhotoService:
    """User-owned photo operations."""

    def __init__(self) -> None:
        self.photos = PhotoRepository()
        self.storage = LocalStorageService()
        self.queue = QueueRepository()
        self.audit = AuditService()
        self.activity = ActivityService()

    def upload_many(self, owner: User, uploads: list[FileStorage], metadata: dict | None = None) -> list[PhotoUploadResult]:
        results: list[PhotoUploadResult] = []
        validator = UploadValidator(
            current_app.config["ALLOWED_EXTENSIONS"], current_app.config["ALLOWED_MIME_TYPES"]
        )
        for upload in uploads:
            image_format, width, height = validator.validate(upload)
            stored_filename, original_path = self.storage.save_original(owner.uuid, upload)
            sha256 = sha256_file(original_path)
            photo = Photo(
                owner_id=owner.id,
                original_filename=upload.filename or stored_filename,
                stored_filename=stored_filename,
                original_path=str(original_path),
                sha256=sha256,
                checksum=sha256,
                width=width,
                height=height,
                format=image_format,
                mime_type=upload.mimetype,
                file_size=original_path.stat().st_size,
                processing_status="pending"
            )
            db.session.add(photo)
            db.session.flush()
            
            self.queue.enqueue(owner.id, photo.id, QueueTaskType.IMAGE_PROCESSING.value)
            
            self.activity.record(
                owner_id=owner.id,
                photo_id=photo.id,
                action=ActivityType.UPLOAD.value,
                message=f"Uploaded {photo.original_filename}",
            )
            self.audit.record(
                actor_id=owner.id,
                action="photo.upload",
                resource_type="photo",
                resource_id=photo.uuid,
            )
            results.append(
                PhotoUploadResult(
                    photo_id=photo.id,
                    photo_uuid=photo.uuid,
                    original_filename=photo.original_filename,
                    processing_status=photo.processing_status,
                )
            )
        db.session.commit()
        return results

    def list_photos(self, owner_id: int, filters: SearchFilters):
        return self.photos.list_owned(
            owner_id,
            search=filters.query,
            sort=filters.sort,
            favorite=filters.favorite,
            archived=filters.archived,
            deleted=filters.deleted,
            file_format=filters.file_format,
            page=filters.page,
            per_page=filters.per_page,
        )

    def get_owned_or_404(self, owner_id: int, photo_id: int) -> Photo:
        photo = self.photos.get_owned(owner_id, photo_id)
        if not photo:
            raise NotFoundError("Photo not found.")
        return photo

    def toggle_favorite(self, owner_id: int, photo_id: int) -> Photo:
        photo = self.get_owned_or_404(owner_id, photo_id)
        photo.favorite = not photo.favorite
        existing = Favorite.query.filter_by(owner_id=owner_id, photo_id=photo.id).first()
        if photo.favorite and not existing:
            db.session.add(Favorite(owner_id=owner_id, photo_id=photo.id))
        if not photo.favorite and existing:
            db.session.delete(existing)
        self.activity.record(
            owner_id=owner_id,
            photo_id=photo.id,
            action=ActivityType.FAVORITE.value,
            message=f"{'Favorited' if photo.favorite else 'Unfavorited'} {photo.original_filename}",
        )
        db.session.commit()
        return photo

    def archive(self, owner_id: int, photo_id: int, archived: bool = True) -> Photo:
        photo = self.get_owned_or_404(owner_id, photo_id)
        photo.archived = archived
        self.activity.record(
            owner_id=owner_id,
            photo_id=photo.id,
            action=ActivityType.ARCHIVE.value,
            message=f"{'Archived' if archived else 'Restored from archive'} {photo.original_filename}",
        )
        db.session.commit()
        return photo

    def soft_delete(self, owner_id: int, photo_id: int) -> Photo:
        photo = self.get_owned_or_404(owner_id, photo_id)
        photo.deleted = True
        db.session.add(Trash(owner_id=owner_id, photo_id=photo.id))
        self.activity.record(
            owner_id=owner_id,
            photo_id=photo.id,
            action=ActivityType.DELETE.value,
            message=f"Moved {photo.original_filename} to trash",
        )
        db.session.commit()
        return photo

    def restore(self, owner_id: int, photo_id: int) -> Photo:
        photo = self.get_owned_or_404(owner_id, photo_id)
        photo.deleted = False
        trash = Trash.query.filter_by(owner_id=owner_id, photo_id=photo.id).first()
        if trash:
            db.session.delete(trash)
        self.activity.record(
            owner_id=owner_id,
            photo_id=photo.id,
            action=ActivityType.RESTORE.value,
            message=f"Restored {photo.original_filename}",
        )
        db.session.commit()
        return photo

    def delete_forever(self, owner_id: int, photo_id: int) -> None:
        photo = self.get_owned_or_404(owner_id, photo_id)
        paths = [photo.original_path, photo.preview_path, photo.thumbnail_path, photo.compressed_path]
        self.storage.remove_paths(paths)
        db.session.delete(photo)
        self.audit.record(
            actor_id=owner_id,
            action="photo.delete_forever",
            resource_type="photo",
            resource_id=photo.uuid,
        )
        db.session.commit()

    def authorized_file_path(self, owner_id: int, photo_id: int, variant: str) -> Path:
        photo = self.get_owned_or_404(owner_id, photo_id)
        mapping = {
            "original": photo.original_path,
            "preview": photo.preview_path or photo.original_path,
            "thumbnail": photo.thumbnail_path or photo.preview_path or photo.original_path,
            "compressed": photo.compressed_path or photo.preview_path or photo.original_path,
        }
        value = mapping.get(variant)
        if not value:
            raise AuthorizationError("Variant is not available.")
        return Path(value)

