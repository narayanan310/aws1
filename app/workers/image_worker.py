"""Image processing worker."""

from __future__ import annotations

from app.application.services.image_processing_service import ImageProcessingService
from app.domain.entities.enums import QueueTaskType
from app.extensions import db
from app.infrastructure.database.models import Photo, ProcessingQueue
from app.workers.base_worker import BaseWorker


class ImageWorker(BaseWorker):
    task_type = QueueTaskType.IMAGE_PROCESSING.value

    def handle(self, photo: Photo, task: ProcessingQueue) -> None:
        ImageProcessingService().process(photo)
        db.session.flush()


if __name__ == "__main__":
    ImageWorker().run()

