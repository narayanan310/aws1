"""Processing queue repository."""

from __future__ import annotations

from app.infrastructure.database.models import ProcessingQueue, utcnow


class QueueRepository:
    """Local SQLite queue repository."""

    def enqueue(self, owner_id: int, photo_id: int, task_type: str, payload: dict | None = None) -> ProcessingQueue:
        task = ProcessingQueue(owner_id=owner_id, photo_id=photo_id, task_type=task_type, payload=payload or {})
        from app.extensions import db

        db.session.add(task)
        return task

    def next_pending(self, task_type: str) -> ProcessingQueue | None:
        return (
            ProcessingQueue.query.filter_by(task_type=task_type, status="pending")
            .order_by(ProcessingQueue.created_at.asc())
            .first()
        )

    def mark_running(self, task: ProcessingQueue) -> None:
        task.status = "running"
        task.started_at = utcnow()
        task.attempts += 1

    def update_status(self, task: ProcessingQueue, new_status: str) -> None:
        task.status = new_status
        from app.extensions import db
        db.session.commit()

    def mark_completed(self, task: ProcessingQueue) -> None:
        task.status = "completed"
        task.completed_at = utcnow()

    def mark_failed(self, task: ProcessingQueue, message: str) -> None:
        task.error_message = message
        task.status = "failed" if task.attempts >= task.max_attempts else "pending"

