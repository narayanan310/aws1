"""Repository base classes."""

from __future__ import annotations

from typing import Generic, TypeVar

from app.extensions import db

ModelT = TypeVar("ModelT")


class UnitOfWork:
    """Tiny SQLAlchemy unit-of-work wrapper."""

    def commit(self) -> None:
        db.session.commit()

    def rollback(self) -> None:
        db.session.rollback()

    def add(self, entity: object) -> None:
        db.session.add(entity)

    def delete(self, entity: object) -> None:
        db.session.delete(entity)


class Repository(Generic[ModelT]):
    """Base repository for shared persistence helpers."""

    model: type[ModelT]

    def get(self, entity_id: int) -> ModelT | None:
        return db.session.get(self.model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        db.session.add(entity)
        return entity

