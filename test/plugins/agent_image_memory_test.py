# ruff: noqa: S101

import ast
import asyncio
import types

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.model.common import Friend, FriendCategory, Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebug import App


async def _noop(*_args, **_kwargs):
    return None


@pytest.mark.asyncio
async def test_agent_saves_images_without_scheduling_summary(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"insert_images": 0, "schedule_summary": 0}
    captured = {}

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            calls["insert_images"] += 1
            return ["cache/images/456/1_0.jpg"]

        async def prepare_message(self, *_args, **_kwargs):
            return []

    class DummyCognitive:
        async def chat_agent(self, *_args, **kwargs):
            captured["image_inputs"] = kwargs.get("image_inputs")
            captured["video_inputs"] = kwargs.get("video_inputs")
            captured["query_text"] = kwargs.get("query_text")
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    class DummyBot:
        async def send_group_message_reaction(self, **_kwargs):
            return None

    async def fake_message_extract(_segments):
        return "hi", [b"image-bytes"], [], [b"video-bytes"]

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
        segments=[{"type": "text", "data": {"text": "hi"}}],
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["insert_images"] == 1
    assert calls["schedule_summary"] == 0
    assert captured["image_inputs"] == [b"image-bytes"]
    assert captured["video_inputs"] == [b"video-bytes"]
    assert captured["query_text"] == "hi\n[视频]"


