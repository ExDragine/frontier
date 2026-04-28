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


@pytest.mark.asyncio
async def test_assistant_agent_uses_basic_model_config(monkeypatch):
    import builtins
    import types
    from utils import agents
    from utils.configs import EnvConfig

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
    from utils.configs import EnvConfig

    class DummyAgent:
        async def ainvoke(self, payload, config=None):
            captured["payload"] = payload
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
    )

    assert captured.get("use_responses_api") is False
    assert captured.get("provider") == "openai"
    assert captured.get("endpoint") == "openrouter"
    assert "reasoning_effort" not in captured
    assert "verbosity" not in captured
    assert captured["payload"]["messages"][0]["content"] == [
        {"type": "text", "text": "hi\n\n[图片已省略：当前模型不支持视觉输入]"}
    ]


@pytest.mark.asyncio
async def test_chat_agent_includes_reasoning_params_when_responses_api(monkeypatch):
    import types
    from utils import agents
    from utils.configs import EnvConfig

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
