# ruff: noqa: S101

import builtins
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


def test_subagents_model_respects_config(monkeypatch):
    import sys

    import utils.llm_factory as factory
    import utils.subagents as subagents_module
    from utils.configs import EnvConfig

    created_kwargs = {}

    class CapturingModel:
        def __init__(self, **kwargs):
            created_kwargs.update(kwargs)

    # Register original module with monkeypatch so it's restored on teardown
    monkeypatch.setitem(sys.modules, "utils.subagents", subagents_module)

    monkeypatch.setattr(factory, "ChatOpenAI", CapturingModel)
    monkeypatch.setattr(EnvConfig, "BASIC_MODEL_USE_RESPONSES_API", False)

    del sys.modules["utils.subagents"]
    import utils.subagents  # noqa: F401

    assert created_kwargs.get("use_responses_api") is False


def test_subagents_model_uses_basic_provider_endpoint(monkeypatch):
    import sys

    import utils.llm_factory as factory
    import utils.subagents as subagents_module
    from utils.configs import EnvConfig

    created_kwargs = {}

    def fake_create_llm(**kwargs):
        created_kwargs.update(kwargs)
        return object()

    monkeypatch.setitem(sys.modules, "utils.subagents", subagents_module)
    monkeypatch.setattr(factory, "create_llm", fake_create_llm)
    monkeypatch.setattr(EnvConfig, "BASIC_MODEL_PROVIDER", "anthropic")
    monkeypatch.setattr(EnvConfig, "BASIC_MODEL_ENDPOINT", "anthropic_proxy")

    del sys.modules["utils.subagents"]
    import utils.subagents  # noqa: F401

    assert created_kwargs.get("provider") == "anthropic"
    assert created_kwargs.get("endpoint") == "anthropic_proxy"


def test_domain_subagents_use_grouped_tools(monkeypatch):
    import utils.subagents as subagents_module

    grouped_tools = {
        "research": ["research-tool"],
        "astro": ["astro-tool"],
        "earth": ["earth-tool"],
        "media": ["media-tool"],
        "memory": ["memory-tool"],
        "divination": ["divination-tool"],
        "external": ["external-tool"],
    }
    monkeypatch.setattr(subagents_module.agent_tools, "subagent_tools", grouped_tools, raising=False)
    monkeypatch.setattr(subagents_module.agent_tools, "web_tools", ["web-tool"], raising=False)

    subagents = subagents_module.get_domain_subagents()
    by_name = {item["name"]: item for item in subagents}

    assert by_name["general-purpose"]["tools"] == []
    assert by_name["fact_check_agent"]["tools"] == ["web-tool"]
    assert by_name["research_agent"]["tools"] == ["research-tool"]
    assert by_name["astro_agent"]["tools"] == ["astro-tool"]
    assert by_name["earth_agent"]["tools"] == ["earth-tool"]
    assert by_name["media_agent"]["tools"] == ["media-tool"]
    assert by_name["memory_agent"]["tools"] == ["memory-tool"]
    assert by_name["divination_agent"]["tools"] == ["divination-tool"]
    assert by_name["external_agent"]["tools"] == ["external-tool"]


def test_frontier_cognitive_uses_main_tools_and_domain_subagents(monkeypatch):
    domain_subagents = [{"name": "research_agent", "tools": ["research-tool"]}]
    monkeypatch.setattr(agents.agent_tools, "all_tools", ["all-tool"], raising=False)
    monkeypatch.setattr(agents.agent_tools, "main_tools", ["main-tool"], raising=False)
    monkeypatch.setattr(agents, "get_domain_subagents", lambda: domain_subagents, raising=False)

    frontier = agents.FrontierCognitive()

    assert frontier.tools == ["main-tool"]
    assert frontier.subagents == domain_subagents


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
    frontier.subagents = []
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
    frontier.subagents = []
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
