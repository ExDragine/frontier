# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
async def test_send_staged_artifact_returns_loaded_artifact(load_tool_module, monkeypatch):
    mod = load_tool_module("artifact_bridge")
    loaded = mod.UniMessage.image(url="https://example.com/a.png")

    monkeypatch.setattr(mod, "load_staged_artifact", lambda artifact_id, **_kwargs: loaded)

    text, artifact = await mod.send_staged_artifact("00000000-0000-4000-8000-000000000000")

    assert "已读取暂存内容" in text
    assert artifact is loaded


@pytest.mark.asyncio
async def test_send_staged_artifact_reports_missing_artifact(load_tool_module, monkeypatch):
    mod = load_tool_module("artifact_bridge")

    def missing(_artifact_id, **_kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(mod, "load_staged_artifact", missing)

    text, artifact = await mod.send_staged_artifact("00000000-0000-4000-8000-000000000000")

    assert "暂存内容不存在" in text
    assert artifact is None
