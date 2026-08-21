"""Provider-neutral helpers for message media and LangChain content blocks."""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from PIL import Image as PILImage
from PIL import ImageOps

MediaKind = Literal["image", "audio", "video", "file"]

_IMAGE_FORMAT_MIME = {
    "AVIF": "image/avif",
    "GIF": "image/gif",
    "HEIF": "image/heif",
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
MODEL_IMAGE_MIME_TYPES = frozenset({"image/gif", "image/jpeg", "image/png", "image/webp"})
_MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "audio/aac": ".aac",
    "audio/aiff": ".aiff",
    "audio/flac": ".flac",
    "audio/amr": ".amr",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
    "audio/silk": ".silk",
    "audio/wav": ".wav",
    "image/avif": ".avif",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "image/heif": ".heif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/3gpp": ".3gpp",
    "video/avi": ".avi",
    "video/mp4": ".mp4",
    "video/mpeg": ".mpeg",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-flv": ".flv",
    "video/x-ms-wmv": ".wmv",
}


@dataclass(frozen=True, slots=True)
class ResolvedMedia:
    """Downloaded media with enough metadata for storage and model input."""

    kind: MediaKind
    data: bytes
    mime_type: str
    extension: str
    file_name: str | None = None


def _clean_declared_mime(value: str | None) -> str | None:
    if not value:
        return None
    mime = value.split(";", 1)[0].strip().lower()
    return mime if "/" in mime else None


def _image_mime(data: bytes) -> str | None:
    try:
        with PILImage.open(BytesIO(data)) as image:
            return _IMAGE_FORMAT_MIME.get(str(image.format or "").upper())
    except Exception:
        return None


