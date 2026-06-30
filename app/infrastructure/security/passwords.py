"""Password validation and hashing."""

from __future__ import annotations

import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.domain.exceptions.domain_exceptions import ValidationError


def validate_strong_password(password: str) -> None:
    """Require a SaaS-style password baseline."""

    if len(password) < 10:
        raise ValidationError("Password must be at least 10 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must include a lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must include a number.")


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)

