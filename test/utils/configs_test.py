# ruff: noqa: S101, S105

import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_env_config_defaults(monkeypatch):
    from utils.configs import EnvConfig

    monkeypatch.setenv("ZENMUX_API_KEY", "unused-old-key")
    EnvConfig.reload({"config_version": 2})
    assert EnvConfig.settings.config_version == 2
    assert EnvConfig.BASIC_MODEL_PROVIDER == ""
    assert EnvConfig.BASIC_MODEL_CAPABILITIES == []
    assert EnvConfig.ADVAN_MODEL_PROVIDER == ""
    assert EnvConfig.SIGNAL_MODEL == "deepseek-v4-flash"
    assert EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek"
    assert EnvConfig.SIGNAL_MODEL_CAPABILITIES == ["text"]
    assert EnvConfig.DAILY_NEWS_MODEL_PROVIDER == "deepseek_responses"
    assert EnvConfig.LLM_PROVIDERS["openai"]["api_mode"] == "responses"
    assert EnvConfig.LLM_PROVIDERS["deepseek"]["type"] == "deepseek"
    assert EnvConfig.LLM_PROVIDERS["deepseek_responses"]["type"] == "openai"
    assert EnvConfig.LLM_PROVIDERS["deepseek_responses"]["base_url"] == "https://api.deepseek.com"
    assert EnvConfig.LLM_PROVIDERS["deepseek_anthropic"]["api_mode"] == "messages"
    assert EnvConfig.PAINT_MODEL_PROVIDER == EnvConfig.VIDEO_MODEL_PROVIDER == "openai"
    assert EnvConfig.LLM_PROVIDERS["openai"]["api_key"] == ""
    assert "paint" not in EnvConfig.LLM_PROVIDERS
    assert "video" not in EnvConfig.LLM_PROVIDERS
    assert EnvConfig.VIDEO_MODEL == "sora-2"
    assert EnvConfig.PAINT_SIZE == "1024x1024"
    assert EnvConfig.PAINT_QUALITY == "auto"
    assert EnvConfig.VIDEO_SIZE == "1280x720"
    assert EnvConfig.VIDEO_SECONDS == "8"
    assert EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 1
    assert EnvConfig.MEDIA_TTL_DAYS == EnvConfig.IMAGE_TTL_DAYS == 30
    assert EnvConfig.MAX_INLINE_IMAGES == 4
    assert EnvConfig.MAX_INLINE_MEDIA_BYTES == 20 * 1024 * 1024
    assert EnvConfig.CONTENT_CHECK_ENABLED is False
    assert EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE is False


def test_env_config_reload_updates_runtime_sections():
    from utils.configs import EnvConfig

    before = EnvConfig.REVISION
    EnvConfig.reload({
        "config_version": 2,
        "auto_reply_policy": {
            "whitelist_mode": True,
            "whitelist_group_list": [1001],
            "blacklist_group_list": [1002],
        },
        "storage": {"image_enabled": False, "image_ttl_days": 9, "image_auto_cleanup": False},
        "content_check": {"enabled": True},
        "models": {"signal_model_provider": "deepseek_responses"},
    })
    assert EnvConfig.REVISION == before + 1
    assert EnvConfig.IMAGE_ENABLED is False
    assert EnvConfig.MEDIA_TTL_DAYS == EnvConfig.IMAGE_TTL_DAYS == 9
    assert EnvConfig.IMAGE_AUTO_CLEANUP is False
    assert EnvConfig.CONTENT_CHECK_ENABLED is True
    assert EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE is True
    assert EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST == [1001]
    assert EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST == [1002]
    assert EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek_responses"

    EnvConfig.reload({"config_version": 2})
    assert EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE is False
    assert EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST == []
    assert EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST == []
    assert EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek"


def test_media_models_use_explicit_profiles():
    from utils.configs import EnvConfig

    EnvConfig.reload({
        "config_version": 2,
        "models": {
            "paint_model": "paint",
            "paint_model_provider": "images",
            "paint_size": "2048x1152",
            "video_model": "custom-video",
            "video_model_provider": "videos",
        },
        "providers": {
            "images": {"type": "openai", "base_url": "https://paint.example.com", "api_key": "sk-paint"},
            "videos": {"type": "openai", "base_url": "https://video.example.com", "api_key": "sk-video"},
        },
        "features": {"video_enabled": False},
        "limits": {"video_rate_limit_max_requests": 2, "agent_llm_timeout_seconds": 1234},
    })
    assert EnvConfig.PAINT_SIZE == "2048x1152"
    assert EnvConfig.PAINT_MODEL_PROVIDER == "images"
    assert EnvConfig.LLM_PROVIDERS["images"]["api_key"] == "sk-paint"
    assert EnvConfig.LLM_PROVIDERS["images"]["api_mode"] == "chat_completions"
    assert EnvConfig.VIDEO_MODEL == "custom-video"
    assert EnvConfig.VIDEO_MODEL_PROVIDER == "videos"
    assert EnvConfig.LLM_PROVIDERS["videos"]["base_url"] == "https://video.example.com"
    assert EnvConfig.VIDEO_MODULE_ENABLED is False
    assert EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 2
    assert EnvConfig.AGENT_LLM_TIMEOUT_SECONDS == 1234


