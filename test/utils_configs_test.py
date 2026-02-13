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
agent_capability = "minimal"
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

[memory]
enabled = true

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.MEMORY_ENABLED is True
    assert configs.EnvConfig.DASHBOARD_PASSWORD == "admin"
    assert isinstance(configs.EnvConfig.OPENAI_API_KEY, SecretStr)
    assert configs.EnvConfig.ANNOUNCE_GROUP_ID == configs.EnvConfig.TEST_GROUP_ID
