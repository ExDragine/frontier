"""WAV I/O for the pinned MOSS model, using existing Torch/FFmpeg dependencies.

Copied into the model directory by setup_moss_tts.py. The upstream model uses
only load/save/functional.resample from torchaudio; no audio operators change.
"""

import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import torch


def load(path: str) -> tuple[torch.Tensor, int]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2 or source.getnframes() > source.getframerate() * 30:
            raise ValueError("Expected a short PCM16 reference WAV")
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").copy()
        samples = samples.reshape(-1, source.getnchannels()).T.astype(np.float32) / 32768
        return torch.from_numpy(samples), source.getframerate()


def save(path: str, waveform: torch.Tensor, sample_rate: int) -> None:
    samples = waveform.detach().float().cpu().numpy()
    if samples.ndim != 2 or not np.isfinite(samples).all():
        raise ValueError("Invalid generated waveform")
    pcm = (np.clip(samples.T, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(Path(path)), "wb") as output:
        output.setnchannels(samples.shape[0])
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm)


class functional:
    @staticmethod
    def resample(waveform: torch.Tensor, orig_freq: int, new_freq: int) -> torch.Tensor:
        samples = waveform.detach().float().cpu().numpy()
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-threads",
            "1",
            "-f",
            "f32le",
            "-ar",
            str(orig_freq),
            "-ac",
            str(samples.shape[0]),
            "-i",
            "pipe:0",
            "-f",
            "f32le",
            "-ar",
            str(new_freq),
            "pipe:1",
        ]
        result = subprocess.run(  # noqa: S603
            command,
            input=samples.T.astype("<f4").tobytes(),
            capture_output=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        values = np.frombuffer(result.stdout, dtype="<f4").copy().reshape(-1, samples.shape[0]).T
        return torch.from_numpy(values)


class AudioIO:
    load = staticmethod(load)
    save = staticmethod(save)
    functional = functional


audio = AudioIO()
