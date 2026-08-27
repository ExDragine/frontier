# ruff: noqa: S101

import asyncio
import json
import types
from typing import Any, cast

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.message import Message
from nonebot.adapters.milky.model.common import Friend, FriendCategory, Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebug import App


async def _noop(*_args, **_kwargs):
    return None


def _first_text(content) -> str:
    if isinstance(content, str):
        return content
    return str(content[0]["text"])


def test_attached_image_placeholders_are_removed_only_when_all_images_persist(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    text = "查看图片\n[图片]\n[图片:动画表情]"

    assert agent._remove_attached_image_placeholders(text, 1) == text
    assert agent._remove_attached_image_placeholders(text, 2) == "查看图片"
    assert agent._remove_attached_image_placeholders(text, 0) == text


def test_direct_bot_mention_requires_explicit_matching_mention_segment():
    from utils.reply_context import segments_directly_mention_user

    assert segments_directly_mention_user(
        [{"type": "mention", "data": {"user_id": 1}}, {"type": "text", "data": {"text": "你好"}}],
        "1",
    )
    assert not segments_directly_mention_user(
        [{"type": "mention", "data": {"user_id": 2}}, {"type": "text", "data": {"text": "你看"}}],
        "1",
    )
    assert not segments_directly_mention_user(
        [{"type": "text", "data": {"text": "Frontier 你好"}}],
        "1",
    )


@pytest.mark.asyncio
async def test_group_progress_reporter_blocks_all_intermediate_messages(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    sent: list[str] = []

    class DummyUniMessage:
        def __init__(self, content: str):
            self.content = content

        @classmethod
        def text(cls, content: str):
            return cls(content)

        async def send(self):
            sent.append(self.content)

    async def allow_text(content: str):
        return content

    monkeypatch.setattr(agent, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(agent, "sanitize_outgoing_text", allow_text)
    reporter = agent._chat_progress_reporter(group_id=123)

    await reporter(agent.ProgressEvent(type="thinking", message="正在思考…"))
    await reporter(agent.ProgressEvent(type="tool_call", message="正在搜索…"))
    await reporter(agent.ProgressEvent(type="subagent_start", message="正在委派…"))
    await reporter(agent.ProgressEvent(type="assistant_preamble", message="我先查一下资料。"))
    await reporter(agent.ProgressEvent(type="assistant_preamble", message="接着核对来源。"))

    assert sent == []


@pytest.mark.asyncio
async def test_private_progress_reporter_keeps_templates_and_two_preambles(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    sent: list[str] = []

    class DummyUniMessage:
        def __init__(self, content: str):
            self.content = content

        @classmethod
        def text(cls, content: str):
            return cls(content)

        async def send(self):
            sent.append(self.content)

    async def allow_text(content: str):
        return content

    monkeypatch.setattr(agent, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(agent, "sanitize_outgoing_text", allow_text)
    reporter = agent._chat_progress_reporter(group_id=None)

    await reporter(agent.ProgressEvent(type="thinking", message="正在思考…"))
    await reporter(agent.ProgressEvent(type="assistant_preamble", message="我先查一下资料。"))
    await reporter(agent.ProgressEvent(type="assistant_preamble", message="接着核对来源。"))
    await reporter(agent.ProgressEvent(type="assistant_preamble", message="最后再整理结果。"))

    assert sent == ["正在思考…", "我先查一下资料。", "接着核对来源。"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("persist_media", "expected_user_text"),
    [
        (True, "hi\n[视频]\n[语音]"),
        (False, "hi\n[图片]\n[视频]\n[语音]"),
    ],
)
async def test_agent_image_placeholders_follow_persistence(  # noqa: C901
    monkeypatch,
    persist_media,
    expected_user_text,
):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"insert_media": 0, "schedule_summary": 0}
    captured = {}

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_media(self, **kwargs):
            calls["insert_media"] += 1
            if not persist_media:
                raise RuntimeError("database unavailable")
            return [
                types.SimpleNamespace(
                    kind=item.kind,
                    mime_type=item.mime_type,
                    file_name=f"1_{index}{item.extension}",
                    virtual_path=f"/memory/group-123/{item.kind}/1_{index}{item.extension}",
                )
                for index, item in enumerate(kwargs["media"])
            ]

        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def finalize_message_context(self, **kwargs):
            captured["finalized_context"] = kwargs

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **kwargs):
            captured["messages"] = messages
            captured["image_inputs"] = kwargs.get("image_inputs")
            captured["audio_inputs"] = kwargs.get("audio_inputs")
            captured["video_inputs"] = kwargs.get("video_inputs")
            captured["user_text"] = kwargs.get("user_text")
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_extract(_segments):
        return "hi", [b"image-bytes"], [b"audio-bytes"], [b"video-bytes"]

    async def fake_message_gateway(_event, _messages):
        return True

    async def fake_send_messages(*_args, **_kwargs):
        return None

    async def fake_send_artifacts(*_args, **_kwargs):
        return None

    def fake_schedule_summary(*_args, **_kwargs):
        calls["schedule_summary"] += 1

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "send_messages", fake_send_messages)
    monkeypatch.setattr(agent, "send_artifacts", fake_send_artifacts)
    monkeypatch.setattr(agent, "schedule_image_summary_write", fake_schedule_summary, raising=False)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[
            {"type": "text", "data": {"text": "hi"}},
            {
                "type": "image",
                "data": {
                    "resource_id": "image-resource",
                    "temp_url": "https://example.com/image.jpg",
                    "width": 100,
                    "height": 100,
                },
            },
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["insert_media"] == 1
    assert calls["schedule_summary"] == 0
    assert captured["image_inputs"] == [b"image-bytes"]
    assert captured["audio_inputs"] == [b"audio-bytes"]
    assert captured["video_inputs"] == [b"video-bytes"]
    assert captured["user_text"] == expected_user_text
    current_content = captured["messages"][-1]["content"]
    assert ("[图片]" in current_content[0]["text"]) is (not persist_media)
    assert current_content[1] == {"type": "text", "text": "以下图片来自当前消息："}
    assert current_content[2]["type"] == "image"
    assert current_content[3] == {"type": "text", "text": "以下语音来自当前消息："}
    assert current_content[4]["type"] == "audio"
    assert current_content[5] == {"type": "text", "text": "以下视频来自当前消息："}
    assert current_content[6]["type"] == "video"


@pytest.mark.asyncio
@pytest.mark.parametrize("index_file", [True, False])
async def test_agent_injects_staged_file_memory_path_even_if_indexing_fails(  # noqa: C901
    monkeypatch,
    tmp_path,
    index_file,
):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def insert_attachment(self, **kwargs):
            if not index_file:
                raise RuntimeError("database unavailable")
            captured["attachment"] = kwargs

    class DummyCognitive:
        working_dir = str(tmp_path / "sandbox")

        async def chat_agent(self, messages, *_args, **_kwargs):
            captured["messages"] = messages
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_gateway(_event, _messages):
        return True

    async def fake_stage_message_files(_bot, file_items, **kwargs):
        captured["file_items"] = file_items
        captured["memory_dir"] = kwargs["memory_dir"]
        captured["workspace_key"] = kwargs["workspace_key"]
        captured["message_time"] = kwargs["message_time"]
        local_path = tmp_path / "sandbox" / "memory" / "group-123" / "files" / "report.txt"
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text("data", encoding="utf-8")
        return [
            types.SimpleNamespace(
                file_name="report.txt",
                file_size=4,
                virtual_path="/memory/group-123/files/report.txt",
                local_path=local_path,
                mime_type="text/plain",
                sha256="file-sha256",
            )
        ]

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "stage_message_files", fake_stage_message_files)
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[
            {
                "type": "file",
                "data": {
                    "file_id": "file-1",
                    "file_name": "report.txt",
                    "file_size": 4,
                    "file_hash": None,
                },
            }
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["file_items"][0].file_id == "file-1"
    assert captured["memory_dir"] == tmp_path / "sandbox" / "memory" / "group-123"
    assert captured["workspace_key"] == "group-123"
    assert isinstance(captured["message_time"], int)
    assert captured["message_time"] > 0
    current_text = _first_text(captured["messages"][-1]["content"])
    payload = json.loads(current_text)
    assert payload["attachments"] == [
        {
            "kind": "file",
            "mime_type": "text/plain",
            "file_name": "report.txt",
            "path": "/memory/group-123/files/report.txt",
        }
    ]
    if index_file:
        assert captured["attachment"]["kind"] == "file"
        assert captured["attachment"]["mime_type"] == "text/plain"
        assert captured["attachment"]["sha256"] == "file-sha256"
    else:
        assert "attachment" not in captured
    staged_path = tmp_path / "sandbox" / "memory" / "group-123" / "files" / "report.txt"
    assert staged_path.exists() is index_file


@pytest.mark.asyncio
async def test_parallel_quote_failure_cleans_successfully_staged_files(monkeypatch, tmp_path):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    staged_path = tmp_path / "memory/group-123/files/report.txt"
    staged_path.parent.mkdir(parents=True)
    staged_path.write_text("data", encoding="utf-8")
    staged_file = types.SimpleNamespace(local_path=staged_path)

    async def media_result():
        return [], [], []

    async def file_result():
        return [staged_file]

    async def quote_failure():
        raise RuntimeError("quote lookup failed")

    with pytest.raises(RuntimeError, match="quote lookup failed"):
        await agent._collect_incoming_assets(
            media_result(),
            file_result(),
            quote_failure(),
        )

    assert not staged_path.exists()


@pytest.mark.asyncio
async def test_rejected_group_file_message_does_not_stage_file_before_gateway(monkeypatch, tmp_path):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured: dict[str, Any] = {"agent_calls": 0}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "user":
                captured["stored_content"] = kwargs["content"]

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyCognitive:
        working_dir = str(tmp_path / "sandbox")

        async def chat_agent(self, *_args, **_kwargs):
            captured["agent_calls"] += 1
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        pass

    async def fake_message_gateway(_event, _messages):
        return False

    async def fake_stage_message_files(_bot, file_items, **kwargs):
        captured["file_items"] = file_items
        captured["memory_dir"] = kwargs["memory_dir"]
        return [
            types.SimpleNamespace(
                file_name="Clear icon cache.bat",
                file_size=1175,
                virtual_path="/memory/1035400922/files/Clear icon cache.bat",
            )
        ]

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "stage_message_files", fake_stage_message_files)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=1035400922,
        message_seq=73686,
        sender_id=1530518186,
        time=0,
        segments=[
            {
                "type": "file",
                "data": {
                    "file_id": "/dbd89abd-f51a-4160-b8bd-8f10cc27c585",
                    "file_name": "Clear icon cache.bat",
                    "file_size": 1175,
                },
            }
        ],
        friend=None,
        group=Group(group_id=1035400922, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=1530518186,
            nickname="u",
            sex="unknown",
            group_id=1035400922,
            card="",
            title="",
            level="0",
            role="member",
            join_time=0,
            last_sent_time=0,
            shut_up_end_time=0,
        ),
    )
    event = MessageEvent(data=incoming, to_me=False, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert "file_items" not in captured
    assert "memory_dir" not in captured
    assert "/memory/1035400922/files/Clear icon cache.bat" not in captured["stored_content"]
    assert "Clear icon cache.bat" in captured["stored_content"]
    assert captured["agent_calls"] == 0


@pytest.mark.asyncio
async def test_agent_stores_expanded_forward_message_and_derived_nodes(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "user":
                captured["insert"] = kwargs

        async def replace_derived_messages(self, **kwargs):
            captured["derived"] = kwargs

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **kwargs):
            captured["messages"] = messages
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

        async def get_forwarded_messages(self, *, forward_id):
            if forward_id == "outer":
                return [
                    types.SimpleNamespace(
                        sender_name="Alice",
                        time=1714521600,
                        segments=[{"type": "text", "data": {"text": "第一条"}}],
                    ),
                    types.SimpleNamespace(
                        sender_name="Carol",
                        time=1714521601,
                        segments=[
                            {
                                "type": "forward",
                                "data": {"forward_id": "inner", "title": "内层", "summary": "1条"},
                            }
                        ],
                    ),
                ]
            if forward_id == "inner":
                return [
                    types.SimpleNamespace(
                        sender_name="Dana",
                        time=1714521602,
                        segments=[{"type": "text", "data": {"text": "第二层"}}],
                    )
                ]
            raise AssertionError(f"unexpected forward_id={forward_id}")

    async def fake_message_gateway(_event, _messages):
        return True

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[
            {
                "type": "forward",
                "data": {"forward_id": "outer", "title": "聊天记录", "summary": "2条"},
            }
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert "Alice: 第一条" in captured["insert"]["content"]
    assert "Dana: 第二层" in captured["insert"]["content"]
    assert captured["insert"]["normalized_version"] == agent.NORMALIZED_VERSION
    assert captured["insert"]["normalized_status"] == "complete"
    assert captured["insert"]["raw_segments_json"]
    assert len(captured["derived"]["derived_messages"]) == 3
    current_text = _first_text(captured["messages"][-1]["content"])
    assert "Dana: 第二层" in current_text


@pytest.mark.asyncio
async def test_agent_does_not_duplicate_normalized_video_marker(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "user":
                captured["stored_content"] = kwargs["content"]

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **kwargs):
            captured["messages"] = messages
            captured["video_inputs"] = kwargs.get("video_inputs")
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_gateway(_event, _messages):
        return True

    async def fake_download_media(_image_downloaders, _audio_downloaders, video_downloaders):
        assert len(video_downloaders) == 1
        return [], [], [b"video-bytes"]

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "download_media", fake_download_media)
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[
            {
                "type": "video",
                "data": {
                    "temp_url": "https://example.com/video.mp4",
                    "duration": 12,
                },
            }
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["stored_content"] == "[视频:12秒]"
    current_text = _first_text(captured["messages"][-1]["content"])
    assert current_text.count("[视频") == 1
    assert captured["video_inputs"] == [b"video-bytes"]


@pytest.mark.asyncio
async def test_agent_appends_local_quoted_text_to_current_message(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "user":
                captured["stored_content"] = kwargs["content"]
                captured["stored_reply_context"] = kwargs["reply_context_json"]

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def select_by_msg_id(self, *, msg_id, group_id):
            assert msg_id == 900
            assert group_id == 123
            return types.SimpleNamespace(
                time=500,
                msg_id=900,
                user_id=111,
                group_id=123,
                user_name="Alice",
                role="user",
                content="原始消息内容",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            return []

        def load_attachment_files(self, _records):
            return [], 0

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **_kwargs):
            captured["messages"] = messages
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

        async def get_message(self, **_kwargs):
            return types.SimpleNamespace(segments=[{"type": "text", "data": {"text": "原始消息内容"}}])

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=901,
        sender_id=456,
        time=0,
        segments=[
            {"type": "reply", "data": {"message_seq": 900}},
            {"type": "text", "data": {"text": "这是什么意思？"}},
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
            nickname="Bob",
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["stored_content"] == "这是什么意思？"
    stored_reply = json.loads(captured["stored_reply_context"])
    assert stored_reply["sender"]["user_id"] == "111"
    assert stored_reply["content"] == "原始消息内容"
    current = json.loads(_first_text(captured["messages"][-1]["content"]))
    assert current["content"] == "这是什么意思？"
    assert current["reply_to"]["sender"]["display_name"] == "Alice"
    assert current["reply_to"]["content"] == "原始消息内容"


@pytest.mark.asyncio
async def test_rejected_reply_does_not_resolve_quoted_images(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"agent": 0, "image_lookup": 0}

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def select_by_msg_id(self, *, msg_id, group_id):
            assert (msg_id, group_id) == (900, 123)
            return types.SimpleNamespace(
                time=500,
                msg_id=900,
                user_id=111,
                group_id=123,
                user_name="Alice",
                role="user",
                content="[图片]",
                raw_segments_json=None,
                normalized_version=agent.NORMALIZED_VERSION,
                normalized_status="complete",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            calls["image_lookup"] += 1
            raise AssertionError("网关拒绝后不应解析引用图片")

    class DummyCognitive:
        async def chat_agent(self, *_args, **_kwargs):
            calls["agent"] += 1
            raise AssertionError("网关拒绝后不应调用 Agent")

    async def fake_message_gateway(_event, _messages):
        return False

    async def fake_stage_message_files(*_args, **_kwargs):
        return []

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: types.SimpleNamespace())
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "stage_message_files", fake_stage_message_files)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=901,
        sender_id=456,
        time=0,
        segments=[
            {"type": "reply", "data": {"message_seq": 900}},
            {"type": "text", "data": {"text": "这张图是什么？"}},
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
            nickname="Bob",
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls == {"agent": 0, "image_lookup": 0}


@pytest.mark.asyncio
async def test_agent_fetches_unindexed_quoted_image_from_milky(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {"restored_images": []}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "user":
                captured["stored_content"] = kwargs["content"]

        async def insert_images(self, **kwargs):
            captured["restored_images"].append(kwargs)
            return ["cache/images/111/500_0.jpg"]

        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def finalize_message_context(self, **kwargs):
            captured["finalized_context"] = kwargs

        async def select_by_msg_id(self, *, msg_id, group_id):
            assert msg_id == 900
            assert group_id == 123
            return types.SimpleNamespace(
                time=500,
                msg_id=900,
                user_id=111,
                group_id=123,
                user_name="Alice",
                role="user",
                content="",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            return []

        def load_attachment_files(self, records):
            assert records == []
            return [], 0

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **_kwargs):
            captured["messages"] = messages
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

        async def get_message(self, **kwargs):
            assert kwargs == {"message_scene": "group", "peer_id": 123, "message_seq": 900}
            return IncomingMessage(
                message_scene="group",
                peer_id=123,
                message_seq=900,
                sender_id=111,
                time=500,
                segments=[
                    {
                        "type": "image",
                        "data": {
                            "resource_id": "resource-1",
                            "temp_url": "https://expired.example/image.jpg",
                            "width": 10,
                            "height": 10,
                            "summary": "image",
                            "sub_type": "normal",
                        },
                    }
                ],
                friend=None,
                group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
                group_member=Member(
                    user_id=111,
                    nickname="Alice",
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

        async def get_resource_temp_url(self, *, resource_id):
            assert resource_id == "resource-1"
            return "https://fresh.example/image.jpg"

    async def fake_get(url):
        if "expired" in url:
            raise RuntimeError("expired")
        return types.SimpleNamespace(content=b"quoted-image")

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setitem(agent.build_reply_context.__globals__, "_httpx_client", types.SimpleNamespace(get=fake_get))
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=901,
        sender_id=456,
        time=0,
        segments=[
            {"type": "reply", "data": {"message_seq": 900}},
            {"type": "text", "data": {"text": "这张图呢？"}},
        ],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
            nickname="Bob",
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["restored_images"][0]["msg_time"] == 500
    assert captured["restored_images"][0]["images"] == [b"quoted-image"]
    current_content = captured["messages"][-1]["content"]
    assert current_content[0]["type"] == "text"
    assert "[图片]" not in current_content[0]["text"]
    reply_to = json.loads(current_content[0]["text"])["reply_to"]
    assert reply_to["content"] == "[引用消息包含图片 1 张]"
    assert reply_to["media"] == {"image_count": 1}
    finalized_reply = json.loads(captured["finalized_context"]["reply_context_json"])
    assert finalized_reply == reply_to
    assert current_content[1] == {"type": "text", "text": "以下图片来自上面的引用消息："}
    assert current_content[2]["type"] == "image"


@pytest.mark.asyncio
@pytest.mark.parametrize(("group_id", "expected_chat_type"), [(123, "group"), (None, "private")])
async def test_process_agent_request_adds_current_chat_metadata(monkeypatch, group_id, expected_chat_type):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            captured["stored_user_id"] = kwargs["user_id"]
            captured["stored_sender_user_id"] = kwargs["sender_user_id"]
            return None

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **_kwargs):
            captured["messages"] = messages
            captured["kwargs"] = _kwargs
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    context = agent.AgentRequestContext(
        event=cast(Any, types.SimpleNamespace)(
            self_id="1",
            get_plaintext=lambda: "hi",
            data=types.SimpleNamespace(
                group_member=types.SimpleNamespace(role="admin") if group_id is not None else None,
            ),
        ),
        user_id="456",
        user_name="项目经理" if group_id is not None else "Bob",
        user_nickname="Bob",
        user_card="项目经理" if group_id is not None else None,
        event_id=1,
        group_id=group_id,
        msg_time=1000,
        text="hi",
        quoted_images=[],
        images=[],
        videos=[],
        direct_mention=group_id is not None,
    )

    await agent._process_agent_request(context)

    assert len(captured["messages"]) == 1
    current_text = _first_text(captured["messages"][-1]["content"])
    payload = json.loads(current_text)
    assert payload["schema"] == "frontier.qq_message.v1"
    assert payload["chat"]["type"] == expected_chat_type
    assert payload["chat"].get("group_id") == (str(group_id) if group_id is not None else None)
    assert payload["sender"]["user_id"] == "456"
    expected_bot_context = {"user_id": "1"}
    if group_id is not None:
        expected_bot_context["directly_mentioned"] = True
    assert payload["bot_context"] == expected_bot_context
    assert payload["sender"]["display_name"] == ("项目经理" if group_id is not None else "Bob")
    if group_id is not None:
        assert payload["sender"]["nickname"] == "Bob"
        assert "card" not in payload["sender"]
        assert payload["content"].startswith("[你被主动@了，这条消息是明确对你说的]")
    else:
        assert payload["content"] == "hi"
    assert "is_current" not in payload
    assert captured["kwargs"]["user_text"] == "hi"
    assert captured["kwargs"]["group_member_role"] == ("admin" if group_id is not None else None)
    assert captured["stored_user_id"] == (1 if group_id is not None else 456)
    assert captured["stored_sender_user_id"] == 1


@pytest.mark.asyncio
async def test_process_agent_request_interprets_empty_text_as_user_calling_bot(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyCognitive:
        async def chat_agent(self, messages, *_args, **_kwargs):
            captured["messages"] = messages
            return {"response": {"messages": [types.SimpleNamespace(text="在呢")]}, "uni_messages": []}

    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")

    context = agent.AgentRequestContext(
        event=cast(Any, types.SimpleNamespace)(self_id="1", get_plaintext=lambda: ""),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=None,
        msg_time=1000,
        text="",
        quoted_images=[],
        images=[],
        videos=[],
    )

    await agent._process_agent_request(context)

    current_text = _first_text(captured["messages"][-1]["content"])
    payload = json.loads(current_text)
    assert payload["content"] == "[用户叫了你一声]"


@pytest.mark.asyncio
async def test_run_serialized_blocks_same_thread_concurrent_requests(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent
    from utils.agents import run_serialized

    calls = []
    first_started = asyncio.Event()
    release_first = asyncio.Event()

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyCognitive:
        async def chat_agent(self, *_args, **_kwargs):
            index = sum(call.startswith("start-") for call in calls)
            calls.append(f"start-{index}")
            if index == 0:
                first_started.set()
                await release_first.wait()
            calls.append(f"end-{index}")
            return {"response": {"messages": [types.SimpleNamespace(text=f"ok-{index}")]}, "uni_messages": []}

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")

    context_a = agent.AgentRequestContext(
        event=cast(Any, types.SimpleNamespace)(self_id="1", get_plaintext=lambda: "first"),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=123,
        msg_time=1000,
        text="first",
        quoted_images=[],
        images=[],
        videos=[],
    )
    context_b = agent.AgentRequestContext(
        event=cast(Any, types.SimpleNamespace)(self_id="1", get_plaintext=lambda: "second"),
        user_id="456",
        user_name="Bob",
        event_id=2,
        group_id=123,
        msg_time=1001,
        text="second",
        quoted_images=[],
        images=[],
        videos=[],
    )
    thread_id = str(agent.agent_thread_id("456", 123))

    task_a = asyncio.create_task(run_serialized(thread_id, agent._process_agent_request(context_a)))
    await first_started.wait()
    task_b = asyncio.create_task(run_serialized(thread_id, agent._process_agent_request(context_b)))
    await asyncio.sleep(0)

    assert calls == ["start-0"]

    release_first.set()
    await task_a
    await task_b

    assert calls == ["start-0", "end-0", "start-1", "end-1"]


def test_system_prompt_describes_message_envelope_and_tool_scope(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    prompt = (agent.PROJECT_ROOT / "prompts" / "AGENTS.md").read_text(encoding="utf-8")

    assert "`frontier.qq_message.v1`" in prompt
    assert "`chat.group_id`" in prompt
    assert "`sender.user_id`" in prompt
    assert "`reply_to`" in prompt
    assert '"private"' in prompt
    assert '"group"' in prompt
    assert "私聊里只用好友/私聊工具" in prompt
    assert "群聊里使用群聊工具" in prompt


@pytest.mark.asyncio
async def test_gateway_approved_message_routes_directly_to_agent(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    sent_messages = []
    stored_messages = []
    sanitized_messages = []
    calls = {"agent": 0}

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "assistant":
                stored_messages.append(kwargs["content"])
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyCognitive:
        async def chat_agent(self, *_args, **_kwargs):
            calls["agent"] += 1
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    class DummyUniMessage:
        def __init__(self, content):
            self.content = content

        @classmethod
        def text(cls, text):
            return cls(text)

        async def send(self):
            sent_messages.append(self.content)

    async def fake_message_extract(_segments):
        return "这个算法怎么优化", [], [], []

    async def fake_message_gateway(_event, _messages):
        return True

    async def fake_sanitize(text):
        sanitized_messages.append(text)
        return text

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "sanitize_outgoing_text", fake_sanitize)
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[{"type": "text", "data": {"text": "这个算法怎么优化"}}],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["agent"] == 1
    assert sent_messages == []
    assert sanitized_messages == ["ok"]
    assert stored_messages == ["ok"]


@pytest.mark.asyncio
async def test_gateway_approved_weather_request_routes_directly_to_agent(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}
    sent_messages = []

    async def fake_run_serialized(_key, coro):
        calls["queue"] += 1
        coro.close()
        return None

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    class DummyUniMessage:
        def __init__(self, content):
            self.content = content

        @classmethod
        def text(cls, text):
            return cls(text)

        async def send(self):
            sent_messages.append(self.content)

    async def fake_message_extract(_segments):
        return "帮我查一下今天北京天气", [], [], []

    async def fake_message_gateway(_event, _messages):
        return True

    monkeypatch.setattr(agent, "run_serialized", fake_run_serialized)
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[{"type": "text", "data": {"text": "帮我查一下今天北京天气"}}],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 1
    assert sent_messages == []


@pytest.mark.asyncio
async def test_process_agent_request_passes_configured_capability_directly(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def insert(self, **_kwargs):
            return None

    class DummyCognitive:
        async def chat_agent(self, *_args, **_kwargs):
            captured["capability"] = _args[3]
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")

    context = agent.AgentRequestContext(
        event=cast(Any, types.SimpleNamespace)(self_id="1"),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=123,
        msg_time=1000,
        text="继续解释一下",
        quoted_images=[],
        images=[],
        videos=[],
    )

    await agent._process_agent_request(context)

    assert captured["capability"] == "high"


@pytest.mark.asyncio
async def test_process_agent_request_sanitizes_final_response(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {"sent": None, "stored": None, "checked": None}

    class DummyMessagesDb:
        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def insert(self, **kwargs):
            if kwargs["role"] == "assistant":
                captured["stored"] = kwargs["content"]

    class DummyCognitive:
        async def chat_agent(self, *_args, **_kwargs):
            return {"response": {"messages": [types.SimpleNamespace(text="unsafe final")]}, "uni_messages": []}

    async def fake_sanitize(text):
        captured["checked"] = text
        return "这段回复被拦住了"

    async def fake_send_messages(_group_id, _message_id, response):
        captured["sent"] = agent.outgoing_message_content(response["messages"][-1])

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "sanitize_outgoing_text", fake_sanitize)
    monkeypatch.setattr(agent, "send_messages", fake_send_messages)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")

    context = agent.AgentRequestContext(
        event=cast(Any, types.SimpleNamespace)(self_id="1"),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=123,
        msg_time=1000,
        text="继续解释一下",
        quoted_images=[],
        images=[],
        videos=[],
    )

    await agent._process_agent_request(context)

    assert captured["checked"] == "unsafe final"
    assert captured["sent"] == "这段回复被拦住了"
    assert captured["stored"] == "这段回复被拦住了"


@pytest.mark.asyncio
async def test_gateway_approved_greeting_runs_agent(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}
    assistant_messages = []
    sent_messages = []

    async def fake_run_serialized(_key, coro):
        calls["queue"] += 1
        coro.close()
        return None

    class DummyMessagesDb:
        async def insert(self, **kwargs):
            if kwargs["role"] == "assistant":
                assistant_messages.append(kwargs["content"])

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_extract(_segments):
        return "早", [], [], []

    async def fake_message_gateway(_event, _messages):
        return True

    class DummyUniMessage:
        def __init__(self, content):
            self.content = content

        @classmethod
        def text(cls, text):
            return cls(text)

        async def send(self):
            sent_messages.append(self.content)

    monkeypatch.setattr(agent, "run_serialized", fake_run_serialized)
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[{"type": "text", "data": {"text": "早"}}],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 1
    assert sent_messages == []
    assert assistant_messages == []


@pytest.mark.asyncio
async def test_gateway_rejected_message_finishes_before_queue(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}

    async def fake_run_serialized(_key, coro):
        calls["queue"] += 1
        coro.close()
        return None

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_extract(_segments):
        return "早", [], [], []

    async def fake_message_gateway(_event, _messages):
        return False

    sent_messages = []

    class DummyUniMessage:
        def __init__(self, content):
            self.content = content

        @classmethod
        def text(cls, text):
            return cls(text)

        async def send(self):
            sent_messages.append(self.content)

    monkeypatch.setattr(agent, "run_serialized", fake_run_serialized)
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[{"type": "text", "data": {"text": "早"}}],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 0
    assert sent_messages == []


@pytest.mark.asyncio
async def test_gateway_approved_closing_message_runs_agent(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}

    async def fake_run_serialized(_key, coro):
        calls["queue"] += 1
        coro.close()
        return None

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return [{"role": "assistant", "content": "{'content': '前一个问题已经回答完毕'}"}]

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_extract(_segments):
        return "谢谢", [], [], []

    async def fake_message_gateway(_event, _messages):
        return True

    monkeypatch.setattr(agent, "run_serialized", fake_run_serialized)
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="group",
        peer_id=123,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[{"type": "text", "data": {"text": "谢谢"}}],
        friend=None,
        group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=456,
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 1


@pytest.mark.asyncio
async def test_gateway_approved_private_chat_routes_to_agent_without_group_reaction(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls: dict[str, Any] = {"queue": 0, "reactions": []}

    async def fake_run_serialized(_key, coro):
        calls["queue"] += 1
        coro.close()
        return None

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return [{"role": "assistant", "content": "{'content': '前一个问题已经回答完毕'}"}]

    class DummyBot:
        async def send_group_message_reaction(self, **kwargs):
            calls["reactions"].append(kwargs)

    async def fake_message_extract(_segments):
        return "谢谢", [], [], []

    async def fake_message_gateway(_event, _messages):
        return True

    monkeypatch.setattr(agent, "run_serialized", fake_run_serialized)
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_MODULE_ENABLED", True)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", False)

    incoming = IncomingMessage(
        message_scene="friend",
        peer_id=456,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[{"type": "text", "data": {"text": "谢谢"}}],
        friend=Friend(
            user_id=456,
            nickname="u",
            sex="unknown",
            qid="",
            remark="",
            category=FriendCategory(category_id=0, category_name="default"),
        ),
        group=None,
        group_member=None,
    )
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 1
    assert calls["reactions"] == []


@pytest.mark.asyncio
async def test_agent_startup_cleans_cached_files_and_schedules_daily_job(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = []

    class DummyMessagesDb:
        async def cleanup_expired_attachments(self):
            calls.append("attachments")
            return 0

        async def repair_legacy_media_attachments(self):
            calls.append("repair")
            return 1, 0

    class DummyScheduler:
        def add_job(self, func, trigger, **kwargs):
            calls.append((func, trigger, kwargs))

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "scheduler", DummyScheduler())
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_AUTO_CLEANUP", True)
    await agent.on_startup()

    assert calls[:2] == ["attachments", "repair"]
    func, trigger, kwargs = calls[2]
    assert func is agent.run_daily_cache_cleanup
    assert trigger == "cron"
    assert kwargs["id"] == agent.CACHE_CLEANUP_JOB_ID
    assert kwargs["hour"] == 4
    assert kwargs["timezone"] == "Asia/Shanghai"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_daily_cache_cleanup_cleans_attachments_and_acp(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = []

    class DummyMessagesDb:
        async def cleanup_expired_attachments(self):
            calls.append("attachments")
            return 2

    class DummyAcpService:
        async def cleanup_cache(self):
            calls.append("acp")
            return 1

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "acp_service", DummyAcpService())
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_AUTO_CLEANUP", True)

    await agent.run_daily_cache_cleanup()

    assert calls == ["attachments", "acp"]
