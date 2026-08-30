# ruff: noqa: S101

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import utils.llm_factory as factory


def test_gemini_routes_to_google(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(model="gemini-2.5-flash", max_retries=2, streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "gemini-2.5-flash"
    assert "google_api_key" in kw
    assert kw.get("max_retries") == 2
    assert kw.get("streaming") is False
    assert kw["profile"]["max_input_tokens"] == 1_048_576
    assert kw["profile"]["image_inputs"] is True
    assert kw["profile"]["tool_calling"] is True


def test_unknown_model_does_not_receive_catalog_profile(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="vendor-private-model")

    assert "profile" not in mock_cls.call_args.kwargs


def test_explicit_model_profile_overrides_catalog(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)
    custom_profile = {"max_input_tokens": 1234, "text_inputs": True}

    factory.create_llm(model="gemini-2.5-flash", profile=custom_profile)

    assert mock_cls.call_args.kwargs["profile"] is custom_profile


def test_catalog_profile_accepts_proxy_prefixed_model_id(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="openrouter/google/gemini-2.5-flash", provider="openai")

    assert mock_cls.call_args.kwargs["profile"]["max_input_tokens"] == 1_048_576


def test_gpt_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "openai": {
                "type": "openai",
                "api_mode": "responses",
                "base_url": "https://example.com",
                "api_key": "sk-test",
            }
        },
    )

    factory.create_llm(model="gpt-4o", timeout=300, streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "gpt-4o"
    assert "openai_api_key" in kw
    assert "openai_api_base" in kw
    assert kw["use_responses_api"] is True
    assert kw.get("request_timeout") == 300  # timeout → request_timeout
    assert "timeout" not in kw  # raw "timeout" filtered out


def test_o3_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="o3", streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "o3"
    assert "openai_api_key" in kw


def test_o1_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="o1-mini")

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "o1-mini"
    assert "openai_api_key" in kw


def test_o4_mini_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="o4-mini")

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "o4-mini"
    assert "openai_api_key" in kw


def test_claude_routes_to_anthropic(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "anthropic": {
                "type": "anthropic",
                "api_mode": "messages",
                "base_url": "https://anthropic.example.com",
            }
        },
    )

    factory.create_llm(model="claude-3-5-sonnet-20241022", timeout=60)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "claude-3-5-sonnet-20241022"
    assert "anthropic_api_key" in kw
    assert kw["anthropic_api_url"] == "https://anthropic.example.com"
    assert kw.get("default_request_timeout") == 60  # timeout → default_request_timeout
    assert "timeout" not in kw


def test_deepseek_routes_to_deepseek(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatDeepSeek", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {"deepseek": {"type": "deepseek", "api_mode": "chat_completions", "base_url": ""}},
    )

    factory.create_llm(model="deepseek-v4-flash", timeout=30, max_retries=2)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "deepseek-v4-flash"
    assert "api_key" in kw
    assert "api_base" not in kw
    assert "use_responses_api" not in kw
    assert kw["timeout"] == 30
    assert kw["max_retries"] == 2
    assert (
        factory.provider_official_deepseek_api_mode("deepseek-v4-flash", "deepseek")
        == "chat_completions"
    )


def test_deepseek_responses_routes_through_chat_openai(monkeypatch):
    openai_cls = MagicMock()
    deepseek_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", openai_cls)
    monkeypatch.setattr(factory, "ChatDeepSeek", deepseek_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "deepseek_responses": {
                "type": "openai",
                "api_mode": "responses",
                "base_url": "https://api.deepseek.com",
                "api_key": "sk-deepseek-responses",
            }
        },
    )

    factory.create_llm(
        model="deepseek-v4-pro",
        provider="deepseek_responses",
        timeout=30,
        reasoning_effort="medium",
        verbosity="low",
    )

    openai_cls.assert_called_once()
    deepseek_cls.assert_not_called()
    kw = openai_cls.call_args.kwargs
    assert kw["model"] == "deepseek-v4-pro"
    assert kw["openai_api_key"].get_secret_value() == "sk-deepseek-responses"
    assert kw["openai_api_base"] == "https://api.deepseek.com"
    assert kw["use_responses_api"] is True
    assert kw["request_timeout"] == 30
    assert kw["reasoning_effort"] == "medium"
    assert kw["verbosity"] == "low"
    assert kw["profile"]["max_input_tokens"] == 1_000_000
    assert factory.provider_uses_responses_api("deepseek-v4-pro", "deepseek_responses") is True
    assert factory.model_supports_native_web_search("deepseek-v4-pro", "deepseek_responses") is True
    assert factory.provider_is_official_openai("deepseek-v4-pro", "deepseek_responses") is False
    assert (
        factory.provider_official_deepseek_api_mode("deepseek-v4-pro", "deepseek_responses")
        == "responses"
    )