@pytest.mark.parametrize("version", [None, 1, 3, True, "2"])
def test_config_requires_current_version(version):
    from utils.configs import parse_config

    config = {} if version is None else {"config_version": version}
    with pytest.raises(ValueError, match="仅支持 config_version = 2"):
        parse_config(config)


@pytest.mark.parametrize("section", [
    "information", "endpoint", "llm_endpoints", "function", "message", "database", "image_memory", "memory",
])
def test_retired_config_sections_are_rejected_without_runtime_changes(section):
    from utils.configs import EnvConfig

    before = EnvConfig.settings, EnvConfig.REVISION
    config = {"config_version": 2, section: {}, "features": {"agent_enabled": False}}
    with pytest.raises(ValueError, match="不支持的配置段"):
        EnvConfig.reload(config)
    assert (EnvConfig.settings, EnvConfig.REVISION) == before
    assert config[section] == {}


@pytest.mark.parametrize("profile", [
    {"type": "deepseek_responses"},
    {"provider": "openai"},
    {"type": "openai", "use_responses_api": True},
    {"type": "openai", "api_mode": "responses", "use_responses_api": True},
    {"type": "deepseek", "use_responses_api": True},
])
def test_retired_provider_fields_are_rejected(profile):
    from utils.configs import parse_config

    with pytest.raises(ValueError):
        parse_config({"config_version": 2, "providers": {"retired": profile}})


@pytest.mark.parametrize("fields", [
    {"paint_image_size": "2K"},
    {"paint_aspect_ratio": "16:9"},
    {"basic_model_use_responses_api": True},
])
def test_retired_model_fields_are_rejected(fields):
    from utils.configs import parse_config

    with pytest.raises(ValueError):
        parse_config({"config_version": 2, "models": fields})


def test_v2_config_loads_new_sections_and_keeps_keys_in_toml(monkeypatch):
    from utils.configs import EnvConfig

    monkeypatch.setenv("NICKNAME", '["EnvBot", "小助手", "EnvBot", ""]')
    EnvConfig.reload(
        {
            "config_version": 2,
            "bot": {"system_prompt": "你是 {name}"},
            "models": {
                "basic_model": "gpt-5-mini",
                "basic_model_provider": "openai_chat",
                "signal_model": "gpt-5-nano",
                "signal_model_provider": "openai",
                "advanced_model": "gpt-5.4",
                "advanced_model_provider": "openai",
                "advanced_model_capabilities": ["text", "vision"],
                "daily_news_model": "deepseek-v4-pro",
                "daily_news_model_provider": "deepseek_responses",
                "daily_news_model_capabilities": ["text"],
                "paint_model": "gpt-image-1.5",
                "paint_model_provider": "openai",
                "paint_size": "1536x1024",
                "paint_quality": "high",
                "video_model": "sora-2",
                "video_model_provider": "openai",
                "video_size": "1280x720",
                "video_seconds": "12",
            },
            "providers": {
                "openai": {
                    "type": "openai",
                    "api_mode": "responses",
                    "native_web_search": True,
                    "base_url": "https://api.example.com/v1",
                    "api_key": "sk-v2",
                },
                "openai_chat": {
                    "type": "openai",
                    "api_mode": "chat_completions",
                    "base_url": "https://chat.example.com/v1",
                    "api_key": "sk-chat",
                },
                "google": {"type": "google", "base_url": "", "api_key": "google-v2"},
            },
            "key": {"nasa_api_key": "nasa-v2"},
            "features": {"agent_enabled": True, "paint_enabled": False, "video_enabled": False},
            "agent": {"reasoning_effort": "high"},
            "agent_policy": {"blacklist_group_list": [1001]},
            "auto_reply_policy": {"whitelist_mode": True, "whitelist_group_list": [1002]},
            "limits": {"agent_llm_timeout_seconds": 120},
            "notifications": {"earth_now_group_id": [1003]},
            "storage": {"query_message_numbers": 20, "image_enabled": False},
            "dashboard": {"password": "password", "jwt_secret": "v2-secret"},
        }
    )

    assert EnvConfig.BOT_NAME == "EnvBot"
    assert EnvConfig.BOT_NICKNAMES == ["EnvBot", "小助手"]
    assert EnvConfig.SYSTEM_PROMPT == "你是 {name}"
    assert EnvConfig.BASIC_MODEL == "gpt-5-mini"
    assert EnvConfig.BASIC_MODEL_PROVIDER == "openai_chat"
    assert EnvConfig.ADVAN_MODEL == "gpt-5.4"
    assert EnvConfig.ADVAN_MODEL_CAPABILITIES == ["text", "vision"]
    assert EnvConfig.DAILY_NEWS_MODEL == "deepseek-v4-pro"
    assert EnvConfig.DAILY_NEWS_MODEL_PROVIDER == "deepseek_responses"
    assert EnvConfig.LLM_PROVIDERS["openai_chat"]["api_mode"] == "chat_completions"
    assert EnvConfig.LLM_PROVIDERS["openai"]["api_mode"] == "responses"
    assert EnvConfig.LLM_PROVIDERS["openai"]["native_web_search"] is True
    assert EnvConfig.LLM_PROVIDERS["openai"]["api_key"] == "sk-v2"
    assert EnvConfig.PAINT_MODEL_PROVIDER == "openai"
    assert EnvConfig.PAINT_SIZE == "1536x1024"
    assert EnvConfig.PAINT_QUALITY == "high"
    assert EnvConfig.VIDEO_MODEL_PROVIDER == "openai"
    assert EnvConfig.VIDEO_SIZE == "1280x720"
    assert EnvConfig.VIDEO_SECONDS == "12"
    assert EnvConfig.AGENT_CAPABILITY == "high"
    assert EnvConfig.AGENT_BLACKLIST_GROUP_LIST == [1001]
    assert EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST == [1002]
    assert EnvConfig.AGENT_LLM_TIMEOUT_SECONDS == 120
    assert EnvConfig.EARTH_NOW_GROUP_ID == [1003]
    assert EnvConfig.QUERY_MESSAGE_NUMBERS == 20
    assert EnvConfig.IMAGE_ENABLED is False


