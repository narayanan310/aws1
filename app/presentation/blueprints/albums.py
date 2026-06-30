"""Album blueprint."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.application.services.catalog_service import AlbumService
from app.infrastructure.repositories.catalog_repository import CatalogRepository

albums_bp = Blueprint("albums", __name__, url_prefix="/albums")


@albums_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    service = AlbumService()
    if request.method == "POST":
        service.create(
            current_user.id,
            request.form.get("name", ""),
            request.form.get("description", ""),
            request.form.get("parent_id", type=int),
        )
        flash("Album created.", "success")
        return redirect(url_for("albums.index"))
    albums = CatalogRepository().albums(current_user.id)
    return render_template("albums/index.html", albums=albums)

@albums_bp.route("/<int:album_id>/add/<int:photo_id>", methods=["POST"])
@login_required
def add_photo(album_id: int, photo_id: int):
    AlbumService().add_photo(current_user.id, album_id, photo_id)
    flash("Photo added to album.", "success")
    return redirect(url_for("photos.detail", photo_id=photo_id))

