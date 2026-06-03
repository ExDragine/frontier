# ruff: noqa: S101

import importlib
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
async def test_send_messages_retries_image_render(monkeypatch):
    monkeypatch.setattr(message_module, "UniMessage", DummyUniMessage)

    calls = 0
    sleeps = []

    async def fake_markdown_to_image(_content):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("render failed")
        return b"img"

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(message_module, "markdown_to_image", fake_markdown_to_image)
    monkeypatch.setattr(message_module.asyncio, "sleep", fake_sleep)

    response = {"messages": [types.SimpleNamespace(content=str({"content": "x" * 500}))]}
    await message_module.send_messages(group_id=None, message_id=1, response=response)

    assert calls == 2
    assert sleeps == [message_module.MESSAGE_IMAGE_RENDER_RETRY_DELAY_SECONDS]


@pytest.mark.parametrize(
    "content",
    [
        "短公式应该渲染成图片：$E = mc^2$",
        "块级公式应该渲染成图片：\n$$\n\\int_0^1 x^2 dx\n$$",
        "LaTeX 括号公式应该渲染成图片：\\[a^2 + b^2 = c^2\\]",
        "| 名称 | 数值 |\n| --- | ---: |\n| alpha | 1 |",
        "```mermaid\ngraph TD\nA --> B\n```",
        "flowchart LR\nA[开始] --> B[结束]",
    ],
)
def test_message_should_render_image_for_hard_to_text_content(content):
    assert message_module._message_should_render_as_image(content) is True


@pytest.mark.parametrize(
    "content",
    [
        "普通短消息继续走文本",
        "The price is $5 today.",
        "Use `echo hello` in shell.",
    ],
)
def test_message_keeps_simple_short_content_as_text(content):
    assert message_module._message_should_render_as_image(content) is False


def test_message_renders_long_simple_content_as_image_for_any_group():
    assert message_module._message_should_render_as_image("x" * 600) is True


def test_extract_message_text_reads_content_block_lists():
    content = [
        {"type": "text", "text": "hello"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
        {"type": "output_text", "text": "world"},
    ]

    assert message_module.extract_message_text(content) == "hello\nworld"


def test_outgoing_message_content_reads_llm_content_blocks():
    raw = types.SimpleNamespace(
        content=[
            {"type": "text", "text": "hello"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
        ]
    )

    assert message_module.outgoing_message_content(raw) == "hello"


def test_outgoing_message_content_reads_wrapped_content_blocks():
    raw = types.SimpleNamespace(content=str({"content": [{"type": "text", "text": "hello"}]}))

    assert message_module.outgoing_message_content(raw) == "hello"


def test_message_text_extractors_handle_text_methods():
    class MessageWithTextMethod:
        content = [{"type": "text", "text": "content text"}]

        def text(self):
            return ""

    raw = MessageWithTextMethod()

    assert message_module.extract_message_text(raw) == "content text"
    assert message_module.outgoing_message_content(raw) == "content text"


@pytest.mark.asyncio
async def test_message_http_client_uses_registry():
    """验证 message 模块的 HTTP 客户端通过注册表获取。"""
    from utils import http_client as registry

    # Clean start
    registry._clients.clear()
    registry._aclose_all_called = False
    reloaded_message = importlib.reload(message_module)

    assert reloaded_message.httpx_client is not None
    assert registry.get_http_client("message") is reloaded_message.httpx_client

    await registry.aclose_all()
