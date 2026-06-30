"""Application factory for AI Photo Manager."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from flask import Flask, abort, session
from flask_login import current_user

from config import BaseConfig, get_config

from app.extensions import csrf, db, login_manager
from app.infrastructure.database.models import User
from app.infrastructure.logging.logging_config import configure_logging
from app.infrastructure.security.rate_limiter import rate_limiter
from app.presentation.blueprints.albums import albums_bp
from app.presentation.blueprints.auth import auth_bp
from app.presentation.blueprints.dashboard import dashboard_bp
from app.presentation.blueprints.errors import errors_bp
from app.presentation.blueprints.photos import photos_bp
from app.presentation.blueprints.api import api_bp
from app.utils.files import format_bytes


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """Create the Flask app."""

    app = Flask(__name__, template_folder="presentation/templates", static_folder="presentation/static")
    app.config.from_object(config_class or get_config())

    _ensure_dirs(app)
    configure_logging(app.config["LOG_DIR"], app.config["LOG_LEVEL"])
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    app.jinja_env.filters["bytes"] = format_bytes

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    @app.before_request
    def apply_security_controls() -> None:
        if not rate_limiter.check():
            abort(429)
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=app.config["SESSION_TIMEOUT_MINUTES"])
        if current_user.is_authenticated:
            session.modified = True

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(photos_bp)
    app.register_blueprint(albums_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(errors_bp)

    with app.app_context():
        db.create_all()
    return app


def _ensure_dirs(app: Flask) -> None:
    Path(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")).parent.mkdir(
        parents=True, exist_ok=True
    )
    app.config["UPLOAD_ROOT"].mkdir(parents=True, exist_ok=True)
    app.config["LOG_DIR"].mkdir(parents=True, exist_ok=True)

