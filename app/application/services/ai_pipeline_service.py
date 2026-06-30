"""AI Pipeline manual trigger and approval service."""

from __future__ import annotations

import string
from pathlib import Path
from typing import Any

from flask import current_app

from app.application.services.audit_service import ActivityService, AuditService
from app.application.services.photo_service import PhotoService
from app.domain.entities.enums import ActivityType, QueueTaskType
from app.domain.exceptions.domain_exceptions import NotFoundError, ValidationError
from app.extensions import db
from app.infrastructure.database.models import AIResult, Photo, PhotoTag, Tag, User
from app.infrastructure.repositories.queue_repository import QueueRepository


class AIPipelineService:
    """Handles manual AI analysis triggers and metadata approval."""

    def __init__(self) -> None:
        self.queue = QueueRepository()
        self.photo_service = PhotoService()
        self.activity = ActivityService()
        self.audit = AuditService()

    def trigger_analysis(self, owner_id: int, photo_id: int) -> dict[str, str]:
        """Trigger AI analysis for a photo."""
        photo = self.photo_service.get_owned_or_404(owner_id, photo_id)

        # Enqueue unified VLM task
        self.queue.enqueue(owner_id, photo.id, QueueTaskType.AI_ANALYSIS.value)

        # Update status
        photo.ai_status = "queued"
        db.session.commit()

        self.activity.record(
            owner_id=owner_id,
            photo_id=photo.id,
            action=ActivityType.AI_PROCESSING.value,
            message=f"Queued AI analysis for {photo.original_filename}",
        )
        return {"status": "success", "message": "AI analysis queued"}

    def trigger_batch_analysis(self, owner_id: int, photo_ids: list[int]) -> dict[str, Any]:
        """Trigger AI analysis for a batch of photos."""
        queued_count = 0
        for photo_id in photo_ids:
            try:
                self.trigger_analysis(owner_id, photo_id)
                queued_count += 1
            except NotFoundError:
                pass
        return {"status": "success", "message": f"Queued {queued_count} photos for AI analysis"}

    def update_metadata(self, owner_id: int, photo_id: int, payload: dict[str, Any]) -> dict[str, str]:
        """Save user manual edits to the database and trigger embedding."""
        photo = self.photo_service.get_owned_or_404(owner_id, photo_id)
        
        # Get or create AIResult
        ai_result = AIResult.query.filter_by(owner_id=owner_id, photo_id=photo_id).first()
        if not ai_result:
            ai_result = AIResult(owner_id=owner_id, photo_id=photo_id)
            db.session.add(ai_result)

        # Apply manual fields if provided
        if "title" in payload:
            ai_result.title = payload["title"]
        if "description" in payload:
            ai_result.description = payload["description"]
            
        # Handle tags
        if "tags" in payload:
            ai_result.keywords = payload["tags"]
            self._sync_tags(owner_id, photo_id, payload["tags"])

        # Only set to completed/approved if AI is not currently running
        if photo.ai_status not in ["queued", "analyzing"]:
            ai_result.status = "approved"
            photo.ai_status = "completed"
            # Queue Embedding since the metadata is now finalized
            self.queue.enqueue(owner_id, photo.id, QueueTaskType.EMBEDDING.value)

        db.session.commit()

        self.activity.record(
            owner_id=owner_id,
            photo_id=photo.id,
            action=ActivityType.AI_PROCESSING.value,
            message=f"Updated metadata for {photo.original_filename}",
        )
        return {"status": "success", "message": "Metadata saved"}

    def _sync_tags(self, owner_id: int, photo_id: int, tags: list[str]) -> None:
        """Create tags and relationships based on accepted tag strings."""
        if not tags:
            return

        # First, clear existing AI tags to prevent duplicates if re-running
        PhotoTag.query.filter_by(photo_id=photo_id, owner_id=owner_id, ai_generated=True).delete()

        translator = str.maketrans("", "", string.punctuation)
        for tag_name in set(tags):
            tag_name = tag_name.strip()
            if not tag_name:
                continue

            normalized = tag_name.lower().translate(translator)
            tag = Tag.query.filter_by(owner_id=owner_id, normalized_name=normalized).first()
            if not tag:
                tag = Tag(owner_id=owner_id, name=tag_name, normalized_name=normalized, ai_generated=True)
                db.session.add(tag)
                db.session.flush()

            # Add mapping
            pt = PhotoTag(photo_id=photo_id, tag_id=tag.id, owner_id=owner_id, ai_generated=True)
            db.session.merge(pt)

    def run_analysis(self, photo: Photo, update_status: Any = None) -> None:
        """Run Vision pipeline in the background using the unified VLM."""
        from app.infrastructure.ai.providers import MockVisionService
        
        if update_status:
            update_status("Running VLM Analysis...")
            
        vision_result = MockVisionService().analyze(Path(photo.original_path))
            
        ai_result = AIResult.query.filter_by(owner_id=photo.owner_id, photo_id=photo.id).first()
        if not ai_result:
            ai_result = AIResult(owner_id=photo.owner_id, photo_id=photo.id)
            db.session.add(ai_result)
            
        # Store raw output for debugging or future reference
        ai_result.raw = vision_result
        
        # Merge Intelligently
        ai_result.title = ai_result.title or vision_result.get("title", "")
        ai_result.caption = ai_result.caption or vision_result.get("summary", "")
        ai_result.description = ai_result.description or vision_result.get("description", "")
        ai_result.suggested_album = ai_result.suggested_album or "AI Suggested"
        ai_result.scene_type = ai_result.scene_type or vision_result.get("scene", "")
        ai_result.ocr_text = ai_result.ocr_text or vision_result.get("text_detected", "")
        ai_result.confidence = 0.95
        
        # Combine tags uniquely
        existing_keywords = set(ai_result.keywords) if ai_result.keywords else set()
        vlm_keywords = set(vision_result.get("searchable_keywords", []) + vision_result.get("tags", []))
        ai_result.keywords = list(existing_keywords.union(vlm_keywords))
        
        ai_result.objects = vision_result.get("detected_objects", [])
        
        # Finalize and trigger next steps
        ai_result.status = "approved"
        photo.ai_status = "completed"
        
        # Sync tags table
        self._sync_tags(photo.owner_id, photo.id, ai_result.keywords)
        
        if update_status:
            update_status("completed")
            
        self.queue.enqueue(photo.owner_id, photo.id, QueueTaskType.EMBEDDING.value)

    def run_embedding(self, photo: Photo, update_status: Any = None) -> None:
        """Generate embeddings from the accepted metadata."""
        from app.infrastructure.ai.providers import MockEmbeddingService
        from app.infrastructure.database.models import Embedding
        
        if update_status:
            update_status("Generating Vector...")
            
        ai_result = AIResult.query.filter_by(owner_id=photo.owner_id, photo_id=photo.id).first()
        text_context = ""
        if ai_result:
            text_context = f"{ai_result.title} {ai_result.description} {' '.join(ai_result.keywords)}"
            
        vector = MockEmbeddingService().embed_image(Path(photo.original_path), text_context)
        
        emb = Embedding.query.filter_by(owner_id=photo.owner_id, photo_id=photo.id).first()
        if not emb:
            emb = Embedding(
                owner_id=photo.owner_id, 
                photo_id=photo.id,
                model_name=MockEmbeddingService.model_name,
                dimension=MockEmbeddingService.dimension
            )
            db.session.add(emb)
        emb.vector = vector
