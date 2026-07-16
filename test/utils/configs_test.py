# ruff: noqa: S101, S105

import importlib
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_env_config_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ZENMUX_API_KEY", raising=False)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"

[key]
openai_api_key = "sk"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.DASHBOARD_PASSWORD == "admin"
    assert not hasattr(configs.EnvConfig, "RAW_MESSAGE_GROUP_ID")
    assert configs.EnvConfig.LLM_PROVIDERS["openai"]["api_key"] == "sk"
    assert configs.EnvConfig.ANNOUNCE_GROUP_ID == configs.EnvConfig.TEST_GROUP_ID
    assert configs.EnvConfig.CONTENT_CHECK_ENABLED is False
    assert configs.EnvConfig.LLM_PROVIDERS["google"]["api_key"] == ""
    assert configs.EnvConfig.LLM_PROVIDERS["anthropic"]["api_key"] == ""
    assert configs.EnvConfig.LLM_PROVIDERS["anthropic"]["base_url"] == ""
    assert configs.EnvConfig.BASIC_MODEL_PROVIDER == ""
    assert configs.EnvConfig.BASIC_MODEL_CAPABILITIES == []
    assert configs.EnvConfig.ADVAN_MODEL_PROVIDER == ""
    assert configs.EnvConfig.ADVAN_MODEL_CAPABILITIES == []
    assert configs.EnvConfig.SIGNAL_MODEL == "deepseek-v4-flash"
    assert configs.EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek"
    assert configs.EnvConfig.SIGNAL_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.LLM_PROVIDERS["openai"]["use_responses_api"] is True
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["use_responses_api"] is False
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["api_key"] == ""
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["base_url"] == ""
    assert configs.EnvConfig.VIDEO_MODULE_ENABLED is True
    assert configs.EnvConfig.VIDEO_MODEL == "sora-2"
    assert configs.EnvConfig.VIDEO_MODEL_PROVIDER == "video"
    assert configs.EnvConfig.LLM_PROVIDERS["video"]["type"] == "openai"
    assert configs.EnvConfig.LLM_PROVIDERS["video"]["base_url"] == ""
    assert configs.EnvConfig.LLM_PROVIDERS["video"]["api_key"] == ""
    assert configs.EnvConfig.PAINT_SIZE == "1024x1024"
    assert configs.EnvConfig.PAINT_QUALITY == "auto"
    assert configs.EnvConfig.VIDEO_SIZE == "1280x720"
    assert configs.EnvConfig.VIDEO_SECONDS == "8"
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 1
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS == 900
    assert configs.EnvConfig.VIDEO_POLL_INTERVAL_SECONDS == 15
    assert configs.EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS == 900
    assert configs.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE is False
    assert configs.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST == []
    assert configs.EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST == []


def test_env_config_anthropic_base_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"

[key]
openai_api_key = "sk"
nasa_api_key = "nasa"
github_pat = "gh"
anthropic_api_key = "ant"
anthropic_base_url = "https://anthropic.example.com"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.LLM_PROVIDERS["anthropic"]["base_url"] == "https://anthropic.example.com"
    assert configs.EnvConfig.LLM_PROVIDERS["anthropic"]["api_key"] == "ant"


def test_env_config_reload_updates_runtime_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"

[key]
openai_api_key = "sk"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    configs.EnvConfig.reload(
        {
            "function": {
                "agent_auto_reply_whitelist_mode": True,
                "agent_auto_reply_whitelist_group_list": [1001],
                "agent_auto_reply_blacklist_group_list": [1002],
            },
            "image_memory": {"enabled": False, "ttl_days": 9, "auto_cleanup": False},
            "content_check": {"enabled": True},
            "endpoint": {"signal_model_use_responses_api": True},
        }
    )

    assert configs.EnvConfig.IMAGE_ENABLED is False
    assert configs.EnvConfig.IMAGE_TTL_DAYS == 9
    assert configs.EnvConfig.IMAGE_AUTO_CLEANUP is False
    assert configs.EnvConfig.CONTENT_CHECK_ENABLED is True
    assert configs.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE is True
    assert configs.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST == [1001]
    assert configs.EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST == [1002]
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["use_responses_api"] is True

    configs.EnvConfig.reload({"function": {}, "endpoint": {}})

    assert configs.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE is False
    assert configs.EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST == []
    assert configs.EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST == []
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["use_responses_api"] is False


def test_env_config_migrates_legacy_endpoint_profiles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
basic_model_provider = "anthropic"
basic_model_endpoint = "anthropic_proxy"
basic_model_capabilities = ["text"]
signal_model = "deepseek-v4-flash"
signal_model_provider = "deepseek"
signal_model_endpoint = "deepseek_signal"
signal_model_capabilities = ["text"]
signal_model_use_responses_api = true
advan_model = "advan"
advan_model_provider = "openai"
advan_model_endpoint = "openrouter"
advan_model_capabilities = ["text", "vision"]
paint_model = "paint"

[llm_endpoints.openrouter]
provider = "openai"
base_url = "https://openrouter.example.com/api/v1"
api_key = "sk-openrouter"
capabilities = ["text", "vision"]

[llm_endpoints.anthropic_proxy]
provider = "anthropic"
base_url = "https://anthropic-proxy.example.com"
api_key = "ant-proxy"
capabilities = ["text"]

[llm_endpoints.deepseek_signal]
provider = "deepseek"
base_url = "https://deepseek.example.com/v1"
api_key = "sk-deepseek-profile"
capabilities = ["text"]

