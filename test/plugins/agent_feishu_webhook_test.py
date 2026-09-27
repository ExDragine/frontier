"""Security and transport contract tests for the Feishu webhook boundary."""

# ruff: noqa: S101, S106

import asyncio
import hashlib
import time
from types import SimpleNamespace

import pytest

from plugins.agent.adapters.feishu_webhook import (
    FeishuWebhookConnector,
    FeishuWebhookError,
    FeishuWebhookHost,
)


def _signed_body(payload, *, encrypt_key, timestamp=None, nonce="nonce-1"):
    timestamp = str(timestamp or int(time.time()))
    import json

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    signature = hashlib.sha256(
        timestamp.encode() + nonce.encode() + encrypt_key.encode() + body
    ).hexdigest()
    headers = {
        "X-Lark-Request-Timestamp": timestamp,
        "X-Lark-Request-Nonce": nonce,
        "X-Lark-Signature": signature,
    }
    return body, headers


class FakeGateway:
    def __init__(self, outcome=None):
        self.events = []
        self.outcome = outcome

    async def handle_event(self, event):
        self.events.append(event)
        return self.outcome


class RejectingGateway(FakeGateway):
    async def handle_event(self, event):
        self.events.append(event)
        raise ValueError("provider payload is incomplete")


class BlockingGateway(FakeGateway):
    def __init__(self, outcome=None):
        super().__init__(outcome)
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def handle_event(self, event):
        self.started.set()
        await self.release.wait()
        return await super().handle_event(event)


@pytest.mark.asyncio
async def test_url_verification_returns_challenge_after_token_check():
    gateway = FakeGateway()
    connector = FeishuWebhookConnector(gateway, verification_token="verify-token")

    result = await connector.handle(
        {"type": "url_verification", "token": "verify-token", "challenge": "challenge-1"}
    )

    assert result.status_code == 200
    assert result.body == {"challenge": "challenge-1"}
    assert gateway.events == []


@pytest.mark.asyncio
async def test_token_only_event_requires_matching_verification_token():
    gateway = FakeGateway()
    connector = FeishuWebhookConnector(gateway, verification_token="verify-token")
    payload = {"token": "wrong", "event": {"message": {}}}

    with pytest.raises(FeishuWebhookError, match="verification token"):
        await connector.handle(payload)
    assert gateway.events == []


@pytest.mark.asyncio
async def test_signed_event_uses_raw_body_and_dispatches_once():
    gateway = FakeGateway(SimpleNamespace(status=SimpleNamespace(value="accepted")))
    connector = FeishuWebhookConnector(gateway, encrypt_key="encrypt-key")
    payload = {"header": {"event_id": "evt-1"}, "event": {"message": {}}}
    body, headers = _signed_body(payload, encrypt_key="encrypt-key")

    result = await connector.handle(body, headers)

    assert result.status_code == 200
    assert result.body == {"status": "accepted"}
    assert gateway.events == [payload]


@pytest.mark.asyncio
async def test_signature_covers_exact_raw_body_bytes():
    gateway = FakeGateway(SimpleNamespace(status=SimpleNamespace(value="accepted")))
    connector = FeishuWebhookConnector(gateway, encrypt_key="encrypt-key")
    body = b'{ "event": { "message": {} }, "header": { "event_id": "evt-raw" } }'
    timestamp = str(int(time.time()))
    nonce = "nonce-raw"
    signature = hashlib.sha256(
        timestamp.encode() + nonce.encode() + b"encrypt-key" + body
    ).hexdigest()

    result = await connector.handle(
        body,
        {
            "X-Lark-Request-Timestamp": timestamp,
            "X-Lark-Request-Nonce": nonce,
            "X-Lark-Signature": signature,
        },
    )

    assert result.body == {"status": "accepted"}
    assert gateway.events == [{"event": {"message": {}}, "header": {"event_id": "evt-raw"}}]


@pytest.mark.asyncio
async def test_invalid_signature_and_stale_timestamp_are_rejected():
    gateway = FakeGateway()
    connector = FeishuWebhookConnector(gateway, encrypt_key="encrypt-key")
    payload = {"event": {"message": {}}}
    body, headers = _signed_body(payload, encrypt_key="encrypt-key")
    headers["X-Lark-Signature"] = "bad"
    with pytest.raises(FeishuWebhookError, match="signature"):
        await connector.handle(body, headers)

    stale_body, stale_headers = _signed_body(payload, encrypt_key="encrypt-key", timestamp=int(time.time()) - 301)
    with pytest.raises(FeishuWebhookError, match="timestamp"):
        await connector.handle(stale_body, stale_headers)