@pytest.mark.parametrize(
    "base_url",
    ["", "https://api.openai.com", "https://api.openai.com/v1/", "https://API.OPENAI.COM:443/v1"],
)
def test_official_openai_route_detection_accepts_only_first_party_endpoints(monkeypatch, base_url):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "first_party": {
                "type": "openai",
                "api_mode": "responses",
                "base_url": base_url,
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_is_official_openai("gpt-5.4", "first_party") is True
    assert factory.model_supports_native_web_search("gpt-5.4", "first_party") is True


def test_openai_native_web_search_requires_responses_api(monkeypatch):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "openai_chat_completions": {
                "type": "openai",
                "api_mode": "chat_completions",
                "native_web_search": True,
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_is_official_openai("gpt-5.4", "openai_chat_completions") is True
    assert factory.model_supports_native_web_search("gpt-5.4", "openai_chat_completions") is False


def test_responses_proxy_can_explicitly_enable_native_web_search(monkeypatch):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "responses_proxy": {
                "type": "openai",
                "api_mode": "responses",
                "native_web_search": True,
                "base_url": "https://gateway.example.com/v1",
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_is_official_openai("gpt-5.4", "responses_proxy") is False
    assert factory.model_supports_native_web_search("gpt-5.4", "responses_proxy") is True


@pytest.mark.parametrize(
    ("provider_type", "api_mode", "base_url"),
    [
        ("openai", "responses", "https://api.deepseek.com"),
        ("openai", "responses", "https://openrouter.ai/api/v1"),
        ("openai", "responses", "https://api.openai.com.example.com/v1"),
        ("openai", "responses", "http://api.openai.com/v1"),
        ("openai", "responses", "https://api.openai.com/v2"),
        ("openai", "responses", "https://api.openai.com/v1?proxy=1"),
        ("deepseek", "chat_completions", ""),
        ("anthropic", "messages", "https://api.deepseek.com/anthropic"),
    ],
)
def test_official_openai_route_detection_rejects_compatible_and_non_openai_routes(
    monkeypatch,
    provider_type,
    api_mode,
    base_url,
):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "candidate": {
                "type": provider_type,
                "api_mode": api_mode,
                "base_url": base_url,
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_is_official_openai("model", "candidate") is False


@pytest.mark.parametrize(
    ("provider_type", "api_mode", "base_url", "model"),
    [
        ("deepseek", "chat_completions", "https://deepseek.example.com/v1", "deepseek-chat"),
        ("openai", "responses", "https://openrouter.ai/api/v1", "deepseek-v4-pro"),
        ("openai", "responses", "", "deepseek-v4-pro"),
        ("anthropic", "messages", "https://anthropic.example.com", "deepseek-v4-pro"),
        ("anthropic", "messages", "", "deepseek-v4-pro"),
        ("anthropic", "messages", "https://api.deepseek.com/anthropic", "claude-sonnet-4"),
        ("openai", "responses", "https://user@api.deepseek.com/v1", "deepseek-v4-pro"),
    ],
)
def test_official_deepseek_route_detection_rejects_proxies_and_wrong_models(
    monkeypatch,
    provider_type,
    api_mode,
    base_url,
    model,
):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "candidate": {
                "type": provider_type,
                "api_mode": api_mode,
                "base_url": base_url,
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_official_deepseek_api_mode(model, "candidate") is None


def test_deepseek_native_web_search_accepts_official_v1_base_url(monkeypatch):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "official_deepseek": {
                "type": "openai",
                "api_mode": "responses",
                "base_url": "https://api.deepseek.com/v1/",
                "api_key": "sk-deepseek-responses",
            }
        },
    )

    assert factory.model_supports_native_web_search("deepseek-future-model", "official_deepseek") is True


@pytest.mark.parametrize(
    ("model", "base_url"),
    [
        ("deepseek-v4-pro", "https://openrouter.ai/api/v1"),
        ("gpt-5.4", "https://openrouter.ai/api/v1"),
        ("deepseek-v4-pro", "https://api.deepseek.com.example.com"),
        ("deepseek-v4-pro", "https://api.deepseek.com/anthropic"),
        ("gpt-5.4", "https://api.deepseek.com"),
    ],
)
def test_native_web_search_rejects_non_official_deepseek_routes(monkeypatch, model, base_url):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "responses_proxy": {
                "type": "openai",
                "api_mode": "responses",
                "base_url": base_url,
                "api_key": "sk-test",
            }
        },
    )

    assert factory.model_supports_native_web_search(model, "responses_proxy") is False


def test_deepseek_anthropic_routes_through_chat_anthropic(monkeypatch):
    anthropic_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", anthropic_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "deepseek_anthropic": {
                "type": "anthropic",
                "api_mode": "messages",
                "base_url": "https://api.deepseek.com/anthropic",
                "api_key": "sk-deepseek-anthropic",
            }
        },
    )

    factory.create_llm(model="deepseek-v4-pro", provider="deepseek_anthropic", timeout=30)

    kw = anthropic_cls.call_args.kwargs
    assert kw["model"] == "deepseek-v4-pro"
    assert kw["anthropic_api_key"].get_secret_value() == "sk-deepseek-anthropic"
    assert kw["anthropic_api_url"] == "https://api.deepseek.com/anthropic"
    assert kw["default_request_timeout"] == 30
    assert "use_responses_api" not in kw
    assert factory.provider_uses_responses_api("deepseek-v4-pro", "deepseek_anthropic") is False
    assert factory.model_supports_native_web_search("deepseek-v4-pro", "deepseek_anthropic") is False
    assert factory.provider_is_official_openai("deepseek-v4-pro", "deepseek_anthropic") is False
    assert (
        factory.provider_official_deepseek_api_mode("deepseek-v4-pro", "deepseek_anthropic")
        == "messages"
    )


