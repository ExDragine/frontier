# ruff: noqa: S101

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import pytest

from utils.delivery import DeliveryResult
from utils.message import StagedMessageFile


def _context(agent):
    return agent.AgentRequestContext(
        event=cast(Any, SimpleNamespace(self_id="1")),
        user_id="2",
        user_name="user",
        event_id=3,
        group_id=4,
        msg_time=5,
        text="question",
        quoted_images=[],
        images=[],
        videos=[],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("group_id", [4, None])
async def test_delivered_reply_can_be_quoted_as_original_text(monkeypatch, group_id):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent
    from utils import database as db_module
    from utils.database import MessageDatabase
    from utils.reply_context import build_reply_context

    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    original = "| 原始 Markdown | 数值 |\n| --- | --- |\n| [图片] 是说明文字 | 42 |"

    class Cognitive:
        async def chat_agent(self, *_args, **_kwargs):
            return {"response": {"messages": [original]}, "uni_messages": []}

    async def send(*_args):
        return DeliveryResult(attempted=1, sent=1, message_ids=(900,))

    async def reject(*_args, **_kwargs):
        raise AssertionError("stored assistant source must not fetch or read rendered media")

    monkeypatch.setattr(agent, "f_cognitive", Cognitive())
    monkeypatch.setattr(agent, "messages_db", database)
    monkeypatch.setattr(agent, "send_messages", send)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)
    event = SimpleNamespace(self_id="1", data=SimpleNamespace(peer_id=2))
    context = replace(_context(agent), group_id=group_id, event=cast(Any, event))
    assert await agent._process_agent_request(context)
    monkeypatch.setattr(database, "select_image_attachments_by_msg_time", reject)
    for load_images in (False, True):
        payload, images = await build_reply_context(
            SimpleNamespace(get_message=reject), cast(Any, event), 900, group_id, database,
            load_images=load_images,
        )
        assert payload is not None
        assert payload["content"] == original
        assert payload["sender"]["role"] == "assistant"
        assert payload["sender"]["user_id"] == "1"
        assert images == []


@pytest.mark.asyncio
@pytest.mark.parametrize("delivered", [True, False])
async def test_history_only_records_delivered_response_after_send(monkeypatch, delivered):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = []

    class Cognitive:
        async def chat_agent(self, *_args, **_kwargs):
            return {"response": {"messages": ["answer"]}, "uni_messages": []}

    class Database:
        async def insert(self, **kwargs):
            calls.append(("store", kwargs["content"]))

    async def send(*_args):
        calls.append(("send", "answer"))
        return DeliveryResult(attempted=1, sent=1) if delivered else DeliveryResult(attempted=1, errors=("fail",))

    monkeypatch.setattr(agent, "f_cognitive", Cognitive())
    monkeypatch.setattr(agent, "messages_db", Database())
    monkeypatch.setattr(agent, "send_messages", send)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)
    context = _context(agent)

    assert await agent._process_agent_request(context) is delivered
    assert calls == ([("send", "answer"), ("store", "answer")] if delivered else [("send", "answer")])


@pytest.mark.asyncio
async def test_artifact_failure_reaches_user_even_without_final_text(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    sent = []

    class Cognitive:
        async def chat_agent(self, *_args, **_kwargs):
            return {"response": {"messages": []}, "uni_messages": ["artifact"]}

    class Database:
        async def insert(self, **_kwargs):
            pass

    async def send_artifacts(_artifacts):
        return DeliveryResult(attempted=1, errors=("RuntimeError",))

    async def send_messages(_group_id, _message_id, response):
        sent.append(agent.outgoing_message_content(response["messages"][-1]))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "f_cognitive", Cognitive())
    monkeypatch.setattr(agent, "messages_db", Database())
    monkeypatch.setattr(agent, "send_artifacts", send_artifacts)
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    assert await agent._process_agent_request(_context(agent))
    assert sent == ["部分附件发送失败，请稍后重试。"]


