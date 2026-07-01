"""Repositories for albums, tags, notes, and dashboard data."""

from __future__ import annotations

from sqlalchemy import func

from app.extensions import db
from app.infrastructure.database.models import (
    ActivityLog,
    Album,
    AlbumPhoto,
    Photo,
    PhotoNote,
    PhotoNoteVersion,
    ProcessingQueue,
    Tag,
)


class CatalogRepository:
    """Read/write helpers for user-owned catalog entities."""

    def albums(self, owner_id: int) -> list[Album]:
        return Album.query.filter_by(owner_id=owner_id).order_by(Album.name.asc()).all()

    def album_by_id(self, owner_id: int, album_id: int) -> Album | None:
        return Album.query.filter_by(owner_id=owner_id, id=album_id).first()

    def tags(self, owner_id: int) -> list[Tag]:
        return Tag.query.filter_by(owner_id=owner_id).order_by(Tag.name.asc()).all()

    def note_for_photo(self, owner_id: int, photo_id: int) -> PhotoNote | None:
        return PhotoNote.query.filter_by(owner_id=owner_id, photo_id=photo_id).first()

    def save_note_version(self, note: PhotoNote) -> None:
        db.session.add(
            PhotoNoteVersion(
                note_id=note.id,
                owner_id=note.owner_id,
                title=note.title,
                description=note.description,
                personal_notes=note.personal_notes,
                ai_notes=note.ai_notes,
                version=note.version,
            )
        )

    def recent_activity(self, owner_id: int, limit: int = 12) -> list[ActivityLog]:
        return (
            ActivityLog.query.filter_by(owner_id=owner_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def dashboard_stats(self, owner_id: int) -> dict[str, int]:
        total_photos = Photo.query.filter_by(owner_id=owner_id, deleted=False).count()
        favorites = Photo.query.filter_by(owner_id=owner_id, favorite=True, deleted=False).count()
        albums = Album.query.filter_by(owner_id=owner_id).count()
        storage = (
            db.session.query(func.sum(Photo.file_size))
            .filter(Photo.owner_id == owner_id, Photo.deleted.is_(False))
            .scalar()
            or 0
        )
        queue = ProcessingQueue.query.filter_by(owner_id=owner_id, status="pending").count()


        return {
            "total_photos": int(total_photos),
            "favorites": int(favorites),
            "albums": int(albums),
            "storage_bytes": int(storage),
            "pending_queue": int(queue),
        }

    def photo_count_in_album(self, owner_id: int, album_id: int) -> int:
        return AlbumPhoto.query.filter_by(owner_id=owner_id, album_id=album_id).count()

