# ruff: noqa: S101, S106

import types
from typing import cast

import pytest
from fastapi import HTTPException
from sqlmodel import Session, create_engine
from starlette.requests import Request

from plugins.dashboard.api import auth_routes, messages_routes, settings_routes, status_routes, tasks_routes


@pytest.mark.asyncio
async def test_session_defaults_can_be_saved_as_a_new_config_section(tmp_path, monkeypatch):
    path = tmp_path / "settings.toml"
    path.write_text("config_version = 2\n", encoding="utf-8")
    monkeypatch.setattr(settings_routes, "TOML_PATH", path)
    monkeypatch.setattr(settings_routes, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(settings_routes, "_reload_env_config", lambda _config: None)
    settings = (await settings_routes.get_settings(user={}))['config']
    assert settings['sessions']['enabled'] is False
    assert settings['sessions']['history_window_fraction'] == 0.25
    await settings_routes._update_section('sessions', {'enabled': True, 'group_idle_seconds': 900})
    saved = (await settings_routes.get_section('sessions', user={}))['config']
    assert saved['enabled'] is True
    assert saved['group_idle_seconds'] == 900
    assert saved['history_max_tokens'] == 32000


@pytest.mark.asyncio
async def test_login_rate_limit(monkeypatch):
    monkeypatch.setattr(auth_routes, "check_rate_limit", lambda _ip: False)
    request = types.SimpleNamespace(client=types.SimpleNamespace(host="127.0.0.1"))
    with pytest.raises(HTTPException):
        await auth_routes.login(cast(Request, request), auth_routes.LoginRequest(password="x"))


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
    assert "usage_missing_calls" in result["agent_usage"]
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
        messages_routes, "Message", types.SimpleNamespace(
            time=types.SimpleNamespace(desc=lambda: None),
            id=types.SimpleNamespace(desc=lambda: None),
        )
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
    monkeypatch.setattr(messages_routes, "col", lambda value: value)
    monkeypatch.setattr(messages_routes, "func", types.SimpleNamespace(count=lambda: None))

    result = await messages_routes.list_messages(user={}, page=1, page_size=50)
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_messages_pagination_keeps_equal_timestamps_distinct(tmp_path, monkeypatch):
    from utils.database import Message

    engine = create_engine(f"sqlite:///{tmp_path / 'dashboard-messages.db'}")
    Message.__table__.create(engine)
    with Session(engine) as session:
        session.add_all([
            Message(time=1000, msg_id=sequence, user_id=sequence, group_id=123,
                    user_name=f"Member {sequence}", role="user", content=f"message {sequence}")
            for sequence in (7, 8, 9)
        ])
        session.commit()
    monkeypatch.setattr(messages_routes, "engine", engine)

    pages = [
        await messages_routes.list_messages(group_id=123, page=page, page_size=1, user={})
        for page in (1, 2, 3)
    ]
    messages = [page["messages"][0] for page in pages]
    assert [message["msg_id"] for message in messages] == [9, 8, 7]
    assert len({message["id"] for message in messages}) == 3
    assert all(message["time"] == 1000 for message in messages)
    assert all(page["total"] == 3 for page in pages)


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


def test_settings_sanitize_masks_non_model_service_keys():
    result = settings_routes._sanitize_config(
        {
            "key": {
                "nasa_api_key": "nasa-secret",
                "github_pat": "github-secret",
            }
        }
    )

    assert result["key"]["nasa_api_key"] == "****cret"
    assert result["key"]["github_pat"] == "****cret"


def test_settings_sanitize_masks_provider_api_key():
    result = settings_routes._sanitize_config(
        {
            "providers": {
                "openrouter": {
                    "type": "openai",
                    "base_url": "https://openrouter.example.com/api/v1",
                    "api_key": "sk-openrouter-secret",
                }
            }
        }
    )

    assert result["providers"]["openrouter"]["api_key"] == "****cret"


@pytest.mark.asyncio
async def test_settings_section_recursively_masks_provider_api_key(monkeypatch):
    monkeypatch.setattr(
        settings_routes,
        "_read_toml",
        lambda: {
            "providers": {
                "openrouter": {
                    "type": "openai",
                    "api_key": "sk-openrouter-secret",
                }
            }
        },
    )

    result = await settings_routes.get_section("providers", user={})

    assert result["config"]["openrouter"]["api_key"] == "****cret"


def test_settings_update_preserves_masked_nested_provider_api_key():
    result = settings_routes._resolve_update_value(
        "providers",
        "openrouter",
        {
            "type": "openai",
            "base_url": "https://old.example.com/api/v1",
            "api_key": "sk-openrouter-secret",
        },
        {
            "type": "openai",
            "base_url": "https://new.example.com/api/v1",
            "api_key": "****cret",
        },
    )

    assert result["base_url"] == "https://new.example.com/api/v1"
    assert result["api_key"] == "sk-openrouter-secret"


@pytest.mark.asyncio
async def test_settings_rejects_invalid_config_before_writing(tmp_path, monkeypatch):
    env_path = tmp_path / "env.toml"
    original = """config_version = 2

[limits]
agent_llm_timeout_seconds = 900
"""
    env_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(settings_routes, "TOML_PATH", env_path)
    monkeypatch.setattr(settings_routes, "BACKUP_DIR", tmp_path / "backups")

    with pytest.raises(HTTPException) as exc_info:
        await settings_routes.update_section(
            "limits",
            settings_routes.SectionUpdate(config={"agent_llm_timeout_seconds": 0}),
            user={},
        )

    assert exc_info.value.status_code == 422
    assert env_path.read_text(encoding="utf-8") == original
    assert not settings_routes.BACKUP_DIR.exists()


def test_reload_env_config_recomputes_paint_specific_values(tmp_path, monkeypatch):
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
config_version = 2

[models]
basic_model = "basic"
basic_model_provider = "anthropic_proxy"
basic_model_capabilities = ["text"]
signal_model = "deepseek-v4-flash"
signal_model_provider = "deepseek_signal"
signal_model_capabilities = ["text"]
advanced_model = "advan"
advanced_model_provider = "openrouter"
advanced_model_capabilities = ["text", "vision"]
paint_model = "paint"
paint_model_provider = "openai"
video_model = "alibaba/happyhorse-1.0"
video_model_provider = "video"

[providers.openai]
type = "openai"
base_url = "https://global.example.com/v1"
api_key = "sk-global"

[providers.openrouter]
type = "openai"
api_mode = "responses"
base_url = "https://openrouter.example.com/api/v1"
api_key = "sk-openrouter"

[providers.anthropic_proxy]
type = "anthropic"
base_url = "https://anthropic.example.com"
api_key = "ant-proxy"

[providers.deepseek_signal]
type = "deepseek"
base_url = "https://deepseek.example.com/v1"
api_key = "sk-deepseek-profile"

[providers.google]
type = "google"
api_key = "ggl-global"

[providers.anthropic]
type = "anthropic"
api_key = "ant-global"
base_url = "https://anthropic.example.com"

[providers.deepseek]
type = "deepseek"
api_key = "sk-deepseek"
base_url = "https://api.deepseek.example/v1"

[providers.video]
type = "openai"
base_url = "https://zenmux.ai/api/vertex-ai"
api_key = "sk-video"

[key]
nasa_api_key = "nasa"
github_pat = "gh"

[agent]
reasoning_effort = "none"

[limits]
video_rate_limit_max_requests = 2
video_rate_limit_window_seconds = 1200
video_poll_interval_seconds = 3
video_poll_timeout_seconds = 600
agent_llm_timeout_seconds = 1500
agent_job_timeout_seconds = 5400

[storage]
query_message_numbers = 3

[dashboard]
password = "admin"
jwt_secret = "secret"

""",
        encoding="utf-8",
    )

    monkeypatch.setattr(settings_routes, "TOML_PATH", env_path)

    import utils.configs as configs

    configs.EnvConfig.BASIC_MODEL_PROVIDER = ""
    configs.EnvConfig.BASIC_MODEL_CAPABILITIES = []
    configs.EnvConfig.SIGNAL_MODEL = "old-signal"
    configs.EnvConfig.SIGNAL_MODEL_PROVIDER = ""
    configs.EnvConfig.SIGNAL_MODEL_CAPABILITIES = []
    configs.EnvConfig.ADVAN_MODEL_PROVIDER = ""
    configs.EnvConfig.ADVAN_MODEL_CAPABILITIES = []
    configs.EnvConfig.PAINT_MODEL_PROVIDER = "old-paint"
    configs.EnvConfig.PAINT_SIZE = "old-size"
    configs.EnvConfig.PAINT_QUALITY = "old-quality"
    configs.EnvConfig.VIDEO_MODEL = "old-video"
    configs.EnvConfig.VIDEO_MODEL_PROVIDER = "old-video"
    configs.EnvConfig.VIDEO_SIZE = "old-size"
    configs.EnvConfig.VIDEO_SECONDS = "0"
    configs.EnvConfig.LLM_PROVIDERS = {}
    configs.EnvConfig.VIDEO_MODULE_ENABLED = False
    configs.EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS = 1
    configs.EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS = 900
    configs.EnvConfig.VIDEO_POLL_INTERVAL_SECONDS = 15
    configs.EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS = 900
    configs.EnvConfig.AGENT_LLM_TIMEOUT_SECONDS = 300
    configs.EnvConfig.AGENT_JOB_TIMEOUT_SECONDS = 900

    settings_routes._reload_env_config()

    assert configs.EnvConfig.BASIC_MODEL_PROVIDER == "anthropic_proxy"
    assert configs.EnvConfig.BASIC_MODEL_CAPABILITIES == ["text"]
    assert configs.EnvConfig.ADVAN_MODEL_PROVIDER == "openrouter"
    assert configs.EnvConfig.ADVAN_MODEL_CAPABILITIES == ["text", "vision"]
    assert configs.EnvConfig.SIGNAL_MODEL == "deepseek-v4-flash"
    assert configs.EnvConfig.SIGNAL_MODEL_PROVIDER == "deepseek_signal"
    assert configs.EnvConfig.SIGNAL_MODEL_CAPABILITIES == ["text"]
    paint_profile = configs.EnvConfig.LLM_PROVIDERS[configs.EnvConfig.PAINT_MODEL_PROVIDER]
    assert paint_profile["base_url"] == "https://global.example.com/v1"
    assert paint_profile["api_key"] == "sk-global"
    assert configs.EnvConfig.PAINT_SIZE == "1024x1024"
    assert configs.EnvConfig.PAINT_QUALITY == "auto"
    assert configs.EnvConfig.VIDEO_MODEL == "alibaba/happyhorse-1.0"
    video_profile = configs.EnvConfig.LLM_PROVIDERS[configs.EnvConfig.VIDEO_MODEL_PROVIDER]
    assert video_profile["base_url"] == "https://zenmux.ai/api/vertex-ai"
    assert video_profile["api_key"] == "sk-video"
    assert video_profile["type"] == "openai"
    assert configs.EnvConfig.VIDEO_SIZE == "1280x720"
    assert configs.EnvConfig.VIDEO_SECONDS == "8"
    assert "capabilities" not in configs.EnvConfig.LLM_PROVIDERS["openrouter"]
    assert configs.EnvConfig.LLM_PROVIDERS["openrouter"]["api_key"] == "sk-openrouter"
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek_signal"]["type"] == "deepseek"
    assert configs.EnvConfig.LLM_PROVIDERS["openai"]["api_key"] == "sk-global"
    assert configs.EnvConfig.LLM_PROVIDERS["google"]["api_key"] == "ggl-global"
    assert configs.EnvConfig.LLM_PROVIDERS["anthropic"]["api_key"] == "ant-global"
    assert configs.EnvConfig.LLM_PROVIDERS["anthropic"]["base_url"] == "https://anthropic.example.com"
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["api_key"] == "sk-deepseek"
    assert configs.EnvConfig.LLM_PROVIDERS["deepseek"]["base_url"] == "https://api.deepseek.example/v1"
    assert configs.EnvConfig.VIDEO_MODULE_ENABLED is True
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS == 2
    assert configs.EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS == 1200
    assert configs.EnvConfig.VIDEO_POLL_INTERVAL_SECONDS == 3
    assert configs.EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS == 600
    assert configs.EnvConfig.AGENT_LLM_TIMEOUT_SECONDS == 1500
    assert configs.EnvConfig.AGENT_JOB_TIMEOUT_SECONDS == 5400