@pytest.mark.parametrize(
    "base_url",
    ["", "https://api.anthropic.com", "https://api.anthropic.com/v1/"],
)
def test_official_anthropic_route_detection_accepts_first_party_endpoints(monkeypatch, base_url):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "first_party": {
                "type": "anthropic",
                "api_mode": "messages",
                "base_url": base_url,
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_is_official_anthropic("claude-sonnet-4", "first_party") is True


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.deepseek.com/anthropic",
        "https://anthropic.example.com",
        "http://api.anthropic.com/v1",
        "https://api.anthropic.com.example.com/v1",
    ],
)
def test_official_anthropic_route_detection_rejects_other_endpoints(monkeypatch, base_url):
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "candidate": {
                "type": "anthropic",
                "api_mode": "messages",
                "base_url": base_url,
                "api_key": "sk-test",
            }
        },
    )

    assert factory.provider_is_official_anthropic("claude-sonnet-4", "candidate") is False


def test_deepseek_provider_profile_overrides_api_key_and_base_url(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatDeepSeek", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "deepseek_signal": {
                "type": "deepseek",
                "api_mode": "chat_completions",
                "base_url": "https://deepseek.example.com/v1",
                "api_key": "sk-deepseek-profile",
            }
        },
    )

    factory.create_llm(model="custom-signal", provider="deepseek_signal")

    kw = mock_cls.call_args.kwargs
    assert kw["api_key"].get_secret_value() == "sk-deepseek-profile"
    assert kw["api_base"] == "https://deepseek.example.com/v1"


