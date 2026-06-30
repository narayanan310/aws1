"""Ownership authorization policy."""

from __future__ import annotations

from app.domain.exceptions.domain_exceptions import AuthorizationError


def require_owner(owner_id: int, actor_id: int) -> None:
    """Raise when the actor does not own a resource."""

    if owner_id != actor_id:
        raise AuthorizationError("You do not have access to this resource.")

