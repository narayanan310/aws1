"""Photo UI blueprint."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.application.dto.photo_dto import SearchFilters
from app.application.services.catalog_service import NoteService
from app.application.services.photo_service import PhotoService
from app.application.services.search_service import SearchService
from app.domain.exceptions.domain_exceptions import ValidationError
from app.infrastructure.database.models import PhotoNote
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





@photos_bp.route("/<int:photo_id>/file/<variant>")
@login_required
def file(photo_id: int, variant: str):
    path = PhotoService().authorized_file_path(current_user.id, photo_id, variant)
    if str(path).startswith("http"):
        return redirect(str(path))
    return send_file(path)


@photos_bp.route("/<int:photo_id>/download")
@login_required
def download(photo_id: int):
    path = PhotoService().authorized_file_path(current_user.id, photo_id, "original")
    if str(path).startswith("http"):
        return redirect(str(path))
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
    )
    flash("Notes saved.", "success")
    return redirect(url_for("photos.gallery"))



def _bool_arg(name: str) -> bool | None:
    value = request.args.get(name)
    if value is None or value == "":
        return None
    return value.lower() in {"1", "true", "yes", "on"}



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
        "tags": [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
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
            "processing_status": p.processing_status
        }
        
    return {"statuses": statuses}


@photos_bp.route("/api/<int:photo_id>/metadata", methods=["POST"])
@login_required
def api_save_metadata(photo_id: int):
    """JSON endpoint used by the gallery side-panel to save title, description and tags."""
    payload = request.get_json(silent=True) or {}
    NoteService().upsert(
        current_user.id,
        photo_id,
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        personal_notes=payload.get("personal_notes", ""),
    )
    # Handle tags if provided
    raw_tags = payload.get("tags", [])
    if isinstance(raw_tags, list):
        from app.application.services.catalog_service import TagService
        TagService().set_tags(current_user.id, photo_id, raw_tags)
    return {"status": "ok"}
