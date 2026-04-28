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


def test_gpt_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="gpt-4o", timeout=300, streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "gpt-4o"
    assert "openai_api_key" in kw
    assert "openai_api_base" in kw
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
    monkeypatch.setattr(factory.EnvConfig, "ANTHROPIC_BASE_URL", "https://anthropic.example.com")

    factory.create_llm(model="claude-3-5-sonnet-20241022", timeout=60)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "claude-3-5-sonnet-20241022"
    assert "anthropic_api_key" in kw
    assert kw["anthropic_api_url"] == "https://anthropic.example.com"
    assert kw.get("default_request_timeout") == 60  # timeout → default_request_timeout
    assert "timeout" not in kw


def test_openai_kwargs_filtered_for_google(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(
        model="gemini-2.5-flash",
        use_responses_api=True,
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
        use_responses_api=True,
        reasoning_effort="medium",
        max_retries=2,
    )

    kw = mock_cls.call_args.kwargs
    assert "use_responses_api" not in kw
    assert "reasoning_effort" not in kw
    assert kw.get("max_retries") == 2


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


def test_endpoint_profile_can_set_provider_base_url_and_api_key(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_ENDPOINTS",
        {
            "anthropic_proxy": {
                "provider": "anthropic",
                "base_url": "https://anthropic-proxy.example.com",
                "api_key": "ant-profile",
            }
        },
    )

    factory.create_llm(model="custom-sonnet", endpoint="anthropic_proxy")

    kw = mock_cls.call_args.kwargs
    assert kw["anthropic_api_key"].get_secret_value() == "ant-profile"
    assert kw["anthropic_api_url"] == "https://anthropic-proxy.example.com"


def test_endpoint_profile_overrides_openai_base_url(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_ENDPOINTS",
        {
            "openrouter": {
                "provider": "openai",
                "base_url": "https://openrouter.example.com/api/v1",
                "api_key": "sk-openrouter",
            }
        },
    )

    factory.create_llm(model="any-model", endpoint="openrouter")

    kw = mock_cls.call_args.kwargs
    assert kw["openai_api_key"].get_secret_value() == "sk-openrouter"
    assert kw["openai_api_base"] == "https://openrouter.example.com/api/v1"


def test_unknown_endpoint_profile_raises():
    with pytest.raises(ValueError, match="未知 LLM endpoint profile"):
        factory.create_llm(model="gpt-4o", endpoint="missing")


def test_model_capabilities_default_to_text(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "LLM_ENDPOINTS", {})

    assert factory.get_model_capabilities("unknown-model") == {"text"}
    assert factory.model_supports("unknown-model", "text") is True
    assert factory.model_supports("unknown-model", "vision") is False


def test_model_capabilities_use_model_specific_config(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL_CAPABILITIES", ["text", "vision"])
    monkeypatch.setattr(factory.EnvConfig, "LLM_ENDPOINTS", {})

    assert factory.get_model_capabilities("basic-model") == {"text", "vision"}
    assert factory.model_supports("basic-model", "vision") is True


def test_model_capabilities_fall_back_to_endpoint_profile(monkeypatch):
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(factory.EnvConfig, "BASIC_MODEL_CAPABILITIES", [])
    monkeypatch.setattr(
        factory.EnvConfig,
        "LLM_ENDPOINTS",
        {
            "text_gateway": {
                "provider": "openai",
                "capabilities": ["text"],
            }
        },
    )

    assert factory.get_model_capabilities("basic-model", endpoint="text_gateway") == {"text"}
    assert factory.model_supports("basic-model", "vision", endpoint="text_gateway") is False


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
