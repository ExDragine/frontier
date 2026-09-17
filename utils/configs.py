from __future__ import annotations

import json
import os
import secrets
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Literal

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
            model="deepseek-flash",
            provider="deepseek",
            capabilities=("text",),
        )
    )
    advanced: ModelConfig = Field(default_factory=ModelConfig)
    daily_news: ModelConfig = Field(
        default_factory=lambda: ModelConfig(
            model="deepseek-flash",
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
    native_web_search: bool = False
    structured_output_method: Literal["auto", "json_schema", "function_calling", "json_mode", "text_json"] = "auto"
    signal_extra_body: dict[str, Any] = Field(default_factory=dict)


class KeyConfig(_FrozenConfig):
    nasa_api_key: SecretStr = Field(default_factory=lambda: SecretStr("DEMO_KEY"))
    github_pat: SecretStr = Field(default_factory=lambda: SecretStr(""))


class FeatureConfig(_FrozenConfig):
    agent_enabled: bool = True
    paint_enabled: bool = True
    video_enabled: bool = True


class AgentConfig(_FrozenConfig):
    reasoning_effort: str = "medium"


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
    agent_model_call_limit: int = Field(default=20, ge=1)
    agent_tool_call_limit: int = Field(default=40, ge=1)
    agent_ptc_call_limit: int = Field(default=20, ge=1)


class SessionConfig(_FrozenConfig):
    enabled: bool = False
    group_idle_seconds: int = Field(default=1800, ge=1)
    private_idle_seconds: int = Field(default=7200, ge=1)
    max_sessions: int = Field(default=128, ge=1)
    max_generation_turns: int = Field(default=30, ge=1)
    max_session_bytes: int = Field(default=64 * 1024 * 1024, ge=1024)
    max_total_bytes: int = Field(default=256 * 1024 * 1024, ge=1024)
    history_max_tokens: int = Field(default=32000, ge=1)
    history_window_fraction: float = Field(default=0.25, gt=0, le=1)
    cleanup_interval_seconds: int = Field(default=60, ge=1)


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
    config_version: int = Field(default=CONFIG_VERSION, ge=CONFIG_VERSION, le=CONFIG_VERSION)
    bot: BotConfig = Field(default_factory=BotConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    providers: dict[str, ProviderProfile] = Field(default_factory=dict)
    keys: KeyConfig = Field(default_factory=KeyConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    agent_policy: AccessPolicy = Field(default_factory=AccessPolicy)
    auto_reply_policy: AutoReplyPolicy = Field(default_factory=AutoReplyPolicy)
    paint_policy: AccessPolicy = Field(default_factory=AccessPolicy)
    limits: LimitConfig = Field(default_factory=LimitConfig)
    sessions: SessionConfig = Field(default_factory=SessionConfig)
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


def _validate_model_provider_sections(
    models: Mapping[str, Any],
    providers: Mapping[str, Any],
    keys: Mapping[str, Any],
) -> None:
    removed_model_fields = sorted(
        key
        for key in models
        if key.endswith(("_model_endpoint", "_model_use_responses_api"))
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
        removed = {"provider", "use_responses_api"} & raw_profile.keys()
        if removed:
            raise ValueError(
                f"[providers.{name}] 不再接受 {', '.join(sorted(removed))}，请使用 type 和 api_mode"
            )


def _default_api_mode(provider_type: str) -> str:
    return {
        "openai": _API_MODE_CHAT_COMPLETIONS,
        "google": _API_MODE_GENERATE_CONTENT,
        "anthropic": _API_MODE_MESSAGES,
        "deepseek": _API_MODE_CHAT_COMPLETIONS,
    }.get(provider_type, "")


def _validate_normalized_provider_protocols(provider_profiles: dict[str, dict[str, Any]]) -> None:
    for name, profile in provider_profiles.items():
        provider_type = str(profile.get("type", "")).strip().lower()
        api_mode = str(profile.get("api_mode", "")).strip().lower()
        profile["type"] = provider_type
        profile["api_mode"] = api_mode
        supported_modes = _PROVIDER_API_MODES.get(provider_type)
        if supported_modes is None:
            raise ValueError(f"[providers.{name}].type 无效: {provider_type!r}")
        if api_mode not in supported_modes:
            raise ValueError(
                f"[providers.{name}] 的 type={provider_type!r} 不支持 api_mode={api_mode!r}"
            )


def _normalize_provider_profile(
    raw_profile: Mapping[str, Any],
    existing: Mapping[str, Any],
) -> dict[str, Any]:
    profile = dict(raw_profile)
    provider_type = str(profile.get("type", existing.get("type", ""))).strip().lower()
    profile["type"] = provider_type
    if "api_mode" not in profile:
        profile["api_mode"] = (
            existing["api_mode"]
            if existing and provider_type == existing.get("type")
            else _default_api_mode(provider_type)
        )
    return {**existing, **profile}


def _normalize_provider_profiles(providers: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {
        "openai": {"type": "openai", "api_mode": _API_MODE_RESPONSES},
        "google": {"type": "google", "api_mode": _API_MODE_GENERATE_CONTENT},
        "anthropic": {"type": "anthropic", "api_mode": _API_MODE_MESSAGES},
        "deepseek": {"type": "deepseek", "api_mode": _API_MODE_CHAT_COMPLETIONS},
        "deepseek_responses": {
            "type": "openai",
            "api_mode": _API_MODE_RESPONSES,
            "base_url": _DEEPSEEK_RESPONSES_BASE_URL,
        },
        "deepseek_anthropic": {
            "type": "anthropic",
            "api_mode": _API_MODE_MESSAGES,
            "base_url": _DEEPSEEK_ANTHROPIC_BASE_URL,
        },
    }
    for name, raw_profile in providers.items():
        profiles[name] = _normalize_provider_profile(raw_profile, profiles.get(name, {}))
    _validate_normalized_provider_protocols(profiles)
    return profiles


def _normalize_models(models: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Map current flat TOML model fields onto typed model roles."""
    defaults = ModelsConfig()
    normalized = {}
    known_fields = set()
    for role in ModelsConfig.model_fields:
        model = getattr(defaults, role)
        values = {}
        for field in type(model).model_fields:
            suffix = {
                "model": "model",
                "provider": "model_provider",
                "capabilities": "model_capabilities",
            }.get(field, field)
            key = f"{role}_{suffix}"
            known_fields.add(key)
            values[field] = models.get(key, getattr(model, field))
        normalized[role] = values
    unknown = models.keys() - known_fields
    if unknown:
        raise ValueError("[models] 不支持的字段: " + ", ".join(sorted(unknown)))
    return normalized


def parse_config(config: Mapping[str, Any]) -> FrontierSettings:
    """Validate the current configuration without converting older formats."""
    if not isinstance(config, Mapping):
        raise TypeError("配置根节点必须是 TOML table")
    version = config.get("config_version")
    if type(version) is not int or version != CONFIG_VERSION:
        raise ValueError(f"仅支持 config_version = {CONFIG_VERSION}，请按 env.toml.example 更新配置")

    retired_sections = {
        "information", "endpoint", "llm_endpoints", "function", "message", "database", "image_memory", "memory",
    } & config.keys()
    if retired_sections:
        raise ValueError("不支持的配置段，请按 env.toml.example 更新配置: " + ", ".join(sorted(retired_sections)))

    models = _section(config, "models")
    providers = _section(config, "providers")
    keys = _section(config, "key")
    _validate_model_provider_sections(models, providers, keys)
    normalized = {
        key: _section(config, key)
        for key in FrontierSettings.model_fields
        if key not in {"config_version", "models", "providers", "keys"}
    }
    # Preserve the documented defaults for omitted current-format fields.
    normalized["features"].setdefault("video_enabled", normalized["features"].get("paint_enabled", True))
    normalized["storage"].setdefault("media_ttl_days", normalized["storage"].get("image_ttl_days", 30))
    return FrontierSettings.model_validate({
        **normalized,
        "config_version": version,
        "models": _normalize_models(models),
        "providers": _normalize_provider_profiles(providers),
        "keys": keys,
    })


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
    AGENT_MODEL_CALL_LIMIT: ClassVar[int]
    AGENT_TOOL_CALL_LIMIT: ClassVar[int]
    AGENT_PTC_CALL_LIMIT: ClassVar[int]
    SESSIONS: ClassVar[SessionConfig]

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

    REVISION: ClassVar[int] = 0

    @classmethod
    def reload(cls, config: Mapping[str, Any], *, warn: bool = False) -> None:
        settings = parse_config(config)
        nicknames = load_nicknames()
        model = settings.models
        keys = settings.keys
        providers = _provider_profiles(settings)
        values: dict[str, Any] = {
            "SESSIONS": settings.sessions,
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
        cls.REVISION += 1

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


def get_provider_profile(name: str) -> dict[str, Any]:
    profile = EnvConfig.LLM_PROVIDERS.get(name)
    if profile is None:
        raise ValueError(f"未知 provider profile: {name!r}")
    if not isinstance(profile, dict):
        raise ValueError(f"provider profile 必须是表格: {name!r}")
    return profile


EnvConfig.reload(load_config(), warn=True)
