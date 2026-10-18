# ruff: noqa: S101

import asyncio
import hashlib
import io
import json
import sys
import wave
from pathlib import Path

import pytest

from utils import moss_tts_assets as assets
from utils import speech_synthesis as speech
from utils.configs import EnvConfig, SpeechSynthesisConfig, parse_config


def _wav(seconds=0.2, sample_rate=48000):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\0\0\0\0" * int(seconds * sample_rate))
    return output.getvalue()


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setattr(speech, "speech_inference_lock", asyncio.Lock())
    monkeypatch.setattr(speech, "verify_installation", lambda _root: None)
    return SpeechSynthesisConfig(enabled=True, auto_download=False, model_dir=str(tmp_path))


def test_synthesis_opt_in_config_validation_and_reload():
    assert not parse_config({"config_version": 2}).speech_synthesis.enabled
    EnvConfig.reload({"config_version": 2, "speech_synthesis": {"enabled": True, "max_cpu_cores": 2}})
    assert EnvConfig.SPEECH_SYNTHESIS.enabled and EnvConfig.SPEECH_SYNTHESIS.max_cpu_cores == 2
    for invalid in ({"voice": "unknown"}, {"max_cpu_cores": 0}, {"timeout_seconds": 0}, {"unknown": True}):
        with pytest.raises(ValueError):
            parse_config({"config_version": 2, "speech_synthesis": invalid})


@pytest.mark.asyncio
async def test_synthesis_returns_real_bytes_and_cleans_temporary_files(settings, monkeypatch):
    directories = []

    async def run(args, *, cores):
        assert args[:2] == [sys.executable, str(speech._WORKER)]
        request = Path(args[2])
        payload = json.loads(request.read_text(encoding="utf-8"))
        assert payload["text"] == "你好" and payload["max_cpu_cores"] == cores == 4
        assert payload["model_dir"] == settings.model_dir
        directories.append(request.parent)
        (request.parent / "output.wav").write_bytes(_wav())
        (request.parent / "output.silk").write_bytes(b"\x02#!SILK_V3payload")
        return b""

    monkeypatch.setattr(speech, "_run_process", run)
    result = await speech.synthesize_speech("  你好  ", settings=settings)
    assert result.wav == _wav() and result.silk.startswith(b"\x02#!SILK_V3")
    assert result.audio_seconds == pytest.approx(0.2)
    assert not directories[0].exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, update, code",
    [
        ("", {}, "empty_text"),
        ("   ", {}, "empty_text"),
        ("测试", {"max_text_chars": 1}, "text_limit"),
        ("测试", {"enabled": False}, "disabled"),
    ],
)
async def test_invalid_requests_do_not_load_model(settings, monkeypatch, text, update, code):
    def unexpected(_root):
        pytest.fail("invalid request must not access model")

    monkeypatch.setattr(speech, "verify_installation", unexpected)
    with pytest.raises(speech.SpeechSynthesisError, match=code):
        await speech.synthesize_speech(text, settings=settings.model_copy(update=update))


@pytest.mark.asyncio
async def test_timeout_includes_asr_queue_wait(settings):
    from utils import speech_recognition
    from utils.speech_resources import speech_inference_lock

    assert speech_recognition._recognition_lock is speech_inference_lock
    async with speech.speech_inference_lock:
        with pytest.raises(speech.SpeechSynthesisError, match="timeout"):
            await speech.synthesize_speech("你好", settings=settings.model_copy(update={"timeout_seconds": 0.01}))


@pytest.mark.asyncio
async def test_worker_failure_is_sanitized(settings, monkeypatch):
    async def run(*_args, **_kwargs):
        raise speech.SpeechRecognitionError("runtime_failed")

    monkeypatch.setattr(speech, "_run_process", run)
    with pytest.raises(speech.SpeechSynthesisError, match="runtime_failed"):
        await speech.synthesize_speech("你好", settings=settings)


@pytest.mark.asyncio
async def test_timeout_cancels_worker_before_cleaning_its_files(settings, monkeypatch):
    cancelled = []
    directories = []

    async def run(args, *, cores):
        directories.append(Path(args[2]).parent)
        try:
            await asyncio.Future()
        finally:
            assert directories[0].exists()
            cancelled.append(True)

    monkeypatch.setattr(speech, "_run_process", run)
    with pytest.raises(speech.SpeechSynthesisError, match="timeout"):
        await speech.synthesize_speech("你好", settings=settings.model_copy(update={"timeout_seconds": 0.1}))
    assert cancelled and not directories[0].exists()


@pytest.mark.asyncio
async def test_unverified_model_never_executes(settings, monkeypatch):
    def verify(_root):
        raise ValueError("private path and body")

    monkeypatch.setattr(speech, "verify_installation", verify)
    with pytest.raises(speech.SpeechSynthesisError, match="^runtime_missing_or_unverified$"):
        await speech.synthesize_speech("你好", settings=settings)


@pytest.mark.parametrize(
    "wav, silk, code",
    [
        (_wav(1.01), b"\x02#!SILK_V3data", "audio_duration_limit"),
        (_wav(sample_rate=16000), b"\x02#!SILK_V3data", "invalid_audio"),
        (_wav(), b"not silk", "invalid_audio"),
        (_wav()[:-4], b"\x02#!SILK_V3data", "invalid_audio"),
    ],
    ids=["too-long", "wrong-rate", "wrong-silk", "truncated-wav"],
)
def test_audio_validation_rejects_invalid_or_partial_output(tmp_path, wav, silk, code):
    (tmp_path / "output.wav").write_bytes(wav)
    (tmp_path / "output.silk").write_bytes(silk)
    with pytest.raises(speech.SpeechSynthesisError, match=code):
        speech._read_audio(tmp_path, 1)


def test_pinned_model_code_and_audio_adapter_are_verified(tmp_path, monkeypatch):
    model_dir = tmp_path / "MOSS-TTS-Nano-100M"
    model_dir.mkdir()
    original = b"import torchaudio\n"
    assets.original_path(tmp_path, assets.MODEL_CODE).write_bytes(original)
    monkeypatch.setattr(
        assets,
        "assets",
        lambda: [
            {
                "file": assets.MODEL_CODE,
                "sha256": hashlib.sha256(original).hexdigest(),
            }
        ],
    )
    assets.prepare_audio_adapter(tmp_path)
    assets.verify_installation(tmp_path)
    (tmp_path / assets.MODEL_CODE).write_bytes(b"changed code")
    with pytest.raises(ValueError, match="patch mismatch"):
        assets.verify_installation(tmp_path)


def test_pinned_manifest_uses_native_weights_and_immutable_revisions():
    manifest = json.loads(assets.MANIFEST.read_text(encoding="utf-8"))
    assert all(len(revision) == 40 for revision in manifest["model_revisions"].values())
    assert any(asset["file"].endswith("pytorch_model.bin") for asset in manifest["assets"])
    assert not any("onnx" in asset["file"].lower() for asset in manifest["assets"])
    assert all(len(asset["sha256"]) == 64 and "/main/" not in asset["url"] for asset in manifest["assets"])
