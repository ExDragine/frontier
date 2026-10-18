# ruff: noqa: S101

import asyncio
import io
import sys
import wave

import pytest

from utils import speech_recognition as speech
from utils.configs import EnvConfig, SpeechRecognitionConfig, parse_config


def _wav(seconds=0.2):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * int(seconds * 16000))
    return output.getvalue()


@pytest.fixture
def settings(tmp_path, monkeypatch):
    executable, model, vad = (tmp_path / name for name in ("runtime.exe", "model.gguf", "vad.gguf"))
    for path in (executable, model, vad):
        path.write_bytes(b"test")
    settings = SpeechRecognitionConfig(
        enabled=True,
        executable=str(executable),
        model_path=str(model),
        vad_model_path=str(vad),
    )
    monkeypatch.setattr(speech, "_recognition_lock", asyncio.Lock())
    monkeypatch.setattr(EnvConfig, "SPEECH_RECOGNITION", settings)
    return settings


def test_config_opt_in_reload_and_validation():
    assert not parse_config({"config_version": 2}).speech_recognition.enabled
    EnvConfig.reload({"config_version": 2, "speech_recognition": {"max_cpu_cores": 2}})
    assert EnvConfig.SPEECH_RECOGNITION.max_cpu_cores == 2
    for invalid in ({"max_cpu_cores": 0}, {"max_audio_seconds": 0}, {"timeout_seconds": -1}, {"unknown": True}):
        with pytest.raises(ValueError):
            parse_config({"config_version": 2, "speech_recognition": invalid})


@pytest.mark.asyncio
async def test_transcription_decodes_bounded_wav_uses_cpu_and_hides_tags(settings, monkeypatch):
    calls = []

    async def run(args, *, cores):
        calls.append((args, cores))
        if "-i" in args:
            from pathlib import Path

            Path(args[-1]).write_bytes(_wav())
            assert args[args.index("-protocol_whitelist") + 1] == "file,pipe"
            assert "-format_whitelist" in args
            return b""
        assert args[args.index("--backend") + 1] == "cpu"
        assert args[args.index("--vad") + 1] == settings.vad_model_path
        return "<|zh|><|NEUTRAL|>你好，世界。".encode()

    monkeypatch.setattr(speech, "_run_process", run)
    result = await speech.transcribe_audio(_wav())
    assert result.text == "你好，世界。" and result.audio_seconds == pytest.approx(0.2)
    assert len(calls) == 2 and all(cores == 4 for _, cores in calls)
    from pathlib import Path

    assert not Path(calls[0][0][-1]).exists()


@pytest.mark.asyncio
async def test_tencent_silk_uses_isolated_python_worker(settings, monkeypatch):
    calls = []

    async def run(args, *, cores):
        calls.append(args)
        if args[0] == sys.executable:
            from pathlib import Path

            Path(args[3]).write_bytes(_wav())
            return b""
        return "测试".encode()

    monkeypatch.setattr(speech, "_run_process", run)
    assert (await speech.transcribe_audio(b"\x02#!SILK_V3example")).text == "测试"
    assert "speech_decode.py" in calls[0][1]


@pytest.mark.asyncio
async def test_oversize_and_unconfigured_audio_never_start_a_process(settings, monkeypatch):
    async def fail(*_args, **_kwargs):
        raise AssertionError("must not start")

    monkeypatch.setattr(speech, "_run_process", fail)
    with pytest.raises(speech.SpeechRecognitionError, match="audio_size_limit"):
        await speech.transcribe_audio(b"x" * (settings.max_audio_bytes + 1))
    with pytest.raises(speech.SpeechRecognitionError, match="runtime_not_configured"):
        await speech.transcribe_audio(_wav(), settings=settings.model_copy(update={"executable": ""}))


@pytest.mark.asyncio
async def test_timeout_includes_queue_wait(settings):
    async with speech._recognition_lock:
        with pytest.raises(speech.SpeechRecognitionError, match="timeout"):
            await speech.transcribe_audio(_wav(), settings=settings.model_copy(update={"timeout_seconds": 0.01}))


@pytest.mark.asyncio
async def test_cancelled_process_is_killed_and_reaped(monkeypatch):
    import psutil

    entered = asyncio.Event()

    class Process:
        pid = 123
        returncode = None
        killed = False
        reaped = False

        async def communicate(self):
            entered.set()
            await asyncio.Future()

        def kill(self):
            self.killed = True

        async def wait(self):
            self.reaped = True
            self.returncode = -9

    process = Process()
    real_process = psutil.Process

    def lookup(pid=None):
        if pid == process.pid:
            from types import SimpleNamespace

            return SimpleNamespace(children=lambda **_kwargs: [])
        return real_process(pid)

    async def spawn(*_args, **_kwargs):
        assert "shell" not in _kwargs
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(psutil, "Process", lookup)
    monkeypatch.setattr(speech, "_limit_cpu", lambda *_args: None)
    task = asyncio.create_task(speech._run_process(["runtime"], cores=2))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert process.killed and process.reaped