def test_reload_validation_is_atomic():
    from utils.configs import EnvConfig

    before = (EnvConfig.BOT_NAME, EnvConfig.AGENT_LLM_TIMEOUT_SECONDS)
    with pytest.raises(ValidationError):
        EnvConfig.reload(
            {
                "config_version": 2,
                "bot": {"system_prompt": "ShouldNotApply"},
                "limits": {"agent_llm_timeout_seconds": 0},
            }
        )

    assert (EnvConfig.BOT_NAME, EnvConfig.AGENT_LLM_TIMEOUT_SECONDS) == before


def test_env_toml_example_is_valid_v2_config():
    from utils.configs import parse_config

    example_path = Path(__file__).resolve().parents[2] / "env.toml.example"
    with example_path.open("rb") as file:
        settings = parse_config(tomllib.load(file))

    assert settings.config_version == 2
    assert settings.providers["openai"].api_mode == "responses"
    assert settings.providers["deepseek"].type == "deepseek"
    assert settings.providers["deepseek"].api_mode == "chat_completions"
    assert settings.providers["deepseek_responses"].type == "openai"
    assert settings.providers["deepseek_responses"].base_url == "https://api.deepseek.com"
    assert settings.providers["deepseek_responses"].api_mode == "responses"
    assert settings.providers["deepseek_anthropic"].type == "anthropic"
    assert settings.providers["deepseek_anthropic"].api_mode == "messages"
    assert settings.models.advanced.provider == "openai"
    assert settings.models.daily_news.model == "deepseek-v4-flash"
    assert settings.models.daily_news.provider == "deepseek_responses"
    assert settings.models.paint.provider == "openai"
    assert settings.models.paint.size == "1024x1024"
    assert settings.models.video.provider == "openai"
    assert settings.models.video.model == "sora-2"


@pytest.mark.parametrize(
    "config, message",
    [
        (
            {"config_version": 2, "models": {"basic_model_endpoint": "openrouter"}},
            "不再接受 endpoint",
        ),
        (
            {
                "config_version": 2,
                "providers": {"openai": {"type": "openai", "capabilities": ["text"]}},
            },
            "不再接受 capabilities",
        ),
        (
            {"config_version": 2, "models": {"paint_base_url": "https://example.com"}},
            "不再接受 endpoint、base_url",
        ),
        (
            {"config_version": 2, "key": {"openai_api_key": "sk-old"}},
            "不再接受模型 API key",
        ),
        (
            {
                "config_version": 2,
                "providers": {"deepseek": {"type": "deepseek", "api_mode": "responses"}},
            },
            "不支持 api_mode='responses'",
        ),
        (
            {
                "config_version": 2,
                "providers": {
                    "anthropic_chat": {"type": "anthropic", "api_mode": "chat_completions"}
                },
            },
            "不支持 api_mode='chat_completions'",
        ),
        (
            {
                "config_version": 2,
                "providers": {
                    "conflict": {
                        "type": "openai",
                        "api_mode": "responses",
                        "use_responses_api": False,
                    }
                },
            },
            "不再接受 use_responses_api",
        ),
        (
            {
                "config_version": 2,
                "providers": {"invalid": {"type": "openai", "api_mode": "response"}},
            },
            "api_mode 无效",
        ),
    ],
)
def test_v2_rejects_fields_moved_between_models_and_providers(config, message):
    from utils.configs import parse_config

    with pytest.raises(ValueError, match=message):
        parse_config(config)


def test_nickname_requires_non_empty_environment_value():
    from utils.configs import load_nicknames

    with pytest.raises(ValueError, match="至少一个非空 NICKNAME"):
        load_nicknames("")


def test_nickname_rejects_non_string_array_items():
    from utils.configs import load_nicknames

    with pytest.raises(ValueError, match="每一项"):
        load_nicknames('["Frontier", 1]')