def test_openai_kwargs_filtered_for_google(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(
        model="gemini-2.5-flash",
        reasoning_effort="high",
        verbosity="low",
        max_retries=2,
    )

    kw = mock_cls.call_args.kwargs
    assert "use_responses_api" not in kw
    assert "reasoning_effort" not in kw
    assert "verbosity" not in kw
    assert kw.get("max_retries") == 2  # 通用参数正常传入


def test_openai_kwargs_filtered_for_anthropic(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)

    factory.create_llm(
        model="claude-3-5-haiku-20241022",
        reasoning_effort="medium",
        max_retries=2,
        model_kwargs={"cache_control": {"type": "ephemeral"}},
    )

    kw = mock_cls.call_args.kwargs
    assert "use_responses_api" not in kw
    assert "reasoning_effort" not in kw
    assert kw.get("max_retries") == 2
    assert kw["model_kwargs"] == {"cache_control": {"type": "ephemeral"}}


def test_anthropic_provider_metadata_reaches_payload_without_tracing_collision():
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.update(
        {
            "FRONTIER_CONFIG": str(project_root / "env.toml.example"),
            "NICKNAME": '["Frontier"]',
        }
    )
    script = """
from langchain_core.messages import HumanMessage
from utils.configs import EnvConfig
from utils.llm_factory import create_llm

pseudonym = "frontier-agent-v1_user_0123456789abcdef0123456789abcdef01234567"
EnvConfig.LLM_PROVIDERS = {
    "deepseek_anthropic": {
        "type": "anthropic",
        "api_mode": "messages",
        "base_url": "https://api.deepseek.com/anthropic",
        "api_key": "sk-test",
    }
}
model = create_llm(
    model="deepseek-v4-pro",
    provider="deepseek_anthropic",
    model_kwargs={"metadata": {"user_id": pseudonym}},
)
payload = model._get_request_payload([HumanMessage(content="hi")])
assert payload["metadata"] == {"user_id": pseudonym}
assert "user_id" not in (model.metadata or {})
"""

    subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        cwd=project_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_openai_extra_body_forwarded_as_explicit_kwarg(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="gpt-4o", extra_body={"thinking": {"type": "disabled"}})

    kw = mock_cls.call_args.kwargs
    assert kw["extra_body"] == {"thinking": {"type": "disabled"}}
    assert "model_kwargs" not in kw


def test_deepseek_extra_body_forwarded_as_explicit_kwarg(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatDeepSeek", mock_cls)

    factory.create_llm(model="deepseek-v4-flash", extra_body={"thinking": {"type": "disabled"}})

    kw = mock_cls.call_args.kwargs
    assert kw["extra_body"] == {"thinking": {"type": "disabled"}}
    assert "model_kwargs" not in kw


def test_unknown_prefix_routes_to_openai_compatible(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="mistral-7b-instruct")

    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "mistral-7b-instruct"
    assert "openai_api_key" in kw


def test_explicit_provider_routes_without_model_prefix(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)

    factory.create_llm(model="custom-sonnet", provider="anthropic")

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "custom-sonnet"
    assert "anthropic_api_key" in kw


def test_provider_profile_can_set_type_base_url_and_api_key(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "anthropic_proxy": {
                "type": "anthropic",
                "api_mode": "messages",
                "base_url": "https://anthropic-proxy.example.com",
                "api_key": "ant-profile",
            }
        },
    )

    factory.create_llm(model="custom-sonnet", provider="anthropic_proxy")

    kw = mock_cls.call_args.kwargs
    assert kw["anthropic_api_key"].get_secret_value() == "ant-profile"
    assert kw["anthropic_api_url"] == "https://anthropic-proxy.example.com"


def test_provider_profile_controls_openai_base_url_and_responses_api(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "openrouter": {
                "type": "openai",
                "api_mode": "chat_completions",
                "base_url": "https://openrouter.example.com/api/v1",
                "api_key": "sk-openrouter",
            }
        },
    )

    factory.create_llm(model="any-model", provider="openrouter")

    kw = mock_cls.call_args.kwargs
    assert kw["openai_api_key"].get_secret_value() == "sk-openrouter"
    assert kw["openai_api_base"] == "https://openrouter.example.com/api/v1"
    assert kw["use_responses_api"] is False
    assert factory.provider_uses_responses_api("any-model", "openrouter") is False


def test_unknown_provider_profile_raises():
    with pytest.raises(ValueError, match="未知 LLM provider profile"):
        factory.create_llm(model="gpt-4o", provider="missing")


@pytest.mark.parametrize("removed_kwarg", ["endpoint", "use_responses_api"])
def test_removed_model_routing_kwargs_raise(removed_kwarg):
    with pytest.raises(TypeError, match=removed_kwarg):
        factory.create_llm(model="gpt-4o", **{removed_kwarg: "value"})


