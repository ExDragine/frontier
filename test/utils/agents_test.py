# ruff: noqa: S101

import asyncio
import os
import types
import uuid

import pytest

from utils import agents

# ── 共享 async 迭代工具 ──────────────────────────────────────────


class _AsyncIter:
    """可在测试中注入的异步迭代器。"""

    def __init__(self, items):
        self._items = list(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(0)
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


# ── 测试 ──────────────────────────────────────────────


class _FakeStream:
    """Minimal astream_events v3 return-object mock — exposes .output() async method."""

    def __init__(self, result: dict):
        self._output_result = result

    async def output(self):
        return self._output_result


@pytest.mark.asyncio
async def test_assistant_agent_model_selection(monkeypatch):
    class DummyAgent:
        async def ainvoke(self, payload):
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok")]}

    def fake_create_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_agent", fake_create_agent)

    class DummyModel:
        pass

    monkeypatch.setattr(agents, "create_llm", lambda model, **_kw: DummyModel())

    result = await agents.assistant_agent(user_prompt="hello", use_model="claude-3")
    assert result == "ok"


def test_frontier_load_system_prompt_missing():
    """测试 env.toml 未配置 system_prompt 时返回错误提示"""
    # 测试 fixture 的 env.toml 没有 system_prompt，应返回配置错误
    prompt = agents.FrontierCognitive.load_system_prompt()
    assert "配置错误" in prompt


@pytest.mark.asyncio
async def test_extract_uni_messages():
    response = {
        "messages": [
            types.SimpleNamespace(type="tool", name="tool", artifact="payload"),
            types.SimpleNamespace(type="ai", content="ok"),
        ]
    }
    result = await agents.FrontierCognitive.extract_uni_messages(response)
    assert result == ["payload"]


@pytest.mark.asyncio
async def test_extract_uni_messages_loads_staged_artifact_from_final_text(monkeypatch, tmp_path):
    from utils import staged_artifacts

    class DummyUniMessage:
        def __init__(self, content=None):
            self.content = content

        @classmethod
        def image(cls, url=None, path=None, raw=None, **_kwargs):
            return cls({"type": "image", "url": url, "path": str(path) if path else None, "raw": raw})

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(agents, "UniMessage", DummyUniMessage, raising=False)
    artifact_id = staged_artifacts.stage_artifact(DummyUniMessage.image(raw=b"img"))
    response = {
        "messages": [
            types.SimpleNamespace(
                type="ai",
                content=f'<staged_artifact artifact_id="{artifact_id}" send_tool="send_staged_artifact" />',
            )
        ]
    }

    result = await agents.FrontierCognitive.extract_uni_messages(response)

    assert [artifact.content for artifact in result] == [{"type": "image", "url": None, "path": None, "raw": b"img"}]


@pytest.mark.asyncio
async def test_extract_uni_messages_does_not_duplicate_when_send_tool_already_ran(monkeypatch, tmp_path):
    from utils import staged_artifacts

    class DummyUniMessage:
        def __init__(self, content=None):
            self.content = content

        @classmethod
        def image(cls, url=None, path=None, raw=None, **_kwargs):
            return cls({"type": "image", "url": url, "path": str(path) if path else None, "raw": raw})

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(agents, "UniMessage", DummyUniMessage, raising=False)
    artifact_id = staged_artifacts.stage_artifact(DummyUniMessage.image(raw=b"img"))
    response = {
        "messages": [
            types.SimpleNamespace(type="tool", name="send_staged_artifact", artifact="already-sent"),
            types.SimpleNamespace(
                type="ai",
                content=f'<staged_artifact artifact_id="{artifact_id}" send_tool="send_staged_artifact" />',
            ),
        ]
    }

    result = await agents.FrontierCognitive.extract_uni_messages(response)

    assert result == ["already-sent"]


def test_clean_staged_artifact_handoffs_from_ai_message():
    message = types.SimpleNamespace(
        content=(
            '完成\n<staged_artifact artifact_id="00000000-0000-4000-8000-000000000000" '
            'send_tool="send_staged_artifact" />'
        )
    )

    cleaned = agents.FrontierCognitive.clean_staged_artifact_handoffs(message)

    assert cleaned.content == "完成"


def test_env_config_responses_api_defaults():
    from utils.configs import EnvConfig

    assert EnvConfig.BASIC_MODEL_USE_RESPONSES_API is True
    assert EnvConfig.ADVAN_MODEL_USE_RESPONSES_API is True


def test_build_user_content_omits_images_when_model_lacks_vision():
    content = agents._build_user_content("hello", [b"image-bytes"], supports_vision=False)

    assert isinstance(content, str)
    assert "hello" in content
    assert "图片已省略" in content


def test_build_user_content_keeps_images_when_model_supports_vision():
    content = agents._build_user_content("hello", [b"image-bytes"], supports_vision=True)

    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "hello"}
    assert content[1]["type"] == "image_url"


