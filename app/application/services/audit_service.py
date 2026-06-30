"""Audit and activity logging services."""

from __future__ import annotations

from flask import request

from app.extensions import db
from app.infrastructure.database.models import ActivityLog, AuditLog


class AuditService:
    """Write security audit records."""

    def record(
        self,
        *,
        actor_id: int | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        outcome: str = "success",
        metadata: dict | None = None,
    ) -> None:
        db.session.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get("User-Agent") if request else None,
                outcome=outcome,
                log_metadata=metadata or {},
            )
        )


class ActivityService:
    """Write user-facing activity records."""

    def record(
        self,
        *,
        owner_id: int | None,
        action: str,
        message: str,
        photo_id: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        db.session.add(
            ActivityLog(
                owner_id=owner_id,
                photo_id=photo_id,
                action=action,
                message=message,
                log_metadata=metadata or {},
            )
        )

