"""Secure image upload validation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

from app.domain.exceptions.domain_exceptions import ValidationError

MAGIC_NUMBERS = {
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],
}


class UploadValidator:
    """Validate extension, MIME type, magic bytes, and Pillow integrity."""

    def __init__(self, allowed_extensions: set[str], allowed_mime_types: set[str]) -> None:
        self.allowed_extensions = allowed_extensions
        self.allowed_mime_types = allowed_mime_types

    def validate(self, upload: FileStorage) -> tuple[str, int, int]:
        if not upload or not upload.filename:
            raise ValidationError("Choose an image to upload.")
        extension = Path(upload.filename).suffix.lower().lstrip(".")
        if extension not in self.allowed_extensions:
            raise ValidationError("Only JPG, PNG and WEBP images are allowed.")
        if upload.mimetype not in self.allowed_mime_types:
            raise ValidationError("Unsupported image MIME type.")

        head = upload.stream.read(16)
        upload.stream.seek(0)
        if not any(head.startswith(prefix) for prefix in MAGIC_NUMBERS[extension]):
            raise ValidationError("File signature does not match the extension.")

        try:
            image = Image.open(upload.stream)
            image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError("The file is not a valid image.") from exc
        finally:
            upload.stream.seek(0)

        with Image.open(upload.stream) as image:
            image_format = image.format or extension.upper()
            width, height = image.size
        upload.stream.seek(0)
        return image_format.upper(), width, height