def test_filter_messages_for_text_only_model_removes_image_parts(monkeypatch):
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: False)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
            ],
        }
    ]

    filtered = agents._filter_messages_for_model_capabilities(messages, "text-model", endpoint="")

    assert filtered[0]["content"] == [{"type": "text", "text": "hello\n\n[图片已省略：当前模型不支持视觉输入]"}]
    assert messages[0]["content"][1]["type"] == "image_url"


def test_frontier_cognitive_uses_main_tools(monkeypatch):
    monkeypatch.setattr(agents.agent_tools, "all_tools", ["all-tool"], raising=False)
    monkeypatch.setattr(agents.agent_tools, "main_tools", ["main-tool"], raising=False)

    frontier = agents.FrontierCognitive()

    assert frontier.tools == ["main-tool"]
    assert not hasattr(frontier, "subagents")


@pytest.mark.asyncio
async def test_assistant_agent_uses_basic_model_config(monkeypatch):
    import types

    from utils import agents

    captured = {}

    class DummyAgent:
        async def ainvoke(self, payload):
            captured["payload"] = payload
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok")]}

    def fake_create_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_agent", fake_create_agent)

    def capturing_create_llm(model, **kwargs):
        captured.update(kwargs)
        captured["model"] = model

        class DummyModel:
            pass

        return DummyModel()

    monkeypatch.setattr(agents, "create_llm", capturing_create_llm)

    # Monkeypatch the EnvConfig in the agents module
    monkeypatch.setattr(agents.EnvConfig, "BASIC_MODEL_USE_RESPONSES_API", False)
    monkeypatch.setattr(agents.EnvConfig, "BASIC_MODEL_PROVIDER", "anthropic")
    monkeypatch.setattr(agents.EnvConfig, "BASIC_MODEL_ENDPOINT", "anthropic_proxy")
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: False)

    await agents.assistant_agent(user_prompt="hello", images=[b"image-bytes"])

    assert captured.get("use_responses_api") is False
    assert captured.get("provider") == "anthropic"
    assert captured.get("endpoint") == "anthropic_proxy"
    assert "图片已省略" in captured["payload"]["messages"][0]["content"]


@pytest.mark.asyncio
async def test_assistant_agent_uses_signal_model_config(monkeypatch):
    import types

    from utils import agents

    captured = {}

    class DummyAgent:
        async def ainvoke(self, payload):
            captured["payload"] = payload
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok")]}

    monkeypatch.setattr(agents, "create_agent", lambda **_kwargs: DummyAgent())

    def capturing_create_llm(model, **kwargs):
        captured.update(kwargs)
        captured["model"] = model
        return object()

    monkeypatch.setattr(agents, "create_llm", capturing_create_llm)
    monkeypatch.setattr(agents.EnvConfig, "SIGNAL_MODEL", "signal-model")
    monkeypatch.setattr(agents.EnvConfig, "SIGNAL_MODEL_PROVIDER", "deepseek")
    monkeypatch.setattr(agents.EnvConfig, "SIGNAL_MODEL_ENDPOINT", "deepseek_signal")

    await agents.assistant_agent(user_prompt="hello", use_model="signal-model")

    assert captured["model"] == "signal-model"
    assert captured["provider"] == "deepseek"
    assert captured["endpoint"] == "deepseek_signal"


