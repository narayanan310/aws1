"""Restartable local queue workers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from loguru import logger

from app import create_app
from app.extensions import db
from app.infrastructure.database.models import Photo, ProcessingQueue
from app.infrastructure.repositories.queue_repository import QueueRepository


class BaseWorker(ABC):
    """Polls SQLite processing_queue for one task type."""

    task_type: str

    def __init__(self, sleep_seconds: float = 2.0, once: bool = False) -> None:
        from flask import current_app
        self.app = current_app._get_current_object() if current_app else create_app()
        self.queue = QueueRepository()
        self.sleep_seconds = sleep_seconds
        self.once = once

    def run(self) -> None:
        print(f"DEBUG: Worker started for task_type={self.task_type}")
        while True:
            with self.app.app_context():
                task = self.queue.next_pending(self.task_type)
                print(f"DEBUG: {self.task_type} next_pending returned {task}")
                if task:
                    self._run_task(task)
                    db.session.commit()
            if self.once:
                break
            time.sleep(self.sleep_seconds)

    def _run_task(self, task: ProcessingQueue) -> None:
        self.queue.mark_running(task)
        try:
            photo = db.session.get(Photo, task.photo_id)
            if not photo:
                raise ValueError("Photo not found")
            self.handle(photo, task)
            self.queue.mark_completed(task)
            print(f"DEBUG: Task {task.id} completed successfully")
        except Exception as exc:
            self.queue.mark_failed(task, str(exc))
            print(f"DEBUG: Task {task.id} failed: {exc}")
            logger.exception("Worker task failed: {}", task.id)

    @abstractmethod
    def handle(self, photo: Photo, task: ProcessingQueue) -> None:
        """Handle a task for one photo."""

