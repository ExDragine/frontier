"""Dependency-free Feishu event webhook boundary.

This module handles the small amount of transport security that belongs at a
webhook edge: JSON decoding, URL challenge validation, optional request
signature validation, and dispatch to :class:`FeishuTextGateway`.  It does not
register a FastAPI route or import a Feishu SDK.  A host application can map
``FeishuWebhookError`` to its HTTP response type and keep the connector
disabled until credentials and an HTTPS endpoint are configured.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import inspect
import json
import logging
import math
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass

from .feishu import FeishuTextGateway


class FeishuWebhookError(ValueError):
    """Raised when a webhook request cannot be authenticated or decoded."""


@dataclass(frozen=True, slots=True)
class FeishuWebhookResult:
    """Small transport-neutral result for an HTTP adapter."""

    status_code: int
    body: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FeishuWebhookDispatch:
    """Authenticated event ready for background Agent execution."""

    payload: Mapping[str, object]


Decryptor = Callable[[str], Mapping[str, object] | bytes | bytearray]
DispatchResultHandler = Callable[[FeishuWebhookResult], Awaitable[object] | object]
_logger = logging.getLogger(__name__)


def _header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            text = str(value).strip()
            return text or None
    return None


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _json_body(raw_body: bytes | bytearray | str | Mapping[str, object]) -> tuple[bytes, Mapping[str, object]]:
    if isinstance(raw_body, Mapping):
        payload = dict(raw_body)
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return encoded, payload
    if isinstance(raw_body, str):
        raw = raw_body.encode("utf-8")
    elif isinstance(raw_body, (bytes, bytearray)):
        raw = bytes(raw_body)
    else:
        raise FeishuWebhookError("webhook body must be JSON bytes, text, or a mapping")
    try:
        decoded = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise FeishuWebhookError("webhook body is not valid JSON") from exc
    payload = _mapping(decoded)
    if not payload:
        raise FeishuWebhookError("webhook body must be a JSON object")
    return raw, payload


def _signature(*, timestamp: str, nonce: str, encrypt_key: str, raw_body: bytes) -> str:
    # Feishu's event signature is the SHA-256 digest of the three header
    # values followed immediately by the exact raw request body.  Do not
    # parse/re-serialize the body or add separators: whitespace and field
    # order are part of the signed bytes.
    message = timestamp.encode("utf-8") + nonce.encode("utf-8") + encrypt_key.encode("utf-8") + raw_body
    return hashlib.sha256(message).hexdigest()


def _payload_token(payload: Mapping[str, object]) -> str | None:
    token = payload.get("token")
    if token is None:
        header = _mapping(payload.get("header"))
        token = header.get("token")
    if token is None:
        return None
    value = str(token).strip()
    return value or None


class FeishuWebhookConnector:
    """Authenticate and dispatch Feishu webhook requests.

    At least one of ``verification_token`` or ``encrypt_key`` is required.
    When an encrypt key is configured, normal events validate the
    ``X-Lark-Request-*`` signature over the *raw* request body.  URL
    verification is a separate handshake: it is decoded first and requires a
    configured Verification Token, but does not require event signature
    headers.  Encrypted payloads require an injected decryptor so the
    repository does not gain a cryptography dependency as part of the
    platform boundary.
    """

    def __init__(
        self,
        gateway: FeishuTextGateway,
        *,
        verification_token: str | None = None,
        encrypt_key: str | None = None,
        decryptor: Decryptor | None = None,
        max_clock_skew_seconds: int = 300,
    ) -> None:
        self.gateway = gateway
        self.verification_token = str(verification_token or "").strip() or None
        self.encrypt_key = str(encrypt_key or "").strip() or None
        self.decryptor = decryptor
        if self.verification_token is None and self.encrypt_key is None:
            raise ValueError("configure a Feishu verification_token or encrypt_key")
        if max_clock_skew_seconds < 1:
            raise ValueError("max_clock_skew_seconds must be positive")
        self.max_clock_skew_seconds = max_clock_skew_seconds

    def _verify_signature(self, raw_body: bytes, headers: Mapping[str, str]) -> None:
        if self.encrypt_key is None:
            return
        timestamp = _header(headers, "X-Lark-Request-Timestamp")
        nonce = _header(headers, "X-Lark-Request-Nonce")
        received = _header(headers, "X-Lark-Signature")
        if not timestamp or not nonce or not received:
            raise FeishuWebhookError("missing Feishu request signature headers")
        try:
            timestamp_value = float(timestamp)
        except ValueError as exc:
            raise FeishuWebhookError("invalid Feishu request timestamp") from exc
        if not math.isfinite(timestamp_value) or abs(time.time() - timestamp_value) > self.max_clock_skew_seconds:
            raise FeishuWebhookError("Feishu request timestamp is outside the allowed window")
        expected = _signature(
            timestamp=timestamp,
            nonce=nonce,
            encrypt_key=self.encrypt_key,
            raw_body=raw_body,
        )
        if not hmac.compare_digest(expected, received):
            raise FeishuWebhookError("invalid Feishu request signature")

    def _decode_payload(
        self,
        raw_body: bytes,
        payload: Mapping[str, object],
        headers: Mapping[str, str],
        *,
        verify_signature: bool = True,
    ) -> Mapping[str, object]:
        if verify_signature:
            self._verify_signature(raw_body, headers)
        encrypted = payload.get("encrypt")
        if encrypted is None:
            return payload
        if self.decryptor is None:
            raise FeishuWebhookError("encrypted Feishu event requires an injected decryptor")
        decrypted = self.decryptor(str(encrypted))
        if isinstance(decrypted, Mapping):
            return decrypted
        try:
            decoded = json.loads(bytes(decrypted))
        except (TypeError, ValueError) as exc:
            raise FeishuWebhookError("Feishu decryptor did not return a JSON object") from exc
        result = _mapping(decoded)
        if not result:
            raise FeishuWebhookError("Feishu decryptor did not return a JSON object")
        return result

    def _verify_token(self, payload: Mapping[str, object], *, required: bool) -> None:
        if self.verification_token is None:
            if required:
                raise FeishuWebhookError("Feishu verification token is not configured")
            return
        incoming = _payload_token(payload)
        if incoming is None:
            if required:
                raise FeishuWebhookError("missing Feishu verification token")
            return
        if not hmac.compare_digest(self.verification_token, incoming):
            raise FeishuWebhookError("invalid Feishu verification token")

    @staticmethod
    def _ignored_reason(payload: Mapping[str, object]) -> str | None:
        """Return a stable ACK reason for events outside the text MVP.

        Feishu sends many event kinds to one subscription.  They are valid
        authenticated callbacks, so acknowledging them avoids provider
        retries; they must not reach the text gateway where they would look
        like malformed messages.
        """

        header = _mapping(payload.get("header"))
        event_type = payload.get("event_type") or header.get("event_type")
        if event_type is not None and str(event_type).strip() not in {"", "im.message.receive_v1"}:
            return "unsupported_event_type"
        event = _mapping(payload.get("event"))
        message = _mapping(event.get("message")) or _mapping(payload.get("message")) or payload
        message_type = message.get("message_type") or message.get("messageType") or message.get("type")
        if message_type is not None and str(message_type).strip().lower() not in {"", "text"}:
            return "unsupported_message_type"
        chat_type = message.get("chat_type") or message.get("chatType")
        if chat_type is not None and str(chat_type).strip().lower() in {"thread", "topic", "topic_group"}:
            return "thread_not_supported"
        if any(message.get(key) is not None for key in ("parent_id", "parentId", "root_id", "rootId")):
            return "reply_not_supported"
        return None

    async def handle(
        self,
        raw_body: bytes | bytearray | str | Mapping[str, object],
        headers: Mapping[str, str] | None = None,
    ) -> FeishuWebhookResult:
        """Validate one request and dispatch it to the text gateway."""

        prepared = self.prepare(raw_body, headers)
        if isinstance(prepared, FeishuWebhookResult):
            return prepared
        return await self.dispatch(prepared)

    def prepare(
        self,
        raw_body: bytes | bytearray | str | Mapping[str, object],
        headers: Mapping[str, str] | None = None,
    ) -> FeishuWebhookResult | FeishuWebhookDispatch:
        """Authenticate an event without starting Agent execution.

        URL verification and ignored event types return a final result. A
        supported text event returns an authenticated dispatch envelope that
        a host can enqueue before acknowledging the provider request.
        """

        headers = headers or {}
        raw, envelope = _json_body(raw_body)
        # URL verification is a special handshake.  Feishu explicitly does
        # not apply event signature validation to this request; when Encrypt
        # Key is enabled, the outer envelope is decrypted first and the
        # challenge/token are checked on the inner object.
        if envelope.get("type") == "url_verification":
            payload = envelope
        elif envelope.get("encrypt") is not None:
            signature_headers_present = all(
                _header(headers, name)
                for name in (
                    "X-Lark-Request-Timestamp",
                    "X-Lark-Request-Nonce",
                    "X-Lark-Signature",
                )
            )
            payload = self._decode_payload(raw, envelope, headers, verify_signature=signature_headers_present)
            if not signature_headers_present and payload.get("type") != "url_verification":
                self._verify_signature(raw, headers)
        else:
            payload = self._decode_payload(raw, envelope, headers)

        if payload.get("type") == "url_verification":
            self._verify_token(payload, required=True)
            challenge = payload.get("challenge")
            if not isinstance(challenge, str) or not challenge:
                raise FeishuWebhookError("Feishu URL verification is missing challenge")
            return FeishuWebhookResult(200, {"challenge": challenge})

        # With an encrypt key, the signature authenticates the raw body. With
        # token-only mode, require the Verification Token on normal events.
        self._verify_token(payload, required=self.encrypt_key is None)
        if ignored := self._ignored_reason(payload):
            return FeishuWebhookResult(200, {"status": "ignored", "reason": ignored})

        return FeishuWebhookDispatch(payload)

    async def dispatch(self, prepared: FeishuWebhookDispatch) -> FeishuWebhookResult:
        """Run one previously authenticated event through the Agent gateway."""

        try:
            outcome = await self.gateway.handle_event(prepared.payload)
        except ValueError:
            # The adapter may reject an authenticated but incomplete payload
            # (for example a provider event shape outside this MVP).  It is a
            # valid callback from the transport's perspective, so ACK it
            # without exposing exception text or causing a retry loop.
            return FeishuWebhookResult(200, {"status": "ignored", "reason": "unsupported_payload"})
        if outcome is None:
            return FeishuWebhookResult(200, {"status": "duplicate"})
        status_code = 503 if outcome.status.value in {"history_failed", "gate_failed"} else 200
        return FeishuWebhookResult(status_code, {"status": outcome.status.value})


class FeishuWebhookHost:
    """Bounded background dispatcher for a validated webhook connector.

    The host performs authentication in :meth:`receive`, schedules Agent work
    and returns a provider-facing 200 immediately. It intentionally does not
    import FastAPI or NoneBot; a framework route only needs to read raw bytes,
    call ``receive`` and translate :class:`FeishuWebhookError` to its HTTP
    error response.

    This is an in-process queue. A production deployment should replace it
    with a durable queue before relying on delivery across restarts or
    multiple workers.
    """

    def __init__(
        self,
        connector: FeishuWebhookConnector,
        *,
        max_pending: int = 64,
        on_result: DispatchResultHandler | None = None,
    ) -> None:
        if max_pending < 1:
            raise ValueError("max_pending must be positive")
        self.connector = connector
        self.max_pending = max_pending
        self._on_result = on_result
        self._tasks: set[asyncio.Task[None]] = set()

    @property
    def pending_count(self) -> int:
        """Return the number of Agent dispatches still running."""

        return len(self._tasks)

    async def receive(
        self,
        raw_body: bytes | bytearray | str | Mapping[str, object],
        headers: Mapping[str, str] | None = None,
    ) -> FeishuWebhookResult:
        """Authenticate, enqueue and immediately acknowledge one request."""

        prepared = self.connector.prepare(raw_body, headers)
        if isinstance(prepared, FeishuWebhookResult):
            return prepared
        if len(self._tasks) >= self.max_pending:
            return FeishuWebhookResult(503, {"status": "overloaded"})
        task = asyncio.create_task(self._run(prepared), name="frontier-feishu-event")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return FeishuWebhookResult(200, {"status": "accepted"})

    async def _run(self, prepared: FeishuWebhookDispatch) -> None:
        try:
            result = await self.connector.dispatch(prepared)
        except Exception as error:  # pragma: no cover - defensive task boundary
            _logger.error("Feishu background dispatch failed: %s", type(error).__name__)
            return
        if self._on_result is None:
            return
        try:
            callback_result = self._on_result(result)
            if inspect.isawaitable(callback_result):
                await callback_result
        except Exception as error:  # pragma: no cover - metrics/logging callback
            _logger.warning("Feishu dispatch result callback failed: %s", type(error).__name__)

    async def close(self) -> None:
        """Cancel and settle in-process dispatches during application shutdown."""

        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()


__all__ = [
    "FeishuWebhookConnector",
    "FeishuWebhookDispatch",
    "FeishuWebhookError",
    "FeishuWebhookHost",
    "FeishuWebhookResult",
]