def test_model_capabilities_default_to_text(monkeypatch):
    assert factory.get_model_capabilities("unknown-model") == {"text"}
    assert factory.model_supports("unknown-model", "text") is True
    assert factory.model_supports("unknown-model", "vision") is False


def test_model_capabilities_use_model_specific_config(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL_CAPABILITIES", ["text", "vision"])

    assert factory.get_model_capabilities("basic-model") == {"text", "vision"}
    assert factory.model_supports("basic-model", "vision") is True


def test_model_capabilities_treat_image_as_vision(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL_CAPABILITIES", ["text", "image"])

    assert factory.get_model_capabilities("basic-model", role="basic") == {"text", "vision"}
    assert factory.model_supports("basic-model", "vision", role="basic") is True
    assert factory.model_supports("basic-model", "image", role="basic") is True


def test_model_capabilities_fall_back_to_catalog_for_unconfigured_role(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "ADVAN_MODEL", "catalog-model")
    monkeypatch.setattr(factory.EnvConfig, "ADVAN_MODEL_CAPABILITIES", [])
    monkeypatch.setattr(
        factory,
        "get_langchain_model_profile",
        lambda *_args: {
            "text_inputs": True,
            "image_inputs": True,
            "audio_inputs": True,
            "video_inputs": True,
            "pdf_inputs": True,
        },
    )

    assert factory.get_model_capabilities("catalog-model", role="advanced") == {
        "text",
        "vision",
        "audio",
        "video",
        "file",
    }


def test_model_capabilities_are_resolved_by_role_for_shared_model(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL", "shared-model")
    monkeypatch.setattr(factory.EnvConfig, "ADVAN_MODEL", "shared-model")
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL_CAPABILITIES", ["text"])
    monkeypatch.setattr(factory.EnvConfig, "ADVAN_MODEL_CAPABILITIES", ["text", "vision"])

    assert factory.model_supports("shared-model", "vision", role="basic") is False
    assert factory.model_supports("shared-model", "vision", role="advanced") is True
    assert factory.model_supports("shared-model", "vision") is True


def test_model_capabilities_use_signal_model_config(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "SIGNAL_MODEL", "signal-model")
    monkeypatch.setattr(factory.EnvConfig, "SIGNAL_MODEL_CAPABILITIES", ["text"])

    assert factory.get_model_capabilities("signal-model") == {"text"}
    assert factory.model_supports("signal-model", "text") is True
    assert factory.model_supports("signal-model", "vision") is False


def test_provider_capabilities_do_not_override_model_capabilities(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL_CAPABILITIES", [])
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "text_gateway": {
                "type": "openai",
                "api_mode": "responses",
                "capabilities": ["text", "vision"],
            }
        },
    )

    assert factory.get_model_capabilities("basic-model") == {"text"}
    assert factory.model_supports("basic-model", "vision") is False


def test_openai_base_url_included(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "openai": {
                "type": "openai",
                "api_mode": "responses",
                "base_url": "https://example.com",
                "api_key": "sk-test",
            }
        },
    )

    factory.create_llm(model="gpt-4o")

    kw = mock_cls.call_args.kwargs
    assert "openai_api_base" in kw
    assert kw["openai_api_base"]  # 非空


def test_google_no_base_url_field(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(model="gemini-2.0-flash")

    kw = mock_cls.call_args.kwargs
    assert "openai_api_base" not in kw
    assert "base_url" not in kw


def test_vendor_prefix_stripped_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="openai/gpt-5.4-nano")

    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "openai/gpt-5.4-nano"


def test_vendor_prefix_stripped_google(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(model="google/gemini-2.5-flash")

    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "google/gemini-2.5-flash"


def test_vendor_prefix_stripped_anthropic(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)

    factory.create_llm(model="anthropic/claude-3-5-sonnet-20241022")

    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "anthropic/claude-3-5-sonnet-20241022"


def test_vendor_prefix_stripped_deepseek(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatDeepSeek", mock_cls)

    factory.create_llm(model="deepseek/deepseek-v4-flash")

    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "deepseek/deepseek-v4-flash"
