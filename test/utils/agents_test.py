# ruff: noqa: S101

import builtins
import os
import types

import pytest

from utils import agents


@pytest.mark.asyncio
async def test_assistant_agent_model_selection(monkeypatch):
    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("system_prompt.md"):
            raise FileNotFoundError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

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


def test_frontier_load_system_prompt_missing(monkeypatch):
    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("system_prompt.md"):
            raise FileNotFoundError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
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

    assert [artifact.content for artifact in result] == [
        {"type": "image", "url": None, "path": None, "raw": b"img"}
    ]


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


def test_frontier_cognitive_uses_in_memory_checkpoint(monkeypatch):
    class DummyInMemorySaver:
        pass

    monkeypatch.setattr(agents, "InMemorySaver", DummyInMemorySaver)

    frontier = agents.FrontierCognitive()

    assert isinstance(frontier.checkpoint, DummyInMemorySaver)
    assert not hasattr(frontier, "_checkpoint_db_path")


@pytest.mark.asyncio
async def test_assistant_agent_uses_basic_model_config(monkeypatch):
    import builtins
    import types

    from utils import agents

    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("system_prompt.md"):
            raise FileNotFoundError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

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
    import builtins
    import types

    from utils import agents

    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("system_prompt.md"):
            raise FileNotFoundError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

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
            return {
                "messages": [
                    types.SimpleNamespace(type="ai", text='{"title": "日报", "count": 2}', content="")
                ]
            }

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
        async def ainvoke(self, payload, config=None):
            captured["payload"] = payload
            captured["config"] = config
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]}

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
    frontier.checkpoint = None
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
async def test_chat_agent_uses_thread_scoped_composite_backend(monkeypatch, tmp_path):
    import types

    from utils import agents

    captured = {}

    class DummyAgent:
        async def ainvoke(self, payload, config=None):
            captured["payload"] = payload
            captured["config"] = config
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr(agents, "create_llm", lambda **_kwargs: object())
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: True)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.checkpoint = None
    frontier.working_dir = str(tmp_path / "sandbox")

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
        group_id=123,
    )

    thread_id = agents._agent_thread_id("u1", 123)
    backend = captured["backend"]

    assert isinstance(backend, agents.CompositeBackend)
    assert backend.default.virtual_mode is True
    assert backend.default.root_dir == str(tmp_path / "sandbox" / "workspaces" / str(thread_id))
    assert set(backend.routes) == {"/skills/", "/memory/"}
    assert backend.routes["/skills/"].root_dir == str(tmp_path / "sandbox" / "skills")
    assert backend.routes["/memory/"].root_dir == str(tmp_path / "sandbox" / "memory")
    assert captured["skills"] == ["/skills"]
    assert captured["memory"] == ["/memory/AGENTS.md"]
    assert (tmp_path / "sandbox" / "workspaces" / str(thread_id)).is_dir()
    assert (tmp_path / "sandbox" / "skills").is_dir()
    assert (tmp_path / "sandbox" / "memory").is_dir()


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
        async def ainvoke(self, payload, config=None):
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]}

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
    frontier.checkpoint = None
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
        async def ainvoke(self, payload, config=None):
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]}

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
