from __future__ import annotations

import json
import os
import secrets
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

import dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr

dotenv.load_dotenv()

CONFIG_VERSION = 2
CONFIG_PATH = Path(os.getenv("FRONTIER_CONFIG", "env.toml"))
_DEFAULT_DASHBOARD_JWT_SECRET = "frontier-dashboard-default-secret"  # noqa: S105
_DEEPSEEK_RESPONSES_BASE_URL = "https://api.deepseek.com"
_DEEPSEEK_ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
_API_MODE_CHAT_COMPLETIONS = "chat_completions"
_API_MODE_RESPONSES = "responses"
_API_MODE_MESSAGES = "messages"
_API_MODE_GENERATE_CONTENT = "generate_content"
_VALID_API_MODES = {
    _API_MODE_CHAT_COMPLETIONS,
    _API_MODE_RESPONSES,
    _API_MODE_MESSAGES,
    _API_MODE_GENERATE_CONTENT,
}
_PROVIDER_API_MODES = {
    "openai": {_API_MODE_CHAT_COMPLETIONS, _API_MODE_RESPONSES},
    "google": {_API_MODE_GENERATE_CONTENT},
    "anthropic": {_API_MODE_MESSAGES},
    "deepseek": {_API_MODE_CHAT_COMPLETIONS},
}


class _FrozenConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BotConfig(_FrozenConfig):
    system_prompt: str = ""


class ModelConfig(_FrozenConfig):
    model: str = ""
    provider: str = ""
    capabilities: tuple[str, ...] = ()


class MediaModelConfig(_FrozenConfig):
    model: str = ""
    provider: str = ""


class PaintModelConfig(MediaModelConfig):
    size: str = "1024x1024"
    quality: str = "auto"


class VideoModelConfig(MediaModelConfig):
    size: str = "1280x720"
    seconds: str = "8"


class ModelsConfig(_FrozenConfig):
    basic: ModelConfig = Field(default_factory=ModelConfig)
    signal: ModelConfig = Field(
        default_factory=lambda: ModelConfig(
            model="deepseek-v4-flash",
            provider="deepseek",
            capabilities=("text",),
        )
    )
    advanced: ModelConfig = Field(default_factory=ModelConfig)
    daily_news: ModelConfig = Field(
        default_factory=lambda: ModelConfig(
            model="deepseek-v4-flash",
            provider="deepseek_responses",
            capabilities=("text",),
        )
    )
    paint: PaintModelConfig = Field(default_factory=lambda: PaintModelConfig(provider="openai"))
    video: VideoModelConfig = Field(
        default_factory=lambda: VideoModelConfig(
            model="sora-2",
            provider="openai",
        )
    )


class ProviderProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    type: str = ""
    api_mode: str = ""
    base_url: str = ""
    api_key: str = ""


class KeyConfig(_FrozenConfig):
    nasa_api_key: SecretStr = Field(default_factory=lambda: SecretStr("DEMO_KEY"))
    github_pat: SecretStr = Field(default_factory=lambda: SecretStr(""))


class FeatureConfig(_FrozenConfig):
    agent_enabled: bool = True
    paint_enabled: bool = True
    video_enabled: bool = True


class AgentConfig(_FrozenConfig):
    reasoning_effort: str = "medium"


class DshAgentConfig(_FrozenConfig):
    provider: str = "deepseek"
    model: str = "deepseek-v4-flash"
    max_tokens: int = Field(default=49_152, ge=1)


class AccessPolicy(_FrozenConfig):
    whitelist_mode: bool = False
    whitelist_person_list: tuple[int | str, ...] = ()
    whitelist_group_list: tuple[int | str, ...] = ()
    blacklist_person_list: tuple[int | str, ...] = ()
    blacklist_group_list: tuple[int | str, ...] = ()


class AutoReplyPolicy(_FrozenConfig):
    whitelist_mode: bool = False
    whitelist_group_list: tuple[int | str, ...] = ()
    blacklist_group_list: tuple[int | str, ...] = ()


class LimitConfig(_FrozenConfig):
    paint_rate_limit_max_requests: int = Field(default=3, ge=1)
    paint_rate_limit_window_seconds: int = Field(default=600, ge=1)
    video_rate_limit_max_requests: int = Field(default=1, ge=1)
    video_rate_limit_window_seconds: int = Field(default=900, ge=1)
    video_poll_interval_seconds: int = Field(default=15, ge=1)
    video_poll_timeout_seconds: int = Field(default=900, ge=1)
    agent_llm_timeout_seconds: int = Field(default=900, ge=1)
    agent_job_timeout_seconds: int = Field(default=3600, ge=1)


class NotificationConfig(_FrozenConfig):
    test_group_id: tuple[int | str, ...] = ()
    announce_group_id: tuple[int | str, ...] = ()
    apod_group_id: tuple[int | str, ...] = ()
    earth_now_group_id: tuple[int | str, ...] = ()
    news_summary_group_id: tuple[int | str, ...] = ()
    earthquake_group_id: tuple[int | str, ...] = ()
    nrc_merchant_group_id: tuple[int | str, ...] = ()


