# ruff: noqa: S101

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
                "base_url": "https://anthropic.example.com",
                "use_responses_api": False,
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
        {"deepseek": {"type": "deepseek", "base_url": "", "use_responses_api": False}},
    )

    factory.create_llm(model="deepseek-v4-flash", timeout=30, max_retries=2)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "deepseek-v4-flash"
    assert "api_key" in kw
    assert "api_base" not in kw
    assert kw["timeout"] == 30
    assert kw["max_retries"] == 2


def test_deepseek_provider_profile_overrides_api_key_and_base_url(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatDeepSeek", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_PROVIDERS",
        {
            "deepseek_signal": {
                "type": "deepseek",
                "base_url": "https://deepseek.example.com/v1",
                "api_key": "sk-deepseek-profile",
                "use_responses_api": False,
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
    )

    kw = mock_cls.call_args.kwargs
    assert "use_responses_api" not in kw
    assert "reasoning_effort" not in kw
    assert kw.get("max_retries") == 2


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
                "base_url": "https://anthropic-proxy.example.com",
                "api_key": "ant-profile",
                "use_responses_api": False,
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
                "base_url": "https://openrouter.example.com/api/v1",
                "api_key": "sk-openrouter",
                "use_responses_api": False,
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
                "capabilities": ["text", "vision"],
                "use_responses_api": True,
            }
        },
    )

    assert factory.get_model_capabilities("basic-model") == {"text"}
    assert factory.model_supports("basic-model", "vision") is False


def test_openai_base_url_included(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

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
