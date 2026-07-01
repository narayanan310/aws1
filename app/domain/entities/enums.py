"""Domain enums used across models and services."""

from __future__ import annotations

from enum import StrEnum


class PhotoStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class QueueStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class QueueTaskType(StrEnum):
    IMAGE_PROCESSING = "image_processing"

    EMBEDDING = "embedding"
    CLEANUP = "cleanup"


class Visibility(StrEnum):
    PRIVATE = "private"


class ActivityType(StrEnum):
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD = "upload"
    DELETE = "delete"
    RESTORE = "restore"
    ARCHIVE = "archive"
    DOWNLOAD = "download"
    EDIT_NOTES = "edit_notes"

    FAVORITE = "favorite"