[key]
openai_api_key = "sk"
deepseek_api_key = "sk-deepseek"
deepseek_api_base = "https://api.deepseek.example/v1"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.BASIC_MODEL_PROVIDER == "anthropic_proxy"
    assert configs.EnvConfig.BASIC_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.ADVAN_MODEL_PROVIDER == "openrouter"
    assert configs.EnvConfig.ADVAN_MODEL_CAPABILITIES == ["text", "vision"]
    assert configs.EnvConfig.SIGNAL_MODEL == "deepseek-v4-flash"
    assert configs.EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek_signal"
    assert configs.EnvConfig.SIGNAL_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.LLM_PROVIDERS["openrouter"]["api_key"] == "sk-openrouter"
    assert "capabilities" not in configs.EnvConfig.LLM_PROVIDERS["openrouter"]
    assert configs.EnvConfig.LLM_PROVIDERS["openrouter"]["use_responses_api"] is True
    assert configs.EnvConfig.LLM_PROVIDERS["anthropic_proxy"]["base_url"] == "https://anthropic-proxy.example.com"
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek_signal"]["type"] == "deepseek"
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek_signal"]["use_responses_api"] is True
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["api_key"] == "sk-deepseek"
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["base_url"] == "https://api.deepseek.example/v1"


def test_legacy_canonical_profile_keeps_global_provider_key():
    from utils.configs import parse_config

    settings = parse_config(
        {
            "llm_endpoints": {
                "openai": {
                    "provider": "openai",
                    "base_url": "https://openai.example.com/v1",
                    "api_key": "",
                }
            },
            "key": {"openai_api_key": "sk-legacy"},
        }
    )

    assert settings.providers["openai"].api_key == "sk-legacy"


def test_legacy_paint_dimensions_migrate_to_openai_size():
    from utils.configs import parse_config

    settings = parse_config(
        {
            "models": {
                "paint_model": "gpt-image-test",
                "paint_aspect_ratio": "16:9",
                "paint_image_size": "2K",
            }
        }
    )

    assert settings.models.paint.size == "2048x1152"
    assert settings.models.paint.quality == "auto"


def test_env_config_paint_fields_fall_back_to_openai_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
paint_base_url = ""

[key]
openai_api_key = "sk-openai"
paint_api_key = ""
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    profile = configs.EnvConfig.LLM_PROVIDERS[configs.EnvConfig.PAINT_MODEL_PROVIDER]
    assert profile["base_url"] == "https://example.com"
    assert profile["api_key"] == "sk-openai"


def test_env_config_paint_fields_fall_back_when_keys_are_omitted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"

[key]
openai_api_key = "sk-openai"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    profile = configs.EnvConfig.LLM_PROVIDERS[configs.EnvConfig.PAINT_MODEL_PROVIDER]
    assert profile["base_url"] == "https://example.com"
    assert profile["api_key"] == "sk-openai"


def test_env_config_paint_fields_allow_explicit_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
paint_base_url = "https://paint.example.com"

[key]
openai_api_key = "sk-openai"
paint_api_key = "sk-paint"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    profile = configs.EnvConfig.LLM_PROVIDERS[configs.EnvConfig.PAINT_MODEL_PROVIDER]
    assert profile["base_url"] == "https://paint.example.com"
    assert profile["api_key"] == "sk-paint"


def test_env_config_video_fields_allow_explicit_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
video_model = "custom-video"
video_base_url = "https://video.example.com"

[key]
openai_api_key = "sk-openai"
video_api_key = "sk-video"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
video_module_enabled = false
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []
video_rate_limit_max_requests = 2
video_rate_limit_window_seconds = 1200
video_poll_interval_seconds = 5
video_poll_timeout_seconds = 600
agent_llm_timeout_seconds = 1234
agent_job_timeout_seconds = 4321

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.VIDEO_MODULE_ENABLED is False
    assert configs.EnvConfig.VIDEO_MODEL == "custom-video"
    profile = configs.EnvConfig.LLM_PROVIDERS[configs.EnvConfig.VIDEO_MODEL_PROVIDER]
    assert profile["base_url"] == "https://video.example.com"
    assert profile["api_key"] == "sk-video"
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 2
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS == 1200
    assert configs.EnvConfig.VIDEO_POLL_INTERVAL_SECONDS == 5
    assert configs.EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS == 600
    assert configs.EnvConfig.AGENT_LLM_TIMEOUT_SECONDS == 1234
    assert configs.EnvConfig.AGENT_JOB_TIMEOUT_SECONDS == 4321


def test_v2_config_loads_new_sections_and_keeps_keys_in_toml(monkeypatch):
    from utils.configs import EnvConfig

    monkeypatch.setenv("NICKNAME", '["EnvBot", "小助手", "EnvBot", ""]')
    EnvConfig.reload(
        {
            "config_version": 2,
            "bot": {"name": "IgnoredTomlName", "system_prompt": "你是 {name}"},
            "models": {
                "basic_model": "gpt-5-mini",
                "basic_model_provider": "openai_chat",
                "signal_model": "gpt-5-nano",
                "signal_model_provider": "openai",
                "advanced_model": "gpt-5.4",
                "advanced_model_provider": "openai",
                "advanced_model_capabilities": ["text", "vision"],
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
                    "base_url": "https://api.example.com/v1",
                    "api_key": "sk-v2",
                    "use_responses_api": True,
                },
                "openai_chat": {
                    "type": "openai",
                    "base_url": "https://chat.example.com/v1",
                    "api_key": "sk-chat",
                    "use_responses_api": False,
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
    assert EnvConfig.LLM_PROVIDERS["openai_chat"]["use_responses_api"] is False
    assert EnvConfig.LLM_PROVIDERS["openai"]["use_responses_api"] is True
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
                "bot": {"name": "ShouldNotApply"},
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
    assert settings.providers["openai"].use_responses_api is True
    assert settings.models.advanced.provider == "openai"
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
