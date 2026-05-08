# ruff: noqa: S101

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
async def test_message_http_client_can_be_closed(monkeypatch):
    closed = False

    class DummyClient:
        async def aclose(self):
            nonlocal closed
            closed = True

    monkeypatch.setattr(message_module, "httpx_client", DummyClient())

    await message_module.aclose_http_client()

    assert closed is True


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
            return "hello"

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
async def test_message_gateway_test_group_reply_check_does_not_mutate_messages(monkeypatch):
    import builtins

    class DummyEvent:
        def __init__(self):
            self.data = types.SimpleNamespace(group=types.SimpleNamespace(group_id=5))

        def get_user_id(self):
            return "12345"

        def is_tome(self):
            return False

        def get_plaintext(self):
            return "hello"

        to_me = False

    class DummyReplyCheck:
        should_reply = "false"
        confidence = 0.0

    async def fake_assistant_agent(*_args, **_kwargs):
        return DummyReplyCheck()

    original_open = builtins.open

    class DummyPromptFile:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return "{name}"

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("reply_check.md"):
            return DummyPromptFile()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(message_module.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [])
    monkeypatch.setattr(message_module.EnvConfig, "TEST_GROUP_ID", [5])
    monkeypatch.setattr(message_module, "assistant_agent", fake_assistant_agent)
    monkeypatch.setattr(builtins, "open", fake_open)
    messages = [{"role": "user", "content": "history"}]

    result = await message_module.message_gateway(DummyEvent(), messages)

    assert result is False
    assert messages == [{"role": "user", "content": "history"}]


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
