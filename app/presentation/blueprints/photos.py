"""Photo UI blueprint."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.application.dto.photo_dto import SearchFilters
from app.application.services.catalog_service import NoteService
from app.application.services.photo_service import PhotoService
from app.application.services.search_service import SearchService
from app.domain.exceptions.domain_exceptions import ValidationError
from app.infrastructure.database.models import AIResult, PhotoNote
from app.infrastructure.repositories.photo_repository import PhotoRepository

photos_bp = Blueprint("photos", __name__, url_prefix="/photos")


@photos_bp.route("/")
@login_required
def gallery():
    filters = SearchFilters(
        query=request.args.get("q", ""),
        sort=request.args.get("sort", "newest"),
        favorite=_bool_arg("favorite"),
        archived=_bool_arg("archived"),
        deleted=_bool_arg("deleted") or False,
        file_format=request.args.get("format") or None,
        page=request.args.get("page", 1, type=int),
        per_page=24,
    )
    pagination = PhotoService().list_photos(current_user.id, filters)
    return render_template("photos/gallery.html", pagination=pagination, filters=filters)


@photos_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        try:
            uploads = request.files.getlist("photos")
            metadata = {
                "title": request.form.get("title", "").strip(),
                "caption": request.form.get("caption", "").strip(),
                "description": request.form.get("description", "").strip(),
                "album": request.form.get("album", "").strip(),
                "tags": [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
            }
            results = PhotoService().upload_many(current_user, uploads, metadata=metadata)
            flash(f"Uploaded {len(results)} photo(s). Workers will process them.", "success")
            return redirect(url_for("photos.gallery"))
        except ValidationError as exc:
            flash(str(exc), "error")
    return render_template("photos/upload.html")


@photos_bp.route("/<int:photo_id>")
@login_required
def detail(photo_id: int):
    photo = PhotoService().get_owned_or_404(current_user.id, photo_id)
    ai = AIResult.query.filter_by(owner_id=current_user.id, photo_id=photo.id).first()
    note = PhotoNote.query.filter_by(owner_id=current_user.id, photo_id=photo.id).first()
    tags = PhotoRepository().tags_for_photo(current_user.id, photo.id)
    return render_template("photos/detail.html", photo=photo, ai=ai, note=note, tags=tags)


@photos_bp.route("/<int:photo_id>/file/<variant>")
@login_required
def file(photo_id: int, variant: str):
    path = PhotoService().authorized_file_path(current_user.id, photo_id, variant)
    return send_file(path)


@photos_bp.route("/<int:photo_id>/download")
@login_required
def download(photo_id: int):
    path = PhotoService().authorized_file_path(current_user.id, photo_id, "original")
    return send_file(path, as_attachment=True)


@photos_bp.route("/<int:photo_id>/favorite", methods=["POST"])
@login_required
def favorite(photo_id: int):
    PhotoService().toggle_favorite(current_user.id, photo_id)
    return redirect(request.referrer or url_for("photos.gallery"))


@photos_bp.route("/<int:photo_id>/archive", methods=["POST"])
@login_required
def archive(photo_id: int):
    archived = request.form.get("archived", "true") == "true"
    PhotoService().archive(current_user.id, photo_id, archived)
    return redirect(request.referrer or url_for("photos.gallery"))


@photos_bp.route("/<int:photo_id>/delete", methods=["POST"])
@login_required
def delete(photo_id: int):
    PhotoService().soft_delete(current_user.id, photo_id)
    return redirect(url_for("photos.gallery"))


@photos_bp.route("/<int:photo_id>/restore", methods=["POST"])
@login_required
def restore(photo_id: int):
    PhotoService().restore(current_user.id, photo_id)
    return redirect(url_for("photos.gallery", deleted="true"))


@photos_bp.route("/<int:photo_id>/notes", methods=["POST"])
@login_required
def notes(photo_id: int):
    NoteService().upsert(
        current_user.id,
        photo_id,
        title=request.form.get("title", ""),
        description=request.form.get("description", ""),
        personal_notes=request.form.get("personal_notes", ""),
        ai_notes=request.form.get("ai_notes", ""),
    )
    flash("Notes saved.", "success")
    return redirect(url_for("photos.detail", photo_id=photo_id))


@photos_bp.route("/search/semantic")
@login_required
def semantic_search():
    query = request.args.get("q", "")
    results = SearchService().semantic(current_user.id, query) if query else []
    return render_template("photos/search.html", results=results, query=query)


def _bool_arg(name: str) -> bool | None:
    value = request.args.get(name)
    if value is None or value == "":
        return None
    return value.lower() in {"1", "true", "yes", "on"}


from app.application.services.ai_pipeline_service import AIPipelineService
from app.infrastructure.database.models import ProcessingQueue

@photos_bp.route("/api/<int:photo_id>/analyze", methods=["POST"])
@login_required
def api_analyze(photo_id: int):
    return AIPipelineService().trigger_analysis(current_user.id, photo_id)


@photos_bp.route("/api/analyze-batch", methods=["POST"])
@login_required
def api_analyze_batch():
    data = request.get_json() or {}
    photo_ids = data.get("photo_ids", [])
    return AIPipelineService().trigger_batch_analysis(current_user.id, photo_ids)


@photos_bp.route("/api/<int:photo_id>/ai-status")
@login_required
def api_ai_status(photo_id: int):
    task = ProcessingQueue.query.filter_by(
        owner_id=current_user.id, photo_id=photo_id
    ).order_by(ProcessingQueue.created_at.desc()).first()
    
    if not task:
        return {"status": "not_queued", "progress": None}
    
    return {"status": task.status, "task_type": task.task_type}


@photos_bp.route("/api/<int:photo_id>/ai-draft")
@login_required
def api_ai_draft(photo_id: int):
    ai = AIResult.query.filter_by(owner_id=current_user.id, photo_id=photo_id).first()
    if not ai:
        return {}
        
    raw = ai.raw or {}
    
    return {
        "title": ai.title or raw.get("title", ""),
        "caption": ai.caption or raw.get("summary", ""),
        "description": ai.description or raw.get("description", ""),
        "suggested_album": ai.suggested_album or "AI Suggested",
        "keywords": ai.keywords or raw.get("searchable_keywords", []) or raw.get("tags", []),
        "objects": ai.objects or raw.get("detected_objects", []),
        "scene_type": ai.scene_type or raw.get("scene", ""),
        "confidence": ai.confidence or 0.95,
        "raw": raw
    }


@photos_bp.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    if "photo" not in request.files:
        return {"error": "No file provided"}, 400
        
    upload = request.files["photo"]
    metadata = {
        "title": request.form.get("title", "").strip(),
        "caption": request.form.get("caption", "").strip(),
        "description": request.form.get("description", "").strip(),
        "album": request.form.get("album", "").strip(),
        "tags": [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()],
        "skip_ai": request.form.get("skip_ai") == "true"
    }
    
    try:
        results = PhotoService().upload_many(current_user, [upload], metadata=metadata)
        if not results:
            return {"error": "Upload failed"}, 500
            
        result = results[0]
        # Get the photo object to return its ai_status
        photo = PhotoService().get_owned_or_404(current_user.id, result.photo_id)
        
        return {
            "status": "success",
            "photo_id": photo.id,
            "filename": photo.original_filename,
            "processing_status": photo.processing_status,
            "ai_status": photo.ai_status,
            "thumbnail_url": url_for("photos.file", photo_id=photo.id, variant="thumbnail")
        }
    except ValidationError as exc:
        return {"error": str(exc)}, 400

@photos_bp.route("/api/status")
@login_required
def api_batch_status():
    ids_str = request.args.get("ids", "")
    if not ids_str:
        return {"statuses": {}}
        
    try:
        photo_ids = [int(i.strip()) for i in ids_str.split(",") if i.strip()]
    except ValueError:
        return {"error": "Invalid IDs"}, 400
        
    from app.infrastructure.database.models import Photo
    photos = Photo.query.filter(Photo.owner_id == current_user.id, Photo.id.in_(photo_ids)).all()
    
    statuses = {}
    for p in photos:
        statuses[p.id] = {
            "processing_status": p.processing_status,
            "ai_status": p.ai_status
        }
        
    return {"statuses": statuses}

@photos_bp.route("/api/<int:photo_id>/metadata", methods=["POST"])
@login_required
def api_update_metadata(photo_id: int):
    payload = request.get_json() or {}
    return AIPipelineService().update_metadata(current_user.id, photo_id, payload)



