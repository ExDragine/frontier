# ruff: noqa: S101

import asyncio
import importlib
import subprocess
import sys
import types
from pathlib import Path

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


class DummyTestGroupEvent:
    def __init__(self, plaintext="hello", *, is_tome=False, to_me=False):
        self.data = types.SimpleNamespace(group=types.SimpleNamespace(group_id=5))
        self.plaintext = plaintext
        self._is_tome = is_tome
        self.to_me = to_me

    def get_user_id(self):
        return "12345"

    def is_tome(self):
        return self._is_tome

    def get_plaintext(self):
        return self.plaintext


class DummyDmEvent:
    def __init__(self, plaintext="hello", *, is_tome=True, to_me=True):
        self.data = types.SimpleNamespace(group=None)
        self.plaintext = plaintext
        self._is_tome = is_tome
        self.to_me = to_me

    def get_user_id(self):
        return "12345"

    def is_tome(self):
        return self._is_tome

    def get_plaintext(self):
        return self.plaintext


class DummyReplyCheckFalse:
    should_reply = "false"
    confidence = 0.0


class DummyReplyCheckTrue:
    should_reply = "true"
    confidence = 0.9


class DummyReplyCheckDb:
    def __init__(self, *, message_count=0, latest_assistant_time=None):
        self.message_count = message_count
        self.latest_assistant_time = latest_assistant_time

    async def count_group_messages_since(self, *, group_id, since_time):
        return self.message_count

    async def latest_group_role_message_time(self, *, group_id, role):
        return self.latest_assistant_time


def patch_reply_check_prompt(monkeypatch, prompt_text: str) -> None:
    import builtins

    original_open = builtins.open

    class DummyPromptFile:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return prompt_text

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("reply_check.md"):
            return DummyPromptFile()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)


@pytest.fixture(autouse=True)
def clear_reply_check_state(monkeypatch):
    monkeypatch.setattr(message_module, "messages_db", DummyReplyCheckDb())
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST", [])
    message_module._reply_check_last_checked_at.clear()
    yield
    message_module._reply_check_last_checked_at.clear()


@pytest.fixture
def memory_engine():
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


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


def test_extract_message_files():
    segments = [
        {"type": "text", "data": {"text": "hi"}},
        {
            "type": "file",
            "data": {
                "file_id": "file-1",
                "file_name": "a.txt",
                "file_size": 10,
                "file_hash": "hash-1",
            },
        },
    ]

    files = message_module.extract_message_files(segments)

    assert files == [
        message_module.MessageFileItem(
            file_id="file-1",
            file_name="a.txt",
            file_size=10,
            file_hash="hash-1",
        )
    ]


@pytest.mark.asyncio
async def test_stage_message_files_downloads_group_file_to_memory_files(monkeypatch, tmp_path):
    calls = []

    class DummyBot:
        async def get_group_file_download_url(self, **kwargs):
            calls.append(("get_group_file_download_url", kwargs))
            return "https://example.com/a.txt"

    async def fake_get(url):
        calls.append(("get", url))
        return DummyResponse(b"file-bytes")

    monkeypatch.setattr(message_module.httpx_client, "get", fake_get)

    staged = await message_module.stage_message_files(
        DummyBot(),
        [
            message_module.MessageFileItem(
                file_id="file-1",
                file_name="../a.txt",
                file_size=10,
            )
        ],
        memory_dir=tmp_path,
        workspace_key="123",
        user_id="456",
        group_id=123,
    )

    assert len(staged) == 1
    assert staged[0].file_name == "a.txt"
    assert staged[0].virtual_path == "/memory/123/files/a.txt"
    assert staged[0].local_path.read_bytes() == b"file-bytes"
    assert calls == [
        ("get_group_file_download_url", {"group_id": 123, "file_id": "file-1"}),
        ("get", "https://example.com/a.txt"),
    ]


