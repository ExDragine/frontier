# ruff: noqa: S101, S106
"""Tests for the optional FastAPI transport wrapper."""

import hashlib
import json
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from plugins.agent.adapters.feishu_webhook import FeishuWebhookConnector, FeishuWebhookHost
from plugins.agent.feishu_http import mount_feishu_webhook


class Gateway:
    async def handle_event(self, _event):
        return None


def _signed_body(payload, *, encrypt_key):
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    nonce = "http-nonce"
    signature = hashlib.sha256(timestamp.encode() + nonce.encode() + encrypt_key.encode() + body).hexdigest()
    return body, {
        "X-Lark-Request-Timestamp": timestamp,
        "X-Lark-Request-Nonce": nonce,
        "X-Lark-Signature": signature,
    }


def test_mount_preserves_raw_body_for_signature_and_returns_fast_ack():
    app = FastAPI()
    host = FeishuWebhookHost(FeishuWebhookConnector(Gateway(), encrypt_key="encrypt-key"))
    mount_feishu_webhook(app, host, path="/hooks/feishu")
    body, headers = _signed_body(
        {"header": {"event_id": "http-event"}, "event": {"message": {}}},
        encrypt_key="encrypt-key",
    )

    with TestClient(app) as client:
        response = client.post("/hooks/feishu", content=body, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


def test_mount_handles_url_challenge_and_hides_route_from_schema():
    app = FastAPI()
    host = FeishuWebhookHost(FeishuWebhookConnector(Gateway(), verification_token="verify-token"))
    mount_feishu_webhook(app, host)

    with TestClient(app) as client:
        response = client.post(
            "/feishu/events",
            json={"type": "url_verification", "token": "verify-token", "challenge": "challenge"},
        )
        schema = client.get("/openapi.json").json()

    assert response.status_code == 200
    assert response.json() == {"challenge": "challenge"}
    assert "/feishu/events" not in schema["paths"]


def test_mount_does_not_echo_invalid_webhook_details():
    app = FastAPI()
    host = FeishuWebhookHost(FeishuWebhookConnector(Gateway(), verification_token="verify-token"))
    mount_feishu_webhook(app, host)

    with TestClient(app) as client:
        response = client.post("/feishu/events", json={"token": "wrong"})

    assert response.status_code == 400
    assert response.json() == {"error": "invalid_feishu_webhook"}
    assert "wrong" not in response.text


def test_mount_rejects_root_path():
    app = FastAPI()
    host = FeishuWebhookHost(FeishuWebhookConnector(Gateway(), verification_token="verify-token"))

    with pytest.raises(ValueError, match="non-root"):
        mount_feishu_webhook(app, host, path="/")
