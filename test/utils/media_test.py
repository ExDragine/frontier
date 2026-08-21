# ruff: noqa: S101

import base64
from io import BytesIO

from PIL import Image

from utils.media import (
    detect_mime_type,
    inline_media_bytes,
    media_block_kind,
    normalize_image_for_model,
    resolve_media,
    standard_media_block,
)


def _image_bytes(format_name: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (2, 2), "red").save(buffer, format=format_name)
    return buffer.getvalue()


def test_detect_mime_type_uses_image_content_instead_of_declared_type():
    payload = _image_bytes("PNG")

    assert detect_mime_type(payload, kind="image", declared_mime="image/jpeg") == "image/png"
    assert resolve_media(payload, "image").extension == ".png"


def test_detect_mime_type_recognizes_common_binary_signatures():
    assert detect_mime_type(b"%PDF-1.7\n", kind="file") == "application/pdf"
    assert detect_mime_type(b"RIFF" + b"\x00" * 4 + b"WAVE", kind="audio") == "audio/wav"
    assert detect_mime_type(b"#!AMR\nvoice", kind="audio") == "audio/amr"
    assert detect_mime_type(b"\x02#!SILK_V3voice", kind="audio") == "audio/silk"
    assert detect_mime_type(b"\x00\x00\x00\x18ftypisom", kind="video") == "video/mp4"
    assert detect_mime_type(b"\x00\x00\x00\x18ftypavif", kind="image") == "image/avif"


def test_standard_block_and_legacy_blocks_decode_to_same_bytes():
    payload = _image_bytes("JPEG")
    standard = standard_media_block(resolve_media(payload, "image"))
    legacy = {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(payload).decode()}"},
    }

    assert standard["type"] == "image"
    assert inline_media_bytes(standard) == (payload, "image/jpeg")
    assert inline_media_bytes(legacy) == (payload, "image/jpeg")
    assert media_block_kind(legacy) == "image"


def test_legacy_video_url_remains_supported():
    payload = b"video"
    block = {
        "type": "video_url",
        "video_url": {"url": f"data:video/mp4;base64,{base64.b64encode(payload).decode()}"},
    }

    assert media_block_kind(block) == "video"
    assert inline_media_bytes(block) == (payload, "video/mp4")


def test_normalize_image_for_model_preserves_supported_image():
    payload = _image_bytes("PNG")

    normalized = normalize_image_for_model(payload)

    assert normalized is not None
    assert normalized.data == payload
    assert normalized.mime_type == "image/png"


def test_normalize_image_for_model_converts_unsupported_image():
    payload = _image_bytes("BMP")

    normalized = normalize_image_for_model(payload)

    assert normalized is not None
    assert normalized.mime_type == "image/jpeg"
    assert normalized.data.startswith(b"\xff\xd8\xff")


def test_normalize_image_for_model_rejects_invalid_bytes():
    assert normalize_image_for_model(b"not-an-image") is None