@pytest.mark.asyncio
async def test_assistant_agent_parses_structured_response_from_ai_json_text(monkeypatch):
    from pydantic import BaseModel

    class StructuredPayload(BaseModel):
        title: str
        count: int

    class DummyAgent:
        async def ainvoke(self, _payload):
            return {"messages": [types.SimpleNamespace(type="ai", text='{"title": "日报", "count": 2}', content="")]}

    monkeypatch.setattr(agents, "create_agent", lambda **_kwargs: DummyAgent())
    monkeypatch.setattr(agents, "create_llm", lambda **_kwargs: object())

    result = await agents.assistant_agent(
        system_prompt="system",
        user_prompt="hello",
        use_model="any-model",
        response_format=StructuredPayload,
    )

    assert result == StructuredPayload(title="日报", count=2)


@pytest.mark.asyncio
async def test_chat_agent_drops_reasoning_params_when_chat_completions(monkeypatch):
    import types

    from utils import agents

    class DummyAgent:
        async def astream_events(self, payload, config=None, version=None):
            captured["payload"] = payload
            captured["config"] = config
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)

    captured = {}

    def capturing_create_llm(**kwargs):
        captured.update(kwargs)

        class DummyModel:
            pass

        return DummyModel()

    monkeypatch.setattr(agents, "create_llm", capturing_create_llm)
    monkeypatch.setattr(agents.EnvConfig, "ADVAN_MODEL_USE_RESPONSES_API", False)
    monkeypatch.setattr(agents.EnvConfig, "ADVAN_MODEL_PROVIDER", "openai")
    monkeypatch.setattr(agents.EnvConfig, "ADVAN_MODEL_ENDPOINT", "openrouter")
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: False)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.backend = None

    await frontier.chat_agent(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hi"},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
                ],
            }
        ],
        user_id="u1",
        user_name="test",
        group_id=123,
    )

    assert captured.get("use_responses_api") is False
    assert captured.get("provider") == "openai"
    assert captured.get("endpoint") == "openrouter"
    assert "reasoning_effort" not in captured
    assert "verbosity" not in captured
    assert captured["payload"]["messages"][0]["content"] == [
        {"type": "text", "text": "hi\n\n[图片已省略：当前模型不支持视觉输入]"}
    ]
    assert str(captured["config"]["configurable"]["thread_id"]) == str(agents._agent_thread_id("u1", 123))


@pytest.mark.asyncio
async def test_chat_agent_uses_group_id_scoped_workspace(monkeypatch, tmp_path):
    import types

    from utils import agents

    captured = {}

    class DummyAgent:
        async def astream_events(self, input=None, config=None, version=None):
            captured["payload"] = input
            captured["config"] = config
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr(agents, "create_llm", lambda **_kwargs: object())
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: True)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.working_dir = str(tmp_path / "sandbox")

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
        group_id=123,
        group_member_role="owner",
    )

    backend = captured["backend"]

    assert isinstance(backend, agents.CompositeBackend)
    assert backend.default.virtual_mode is True
    assert backend.default.root_dir == str(tmp_path / "sandbox" / "workspaces" / "123")
    assert set(backend.routes) == {"/skills/", "/memory/123/"}
    assert backend.routes["/skills/"].root_dir == str(tmp_path / "sandbox" / "skills")
    assert backend.routes["/memory/123/"].root_dir == str(tmp_path / "sandbox" / "memory" / "123")
    assert captured["skills"] == ["/skills"]
    assert captured["memory"] == ["/memory/123/AGENTS.md"]
    assert (tmp_path / "sandbox" / "workspaces" / "123").is_dir()
    assert (tmp_path / "sandbox" / "skills").is_dir()
    assert (tmp_path / "sandbox" / "memory").is_dir()
    assert captured["config"]["configurable"]["workspace_dir"] == str(tmp_path / "sandbox" / "workspaces" / "123")
    assert captured["config"]["configurable"]["group_member_role"] == "owner"


