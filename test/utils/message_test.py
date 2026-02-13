# ruff: noqa: S101

import ast
import types

import pytest

from utils import message as message_module


class DummyUniMessage:
    def __init__(self, content=None):
        self.content = content
        self.sent = False

    def __add__(self, other):
        return DummyUniMessage((self.content, other.content))

    async def send(self, *args, **kwargs):
        self.sent = True
        return None

    @classmethod
    def reply(cls, *_args, **_kwargs):
        return cls("reply")

    @classmethod
    def text(cls, text):
        return cls(text)

    @classmethod
    def image(cls, raw=None):
        return cls(raw)


class DummyResponse:
    def __init__(self, content=b"data"):
        self.content = content


@pytest.mark.asyncio
async def test_message_extract(monkeypatch):
    async def fake_get(_url):
        return DummyResponse()

    monkeypatch.setattr(message_module.httpx_client, "get", fake_get)

    segments = [
        {"type": "text", "data": {"text": "hi"}},
        {"type": "mention", "data": {"user_id": "1"}},
        {"type": "image", "data": {"temp_url": "http://img"}},
        {"type": "record", "data": {"temp_url": "http://aud", "duration": 3}},
        {"type": "video", "data": {"temp_url": "http://vid", "duration": 1}},
        {"type": "file", "data": {"file_name": "a.txt", "file_size": 10}},
    ]
    text, images, audio, video = await message_module.message_extract(segments)
    assert "hi" in text
    assert images
    assert audio
    assert video


@pytest.mark.asyncio
async def test_send_messages_fallback_to_text(monkeypatch):
    monkeypatch.setattr(message_module, "UniMessage", DummyUniMessage)

    async def fake_markdown_to_text(content):
        return content

    monkeypatch.setattr(message_module, "markdown_to_text", fake_markdown_to_text)

    async def fake_markdown_to_image(_content):
        return None

    monkeypatch.setattr(message_module, "markdown_to_image", fake_markdown_to_image)
    response = {"messages": [types.SimpleNamespace(content=str({"content": "hello"}))]}
    await message_module.send_messages(group_id=None, message_id=1, response=response)


@pytest.mark.asyncio
async def test_message_gateway_blacklist(monkeypatch):
    class DummyEvent:
        def __init__(self):
            self.data = types.SimpleNamespace(group=types.SimpleNamespace(group_id=1))

        def get_user_id(self):
            return "user"

        def is_tome(self):
            return False

        def get_plaintext(self):
            return "hello"

        to_me = False

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [1])
    result = await message_module.message_gateway(DummyEvent(), [])
    assert result is False


@pytest.mark.asyncio
async def test_message_check_text(monkeypatch):
    async def fake_predict(text):
        return "Safe", []

    monkeypatch.setattr(message_module.text_det, "predict", fake_predict)
    result = await message_module.message_check("hello", None)
    assert result == "Safe"
