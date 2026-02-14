# ruff: noqa: S101

import types

import pytest
from fastapi import HTTPException

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
            MEMORY_ENABLED=True,
            AGENT_CAPABILITY="minimal",
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