@pytest.mark.asyncio
async def test_chat_agent_uses_user_id_scoped_workspace_for_dm(monkeypatch, tmp_path):
    import types

    from utils import agents

    captured = {}

    class DummyAgent:
        async def astream_events(self, payload, config=None, version=None):
            captured["payload"] = payload
            captured["config"] = config
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr(agents, "create_llm", lambda **_kwargs: object())
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: True)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.working_dir = str(tmp_path / "sandbox")

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
        group_id=None,
    )

    assert captured["backend"].default.root_dir == str(tmp_path / "sandbox" / "workspaces" / "u1")
    assert captured["config"]["configurable"]["workspace_dir"] == str(tmp_path / "sandbox" / "workspaces" / "u1")
    assert (tmp_path / "sandbox" / "workspaces" / "u1").is_dir()


@pytest.mark.asyncio
async def test_chat_agent_passes_base_system_prompt_from_load_method(monkeypatch, tmp_path):
    """load_system_prompt 返回的 system prompt 直接透传给 create_deep_agent，不做额外拼接。"""
    import types

    from utils import agents

    captured = {}

    class DummyAgent:
        async def astream_events(self, payload, config=None, version=None):
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr(agents, "create_llm", lambda **_kwargs: object())
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        agents.FrontierCognitive, "load_system_prompt", staticmethod(lambda *_args, **_kwargs: "base prompt")
    )

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.working_dir = str(tmp_path / "sandbox")

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
    )

    assert captured["system_prompt"] == "base prompt"


def test_agent_thread_id_isolated_by_group_and_user():
    group_user = agents._agent_thread_id("u1", 123)
    same_user_other_group = agents._agent_thread_id("u1", 456)
    other_user_same_group = agents._agent_thread_id("u2", 123)
    dm_user = agents._agent_thread_id("u1", None)

    assert group_user != same_user_other_group
    assert group_user != other_user_same_group
    assert group_user != dm_user


@pytest.mark.asyncio
async def test_chat_agent_includes_reasoning_params_when_responses_api(monkeypatch):
    import types

    from utils import agents

    class DummyAgent:
        async def astream_events(self, payload, config=None, version=None):
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)

    captured = {}

    def capturing_create_llm(**kwargs):
        captured.update(kwargs)

        class DummyModel:
            pass

        return DummyModel()

    monkeypatch.setattr(agents, "create_llm", capturing_create_llm)
    monkeypatch.setattr(agents.EnvConfig, "ADVAN_MODEL_USE_RESPONSES_API", True)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.subagents = []
    frontier.backend = None

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
        capability="medium",
    )

    assert captured.get("use_responses_api") is True
    assert captured.get("reasoning_effort") == "medium"
    assert captured.get("verbosity") == "low"


@pytest.mark.asyncio
async def test_chat_agent_uses_configured_agent_llm_timeout(monkeypatch):
    from utils import agents

    class DummyAgent:
        async def astream_events(self, payload, config=None, version=None):
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)

    captured = {}

    def capturing_create_llm(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(agents, "create_llm", capturing_create_llm)
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(agents.EnvConfig, "AGENT_LLM_TIMEOUT_SECONDS", 1234, raising=False)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.working_dir = os.getcwd()

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
    )

    assert captured["timeout"] == 1234


class TestProgressEvent:
    """ProgressEvent 类型单元测试。"""

    def test_construct_minimal(self):
        from utils.agents import ProgressEvent

        event = ProgressEvent(type="thinking", message="test")
        assert event.type == "thinking"
        assert event.message == "test"
        assert event.detail is None

    def test_construct_with_detail(self):
        from utils.agents import ProgressEvent

        event = ProgressEvent(
            type="tool_call",
            message="test",
            detail={"tool_name": "search"},
        )
        assert event.detail == {"tool_name": "search"}

    def test_all_type_literals_valid(self):
        from utils.agents import ProgressEvent

        valid_types = [
            "thinking",
            "tool_call",
            "tool_result",
            "subagent_start",
            "subagent_done",
            "text_delta",
            "done",
        ]
        for t in valid_types:
            event = ProgressEvent(type=t, message="test")
            assert event.type == t


