# ruff: noqa: S101

from types import SimpleNamespace

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.message import Message
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebot.permission import SUPERUSER
from nonebug import App

from plugins.acp import commands as acp
from utils.agents.progress import ProgressEvent, emit_progress
from utils.delivery import DeliveryResult


def _event():
    return SimpleNamespace(
        data=SimpleNamespace(segments=[], group=None, message_seq=9),
        get_user_id=lambda: "42",
    )


def _group_message_event(text: str, *, sender_id: int = 456) -> MessageEvent:
    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=sender_id,
        time=0,
        segments=[{"type": "text", "data": {"text": text}}],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=sender_id,
            nickname="u",
            sex="unknown",
            group_id=123,
            card="",
            title="",
            level="0",
            role="member",
            join_time=0,
            last_sent_time=0,
            shut_up_end_time=0,
        ),
    )
    return MessageEvent(
        data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message()
    )


def test_acp_command_requires_superuser():
    # nonebot 的 on() 会用 ``Permission() | permission`` 重建 Permission 对象，
    # 因此比较 checker 集合，而不是对象身份。
    assert acp.acp_command.permission is not None
    assert acp.acp_command.permission.checkers == SUPERUSER.checkers


@pytest.mark.asyncio
async def test_acp_command_rejects_non_superuser():
    async with App().test_matcher(acp.acp_command) as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, _group_message_event("/acp --list"))
        ctx.should_not_pass_permission(acp.acp_command)


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
@pytest.mark.parametrize("group_id", [pytest.param(None, id="private"), pytest.param(123, id="group")])
async def test_acp_command_does_not_send_progress_messages(monkeypatch, group_id):
    sent: list[str] = []
    final_responses = []
    reporters = []

    class DummyUniMessage:
        def __init__(self, content: str):
            self.content = content

        @classmethod
        def text(cls, content: str):
            return cls(content)

        async def send(self):
            sent.append(self.content)

    async def fake_extract(_segments):
        return "/acp 帮我查一下资料", [], [], []

    async def fake_download(*_args):
        return [], [], []

    async def fake_chat(_prompt, *, progress_reporter=None, **_kwargs):
        reporters.append(progress_reporter)
        for event in (
            ProgressEvent(type="thinking", message="正在思考…"),
            ProgressEvent(type="tool_call", message="正在调用工具…"),
            ProgressEvent(type="tool_result", message="工具执行完成"),
            ProgressEvent(type="assistant_preamble", message="我先查一下资料。"),
        ):
            await emit_progress(progress_reporter, event)
        return {"response": {"messages": [SimpleNamespace(content="最终回答")]}, "uni_messages": []}

    async def fake_send(target_group_id, message_seq, response):
        final_responses.append((target_group_id, message_seq, acp.outgoing_message_content(response["messages"][-1])))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(acp, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(acp, "message_extract", fake_extract)
    monkeypatch.setattr(acp, "download_media", fake_download)
    monkeypatch.setattr(acp.acp_agent, "chat_agent", fake_chat)
    monkeypatch.setattr(acp, "send_messages", fake_send)

    event = _event()
    event.data.group = SimpleNamespace(group_id=group_id) if group_id is not None else None
    await acp.handle_acp(event)

    assert reporters == [None]
    assert sent == []
    assert final_responses == [(group_id, 9, "最终回答")]


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
