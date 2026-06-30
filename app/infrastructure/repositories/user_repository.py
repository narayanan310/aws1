"""User repository."""

from __future__ import annotations

from app.infrastructure.database.models import User
from app.infrastructure.repositories.base import Repository


class UserRepository(Repository[User]):
    model = User

    def by_identifier(self, identifier: str) -> User | None:
        normalized = identifier.strip().lower()
        return User.query.filter((User.email == normalized) | (User.username == identifier.strip())).first()

    def by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email.strip().lower()).first()

    def by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username.strip()).first()

