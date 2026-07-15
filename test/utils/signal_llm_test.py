# ruff: noqa: S101

import pytest
from pydantic import BaseModel, Field

from utils import signal_llm


class Gateway(BaseModel):
    is_safe: bool = Field(default=False)


@pytest.mark.asyncio
async def test_signal_structured_uses_json_mode_and_signal_model_config(monkeypatch):
    captured = {}

    class DummyRunnable:
        async def ainvoke(self, messages):
            captured["messages"] = messages
            return Gateway(is_safe=True)

    class DummyModel:
        def with_structured_output(self, schema, *, method):
            captured["schema"] = schema
            captured["method"] = method
            return DummyRunnable()

    def fake_create_llm(**kwargs):
        captured["llm_kwargs"] = kwargs
        return DummyModel()

    monkeypatch.setattr(signal_llm, "create_llm", fake_create_llm)
    monkeypatch.setattr(signal_llm.EnvConfig, "SIGNAL_MODEL", "deepseek-v4-flash")
    monkeypatch.setattr(signal_llm.EnvConfig, "SIGNAL_MODEL_PROVIDER", "deepseek")
    monkeypatch.setattr(signal_llm.EnvConfig, "SIGNAL_MODEL_ENDPOINT", "deepseek_signal")
    monkeypatch.setattr(signal_llm.EnvConfig, "SIGNAL_MODEL_USE_RESPONSES_API", True)

    response = await signal_llm.signal_structured(
        system_prompt="Classify the gateway.",
        user_prompt="Is this gateway safe?",
        schema=Gateway,
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )

    assert response.is_safe is True
    assert captured["schema"] is Gateway
    assert captured["method"] == "json_mode"
    assert captured["llm_kwargs"] == {
        "model": "deepseek-v4-flash",
        "streaming": False,
        "max_retries": 2,
        "timeout": 30,
        "provider": "deepseek",
        "endpoint": "deepseek_signal",
        "use_responses_api": True,
        "temperature": 0,
        "extra_body": {"thinking": {"type": "disabled"}},
    }
    assert captured["messages"][0][0] == "system"
    assert "Classify the gateway." in captured["messages"][0][1]
    assert "Return ONLY valid JSON" in captured["messages"][0][1]
    assert captured["messages"][1] == ("human", "Is this gateway safe?")


@pytest.mark.asyncio
async def test_signal_llm_class_allows_explicit_model_override(monkeypatch):
    captured = {}

    class DummyRunnable:
        async def ainvoke(self, messages):
            captured["messages"] = messages
            return Gateway(is_safe=False)

    class DummyModel:
        def with_structured_output(self, schema, *, method):
            captured["schema"] = schema
            captured["method"] = method
            return DummyRunnable()

    def fake_create_llm(**kwargs):
        captured["llm_kwargs"] = kwargs
        return DummyModel()

    monkeypatch.setattr(signal_llm, "create_llm", fake_create_llm)

    llm = signal_llm.SignalLLM(model="custom-route", provider="deepseek", endpoint="")
    response = await llm.structured("", "使用json格式回答: Is this gateway safe?", Gateway)

    assert response.is_safe is False
    assert captured["llm_kwargs"]["model"] == "custom-route"
    assert captured["llm_kwargs"]["provider"] == "deepseek"
    assert captured["method"] == "json_mode"
    assert captured["messages"][0][0] == "system"
    assert "Return ONLY valid JSON" in captured["messages"][0][1]
