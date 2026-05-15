# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("module_name", "client_attr"),
    [
        ("heavens_above", "httpx_client"),
        ("satellite", "httpx_client"),
        ("space_weather", "httpx_client"),
        ("weather", "httpx_client"),
        ("deepseek_balance", "httpx_client"),
        ("rocket", "http_client"),
    ],
)
async def test_tool_module_http_clients_can_be_closed(load_tool_module, monkeypatch, module_name, client_attr):
    mod = load_tool_module(module_name)
    closed = False

    class DummyClient:
        async def aclose(self):
            nonlocal closed
            closed = True

    monkeypatch.setattr(mod, client_attr, DummyClient())

    await mod.aclose_http_client()

    assert closed is True
