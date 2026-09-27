"""Optional FastAPI host adapter for the SDK-free Feishu webhook host.

The module is deliberately not imported by the default Agent plugin. A host
application can call :func:`mount_feishu_webhook` from its own startup hook
after it has built a configured ``FeishuWebhookHost``. This keeps route
registration, raw request handling and HTTP error mapping outside the neutral
adapter and preserves the default-off Feishu deployment boundary.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .adapters.feishu_webhook import FeishuWebhookError, FeishuWebhookHost


async def _handle_request(request: Request, host: FeishuWebhookHost) -> JSONResponse:
    raw_body = await request.body()
    try:
        result = await host.receive(raw_body, request.headers)
    except FeishuWebhookError:
        # Do not echo signature, token, decryptor or provider payload details.
        return JSONResponse({"error": "invalid_feishu_webhook"}, status_code=400)
    return JSONResponse(dict(result.body), status_code=result.status_code)


def make_feishu_webhook_endpoint(host: FeishuWebhookHost):
    """Build a FastAPI endpoint that preserves the raw signed body."""

    async def endpoint(request: Request) -> JSONResponse:
        return await _handle_request(request, host)

    return endpoint


def mount_feishu_webhook(
    app: FastAPI,
    host: FeishuWebhookHost,
    *,
    path: str = "/feishu/events",
    **route_kwargs: Any,
):
    """Mount one POST endpoint without enabling it implicitly.

    ``route_kwargs`` is intentionally narrow in normal use (for example a
    custom route name). The route is hidden from the public OpenAPI schema by
    default because it is a provider callback rather than a user API.
    """

    if not path.startswith("/") or path == "/":
        raise ValueError("Feishu webhook path must be a non-root absolute path")
    endpoint = make_feishu_webhook_endpoint(host)
    route_kwargs.setdefault("include_in_schema", False)
    app.add_api_route(path, endpoint, methods=["POST"], **route_kwargs)
    return endpoint


__all__ = ["make_feishu_webhook_endpoint", "mount_feishu_webhook"]
