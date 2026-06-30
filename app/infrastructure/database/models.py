"""SQLAlchemy persistence models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.extensions import db


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


from flask_login import UserMixin

class User(UserMixin, db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True))
    last_login_at = db.Column(db.DateTime(timezone=True))
    settings = db.Column(db.JSON, default=dict, nullable=False)

    @property
    def is_active(self) -> bool:
        return self.is_active_account

    def get_id(self) -> str:
        return str(self.id)


class Photo(db.Model, TimestampMixin):
    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    sha256 = db.Column(db.String(64), nullable=False, index=True)
    checksum = db.Column(db.String(64), nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    format = db.Column(db.String(20))
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    thumbnail_path = db.Column(db.String(500))
    preview_path = db.Column(db.String(500))
    compressed_path = db.Column(db.String(500))
    original_path = db.Column(db.String(500), nullable=False)
    exif_metadata = db.Column(db.JSON, default=dict, nullable=False)
    gps = db.Column(db.JSON, default=dict, nullable=False)
    camera = db.Column(db.String(255))
    lens = db.Column(db.String(255))
    iso = db.Column(db.String(50))
    exposure = db.Column(db.String(80))
    favorite = db.Column(db.Boolean, default=False, nullable=False, index=True)
    archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    visibility = db.Column(db.String(30), default="private", nullable=False)
    processing_status = db.Column(db.String(50), default="pending", nullable=False, index=True)
    ai_status = db.Column(db.String(50), default="not_analyzed", nullable=False, index=True)
    histogram = db.Column(db.JSON, default=dict, nullable=False)
    blur_score = db.Column(db.Float)
    color_palette = db.Column(db.JSON, default=list, nullable=False)
    dominant_colors = db.Column(db.JSON, default=list, nullable=False)

    owner = db.relationship("User", backref=db.backref("photos", lazy="dynamic"))
    __table_args__ = (
        db.Index("ix_photos_owner_deleted_uploaded", "owner_id", "deleted", "uploaded_at"),
        db.Index("ix_photos_owner_favorite", "owner_id", "favorite"),
        db.Index("ix_photos_owner_archived", "owner_id", "archived"),
    )


class Album(db.Model, TimestampMixin):
    __tablename__ = "albums"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("albums.id"))
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    cover_photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"))
    ai_suggested = db.Column(db.Boolean, default=False, nullable=False)


class AlbumPhoto(db.Model):
    __tablename__ = "album_photos"

    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"), primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    added_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class PhotoNote(db.Model, TimestampMixin):
    __tablename__ = "photo_notes"

    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    personal_notes = db.Column(db.Text)
    ai_notes = db.Column(db.Text)
    markdown_enabled = db.Column(db.Boolean, default=True, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)


class PhotoNoteVersion(db.Model):
    __tablename__ = "photo_note_versions"

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("photo_notes.id"), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    personal_notes = db.Column(db.Text)
    ai_notes = db.Column(db.Text)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Tag(db.Model, TimestampMixin):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    normalized_name = db.Column(db.String(120), nullable=False, index=True)
    ai_generated = db.Column(db.Boolean, default=False, nullable=False)
    __table_args__ = (db.UniqueConstraint("owner_id", "normalized_name", name="uq_owner_tag"),)


class PhotoTag(db.Model):
    __tablename__ = "photo_tags"

    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    ai_generated = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Favorite(db.Model):
    __tablename__ = "favorites"

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Trash(db.Model):
    __tablename__ = "trash"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), nullable=False, index=True)
    deleted_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    purge_after = db.Column(db.DateTime(timezone=True))


class AIResult(db.Model, TimestampMixin):
    __tablename__ = "ai_results"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), nullable=False, index=True)
    status = db.Column(db.String(30), default="draft", nullable=False, index=True)
    title = db.Column(db.String(255))
    caption = db.Column(db.Text)
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    suggested_album = db.Column(db.String(255))
    keywords = db.Column(db.JSON, default=list, nullable=False)
    objects = db.Column(db.JSON, default=list, nullable=False)
    scene_type = db.Column(db.String(120))
    environment = db.Column(db.String(120))
    weather = db.Column(db.String(120))
    mood = db.Column(db.String(120))
    photography_style = db.Column(db.String(120))
    indoor_outdoor = db.Column(db.String(40))
    time_of_day = db.Column(db.String(80))
    possible_event = db.Column(db.String(160))
    ocr_text = db.Column(db.Text)
    confidence = db.Column(db.Float, default=0.0, nullable=False)
    raw = db.Column(db.JSON, default=dict, nullable=False)


class Embedding(db.Model, TimestampMixin):
    __tablename__ = "embeddings"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), nullable=False, index=True)
    model_name = db.Column(db.String(120), nullable=False)
    vector = db.Column(db.JSON, nullable=False)
    dimension = db.Column(db.Integer, nullable=False)


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    message = db.Column(db.String(500), nullable=False)
    log_metadata = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class SessionRecord(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(80))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True))


class ProcessingQueue(db.Model):
    __tablename__ = "processing_queue"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), nullable=False, index=True)
    task_type = db.Column(db.String(80), nullable=False, index=True)
    status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    max_attempts = db.Column(db.Integer, default=3, nullable=False)
    error_message = db.Column(db.Text)
    payload = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(120), nullable=False, index=True)
    resource_type = db.Column(db.String(120), nullable=False)
    resource_id = db.Column(db.String(120))
    ip_address = db.Column(db.String(80))
    user_agent = db.Column(db.String(500))
    outcome = db.Column(db.String(40), nullable=False)
    log_metadata = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class EmailVerificationToken(db.Model):
    __tablename__ = "email_verification_tokens"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(80), index=True)
    successful = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