@pytest.mark.asyncio
async def test_agent_injects_staged_file_memory_path(monkeypatch, tmp_path):  # noqa: C901
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
        return [
            types.SimpleNamespace(
                file_name="report.txt",
                file_size=4,
                virtual_path="/memory/123/files/report.txt",
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["file_items"][0].file_id == "file-1"
    assert captured["memory_dir"] == tmp_path / "sandbox" / "memory" / "123"
    assert captured["workspace_key"] == "123"
    current_text = captured["messages"][-1]["content"][0]["text"]
    payload = ast.literal_eval(current_text)
    assert "/memory/123/files/report.txt" in payload["content"]


@pytest.mark.asyncio
async def test_rejected_group_file_message_stages_file_before_gateway(monkeypatch, tmp_path):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {"agent_calls": 0}

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
    event = MessageEvent(data=incoming, to_me=False, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["file_items"][0].file_id == "/dbd89abd-f51a-4160-b8bd-8f10cc27c585"
    assert captured["memory_dir"] == tmp_path / "sandbox" / "memory" / "1035400922"
    assert "/memory/1035400922/files/Clear icon cache.bat" in captured["stored_content"]
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

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
    current_text = captured["messages"][-1]["content"][0]["text"]
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["stored_content"] == "[视频:12秒]"
    current_text = captured["messages"][-1]["content"][0]["text"]
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert "[引用消息]" in captured["stored_content"]
    assert "用户(Alice): 原始消息内容" in captured["stored_content"]
    current = captured["messages"][-1]["content"][0]["text"]
    assert "[引用消息]" in current
    assert "用户(Alice): 原始消息内容" in current


@pytest.mark.asyncio
async def test_agent_fetches_missing_quoted_image_from_milky(monkeypatch):  # noqa: C901
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
            return [types.SimpleNamespace(id=1, file_name="500_0.jpg", physical_path="cache/images/111/500_0.jpg")]

        def load_attachment_files(self, _records):
            return [], 1

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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert captured["restored_images"][0]["msg_time"] == 500
    assert captured["restored_images"][0]["images"] == [b"quoted-image"]
    current_content = captured["messages"][-1]["content"]
    assert current_content[0]["type"] == "text"
    assert "用户(Alice): [图片]" in current_content[0]["text"]
    assert current_content[1]["type"] == "image_url"


@pytest.mark.asyncio
@pytest.mark.parametrize(("group_id", "expected_chat_type"), [(123, "group"), (None, "private")])
async def test_process_agent_request_adds_current_chat_metadata(monkeypatch, group_id, expected_chat_type):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
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
        bot=None,
        event=types.SimpleNamespace(
            self_id="1",
            get_plaintext=lambda: "hi",
            data=types.SimpleNamespace(
                group_member=types.SimpleNamespace(role="admin") if group_id is not None else None,
            ),
        ),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=group_id,
        msg_time=1000,
        text="hi",
        quoted_images=[],
        images=[],
        videos=[],
    )

    await agent._process_agent_request(context, [{"role": "assistant", "content": "history"}])

    current_text = captured["messages"][-1]["content"][0]["text"]
    payload = ast.literal_eval(current_text)
    assert payload["metadata"]["chat_type"] == expected_chat_type
    assert payload["metadata"]["group_id"] == group_id
    assert payload["metadata"]["user_id"] == "456"
    assert payload["is_current"] is True
    assert captured["kwargs"]["group_member_role"] == ("admin" if group_id is not None else None)


@pytest.mark.asyncio
async def test_agent_queue_serializes_same_thread_chat_jobs(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent
    from utils.agent_queue import AgentQueueManager

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
    monkeypatch.setattr(
        agent, "agent_queue", AgentQueueManager(maxsize=2, idle_ttl_seconds=1.0, job_timeout_seconds=1.0)
    )
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "none")

    context_a = agent.AgentRequestContext(
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
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
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
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
    thread_id = agent._agent_thread_id("456", 123)

    task_a = asyncio.create_task(agent.agent_queue.submit(thread_id, lambda: agent._process_agent_request(context_a)))
    await first_started.wait()
    task_b = asyncio.create_task(agent.agent_queue.submit(thread_id, lambda: agent._process_agent_request(context_b)))
    await asyncio.sleep(0)

    assert calls == ["start-0"]

    release_first.set()
    await task_a
    await task_b

    assert calls == ["start-0", "end-0", "start-1", "end-1"]

    await agent.agent_queue.aclose()


def test_system_prompt_describes_chat_metadata_and_tool_scope(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    prompt = (agent.PROJECT_ROOT / "prompts" / "AGENTS.md").read_text(encoding="utf-8")

    assert "`chat_type`" in prompt
    assert "`group_id`" in prompt
    assert "`user_id`" in prompt
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

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

    class DummyQueue:
        async def submit(self, *_args, **_kwargs):
            calls["queue"] += 1

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

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

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
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
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
        captured["sent"] = response["messages"][-1].text

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "sanitize_outgoing_text", fake_sanitize)
    monkeypatch.setattr(agent, "send_messages", fake_send_messages)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")

    context = agent.AgentRequestContext(
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
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
async def test_gateway_approved_greeting_routes_to_agent_queue(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}
    assistant_messages = []
    sent_messages = []

    class DummyQueue:
        async def submit(self, *_args, **_kwargs):
            calls["queue"] += 1

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

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

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
    class DummyQueue:
        async def submit(self, *_args, **_kwargs):
            calls["queue"] += 1

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

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 0
    assert sent_messages == []


@pytest.mark.asyncio
async def test_gateway_approved_closing_message_routes_to_agent_queue(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}

    class DummyQueue:
        async def submit(self, *_args, **_kwargs):
            calls["queue"] += 1

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

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

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

    calls = {"queue": 0, "reactions": []}

    class DummyQueue:
        async def submit(self, *_args, **_kwargs):
            calls["queue"] += 1

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

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()

    assert calls["queue"] == 1
    assert calls["reactions"] == []


@pytest.mark.asyncio
async def test_agent_startup_only_cleans_cached_files(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = []

    class DummyMessagesDb:
        async def cleanup_expired_attachments(self):
            calls.append("attachments")
            return 0

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_AUTO_CLEANUP", True)
    monkeypatch.setattr(agent, "cleanup_expired_staged_artifacts", lambda: 0)

    await agent.on_startup()

    assert calls == ["attachments"]


@pytest.mark.asyncio
async def test_agent_finishes_when_thread_queue_is_full(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent
    from utils.agent_queue import AgentQueueFullError

    class FullQueue:
        async def submit(self, *_args, **_kwargs):
            raise AgentQueueFullError("thread", 2)

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
        return "hi", [], [], []

    async def fake_message_gateway(_event, _messages):
        return True

    monkeypatch.setattr(agent, "agent_queue", FullQueue())
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
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
        segments=[{"type": "text", "data": {"text": "hi"}}],
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
    event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "前面还有请求在处理，稍等一下")
        ctx.should_finished()
