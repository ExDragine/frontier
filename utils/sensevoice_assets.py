"""Pinned official Windows x64 SenseVoice Q8 assets; no application imports."""

import hashlib
import json
import os
import platform
import zipfile
from pathlib import Path

from utils.speech_download import download_verified, installation_lock, sha256

DEFAULT_DIRECTORY = "cache/speech/sensevoice"
EXECUTABLE = "llama-funasr-sensevoice.exe"
MODEL = "sensevoice-small-q8.gguf"
VAD = "fsmn-vad.gguf"
RELEASE = "runtime-llamacpp-v0.2.1"
ASSETS = (
    (
        "runtime.zip",
        f"https://github.com/QwenAudio/SenseVoice/releases/download/{RELEASE}/funasr-llamacpp-windows-x64.zip",
        "b8f2b8f241b57921d82d64068d9b5695629779f3db5f3205a730cb3810232bb4",
    ),
    (
        MODEL,
        "https://huggingface.co/FunAudioLLM/SenseVoiceSmall-GGUF/resolve/"
        "90c1c61912018b70ada0fcc024ea24aca62f2e63/sensevoice-small-q8.gguf",
        "4ae45c94422de949b387e2e0fb10d7e14e4c42c69db30c3444ecc7d4b844b7c5",
    ),
    (
        VAD,
        "https://huggingface.co/FunAudioLLM/fsmn-vad-GGUF/resolve/"
        "6840bae4c5c92ee8c04faaf4db23dd0105098d7f/fsmn-vad.gguf",
        "1270f2559c495f4e7b6e739541151027d360761a3fda43fc147034f5719f5479",
    ),
)
AVX2_RUNTIME = (
    "runtime-avx2.zip",
    f"https://github.com/QwenAudio/SenseVoice/releases/download/{RELEASE}/funasr-llamacpp-windows-x64-avx2.zip",
    "67e428a91614f8a0c1d53dc2d79cce8efc7916c030ae2ddce2cbcf667ec1c502",
)
EXECUTABLE_HASHES = {
    False: "eb1faf1f7251c6756e4c28fa1fe3f47d3691449bde6f38bc322a3eb5df43466c",
    True: "fe8ba6a74a7acd57bdc5a5fb5cb58cb3acc96a883e54be727de285eb5db090a7",
}


def supported_platform() -> bool:
    return os.name == "nt" and platform.machine().lower() in {"amd64", "x86_64"}


def runtime_files(destination: Path, *, avx2: bool = False) -> list[tuple[Path, str]]:
    runtime = destination / ("runtime-avx2" if avx2 else "runtime") / EXECUTABLE
    return [(runtime, EXECUTABLE_HASHES[avx2]), *[(destination / name, digest) for name, _, digest in ASSETS[1:]]]


def verify_installation(destination: Path, *, avx2: bool = False) -> None:
    for path, digest in runtime_files(destination, avx2=avx2):
        if not path.is_file() or sha256(path) != digest:
            raise ValueError("SenseVoice asset missing or unverified")


def install(destination: Path, *, avx2: bool = False) -> None:
    if not supported_platform():
        raise ValueError("SenseVoice automatic installation requires Windows x64")
    destination = destination.resolve()
    with installation_lock(destination):
        assets = (AVX2_RUNTIME, *ASSETS[1:]) if avx2 else ASSETS
        for name, url, expected in assets:
            print(f"Checking {name}...", flush=True)
            download_verified(destination / name, url, expected)
        executable = runtime_files(destination, avx2=avx2)[0][0]
        executable.parent.mkdir(exist_ok=True)
        if not executable.is_file() or sha256(executable) != EXECUTABLE_HASHES[avx2]:
            with zipfile.ZipFile(destination / assets[0][0]) as archive:
                matches = [item for item in archive.infolist() if Path(item.filename).name == EXECUTABLE]
                if len(matches) != 1:
                    raise ValueError("Expected exactly one SenseVoice executable")
                data = archive.read(matches[0])
            if hashlib.sha256(data).hexdigest() != EXECUTABLE_HASHES[avx2]:
                raise ValueError("SenseVoice executable checksum mismatch")
            partial = executable.with_suffix(".exe.part")
            try:
                partial.write_bytes(data)
                partial.replace(executable)
            finally:
                partial.unlink(missing_ok=True)
        verify_installation(destination, avx2=avx2)
        (destination / ("manifest-avx2.json" if avx2 else "manifest.json")).write_text(
            json.dumps(
                {
                    "release": RELEASE,
                    "assets": [{"file": name, "url": url, "sha256": digest} for name, url, digest in assets],
                    "executable_sha256": EXECUTABLE_HASHES[avx2],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print(f"Verified runtime ready: {executable}")
