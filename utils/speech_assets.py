"""Prepare enabled speech models on first use, with bounded, shared downloads."""

import asyncio
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from utils import moss_tts_assets, sensevoice_assets

if TYPE_CHECKING:
    from utils.configs import SpeechRecognitionConfig, SpeechSynthesisConfig

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
_asset_lock = asyncio.Lock()
type Signature = tuple[tuple[str, int, int, int, int], ...]
_verified: dict[tuple[str, ...], Signature] = {}


class SpeechAssetsError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _signature(paths: list[Path]) -> Signature:
    result = []
    for path in paths:
        info = path.stat()
        result.append((str(path), info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_ino))
    return tuple(result)


def _is_verified(key: tuple[str, ...], paths: list[Path], verify: Callable[[], None]) -> bool:
    try:
        signature = _signature(paths)
        if _verified.get(key) == signature:
            return True
        verify()
        if signature != _signature(paths):
            return False
    except OSError, ValueError:
        _verified.pop(key, None)
        return False
    if len(_verified) >= 16:
        _verified.pop(next(iter(_verified)))
    _verified[key] = signature
    return True


async def _prepare(
    kind: str,
    root: Path,
    paths: list[Path],
    verify: Callable[[], None],
    *,
    timeout: float,
    cores: int,
    avx2: bool = False,
) -> None:
    key = (kind, str(root), str(avx2))
    try:
        async with asyncio.timeout(timeout), _asset_lock:
            if await asyncio.to_thread(_is_verified, key, paths, verify):
                return
            logger.info("本地语音资源准备开始 kind=%s", kind)
            script = "setup_sensevoice.py" if kind == "recognition" else "setup_moss_tts.py"
            args = [sys.executable, str(ROOT / "scripts" / script), "--destination", str(root)]
            if avx2:
                args.append("--avx2")
            # Import after application initialization; the child installers never
            # import EnvConfig, load weights, or execute a downloaded runtime.
            from utils.speech_recognition import SpeechRecognitionError, _run_process

            try:
                await _run_process(args, cores=cores)
            except SpeechRecognitionError as exc:
                raise SpeechAssetsError("asset_download_failed") from exc
            if not await asyncio.to_thread(_is_verified, key, paths, verify):
                raise SpeechAssetsError("asset_verification_failed")
            logger.info("本地语音资源准备完成 kind=%s", kind)
    except TimeoutError as exc:
        raise SpeechAssetsError("asset_download_timeout") from exc


async def ensure_recognition_assets(settings: SpeechRecognitionConfig) -> None:
    if not settings.enabled or not settings.auto_download or not settings.executable or not settings.model_path:
        return
    executable = Path(settings.executable).resolve()
    root = executable.parent.parent
    if executable.name != sensevoice_assets.EXECUTABLE or executable.parent.name not in {"runtime", "runtime-avx2"}:
        return
    if Path(settings.model_path).resolve() != root / sensevoice_assets.MODEL:
        return
    if settings.vad_model_path and Path(settings.vad_model_path).resolve() != root / sensevoice_assets.VAD:
        return
    if not sensevoice_assets.supported_platform():
        raise SpeechAssetsError("asset_platform_unsupported")
    avx2 = executable.parent.name == "runtime-avx2"
    await _prepare(
        "recognition",
        root,
        [path for path, _ in sensevoice_assets.runtime_files(root, avx2=avx2)],
        lambda: sensevoice_assets.verify_installation(root, avx2=avx2),
        timeout=settings.download_timeout_seconds,
        cores=settings.max_cpu_cores,
        avx2=avx2,
    )


async def ensure_synthesis_assets(settings: SpeechSynthesisConfig) -> None:
    if not settings.enabled or not settings.auto_download:
        return
    root = Path(settings.model_dir).resolve()
    await _prepare(
        "synthesis",
        root,
        moss_tts_assets.installed_files(root),
        lambda: moss_tts_assets.verify_installation(root, full=True),
        timeout=settings.download_timeout_seconds,
        cores=settings.max_cpu_cores,
    )
