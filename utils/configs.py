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
    base_url: str = ""


class PaintModelConfig(MediaModelConfig):
    aspect_ratio: str = "1:1"
    image_size: str = "1K"


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
    paint: PaintModelConfig = Field(default_factory=PaintModelConfig)
    video: MediaModelConfig = Field(
        default_factory=lambda: MediaModelConfig(
            model="alibaba/happyhorse-1.0",
            base_url="https://zenmux.ai/api/vertex-ai",
        )
    )


class ProviderProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    type: str = ""
    base_url: str = ""
    api_key: str = ""
    use_responses_api: bool = False


class KeyConfig(_FrozenConfig):
    openai_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    paint_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    video_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    google_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    anthropic_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    deepseek_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
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
) -> None:
    if not isinstance(config_version, int) or config_version < 2:
        return
    removed_model_fields = sorted(
        key for key in models if key.endswith("_model_endpoint") or key.endswith("_model_use_responses_api")
    )
    if removed_model_fields:
        raise ValueError(
            "[models] 不再接受 endpoint 或 use_responses_api，请将 API 模式配置到 [providers.<name>]: "
            + ", ".join(removed_model_fields)
        )
    for name, raw_profile in providers.items():
        if not isinstance(raw_profile, Mapping):
            raise ValueError(f"[providers.{name}] 必须是供应商 table")
        if "capabilities" in raw_profile:
            raise ValueError(f"[providers.{name}] 不再接受 capabilities，请配置到对应模型")


