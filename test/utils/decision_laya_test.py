# ruff: noqa: S101

import sys
from types import SimpleNamespace

import pytest

from utils.decision import (
    LayaDecisionProvider,
    LayaProviderError,
    build_reply_gate_state,
    score_reply_gate,
)


class FakeRouter:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def predict(self, state, questions, *, model=None):
        self.calls.append((state, questions, model))
        return self.payload


@pytest.mark.asyncio
async def test_laya_provider_uses_injected_local_router_without_importing_sdk():
    router = FakeRouter(
        {
            "answers": {
                "should_reply": {
                    "type": "noul",
                    "noul": 0.83,
                    "answer_confidence": 0.83,
                }
            },
            "routing": {"model": "multilingual"},
            "usage": {"input_tokens": 12, "output_tokens": 1},
        }
    )
    provider = LayaDecisionProvider(model="multilingual", router=router)

    score = await score_reply_gate(provider, "这个报错怎么解决？", [{"role": "user", "content": "你好"}])

    assert score.should_reply is True
    assert score.probability == 0.83
    assert score.decision.provider == "laya-local"
    assert router.calls[0][2] == "multilingual"
    assert "user: 这个报错怎么解决？" in router.calls[0][0]


@pytest.mark.asyncio
async def test_laya_provider_auto_mode_lets_router_choose_language():
    router = FakeRouter({"answers": {"should_reply": {"noul": 0.5}}})
    provider = LayaDecisionProvider(model="auto", router=router)

    await provider.decide("你好", {"should_reply": {"type": "noul"}})

    assert router.calls[0][2] is None


def test_laya_provider_passes_explicit_device_to_lazy_router(monkeypatch):
    captured = {}

    class Router:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setitem(sys.modules, "laya", SimpleNamespace(Router=Router))
    provider = LayaDecisionProvider(model="multilingual", device="cpu", preload=True)

    provider._build_router()

    assert captured == {"preload": True, "default": "multilingual", "device": "cpu"}


@pytest.mark.asyncio
async def test_laya_provider_http_mode_sends_jev_shape_and_auth_header():
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answers": {"should_reply": {"noul": 0.12, "confidence": 0.88}}}

    class Client:
        async def post(self, *args, **kwargs):
            calls.append((args, kwargs))
            return Response()

    provider = LayaDecisionProvider(
        model="multilingual",
        base_url="http://127.0.0.1:8000/",
        api_key="secret",
        http_client=Client(),
    )

    score = await score_reply_gate(provider, "哈哈哈")

    assert score.should_reply is False
    assert score.decision.provider == "laya-http"
    assert calls[0][0] == ("http://127.0.0.1:8000/v1/systemone",)
    assert calls[0][1]["headers"] == {"Authorization": "Bearer secret"}
    assert calls[0][1]["json"]["model"] == "multilingual"
    assert calls[0][1]["json"]["questions"]["should_reply"]["type"] == "noul"


@pytest.mark.asyncio
async def test_laya_provider_rejects_invalid_response_shape():
    provider = LayaDecisionProvider(router=FakeRouter({"answers": {"should_reply": []}}))

    with pytest.raises(LayaProviderError, match="answers.should_reply"):
        await provider.decide("hello", {"should_reply": {"type": "noul"}})


def test_build_reply_gate_state_is_bounded_and_normalizes_content():
    state = build_reply_gate_state(
        "最新问题",
        [
            {"role": "user", "content": "旧问题"},
            SimpleNamespace(role="assistant", content=[{"type": "text", "text": "旧回答"}]),
        ],
    )

    assert state == "user: 旧问题\nassistant: 旧回答\nuser: 最新问题"
