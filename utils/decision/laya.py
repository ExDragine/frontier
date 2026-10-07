"""Laya decision provider.

Laya is intentionally kept behind this adapter.  The rest of Frontier only
sees ``DecisionResult`` and never imports torch, transformers, or the Laya
SDK.  Both the in-process SDK and the compatible ``/v1/systemone`` HTTP
server are supported.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Mapping
from typing import Any, cast

from .models import DecisionQuestions, DecisionResult, DecisionState
from .validation import validate_answers, validate_questions


class LayaProviderError(RuntimeError):
    """Raised when Laya cannot produce a valid typed decision."""


def _as_mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LayaProviderError(f"Laya response field {name!r} must be an object")
    return value


def _normalize_payload(payload: object, *, questions: DecisionQuestions, provider: str, latency_ms: float) -> DecisionResult:
    body = _as_mapping(payload, name="response")
    answers = _as_mapping(body.get("answers", {}), name="answers")
    normalized_answers: dict[str, Mapping[str, Any]] = {}
    for question_id, answer in answers.items():
        item = dict(_as_mapping(answer, name=f"answers.{question_id}"))
        if item.get("type") != "refusal":
            expected = questions.get(question_id, {}).get("type")
            item.setdefault("type", "noul" if expected == "predicate" else expected)
            if item["type"] == "noul":
                item["type"] = "predicate"
                value = item.pop("noul", None)
                item["probability"] = float(value) if isinstance(value, bool) else value
            if "answer_confidence" in item:
                item["confidence"] = item.pop("answer_confidence")
        normalized_answers[question_id] = item
    try:
        normalized_answers = validate_answers(normalized_answers, questions)
    except ValueError as error:
        raise LayaProviderError(str(error)) from error
    routing = body.get("routing", {})
    usage = body.get("usage", {})
    return DecisionResult(
        answers=normalized_answers,
        provider=provider,
        latency_ms=latency_ms,
        routing=_as_mapping(routing, name="routing"),
        usage=_as_mapping(usage, name="usage"),
        raw=body,
    )


class LayaDecisionProvider:
    """Run Laya locally or through a Laya-compatible HTTP endpoint.

    ``router`` and ``http_client`` are injectable for tests.  The SDK import
    and router construction are lazy, so importing this class never downloads
    model weights even though the SDK is installed with the project.
    """

    def __init__(
        self,
        *,
        model: str = "auto",
        device: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 10.0,
        preload: bool = False,
        router: object | None = None,
        http_client: object | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if base_url is not None and not base_url.strip():
            raise ValueError("base_url must not be blank")
        self.model = model.strip()
        self.device = device.strip() if device and device.strip() else None
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.timeout = float(timeout)
        self.preload = preload
        self._router = router
        self._router_lock = asyncio.Lock()
        self._http_client = http_client

    async def decide(self, state: DecisionState, questions: DecisionQuestions) -> DecisionResult:
        """Answer ``questions`` and normalize the SDK or HTTP response."""

        validate_questions(questions)
        wire_questions = {
            name: {**question, "type": "noul" if question["type"] == "predicate" else question["type"]}
            for name, question in questions.items()
        }
        started = time.perf_counter()
        if self.base_url:
            payload = await self._decide_http(state, wire_questions)
            provider = "laya-http"
        else:
            payload = await self._decide_local(state, wire_questions)
            provider = "laya-local"
        return _normalize_payload(
            payload,
            questions=questions,
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )

    async def _get_router(self) -> object:
        if self._router is not None:
            return self._router
        async with self._router_lock:
            if self._router is None:
                self._router = await asyncio.to_thread(self._build_router)
        return self._router

    def _build_router(self) -> object:
        try:
            from laya import Router
        except ImportError as error:
            raise LayaProviderError(
                "Laya local provider could not import the installed 'laya' package"
            ) from error
        try:
            default = "multilingual" if self.model == "auto" else self.model
            kwargs: dict[str, Any] = {"preload": self.preload, "default": default}
            if self.device is not None:
                kwargs["device"] = self.device
            return Router(**kwargs)
        except Exception as error:
            raise LayaProviderError(f"failed to initialize Laya Router: {error}") from error

    async def _decide_local(self, state: DecisionState, questions: DecisionQuestions) -> object:
        router = await self._get_router()
        predict = getattr(router, "predict", None)
        if not callable(predict):
            raise LayaProviderError("Laya router does not expose predict()")
        try:
            kwargs = {} if self.model == "auto" else {"model": self.model}
            result = await asyncio.to_thread(predict, state, dict(questions), **kwargs)
        except Exception as error:
            raise LayaProviderError(f"Laya local inference failed: {error}") from error
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _decide_http(self, state: DecisionState, questions: DecisionQuestions) -> object:
        client = cast(Any, self._http_client)
        if client is None:
            from utils.http_client import get_http_client

            client = get_http_client("laya-decision", timeout=self.timeout)
        body: dict[str, Any] = {"state": state, "questions": dict(questions)}
        if self.model != "auto":
            body["model"] = self.model
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        try:
            response = await client.post(
                f"{self.base_url}/v1/systemone",
                json=body,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            raise LayaProviderError(f"Laya HTTP inference failed: {error}") from error


__all__ = ["LayaDecisionProvider", "LayaProviderError"]