@pytest.mark.asyncio
async def test_duplicate_event_stops_before_gateway_and_media_download(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    class Finished(Exception):
        pass

    class Database:
        async def insert(self, **_kwargs):
            return SimpleNamespace(message_id=7, time=8, inserted=False)

    async def finish():
        raise Finished

    async def reject(*_args, **_kwargs):
        raise AssertionError("duplicate event must not query history, download, or execute")

    monkeypatch.setattr(agent, "get_bot", lambda: object())
    monkeypatch.setattr(agent, "messages_db", Database())
    monkeypatch.setattr(agent.common, "finish", finish)
    monkeypatch.setattr(agent, "message_gateway", reject)
    monkeypatch.setattr(agent, "download_media", reject)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    event = SimpleNamespace(
        self_id="1",
        get_user_id=lambda: "2",
        is_tome=lambda: True,
        data=SimpleNamespace(
            message_seq=3,
            group=SimpleNamespace(group_id=4),
            friend=None,
            group_member=SimpleNamespace(nickname="user", card=""),
            segments=[
                {"type": "text", "data": {"text": "question"}},
                {"type": "image", "data": {"temp_url": "https://example.com/image"}},
            ],
        ),
    )

    with pytest.raises(Finished):
        await agent.handle_common(cast(Any, event))


@pytest.mark.asyncio
async def test_same_group_members_share_generation_and_delivery_queue(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []

    class Bot:
        async def send_group_message_reaction(self, **_kwargs):
            pass

    async def process(context, _history):
        calls.append(context.user_id)
        if context.user_id == "2":
            entered.set()
            await release.wait()

    monkeypatch.setattr(agent, "_process_agent_request", process)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    async def run(context):
        await agent._run_agent_turn(
            bot=Bot(),
            context=context,
            history_messages=[],
            previous_reply_payload=None,
            fetched_reply_payload=None,
            original_text=context.text,
        )

    first = asyncio.create_task(run(_context(agent)))
    await entered.wait()
    second = asyncio.create_task(run(replace(_context(agent), user_id="3", event_id=4)))
    try:
        await asyncio.sleep(0)
        assert calls == ["2"]
    finally:
        release.set()
        await asyncio.gather(first, second)
    assert calls == ["2", "3"]


@pytest.mark.asyncio
async def test_delivery_queue_timeout_never_starts_expired_request(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    locked = asyncio.Event()
    release = asyncio.Event()
    notices = []

    async def block():
        locked.set()
        await release.wait()

    async def process(*_args):
        raise AssertionError("expired queued request must not execute")

    async def send(_group_id, _event_id, response):
        notices.append(agent.outgoing_message_content(response["messages"][-1]))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "_process_agent_request", process)
    monkeypatch.setattr(agent, "send_messages", send)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_JOB_TIMEOUT_SECONDS", 0.01)
    holder = asyncio.create_task(agent.run_serialized("delivery:group-4", block))
    await locked.wait()
    try:
        await agent._process_queued_agent_request(_context(agent), [])
    finally:
        release.set()
        await holder

    assert notices == ["等待处理超时，本轮请求尚未开始，请稍后重试。"]


@pytest.mark.asyncio
async def test_processing_deadline_cancels_work_and_releases_delivery_lock(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    cancelled = asyncio.Event()
    notices = []

    async def process(*_args):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    async def send(_group_id, _event_id, response):
        notices.append(agent.outgoing_message_content(response["messages"][-1]))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "_process_agent_request", process)
    monkeypatch.setattr(agent, "send_messages", send)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_JOB_TIMEOUT_SECONDS", 0.01)

    await agent._process_queued_agent_request(_context(agent), [])

    assert cancelled.is_set()
    assert notices == ["本轮处理超时，请稍后重试。"]
    assert (
        await agent.run_serialized("delivery:group-4", asyncio.sleep(0, result="released"), timeout=0.1) == "released"
    )


@pytest.mark.asyncio
async def test_asset_collection_cancellation_cleans_completed_files(monkeypatch, tmp_path):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    downloaded = asyncio.Event()
    media_cancelled = asyncio.Event()
    path = tmp_path / "unindexed.txt"

    async def files():
        path.write_bytes(b"file")
        downloaded.set()
        return [StagedMessageFile(file_name=path.name, file_size=4, virtual_path="/memory/file", local_path=path)]

    async def media():
        try:
            await asyncio.Event().wait()
        finally:
            media_cancelled.set()

    task = asyncio.create_task(agent._collect_incoming_assets(media(), files()))
    await downloaded.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert media_cancelled.is_set()
    assert not path.exists()
