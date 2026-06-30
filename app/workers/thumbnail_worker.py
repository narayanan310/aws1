"""Thumbnail worker.

Thumbnail generation is handled by ImageWorker in the local implementation.
This worker remains independent so it can map to a separate Lambda/SQS consumer later.
"""

from __future__ import annotations

from app.domain.entities.enums import QueueTaskType
from app.infrastructure.database.models import Photo
from app.workers.image_worker import ImageWorker


class ThumbnailWorker(ImageWorker):
    task_type = QueueTaskType.IMAGE_PROCESSING.value

    def handle(self, photo: Photo) -> None:
        super().handle(photo)


if __name__ == "__main__":
    ThumbnailWorker().run()