@pytest.mark.asyncio
async def test_cancelled_real_worker_reaps_its_child(tmp_path):
    import psutil

    ready = tmp_path / "child.pid"
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import pathlib, subprocess, sys, time\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "pathlib.Path(sys.argv[1]).write_text(str(child.pid))\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    task = asyncio.create_task(speech._run_process([sys.executable, str(worker), str(ready)], cores=2))
    try:
        async with asyncio.timeout(10):
            while not ready.exists():
                if task.done():
                    await task
                await asyncio.sleep(0.02)
        child = psutil.Process(int(ready.read_text()))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not child.is_running() or child.status() == psutil.STATUS_ZOMBIE
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_recognition_enriches_user_input_without_logging_transcripts(settings, monkeypatch, caplog):
    async def recognize(*_args, **_kwargs):
        return speech.Transcription("private spoken text", 0.5, 0.1)

    monkeypatch.setattr(speech, "transcribe_audio", recognize)
    with caplog.at_level("INFO", logger=speech.__name__):
        text, handled = await speech.transcribe_message_audio("原有文字", [b"audio"])
    assert handled and "原有文字" in text and "用户语音 1 自动转写" in text and "private spoken text" in text
    assert "private spoken text" not in caplog.text


@pytest.mark.asyncio
async def test_failure_is_explicit_and_preserves_other_user_text(settings, monkeypatch, caplog):
    async def recognize(*_args, **_kwargs):
        raise speech.SpeechRecognitionError("runtime_failed")

    monkeypatch.setattr(speech, "transcribe_audio", recognize)
    text, handled = await speech.transcribe_message_audio("已有文字", [b"audio"])
    assert handled and "已有文字" in text and "无法据此判断语音内容" in text
    assert "code=runtime_failed" in caplog.text


@pytest.mark.asyncio
async def test_disabled_recognition_leaves_native_audio_path_intact(settings, monkeypatch):
    monkeypatch.setattr(EnvConfig, "SPEECH_RECOGNITION", settings.model_copy(update={"enabled": False}))
    assert await speech.transcribe_message_audio("hello", [b"audio"]) == ("hello", False)


@pytest.mark.asyncio
async def test_message_audio_count_is_bounded_and_preserves_partial_success(settings, monkeypatch):
    calls = []

    async def recognize(data, **_kwargs):
        calls.append(data)
        if data == b"bad":
            raise speech.SpeechRecognitionError("no_speech")
        return speech.Transcription("识别成功", 1, 0.1)

    monkeypatch.setattr(speech, "transcribe_audio", recognize)
    monkeypatch.setattr(EnvConfig, "SPEECH_RECOGNITION", settings.model_copy(update={"max_audio_per_message": 2}))
    text, handled = await speech.transcribe_message_audio("文字", [b"good", b"bad", b"extra"])
    assert handled and calls == [b"good", b"bad"]
    assert "识别成功" in text and "no_speech" in text and "数量限制" in text


@pytest.mark.asyncio
async def test_media_decoder_rejects_playlists_without_fetching_urls(settings, tmp_path):
    fetched = []

    async def handler(reader, writer):
        fetched.append(await reader.read(1024))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    async with server:
        port = server.sockets[0].getsockname()[1]
        playlist = f"#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\nhttp://127.0.0.1:{port}/secret\n#EXT-X-ENDLIST\n"
        with pytest.raises(speech.SpeechRecognitionError):
            await speech._decode_audio(playlist.encode(), tmp_path, settings)
    assert fetched == []


def test_invalid_and_long_decoded_audio_are_rejected(tmp_path):
    path = tmp_path / "audio.wav"
    path.write_bytes(_wav(2))
    with pytest.raises(speech.SpeechRecognitionError, match="audio_duration_limit"):
        speech._wave_duration(path, 1)
    path.write_bytes(b"invalid")
    with pytest.raises(speech.SpeechRecognitionError, match="invalid_audio"):
        speech._wave_duration(path, 10)


def test_silk_pcm_writer_enforces_limit():
    from utils.speech_decode import _BoundedPcm

    output = _BoundedPcm(4)
    assert output.write(b"\x00" * 4) == 4
    with pytest.raises(ValueError, match="audio_duration_limit"):
        output.write(b"\x00\x00")
