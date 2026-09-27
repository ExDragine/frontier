# ruff: noqa: S101, S105, S106
"""Lifecycle contracts for the opt-in Feishu webhook host."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

import plugins.agent.feishu_lifecycle as lifecycle
from plugins.agent.adapters.feishu_webhook import FeishuWebhookConnector, FeishuWebhookHost
from utils.configs import EnvConfig


@dataclass
class Driver:
    startup: list = field(default_factory=list)
    shutdown: list = field(default_factory=list)

    def on_startup(self, callback):
        self.startup.append(callback)

    def on_shutdown(self, callback):
        self.shutdown.append(callback)


class Gateway:
    async def handle_event(self, _event):
        return None


class TrackingHost(FeishuWebhookHost):
    def __init__(self):
        super().__init__(FeishuWebhookConnector(Gateway(), verification_token="verify-token"))
        self.close_calls = 0

    async def close(self):
        self.close_calls += 1
        await super().close()


def _set_enabled_config(monkeypatch, *, encrypt_key: str = ""):
    monkeypatch.setattr(EnvConfig, "FEISHU_ENABLED", True)
    monkeypatch.setattr(EnvConfig, "FEISHU_APP_ID", "cli-app")
    monkeypatch.setattr(EnvConfig, "FEISHU_BOT_OPEN_ID", "")
    monkeypatch.setattr(EnvConfig, "FEISHU_PATH", "/hooks/feishu")
    monkeypatch.setattr(EnvConfig, "AGENT_CAPABILITY", "medium")
    monkeypatch.setattr(EnvConfig, "FEISHU_APP_SECRET", SecretStr("app-secret"))
    monkeypatch.setattr(EnvConfig, "FEISHU_VERIFICATION_TOKEN", SecretStr("verify-token"))
    monkeypatch.setattr(EnvConfig, "FEISHU_ENCRYPT_KEY", SecretStr(encrypt_key))


@pytest.mark.asyncio
async def test_disabled_lifecycle_does_not_build_or_import_host(monkeypatch):
    monkeypatch.setattr(EnvConfig, "FEISHU_ENABLED", False)
    called = []

    def factory():
        called.append(True)
        raise AssertionError("disabled lifecycle must not call host factory")

    driver = Driver()
    startup, shutdown = lifecycle.register_feishu_lifecycle(driver, host_factory=factory)
    await startup()
    await shutdown()
    assert called == []
    assert driver.startup == [startup]
    assert driver.shutdown == [shutdown]


@pytest.mark.asyncio
async def test_enabled_lifecycle_requires_credentials_before_mount(monkeypatch):
    monkeypatch.setattr(EnvConfig, "FEISHU_ENABLED", True)
    monkeypatch.setattr(EnvConfig, "FEISHU_APP_ID", "")
    monkeypatch.setattr(EnvConfig, "FEISHU_APP_SECRET", SecretStr(""))
    monkeypatch.setattr(EnvConfig, "FEISHU_VERIFICATION_TOKEN", SecretStr(""))
    called = []

    def factory():
        called.append(True)
        raise AssertionError("incomplete credentials must not call host factory")

    startup, _ = lifecycle.register_feishu_lifecycle(Driver(), host_factory=factory)
    await startup()
    assert called == []


@pytest.mark.asyncio
async def test_enabled_lifecycle_mounts_once_and_closes_host(monkeypatch):
    _set_enabled_config(monkeypatch)
    app = FastAPI()
    monkeypatch.setattr(lifecycle, "get_app", lambda: app)
    host = TrackingHost()
    calls = []

    def factory():
        calls.append(True)
        return host

    startup, shutdown = lifecycle.register_feishu_lifecycle(Driver(), host_factory=factory)
    await startup()
    await startup()

    assert calls == [True]
    assert getattr(app.state, lifecycle.FEISHU_HOST_STATE) is host
    assert any(route.path == "/hooks/feishu" for route in app.routes)

    await shutdown()
    assert host.close_calls == 1
    assert not hasattr(app.state, lifecycle.FEISHU_HOST_STATE)


@pytest.mark.asyncio
async def test_custom_factory_can_supply_encrypt_key_decoder(monkeypatch):
    _set_enabled_config(monkeypatch, encrypt_key="encrypt-key")
    app = FastAPI()
    monkeypatch.setattr(lifecycle, "get_app", lambda: app)
    host = TrackingHost()

    startup, shutdown = lifecycle.register_feishu_lifecycle(
        Driver(), host_factory=lambda: host
    )
    await startup()
    assert getattr(app.state, lifecycle.FEISHU_HOST_STATE) is host
    await shutdown()


@pytest.mark.asyncio
async def test_default_factory_stays_closed_when_encrypt_key_needs_decoder(monkeypatch):
    _set_enabled_config(monkeypatch, encrypt_key="encrypt-key")
    called = []

    def default_factory():
        called.append(True)
        raise AssertionError("default factory must not run without a decoder")

    monkeypatch.setattr(lifecycle, "_default_host_factory", default_factory)
    startup, _ = lifecycle.register_feishu_lifecycle(Driver())
    await startup()
    assert called == []


@pytest.mark.asyncio
async def test_mount_failure_closes_constructed_host(monkeypatch):
    _set_enabled_config(monkeypatch)
    monkeypatch.setattr(EnvConfig, "FEISHU_PATH", "/")
    app = FastAPI()
    monkeypatch.setattr(lifecycle, "get_app", lambda: app)
    host = TrackingHost()

    startup, _ = lifecycle.register_feishu_lifecycle(Driver(), host_factory=lambda: host)
    await startup()
    assert host.close_calls == 1
    assert not hasattr(app.state, lifecycle.FEISHU_HOST_STATE)


def test_build_host_unwraps_secret_values_with_injected_sender(monkeypatch):
    host = lifecycle.build_feishu_host(
        app_id=" cli-app ",
        app_secret=SecretStr(" app-secret "),
        verification_token=SecretStr(" verify-token "),
        encrypt_key=SecretStr(" encrypt-key "),
        decryptor=lambda _value: {},
        core=object(),
        history=object(),
        text_sender=lambda *_args: True,
    )
    assert isinstance(host, FeishuWebhookHost)
