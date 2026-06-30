"""AI analysis worker."""

from __future__ import annotations

from app.application.services.ai_pipeline_service import AIPipelineService
from app.domain.entities.enums import QueueTaskType
from app.extensions import db
from app.infrastructure.database.models import Photo, ProcessingQueue
from app.workers.base_worker import BaseWorker


class AIWorker(BaseWorker):
    task_type = QueueTaskType.AI_ANALYSIS.value

    def handle(self, photo: Photo, task: ProcessingQueue) -> None:
        def update_status(msg: str):
            self.queue.update_status(task, msg)
        AIPipelineService().run_analysis(photo, update_status)
        db.session.flush()


if __name__ == "__main__":
    AIWorker().run()

