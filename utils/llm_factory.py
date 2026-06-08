from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
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
    static_kwargs: dict = field(default_factory=dict)


_OPENAI_VALID = {
    "streaming",
    "max_retries",
    "timeout",
    "use_responses_api",
    "reasoning_effort",
    "verbosity",
    "temperature",
    "model_kwargs",
    "extra_body",
}
_GOOGLE_VALID = {"streaming", "max_retries", "timeout", "temperature"}
_ANTHROPIC_VALID = {"streaming", "max_retries", "timeout", "temperature"}
_DEEPSEEK_VALID = {"streaming", "max_retries", "timeout", "temperature", "model_kwargs", "extra_body"}

_openai_config = ProviderConfig(
    cls_fn=lambda: ChatOpenAI,
    api_key_fn=lambda: EnvConfig.OPENAI_API_KEY,
    api_key_field="openai_api_key",
    valid_kwargs=_OPENAI_VALID,
    kwarg_map={"timeout": "request_timeout"},
    base_url_fn=lambda: EnvConfig.OPENAI_BASE_URL,
    base_url_field="openai_api_base",
)

_google_config = ProviderConfig(
    cls_fn=lambda: ChatGoogleGenerativeAI,
    api_key_fn=lambda: EnvConfig.GOOGLE_API_KEY,
    api_key_field="google_api_key",
    valid_kwargs=_GOOGLE_VALID,
)

_anthropic_config = ProviderConfig(
    cls_fn=lambda: ChatAnthropic,
    api_key_fn=lambda: EnvConfig.ANTHROPIC_API_KEY,
    api_key_field="anthropic_api_key",
    valid_kwargs=_ANTHROPIC_VALID,
    kwarg_map={"timeout": "default_request_timeout"},
    base_url_fn=lambda: EnvConfig.ANTHROPIC_BASE_URL,
    base_url_field="anthropic_api_url",
)

_deepseek_config = ProviderConfig(
    cls_fn=lambda: ChatDeepSeek,
    api_key_fn=lambda: EnvConfig.DEEPSEEK_API_KEY,
    api_key_field="api_key",
    valid_kwargs=_DEEPSEEK_VALID,
    base_url_fn=lambda: EnvConfig.DEEPSEEK_API_BASE,
    base_url_field="api_base",
)

_PROVIDER_CONFIGS = {
    "openai": _openai_config,
    "google": _google_config,
    "anthropic": _anthropic_config,
    "deepseek": _deepseek_config,
}


def _clean_optional(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _infer_provider(model: str) -> str:
    vendor, sep, route_key = model.partition("/")
    if sep and vendor.lower() in _PROVIDER_CONFIGS:
        return vendor.lower()
    route_key = route_key if sep else model
    match route_key:
        case k if k.startswith("deepseek"):
            return "deepseek"
        case k if k.startswith(("gemini-", "google")):
            return "google"
        case k if k.startswith(("claude-", "anthropic")):
            return "anthropic"
        case _:
            return "openai"


def _endpoint_profile(endpoint: str | None) -> dict:
    endpoint_name = _clean_optional(endpoint)
    if not endpoint_name:
        return {}
    profile = EnvConfig.LLM_ENDPOINTS.get(endpoint_name)
    if profile is None:
        raise ValueError(f"未知 LLM endpoint profile: {endpoint_name!r}")
    if not isinstance(profile, dict):
        raise ValueError(f"LLM endpoint profile 必须是表格: {endpoint_name!r}")
    return profile


def _normalize_capabilities(capabilities: object) -> set[str]:
    if not isinstance(capabilities, list):
        return set()
    return {capability.strip().lower() for capability in capabilities if isinstance(capability, str) and capability.strip()}


def _model_specific_capabilities(model: str) -> set[str]:
    if model == EnvConfig.BASIC_MODEL:
        return _normalize_capabilities(EnvConfig.BASIC_MODEL_CAPABILITIES)
    if model == EnvConfig.ADVAN_MODEL:
        return _normalize_capabilities(EnvConfig.ADVAN_MODEL_CAPABILITIES)
    if model == EnvConfig.SIGNAL_MODEL:
        return _normalize_capabilities(EnvConfig.SIGNAL_MODEL_CAPABILITIES)
    return set()


def get_model_capabilities(model: str, endpoint: str | None = None) -> set[str]:
    capabilities = _model_specific_capabilities(model)
    if capabilities:
        return capabilities
    capabilities = _normalize_capabilities(_endpoint_profile(endpoint).get("capabilities"))
    return capabilities or {"text"}


def model_supports(model: str, capability: str, endpoint: str | None = None) -> bool:
    return capability.strip().lower() in get_model_capabilities(model, endpoint=endpoint)


def create_llm(model: str, provider: str | None = None, endpoint: str | None = None, **kwargs) -> BaseChatModel:
    """根据模型名称前缀路由到对应 Provider，自动过滤不支持的 kwargs。

    模型名支持 vendor/model 格式（如 "openai/gpt-4o"），vendor 前缀仅用于路由判断，
    传入框架的模型名保持原始值。未匹配 Google/Anthropic 前缀的模型均视为 OpenAI-compatible。
    """
    profile = _endpoint_profile(endpoint)
    provider_name = _clean_optional(provider) or _clean_optional(profile.get("provider")) or _infer_provider(model)
    config = _PROVIDER_CONFIGS.get(provider_name.lower())
    if config is None:
        raise ValueError(f"未知 LLM provider: {provider_name!r}")

    cls = config.cls_fn()
    api_key = SecretStr(profile["api_key"]) if _clean_optional(profile.get("api_key")) else config.api_key_fn()
    filtered: dict = {}
    for k, v in kwargs.items():
        if k in config.valid_kwargs:
            actual_key = config.kwarg_map.get(k, k)
            filtered[actual_key] = v
    base_url = _clean_optional(profile.get("base_url"))
    if config.base_url_fn and config.base_url_field:
        if not base_url:
            base_url = config.base_url_fn()
        if base_url:
            filtered[config.base_url_field] = base_url
    return cls(**{config.api_key_field: api_key, "model": model, **filtered, **config.static_kwargs})
