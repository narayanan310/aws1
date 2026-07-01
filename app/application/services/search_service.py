"""Text and semantic search use cases."""

from __future__ import annotations

import math

from app.infrastructure.database.models import Photo, PhotoTag, Tag
from app.infrastructure.repositories.photo_repository import PhotoRepository


class SearchService:
    """Search user-owned photos with text filters and local vector similarity."""

    def __init__(self) -> None:
        self.photos = PhotoRepository()


    def full_text(self, owner_id: int, query: str, limit: int = 50) -> list[Photo]:
        like = f"%{query}%"
        return (
            Photo.query.outerjoin(PhotoTag, PhotoTag.photo_id == Photo.id)
            .outerjoin(Tag, Tag.id == PhotoTag.tag_id)
            .filter(Photo.owner_id == owner_id, Photo.deleted.is_(False))
            .filter(
                (Photo.original_filename.ilike(like))
                | (Photo.camera.ilike(like))
                | (Tag.name.ilike(like))
            )
            .limit(limit)
            .all()
        )

