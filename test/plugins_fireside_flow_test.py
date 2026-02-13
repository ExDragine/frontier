# ruff: noqa: S101

import types

import pytest

from plugins.fireside import store_memory_async
from utils.memory_types import MemoryAnalyzeResult


@pytest.mark.asyncio
async def test_store_memory_async_privacy_block(monkeypatch):
    class DummyMemory:
        def apply_privacy_filter(self, text):
            return False, "", "high_sensitive"

    monkeypatch.setattr("plugins.fireside.memory", DummyMemory())
    await store_memory_async("sk-123", "u", None, None)


@pytest.mark.asyncio
async def test_store_memory_async_success(monkeypatch):
    class DummyMemory:
        def apply_privacy_filter(self, text):
            return True, text, "ok"

        async def persist_from_analysis(self, **_kwargs):
            return ["id"]

    monkeypatch.setattr("plugins.fireside.memory", DummyMemory())

    async def fake_assistant_agent(*_args, **_kwargs):
        return MemoryAnalyzeResult(should_memory=True, memory_content="ok")

    monkeypatch.setattr("plugins.fireside.assistant_agent", fake_assistant_agent)

    class DummyFile:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return "prompt"

    import builtins

    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("memory_analyze_v2.txt"):
            return DummyFile()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    await store_memory_async("hello", "u", None, None)