def _magic_mime(data: bytes) -> str | None:
    signatures = (
        (b"%PDF-", "application/pdf"),
        (b"#!AMR\n", "audio/amr"),
        (b"#!AMR-WB\n", "audio/amr"),
        (b"\x02#!SILK_V3", "audio/silk"),
        (b"ID3", "audio/mpeg"),
        (b"\xff\xfb", "audio/mpeg"),
        (b"\xff\xf3", "audio/mpeg"),
        (b"\xff\xf2", "audio/mpeg"),
        (b"fLaC", "audio/flac"),
        (b"OggS", "audio/ogg"),
        (b"\x1aE\xdf\xa3", "video/webm"),
        (b"FLV", "video/x-flv"),
    )
    if match := next((mime for prefix, mime in signatures if data.startswith(prefix)), None):
        return match
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "audio/wav"
    if data.startswith(b"RIFF") and data[8:12] == b"AVI ":
        return "video/avi"
    if data.startswith((b"\xff\xf1", b"\xff\xf9")):
        return "audio/aac"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in {b"avif", b"avis"}:
            return "image/avif"
        if brand in {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"}:
            return "image/heic"
        if brand in {b"M4A ", b"M4B ", b"M4P "}:
            return "audio/mp4"
        if brand == b"qt  ":
            return "video/quicktime"
        return "video/mp4"
    return None


def detect_mime_type(
    data: bytes,
    *,
    kind: MediaKind | None = None,
    declared_mime: str | None = None,
    file_name: str | None = None,
) -> str:
    """Detect a useful MIME type without trusting any single external hint."""
    if image_mime := _image_mime(data):
        return image_mime
    if magic_mime := _magic_mime(data):
        return magic_mime

    declared = _clean_declared_mime(declared_mime)
    if declared and declared != "application/octet-stream":
        return declared
    if file_name:
        guessed, _ = mimetypes.guess_type(file_name)
        if guessed:
            return guessed
    if kind:
        return {
            "image": "image/jpeg",
            "audio": "application/octet-stream",
            "video": "application/octet-stream",
            "file": "application/octet-stream",
        }[kind]
    return "application/octet-stream"


def extension_for_mime(mime_type: str, *, fallback_name: str | None = None) -> str:
    if extension := _MIME_EXTENSIONS.get(mime_type.lower()):
        return extension
    if fallback_name and (suffix := Path(fallback_name).suffix):
        return suffix.lower()
    guessed = mimetypes.guess_extension(mime_type, strict=False)
    return guessed or ".bin"


def resolve_media(
    data: bytes,
    kind: MediaKind,
    *,
    declared_mime: str | None = None,
    file_name: str | None = None,
) -> ResolvedMedia:
    mime_type = detect_mime_type(
        data,
        kind=kind,
        declared_mime=declared_mime,
        file_name=file_name,
    )
    return ResolvedMedia(
        kind=kind,
        data=data,
        mime_type=mime_type,
        extension=extension_for_mime(mime_type, fallback_name=file_name),
        file_name=file_name,
    )


def normalize_image_for_model(data: bytes) -> ResolvedMedia | None:
    """Validate an image and convert unsupported formats for model APIs.

    Responses-compatible providers accept GIF, JPEG, PNG, and WebP. Supported
    input is preserved byte-for-byte after Pillow validates it; other decodable
    formats are converted to PNG when they contain transparency, otherwise JPEG.
    Invalid image bytes return ``None`` so one bad attachment can't fail the
    entire model request.
    """
    try:
        with PILImage.open(BytesIO(data)) as image:
            image_format = str(image.format or "").upper()
            image.verify()

        mime_type = _IMAGE_FORMAT_MIME.get(image_format)
        if mime_type in MODEL_IMAGE_MIME_TYPES:
            return ResolvedMedia(
                kind="image",
                data=data,
                mime_type=mime_type,
                extension=extension_for_mime(mime_type),
            )

        with PILImage.open(BytesIO(data)) as image:
            image.seek(0)
            normalized = ImageOps.exif_transpose(image)
            normalized.load()
            has_alpha = normalized.mode in {"LA", "RGBA"} or "transparency" in normalized.info
            output = BytesIO()
            if has_alpha:
                normalized.convert("RGBA").save(output, format="PNG")
                converted_mime = "image/png"
            else:
                normalized.convert("RGB").save(output, format="JPEG", quality=90)
                converted_mime = "image/jpeg"
        return ResolvedMedia(
            kind="image",
            data=output.getvalue(),
            mime_type=converted_mime,
            extension=extension_for_mime(converted_mime),
        )
    except (OSError, SyntaxError, ValueError):
        return None


def standard_media_block(media: ResolvedMedia) -> dict[str, Any]:
    """Build a LangChain standard content block from inline bytes."""
    return {
        "type": media.kind,
        "base64": base64.b64encode(media.data).decode(),
        "mime_type": media.mime_type,
    }


def media_block_kind(block: Any) -> MediaKind | None:
    """Return a standard kind for standard and legacy OpenAI media blocks."""
    if not isinstance(block, dict):
        return None
    block_type = block.get("type")
    if block_type == "image_url":
        return "image"
    if block_type == "audio_url":
        return "audio"
    if block_type == "video_url":
        return "video"
    if block_type in {"image", "audio", "video", "file"}:
        return block_type
    return None


def inline_media_bytes(block: Any) -> tuple[bytes, str] | None:
    """Decode inline standard or legacy content without fetching remote URLs."""
    if not isinstance(block, dict):
        return None
    if isinstance(block.get("base64"), str):
        try:
            return base64.b64decode(block["base64"], validate=True), str(
                block.get("mime_type") or "application/octet-stream"
            )
        except ValueError:
            return None

    block_type = block.get("type")
    value = block.get(block_type) if block_type in {"image_url", "audio_url", "video_url"} else block.get("url")
    if isinstance(value, dict):
        value = value.get("url")
    if not isinstance(value, str) or not value.startswith("data:") or "," not in value:
        return None
    header, payload = value.split(",", 1)
    if ";base64" not in header:
        return None
    try:
        return base64.b64decode(payload, validate=True), header.removeprefix("data:").split(";", 1)[0]
    except ValueError:
        return None
