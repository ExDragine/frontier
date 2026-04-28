# ruff: noqa: S101

import importlib

from pydantic import SecretStr


def test_env_config_defaults(tmp_path, monkeypatch):
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
    assert configs.EnvConfig.LLM_ENDPOINTS == {}


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

    assert configs.EnvConfig.BASIC_MODEL_PROVIDER == "anthropic"
    assert configs.EnvConfig.BASIC_MODEL_ENDPOINT == "anthropic_proxy"
    assert configs.EnvConfig.BASIC_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.ADVAN_MODEL_PROVIDER == "openai"
    assert configs.EnvConfig.ADVAN_MODEL_ENDPOINT == "openrouter"
    assert configs.EnvConfig.ADVAN_MODEL_CAPABILITIES == ["text", "vision"]
    assert configs.EnvConfig.LLM_ENDPOINTS["openrouter"]["api_key"] == "sk-openrouter"
    assert configs.EnvConfig.LLM_ENDPOINTS["openrouter"]["capabilities"] == ["text", "vision"]
    assert configs.EnvConfig.LLM_ENDPOINTS["anthropic_proxy"]["base_url"] == "https://anthropic-proxy.example.com"


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
