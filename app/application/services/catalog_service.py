"""Albums, tags, notes, and dashboard use cases."""

from __future__ import annotations

from app.application.services.audit_service import ActivityService
from app.domain.entities.enums import ActivityType
from app.domain.exceptions.domain_exceptions import NotFoundError, ValidationError
from app.extensions import db
from app.infrastructure.database.models import Album, AlbumPhoto, PhotoNote, PhotoTag, Tag
from app.infrastructure.repositories.catalog_repository import CatalogRepository
from app.infrastructure.repositories.photo_repository import PhotoRepository


class AlbumService:
    """User-owned album operations, including nested albums."""

    def __init__(self) -> None:
        self.catalog = CatalogRepository()
        self.photos = PhotoRepository()

    def create(self, owner_id: int, name: str, description: str = "", parent_id: int | None = None) -> Album:
        if not name.strip():
            raise ValidationError("Album name is required.")
        if parent_id and not self.catalog.album_by_id(owner_id, parent_id):
            raise NotFoundError("Parent album not found.")
        album = Album(owner_id=owner_id, name=name.strip(), description=description.strip(), parent_id=parent_id)
        db.session.add(album)
        db.session.commit()
        return album

    def add_photo(self, owner_id: int, album_id: int, photo_id: int) -> None:
        album = self.catalog.album_by_id(owner_id, album_id)
        photo = self.photos.get_owned(owner_id, photo_id)
        if not album or not photo:
            raise NotFoundError("Album or photo not found.")
        existing = AlbumPhoto.query.filter_by(owner_id=owner_id, album_id=album_id, photo_id=photo_id).first()
        if not existing:
            db.session.add(AlbumPhoto(owner_id=owner_id, album_id=album_id, photo_id=photo_id))
            db.session.commit()


class TagService:
    """Manual and AI tag operations."""

    def ensure_tag(self, owner_id: int, name: str) -> Tag:
        normalized = name.strip().lower()
        if not normalized:
            raise ValidationError("Tag name is required.")
        tag = Tag.query.filter_by(owner_id=owner_id, normalized_name=normalized).first()
        if tag:
            return tag
        tag = Tag(owner_id=owner_id, name=name.strip(), normalized_name=normalized)
        db.session.add(tag)
        db.session.flush()
        return tag

    def tag_photo(self, owner_id: int, photo_id: int, names: list[str]) -> list[Tag]:
        photo = PhotoRepository().get_owned(owner_id, photo_id)
        if not photo:
            raise NotFoundError("Photo not found.")
        tags: list[Tag] = []
        for name in names:
            tag = self.ensure_tag(owner_id, name)
            existing = PhotoTag.query.filter_by(owner_id=owner_id, photo_id=photo_id, tag_id=tag.id).first()
            if not existing:
                db.session.add(
                    PhotoTag(
                        owner_id=owner_id,
                        photo_id=photo_id,
                        tag_id=tag.id,
                    )
                )
            tags.append(tag)
        db.session.commit()
        return tags

    def rename(self, owner_id: int, tag_id: int, new_name: str) -> Tag:
        tag = Tag.query.filter_by(owner_id=owner_id, id=tag_id).first()
        if not tag:
            raise NotFoundError("Tag not found.")
        tag.name = new_name.strip()
        tag.normalized_name = new_name.strip().lower()
        db.session.commit()
        return tag

    def set_tags(self, owner_id: int, photo_id: int, names: list[str]) -> list[Tag]:
        """Replace all tags for a photo with a new set of tags (atomic replace)."""
        # Delete existing tags for this photo
        PhotoTag.query.filter_by(owner_id=owner_id, photo_id=photo_id).delete()
        db.session.flush()
        # Add the new tags
        tags: list[Tag] = []
        for name in names:
            name = name.strip()
            if not name:
                continue
            tag = self.ensure_tag(owner_id, name)
            db.session.add(PhotoTag(owner_id=owner_id, photo_id=photo_id, tag_id=tag.id))
            tags.append(tag)
        db.session.commit()
        return tags



class NoteService:
    """Photo note operations with version history."""

    def __init__(self) -> None:
        self.catalog = CatalogRepository()
        self.photos = PhotoRepository()
        self.activity = ActivityService()

    def upsert(
        self,
        owner_id: int,
        photo_id: int,
        *,
        title: str = "",
        description: str = "",
        personal_notes: str = "",
    ) -> PhotoNote:
        if not self.photos.get_owned(owner_id, photo_id):
            raise NotFoundError("Photo not found.")
        note = self.catalog.note_for_photo(owner_id, photo_id)
        if note:
            self.catalog.save_note_version(note)
            note.version += 1
        else:
            note = PhotoNote(owner_id=owner_id, photo_id=photo_id)
            db.session.add(note)
        note.title = title.strip()
        note.description = description.strip()
        note.personal_notes = personal_notes.strip()

        self.activity.record(
            owner_id=owner_id,
            photo_id=photo_id,
            action=ActivityType.EDIT_NOTES.value,
            message="Updated photo notes",
        )
        db.session.commit()
        return note


class DashboardService:
    """Dashboard aggregation use case."""

    def __init__(self) -> None:
        self.catalog = CatalogRepository()

    def summary(self, owner_id: int) -> dict:
        return {
            "stats": self.catalog.dashboard_stats(owner_id),
            "activity": self.catalog.recent_activity(owner_id),
            "albums": self.catalog.albums(owner_id),
            "tags": self.catalog.tags(owner_id),
        }

