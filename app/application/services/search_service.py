"""Text and semantic search use cases."""

from __future__ import annotations

import math

from app.infrastructure.ai.providers import MockEmbeddingService
from app.infrastructure.database.models import AIResult, Embedding, Photo, PhotoTag, Tag
from app.infrastructure.repositories.photo_repository import PhotoRepository


class SearchService:
    """Search user-owned photos with text filters and local vector similarity."""

    def __init__(self) -> None:
        self.photos = PhotoRepository()
        self.embeddings = MockEmbeddingService()

    def semantic(self, owner_id: int, query: str, limit: int = 24) -> list[Photo]:
        query_vector = self.embeddings.embed_text(query)
        rows = Embedding.query.filter_by(owner_id=owner_id).all()
        scored = [(self._cosine(query_vector, row.vector), row.photo_id) for row in rows]
        scored.sort(reverse=True, key=lambda item: item[0])
        ids = [photo_id for _, photo_id in scored[:limit]]
        if not ids:
            return []
        return Photo.query.filter(Photo.owner_id == owner_id, Photo.id.in_(ids), Photo.deleted.is_(False)).all()

    def full_text(self, owner_id: int, query: str, limit: int = 50) -> list[Photo]:
        like = f"%{query}%"
        return (
            Photo.query.outerjoin(AIResult, AIResult.photo_id == Photo.id)
            .outerjoin(PhotoTag, PhotoTag.photo_id == Photo.id)
            .outerjoin(Tag, Tag.id == PhotoTag.tag_id)
            .filter(Photo.owner_id == owner_id, Photo.deleted.is_(False))
            .filter(
                (Photo.original_filename.ilike(like))
                | (Photo.camera.ilike(like))
                | (AIResult.title.ilike(like))
                | (AIResult.description.ilike(like))
                | (AIResult.notes.ilike(like))
                | (AIResult.ocr_text.ilike(like))
                | (Tag.name.ilike(like))
            )
            .limit(limit)
            .all()
        )

    def _cosine(self, left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
        right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
        return dot / (left_norm * right_norm)