class TestEmitProgress:
    """_emit_progress 安全调用测试。"""

    @pytest.mark.asyncio
    async def test_does_nothing_when_reporter_is_none(self):
        from utils.agents import ProgressEvent, _emit_progress

        event = ProgressEvent(type="thinking", message="test")
        # 不应抛异常
        await _emit_progress(None, event)

    @pytest.mark.asyncio
    async def test_calls_reporter_with_event(self):
        from utils.agents import ProgressEvent, _emit_progress

        received: list[ProgressEvent] = []

        async def reporter(e: ProgressEvent) -> None:
            received.append(e)

        event = ProgressEvent(type="thinking", message="hello")
        await _emit_progress(reporter, event)
        assert len(received) == 1
        assert received[0] is event

    @pytest.mark.asyncio
    async def test_reporter_exception_does_not_propagate(self):
        from utils.agents import ProgressEvent, _emit_progress

        async def failing_reporter(_e: ProgressEvent) -> None:
            raise RuntimeError("boom")

        event = ProgressEvent(type="thinking", message="test")
        # 不应抛异常
        await _emit_progress(failing_reporter, event)


class TestCollectProgress:
    """_collect_progress 消费 astream_events v3 projection 的测试。"""

    @staticmethod
    def _mock_stream(*, subagents=(), tool_calls=(), messages=()):
        """构造一个与 astream_events v3 接口兼容的 mock stream。"""

        class MockStream:
            def __init__(self):
                self.subagents = _AsyncIter(subagents)
                self.tool_calls = _AsyncIter(tool_calls)
                self.messages = _AsyncIter(messages)

        return MockStream()

    @pytest.mark.asyncio
    async def test_noop_when_reporter_is_none(self):
        from utils.agents import _collect_progress

        stream = self._mock_stream()
        # 不应抛异常（_emit_progress 短路）
        await _collect_progress(stream, None)

    @pytest.mark.asyncio
    async def test_emits_thinking_on_first_message(self):
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        mock_text = MagicMock()
        mock_text.__aiter__.return_value = iter([])  # 空文本迭代器

        mock_msg = MagicMock()
        mock_msg.text = mock_text

        stream = self._mock_stream(messages=[mock_msg])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        thinking_calls = [c for c in reporter.call_args_list if c[0][0].type == "thinking"]
        assert len(thinking_calls) == 1

    @pytest.mark.asyncio
    async def test_emits_subagent_start(self):
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        mock_sub = MagicMock()
        mock_sub.name = "research"

        stream = self._mock_stream(subagents=[mock_sub])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        subagent_calls = [c for c in reporter.call_args_list if c[0][0].type == "subagent_start"]
        assert len(subagent_calls) == 1
        assert subagent_calls[0][0][0].detail["name"] == "research"

    @pytest.mark.asyncio
    async def test_emits_tool_call(self):
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        mock_tc = MagicMock()
        mock_tc.tool_name = "web_search"

        stream = self._mock_stream(tool_calls=[mock_tc])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        tool_calls = [c for c in reporter.call_args_list if c[0][0].type == "tool_call"]
        assert len(tool_calls) == 1
        assert tool_calls[0][0][0].detail["tool_name"] == "web_search"

    @pytest.mark.asyncio
    async def test_dedup_consecutive_same_tool_calls(self):
        """连续调用同一工具时，只发送第一条进度事件。"""
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        tc1 = MagicMock()
        tc1.tool_name = "search"
        tc2 = MagicMock()
        tc2.tool_name = "search"
        tc3 = MagicMock()
        tc3.tool_name = "search"
        tc4 = MagicMock()
        tc4.tool_name = "execute"

        stream = self._mock_stream(tool_calls=[tc1, tc2, tc3, tc4])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        tool_calls = [c for c in reporter.call_args_list if c[0][0].type == "tool_call"]
        assert len(tool_calls) == 2, f"Expected 2 unique tool calls, got {len(tool_calls)}"
        assert tool_calls[0][0][0].detail["tool_name"] == "search"
        assert tool_calls[1][0][0].detail["tool_name"] == "execute"

    @pytest.mark.asyncio
    async def test_dedup_consecutive_same_subagents(self):
        """连续启动同一子代理时，只发送第一条进度事件。"""
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        sa1 = MagicMock()
        sa1.name = "coder"
        sa2 = MagicMock()
        sa2.name = "coder"
        sa3 = MagicMock()
        sa3.name = "reviewer"

        stream = self._mock_stream(subagents=[sa1, sa2, sa3])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        subagent_calls = [c for c in reporter.call_args_list if c[0][0].type == "subagent_start"]
        assert len(subagent_calls) == 2, f"Expected 2 unique subagent events, got {len(subagent_calls)}"
        assert subagent_calls[0][0][0].detail["name"] == "coder"
        assert subagent_calls[1][0][0].detail["name"] == "reviewer"

    @pytest.mark.asyncio
    async def test_one_consumer_failure_does_not_block_others(self):
        from unittest.mock import MagicMock

        import utils.agents as agents_mod

        # 让 tool_calls 迭代器抛异常
        class _FailingIter:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise RuntimeError("tool_call projection failed")

        mock_msg = MagicMock()
        mock_msg.text = MagicMock()
        mock_msg.text.__aiter__.return_value = iter([])

        stream = self._mock_stream(messages=[mock_msg])
        stream.tool_calls = _FailingIter()  # 替换为失败的
        reporter = MagicMock()

        # 不应抛异常，thinking 事件仍应被发出
        await agents_mod._collect_progress(stream, reporter)

        thinking_calls = [c for c in reporter.call_args_list if c[0][0].type == "thinking"]
        assert len(thinking_calls) == 1, "thinking event should still emit even if tool_calls fails"

    @pytest.mark.asyncio
    async def test_paragraph_split_text_delta(self):
        """文本按 \\n\\n 段落边界切分并发出 text_delta 事件。"""
        from unittest.mock import AsyncMock, MagicMock

        from utils.agents import _collect_progress

        text_chunks = iter(["段落一\n\n段落二\n\n"])

        mock_text = MagicMock()
        mock_text.__aiter__.return_value = text_chunks

        mock_msg = MagicMock()
        mock_msg.text = mock_text

        stream = self._mock_stream(messages=[mock_msg])
        reporter = AsyncMock()

        await _collect_progress(stream, reporter)

        text_delta_calls = [c for c in reporter.call_args_list if c[0][0].type == "text_delta"]
        assert len(text_delta_calls) == 2, f"Expected 2 text_delta events, got {len(text_delta_calls)}"
        assert text_delta_calls[0][0][0].message == "段落一"
        assert text_delta_calls[1][0][0].message == "段落二"

    @pytest.mark.asyncio
    async def test_trailing_text_without_newline_is_buffered(self):
        """不含 \\n\\n 结尾的文本留在 buffer 中不发出。"""
        from unittest.mock import AsyncMock, MagicMock

        from utils.agents import _collect_progress

        mock_text = MagicMock()
        mock_text.__aiter__.return_value = iter(["未完结文本"])

        mock_msg = MagicMock()
        mock_msg.text = mock_text

        stream = self._mock_stream(messages=[mock_msg])
        reporter = AsyncMock()

        await _collect_progress(stream, reporter)

        text_delta_calls = [c for c in reporter.call_args_list if c[0][0].type == "text_delta"]
        assert len(text_delta_calls) == 0, "Trailing text should be buffered, not emitted"


