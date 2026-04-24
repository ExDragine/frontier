# ruff: noqa: S101

import types

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from plugins.dashboard.api import auth_routes, messages_routes, settings_routes, status_routes, tasks_routes


@pytest.mark.asyncio
async def test_login_rate_limit(monkeypatch):
    monkeypatch.setattr(auth_routes, "check_rate_limit", lambda _ip: False)
    request = types.SimpleNamespace(client=types.SimpleNamespace(host="127.0.0.1"))
    with pytest.raises(HTTPException):
        await auth_routes.login(request, auth_routes.LoginRequest(password="x"))


@pytest.mark.asyncio
async def test_status_overview_handles_missing_task_plugin(monkeypatch):
    class DummySession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def exec(self, *_args, **_kwargs):
            class DummyResult:
                def one(self):
                    return 0

            return DummyResult()

    monkeypatch.setattr(status_routes, "Session", lambda _engine: DummySession())
    monkeypatch.setattr(status_routes, "get_bots", lambda: {})
    monkeypatch.setattr(
        status_routes,
        "EnvConfig",
        types.SimpleNamespace(
            BOT_NAME="bot",
            AGENT_MODULE_ENABLED=True,
            PAINT_MODULE_ENABLED=True,
            AGENT_CAPABILITY="none",
            AGENT_DEBUG_MODE=False,
            BASIC_MODEL="b",
            ADVAN_MODEL="a",
            PAINT_MODEL="p",
        ),
    )

    monkeypatch.setattr(status_routes, "Message", types.SimpleNamespace)
    monkeypatch.setattr(status_routes, "User", types.SimpleNamespace)
    monkeypatch.setattr(
        status_routes,
        "select",
        lambda *_args, **_kwargs: types.SimpleNamespace(select_from=lambda *_a, **_k: types.SimpleNamespace()),
    )
    monkeypatch.setattr(status_routes, "func", types.SimpleNamespace(count=lambda: None))

    result = await status_routes.get_status_overview(user={})
    assert result["database"]["task_count"] == 0


@pytest.mark.asyncio
async def test_messages_list_filters(monkeypatch):
    class DummySession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def exec(self, *_args, **_kwargs):
            class DummyResult:
                def one(self):
                    return 0

                def all(self):
                    return []

            return DummyResult()

    monkeypatch.setattr(messages_routes, "Session", lambda _engine: DummySession())
    monkeypatch.setattr(
        messages_routes, "Message", types.SimpleNamespace(time=types.SimpleNamespace(desc=lambda: None))
    )

    def fake_select(*_args, **_kwargs):
        return types.SimpleNamespace(
            where=lambda *_a, **_k: types.SimpleNamespace(
                where=lambda *_aa, **_kk: types.SimpleNamespace(
                    order_by=lambda *_aaa, **_kkk: types.SimpleNamespace(
                        offset=lambda *_aaaa, **_kkkk: types.SimpleNamespace(
                            limit=lambda *_aaaaa, **_kkkkk: types.SimpleNamespace()
                        )
                    )
                )
            ),
            subquery=lambda: types.SimpleNamespace(),
            select_from=lambda *_a, **_k: types.SimpleNamespace(),
            order_by=lambda *_a, **_k: types.SimpleNamespace(
                offset=lambda *_aa, **_kk: types.SimpleNamespace(limit=lambda *_aaa, **_kkk: types.SimpleNamespace())
            ),
        )

    monkeypatch.setattr(messages_routes, "select", fake_select)
    monkeypatch.setattr(messages_routes, "func", types.SimpleNamespace(count=lambda: None))

    result = await messages_routes.list_messages(user={}, page=1, page_size=50)
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_tasks_routes_missing_plugin(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("plugins.clockwork"):
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(HTTPException):
        await tasks_routes.list_tasks(user={})


def test_settings_mask_value():
    assert settings_routes._mask_value("123456") == "****3456"


def test_settings_sanitize_masks_paint_api_key():
    result = settings_routes._sanitize_config(
        {
            "key": {
                "openai_api_key": "sk-openai",
                "paint_api_key": "sk-paint-secret",
            }
        }
    )

    assert result["key"]["paint_api_key"] == "****cret"


def test_reload_env_config_recomputes_paint_specific_values(tmp_path, monkeypatch):
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://global.example.com/v1"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
paint_base_url = ""

[key]
openai_api_key = "sk-global"
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

    monkeypatch.setattr(settings_routes, "TOML_PATH", env_path)

    import utils.configs as configs

    configs.EnvConfig.OPENAI_BASE_URL = "https://old.example.com/v1"
    configs.EnvConfig.PAINT_BASE_URL = "https://old-paint.example.com/v1"
    configs.EnvConfig.OPENAI_API_KEY = SecretStr("sk-old-global")
    configs.EnvConfig.PAINT_API_KEY = SecretStr("sk-old-paint")

    settings_routes._reload_env_config()

    assert configs.EnvConfig.OPENAI_BASE_URL == "https://global.example.com/v1"
    assert configs.EnvConfig.PAINT_BASE_URL == "https://global.example.com/v1"
    assert configs.EnvConfig.OPENAI_API_KEY.get_secret_value() == "sk-global"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk-global"
