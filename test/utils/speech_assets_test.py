# ruff: noqa: S101

import asyncio
import hashlib
import io
import json
import tomllib
import zipfile
from pathlib import Path

import pytest

from utils import moss_tts_assets as moss
from utils import sensevoice_assets as sensevoice
from utils import speech_assets as assets
from utils import speech_download as downloads
from utils.configs import SpeechRecognitionConfig, SpeechSynthesisConfig, parse_config
from utils.speech_recognition import SpeechRecognitionError


@pytest.fixture(autouse=True)
def isolated_asset_cache(monkeypatch):
    monkeypatch.setattr(assets, "_asset_lock", asyncio.Lock())
    monkeypatch.setattr(assets, "_verified", {})


def test_both_speech_features_are_in_default_uv_dependencies():
    project = tomllib.loads((Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = {value.split("==")[0].split(">=")[0] for value in project["project"]["dependencies"]}
    assert {
        "torch",
        "transformers",
        "sentencepiece",
        "silk-python",
        "imageio-ffmpeg",
        "psutil",
        "filelock",
    } <= dependencies


def test_default_paths_and_download_budget_only_need_feature_enable():
    settings = parse_config(
        {"config_version": 2, "speech_recognition": {"enabled": True}, "speech_synthesis": {"enabled": True}}
    )
    assert settings.speech_recognition.auto_download and settings.speech_synthesis.auto_download
    assert settings.speech_recognition.executable.endswith(sensevoice.EXECUTABLE)
    assert settings.speech_recognition.model_path.endswith(sensevoice.MODEL)
    for field in ("speech_recognition", "speech_synthesis"):
        for invalid in (0, -1, 1801):
            with pytest.raises(ValueError):
                parse_config({"config_version": 2, field: {"download_timeout_seconds": invalid}})


@pytest.mark.asyncio
async def test_disabled_or_offline_settings_do_not_inspect_or_download(monkeypatch):
    async def unexpected(*_args, **_kwargs):
        pytest.fail("must not prepare assets")

    monkeypatch.setattr(assets, "_prepare", unexpected)
    await assets.ensure_recognition_assets(SpeechRecognitionConfig())
    await assets.ensure_synthesis_assets(SpeechSynthesisConfig())
    await assets.ensure_recognition_assets(SpeechRecognitionConfig(enabled=True, auto_download=False))
    await assets.ensure_synthesis_assets(SpeechSynthesisConfig(enabled=True, auto_download=False))


@pytest.mark.asyncio
async def test_custom_recognition_paths_are_never_replaced(tmp_path, monkeypatch):
    async def unexpected(*_args, **_kwargs):
        pytest.fail("custom runtimes are managed by the operator")

    monkeypatch.setattr(assets, "_prepare", unexpected)
    await assets.ensure_recognition_assets(
        SpeechRecognitionConfig(
            enabled=True,
            executable=str(tmp_path / "custom.exe"),
            model_path=str(tmp_path / "custom.gguf"),
        )
    )


@pytest.mark.asyncio
async def test_unsupported_platform_fails_before_download(monkeypatch):
    monkeypatch.setattr(sensevoice, "supported_platform", lambda: False)
    with pytest.raises(assets.SpeechAssetsError, match="asset_platform_unsupported"):
        await assets.ensure_recognition_assets(SpeechRecognitionConfig(enabled=True))


@pytest.mark.asyncio
async def test_managed_recognition_preserves_avx2_selection(tmp_path, monkeypatch):
    calls = []

    async def prepare(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(assets, "_prepare", prepare)
    monkeypatch.setattr(sensevoice, "supported_platform", lambda: True)
    await assets.ensure_recognition_assets(
        SpeechRecognitionConfig(
            enabled=True,
            executable=str(tmp_path / "runtime-avx2" / sensevoice.EXECUTABLE),
            model_path=str(tmp_path / sensevoice.MODEL),
            vad_model_path="",
        )
    )
    assert len(calls) == 1 and calls[0][1]["avx2"] is True
    assert calls[0][0][1] == tmp_path


@pytest.mark.asyncio
async def test_concurrent_first_use_installs_once_and_rechecks_changed_assets(tmp_path, monkeypatch):
    import utils.speech_recognition as speech

    target = tmp_path / "asset.bin"
    calls, checks = [], []

    def verify():
        checks.append(True)
        if target.read_bytes() != b"verified":
            raise ValueError("checksum mismatch")

    async def run(args, *, cores):
        calls.append(args)
        assert cores == 2 and args[-2:] == ["--destination", str(tmp_path)]
        await asyncio.sleep(0.01)
        target.write_bytes(b"verified")
        return b""

    monkeypatch.setattr(speech, "_run_process", run)

    async def prepare():
        await assets._prepare("synthesis", tmp_path, [target], verify, timeout=1, cores=2)

    await asyncio.gather(prepare(), prepare(), prepare())
    assert len(calls) == 1 and len(checks) == 1
    target.write_bytes(b"corrupted")
    await prepare()
    assert len(calls) == 2 and target.read_bytes() == b"verified"


@pytest.mark.asyncio
async def test_download_timeout_cancels_worker_and_releases_lock(tmp_path, monkeypatch):
    import utils.speech_recognition as speech

    cancelled = []

    async def run(*_args, **_kwargs):
        try:
            await asyncio.Future()
        finally:
            cancelled.append(True)

    monkeypatch.setattr(speech, "_run_process", run)
    with pytest.raises(assets.SpeechAssetsError, match="asset_download_timeout"):
        await assets._prepare("synthesis", tmp_path, [tmp_path / "missing"], lambda: None, timeout=0.05, cores=1)
    assert cancelled and not assets._asset_lock.locked() and not assets._verified


@pytest.mark.asyncio
async def test_failed_installer_is_sanitized_and_never_cached(tmp_path, monkeypatch):
    import utils.speech_recognition as speech

    async def run(*_args, **_kwargs):
        raise SpeechRecognitionError("runtime_failed")

    monkeypatch.setattr(speech, "_run_process", run)
    with pytest.raises(assets.SpeechAssetsError, match="^asset_download_failed$"):
        await assets._prepare("recognition", tmp_path, [tmp_path / "missing"], lambda: None, timeout=1, cores=1)
    assert not assets._verified


def test_checksum_failure_keeps_previous_file_and_removes_partial_download(tmp_path, monkeypatch):
    target = tmp_path / "model.bin"
    target.write_bytes(b"previous")
    monkeypatch.setattr(downloads.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(b"bad download"))
    with pytest.raises(ValueError, match="checksum"):
        downloads.download_verified(target, "https://example.invalid/model", hashlib.sha256(b"expected").hexdigest())
    assert target.read_bytes() == b"previous" and not list(tmp_path.glob("*.part"))


def test_interrupted_download_removes_partial_file(tmp_path, monkeypatch):
    class BrokenDownload(io.BytesIO):
        def read(self, *_args):
            raise OSError("network interrupted")

    monkeypatch.setattr(downloads.urllib.request, "urlopen", lambda *_args, **_kwargs: BrokenDownload())
    with pytest.raises(OSError):
        downloads.download_verified(tmp_path / "model.bin", "https://example.invalid/model", "0" * 64)
    assert not (tmp_path / "model.bin").exists() and not list(tmp_path.glob("*.part"))


def test_sensevoice_installer_checks_executable_before_publish(tmp_path, monkeypatch):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr(sensevoice.EXECUTABLE, b"wrong executable")
    content = {"runtime.zip": archive.getvalue(), sensevoice.MODEL: b"model", sensevoice.VAD: b"vad"}
    monkeypatch.setattr(sensevoice, "supported_platform", lambda: True)
    monkeypatch.setattr(
        sensevoice,
        "ASSETS",
        tuple(
            (name, "https://example.invalid/" + name, hashlib.sha256(data).hexdigest())
            for name, data in content.items()
        ),
    )
    monkeypatch.setattr(sensevoice, "download_verified", lambda path, *_args: path.write_bytes(content[path.name]))
    with pytest.raises(ValueError, match="executable checksum"):
        sensevoice.install(tmp_path)
    assert not (tmp_path / "runtime" / sensevoice.EXECUTABLE).exists()


def test_moss_installation_verifies_weights_and_adapter(tmp_path, monkeypatch):
    content = {moss.MODEL_CODE: b"import torchaudio\n", "MOSS-TTS-Nano-100M/pytorch_model.bin": b"weights"}
    manifest = tmp_path / "assets.json"
    manifest.write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "file": name,
                        "url": "https://example.invalid/" + name,
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                    for name, data in content.items()
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(moss, "MANIFEST", manifest)
    monkeypatch.setattr(
        moss,
        "download_verified",
        lambda path, url, _digest: path.write_bytes(content[url.removeprefix("https://example.invalid/")]),
    )
    destination = tmp_path / "models"
    moss.install(destination)
    moss.verify_installation(destination, full=True)
    (destination / "MOSS-TTS-Nano-100M/pytorch_model.bin").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        moss.verify_installation(destination, full=True)
