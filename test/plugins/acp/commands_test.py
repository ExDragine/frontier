# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from plugins.acp import commands as acp
from utils.delivery import DeliveryResult


def _event():
    return SimpleNamespace(
        data=SimpleNamespace(segments=[], group=None, message_seq=9),
        get_user_id=lambda: "42",
    )


def test_parse_acp_command_supports_agent_and_control_actions():
    run = acp._parse_command("/acp --agent demo inspect this")
    reset = acp._parse_command("/acp --reset --agent=demo")

    assert (run.action, run.agent_name, run.prompt) == ("run", "demo", "inspect this")
    assert (reset.action, reset.agent_name, reset.prompt) == ("reset", "demo", "")


def test_acp_command_reuses_agent_access_policy(monkeypatch):
    monkeypatch.setattr(acp.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(acp.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(acp.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [42])

    assert acp._has_agent_access(_event()) is False


@pytest.mark.asyncio
async def test_group_acp_progress_reporter_blocks_intermediate_messages(monkeypatch):
    sent: list[str] = []

    class DummyUniMessage:
        def __init__(self, content: str):
            self.content = content

        @classmethod
        def text(cls, content: str):
            return cls(content)

        async def send(self):
            sent.append(self.content)

    monkeypatch.setattr(acp, "UniMessage", DummyUniMessage)
    reporter = acp._progress_reporter(group_id=123)

    await reporter(acp.ProgressEvent(type="thinking", message="raw thought"))
    await reporter(acp.ProgressEvent(type="tool_call", message="running tool"))
    await reporter(acp.ProgressEvent(type="assistant_preamble", message="working on it"))

    assert sent == []


@pytest.mark.asyncio
async def test_acp_command_runs_prompt_with_media(monkeypatch):
    captured = {}
    sent_responses = []

    async def fake_extract(_segments):
        return "/acp --agent demo build it", [b"lazy-image"], [b"lazy-audio"], []

    async def fake_download(images, audios, videos):
        assert images == [b"lazy-image"]
        assert audios == [b"lazy-audio"]
        assert videos == []
        return [b"image"], [b"audio"], []

    async def fake_chat(prompt, **kwargs):
        captured["prompt"] = prompt
        captured.update(kwargs)
        return {"response": {"messages": [SimpleNamespace(content="result")]}, "uni_messages": []}

    async def fake_send_messages(group_id, event_id, response):
        sent_responses.append((group_id, event_id, response))
        return DeliveryResult(attempted=1, sent=1)

    async def fake_sanitize(text):
        return text

    monkeypatch.setattr(acp, "message_extract", fake_extract)
    monkeypatch.setattr(acp, "download_media", fake_download)
    monkeypatch.setattr(acp.acp_agent, "chat_agent", fake_chat)
    monkeypatch.setattr(acp, "send_messages", fake_send_messages)
    monkeypatch.setattr(acp, "sanitize_outgoing_text", fake_sanitize)

    await acp.handle_acp(_event())

    assert captured["prompt"] == "build it"
    assert captured["workspace_key"] == "dm:42"
    assert captured["agent_name"] == "demo"
    assert [item.kind for item in captured["media"]] == ["image", "audio"]
    assert sent_responses[0][:2] == (None, 9)


@pytest.mark.asyncio
async def test_acp_artifact_failure_is_reported_without_final_text(monkeypatch):
    sent = []

    async def artifacts(_items):
        return DeliveryResult(attempted=1, errors=("transport",))

    async def send(_group_id, _message_seq, response):
        sent.append(acp.outgoing_message_content(response["messages"][-1]))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(acp, "send_artifacts", artifacts)
    monkeypatch.setattr(acp, "send_messages", send)
    monkeypatch.setattr(acp.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    result = await acp._send_result({"uni_messages": ["artifact"]}, group_id=None, message_seq=1)

    assert sent == ["🔌 ACP 附件未完整送达，请稍后重试。"]
    assert result.errors == ("transport",)
    assert not result.successful


@pytest.mark.asyncio
async def test_acp_delivery_failure_sends_notice_and_keeps_failure_result(monkeypatch):
    notices = []

    async def send(_group_id, _message_seq, _response):
        return DeliveryResult(attempted=1, errors=("transport",))

    async def notify(self):
        notices.append(str(self))

    monkeypatch.setattr(acp, "send_messages", send)
    monkeypatch.setattr(acp.UniMessage, "send", notify)
    monkeypatch.setattr(acp.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    result = await acp._send_result({"response": {"messages": ["answer"]}}, group_id=None, message_seq=1)

    assert notices == ["🔌 ACP 回复发送失败，请稍后重试。"]
    assert result.sent == 0
    assert result.errors == ("transport",)


@pytest.mark.asyncio
async def test_acp_sanitizing_does_not_mutate_original_response(monkeypatch):
    sent = []
    original = {"response": {"messages": [SimpleNamespace(content="unsafe")]}}

    async def sanitize(_text):
        return "safe"

    async def send(_group_id, _message_seq, response):
        sent.append(acp.outgoing_message_content(response["messages"][-1]))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(acp, "sanitize_outgoing_text", sanitize)
    monkeypatch.setattr(acp, "send_messages", send)

    result = await acp._send_result(original, group_id=None, message_seq=1)

    assert result.successful
    assert sent == ["safe"]
    assert original["response"]["messages"][0].content == "unsafe"
