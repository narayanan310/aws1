"""Photo repository with mandatory ownership filters."""

from __future__ import annotations

from sqlalchemy import or_

from app.infrastructure.database.models import AIResult, Photo, PhotoTag, Tag
from app.infrastructure.repositories.base import Repository


class PhotoRepository(Repository[Photo]):
    model = Photo

    def get_owned(self, owner_id: int, photo_id: int) -> Photo | None:
        return Photo.query.filter_by(id=photo_id, owner_id=owner_id).first()

    def get_owned_by_uuid(self, owner_id: int, photo_uuid: str) -> Photo | None:
        return Photo.query.filter_by(uuid=photo_uuid, owner_id=owner_id).first()

    def list_owned(
        self,
        owner_id: int,
        *,
        search: str = "",
        sort: str = "newest",
        favorite: bool | None = None,
        archived: bool | None = None,
        deleted: bool = False,
        file_format: str | None = None,
        page: int = 1,
        per_page: int = 24,
    ):
        query = Photo.query.filter_by(owner_id=owner_id, deleted=deleted)
        if favorite is not None:
            query = query.filter(Photo.favorite.is_(favorite))
        if archived is not None:
            query = query.filter(Photo.archived.is_(archived))
        if file_format:
            query = query.filter(Photo.format == file_format.upper())
        if search:
            like = f"%{search}%"
            query = query.outerjoin(AIResult, AIResult.photo_id == Photo.id).filter(
                or_(
                    Photo.original_filename.ilike(like),
                    Photo.camera.ilike(like),
                    AIResult.title.ilike(like),
                    AIResult.description.ilike(like),
                    AIResult.ocr_text.ilike(like),
                )
            )
        if sort == "oldest":
            query = query.order_by(Photo.uploaded_at.asc())
        elif sort == "filename":
            query = query.order_by(Photo.original_filename.asc())
        elif sort == "largest":
            query = query.order_by(Photo.file_size.desc())
        else:
            query = query.order_by(Photo.uploaded_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def tags_for_photo(self, owner_id: int, photo_id: int) -> list[Tag]:
        return (
            Tag.query.join(PhotoTag, PhotoTag.tag_id == Tag.id)
            .filter(PhotoTag.owner_id == owner_id, PhotoTag.photo_id == photo_id)
            .order_by(Tag.name.asc())
            .all()
        )

