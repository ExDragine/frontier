"""Verify pinned model code before allowing local custom-code execution."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from utils.speech_download import download_verified, installation_lock

MANIFEST = Path(__file__).with_suffix(".json")
MODEL_CODE = "MOSS-TTS-Nano-100M/modeling_moss_tts_nano.py"
ADAPTER = Path(__file__).with_name("moss_audio_io.py")


def assets() -> list[dict[str, str]]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]


def original_path(root: Path, name: str) -> Path:
    path = root / name
    return path.with_suffix(".py.upstream") if name == MODEL_CODE else path


def patched_code(original: bytes) -> bytes:
    old = b"import torchaudio\n"
    if original.count(old) != 1:
        raise ValueError("Unexpected MOSS audio import")
    return original.replace(old, b"from .frontier_audio import audio as torchaudio\n")


def prepare_audio_adapter(root: Path) -> None:
    source = original_path(root, MODEL_CODE).read_bytes()
    (root / MODEL_CODE).write_bytes(patched_code(source))
    (root / "MOSS-TTS-Nano-100M/frontier_audio.py").write_bytes(ADAPTER.read_bytes())


def verify_installation(root: Path, *, full: bool = False) -> None:
    for asset in assets():
        path = original_path(root, asset["file"])
        if not path.is_file():
            raise ValueError("Missing MOSS asset")
        # Large weights are fully hashed during installation. Recheck executable
        # code, configuration, tokenizer and the fixed voice on every request.
        if full or path.suffix not in {".bin", ".safetensors"}:
            with path.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            if digest != asset["sha256"]:
                raise ValueError("MOSS asset checksum mismatch")
    if (root / MODEL_CODE).read_bytes() != patched_code(original_path(root, MODEL_CODE).read_bytes()):
        raise ValueError("MOSS adapter patch mismatch")
    if (root / "MOSS-TTS-Nano-100M/frontier_audio.py").read_bytes() != ADAPTER.read_bytes():
        raise ValueError("MOSS audio adapter mismatch")


def installed_files(root: Path) -> list[Path]:
    return [
        *[original_path(root, asset["file"]) for asset in assets()],
        root / MODEL_CODE,
        root / "MOSS-TTS-Nano-100M/frontier_audio.py",
        ADAPTER,
        MANIFEST,
    ]


def install(destination: Path) -> None:
    destination = destination.resolve()
    with installation_lock(destination):
        downloads = []
        for asset in assets():
            target = original_path(destination, asset["file"]).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("Invalid model asset path")
            target.parent.mkdir(parents=True, exist_ok=True)
            downloads.append((asset, target))

        def download(item):
            asset, target = item
            print(f"Checking {asset['file']}...", flush=True)
            download_verified(target, asset["url"], asset["sha256"])

        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(download, downloads))
        prepare_audio_adapter(destination)
        verify_installation(destination, full=True)
        (destination / "installation.json").write_text(MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Verified MOSS-TTS-Nano assets ready: {destination}")
