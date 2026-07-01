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

    def __init__(self, sleep_seconds: float = 3.0, once: bool = False) -> None:
        from flask import current_app
        self.app = current_app._get_current_object() if current_app else create_app()
        self.queue = QueueRepository()
        self.sleep_seconds = sleep_seconds
        self.once = once
        self._idle_logged = False

    def run(self) -> None:
        logger.info("Worker started for task_type={}", self.task_type)
        while True:
            with self.app.app_context():
                task = self.queue.next_pending(self.task_type)
                if task:
                    self._idle_logged = False
                    self._run_task(task)
                    db.session.commit()
                else:
                    if not self._idle_logged:
                        logger.debug("Worker [{}] is idle, polling every {}s", self.task_type, self.sleep_seconds)
                        self._idle_logged = True
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
            logger.info("Task {} ({}) completed successfully", task.id, self.task_type)
        except Exception as exc:
            self.queue.mark_failed(task, str(exc))
            logger.error("Task {} failed: {}", task.id, exc)

    @abstractmethod
    def handle(self, photo: Photo, task: ProcessingQueue) -> None:
        """Handle a task for one photo."""
