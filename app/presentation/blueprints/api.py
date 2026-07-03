"""REST API blueprint."""

from __future__ import annotations

from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user, login_required

from app.application.dto.photo_dto import SearchFilters
from app.application.services.catalog_service import NoteService
from app.application.services.photo_service import PhotoService
from app.application.services.search_service import SearchService
from app.infrastructure.database.models import PhotoNote
from app.infrastructure.repositories.photo_repository import PhotoRepository
from app.extensions import db
from app.infrastructure.database.models import Photo

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def ok(data=None, meta=None, status: int = 200):
    return jsonify({"ok": True, "data": data or {}, "meta": meta or {}}), status


@api_bp.route("/photos")
@login_required
def photos():
    filters = SearchFilters(
        query=request.args.get("q", ""),
        sort=request.args.get("sort", "newest"),
        favorite=_bool_arg("favorite"),
        archived=_bool_arg("archived"),
        deleted=_bool_arg("deleted") or False,
        file_format=request.args.get("format") or None,
        page=request.args.get("page", 1, type=int),
        per_page=min(request.args.get("per_page", 24, type=int), 100),
    )
    pagination = PhotoService().list_photos(current_user.id, filters)
    return ok(
        [_photo_json(photo) for photo in pagination.items],
        {
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
            "per_page": pagination.per_page,
        },
    )


@api_bp.route("/photos/<int:photo_id>")
@login_required
def photo_detail(photo_id: int):
    photo = PhotoService().get_owned_or_404(current_user.id, photo_id)
    note = PhotoNote.query.filter_by(owner_id=current_user.id, photo_id=photo.id).first()
    tags = PhotoRepository().tags_for_photo(current_user.id, photo.id)
    payload = _photo_json(photo)
    payload["note"] = _note_json(note)
    payload["tags"] = [tag.name for tag in tags]
    return ok(payload)


@api_bp.route("/photos/<int:photo_id>/favorite", methods=["POST"])
@login_required
def favorite(photo_id: int):
    photo = PhotoService().toggle_favorite(current_user.id, photo_id)
    return ok(_photo_json(photo))


@api_bp.route("/photos/<int:photo_id>/notes", methods=["POST"])
@login_required
def notes(photo_id: int):
    payload = request.get_json(silent=True) or {}
    note = NoteService().upsert(
        current_user.id,
        photo_id,
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        personal_notes=payload.get("personal_notes", ""),
    )
    return ok(_note_json(note))



def _photo_json(photo):
    return {
        "id": photo.id,
        "uuid": photo.uuid,
        "filename": photo.original_filename,
        "uploaded_at": photo.uploaded_at.isoformat(),
        "width": photo.width,
        "height": photo.height,
        "format": photo.format,
        "file_size": photo.file_size,
        "favorite": photo.favorite,
        "archived": photo.archived,
        "deleted": photo.deleted,
        "processing_status": photo.processing_status,
        "thumbnail_url": url_for("photos.file", photo_id=photo.id, variant="thumbnail"),
        "preview_url": url_for("photos.file", photo_id=photo.id, variant="preview"),
    }


def _note_json(note):
    if not note:
        return None
    return {
        "title": note.title,
        "description": note.description,
        "personal_notes": note.personal_notes,
        "version": note.version,
    }


def _bool_arg(name: str) -> bool | None:
    value = request.args.get(name)
    if value is None or value == "":
        return None
    return value.lower() in {"1", "true", "yes", "on"}

@api_bp.route('/internal/worker-complete', methods=['POST'])
def worker_complete():
    """Webhook triggered by AWS Lambda when thumbnail generation finishes."""
    filename = request.form.get('filename')
    
    if not filename:
        return jsonify({"error": "Missing filename"}), 400
        
    # Find the photo in the database
    photo = Photo.query.filter_by(stored_filename=filename).first()
    if photo:
        # Update status to complete!
        photo.processing_status = 'completed'
        db.session.commit()
        return jsonify({"status": "Database updated successfully"}), 200
        
    return jsonify({"error": "Photo not found"}), 404


