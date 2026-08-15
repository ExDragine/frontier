from __future__ import annotations

# ruff: noqa: S101
import base64
import hashlib

import pytest

from scripts.sync_lobehub_model_names import _extract_models, _verify_integrity


def test_extract_models_reads_static_display_names_without_crossing_model_boundaries() -> None:
    source = """
    const models = [{
      displayName: "First Model",
      id: "first-model",
      type: "chat"
    }, {
      displayName: "Second \\u6a21型",
      id: "second/model",
      type: "image"
    }];
    """

    assert _extract_models(source) == {
        "first-model": "First Model",
        "second/model": "Second 模型",
    }


def test_extract_models_rejects_conflicting_names() -> None:
    source = """
    const models = [
      { displayName: "First Name", id: "same-model" },
      { displayName: "Second Name", id: "same-model" },
    ];
    """

    with pytest.raises(ValueError, match="conflicting display names"):
        _extract_models(source)


def test_verify_integrity_accepts_matching_sha512_and_rejects_mismatch() -> None:
    archive = b"model-bank archive"
    digest = base64.b64encode(hashlib.sha512(archive).digest()).decode("ascii")

    _verify_integrity(archive, f"sha512-{digest}")
    with pytest.raises(ValueError, match="integrity verification failed"):
        _verify_integrity(archive, "sha512-invalid")
