# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from utils.agent_context import FrontierRuntimeContext
from utils.configs import SpeechSynthesisConfig
from utils.media_access import MEDIA_ACCESS_DENIED
from utils.speech_synthesis import SpeechSynthesisError, SynthesizedSpeech


@pytest.fixture
def speech_tool(load_tool_module, monkeypatch):
    module = load_tool_module("speech")
    monkeypatch.setattr(module.EnvConfig, "SPEECH_SYNTHESIS", SpeechSynthesisConfig(enabled=True))
    monkeypatch.setattr(module.EnvConfig, "PAINT_WHITELIST_MODE", False)
    return module


@pytest.mark.asyncio
async def test_voice_is_an_automatic_artifact_without_an_extra_platform_send(speech_tool, monkeypatch):
    async def synthesize(text, *, settings):
        assert text == "你好" and settings.enabled
        return SynthesizedSpeech(b"wav", b"silk", 0.2, 0.3)

    monkeypatch.setattr(speech_tool, "synthesize_speech", synthesize)
    message, artifact = await speech_tool.get_speech("你好", config={"configurable": {"user_id": "123"}})
    assert "自动发送" in message and artifact is not None


@pytest.mark.asyncio
async def test_disabled_and_untrusted_identity_never_infer(speech_tool, monkeypatch):
    async def unexpected(*_args, **_kwargs):
        pytest.fail("denied or disabled synthesis must not run")

    monkeypatch.setattr(speech_tool, "synthesize_speech", unexpected)
    monkeypatch.setattr(speech_tool.EnvConfig, "PAINT_WHITELIST_MODE", True)
    monkeypatch.setattr(speech_tool.EnvConfig, "PAINT_WHITELIST_PERSON_LIST", [123])
    frozen_runtime = SimpleNamespace(context=FrontierRuntimeContext("456", 0, None, "."))
    text, artifact = await speech_tool.get_speech(
        "你好",
        config={"configurable": {"user_id": "123"}},
        runtime=frozen_runtime,
    )
    assert text == MEDIA_ACCESS_DENIED and artifact is None
    monkeypatch.setattr(speech_tool.EnvConfig, "SPEECH_SYNTHESIS", SpeechSynthesisConfig())
    assert (await speech_tool.get_speech("你好"))[1] is None


@pytest.mark.asyncio
async def test_error_code_is_safe_and_has_no_artifact(speech_tool, monkeypatch):
    async def failure(*_args, **_kwargs):
        raise SpeechSynthesisError("timeout")

    monkeypatch.setattr(speech_tool, "synthesize_speech", failure)
    text, artifact = await speech_tool.get_speech("你好")
    assert "timeout" in text and artifact is None


@pytest.mark.asyncio
async def test_voice_has_its_own_user_rate_limit(speech_tool, monkeypatch):
    calls = []

    async def synthesize(*_args, **_kwargs):
        calls.append(True)
        return SynthesizedSpeech(b"wav", b"silk", 0.2, 0.3)

    monkeypatch.setattr(speech_tool, "synthesize_speech", synthesize)
    monkeypatch.setattr(
        speech_tool.EnvConfig,
        "SPEECH_SYNTHESIS",
        SpeechSynthesisConfig(
            enabled=True,
            rate_limit_max_requests=1,
        ),
    )
    await speech_tool.get_speech("你好", config={"configurable": {"user_id": "123"}})
    text, artifact = await speech_tool.get_speech("你好", config={"configurable": {"user_id": "123"}})
    assert "频繁" in text and artifact is None and len(calls) == 1


def test_model_cannot_set_identity_runtime_or_model_paths(speech_tool):
    assert not {"runtime", "user_id", "group_id", "model_dir"} & set(speech_tool.get_speech.args)
