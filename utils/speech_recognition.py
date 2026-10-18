"""Bounded offline SenseVoice recognition, isolated from the bot event loop."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.configs import EnvConfig, SpeechRecognitionConfig
from utils.speech_assets import SpeechAssetsError, ensure_recognition_assets
from utils.speech_resources import speech_inference_lock

logger = logging.getLogger(__name__)
_recognition_lock = speech_inference_lock
_SILK_HEADERS = (b"\x02#!SILK_V3", b"#!SILK_V3")
_TAG = re.compile(r"<\|[^\r\n]*?\|>")
_DECODE_WORKER = Path(__file__).with_name("speech_decode.py")


class SpeechRecognitionError(Exception):
    """A stable, non-sensitive failure code suitable for logs and user notices."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class Transcription:
    text: str
    audio_seconds: float
    elapsed_seconds: float


def _runtime_paths(settings: SpeechRecognitionConfig) -> tuple[Path, Path, Path | None]:
    if not settings.executable or not settings.model_path:
        raise SpeechRecognitionError("runtime_not_configured")
    executable = Path(settings.executable).resolve()
    model = Path(settings.model_path).resolve()
    vad = Path(settings.vad_model_path).resolve() if settings.vad_model_path else None
    if not executable.is_file() or not model.is_file() or (vad is not None and not vad.is_file()):
        raise SpeechRecognitionError("runtime_missing")
    return executable, model, vad


def _limit_cpu(pid: int, cores: int) -> None:
    import psutil

    try:
        process = psutil.Process(pid)
        if hasattr(process, "cpu_affinity"):
            eligible = psutil.Process().cpu_affinity()
            process.cpu_affinity(eligible[:cores])
    except psutil.NoSuchProcess:
        pass
    except psutil.Error as exc:
        raise SpeechRecognitionError("cpu_limit_failed") from exc


async def _run_process(args: list[str], *, cores: int) -> bytes:
    flags = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=flags,
        )
    except OSError as exc:
        raise SpeechRecognitionError("runtime_start_failed") from exc
    try:
        _limit_cpu(process.pid, cores)
        stdout, _stderr = await process.communicate()
        if process.returncode:
            raise SpeechRecognitionError("runtime_failed")
        if len(stdout) > 128 * 1024:
            raise SpeechRecognitionError("output_limit")
        return stdout
    finally:
        if process.returncode is None:
            import psutil

            try:
                children = psutil.Process(process.pid).children(recursive=True)
            except psutil.Error:
                children = []
            for child in reversed(children):
                try:
                    child.kill()
                except psutil.Error:
                    logger.warning("本地语音子进程回收失败 code=child_cleanup_failed")
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
            if children:
                await asyncio.to_thread(psutil.wait_procs, children, timeout=2)


def _wave_duration(path: Path, max_seconds: int) -> float:
    try:
        with wave.open(str(path), "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
            if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getframerate() != 16000:
                raise SpeechRecognitionError("invalid_audio")
    except (OSError, EOFError, wave.Error, ZeroDivisionError) as exc:
        raise SpeechRecognitionError("invalid_audio") from exc
    if duration > max_seconds:
        raise SpeechRecognitionError("audio_duration_limit")
    if duration < 0.1:
        raise SpeechRecognitionError("empty_audio")
    return duration


async def _decode_audio(data: bytes, directory: Path, settings: SpeechRecognitionConfig) -> tuple[Path, float]:
    source, target = directory / "input.audio", directory / "input.wav"
    source.write_bytes(data)
    if data.startswith(_SILK_HEADERS):
        args = [sys.executable, str(_DECODE_WORKER), str(source), str(target), str(settings.max_audio_seconds)]
    else:
        import imageio_ffmpeg

        args = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-threads",
            "1",
            "-protocol_whitelist",
            "file,pipe",
            "-format_whitelist",
            "wav,mp3,flac,ogg,mov,matroska,webm,aac,amr",
            "-i",
            str(source),
            "-vn",
            "-t",
            str(settings.max_audio_seconds + 1),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(target),
        ]
    await _run_process(args, cores=settings.max_cpu_cores)
    return target, _wave_duration(target, settings.max_audio_seconds)


async def transcribe_audio(data: bytes, *, settings: SpeechRecognitionConfig | None = None) -> Transcription:
    """Run a single local request; timeout covers queueing, decoding and inference."""
    settings = settings or EnvConfig.SPEECH_RECOGNITION
    if not settings.enabled:
        raise SpeechRecognitionError("disabled")
    if not data or len(data) > settings.max_audio_bytes:
        raise SpeechRecognitionError("audio_size_limit")
    started = time.monotonic()
    try:
        await ensure_recognition_assets(settings)
        executable, model, vad = _runtime_paths(settings)
        async with asyncio.timeout(settings.timeout_seconds), _recognition_lock:
            with TemporaryDirectory(prefix="frontier-asr-") as temporary:
                wav, duration = await _decode_audio(data, Path(temporary), settings)
                args = [str(executable), "-m", str(model), "-a", str(wav), "--backend", "cpu"]
                if vad is not None:
                    args.extend(["--vad", str(vad), "--vad-maxseg", "30000"])
                output = await _run_process(args, cores=settings.max_cpu_cores)
                try:
                    text = _TAG.sub("", output.decode("utf-8")).strip()
                except UnicodeDecodeError as exc:
                    raise SpeechRecognitionError("invalid_transcript") from exc
                if not text:
                    raise SpeechRecognitionError("no_speech")
                if len(text) > settings.max_transcript_chars:
                    raise SpeechRecognitionError("transcript_limit")
                return Transcription(text, duration, time.monotonic() - started)
    except TimeoutError as exc:
        raise SpeechRecognitionError("timeout") from exc
    except SpeechAssetsError as exc:
        raise SpeechRecognitionError(exc.code) from exc


async def transcribe_message_audio(text: str, audio: list[bytes]) -> tuple[str, bool]:
    """Enrich user text after the reply gate; never treat transcripts as instructions.

    The boolean says local ASR handled the audio, including explicit failures.
    Original bytes remain in the existing attachment store, not sent to the LLM.
    """
    settings = EnvConfig.SPEECH_RECOGNITION
    if not settings.enabled or not audio:
        return text, False
    additions = []
    for index, data in enumerate(audio[: settings.max_audio_per_message], start=1):
        try:
            result = await transcribe_audio(data, settings=settings)
            additions.append(f"[用户语音 {index} 自动转写，可能有识别错误]\n{result.text}\n[语音转写结束]")
            logger.info(
                "本地语音识别完成 audio_seconds=%.2f elapsed_seconds=%.2f chars=%d",
                result.audio_seconds,
                result.elapsed_seconds,
                len(result.text),
            )
        except SpeechRecognitionError as exc:
            logger.warning("本地语音识别失败 code=%s", exc.code)
            additions.append(
                f"[用户语音 {index} 识别失败，错误码：{exc.code}；无法据此判断语音内容，可请用户改发文字]"
            )
    if len(audio) > settings.max_audio_per_message:
        additions.append("[其余语音超出本条消息的识别数量限制，尚未识别]")
    return "\n\n".join([text, *additions]).strip(), True
