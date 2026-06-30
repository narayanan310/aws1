"""Embedding worker."""

from __future__ import annotations

from app.application.services.ai_pipeline_service import AIPipelineService
from app.domain.entities.enums import QueueTaskType
from app.extensions import db
from app.infrastructure.database.models import Photo, ProcessingQueue
from app.workers.base_worker import BaseWorker


class EmbeddingWorker(BaseWorker):
    task_type = QueueTaskType.EMBEDDING.value

    def handle(self, photo: Photo, task: ProcessingQueue) -> None:
        def update_status(msg: str):
            self.queue.update_status(task, msg)
        AIPipelineService().run_embedding(photo, update_status)
        db.session.flush()


if __name__ == "__main__":
    EmbeddingWorker().run()

