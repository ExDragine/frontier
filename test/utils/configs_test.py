# ruff: noqa: S101, S105

import importlib

from pydantic import SecretStr


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
raw_message_group_id = []
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
    assert isinstance(configs.EnvConfig.OPENAI_API_KEY, SecretStr)
    assert configs.EnvConfig.ANNOUNCE_GROUP_ID == configs.EnvConfig.TEST_GROUP_ID
    assert configs.EnvConfig.CONTENT_CHECK_ENABLED is False
    assert isinstance(configs.EnvConfig.GOOGLE_API_KEY, SecretStr)
    assert isinstance(configs.EnvConfig.ANTHROPIC_API_KEY, SecretStr)
    assert configs.EnvConfig.ANTHROPIC_BASE_URL == ""
    assert configs.EnvConfig.BASIC_MODEL_PROVIDER == ""
    assert configs.EnvConfig.BASIC_MODEL_ENDPOINT == ""
    assert configs.EnvConfig.BASIC_MODEL_CAPABILITIES == []
    assert configs.EnvConfig.ADVAN_MODEL_PROVIDER == ""
    assert configs.EnvConfig.ADVAN_MODEL_ENDPOINT == ""
    assert configs.EnvConfig.ADVAN_MODEL_CAPABILITIES == []
    assert configs.EnvConfig.SIGNAL_MODEL == "deepseek-v4-flash"
    assert configs.EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek"
    assert configs.EnvConfig.SIGNAL_MODEL_ENDPOINT == ""
    assert configs.EnvConfig.SIGNAL_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.LLM_ENDPOINTS == {}
    assert isinstance(configs.EnvConfig.DEEPSEEK_API_KEY, SecretStr)
    assert configs.EnvConfig.DEEPSEEK_API_KEY.get_secret_value() == ""
    assert configs.EnvConfig.DEEPSEEK_API_BASE == ""
    assert configs.EnvConfig.VIDEO_MODULE_ENABLED is True
    assert configs.EnvConfig.VIDEO_MODEL == "alibaba/happyhorse-1.0"
    assert configs.EnvConfig.VIDEO_BASE_URL == "https://zenmux.ai/api/vertex-ai"
    assert configs.EnvConfig.VIDEO_API_KEY.get_secret_value() == ""
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 1
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS == 900
    assert configs.EnvConfig.VIDEO_POLL_INTERVAL_SECONDS == 15
    assert configs.EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS == 900


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
raw_message_group_id = []
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

    assert configs.EnvConfig.ANTHROPIC_BASE_URL == "https://anthropic.example.com"


def test_env_config_llm_endpoint_profiles(tmp_path, monkeypatch):
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
raw_message_group_id = []
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

    assert configs.EnvConfig.BASIC_MODEL_PROVIDER == "anthropic"
    assert configs.EnvConfig.BASIC_MODEL_ENDPOINT == "anthropic_proxy"
    assert configs.EnvConfig.BASIC_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.ADVAN_MODEL_PROVIDER == "openai"
    assert configs.EnvConfig.ADVAN_MODEL_ENDPOINT == "openrouter"
    assert configs.EnvConfig.ADVAN_MODEL_CAPABILITIES == ["text", "vision"]
    assert configs.EnvConfig.SIGNAL_MODEL == "deepseek-v4-flash"
    assert configs.EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek"
    assert configs.EnvConfig.SIGNAL_MODEL_ENDPOINT == "deepseek_signal"
    assert configs.EnvConfig.SIGNAL_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.LLM_ENDPOINTS["openrouter"]["api_key"] == "sk-openrouter"
    assert configs.EnvConfig.LLM_ENDPOINTS["openrouter"]["capabilities"] == ["text", "vision"]
    assert configs.EnvConfig.LLM_ENDPOINTS["anthropic_proxy"]["base_url"] == "https://anthropic-proxy.example.com"
    assert configs.EnvConfig.LLM_ENDPOINTS["deepseek_signal"]["provider"] == "deepseek"
    assert configs.EnvConfig.DEEPSEEK_API_KEY.get_secret_value() == "sk-deepseek"
    assert configs.EnvConfig.DEEPSEEK_API_BASE == "https://api.deepseek.example/v1"


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
raw_message_group_id = []
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

    assert configs.EnvConfig.PAINT_BASE_URL == "https://example.com"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk-openai"


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
raw_message_group_id = []
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

    assert configs.EnvConfig.PAINT_BASE_URL == "https://example.com"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk-openai"


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
raw_message_group_id = []
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

    assert configs.EnvConfig.PAINT_BASE_URL == "https://paint.example.com"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk-paint"


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
raw_message_group_id = []
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
    assert configs.EnvConfig.VIDEO_BASE_URL == "https://video.example.com"
    assert configs.EnvConfig.VIDEO_API_KEY.get_secret_value() == "sk-video"
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 2
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS == 1200
    assert configs.EnvConfig.VIDEO_POLL_INTERVAL_SECONDS == 5
    assert configs.EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS == 600
    assert configs.EnvConfig.AGENT_LLM_TIMEOUT_SECONDS == 1234
    assert configs.EnvConfig.AGENT_JOB_TIMEOUT_SECONDS == 4321