@pytest.mark.asyncio
async def test_stage_message_files_passes_empty_private_file_hash(monkeypatch, tmp_path):
    calls = []

    class DummyBot:
        async def get_private_file_download_url(self, **kwargs):
            calls.append(("get_private_file_download_url", kwargs))
            return "https://example.com/private.txt"

    async def fake_get(url):
        calls.append(("get", url))
        return DummyResponse(b"private-file")

    monkeypatch.setattr(message_module.httpx_client, "get", fake_get)

    staged = await message_module.stage_message_files(
        DummyBot(),
        [
            message_module.MessageFileItem(
                file_id="file-1",
                file_name="private.txt",
                file_size=12,
                file_hash="",
            )
        ],
        memory_dir=tmp_path,
        workspace_key="456",
        user_id="456",
        group_id=None,
    )

    assert staged[0].virtual_path == "/memory/456/files/private.txt"
    assert staged[0].local_path.read_bytes() == b"private-file"
    assert calls == [
        ("get_private_file_download_url", {"user_id": 456, "file_id": "file-1", "file_hash": ""}),
        ("get", "https://example.com/private.txt"),
    ]


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
async def test_message_gateway_whitelist_numeric_id(monkeypatch):
    """白名单模式下：get_user_id() 返回字符串，TOML 列表为整数，应能正确匹配。"""

    class DummyEvent:
        def __init__(self):
            self.data = types.SimpleNamespace(group=types.SimpleNamespace(group_id=5))

        def get_user_id(self):
            return "12345"  # string, as returned by NoneBot

        def is_tome(self):
            return True

        def get_plaintext(self):
            return "这个报错怎么解决？"

        to_me = True

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", True)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_GROUP_LIST", [5])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_PERSON_LIST", [12345])  # int from TOML
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    result = await message_module.message_gateway(DummyEvent(), [])
    assert result is True


@pytest.mark.asyncio
async def test_message_gateway_whitelist_dm_allowed(monkeypatch):
    """白名单模式下：私聊（group_id=0）不应被群白名单拦截，通过用户白名单即可放行。"""

    class DummyEvent:
        def __init__(self):
            self.data = types.SimpleNamespace(group=None)  # DM

        def get_user_id(self):
            return "12345"

        def is_tome(self):
            return True

        def get_plaintext(self):
            return "hello"

        to_me = True

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", True)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_GROUP_LIST", [99])  # user not in this group
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_PERSON_LIST", [12345])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    result = await message_module.message_gateway(DummyEvent(), [])
    assert result is True


@pytest.mark.asyncio
async def test_message_gateway_auto_reply_blacklist_skips_reply_check(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("auto reply blacklist should skip reply check")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST", [5])
    monkeypatch.setattr(message_module, "_reply_check_should_reply", fail_if_called)

    result = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), [])

    assert result is False


@pytest.mark.asyncio
async def test_message_gateway_auto_reply_whitelist_controls_reply_check(monkeypatch):
    checked_groups = []

    async def fake_reply_check(group_id, *_args, **_kwargs):
        checked_groups.append(group_id)
        return True

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_MODE", True)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST", [5])
    monkeypatch.setattr(message_module, "_reply_check_should_reply", fake_reply_check)

    allowed = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), [])
    message_module.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST = [6]
    denied = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), [])

    assert allowed is True
    assert denied is False
    assert checked_groups == [5]


@pytest.mark.asyncio
async def test_message_gateway_auto_reply_blacklist_takes_precedence(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("auto reply blacklist should take precedence")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_MODE", True)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST", [5])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST", [5])
    monkeypatch.setattr(message_module, "_reply_check_should_reply", fail_if_called)

    result = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), [])

    assert result is False


@pytest.mark.asyncio
async def test_message_gateway_auto_reply_policy_does_not_block_active_trigger(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("active trigger should not use automatic reply check")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_MODE", True)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST", [5])
    monkeypatch.setattr(message_module, "_reply_check_should_reply", fail_if_called)

    mentioned = await message_module.message_gateway(
        DummyTestGroupEvent("这个报错怎么解决？", is_tome=True, to_me=False),
        [],
    )
    marked_to_me = await message_module.message_gateway(
        DummyTestGroupEvent("帮我看看这个报错", is_tome=False, to_me=True),
        [],
    )
    monkeypatch.setattr(message_module, "_get_wake_words", lambda _group_id: ["Frontier"])
    wake_word = await message_module.message_gateway(DummyTestGroupEvent("Frontier 帮我看看这个报错"), [])

    assert mentioned is True
    assert marked_to_me is True
    assert wake_word is True


@pytest.mark.asyncio
async def test_message_gateway_auto_reply_policy_does_not_block_private_chat(monkeypatch):
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_MODE", True)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST", [0])

    result = await message_module.message_gateway(DummyDmEvent("帮我看看这个报错"), [])

    assert result is True


@pytest.mark.asyncio
async def test_message_gateway_group_active_trigger_can_stay_silent_for_low_info(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("low-information active trigger should not call Signal LLM")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "signal_structured", fail_if_called)

    result = await message_module.message_gateway(DummyTestGroupEvent("哈哈哈", is_tome=True, to_me=True), [])

    assert result is False


