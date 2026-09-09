# ruff: noqa: S101

from types import SimpleNamespace

import pytest
from pydantic import BaseModel, Field

from utils import llm_factory, signal_llm


class Gateway(BaseModel):
    is_safe: bool = Field(default=False)


@pytest.mark.asyncio
async def test_signal_structured_uses_function_calling_for_deepseek(monkeypatch):
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

    response = await signal_llm.signal_structured(
        system_prompt="Classify the gateway.",
        user_prompt="Is this gateway safe?",
        schema=Gateway,
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )

    assert response.is_safe is True
    assert captured["schema"] is Gateway
    assert captured["method"] == "function_calling"
    assert captured["llm_kwargs"] == {
        "model": "deepseek-v4-flash",
        "streaming": False,
        "max_retries": 2,
        "timeout": 30,
        "provider": "deepseek",
        "temperature": 0,
        "extra_body": {"thinking": {"type": "disabled"}},
        "tags": ["frontier:signal"],
    }
    assert captured["messages"][0][0] == "system"
    assert "Classify the gateway." in captured["messages"][0][1]
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

    llm = signal_llm.SignalLLM(model="custom-route", provider="deepseek")
    response = await llm.structured("", "使用json格式回答: Is this gateway safe?", Gateway, method="json_mode")

    assert response.is_safe is False
    assert captured["llm_kwargs"]["model"] == "custom-route"
    assert captured["llm_kwargs"]["provider"] == "deepseek"
    assert captured["method"] == "json_mode"
    assert captured["messages"][0][0] == "system"
    assert "Return ONLY valid JSON" in captured["messages"][0][1]
    assert '"is_safe"' in captured["messages"][0][1]


@pytest.mark.parametrize("profile,capabilities,expected", [
    ({"type": "openai", "api_mode": "responses"}, {"structured_output": True}, {"method": "json_schema", "strict": True}),
    ({"type": "openai", "api_mode": "chat_completions", "base_url": "https://proxy.example/v1"},
     {"structured_output": True, "tool_calling": True}, {"method": "function_calling"}),
    ({"type": "openai", "api_mode": "chat_completions", "base_url": "https://proxy.example/v1"},
     {}, {"method": "json_mode"}),
    ({"type": "google", "api_mode": "generate_content"}, {}, {"method": "json_schema"}),
    ({"type": "anthropic", "api_mode": "messages"}, {"structured_output": True}, {"method": "json_schema"}),
    ({"type": "anthropic", "api_mode": "messages"}, {}, {"method": "function_calling"}),
    ({"type": "deepseek", "api_mode": "chat_completions"}, {"structured_output": True}, {"method": "function_calling"}),
    ({"type": "openai", "api_mode": "responses", "structured_output_method": "json_mode"},
     {"structured_output": True}, {"method": "json_mode"}),
])
def test_structured_strategy_respects_adapter_and_endpoint(monkeypatch, profile, capabilities, expected):
    monkeypatch.setattr(llm_factory.EnvConfig, "LLM_PROVIDERS", {"configured": profile})
    options = llm_factory.structured_output_options("model", "configured", SimpleNamespace(profile=capabilities))
    assert options == expected


@pytest.mark.asyncio
async def test_json_schema_uses_strict_and_validates_result_without_second_request(monkeypatch):
    calls = []

    class Decision(BaseModel):
        answer: bool

    class DummyModel:
        profile = {"structured_output": True}

        def with_structured_output(self, schema, **options):
            assert options == {"method": "json_schema", "strict": True}
            assert schema is Decision
            return self

        async def ainvoke(self, messages):
            calls.append(messages)
            return {"unexpected": "invalid output"}

    monkeypatch.setattr(signal_llm, "create_llm", lambda **kwargs: DummyModel())
    monkeypatch.setattr(llm_factory.EnvConfig, "LLM_PROVIDERS", {
        "official": {"type": "openai", "api_mode": "responses"},
    })
    with pytest.raises(ValueError):
        await signal_llm.SignalLLM(model="model", provider="official").structured("判断", "你好", Decision)
    assert len(calls) == 1
