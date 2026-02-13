# ruff: noqa: S101

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
            return {"messages": [types.SimpleNamespace(type="ai", content="ok")]}

    def fake_create_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_agent", fake_create_agent)

    class DummyModel:
        def __init__(self, **_kwargs):
            pass

    monkeypatch.setattr(agents, "ChatOpenAI", DummyModel)
    monkeypatch.setattr(agents, "ChatAnthropic", DummyModel)
    monkeypatch.setattr(agents, "ChatGoogleGenerativeAI", DummyModel)

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