@pytest.mark.asyncio
async def test_message_gateway_group_wake_word_only_can_stay_silent(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("empty wake-word trigger should not call Signal LLM")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "_get_wake_words", lambda _group_id: ["Frontier"])
    monkeypatch.setattr(message_module, "signal_structured", fail_if_called)

    result = await message_module.message_gateway(DummyTestGroupEvent("Frontier"), [])

    assert result is False


@pytest.mark.asyncio
async def test_message_gateway_group_active_trigger_allows_clear_request(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("clear active request should not need Signal LLM")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "signal_structured", fail_if_called)

    result = await message_module.message_gateway(
        DummyTestGroupEvent("这个报错怎么解决？", is_tome=True, to_me=True),
        [],
    )

    assert result is True


@pytest.mark.asyncio
async def test_message_gateway_group_active_trigger_allows_short_image_edit_request(monkeypatch):
    calls = 0

    async def fake_signal_structured(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)

    result = await message_module.message_gateway(DummyTestGroupEvent("P一下", is_tome=True, to_me=True), [])

    assert result is True
    assert calls == 0


@pytest.mark.asyncio
async def test_message_gateway_group_active_trigger_allows_non_low_info_without_signal(monkeypatch):
    calls = 0

    async def fake_signal_structured(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "_get_wake_words", lambda _group_id: ["Frontier"])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)

    result = await message_module.message_gateway(DummyTestGroupEvent("Frontier 那个"), [])

    assert result is True
    assert calls == 0


@pytest.mark.asyncio
async def test_message_gateway_group_active_trigger_blocks_stop_intent(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("stop-intent active trigger should not call Signal LLM")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "_get_wake_words", lambda _group_id: ["Frontier"])
    monkeypatch.setattr(message_module, "signal_structured", fail_if_called)

    result = await message_module.message_gateway(DummyTestGroupEvent("Frontier 别回了"), [])

    assert result is False


@pytest.mark.asyncio
async def test_message_gateway_private_active_trigger_is_not_silenced(monkeypatch):
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("private chat should not use active group reply gate")

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module, "signal_structured", fail_if_called)

    result = await message_module.message_gateway(DummyDmEvent("哈哈哈"), [])

    assert result is True


@pytest.mark.asyncio
async def test_message_gateway_test_group_reply_check_does_not_mutate_messages(monkeypatch):
    async def fake_signal_structured(*_args, **_kwargs):
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)
    patch_reply_check_prompt(monkeypatch, "{name}")
    messages = [{"role": "user", "content": "history"}]

    result = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), messages)

    assert result is False
    assert messages == [{"role": "user", "content": "history"}]


@pytest.mark.asyncio
async def test_message_gateway_test_group_reply_check_strips_image_data(monkeypatch):
    captured = {}

    async def fake_signal_structured(system_prompt, user_prompt, *_args, **_kwargs):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module.EnvConfig, "BOT_NAME", "Frontier")
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)
    patch_reply_check_prompt(monkeypatch, "bot={name}")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "history text"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + "a" * 1000}},
            ],
        }
    ]

    result = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), messages)

    assert result is False
    assert captured["system_prompt"] == "bot=Frontier"
    assert "history text" in captured["user_prompt"]
    assert "这个报错怎么解决？" in captured["user_prompt"]
    assert "data:image" not in captured["user_prompt"]
    assert "base64" not in captured["user_prompt"]


@pytest.mark.asyncio
async def test_message_gateway_test_group_skips_casual_messages(monkeypatch):
    calls = 0

    async def fake_signal_structured(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)
    patch_reply_check_prompt(monkeypatch, "{name}")

    result = await message_module.message_gateway(DummyTestGroupEvent("哈哈确实"), [])

    assert result is False
    assert calls == 0


@pytest.mark.asyncio
async def test_message_gateway_test_group_reply_check_has_group_cooldown(monkeypatch):
    calls = 0

    async def fake_signal_structured(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)
    monkeypatch.setattr(message_module.time, "monotonic", lambda: 1000.0)
    patch_reply_check_prompt(monkeypatch, "{name}")

    first = await message_module.message_gateway(DummyTestGroupEvent("这个报错怎么解决？"), [])
    second = await message_module.message_gateway(DummyTestGroupEvent("这个问题有人知道吗？"), [])

    assert first is False
    assert second is False
    assert calls == 1


