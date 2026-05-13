# ruff: noqa: S101

import asyncio
import types

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebug import App


async def _noop(*_args, **_kwargs):
    return None


async def _reply_yes(*_args, **_kwargs):
    return types.SimpleNamespace(should_reply=True, needs_agent=True, pre_response=None)


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
    monkeypatch.setattr(agent, "_agent_choice_should_reply", _reply_yes)
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

        async def select_images_by_msg_time(self, _msg_time):
            return []

        def load_image_files(self, _records):
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
    monkeypatch.setattr(agent, "_agent_choice_should_reply", _reply_yes)
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

        async def select_images_by_msg_time(self, _msg_time):
            return [types.SimpleNamespace(id=1, index=0, file_path="cache/images/111/500_0.jpg")]

        def load_image_files(self, _records):
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

        async def get_resource_temp_url(self, resource_id):
            assert resource_id == "resource-1"
            return "https://fresh.example/image.jpg"

    async def fake_get(url):
        if "expired" in url:
            raise RuntimeError("expired")
        return types.SimpleNamespace(content=b"quoted-image")

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "_agent_choice_should_reply", _reply_yes)
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(
        agent.build_reply_context.__globals__["_message_utils"](), "httpx_client", types.SimpleNamespace(get=fake_get)
    )
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


def test_agent_choice_input_uses_plain_text_only(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    context = agent.AgentRequestContext(
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=123,
        msg_time=1000,
        text="谢谢",
        quoted_images=[b"quoted-image"],
        images=[b"image"],
        videos=[b"video"],
    )

    result = agent._build_agent_choice_input(
        context,
        [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "前一个问题已经回答完毕"},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
                ],
            },
            {"role": "user", "content": "我只是评价一下"},
        ],
    )

    assert result == "assistant: 前一个问题已经回答完毕\nuser: 我只是评价一下\nuser: 谢谢"
    assert "recent_context" not in result
    assert "latest_input" not in result
    assert "image_url" not in result
    assert "[图片" not in result
    assert "[视频" not in result


@pytest.mark.asyncio
async def test_agent_choice_uses_signal_llm(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    async def fake_signal_structured(system_prompt, user_prompt, schema, **kwargs):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        captured["schema"] = schema
        captured["kwargs"] = kwargs
        return schema(should_reply=True, needs_agent=True, pre_response="让我想想...")

    context = agent.AgentRequestContext(
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=123,
        msg_time=1000,
        text="这个问题怎么解决",
        quoted_images=[],
        images=[],
        videos=[],
    )

    monkeypatch.setattr(agent, "signal_structured", fake_signal_structured)

    result = await agent._agent_choice_should_reply(context, [{"role": "user", "content": "history"}])

    assert result.needs_agent is True
    assert captured["schema"] is agent.AgentChoice
    assert "reply-gate classifier" in captured["system_prompt"]
    assert captured["user_prompt"] == "user: history\nuser: 这个问题怎么解决"
    assert captured["kwargs"]["temperature"] == 0.7
    assert captured["kwargs"]["model_kwargs"] == {"extra_body": {"thinking": {"type": "disabled"}}}


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

    async def fake_signal_structured(*_args, **_kwargs):
        raise AssertionError("AgentChoice should not select the reasoning capability")

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "signal_structured", fake_signal_structured, raising=False)
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
async def test_agent_choice_short_reply_sends_without_queue(monkeypatch):  # noqa: C901
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

    async def fake_signal_structured(*_args, **_kwargs):
        return agent.AgentChoice(should_reply=True, needs_agent=False, pre_response="早 今天起这么早")

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
    monkeypatch.setattr(agent, "signal_structured", fake_signal_structured, raising=False)
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
    assert sent_messages == ["早 今天起这么早"]
    assert assistant_messages == ["早 今天起这么早"]


@pytest.mark.asyncio
async def test_agent_choice_short_reply_sanitizes_unsafe_output(monkeypatch):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}
    assistant_messages = []

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

    async def fake_signal_structured(*_args, **_kwargs):
        return agent.AgentChoice(should_reply=True, needs_agent=False, pre_response="unsafe short")

    async def fake_sanitize(text):
        assert text == "unsafe short"
        return "这段回复被拦住了"

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
    monkeypatch.setattr(agent, "signal_structured", fake_signal_structured, raising=False)
    monkeypatch.setattr(agent, "sanitize_outgoing_text", fake_sanitize)
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
    assert sent_messages == ["这段回复被拦住了"]
    assert assistant_messages == ["这段回复被拦住了"]


@pytest.mark.asyncio
async def test_agent_choice_false_finishes_before_queue(monkeypatch):  # noqa: C901
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

    async def fake_signal_structured(*_args, **_kwargs):
        return agent.AgentChoice(should_reply=False, needs_agent=False, pre_response=None)

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "get_bot", lambda: DummyBot())
    monkeypatch.setattr(agent, "message_extract", fake_message_extract)
    monkeypatch.setattr(agent, "message_gateway", fake_message_gateway)
    monkeypatch.setattr(agent, "signal_structured", fake_signal_structured, raising=False)
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

    assert calls["queue"] == 0


@pytest.mark.asyncio
async def test_agent_startup_only_cleans_cached_files(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = []

    class DummyMessagesDb:
        async def cleanup_expired_images(self):
            calls.append("images")
            return 0

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent.EnvConfig, "IMAGE_AUTO_CLEANUP", True)
    monkeypatch.setattr(agent, "cleanup_expired_staged_artifacts", lambda: 0)

    await agent.on_startup()

    assert calls == ["images"]


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
    monkeypatch.setattr(agent, "_agent_choice_should_reply", _reply_yes)
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
