"""Error handlers."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from loguru import logger

from app.domain.exceptions.domain_exceptions import AuthorizationError, NotFoundError, ValidationError

errors_bp = Blueprint("errors", __name__)


def wants_json() -> bool:
    return request.path.startswith("/api/") or "application/json" in request.accept_mimetypes


@errors_bp.app_errorhandler(ValidationError)
def validation_error(error):
    return _error(error, 400)


@errors_bp.app_errorhandler(AuthorizationError)
def authorization_error(error):
    return _error(error, 403)


@errors_bp.app_errorhandler(NotFoundError)
def not_found_error(error):
    return _error(error, 404)


@errors_bp.app_errorhandler(403)
def forbidden(error):
    return _error(error, 403)


@errors_bp.app_errorhandler(404)
def not_found(error):
    return _error(error, 404)


@errors_bp.app_errorhandler(429)
def rate_limited(error):
    return _error("Too many requests. Please slow down.", 429)


@errors_bp.app_errorhandler(500)
def server_error(error):
    logger.exception("Unhandled server error")
    return _error("Something went wrong.", 500)


def _error(error, status: int):
    message = str(error)
    if wants_json():
        return jsonify({"ok": False, "error": {"message": message, "status": status}}), status
    template = f"errors/{status}.html" if status in {403, 404, 429, 500} else "errors/generic.html"
    return render_template(template, message=message, status=status), status