def _normalize_provider_profiles(
    providers: Mapping[str, Any],
    legacy_endpoint: Mapping[str, Any],
    keys: Mapping[str, Any],
    legacy_profiles: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    profiles: dict[str, dict[str, Any]] = {
        "openai": {
            "type": "openai",
            "base_url": _pick(providers, legacy_endpoint, "openai_base_url", ""),
            "use_responses_api": True,
        },
        "google": {"type": "google", "base_url": "", "use_responses_api": False},
        "anthropic": {
            "type": "anthropic",
            "base_url": _pick(providers, keys, "anthropic_base_url", ""),
            "use_responses_api": False,
        },
        "deepseek": {
            "type": "deepseek",
            "base_url": _pick(providers, keys, "deepseek_base_url", "", "deepseek_api_base"),
            "use_responses_api": False,
        },
    }
    explicit_responses: set[str] = set()
    for name, raw_profile in providers.items():
        if not isinstance(raw_profile, Mapping):
            continue
        profile = dict(raw_profile)
        if "use_responses_api" in profile:
            explicit_responses.add(name)
        profile["type"] = profile.pop("provider", profile.get("type", name if name in profiles else ""))
        profile.pop("capabilities", None)
        profiles[name] = {**profiles.get(name, {}), **profile}

    for name, raw_profile in legacy_profiles.items():
        if not isinstance(raw_profile, Mapping) or name in profiles:
            continue
        profile = dict(raw_profile)
        if "use_responses_api" in profile:
            explicit_responses.add(name)
        provider_type = profile.get("type") or profile.get("provider", "")
        profiles[name] = {
            "type": provider_type,
            "base_url": profile.get("base_url", ""),
            "api_key": profile.get("api_key", ""),
            "use_responses_api": profile.get("use_responses_api", provider_type == "openai"),
        }
    return profiles, explicit_responses


def _normalize_model_roles(
    models: Mapping[str, Any],
    legacy_endpoint: Mapping[str, Any],
    legacy_profiles: Mapping[str, Any],
    provider_profiles: dict[str, dict[str, Any]],
    explicit_responses: set[str],
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
        if provider_ref and response_explicit and provider_ref not in explicit_responses:
            provider_profiles.setdefault(
                provider_ref,
                {
                    "type": provider_name or provider_ref,
                    "base_url": "",
                    "use_responses_api": bool(response_value),
                },
            )["use_responses_api"] = bool(response_value)
        return {
            "model": role_value("model", default_model),
            "provider": provider_ref,
            "capabilities": capabilities,
        }

    return {
        "basic": model_role("basic", "basic", ("", "", [], True)),
        "signal": model_role("signal", "signal", ("deepseek-v4-flash", "deepseek", ["text"], False)),
        "advanced": model_role("advanced", "advan", ("", "", [], True)),
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
    _validate_v2_model_provider_sections(config_version, models, providers)
    legacy_profiles = _section(config, "llm_endpoints")
    provider_profiles, explicit_responses = _normalize_provider_profiles(
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
        explicit_responses,
    )

    paint_enabled = _pick(features, legacy_function, "paint_enabled", True, "paint_module_enabled")
    normalized = {
        "config_version": config_version,
        "bot": {
            "system_prompt": _pick(bot, information, "system_prompt", ""),
        },
        "providers": provider_profiles,
        "models": {
            **model_roles,
            "paint": {
                "model": _pick(models, legacy_endpoint, "paint_model", ""),
                "base_url": _pick(models, legacy_endpoint, "paint_base_url", ""),
                "aspect_ratio": _pick(models, legacy_endpoint, "paint_aspect_ratio", "1:1"),
                "image_size": _pick(models, legacy_endpoint, "paint_image_size", "1K"),
            },
            "video": {
                "model": _pick(models, legacy_endpoint, "video_model", "alibaba/happyhorse-1.0"),
                "base_url": _pick(
                    models,
                    legacy_endpoint,
                    "video_base_url",
                    "https://zenmux.ai/api/vertex-ai",
                ),
            },
        },
        "keys": {
            name: keys.get(name, default)
            for name, default in (
                ("openai_api_key", ""),
                ("paint_api_key", ""),
                ("video_api_key", os.getenv("ZENMUX_API_KEY", "")),
                ("google_api_key", ""),
                ("anthropic_api_key", ""),
                ("deepseek_api_key", ""),
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

    @classmethod
    def reload(cls, config: Mapping[str, Any], *, warn: bool = False) -> None:
        settings = parse_config(config)
        nicknames = load_nicknames()
        model = settings.models
        keys = settings.keys
        providers = _provider_profiles(settings)
        openai_base_url = providers.get("openai", {}).get("base_url", "")
        values: dict[str, Any] = {
            "BOT_NAME": nicknames[0],
            "BOT_NICKNAMES": list(nicknames),
            "SYSTEM_PROMPT": settings.bot.system_prompt,
            "OPENAI_BASE_URL": openai_base_url,
            "BASIC_MODEL": model.basic.model,
            "BASIC_MODEL_PROVIDER": model.basic.provider,
            "BASIC_MODEL_CAPABILITIES": list(model.basic.capabilities),
            "SIGNAL_MODEL": model.signal.model,
            "SIGNAL_MODEL_PROVIDER": model.signal.provider,
            "SIGNAL_MODEL_CAPABILITIES": list(model.signal.capabilities),
            "ADVAN_MODEL": model.advanced.model,
            "ADVAN_MODEL_PROVIDER": model.advanced.provider,
            "ADVAN_MODEL_CAPABILITIES": list(model.advanced.capabilities),
            "PAINT_MODEL": model.paint.model,
            "PAINT_BASE_URL": model.paint.base_url or openai_base_url,
            "PAINT_ASPECT_RATIO": model.paint.aspect_ratio,
            "PAINT_IMAGE_SIZE": model.paint.image_size,
            "VIDEO_MODEL": model.video.model,
            "VIDEO_BASE_URL": model.video.base_url,
            "LLM_PROVIDERS": providers,
            "OPENAI_API_KEY": keys.openai_api_key,
            "PAINT_API_KEY": SecretStr(
                keys.paint_api_key.get_secret_value() or keys.openai_api_key.get_secret_value()
            ),
            "VIDEO_API_KEY": keys.video_api_key,
            "GOOGLE_API_KEY": keys.google_api_key,
            "ANTHROPIC_API_KEY": keys.anthropic_api_key,
            "ANTHROPIC_BASE_URL": providers.get("anthropic", {}).get("base_url", ""),
            "DEEPSEEK_API_KEY": keys.deepseek_api_key,
            "DEEPSEEK_API_BASE": providers.get("deepseek", {}).get("base_url", ""),
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


EnvConfig.reload(load_config(), warn=True)