class TestChatAgentStreaming:
    """chat_agent 流式改造的集成测试。"""

    @pytest.mark.asyncio
    async def test_no_reporter_behavior_unchanged(self, monkeypatch):
        """不传 progress_reporter 时，chat_agent 行为与 ainvoke 时期一致。"""
        from unittest.mock import AsyncMock, MagicMock

        import utils.agents as agents_mod

        # Mock create_deep_agent 返回的 agent
        mock_stream = MagicMock()
        mock_stream.output = AsyncMock(
            return_value={
                "messages": [
                    type("FakeAIMsg", (), {"type": "ai", "text": "hello", "content": "hello"})(),
                ],
                "user_id": "123",
                "group_id": None,
            }
        )

        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=mock_stream)

        monkeypatch.setattr(agents_mod, "create_deep_agent", MagicMock(return_value=mock_agent))
        monkeypatch.setattr(agents_mod, "_build_agent_backend", MagicMock())
        monkeypatch.setattr(agents_mod, "_agent_thread_id", MagicMock(return_value=uuid.uuid4()))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "load_system_prompt", lambda *a, **kw: "You are a bot.")
        monkeypatch.setattr(agents_mod.FrontierCognitive, "extract_uni_messages", AsyncMock(return_value=[]))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "clean_staged_artifact_handoffs", lambda msg: msg)

        cognitive = agents_mod.FrontierCognitive()
        result = await cognitive.chat_agent(
            messages=[{"role": "user", "content": "hi"}],
            user_id="123",
            user_name="tester",
            progress_reporter=None,  # 不传 reporter
        )

        assert isinstance(result, dict)
        assert "response" in result
        assert "total_time" in result
        assert "uni_messages" in result
        # 验证 astream_events 被调用
        mock_agent.astream_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_reporter_receives_events(self, monkeypatch):
        """传入 progress_reporter 时，_collect_progress 应被调用。"""
        from unittest.mock import AsyncMock, MagicMock

        import utils.agents as agents_mod

        mock_agent_output = {
            "messages": [
                type("FakeAIMsg", (), {"type": "ai", "text": "hello", "content": "hello"})(),
            ],
            "user_id": "123",
            "group_id": None,
        }

        mock_stream = MagicMock()

        # output 现在是 async method；用 async def 函数直接赋值
        async def _delayed_output():
            await asyncio.sleep(0)
            return mock_agent_output

        mock_stream.output = _delayed_output

        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=mock_stream)

        collector_called: list = []

        async def fake_collect(stream, reporter):
            collector_called.append((stream, reporter))

        monkeypatch.setattr(agents_mod, "create_deep_agent", MagicMock(return_value=mock_agent))
        monkeypatch.setattr(agents_mod, "_build_agent_backend", MagicMock())
        monkeypatch.setattr(agents_mod, "_agent_thread_id", MagicMock(return_value=uuid.uuid4()))
        monkeypatch.setattr(agents_mod, "_collect_progress", fake_collect)
        monkeypatch.setattr(agents_mod.FrontierCognitive, "load_system_prompt", lambda *a, **kw: "You are a bot.")
        monkeypatch.setattr(agents_mod.FrontierCognitive, "extract_uni_messages", AsyncMock(return_value=[]))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "clean_staged_artifact_handoffs", lambda msg: msg)

        reporter = AsyncMock()

        cognitive = agents_mod.FrontierCognitive()
        result = await cognitive.chat_agent(
            messages=[{"role": "user", "content": "hi"}],
            user_id="123",
            user_name="tester",
            progress_reporter=reporter,
        )

        assert "response" in result
        assert len(collector_called) == 1, "_collect_progress should be called once"
        # 验证传入了 stream 和 reporter
        assert collector_called[0][0] is mock_stream
        assert collector_called[0][1] is reporter

    @pytest.mark.asyncio
    async def test_error_path_returns_fallback_and_cancels_progress(self, monkeypatch):
        """stream.output 抛出异常时，返回 fallback 响应并取消 progress_task。"""
        from unittest.mock import AsyncMock, MagicMock

        import utils.agents as agents_mod

        mock_stream = MagicMock()
        mock_stream.output = AsyncMock(side_effect=RuntimeError("agent failed"))

        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=mock_stream)

        monkeypatch.setattr(agents_mod, "create_deep_agent", MagicMock(return_value=mock_agent))
        monkeypatch.setattr(agents_mod, "_build_agent_backend", MagicMock())
        monkeypatch.setattr(agents_mod, "_agent_thread_id", MagicMock(return_value=uuid.uuid4()))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "load_system_prompt", lambda *a, **kw: "You are a bot.")

        reporter = AsyncMock()

        cognitive = agents_mod.FrontierCognitive()
        result = await cognitive.chat_agent(
            messages=[{"role": "user", "content": "hi"}],
            user_id="123",
            user_name="tester",
            progress_reporter=reporter,
        )

        # 错误路径应返回带有 error 键的 dict
        assert isinstance(result, dict)
        assert "response" in result
        assert "uni_messages" in result
        assert "error" in result
        assert "服务暂时不可用" in result["response"]["messages"][0].content
