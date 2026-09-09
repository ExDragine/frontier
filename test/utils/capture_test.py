# ruff: noqa: S101

import asyncio

import pytest

from utils.agents.capture import BrowserCaptureIntent, detect_browser_capture_intent


@pytest.mark.asyncio
@pytest.mark.parametrize("text", [None, "你好", "北京明天天气怎么样", "帮我算 5 + 3", "总结 https://example.com"])
async def test_ordinary_chat_does_not_call_capture_signal(monkeypatch, text):
    from utils import signal_llm

    async def reject(**_kwargs):
        raise AssertionError("ordinary chat should not call Signal")

    monkeypatch.setattr(signal_llm, "signal_structured", reject)
    assert await detect_browser_capture_intent(text) == set()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    ["帮我截一下这个站", "看看 GitHub 首页什么样", "打开 example.com 看看", "把网页录下来", "screenshot this page"],
)
async def test_capture_candidates_still_require_signal_authorization(monkeypatch, text):
    from utils import signal_llm

    calls = []

    async def signal(**kwargs):
        calls.append(kwargs["user_prompt"])
        return BrowserCaptureIntent(screenshot=True, recording=False)

    monkeypatch.setattr(signal_llm, "signal_structured", signal)
    assert await detect_browser_capture_intent(text) == {"webpage_screenshot"}
    assert calls == [text]


@pytest.mark.asyncio
async def test_candidate_match_cannot_bypass_signal_denial(monkeypatch):
    from utils import signal_llm

    async def signal(**_kwargs):
        return BrowserCaptureIntent(screenshot=False, recording=False)

    monkeypatch.setattr(signal_llm, "signal_structured", signal)
    assert await detect_browser_capture_intent("你看这个截图的报错") == set()


@pytest.mark.asyncio
async def test_capture_cancellation_propagates(monkeypatch):
    from utils import signal_llm

    async def signal(**_kwargs):
        raise asyncio.CancelledError

    monkeypatch.setattr(signal_llm, "signal_structured", signal)
    with pytest.raises(asyncio.CancelledError):
        await detect_browser_capture_intent("截图这个站")
