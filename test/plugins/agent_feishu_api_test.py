# ruff: noqa: S101, S106
"""Contract tests for the SDK-free Feishu Open API sender."""

import asyncio
from dataclasses import dataclass

import pytest

from plugins.agent.adapters.feishu_api import FeishuApiClient, FeishuApiError
from utils.agent_protocol import ConversationRef


@dataclass
class Response:
    payload: object
    status_code: int = 200

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class Client:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def _group():
    return ConversationRef(
        platform="feishu",
        account_id="app-1",
        kind="group",
        conversation_id="oc_group",
    )


@pytest.mark.asyncio
async def test_sender_fetches_token_once_and_maps_text_message():
    client = Client(
        [
            Response({"code": 0, "tenant_access_token": "tenant-token", "expire": 7200}),
            Response({"code": 0, "data": {"message_id": "om-1"}}),
            Response({"code": 0, "data": {"message_id": "om-2"}}),
        ]
    )
    now = [100.0]
    api = FeishuApiClient(
        app_id="cli-app",
        app_secret="app-secret",
        http_client=client,
        clock=lambda: now[0],
    )

    first = await api.send_text(_group(), "你好 🌏")
    second = await api.send_text(_group(), "第二条")

    assert first == {"status": "delivered", "message_id": "om-1"}
    assert second == {"status": "delivered", "message_id": "om-2"}
    assert len(client.calls) == 3
    token_url, token_kwargs = client.calls[0]
    assert token_url.endswith("/auth/v3/tenant_access_token/internal")
    assert token_kwargs["json"] == {"app_id": "cli-app", "app_secret": "app-secret"}
    send_url, send_kwargs = client.calls[1]
    assert send_url.endswith("/im/v1/messages")
    assert send_kwargs["params"] == {"receive_id_type": "chat_id"}
    assert send_kwargs["headers"] == {
        "Authorization": "Bearer tenant-token",
        "Content-Type": "application/json; charset=utf-8",
    }
    assert send_kwargs["json"]["receive_id"] == "oc_group"
    assert send_kwargs["json"]["msg_type"] == "text"
    assert send_kwargs["json"]["content"] == '{"text":"你好 🌏"}'


@pytest.mark.asyncio
async def test_token_refresh_is_single_flight_and_expiry_margin_is_honored():
    started = asyncio.Event()
    release = asyncio.Event()

    class SlowClient(Client):
        async def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            if len(self.calls) == 1:
                started.set()
                await release.wait()
            return self.responses.pop(0)

    client = SlowClient([Response({"code": 0, "tenant_access_token": "token", "expire": 100})])
    now = [100.0]
    api = FeishuApiClient(
        app_id="cli-app",
        app_secret="app-secret",
        http_client=client,
        token_refresh_margin_seconds=10,
        clock=lambda: now[0],
    )
    first = asyncio.create_task(api.tenant_access_token())
    await asyncio.wait_for(started.wait(), timeout=1)
    second = asyncio.create_task(api.tenant_access_token())
    await asyncio.sleep(0)
    assert len(client.calls) == 1
    release.set()
    assert await first == await second == "token"

    now[0] = 191.0
    client.responses.append(Response({"code": 0, "tenant_access_token": "token-2", "expire": 100}))
    assert await api.tenant_access_token() == "token-2"
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_sender_rejects_unsupported_targets_and_invalid_api_responses():
    client = Client([Response({"code": 0, "tenant_access_token": "token", "expire": 7200})])
    api = FeishuApiClient(app_id="cli-app", app_secret="app-secret", http_client=client)
    direct = ConversationRef("feishu", "app-1", "direct", "ou-user")
    thread = ConversationRef("feishu", "app-1", "thread", "oc-group", parent_id="om-root")
    with pytest.raises(ValueError, match="only handles feishu"):
        await api.send_text(ConversationRef("qq", "bot", "group", "123"), "hello")
    with pytest.raises(ValueError, match="direct or group"):
        await api.send_text(thread, "hello")
    with pytest.raises(ValueError, match="must not be empty"):
        await api.send_text(direct, " ")
    with pytest.raises(ValueError, match="conversation_id"):
        await api.send_text(ConversationRef("feishu", "app-1", "direct", " "), "hello")

    bad_client = Client([Response({"code": 99, "msg": "bad", "secret": "must-not-leak"})])
    bad_api = FeishuApiClient(app_id="cli-app", app_secret="app-secret", http_client=bad_client)
    with pytest.raises(FeishuApiError) as error:
        await bad_api.tenant_access_token()
    assert "app-secret" not in str(error.value)


@pytest.mark.asyncio
async def test_sender_invalidates_cached_token_on_auth_failure_without_retry():
    client = Client(
        [
            Response({"code": 0, "tenant_access_token": "token", "expire": 7200}),
            Response({"code": 0, "data": {}}, status_code=401),
        ]
    )
    api = FeishuApiClient(app_id="cli-app", app_secret="app-secret", http_client=client)
    with pytest.raises(FeishuApiError):
        await api.send_text(_group(), "hello")
    assert api.token_cached is False
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_token_response_requires_code_token_and_positive_expiry():
    for payload in (
        {"tenant_access_token": "token", "expire": 7200},
        {"code": 0, "expire": 7200},
        {"code": 0, "tenant_access_token": "token", "expire": 0},
    ):
        api = FeishuApiClient(
            app_id="cli-app",
            app_secret="app-secret",
            http_client=Client([Response(payload)]),
        )
        with pytest.raises(FeishuApiError):
            await api.tenant_access_token()
