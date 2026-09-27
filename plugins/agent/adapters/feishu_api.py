"""Small SDK-free Feishu Open API client for text delivery.

Only the transport contract needed by the P4 text loop lives here: obtaining
an app tenant access token and sending a text message to a chat. The HTTP
client is injected so this module stays deterministic in tests and does not
own a global network client or any NoneBot lifecycle.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from utils.agent_protocol import ConversationRef


class _HttpResponse(Protocol):
    status_code: int

    def json(self) -> object: ...

    def raise_for_status(self) -> object: ...


class _HttpClient(Protocol):
    async def post(self, url: str, **kwargs: Any) -> _HttpResponse: ...


class FeishuApiError(RuntimeError):
    """Safe, non-secret error raised by the Feishu Open API client."""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _api_code(payload: Mapping[str, object]) -> object:
    return payload.get("code")


def _is_success_code(value: object) -> bool:
    return (type(value) is int and value == 0) or value == "0"


class FeishuApiClient:
    """Fetch tenant credentials and send text messages through Feishu APIs."""

    def __init__(
        self,
        *,
        app_id: str,
        app_secret: str,
        http_client: _HttpClient,
        base_url: str = "https://open.feishu.cn/open-apis",
        token_refresh_margin_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.app_id = str(app_id).strip()
        self.app_secret = str(app_secret).strip()
        if not self.app_id or not self.app_secret:
            raise ValueError("Feishu app_id and app_secret are required")
        self.http_client = http_client
        self.base_url = str(base_url).rstrip("/")
        if not self.base_url:
            raise ValueError("Feishu base_url is required")
        if token_refresh_margin_seconds < 0:
            raise ValueError("token_refresh_margin_seconds must be non-negative")
        self.token_refresh_margin_seconds = float(token_refresh_margin_seconds)
        self._clock = clock
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def token_cached(self) -> bool:
        """Whether a non-expired token is currently cached."""

        return self._token is not None and self._clock() < self._token_expires_at

    def invalidate_token(self) -> None:
        """Drop the cached token without exposing its value."""

        self._token = None
        self._token_expires_at = 0.0

    async def tenant_access_token(self) -> str:
        """Return a cached token or refresh it with the app credentials."""

        now = self._clock()
        if self._token is not None and now < self._token_expires_at - self.token_refresh_margin_seconds:
            return self._token
        async with self._token_lock:
            now = self._clock()
            if self._token is not None and now < self._token_expires_at - self.token_refresh_margin_seconds:
                return self._token
            response = await self.http_client.post(
                f"{self.base_url}/auth/v3/tenant_access_token/internal",
                headers={"Content-Type": "application/json; charset=utf-8"},
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            payload = self._read_response(response, "tenant access token")
            token = payload.get("tenant_access_token")
            if not isinstance(token, str) or not token.strip():
                raise FeishuApiError("Feishu tenant access token response was incomplete")
            try:
                expires_in = float(payload.get("expire"))
            except (TypeError, ValueError) as error:
                raise FeishuApiError("Feishu tenant access token expiry was invalid") from error
            if expires_in <= 0:
                raise FeishuApiError("Feishu tenant access token expiry was invalid")
            self._token = token.strip()
            self._token_expires_at = self._clock() + expires_in
            return self._token

    async def send_text(self, target: ConversationRef, text: str) -> Mapping[str, object]:
        """Send text to a Feishu chat and return a Delivery-compatible result."""

        if target.platform.lower() != "feishu":
            raise ValueError("FeishuApiClient only handles feishu conversations")
        if target.kind.lower() not in {"direct", "group"} or target.parent_id is not None:
            raise ValueError("FeishuApiClient only handles direct or group chats")
        conversation_id = target.conversation_id.strip()
        if not conversation_id:
            raise ValueError("Feishu conversation_id must not be empty")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Feishu text message must not be empty")
        token = await self.tenant_access_token()
        response = await self.http_client.post(
            f"{self.base_url}/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "receive_id": conversation_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}, ensure_ascii=False, separators=(",", ":")),
            },
        )
        if getattr(response, "status_code", 200) in {401, 403}:
            self.invalidate_token()
        payload = self._read_response(response, "text message")
        data = _mapping(payload.get("data"))
        message_id = data.get("message_id") or data.get("messageId") or payload.get("message_id")
        if message_id is None or not str(message_id).strip():
            raise FeishuApiError("Feishu text message response was missing message_id")
        result: dict[str, object] = {"status": "delivered"}
        result["message_id"] = str(message_id)
        return result

    @staticmethod
    def _read_response(response: _HttpResponse, operation: str) -> Mapping[str, object]:
        try:
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                result = raise_for_status()
                if inspect.isawaitable(result):
                    raise FeishuApiError(f"Feishu {operation} response was unexpectedly asynchronous")
            payload = response.json()
        except FeishuApiError:
            raise
        except Exception as error:
            raise FeishuApiError(f"Feishu {operation} request failed: {type(error).__name__}") from error
        data = _mapping(payload)
        if not data:
            raise FeishuApiError(f"Feishu {operation} response was not a JSON object")
        if not _is_success_code(_api_code(data)):
            raise FeishuApiError(f"Feishu {operation} was rejected (code={_api_code(data)!r})")
        return data


__all__ = ["FeishuApiClient", "FeishuApiError"]
