# ruff: noqa: S101

import asyncio

import pytest

from utils import message
from utils.alconna import Image, Text, UniMessage


@pytest.mark.asyncio
async def test_artifacts_preserve_captions_and_order_and_ignore_structured_results(monkeypatch):
    sent = []

    async def send(self):
        sent.append(list(self))

    monkeypatch.setattr(UniMessage, "send", send)
    first = [Text("first"), Image(raw=b"1"), Text("second"), Image(raw=b"2"), Text("tail")]
    last = UniMessage.image(raw=b"3")
    result = await message.send_artifacts([UniMessage(first), {"structured": True}, last])

    assert [segment for batch in sent for segment in batch] == [*first, *last]
    assert all(sum(isinstance(segment, Image) for segment in batch) <= 1 for batch in sent)
    assert result.successful
    assert result.attempted == result.sent == 3


@pytest.mark.asyncio
async def test_artifact_failure_reports_partial_delivery_and_stops_queue(monkeypatch):
    sent = []

    async def send(self):
        raw = self[0].raw
        sent.append(raw)
        if raw == b"2":
            raise RuntimeError("transport unavailable")

    monkeypatch.setattr(UniMessage, "send", send)
    result = await message.send_artifacts([UniMessage.image(raw=data) for data in (b"1", b"2", b"3")])

    assert sent == [b"1", b"2"]
    assert result.attempted == 2
    assert result.sent == 1
    assert result.errors == ("RuntimeError",)
    assert not result.successful


@pytest.mark.asyncio
async def test_text_delivery_failure_can_recover_with_image(monkeypatch):
    calls = []

    async def text(content):
        return content

    async def render(_content):
        return b"image"

    async def send(self):
        calls.append(self[0].type)
        if isinstance(self[0], Text):
            raise RuntimeError("text rejected")

    monkeypatch.setattr(UniMessage, "send", send)
    monkeypatch.setattr(message, "markdown_to_text", text)
    monkeypatch.setattr(message, "_markdown_to_image_with_retry", render)
    result = await message.send_messages(None, 1, {"messages": ["hi"]})

    assert calls == ["text", "image"]
    assert result.successful


@pytest.mark.asyncio
async def test_error_notification_is_not_successful_delivery_of_requested_content(monkeypatch):
    calls = []

    async def render(_content):
        return None

    async def send(self):
        calls.append(str(self))

    monkeypatch.setattr(UniMessage, "send", send)
    monkeypatch.setattr(message, "_markdown_to_image_with_retry", render)
    result = await message.send_messages(None, 1, {"messages": ["long" * 500]})

    assert len(calls) == 1
    assert "消息生成失败" in calls[0]
    assert result.sent == 0
    assert result.errors == ("render_failed",)
    assert not result.successful


@pytest.mark.asyncio
async def test_delivery_cancellation_propagates(monkeypatch):
    async def send(self):
        raise asyncio.CancelledError

    monkeypatch.setattr(UniMessage, "send", send)
    with pytest.raises(asyncio.CancelledError):
        await message.send_artifacts([UniMessage.image(raw=b"1")])
