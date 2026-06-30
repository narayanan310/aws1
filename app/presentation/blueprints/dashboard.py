"""Dashboard blueprint."""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.application.services.catalog_service import DashboardService
from app.infrastructure.database.models import Photo

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    summary = DashboardService().summary(current_user.id)
    recent = (
        Photo.query.filter_by(owner_id=current_user.id, deleted=False)
        .order_by(Photo.uploaded_at.desc())
        .limit(8)
        .all()
    )
    return render_template("dashboard/index.html", summary=summary, recent=recent)

from flask import request
from app.extensions import db

@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        payload = request.get_json()
        if payload:
            current_user.settings = payload
            db.session.commit()
            return {"status": "success"}
        return {"status": "error", "message": "Invalid JSON"}, 400
        
    return render_template("dashboard/settings.html", settings=current_user.settings or {})

