"""Image processing service using Pillow and OpenCV."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from loguru import logger
import boto3
from flask import current_app

from app.domain.entities.enums import PhotoStatus
from app.extensions import db
from app.infrastructure.database.models import Photo, User
from app.infrastructure.storage.local_storage import LocalStorageService


class ImageProcessingService:
    """Generate derivatives and technical metadata."""

    def __init__(self) -> None:
        self.storage = LocalStorageService()

    def process(self, photo: Photo) -> Photo:
        user = db.session.get(User, photo.owner_id)
        if not user:
            raise ValueError("Photo owner not found")
        photo.processing_status = PhotoStatus.PROCESSING.value
        db.session.flush()

        source = Path(photo.original_path)
        stem = source.stem
        preview_path = self.storage.derivative_path(user.uuid, "preview", stem)
        thumbnail_path = self.storage.derivative_path(user.uuid, "thumbnail", stem)
        compressed_path = self.storage.derivative_path(user.uuid, "compressed", stem)

        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)
            photo.width, photo.height = image.size
            photo.format = image.format or photo.format
            photo.exif_metadata = self._extract_exif(image)
            photo.camera = self._camera(photo.exif_metadata)
            photo.lens = str(photo.exif_metadata.get("LensModel", "") or "")
            photo.iso = str(photo.exif_metadata.get("ISOSpeedRatings", "") or "")
            photo.exposure = str(photo.exif_metadata.get("ExposureTime", "") or "")

            rgb = image.convert("RGB")
            preview = rgb.copy()
            preview.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            preview.save(preview_path, "JPEG", quality=86, optimize=True)

            thumb = rgb.copy()
            thumb.thumbnail((320, 320), Image.Resampling.LANCZOS)
            thumb.save(thumbnail_path, "JPEG", quality=82, optimize=True)

            compressed = rgb.copy()
            compressed.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            compressed.save(compressed_path, "JPEG", quality=78, optimize=True)

        photo.preview_path = str(preview_path)
        photo.thumbnail_path = str(thumbnail_path)
        photo.compressed_path = str(compressed_path)
        photo.histogram = self._histogram(source)
        photo.blur_score = self._blur_score(source)
        palette = self._palette(source)
        photo.color_palette = palette
        photo.dominant_colors = palette[:5]
        photo.processing_status = PhotoStatus.PROCESSED.value
        
        # upload to S3 if configured
        if current_app.config.get('S3_BUCKET_NAME'):
            s3_orig = self._upload_to_s3(source, user.uuid, "original")
            if s3_orig:
                photo.original_path = s3_orig
            s3_prev = self._upload_to_s3(preview_path, user.uuid, "preview")
            if s3_prev:
                photo.preview_path = s3_prev
            s3_thumb = self._upload_to_s3(thumbnail_path, user.uuid, "thumbnail")
            if s3_thumb:
                photo.thumbnail_path = s3_thumb
            s3_comp = self._upload_to_s3(compressed_path, user.uuid, "compressed")
            if s3_comp:
                photo.compressed_path = s3_comp
                
        logger.bind(channel="processing").info("Processed photo {}", photo.uuid)
        return photo

    def _upload_to_s3(self, path: Path, user_uuid: str, kind: str) -> str | None:
        bucket = current_app.config.get('S3_BUCKET_NAME')
        if not bucket:
            return None
        region = current_app.config.get('S3_REGION', 'us-east-1')
        s3_client = boto3.client('s3', region_name=region)
        s3_key = f"users/{user_uuid}/{kind}/{path.name}"
        content_type = "image/jpeg"
        if kind == "original":
            import mimetypes
            content_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        with open(path, 'rb') as f:
            s3_client.upload_fileobj(f, bucket, s3_key, ExtraArgs={"ContentType": content_type})
        return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"

    def _extract_exif(self, image: Image.Image) -> dict:
        exif = image.getexif()
        return {str(key): str(value) for key, value in exif.items()} if exif else {}

    def _camera(self, exif: dict) -> str:
        make = exif.get("271", "")
        model = exif.get("272", "")
        return " ".join(part for part in (make, model) if part).strip()

    def _histogram(self, path: Path) -> dict:
        image = cv2.imread(str(path))
        if image is None:
            return {}
        channels = cv2.split(image)
        names = ("blue", "green", "red")
        return {
            name: cv2.calcHist([channel], [0], None, [16], [0, 256]).flatten().astype(int).tolist()
            for name, channel in zip(names, channels, strict=True)
        }

    def _blur_score(self, path: Path) -> float:
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            return 0.0
        return float(cv2.Laplacian(image, cv2.CV_64F).var())

    def _palette(self, path: Path) -> list[str]:
        with Image.open(path) as image:
            small = image.convert("RGB").resize((80, 80))
            arr = np.array(small).reshape((-1, 3)).astype(np.float32)
            _, labels, centers = cv2.kmeans(
                arr,
                8,
                None,
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                3,
                cv2.KMEANS_PP_CENTERS,
            )
            counts = np.bincount(labels.flatten())
            ordered = centers[np.argsort(counts)[::-1]].astype(int)
            return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in ordered]