@pytest.mark.asyncio
async def test_message_gateway_test_group_active_group_requires_strong_signal(monkeypatch):
    calls = 0

    async def fake_signal_structured(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return DummyReplyCheckFalse()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)
    monkeypatch.setattr(
        message_module,
        "messages_db",
        DummyReplyCheckDb(message_count=message_module.REPLY_CHECK_ACTIVE_GROUP_MESSAGE_LIMIT + 1),
    )
    patch_reply_check_prompt(monkeypatch, "{name}")

    normal_question = await message_module.message_gateway(DummyTestGroupEvent("这个东西怎么处理比较好？"), [])
    strong_question = await message_module.message_gateway(DummyTestGroupEvent("求助，这个报错怎么解决？"), [])

    assert normal_question is False
    assert strong_question is False
    assert calls == 1


@pytest.mark.asyncio
async def test_message_gateway_test_group_uses_database_assistant_reply_cooldown(monkeypatch):
    calls = 0

    async def fake_signal_structured(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return DummyReplyCheckTrue()

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module, "signal_structured", fake_signal_structured)
    monkeypatch.setattr(message_module.time, "time", lambda: 2000.0)
    monkeypatch.setattr(
        message_module,
        "messages_db",
        DummyReplyCheckDb(
            latest_assistant_time=2_000_000 - message_module.REPLY_CHECK_ASSISTANT_REPLY_COOLDOWN_SECONDS * 1000 + 1
        ),
    )
    patch_reply_check_prompt(monkeypatch, "{name}")

    result = await message_module.message_gateway(DummyTestGroupEvent("求助，这个报错怎么解决？"), [])

    assert result is False
    assert calls == 0


@pytest.mark.asyncio
async def test_message_check_text(monkeypatch):
    """CONTENT_CHECK_ENABLED=True 时，调用 text_det 进行检测"""
    import types

    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)

    fake_det = types.SimpleNamespace()

    async def fake_predict(text):
        return "Safe", []

    fake_det.predict = fake_predict
    monkeypatch.setattr(message_module, "text_det", fake_det)

    result = await message_module.message_check("hello", None)
    assert result == "Safe"


def test_importing_content_check_does_not_import_ml_runtime():
    project_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import utils.context_check; "
                "assert all(name not in sys.modules for name in ('torch', 'torchao', 'transformers'))"
            ),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_message_check_initializes_text_detector_once_for_concurrent_calls(monkeypatch):
    calls = 0

    class FakeTextCheck:
        def __init__(self):
            nonlocal calls
            calls += 1

        async def predict(self, _text):
            return "Safe", []

    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)
    monkeypatch.setattr(message_module, "TextCheck", FakeTextCheck)
    monkeypatch.setattr(message_module, "text_det", None)
    monkeypatch.setattr(message_module, "_text_det_retry_at", 0.0)

    results = await asyncio.gather(
        message_module.message_check("one", None),
        message_module.message_check("two", None),
    )

    assert results == ["Safe", "Safe"]
    assert calls == 1


@pytest.mark.asyncio
async def test_message_check_only_initializes_detector_for_used_media(monkeypatch):
    calls = {"text": 0, "image": 0}

    class FakeTextCheck:
        def __init__(self):
            calls["text"] += 1

    class FakeImageCheck:
        def __init__(self):
            calls["image"] += 1

        async def predict(self, _image):
            return "safe"

    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)
    monkeypatch.setattr(message_module, "TextCheck", FakeTextCheck)
    monkeypatch.setattr(message_module, "ImageCheck", FakeImageCheck)
    monkeypatch.setattr(message_module, "text_det", None)
    monkeypatch.setattr(message_module, "image_det", None)
    monkeypatch.setattr(message_module, "_image_det_retry_at", 0.0)
    monkeypatch.setattr(message_module.PILImage, "open", lambda _image: object())

    result = await message_module.message_check(None, [b"image"])

    assert result == "Safe"
    assert calls == {"text": 0, "image": 1}


@pytest.mark.asyncio
async def test_message_check_load_failure_is_rate_limited_and_fails_open(monkeypatch):
    calls = 0
    now = 100.0

    class FailingTextCheck:
        def __init__(self):
            nonlocal calls
            calls += 1
            raise RuntimeError("load failed")

    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)
    monkeypatch.setattr(message_module, "TextCheck", FailingTextCheck)
    monkeypatch.setattr(message_module, "text_det", None)
    monkeypatch.setattr(message_module, "_text_det_retry_at", 0.0)
    monkeypatch.setattr(message_module.time, "monotonic", lambda: now)

    assert await message_module.message_check("one", None) == "Safe"
    assert await message_module.message_check("two", None) == "Safe"
    assert calls == 1

    now += message_module.CONTENT_CHECK_RETRY_COOLDOWN_SECONDS
    assert await message_module.message_check("three", None) == "Safe"
    assert calls == 2