@pytest.mark.asyncio
async def test_encrypted_payload_uses_injected_decryptor_before_challenge():
    gateway = FakeGateway()
    connector = FeishuWebhookConnector(
        gateway,
        verification_token="verify-token",
        encrypt_key="encrypt-key",
        decryptor=lambda value: {
            "type": "url_verification",
            "token": "verify-token",
            "challenge": f"{value}-challenge",
        },
    )
    body, headers = _signed_body({"encrypt": "ciphertext"}, encrypt_key="encrypt-key")

    result = await connector.handle(body, headers)

    assert result.body == {"challenge": "ciphertext-challenge"}


def test_connector_requires_at_least_one_security_secret():
    with pytest.raises(ValueError, match="verification_token or encrypt_key"):
        FeishuWebhookConnector(FakeGateway())


def test_signature_fixed_vector_matches_feishu_concatenation():
    timestamp = "1700000000"
    nonce = "nonce"
    encrypt_key = "key"
    body = b'{"type":"event_callback"}'
    expected = "dd754c270c3bff81381a71e16203226097965307de78c04ffaa65398a401ccae"

    # Keep this vector independent of the connector helper so a shared
    # implementation bug cannot make the test pass.
    assert hashlib.sha256(timestamp.encode() + nonce.encode() + encrypt_key.encode() + body).hexdigest() == expected


@pytest.mark.asyncio
async def test_encrypted_url_verification_does_not_require_signature_headers():
    gateway = FakeGateway()
    connector = FeishuWebhookConnector(
        gateway,
        verification_token="verify-token",
        encrypt_key="encrypt-key",
        decryptor=lambda _value: {
            "type": "url_verification",
            "token": "verify-token",
            "challenge": "challenge-encrypted",
        },
    )

    result = await connector.handle(b'{"encrypt":"ciphertext"}')

    assert result.status_code == 200
    assert result.body == {"challenge": "challenge-encrypted"}


@pytest.mark.asyncio
async def test_encrypt_key_only_mode_rejects_url_verification_without_token_configured():
    connector = FeishuWebhookConnector(
        FakeGateway(),
        encrypt_key="encrypt-key",
        decryptor=lambda _value: {
            "type": "url_verification",
            "token": "provider-token",
            "challenge": "challenge",
        },
    )

    with pytest.raises(FeishuWebhookError, match="verification token is not configured"):
        await connector.handle(b'{"encrypt":"ciphertext"}')


@pytest.mark.asyncio
async def test_unsupported_events_are_acknowledged_without_gateway_dispatch():
    gateway = FakeGateway()
    connector = FeishuWebhookConnector(gateway, verification_token="verify-token")

    result = await connector.handle(
        {
            "token": "verify-token",
            "header": {"event_type": "im.message.message_read_v1"},
        }
    )

    assert result.status_code == 200
    assert result.body == {"status": "ignored", "reason": "unsupported_event_type"}
    assert gateway.events == []


@pytest.mark.asyncio
async def test_authenticated_unsupported_payload_is_acknowledged_without_error_text():
    gateway = RejectingGateway()
    connector = FeishuWebhookConnector(gateway, verification_token="verify-token")

    result = await connector.handle({"token": "verify-token", "event": {"message": {}}})

    assert result.status_code == 200
    assert result.body == {"status": "ignored", "reason": "unsupported_payload"}
    assert gateway.events == [{"token": "verify-token", "event": {"message": {}}}]


@pytest.mark.asyncio
async def test_webhook_host_acknowledges_before_agent_dispatch_finishes():
    gateway = BlockingGateway(SimpleNamespace(status=SimpleNamespace(value="accepted")))
    connector = FeishuWebhookConnector(gateway, verification_token="verify-token")
    results = []
    host = FeishuWebhookHost(connector, on_result=results.append)

    result = await host.receive({"token": "verify-token", "event": {"message": {}}})

    assert result.body == {"status": "accepted"}
    assert host.pending_count == 1
    await asyncio.wait_for(gateway.started.wait(), timeout=1)
    assert gateway.events == []

    gateway.release.set()
    for _ in range(20):
        if host.pending_count == 0:
            break
        await asyncio.sleep(0)
    assert gateway.events == [{"token": "verify-token", "event": {"message": {}}}]
    assert results and results[0].body == {"status": "accepted"}
    await host.close()


@pytest.mark.asyncio
async def test_webhook_host_applies_pending_limit_and_cleans_up_tasks():
    gateway = BlockingGateway(SimpleNamespace(status=SimpleNamespace(value="accepted")))
    connector = FeishuWebhookConnector(gateway, verification_token="verify-token")
    host = FeishuWebhookHost(connector, max_pending=1)
    payload = {"token": "verify-token", "event": {"message": {}}}

    first = await host.receive(payload)
    second = await host.receive(payload)

    assert first.status_code == 200
    assert second.status_code == 503
    assert second.body == {"status": "overloaded"}
    await host.close()
    assert host.pending_count == 0
