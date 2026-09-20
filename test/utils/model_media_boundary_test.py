# ruff: noqa: S101

import base64
from io import BytesIO
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage, ToolMessage
from PIL import Image

from utils.agents import inputs
from utils.media import inline_media_bytes, normalize_image_for_model


def encoded(format_name):
    stream = BytesIO()
    Image.new("RGB", (16, 16), "red").save(stream, format=format_name)
    return stream.getvalue()


@pytest.mark.asyncio
async def test_boundary_normalizes_tool_and_restored_messages_without_mutation(monkeypatch):
    monkeypatch.setattr(inputs, "model_supports", lambda *_args, **_kwargs: True)
    raw = encoded("BMP")
    content = [{"type": "input_image", "image_url": "data:image/png;base64," + base64.b64encode(raw).decode()}]
    messages = [HumanMessage(content=content, id="restored"), ToolMessage(content=content, tool_call_id="read-image", id="tool")]
    request = SimpleNamespace(messages=messages, override=lambda **kwargs: SimpleNamespace(**kwargs))
    captured = []

    async def handler(updated):
        captured.extend(updated.messages)
        return "ok"

    middleware = inputs.ModelMediaMiddleware("test")
    assert await middleware.awrap_model_call(request, handler) == "ok"
    assert captured[1].tool_call_id == "read-image"
    assert [message.id for message in captured] == ["restored", "tool"]
    for message in captured:
        data, mime = inline_media_bytes(message.content[0])
        assert mime == "image/jpeg"
        with Image.open(BytesIO(data)) as image:
            image.load()
            assert image.format == "JPEG"
    assert messages[0].content == content
    assert messages[1].content == content


def test_truncated_jpeg_is_rejected_even_when_verify_accepts_header():
    damaged = encoded("JPEG")[:-10]
    with Image.open(BytesIO(damaged)) as image:
        image.verify()
    assert normalize_image_for_model(damaged) is None
