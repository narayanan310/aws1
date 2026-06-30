"""Authentication use cases."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from flask_login import login_user, logout_user

from app.domain.exceptions.domain_exceptions import ValidationError
from app.extensions import db
from app.infrastructure.database.models import (
    EmailVerificationToken,
    LoginAttempt,
    PasswordResetToken,
    User,
    utcnow,
)
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.passwords import hash_password, validate_strong_password, verify_password


class AuthenticationService:
    """Local authentication implementation, replaceable by Cognito later."""

    def __init__(self) -> None:
        self.users = UserRepository()

    def register(self, username: str, email: str, password: str) -> tuple[User, str]:
        username = username.strip()
        email = email.strip().lower()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        validate_strong_password(password)
        if self.users.by_username(username) or self.users.by_email(email):
            raise ValidationError("Username or email already exists.")
        user = User(username=username, email=email, password_hash=hash_password(password))
        db.session.add(user)
        db.session.flush()
        token = self._create_email_verification_token(user.id)
        db.session.commit()
        return user, token

    def authenticate(self, identifier: str, password: str, remember: bool = False) -> User:
        user = self.users.by_identifier(identifier)
        self._record_attempt(identifier, user, False)
        if not user:
            db.session.commit()
            raise ValidationError("Invalid credentials.")
        if user.locked_until and user.locked_until > utcnow():
            db.session.commit()
            raise ValidationError("Account is temporarily locked.")
        if not verify_password(user.password_hash, password):
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = utcnow() + timedelta(minutes=15)
            db.session.commit()
            raise ValidationError("Invalid credentials.")
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = utcnow()
        self._record_attempt(identifier, user, True)
        login_user(user, remember=remember)
        db.session.commit()
        return user

    def logout(self) -> None:
        logout_user()

    def verify_email(self, token: str) -> bool:
        token_hash = hash_password_token(token)
        row = EmailVerificationToken.query.filter_by(token_hash=token_hash, used_at=None).first()
        if not row or row.expires_at < utcnow():
            return False
        user = db.session.get(User, row.owner_id)
        if user:
            user.email_verified = True
        row.used_at = utcnow()
        db.session.commit()
        return True

    def request_password_reset(self, email: str) -> str | None:
        user = self.users.by_email(email)
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        db.session.add(
            PasswordResetToken(
                owner_id=user.id,
                token_hash=hash_password_token(token),
                expires_at=utcnow() + timedelta(hours=1),
            )
        )
        db.session.commit()
        return token

    def reset_password(self, token: str, password: str) -> bool:
        validate_strong_password(password)
        token_hash = hash_password_token(token)
        row = PasswordResetToken.query.filter_by(token_hash=token_hash, used_at=None).first()
        if not row or row.expires_at < utcnow():
            return False
        user = db.session.get(User, row.owner_id)
        if not user:
            return False
        user.password_hash = hash_password(password)
        user.failed_login_count = 0
        user.locked_until = None
        row.used_at = utcnow()
        db.session.commit()
        return True

    def _create_email_verification_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        db.session.add(
            EmailVerificationToken(
                owner_id=user_id,
                token_hash=hash_password_token(token),
                expires_at=utcnow() + timedelta(days=1),
            )
        )
        return token

    def _record_attempt(self, identifier: str, user: User | None, successful: bool) -> None:
        db.session.add(LoginAttempt(identifier=identifier.strip(), successful=successful))


def hash_password_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()

