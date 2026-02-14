# ruff: noqa: S101

from dataclasses import dataclass
import sys
import types

import pytest


@dataclass
class DummyItem:
    scope: object
    content: str


@pytest.mark.asyncio
async def test_get_memory_disabled(load_tool_module, monkeypatch):
    fake_utils_memory = types.ModuleType("utils.memory")
    fake_utils_memory.get_memory_service = lambda: types.SimpleNamespace(retrieve_for_injection=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "utils.memory", fake_utils_memory)
    mod = load_tool_module("memory")
    monkeypatch.setattr(mod.EnvConfig, "MEMORY_ENABLED", False)
    result = await mod.get_memory("你好", user_id="u1", group_id=1)
    assert result == "记忆系统未启用。"


@pytest.mark.asyncio
async def test_get_memory_no_results(load_tool_module, monkeypatch):
    fake_utils_memory = types.ModuleType("utils.memory")
    fake_utils_memory.get_memory_service = lambda: types.SimpleNamespace(retrieve_for_injection=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "utils.memory", fake_utils_memory)
    mod = load_tool_module("memory")
    monkeypatch.setattr(mod.EnvConfig, "MEMORY_ENABLED", True)

    class DummyMemory:
        async def retrieve_for_injection(self, **_kwargs):
            return []

    monkeypatch.setattr(mod, "memory", DummyMemory())
    result = await mod.get_memory("天气", user_id="u1", group_id=1)
    assert result == "未找到相关记忆。"


@pytest.mark.asyncio
async def test_get_memory_formats_user_and_group(load_tool_module, monkeypatch):
    fake_utils_memory = types.ModuleType("utils.memory")
    fake_utils_memory.get_memory_service = lambda: types.SimpleNamespace(retrieve_for_injection=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "utils.memory", fake_utils_memory)
    mod = load_tool_module("memory")
    monkeypatch.setattr(mod.EnvConfig, "MEMORY_ENABLED", True)
    monkeypatch.setattr(mod.EnvConfig, "MEMORY_MAX_INJECTED_MEMORIES", 4)

    class DummyMemory:
        async def retrieve_for_injection(self, **_kwargs):
            return [
                DummyItem(scope=mod.MemoryScope.USER, content="用户偏好A"),
                DummyItem(scope=mod.MemoryScope.GROUP, content="群规则B"),
            ]

    monkeypatch.setattr(mod, "memory", DummyMemory())
    result = await mod.get_memory("规则", user_id="u1", group_id=1)
    assert "用户记忆:" in result
    assert "* 用户偏好A" in result
    assert "群记忆:" in result
    assert "* 群规则B" in result
