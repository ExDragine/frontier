from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from utils.configs import EnvConfig

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


@dataclass
class ProviderConfig:
    cls_fn: Callable[[], type[BaseChatModel]]  # 延迟求值，支持测试时替换
    api_key_fn: Callable[[], SecretStr]
    api_key_field: str
    valid_kwargs: set[str]
    kwarg_map: dict[str, str] = field(default_factory=dict)
    base_url_fn: Callable[[], str] | None = None
    base_url_field: str | None = None


_OPENAI_VALID = {
    "streaming", "max_retries", "timeout",
    "use_responses_api", "reasoning_effort", "verbosity", "temperature",
}
_GOOGLE_VALID = {"streaming", "max_retries", "timeout", "temperature"}
_ANTHROPIC_VALID = {"streaming", "max_retries", "timeout", "temperature"}

# Store original references for comparison
_ORIG_OPENAI = ChatOpenAI
_ORIG_GOOGLE = ChatGoogleGenerativeAI
_ORIG_ANTHROPIC = ChatAnthropic

_openai_config = ProviderConfig(
    cls_fn=lambda: (getattr(sys.modules.get('utils.llm_factory'), 'ChatOpenAI', _ORIG_OPENAI)
                    if getattr(sys.modules.get('utils.llm_factory'), 'ChatOpenAI', _ORIG_OPENAI) is not _ORIG_OPENAI
                    else sys.modules['langchain_openai'].ChatOpenAI),
    api_key_fn=lambda: EnvConfig.OPENAI_API_KEY,
    api_key_field="openai_api_key",
    valid_kwargs=_OPENAI_VALID,
    kwarg_map={"timeout": "request_timeout"},
    base_url_fn=lambda: EnvConfig.OPENAI_BASE_URL,
    base_url_field="openai_api_base",
)

_google_config = ProviderConfig(
    cls_fn=lambda: (getattr(sys.modules.get('utils.llm_factory'), 'ChatGoogleGenerativeAI', _ORIG_GOOGLE)
                    if getattr(sys.modules.get('utils.llm_factory'), 'ChatGoogleGenerativeAI', _ORIG_GOOGLE) is not _ORIG_GOOGLE
                    else sys.modules['langchain_google_genai'].ChatGoogleGenerativeAI),
    api_key_fn=lambda: EnvConfig.GOOGLE_API_KEY,
    api_key_field="google_api_key",
    valid_kwargs=_GOOGLE_VALID,
)

_anthropic_config = ProviderConfig(
    cls_fn=lambda: (getattr(sys.modules.get('utils.llm_factory'), 'ChatAnthropic', _ORIG_ANTHROPIC)
                    if getattr(sys.modules.get('utils.llm_factory'), 'ChatAnthropic', _ORIG_ANTHROPIC) is not _ORIG_ANTHROPIC
                    else sys.modules['langchain_anthropic'].ChatAnthropic),
    api_key_fn=lambda: EnvConfig.ANTHROPIC_API_KEY,
    api_key_field="anthropic_api_key",
    valid_kwargs=_ANTHROPIC_VALID,
    kwarg_map={"timeout": "default_request_timeout"},
)

PROVIDERS: list[tuple[str, ProviderConfig]] = [
    ("gemini-", _google_config),
    ("google/", _google_config),
    ("gpt-", _openai_config),
    ("openai/", _openai_config),
    ("o1", _openai_config),
    ("o3", _openai_config),
    ("o4", _openai_config),
    ("claude-", _anthropic_config),
]


def create_llm(model: str, **kwargs) -> BaseChatModel:
    """根据模型名称前缀路由到对应 Provider，自动过滤不支持的 kwargs。"""
    for prefix, config in PROVIDERS:
        if model.startswith(prefix):
            cls = config.cls_fn()
            api_key = config.api_key_fn()
            filtered: dict = {}
            for k, v in kwargs.items():
                if k in config.valid_kwargs:
                    actual_key = config.kwarg_map.get(k, k)
                    filtered[actual_key] = v
            if config.base_url_fn and config.base_url_field:
                filtered[config.base_url_field] = config.base_url_fn()
            return cls(**{config.api_key_field: api_key, "model": model, **filtered})
    raise ValueError(
        f"未知模型前缀，无法路由: {model!r}。"
        f"支持的前缀: {[p for p, _ in PROVIDERS]}"
    )
