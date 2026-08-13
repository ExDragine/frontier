# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
async def test_webpage_screenshot_exposes_standard_image_block_to_vision_model(load_tool_module, monkeypatch):
    module = load_tool_module("webpage_screenshot")

    async def fake_screenshot(*_args, **_kwargs):
        return b"image-bytes"

    monkeypatch.setattr(module, "screenshot", fake_screenshot)
    monkeypatch.setattr(module, "model_supports", lambda *_args, **_kwargs: True)

    content, artifact = await module.webpage_screenshot("https://example.test")

    assert content[0] == {"type": "text", "text": "网页截图完成: https://example.test"}
    assert content[1]["type"] == "image"
    assert content[1]["base64"]
    assert content[1]["mime_type"] == "image/jpeg"
    assert artifact is not None


@pytest.mark.asyncio
async def test_webpage_screenshot_keeps_tool_content_text_only_for_non_vision_model(load_tool_module, monkeypatch):
    module = load_tool_module("webpage_screenshot")

    async def fake_screenshot(*_args, **_kwargs):
        return b"image-bytes"

    monkeypatch.setattr(module, "screenshot", fake_screenshot)
    monkeypatch.setattr(module, "model_supports", lambda *_args, **_kwargs: False)

    content, artifact = await module.webpage_screenshot("https://example.test")

    assert content == "网页截图完成: https://example.test"
    assert artifact is not None
