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
    assert kw.get("request_timeout") == 300   # timeout → request_timeout
    assert "timeout" not in kw                # raw "timeout" filtered out


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

    factory.create_llm(model="claude-3-5-sonnet-20241022", timeout=60)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "claude-3-5-sonnet-20241022"
    assert "anthropic_api_key" in kw
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
    assert kw.get("max_retries") == 2   # 通用参数正常传入


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


def test_unknown_prefix_raises():
    with pytest.raises(ValueError, match="未知模型前缀"):
        factory.create_llm(model="mistral-7b-instruct")


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