class StorageConfig(_FrozenConfig):
    query_message_numbers: int = Field(default=100, ge=1)
    image_enabled: bool = True
    image_ttl_days: int = Field(default=30, ge=1)
    media_ttl_days: int = Field(default=30, ge=1)
    max_inline_images: int = Field(default=4, ge=0)
    max_inline_media_bytes: int = Field(default=20 * 1024 * 1024, ge=0)
    image_auto_cleanup: bool = True


class DebugConfig(_FrozenConfig):
    agent_debug_mode: bool = False


class DashboardConfig(_FrozenConfig):
    password: str = "admin"  # noqa: S105 - backward-compatible insecure default warning
    jwt_secret: str = _DEFAULT_DASHBOARD_JWT_SECRET
    jwt_expire_hours: int = Field(default=24, ge=1)


class ContentCheckConfig(_FrozenConfig):
    enabled: bool = False


class FrontierSettings(_FrozenConfig):
    config_version: int = Field(default=1, ge=1, le=CONFIG_VERSION)
    bot: BotConfig = Field(default_factory=BotConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    providers: dict[str, ProviderProfile] = Field(default_factory=dict)
    keys: KeyConfig = Field(default_factory=KeyConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    dsh: DshAgentConfig = Field(default_factory=DshAgentConfig)
    agent_policy: AccessPolicy = Field(default_factory=AccessPolicy)
    auto_reply_policy: AutoReplyPolicy = Field(default_factory=AutoReplyPolicy)
    paint_policy: AccessPolicy = Field(default_factory=AccessPolicy)
    limits: LimitConfig = Field(default_factory=LimitConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    content_check: ContentCheckConfig = Field(default_factory=ContentCheckConfig)


def _section(config: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name, {})
    if not isinstance(value, Mapping):
        raise TypeError(f"配置段 [{name}] 必须是 TOML table")
    return dict(value)


def _pick(modern: Mapping[str, Any], legacy: Mapping[str, Any], key: str, default: Any, legacy_key: str | None = None):
    if key in modern:
        return modern[key]
    return legacy.get(legacy_key or key, default)


def load_nicknames(raw: str | None = None) -> tuple[str, ...]:
    """从 NoneBot 的 NICKNAME 环境变量读取有序名称列表。"""
    value = os.getenv("NICKNAME", "") if raw is None else raw
    value = value.strip()
    if not value:
        raise ValueError('必须在 .env 中配置至少一个非空 NICKNAME，例如 ["Frontier"]')

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value

    if isinstance(parsed, str):
        candidates = [parsed]
    elif isinstance(parsed, list):
        candidates = parsed
    else:
        raise ValueError('NICKNAME 必须是字符串或 JSON 字符串数组，例如 ["Frontier"]')

    nicknames: list[str] = []
    for item in candidates:
        if not isinstance(item, str):
            raise ValueError("NICKNAME 数组中的每一项都必须是字符串")
        nickname = item.strip()
        if nickname and nickname not in nicknames:
            nicknames.append(nickname)
    if not nicknames:
        raise ValueError('必须在 .env 中配置至少一个非空 NICKNAME，例如 ["Frontier"]')
    return tuple(nicknames)


def _validate_v2_model_provider_sections(
    config_version: object,
    models: Mapping[str, Any],
    providers: Mapping[str, Any],
    keys: Mapping[str, Any],
) -> None:
    if not isinstance(config_version, int) or config_version < 2:
        return
    removed_model_fields = sorted(
        key
        for key in models
        if key.endswith("_model_endpoint")
        or key.endswith("_model_use_responses_api")
        or key in {"paint_base_url", "video_base_url"}
    )
    if removed_model_fields:
        raise ValueError(
            "[models] 不再接受 endpoint、base_url 或 use_responses_api，请配置到 [providers.<name>]: "
            + ", ".join(removed_model_fields)
        )
    removed_key_fields = sorted(
        key
        for key in keys
        if key
        in {
            "openai_api_key",
            "paint_api_key",
            "video_api_key",
            "google_api_key",
            "anthropic_api_key",
            "deepseek_api_key",
        }
    )
    if removed_key_fields:
        raise ValueError(
            "[key] 不再接受模型 API key，请配置到 [providers.<name>].api_key: " + ", ".join(removed_key_fields)
        )
    for name, raw_profile in providers.items():
        if not isinstance(raw_profile, Mapping):
            raise ValueError(f"[providers.{name}] 必须是供应商 table")
        if "capabilities" in raw_profile:
            raise ValueError(f"[providers.{name}] 不再接受 capabilities，请配置到对应模型")
        api_mode = raw_profile.get("api_mode")
        if api_mode is not None and (not isinstance(api_mode, str) or api_mode.strip().lower() not in _VALID_API_MODES):
            raise ValueError(f"[providers.{name}].api_mode 无效: {api_mode!r}")
        if "use_responses_api" in raw_profile and api_mode is not None:
            uses_responses = bool(raw_profile["use_responses_api"])
            if (api_mode.strip().lower() == _API_MODE_RESPONSES) != uses_responses:
                raise ValueError(
                    f"[providers.{name}] 的 api_mode 与旧字段 use_responses_api 冲突；请只保留 api_mode"
                )


def _default_api_mode(provider_type: str, *, legacy_openai_responses: bool = False) -> str:
    if provider_type == "deepseek_responses":
        return _API_MODE_RESPONSES
    if provider_type == "openai":
        return _API_MODE_RESPONSES if legacy_openai_responses else _API_MODE_CHAT_COMPLETIONS
    return {
        "google": _API_MODE_GENERATE_CONTENT,
        "anthropic": _API_MODE_MESSAGES,
        "deepseek": _API_MODE_CHAT_COMPLETIONS,
    }.get(provider_type, "")


def _legacy_api_mode(provider_type: str, use_responses_api: bool) -> str:
    if provider_type in {"openai", "deepseek", "deepseek_responses"}:
        return _API_MODE_RESPONSES if use_responses_api else _API_MODE_CHAT_COMPLETIONS
    return _default_api_mode(provider_type)


def _migrate_legacy_responses_adapter(profile: dict[str, Any], used_legacy_flag: bool) -> None:
    provider_type = str(profile.get("type", "")).strip().lower()
    if provider_type == "deepseek_responses":
        profile["type"] = "openai"
        profile["api_mode"] = _API_MODE_RESPONSES
        profile["base_url"] = profile.get("base_url") or _DEEPSEEK_RESPONSES_BASE_URL
    elif used_legacy_flag and provider_type == "deepseek" and profile.get("api_mode") == _API_MODE_RESPONSES:
        profile["type"] = "openai"
        profile["base_url"] = profile.get("base_url") or _DEEPSEEK_RESPONSES_BASE_URL


def _validate_normalized_provider_protocols(provider_profiles: dict[str, dict[str, Any]]) -> None:
    for name, profile in provider_profiles.items():
        provider_type = str(profile.get("type", "")).strip().lower()
        api_mode = str(profile.get("api_mode", "")).strip().lower()
        profile["type"] = provider_type
        profile["api_mode"] = api_mode
        supported_modes = _PROVIDER_API_MODES.get(provider_type)
        if supported_modes is None:
            continue
        if api_mode not in supported_modes:
            raise ValueError(
                f"[providers.{name}] 的 type={provider_type!r} 不支持 api_mode={api_mode!r}"
            )


def _normalize_modern_provider_profile(
    name: str,
    raw_profile: Mapping[str, Any],
    existing: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    profile = dict(raw_profile)
    used_legacy_flag = "use_responses_api" in profile
    provider_type = str(
        profile.pop("provider", profile.get("type", existing.get("type", name if existing else "")))
    ).strip().lower()
    profile["type"] = provider_type
    legacy_response_value = profile.pop("use_responses_api", None)
    if "api_mode" not in profile:
        if used_legacy_flag:
            profile["api_mode"] = _legacy_api_mode(provider_type, bool(legacy_response_value))
        elif existing and provider_type == existing.get("type"):
            profile["api_mode"] = existing.get("api_mode", "")
        else:
            profile["api_mode"] = _default_api_mode(provider_type)
    profile.pop("capabilities", None)
    normalized = {**existing, **profile}
    _migrate_legacy_responses_adapter(normalized, used_legacy_flag)
    return normalized, used_legacy_flag or "api_mode" in raw_profile


def _normalize_legacy_provider_profile(
    raw_profile: Mapping[str, Any],
    existing: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    profile = dict(raw_profile)
    used_legacy_flag = "use_responses_api" in profile
    provider_type = str(profile.get("type") or profile.get("provider") or existing.get("type", "")).strip().lower()
    if "api_mode" in profile:
        api_mode = profile["api_mode"]
    elif used_legacy_flag:
        api_mode = _legacy_api_mode(provider_type, bool(profile["use_responses_api"]))
    elif existing.get("api_mode"):
        api_mode = existing["api_mode"]
    else:
        api_mode = _default_api_mode(provider_type, legacy_openai_responses=True)
    normalized = {
        **existing,
        "type": provider_type,
        "api_mode": api_mode,
        "base_url": profile.get("base_url") or existing.get("base_url", ""),
        # 旧版 endpoint profile 的空密钥会回退到 [key] 中对应供应商的密钥。
        "api_key": profile.get("api_key") or existing.get("api_key", ""),
    }
    _migrate_legacy_responses_adapter(normalized, used_legacy_flag)
    return normalized, used_legacy_flag or "api_mode" in profile


def _normalize_provider_profiles(
    providers: Mapping[str, Any],
    legacy_endpoint: Mapping[str, Any],
    keys: Mapping[str, Any],
    legacy_profiles: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    profiles: dict[str, dict[str, Any]] = {
        "openai": {
            "type": "openai",
            "api_mode": _API_MODE_RESPONSES,
            "base_url": _pick(providers, legacy_endpoint, "openai_base_url", ""),
            "api_key": keys.get("openai_api_key", ""),
        },
        "google": {
            "type": "google",
            "api_mode": _API_MODE_GENERATE_CONTENT,
            "base_url": "",
            "api_key": keys.get("google_api_key", ""),
        },
        "anthropic": {
            "type": "anthropic",
            "api_mode": _API_MODE_MESSAGES,
            "base_url": _pick(providers, keys, "anthropic_base_url", ""),
            "api_key": keys.get("anthropic_api_key", ""),
        },
        "deepseek": {
            "type": "deepseek",
            "api_mode": _API_MODE_CHAT_COMPLETIONS,
            "base_url": _pick(providers, keys, "deepseek_base_url", "", "deepseek_api_base"),
            "api_key": keys.get("deepseek_api_key", ""),
        },
        "deepseek_responses": {
            "type": "openai",
            "api_mode": _API_MODE_RESPONSES,
            "base_url": _DEEPSEEK_RESPONSES_BASE_URL,
            "api_key": keys.get("deepseek_api_key", ""),
        },
        "deepseek_anthropic": {
            "type": "anthropic",
            "api_mode": _API_MODE_MESSAGES,
            "base_url": _DEEPSEEK_ANTHROPIC_BASE_URL,
            "api_key": keys.get("deepseek_api_key", ""),
        },
    }
    explicit_api_modes: set[str] = set()
    for name, raw_profile in providers.items():
        if not isinstance(raw_profile, Mapping):
            continue
        normalized, explicit_mode = _normalize_modern_provider_profile(name, raw_profile, profiles.get(name, {}))
        profiles[name] = normalized
        if explicit_mode:
            explicit_api_modes.add(name)

    for name, raw_profile in legacy_profiles.items():
        if not isinstance(raw_profile, Mapping):
            continue
        normalized, explicit_mode = _normalize_legacy_provider_profile(raw_profile, profiles.get(name, {}))
        profiles[name] = normalized
        if explicit_mode:
            explicit_api_modes.add(name)
    return profiles, explicit_api_modes


def _normalize_model_roles(
    models: Mapping[str, Any],
    legacy_endpoint: Mapping[str, Any],
    legacy_profiles: Mapping[str, Any],
    provider_profiles: dict[str, dict[str, Any]],
    explicit_api_modes: set[str],
) -> dict[str, dict[str, Any]]:
    def model_role(prefix: str, legacy_prefix: str, defaults: tuple[Any, str, list[str], bool]) -> dict[str, Any]:
        default_model, default_provider, default_capabilities, default_responses = defaults

        def role_value(suffix: str, default: Any):
            modern_key = f"{prefix}_{suffix}"
            legacy_key = f"{legacy_prefix}_{suffix}"
            return models[modern_key] if modern_key in models else legacy_endpoint.get(legacy_key, default)

        provider_name = role_value("model_provider", default_provider)
        endpoint_name = role_value("model_endpoint", "")
        provider_ref = endpoint_name or provider_name
        capabilities = role_value("model_capabilities", default_capabilities)
        legacy_profile = legacy_profiles.get(endpoint_name, {})
        if not capabilities and isinstance(legacy_profile, Mapping):
            capabilities = legacy_profile.get("capabilities", [])

        response_key = f"{prefix}_model_use_responses_api"
        legacy_response_key = f"{legacy_prefix}_model_use_responses_api"
        response_explicit = response_key in models or legacy_response_key in legacy_endpoint
        response_value = (
            models[response_key]
            if response_key in models
            else legacy_endpoint.get(legacy_response_key, default_responses)
        )
        if provider_ref and response_explicit and provider_ref not in explicit_api_modes:
            profile = provider_profiles.setdefault(
                provider_ref,
                {
                    "type": provider_name or provider_ref,
                    "base_url": "",
                },
            )
            provider_type = str(profile.get("type", "")).strip().lower()
            profile["api_mode"] = _legacy_api_mode(provider_type, bool(response_value))
            _migrate_legacy_responses_adapter(profile, used_legacy_flag=True)
        return {
            "model": role_value("model", default_model),
            "provider": provider_ref,
            "capabilities": capabilities,
        }

    return {
        "basic": model_role("basic", "basic", ("", "", [], True)),
        "signal": model_role("signal", "signal", ("deepseek-v4-flash", "deepseek", ["text"], False)),
        "advanced": model_role("advanced", "advan", ("", "", [], True)),
        "daily_news": model_role(
            "daily_news",
            "daily_news",
            ("deepseek-v4-flash", "deepseek_responses", ["text"], True),
        ),
    }


def _legacy_media_provider(
    profiles: dict[str, dict[str, Any]],
    *,
    preferred_name: str,
    base_url: str,
    api_key: str,
) -> str:
    for name, profile in profiles.items():
        if (
            profile.get("type") == "openai"
            and profile.get("base_url", "") == base_url
            and profile.get("api_key", "") == api_key
        ):
            return name

    name = preferred_name
    suffix = 2
    while name in profiles:
        name = f"{preferred_name}_{suffix}"
        suffix += 1
    profiles[name] = {
        "type": "openai",
        "api_mode": _API_MODE_CHAT_COMPLETIONS,
        "base_url": base_url,
        "api_key": api_key,
    }
    return name


def _normalize_paint_size(models: Mapping[str, Any], legacy_endpoint: Mapping[str, Any]) -> str:
    if "paint_size" in models:
        return str(models["paint_size"])

    image_size = str(_pick(models, legacy_endpoint, "paint_image_size", "1K")).upper()
    aspect_ratio = str(_pick(models, legacy_endpoint, "paint_aspect_ratio", "1:1"))
    if "x" in image_size.lower():
        return image_size.lower()

    legacy_sizes = {
        ("1K", "1:1"): "1024x1024",
        ("1K", "16:9"): "1536x1024",
        ("1K", "9:16"): "1024x1536",
        ("2K", "1:1"): "2048x2048",
        ("2K", "16:9"): "2048x1152",
        ("2K", "9:16"): "1152x2048",
        ("4K", "16:9"): "3840x2160",
        ("4K", "9:16"): "2160x3840",
    }
    return legacy_sizes.get((image_size, aspect_ratio), "1024x1024")


def _normalize_media_models(
    models: Mapping[str, Any],
    legacy_endpoint: Mapping[str, Any],
    keys: Mapping[str, Any],
    provider_profiles: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    paint_provider = models.get("paint_model_provider")
    if not paint_provider:
        paint_provider = _legacy_media_provider(
            provider_profiles,
            preferred_name="paint",
            base_url=legacy_endpoint.get("paint_base_url") or legacy_endpoint.get("openai_base_url", ""),
            api_key=keys.get("paint_api_key") or keys.get("openai_api_key", ""),
        )

    video_provider = models.get("video_model_provider")
    if not video_provider:
        video_provider = _legacy_media_provider(
            provider_profiles,
            preferred_name="video",
            base_url=legacy_endpoint.get("video_base_url", ""),
            api_key=keys.get("video_api_key") or os.getenv("ZENMUX_API_KEY", ""),
        )

    return {
        "paint": {
            "model": _pick(models, legacy_endpoint, "paint_model", ""),
            "provider": paint_provider,
            "size": _normalize_paint_size(models, legacy_endpoint),
            "quality": _pick(models, legacy_endpoint, "paint_quality", "auto"),
        },
        "video": {
            "model": _pick(models, legacy_endpoint, "video_model", "sora-2"),
            "provider": video_provider,
            "size": _pick(models, legacy_endpoint, "video_size", "1280x720"),
            "seconds": str(_pick(models, legacy_endpoint, "video_seconds", "8")),
        },
    }


def parse_config(config: Mapping[str, Any]) -> FrontierSettings:
    """解析 v2 配置；缺少新分区时从 v1 字段兼容迁移。"""
    if not isinstance(config, Mapping):
        raise TypeError("配置根节点必须是 TOML table")

    information = _section(config, "information")
    bot = _section(config, "bot")
    legacy_endpoint = _section(config, "endpoint")
    models = _section(config, "models")
    providers = _section(config, "providers")
    keys = _section(config, "key")
    legacy_function = _section(config, "function")
    features = _section(config, "features")
    agent = _section(config, "agent")
    dsh = _section(config, "dsh")
    agent_policy = _section(config, "agent_policy")
    auto_reply_policy = _section(config, "auto_reply_policy")
    paint_policy = _section(config, "paint_policy")
    limits = _section(config, "limits")
    legacy_message = _section(config, "message")
    notifications = _section(config, "notifications")
    legacy_database = _section(config, "database")
    legacy_image_memory = _section(config, "image_memory")
    storage = _section(config, "storage")

    config_version = config.get("config_version", 1)
    _validate_v2_model_provider_sections(config_version, models, providers, keys)
    legacy_profiles = _section(config, "llm_endpoints")
    provider_profiles, explicit_api_modes = _normalize_provider_profiles(
        providers,
        legacy_endpoint,
        keys,
        legacy_profiles,
    )
    model_roles = _normalize_model_roles(
        models,
        legacy_endpoint,
        legacy_profiles,
        provider_profiles,
        explicit_api_modes,
    )
    _validate_normalized_provider_protocols(provider_profiles)
    media_models = _normalize_media_models(models, legacy_endpoint, keys, provider_profiles)

    paint_enabled = _pick(features, legacy_function, "paint_enabled", True, "paint_module_enabled")
    normalized = {
        "config_version": config_version,
        "bot": {
            "system_prompt": _pick(bot, information, "system_prompt", ""),
        },
        "providers": provider_profiles,
        "models": {
            **model_roles,
            **media_models,
        },
        "keys": {
            name: keys.get(name, default)
            for name, default in (
                ("nasa_api_key", "DEMO_KEY"),
                ("github_pat", ""),
            )
        },
        "features": {
            "agent_enabled": _pick(features, legacy_function, "agent_enabled", True, "agent_module_enabled"),
            "paint_enabled": paint_enabled,
            "video_enabled": _pick(
                features,
                legacy_function,
                "video_enabled",
                paint_enabled,
                "video_module_enabled",
            ),
        },
        "agent": {"reasoning_effort": _pick(agent, legacy_function, "reasoning_effort", "medium", "agent_capability")},
        "dsh": {
            "provider": dsh.get("provider", "deepseek"),
            "model": dsh.get("model", "deepseek-v4-flash"),
            "max_tokens": dsh.get("max_tokens", 49_152),
        },
        "agent_policy": {
            field: _pick(agent_policy, legacy_function, field, default, f"agent_{field}")
            for field, default in (
                ("whitelist_mode", False),
                ("whitelist_person_list", []),
                ("whitelist_group_list", []),
                ("blacklist_person_list", []),
                ("blacklist_group_list", []),
            )
        },
        "auto_reply_policy": {
            field: _pick(
                auto_reply_policy,
                legacy_function,
                field,
                default,
                f"agent_auto_reply_{field}",
            )
            for field, default in (
                ("whitelist_mode", False),
                ("whitelist_group_list", []),
                ("blacklist_group_list", []),
            )
        },
        "paint_policy": {
            field: _pick(paint_policy, legacy_function, field, default, f"paint_{field}")
            for field, default in (
                ("whitelist_mode", False),
                ("whitelist_person_list", []),
                ("whitelist_group_list", []),
                ("blacklist_person_list", []),
                ("blacklist_group_list", []),
            )
        },
        "limits": {
            field: _pick(limits, legacy_function, field, default)
            for field, default in (
                ("paint_rate_limit_max_requests", 3),
                ("paint_rate_limit_window_seconds", 600),
                ("video_rate_limit_max_requests", 1),
                ("video_rate_limit_window_seconds", 900),
                ("video_poll_interval_seconds", 15),
                ("video_poll_timeout_seconds", 900),
                ("agent_llm_timeout_seconds", 900),
                ("agent_job_timeout_seconds", 3600),
            )
        },
        "notifications": {
            field: _pick(notifications, legacy_message, field, []) for field in NotificationConfig.model_fields
        },
        "storage": {
            "query_message_numbers": _pick(storage, legacy_database, "query_message_numbers", 100),
            "image_enabled": _pick(storage, legacy_image_memory, "image_enabled", True, "enabled"),
            "image_ttl_days": _pick(storage, legacy_image_memory, "image_ttl_days", 30, "ttl_days"),
            "media_ttl_days": _pick(
                storage,
                legacy_image_memory,
                "media_ttl_days",
                _pick(storage, legacy_image_memory, "image_ttl_days", 30, "ttl_days"),
            ),
            "max_inline_images": _pick(storage, legacy_image_memory, "max_inline_images", 4),
            "max_inline_media_bytes": _pick(
                storage,
                legacy_image_memory,
                "max_inline_media_bytes",
                20 * 1024 * 1024,
            ),
            "image_auto_cleanup": _pick(storage, legacy_image_memory, "image_auto_cleanup", True, "auto_cleanup"),
        },
        "debug": _section(config, "debug"),
        "dashboard": _section(config, "dashboard"),
        "content_check": _section(config, "content_check"),
    }
    return FrontierSettings.model_validate(normalized)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _runtime_dashboard_secret(configured: str) -> str:
    if configured and configured != _DEFAULT_DASHBOARD_JWT_SECRET:
        return configured

    cache_dir = Path.cwd() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    secret_path = cache_dir / ".runtime_jwt_secret"
    if secret_path.exists():
        cached = secret_path.read_text(encoding="utf-8").strip()
        if cached:
            return cached

    generated = secrets.token_hex(32)
    descriptor = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write(generated)
    return generated


def _provider_profiles(settings: FrontierSettings) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for name, profile in settings.providers.items():
        profiles[name] = profile.model_dump()
    return profiles


class EnvConfig:
    """兼容现有调用点的配置门面；内部由不可变、已验证快照驱动。"""

    settings: ClassVar[FrontierSettings]

    # Bot identity
    BOT_NAME: ClassVar[str]
    BOT_NICKNAMES: ClassVar[list[str]]
    SYSTEM_PROMPT: ClassVar[str]

    # Model roles and provider profiles
    BASIC_MODEL: ClassVar[str]
    BASIC_MODEL_PROVIDER: ClassVar[str]
    BASIC_MODEL_CAPABILITIES: ClassVar[list[str]]
    SIGNAL_MODEL: ClassVar[str]
    SIGNAL_MODEL_PROVIDER: ClassVar[str]
    SIGNAL_MODEL_CAPABILITIES: ClassVar[list[str]]
    ADVAN_MODEL: ClassVar[str]
    ADVAN_MODEL_PROVIDER: ClassVar[str]
    ADVAN_MODEL_CAPABILITIES: ClassVar[list[str]]
    DAILY_NEWS_MODEL: ClassVar[str]
    DAILY_NEWS_MODEL_PROVIDER: ClassVar[str]
    DAILY_NEWS_MODEL_CAPABILITIES: ClassVar[list[str]]
    PAINT_MODEL: ClassVar[str]
    PAINT_MODEL_PROVIDER: ClassVar[str]
    PAINT_SIZE: ClassVar[str]
    PAINT_QUALITY: ClassVar[str]
    VIDEO_MODEL: ClassVar[str]
    VIDEO_MODEL_PROVIDER: ClassVar[str]
    VIDEO_SIZE: ClassVar[str]
    VIDEO_SECONDS: ClassVar[str]
    LLM_PROVIDERS: ClassVar[dict[str, dict[str, Any]]]

    # External credentials
    NASA_API_KEY: ClassVar[SecretStr]
    GITHUB_PAT: ClassVar[SecretStr]

    # Feature switches and agent settings
    AGENT_MODULE_ENABLED: ClassVar[bool]
    PAINT_MODULE_ENABLED: ClassVar[bool]
    VIDEO_MODULE_ENABLED: ClassVar[bool]
    AGENT_CAPABILITY: ClassVar[str]
    DSH_MODEL_PROVIDER: ClassVar[str]
    DSH_MODEL: ClassVar[str]
    DSH_MAX_TOKENS: ClassVar[int]

    # Access policies
    AGENT_WHITELIST_MODE: ClassVar[bool]
    AGENT_WHITELIST_PERSON_LIST: ClassVar[list[int | str]]
    AGENT_WHITELIST_GROUP_LIST: ClassVar[list[int | str]]
    AGENT_BLACKLIST_PERSON_LIST: ClassVar[list[int | str]]
    AGENT_BLACKLIST_GROUP_LIST: ClassVar[list[int | str]]
    AGENT_AUTO_REPLY_WHITELIST_MODE: ClassVar[bool]
    AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST: ClassVar[list[int | str]]
    AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST: ClassVar[list[int | str]]
    PAINT_WHITELIST_MODE: ClassVar[bool]
    PAINT_WHITELIST_PERSON_LIST: ClassVar[list[int | str]]
    PAINT_WHITELIST_GROUP_LIST: ClassVar[list[int | str]]
    PAINT_BLACKLIST_PERSON_LIST: ClassVar[list[int | str]]
    PAINT_BLACKLIST_GROUP_LIST: ClassVar[list[int | str]]

    # Rate limits and timeouts
    PAINT_RATE_LIMIT_MAX_REQUESTS: ClassVar[int]
    PAINT_RATE_LIMIT_WINDOW_SECONDS: ClassVar[int]
    VIDEO_RATE_LIMIT_MAX_REQUESTS: ClassVar[int]
    VIDEO_RATE_LIMIT_WINDOW_SECONDS: ClassVar[int]
    VIDEO_POLL_INTERVAL_SECONDS: ClassVar[int]
    VIDEO_POLL_TIMEOUT_SECONDS: ClassVar[int]
    AGENT_LLM_TIMEOUT_SECONDS: ClassVar[int]
    AGENT_JOB_TIMEOUT_SECONDS: ClassVar[int]

    # Notification targets
    TEST_GROUP_ID: ClassVar[list[int | str]]
    ANNOUNCE_GROUP_ID: ClassVar[list[int | str]]
    APOD_GROUP_ID: ClassVar[list[int | str]]
    EARTH_NOW_GROUP_ID: ClassVar[list[int | str]]
    NEWS_SUMMARY_GROUP_ID: ClassVar[list[int | str]]
    EARTHQUAKE_GROUP_ID: ClassVar[list[int | str]]
    NRC_MERCHANT_GROUP_ID: ClassVar[list[int | str]]

    # Storage, diagnostics, and dashboard
    QUERY_MESSAGE_NUMBERS: ClassVar[int]
    IMAGE_ENABLED: ClassVar[bool]
    IMAGE_TTL_DAYS: ClassVar[int]
    MEDIA_TTL_DAYS: ClassVar[int]
    MAX_INLINE_IMAGES: ClassVar[int]
    MAX_INLINE_MEDIA_BYTES: ClassVar[int]
    IMAGE_AUTO_CLEANUP: ClassVar[bool]
    AGENT_DEBUG_MODE: ClassVar[bool]
    DASHBOARD_PASSWORD: ClassVar[str]
    DASHBOARD_JWT_SECRET: ClassVar[str]
    DASHBOARD_JWT_EXPIRE_HOURS: ClassVar[int]
    CONTENT_CHECK_ENABLED: ClassVar[bool]

    @classmethod
    def reload(cls, config: Mapping[str, Any], *, warn: bool = False) -> None:
        settings = parse_config(config)
        nicknames = load_nicknames()
        model = settings.models
        keys = settings.keys
        providers = _provider_profiles(settings)
        values: dict[str, Any] = {
            "BOT_NAME": nicknames[0],
            "BOT_NICKNAMES": list(nicknames),
            "SYSTEM_PROMPT": settings.bot.system_prompt,
            "BASIC_MODEL": model.basic.model,
            "BASIC_MODEL_PROVIDER": model.basic.provider,
            "BASIC_MODEL_CAPABILITIES": list(model.basic.capabilities),
            "SIGNAL_MODEL": model.signal.model,
            "SIGNAL_MODEL_PROVIDER": model.signal.provider,
            "SIGNAL_MODEL_CAPABILITIES": list(model.signal.capabilities),
            "ADVAN_MODEL": model.advanced.model,
            "ADVAN_MODEL_PROVIDER": model.advanced.provider,
            "ADVAN_MODEL_CAPABILITIES": list(model.advanced.capabilities),
            "DAILY_NEWS_MODEL": model.daily_news.model,
            "DAILY_NEWS_MODEL_PROVIDER": model.daily_news.provider,
            "DAILY_NEWS_MODEL_CAPABILITIES": list(model.daily_news.capabilities),
            "PAINT_MODEL": model.paint.model,
            "PAINT_MODEL_PROVIDER": model.paint.provider,
            "PAINT_SIZE": model.paint.size,
            "PAINT_QUALITY": model.paint.quality,
            "VIDEO_MODEL": model.video.model,
            "VIDEO_MODEL_PROVIDER": model.video.provider,
            "VIDEO_SIZE": model.video.size,
            "VIDEO_SECONDS": model.video.seconds,
            "LLM_PROVIDERS": providers,
            "NASA_API_KEY": keys.nasa_api_key,
            "GITHUB_PAT": keys.github_pat,
            "AGENT_MODULE_ENABLED": settings.features.agent_enabled,
            "PAINT_MODULE_ENABLED": settings.features.paint_enabled,
            "VIDEO_MODULE_ENABLED": settings.features.video_enabled,
            "AGENT_CAPABILITY": settings.agent.reasoning_effort,
            "DSH_MODEL_PROVIDER": settings.dsh.provider,
            "DSH_MODEL": settings.dsh.model,
            "DSH_MAX_TOKENS": settings.dsh.max_tokens,
            "AGENT_WHITELIST_MODE": settings.agent_policy.whitelist_mode,
            "AGENT_WHITELIST_PERSON_LIST": list(settings.agent_policy.whitelist_person_list),
            "AGENT_WHITELIST_GROUP_LIST": list(settings.agent_policy.whitelist_group_list),
            "AGENT_BLACKLIST_PERSON_LIST": list(settings.agent_policy.blacklist_person_list),
            "AGENT_BLACKLIST_GROUP_LIST": list(settings.agent_policy.blacklist_group_list),
            "AGENT_AUTO_REPLY_WHITELIST_MODE": settings.auto_reply_policy.whitelist_mode,
            "AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST": list(settings.auto_reply_policy.whitelist_group_list),
            "AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST": list(settings.auto_reply_policy.blacklist_group_list),
            "PAINT_WHITELIST_MODE": settings.paint_policy.whitelist_mode,
            "PAINT_WHITELIST_PERSON_LIST": list(settings.paint_policy.whitelist_person_list),
            "PAINT_WHITELIST_GROUP_LIST": list(settings.paint_policy.whitelist_group_list),
            "PAINT_BLACKLIST_PERSON_LIST": list(settings.paint_policy.blacklist_person_list),
            "PAINT_BLACKLIST_GROUP_LIST": list(settings.paint_policy.blacklist_group_list),
            "ANNOUNCE_GROUP_ID": list(settings.notifications.announce_group_id),
            "APOD_GROUP_ID": list(settings.notifications.apod_group_id),
            "EARTH_NOW_GROUP_ID": list(settings.notifications.earth_now_group_id),
            "NEWS_SUMMARY_GROUP_ID": list(settings.notifications.news_summary_group_id),
            "EARTHQUAKE_GROUP_ID": list(settings.notifications.earthquake_group_id),
            "NRC_MERCHANT_GROUP_ID": list(settings.notifications.nrc_merchant_group_id),
            "TEST_GROUP_ID": list(settings.notifications.test_group_id),
            "QUERY_MESSAGE_NUMBERS": settings.storage.query_message_numbers,
            "IMAGE_ENABLED": settings.storage.image_enabled,
            "IMAGE_TTL_DAYS": settings.storage.image_ttl_days,
            "MEDIA_TTL_DAYS": settings.storage.media_ttl_days,
            "MAX_INLINE_IMAGES": settings.storage.max_inline_images,
            "MAX_INLINE_MEDIA_BYTES": settings.storage.max_inline_media_bytes,
            "IMAGE_AUTO_CLEANUP": settings.storage.image_auto_cleanup,
            "AGENT_DEBUG_MODE": settings.debug.agent_debug_mode,
            "DASHBOARD_PASSWORD": settings.dashboard.password,
            "DASHBOARD_JWT_SECRET": _runtime_dashboard_secret(settings.dashboard.jwt_secret),
            "DASHBOARD_JWT_EXPIRE_HOURS": settings.dashboard.jwt_expire_hours,
            "CONTENT_CHECK_ENABLED": settings.content_check.enabled,
        }
        for field in LimitConfig.model_fields:
            values[field.upper()] = getattr(settings.limits, field)

        # 解析和所有派生值计算成功后再统一替换，避免半更新状态。
        for name, value in values.items():
            setattr(cls, name, value)
        cls.settings = settings

        if warn and settings.dashboard.password == "admin":  # noqa: S105
            print(
                '⚠️  Dashboard 密码仍为默认值 "admin"，请在 env.toml 的 [dashboard] 中修改。',
                file=sys.stderr,
            )
        if warn and settings.dashboard.jwt_secret == _DEFAULT_DASHBOARD_JWT_SECRET:
            print(
                "⚠️  Dashboard JWT secret 未配置，已生成仅保存在 cache 中的运行时密钥。",
                file=sys.stderr,
            )
        if warn and settings.config_version < CONFIG_VERSION:
            print(
                "⚠️  当前 env.toml 使用旧版配置结构；仍可正常运行，建议按 env.toml.example 渐进迁移。",
                file=sys.stderr,
            )


def get_provider_profile(name: str) -> dict[str, Any]:
    profile = EnvConfig.LLM_PROVIDERS.get(name)
    if profile is None:
        raise ValueError(f"未知 provider profile: {name!r}")
    if not isinstance(profile, dict):
        raise ValueError(f"provider profile 必须是表格: {name!r}")
    return profile


EnvConfig.reload(load_config(), warn=True)