@pytest.mark.asyncio
async def test_sanitize_outgoing_text_predict_failure_resets_detector_and_fails_open(monkeypatch):
    class FailingDetector:
        async def predict(self, _text):
            raise RuntimeError("inference failed")

    now = 200.0
    detector = FailingDetector()
    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)
    monkeypatch.setattr(message_module, "text_det", detector)
    monkeypatch.setattr(message_module, "_text_det_retry_at", 0.0)
    monkeypatch.setattr(message_module.time, "monotonic", lambda: now)

    assert await message_module.sanitize_outgoing_text("original") == "original"
    assert message_module.text_det is None
    assert message_module._text_det_retry_at == now + message_module.CONTENT_CHECK_RETRY_COOLDOWN_SECONDS


@pytest.mark.asyncio
async def test_message_check_loads_after_content_check_is_enabled(monkeypatch):
    calls = 0

    class FakeTextCheck:
        def __init__(self):
            nonlocal calls
            calls += 1

        async def predict(self, _text):
            return "Safe", []

    monkeypatch.setattr(message_module, "TextCheck", FakeTextCheck)
    monkeypatch.setattr(message_module, "text_det", None)
    monkeypatch.setattr(message_module, "_text_det_retry_at", 0.0)
    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    assert await message_module.message_check("disabled", None) == "Safe"
    assert calls == 0

    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)
    assert await message_module.message_check("enabled", None) == "Safe"
    assert calls == 1


@pytest.mark.asyncio
async def test_message_check_disabled_returns_safe(monkeypatch):
    """CONTENT_CHECK_ENABLED=False 时，message_check 直接返回 Safe，不调用检测器"""
    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", False)
    result = await message_module.message_check("任意内容", None)
    assert result == "Safe"


@pytest.mark.asyncio
async def test_message_check_disabled_with_images_returns_safe(monkeypatch):
    """CONTENT_CHECK_ENABLED=False 时，即使有图片也直接返回 Safe"""
    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", False)
    result = await message_module.message_check(None, [b"fake_image_bytes"])
    assert result == "Safe"


@pytest.mark.asyncio
async def test_sanitize_outgoing_text_blocks_unsafe_output(monkeypatch):
    """模型输出为 Unsafe 时，替换成固定拦截提示"""
    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)

    fake_det = types.SimpleNamespace()

    async def fake_predict(text):
        assert text == "dangerous model output"
        return "Unsafe", ["Violent"]

    fake_det.predict = fake_predict
    monkeypatch.setattr(message_module, "text_det", fake_det)

    result = await message_module.sanitize_outgoing_text("dangerous model output")

    assert result == message_module.OUTPUT_RISK_BLOCKED_MESSAGE


@pytest.mark.asyncio
async def test_sanitize_outgoing_text_allows_controversial_output(monkeypatch):
    """只有确定 Unsafe 才拦截，Controversial 输出照常发送"""
    monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)

    fake_det = types.SimpleNamespace()

    async def fake_predict(text):
        assert text == "borderline model output"
        return "Controversial", ["Politically Sensitive Topics"]

    fake_det.predict = fake_predict
    monkeypatch.setattr(message_module, "text_det", fake_det)

    result = await message_module.sanitize_outgoing_text("borderline model output")

    assert result == "borderline model output"


# ── _get_wake_words 测试 ────────────────────────────────────


class TestGetWakeWords:
    def test_returns_env_nicknames_when_no_custom_words(self, monkeypatch):
        from utils.database import get_engine

        monkeypatch.setattr(message_module, "get_engine", get_engine)
        monkeypatch.setattr(message_module.EnvConfig, "BOT_NICKNAMES", ["小李子", "小栗子"])
        words = message_module._get_wake_words(99999)
        assert words == ["小李子", "小栗子"]

    def test_returns_custom_words_from_database(self, monkeypatch, memory_engine):
        from utils.database import GroupSettings, GroupSettingsManager

        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(456, "wake_word", "小天")
        manager.set(456, "wake_word", "助手")

        # 让 _get_wake_words 使用 memory_engine
        monkeypatch.setattr(message_module, "get_engine", lambda url=None: memory_engine)
        monkeypatch.setattr(message_module.EnvConfig, "BOT_NICKNAMES", ["小李子", "小栗子"])

        words = message_module._get_wake_words(456)
        assert sorted(words) == ["助手", "小天"]

    def test_returns_env_nicknames_for_dm(self, monkeypatch):
        monkeypatch.setattr(message_module.EnvConfig, "BOT_NICKNAMES", ["小李子", "小栗子"])
        words = message_module._get_wake_words(0)
        assert words == ["小李子", "小栗子"]
