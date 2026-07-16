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
    base_url_field: str | None = None
    static_kwargs: dict = field(default_factory=dict)


_OPENAI_VALID = {
    "streaming",
    "max_retries",
    "timeout",
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
    base_url_field="openai_api_base",
)

_google_config = ProviderConfig(
    cls_fn=lambda: ChatGoogleGenerativeAI,
    api_key_fn=lambda: EnvConfig.GOOGLE_API_KEY,
    api_key_field="google_api_key",
    valid_kwargs=_GOOGLE_VALID,
    base_url_field="base_url",
)

_anthropic_config = ProviderConfig(
    cls_fn=lambda: ChatAnthropic,
    api_key_fn=lambda: EnvConfig.ANTHROPIC_API_KEY,
    api_key_field="anthropic_api_key",
    valid_kwargs=_ANTHROPIC_VALID,
    kwarg_map={"timeout": "default_request_timeout"},
    base_url_field="anthropic_api_url",
)

_deepseek_config = ProviderConfig(
    cls_fn=lambda: ChatDeepSeek,
    api_key_fn=lambda: EnvConfig.DEEPSEEK_API_KEY,
    api_key_field="api_key",
    valid_kwargs=_DEEPSEEK_VALID,
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


def _provider_profile(model: str, provider: str | None) -> tuple[str, dict]:
    profile_name = _clean_optional(provider) or _infer_provider(model)
    profile = EnvConfig.LLM_PROVIDERS.get(profile_name)
    if profile is None:
        raise ValueError(f"未知 LLM provider profile: {profile_name!r}")
    if not isinstance(profile, dict):
        raise ValueError(f"LLM provider profile 必须是表格: {profile_name!r}")
    return profile_name, profile


def _normalize_capabilities(capabilities: object) -> set[str]:
    if not isinstance(capabilities, list):
        return set()
    normalized = {
        capability.strip().lower() for capability in capabilities if isinstance(capability, str) and capability.strip()
    }
    return {"vision" if capability == "image" else capability for capability in normalized}


def _model_specific_capabilities(model: str, role: str | None = None) -> set[str]:
    role_capabilities = {
        "basic": (EnvConfig.BASIC_MODEL, EnvConfig.BASIC_MODEL_CAPABILITIES),
        "signal": (EnvConfig.SIGNAL_MODEL, EnvConfig.SIGNAL_MODEL_CAPABILITIES),
        "advanced": (EnvConfig.ADVAN_MODEL, EnvConfig.ADVAN_MODEL_CAPABILITIES),
    }
    if role is not None:
        configured = role_capabilities.get(role)
        if configured is None:
            raise ValueError(f"未知模型角色: {role!r}")
        configured_model, capabilities = configured
        return _normalize_capabilities(capabilities) if model == configured_model else set()

    capabilities: set[str] = set()
    for configured_model, configured_capabilities in role_capabilities.values():
        if model == configured_model:
            capabilities.update(_normalize_capabilities(configured_capabilities))
    return capabilities


def get_model_capabilities(model: str, *, role: str | None = None) -> set[str]:
    capabilities = _model_specific_capabilities(model, role)
    return capabilities or {"text"}


def model_supports(model: str, capability: str, *, role: str | None = None) -> bool:
    requested = _normalize_capabilities([capability])
    return bool(requested & get_model_capabilities(model, role=role))


def provider_uses_responses_api(model: str, provider: str | None = None) -> bool:
    _, profile = _provider_profile(model, provider)
    provider_type = (_clean_optional(profile.get("type")) or _infer_provider(model)).lower()
    return provider_type == "openai" and bool(profile.get("use_responses_api", False))


def create_llm(model: str, provider: str | None = None, **kwargs) -> BaseChatModel:
    """根据供应商 profile 路由模型，并过滤底层 SDK 不支持的参数。

    ``provider`` 指向 ``[providers.<name>]``；未指定时按模型名称推断官方供应商。
    profile 的 ``type`` 决定底层协议，``use_responses_api`` 仅对 OpenAI 协议生效。
    """
    if "endpoint" in kwargs:
        raise TypeError("create_llm() 不再接受 endpoint，请通过 provider 选择供应商 profile")
    if "use_responses_api" in kwargs:
        raise TypeError("create_llm() 不再接受 use_responses_api，请在供应商 profile 中配置")
    _, profile = _provider_profile(model, provider)
    provider_type = (_clean_optional(profile.get("type")) or _infer_provider(model)).lower()
    config = _PROVIDER_CONFIGS.get(provider_type)
    if config is None:
        raise ValueError(f"未知 LLM provider type: {provider_type!r}")

    cls = config.cls_fn()
    api_key = SecretStr(profile["api_key"]) if _clean_optional(profile.get("api_key")) else config.api_key_fn()
    filtered: dict = {}
    for k, v in kwargs.items():
        if k in config.valid_kwargs:
            actual_key = config.kwarg_map.get(k, k)
            filtered[actual_key] = v
    if provider_type == "openai":
        filtered["use_responses_api"] = bool(profile.get("use_responses_api", False))
    base_url = _clean_optional(profile.get("base_url"))
    if base_url and config.base_url_field:
        filtered[config.base_url_field] = base_url
    return cls(**{config.api_key_field: api_key, "model": model, **filtered, **config.static_kwargs})
