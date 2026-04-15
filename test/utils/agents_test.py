import builtins
import types

import pytest

from utils import agents
from utils.memory_types import MemoryCategory, MemoryScope


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
async def test_inject_memory_context(monkeypatch):
    class DummyFrontier:
        def __init__(self):
            self.memory = None

        async def inject_memory_context(self, messages, query_text: str, user_id: str, group_id):
            if not query_text.strip():
                return messages
            memory_items = await self.memory.retrieve_for_injection(
                query=query_text,
                user_id=user_id,
                group_id=group_id,
                max_items=1,
            )
            if not memory_items:
                return messages
            memory_context = self.memory.format_for_injection(memory_items)
            prepared_messages = list(messages)
            insert_at = len(prepared_messages)
            if prepared_messages and prepared_messages[-1].get("role") == "user":
                insert_at = max(0, len(prepared_messages) - 1)
            prepared_messages.insert(insert_at, {"role": "system", "content": memory_context})
            return prepared_messages

    fc = DummyFrontier()

    class DummyMemory:
        async def retrieve_for_injection(self, **_kwargs):
            return [
                types.SimpleNamespace(
                    scope=MemoryScope.USER,
                    category=MemoryCategory.OTHER,
                    slot_key="slot",
                    memory_id="m1",
                    content="content",
                )
            ]

        def format_for_injection(self, items):
            return "Memory Context"

    fc.memory = DummyMemory()

    messages = [{"role": "user", "content": "hi"}]
    result = await fc.inject_memory_context(messages, "hi", "u1", None)
    assert any(msg["role"] == "system" for msg in result)


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

    class DummyAgent:
        async def ainvoke(self, payload):
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok")]}

    def fake_create_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_agent", fake_create_agent)

    captured = {}

    def capturing_create_llm(model, **kwargs):
        captured.update(kwargs)
        captured["model"] = model

        class DummyModel:
            pass

        return DummyModel()

    monkeypatch.setattr(agents, "create_llm", capturing_create_llm)

    # Monkeypatch the EnvConfig in the agents module
    monkeypatch.setattr(agents.EnvConfig, "BASIC_MODEL_USE_RESPONSES_API", False)

    await agents.assistant_agent(user_prompt="hello")

    assert captured.get("use_responses_api") is False


@pytest.mark.asyncio
async def test_chat_agent_drops_reasoning_params_when_chat_completions(monkeypatch):
    import types
    from utils import agents
    from utils.configs import EnvConfig

    class DummyAgent:
        async def ainvoke(self, payload, config=None):
            return {
                "messages": [
                    types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)
                ]
            }

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

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.subagents = []
    frontier.checkpoint = None
    frontier.backend = None
    frontier.memory = None

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
    )

    assert captured.get("use_responses_api") is False
    assert "reasoning_effort" not in captured
    assert "verbosity" not in captured


@pytest.mark.asyncio
async def test_chat_agent_includes_reasoning_params_when_responses_api(monkeypatch):
    import types
    from utils import agents
    from utils.configs import EnvConfig

    class DummyAgent:
        async def ainvoke(self, payload, config=None):
            return {
                "messages": [
                    types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)
                ]
            }

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
    frontier.memory = None

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
        capability="medium",
    )

    assert captured.get("use_responses_api") is True
    assert captured.get("reasoning_effort") == "medium"
    assert captured.get("verbosity") == "low"
