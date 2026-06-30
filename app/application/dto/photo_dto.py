"""Photo DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhotoUploadResult:
    photo_id: int
    photo_uuid: str
    original_filename: str
    processing_status: str


@dataclass(frozen=True)
class SearchFilters:
    query: str = ""
    sort: str = "newest"
    favorite: bool | None = None
    archived: bool | None = None
    deleted: bool = False
    file_format: str | None = None
    page: int = 1
    per_page: int = 24

