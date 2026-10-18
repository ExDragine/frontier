"""Bounded, on-demand local MOSS-TTS-Nano synthesis."""

import asyncio
import json
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.configs import EnvConfig, SpeechSynthesisConfig
from utils.moss_tts_assets import verify_installation
from utils.speech_assets import SpeechAssetsError, ensure_synthesis_assets
from utils.speech_recognition import SpeechRecognitionError, _run_process
from utils.speech_resources import speech_inference_lock

_WORKER = Path(__file__).with_name("speech_synthesis_worker.py")


class SpeechSynthesisError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class SynthesizedSpeech:
    wav: bytes
    silk: bytes
    audio_seconds: float
    elapsed_seconds: float


def _read_audio(directory: Path, max_seconds: int) -> tuple[bytes, bytes, float]:
    wav_path, silk_path = directory / "output.wav", directory / "output.silk"
    if wav_path.stat().st_size > max_seconds * 48000 * 4 + 4096 or silk_path.stat().st_size > 1024 * 1024:
        raise SpeechSynthesisError("output_limit")
    with wave.open(str(wav_path), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
        if audio.getsampwidth() != 2 or audio.getnchannels() not in (1, 2) or audio.getframerate() != 48000:
            raise SpeechSynthesisError("invalid_audio")
        if not 0.1 <= duration <= max_seconds:
            raise SpeechSynthesisError("audio_duration_limit")
        if len(audio.readframes(audio.getnframes())) != audio.getnframes() * audio.getnchannels() * 2:
            raise SpeechSynthesisError("invalid_audio")
    silk = silk_path.read_bytes()
    if not silk.startswith(b"\x02#!SILK_V3"):
        raise SpeechSynthesisError("invalid_audio")
    return wav_path.read_bytes(), silk, duration


async def synthesize_speech(text: str, *, settings: SpeechSynthesisConfig | None = None) -> SynthesizedSpeech:
    settings = settings or EnvConfig.SPEECH_SYNTHESIS
    if not settings.enabled:
        raise SpeechSynthesisError("disabled")
    text = text.strip()
    if not text:
        raise SpeechSynthesisError("empty_text")
    if len(text) > settings.max_text_chars:
        raise SpeechSynthesisError("text_limit")
    model_dir = Path(settings.model_dir).resolve()
    started = time.monotonic()
    try:
        await ensure_synthesis_assets(settings)
        async with asyncio.timeout(settings.timeout_seconds), speech_inference_lock:
            try:
                await asyncio.to_thread(verify_installation, model_dir)
            except (OSError, ValueError) as exc:
                raise SpeechSynthesisError("runtime_missing_or_unverified") from exc
            with TemporaryDirectory(prefix="frontier-tts-") as temporary:
                directory = Path(temporary)
                request = directory / "request.json"
                request.write_text(
                    json.dumps(
                        {
                            "model_dir": str(model_dir),
                            "max_cpu_cores": settings.max_cpu_cores,
                            "text": text,
                            "max_audio_seconds": settings.max_audio_seconds,
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                await _run_process([sys.executable, str(_WORKER), str(request)], cores=settings.max_cpu_cores)
                wav, silk, duration = _read_audio(directory, settings.max_audio_seconds)
                return SynthesizedSpeech(wav, silk, duration, time.monotonic() - started)
    except TimeoutError as exc:
        raise SpeechSynthesisError("timeout") from exc
    except SpeechAssetsError as exc:
        raise SpeechSynthesisError(exc.code) from exc
    except SpeechRecognitionError as exc:
        raise SpeechSynthesisError(exc.code) from exc
    except (OSError, ValueError, EOFError, wave.Error) as exc:
        raise SpeechSynthesisError("invalid_audio") from exc
