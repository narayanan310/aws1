"""Trash cleanup worker."""

from __future__ import annotations

from app.domain.entities.enums import QueueTaskType
from app.infrastructure.database.models import Photo
from app.workers.base_worker import BaseWorker


class CleanupWorker(BaseWorker):
    task_type = QueueTaskType.CLEANUP.value

    def handle(self, photo: Photo) -> None:
        # Retention policies can call PhotoService.delete_forever here.
        return None


if __name__ == "__main__":
    CleanupWorker().run()

