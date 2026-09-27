"""Opt-in NoneBot lifecycle wiring for the Feishu text host.

This module is imported only while the ``plugins.agent`` plugin is being
loaded. Pure adapter imports never reach it. Startup validates the explicit
configuration and credentials before constructing an HTTP client or mounting
the FastAPI callback route; shutdown settles the in-process host queue before
the shared HTTP client registry is closed by the existing Agent lifecycle.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from nonebot import get_app, get_driver, logger

from utils.agents.neutral_core import FrontierAgentCore
from utils.agents.runtime_gateway import FrontierAgentRuntime
from utils.configs import EnvConfig

from .adapters.feishu import FeishuDelivery, FeishuHistoryStore, FeishuMessageAdapter, FeishuTextGateway
from .adapters.feishu_api import FeishuApiClient
from .adapters.feishu_webhook import Decryptor, FeishuWebhookHost

FEISHU_HOST_STATE = "frontier_feishu_webhook_host"
HostFactory = Callable[[], FeishuWebhookHost | Awaitable[FeishuWebhookHost]]


def _secret_value(value: object) -> str:
    getter = getattr(value, "get_secret_value", None)
    if callable(getter):
        value = getter()
    return str(value or "").strip()


def _missing_credentials() -> tuple[str, ...]:
    missing: list[str] = []
    if not EnvConfig.FEISHU_APP_ID.strip():
        missing.append("app_id")
    if not _secret_value(EnvConfig.FEISHU_APP_SECRET):
        missing.append("app_secret")
    if not _secret_value(EnvConfig.FEISHU_VERIFICATION_TOKEN):
        missing.append("verification_token")
    return tuple(missing)


def build_feishu_host(
    *,
    app_id: str,
    app_secret: str,
    verification_token: str,
    bot_open_id: str | None = None,
    encrypt_key: str | None = None,
    decryptor: Decryptor | None = None,
    http_client: object | None = None,
    core: object | None = None,
    history: object | None = None,
    text_sender: Callable[..., Any] | None = None,
    execution_profile: str = "medium",
    max_pending: int = 64,
) -> FeishuWebhookHost:
    """Build the default Feishu text host with injectable test seams."""

    app_id = str(app_id).strip()
    app_secret = _secret_value(app_secret)
    verification_token = _secret_value(verification_token)
    encrypt_key = _secret_value(encrypt_key) or None
    if not app_id or not app_secret or not verification_token:
        raise ValueError("Feishu app_id, app_secret and verification_token are required")
    if encrypt_key is not None and decryptor is None:
        raise ValueError("Feishu encrypt_key requires an injected decryptor")

    if text_sender is None:
        if http_client is None:
            from utils.http_client import get_http_client

            http_client = get_http_client("feishu-api", timeout=30)
        text_sender = FeishuApiClient(app_id=app_id, app_secret=app_secret, http_client=http_client).send_text

    adapter = FeishuMessageAdapter(app_id)
    if history is None:
        history = FeishuHistoryStore(adapter=adapter)
    if core is None:
        # Reuse the existing process-level cognitive object after handlers have
        # loaded, while keeping this compatibility import out of pure facades.
        from .handlers import f_cognitive

        core = FrontierAgentCore(FrontierAgentRuntime(cognitive=f_cognitive))
    delivery = FeishuDelivery(text_sender=text_sender)
    gateway = FeishuTextGateway(
        core=core,
        history=history,
        delivery=delivery,
        account_id=app_id,
        bot_open_id=bot_open_id,
        execution_profile=execution_profile,
    )
    from .adapters.feishu_webhook import FeishuWebhookConnector

    connector = FeishuWebhookConnector(
        gateway,
        verification_token=verification_token,
        encrypt_key=encrypt_key,
        decryptor=decryptor,
    )
    return FeishuWebhookHost(connector, max_pending=max_pending)


def _default_host_factory() -> FeishuWebhookHost:
    return build_feishu_host(
        app_id=EnvConfig.FEISHU_APP_ID,
        app_secret=_secret_value(EnvConfig.FEISHU_APP_SECRET),
        verification_token=_secret_value(EnvConfig.FEISHU_VERIFICATION_TOKEN),
        bot_open_id=EnvConfig.FEISHU_BOT_OPEN_ID or None,
        execution_profile=EnvConfig.AGENT_CAPABILITY,
    )


async def _mount_feishu_host(factory: HostFactory, state: dict[str, object]) -> None:
    host = factory()
    if inspect.isawaitable(host):
        host = await host
    if not isinstance(host, FeishuWebhookHost):
        raise TypeError("Feishu host factory must return FeishuWebhookHost")
    try:
        from .feishu_http import mount_feishu_webhook

        app = get_app()
        mount_feishu_webhook(
            app,
            host,
            path=EnvConfig.FEISHU_PATH,
            name="frontier-feishu-webhook",
        )
        setattr(app.state, FEISHU_HOST_STATE, host)
        state["app"] = app
        state["host"] = host
        logger.success("Feishu webhook 已挂载: {}", EnvConfig.FEISHU_PATH)
    except Exception:
        await host.close()
        raise


async def _shutdown_feishu_state(state: dict[str, object]) -> None:
    host = state.pop("host", None)
    app = state.pop("app", None)
    try:
        if isinstance(host, FeishuWebhookHost):
            await host.close()
    finally:
        if app is not None and hasattr(getattr(app, "state", None), FEISHU_HOST_STATE):
            delattr(app.state, FEISHU_HOST_STATE)


def register_feishu_lifecycle(
    driver: object | None = None,
    *,
    host_factory: HostFactory | None = None,
) -> tuple[Callable[[], Awaitable[None]], Callable[[], Awaitable[None]]]:
    """Register startup/shutdown hooks without enabling Feishu implicitly."""

    if driver is None:
        driver = get_driver()
    state: dict[str, object] = {}

    async def startup_feishu() -> None:
        if state.get("host") is not None:
            return
        if not EnvConfig.FEISHU_ENABLED:
            return
        missing = _missing_credentials()
        if missing:
            logger.warning("Feishu 已启用但凭据不完整，未挂载 webhook: {}", ", ".join(missing))
            return
        encrypt_key = _secret_value(EnvConfig.FEISHU_ENCRYPT_KEY) or None
        if encrypt_key and host_factory is None:
            logger.warning("Feishu Encrypt Key 已配置，但当前 host 未提供 AES 解码器，未挂载 webhook")
            return

        factory = host_factory or _default_host_factory
        try:
            await _mount_feishu_host(factory, state)
        except Exception as error:
            logger.warning("Feishu webhook 挂载失败，已保持关闭: {}", type(error).__name__)

    async def shutdown_feishu() -> None:
        await _shutdown_feishu_state(state)

    driver.on_startup(startup_feishu)
    driver.on_shutdown(shutdown_feishu)
    return startup_feishu, shutdown_feishu


__all__ = ["FEISHU_HOST_STATE", "build_feishu_host", "register_feishu_lifecycle"]
