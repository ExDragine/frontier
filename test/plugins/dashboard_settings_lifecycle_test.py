# ruff: noqa: S101, S106

import asyncio
import os
import threading
import tomllib

import pytest
from fastapi import HTTPException

from plugins.dashboard.api import settings_routes


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "settings.toml"
    path.write_text(
        'config_version = 2\n\n[limits]\nagent_llm_timeout_seconds = 900\nagent_job_timeout_seconds = 3600\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_routes, "TOML_PATH", path)
    monkeypatch.setattr(settings_routes, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(settings_routes, "_settings_write_lock", asyncio.Lock())
    return path


async def test_concurrent_settings_updates_merge_without_lost_writes(settings_file, monkeypatch):
    reloads = []
    main_thread = threading.get_ident()
    persist = settings_routes._persist_section
    worker_threads = []

    def capture_persist(*args):
        worker_threads.append(threading.get_ident())
        return persist(*args)

    def reload(config):
        assert threading.get_ident() == main_thread
        reloads.append(config)

    monkeypatch.setattr(settings_routes, "_persist_section", capture_persist)
    monkeypatch.setattr(settings_routes, "_reload_env_config", reload)
    results = await asyncio.gather(*[
        settings_routes.update_section("limits", settings_routes.SectionUpdate(config=change), user={})
        for change in [{"agent_llm_timeout_seconds": 100}, {"agent_job_timeout_seconds": 200}]
    ])
    saved = tomllib.loads(settings_file.read_text())
    assert saved["limits"] == {"agent_llm_timeout_seconds": 100, "agent_job_timeout_seconds": 200}
    assert len(reloads) == 2
    assert set(worker_threads) != {main_thread}
    assert results[0]["backup"] != results[1]["backup"]
    assert all(result["restart_required"] is False for result in results)
    assert results[0]["changed_fields"] == ["limits.agent_llm_timeout_seconds"]
    if os.name != "nt":
        assert settings_file.stat().st_mode & 0o777 == 0o600
        assert all(path.stat().st_mode & 0o777 == 0o600 for path in settings_routes.BACKUP_DIR.iterdir())
    assert not list(settings_file.parent.glob("*.tmp"))


async def test_settings_reload_failure_atomically_restores_file_and_runtime(settings_file, monkeypatch):
    original = settings_file.read_bytes()
    reloads = []

    def reload(config):
        reloads.append(config)
        if len(reloads) == 1:
            raise RuntimeError("cannot activate")

    monkeypatch.setattr(settings_routes, "_reload_env_config", reload)
    with pytest.raises(HTTPException, match="已恢复原配置"):
        await settings_routes.update_section(
            "limits", settings_routes.SectionUpdate(config={"agent_job_timeout_seconds": 50}), user={},
        )
    assert settings_file.read_bytes() == original
    assert reloads[-1] == tomllib.loads(original.decode())
    assert not list(settings_file.parent.glob("*.tmp"))


async def test_settings_disk_failure_does_not_reload_or_replace_original(settings_file, monkeypatch):
    original = settings_file.read_bytes()

    def replace(*args):
        raise OSError("disk failure")

    def reload(config):
        raise AssertionError("failed writes must not activate")

    monkeypatch.setattr(settings_routes.os, "replace", replace)
    monkeypatch.setattr(settings_routes, "_reload_env_config", reload)
    with pytest.raises(HTTPException, match="写入配置失败"):
        await settings_routes.update_section(
            "limits", settings_routes.SectionUpdate(config={"agent_job_timeout_seconds": 50}), user={},
        )
    assert settings_file.read_bytes() == original
    assert not list(settings_file.parent.glob("*.tmp"))


async def test_cancelled_settings_request_finishes_disk_and_runtime_transaction(settings_file, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    persist = settings_routes._persist_section
    reloaded = []

    def wait_and_persist(*args):
        started.set()
        if not release.wait(timeout=5):
            raise AssertionError("test did not release write")
        return persist(*args)

    monkeypatch.setattr(settings_routes, "_persist_section", wait_and_persist)
    monkeypatch.setattr(settings_routes, "_reload_env_config", lambda config: reloaded.append(config))
    request = asyncio.create_task(settings_routes.update_section(
        "limits", settings_routes.SectionUpdate(config={"agent_job_timeout_seconds": 50}), user={},
    ))
    assert await asyncio.to_thread(started.wait, 5)
    request.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await request
    assert reloaded[-1] == tomllib.loads(settings_file.read_text())
    assert reloaded[-1]["limits"]["agent_job_timeout_seconds"] == 50
    assert not settings_routes._settings_write_lock.locked()


async def test_masked_unchanged_settings_do_not_create_backups_or_reload(settings_file, monkeypatch):
    settings_file.write_text('config_version = 2\n[dashboard]\npassword = "private-value"\n', encoding="utf-8")

    def reload(config):
        raise AssertionError("unchanged config must not reload")

    monkeypatch.setattr(settings_routes, "_reload_env_config", reload)
    result = await settings_routes.update_section(
        "dashboard", settings_routes.SectionUpdate(config={"password": "****alue"}), user={},
    )
    assert result["activation"] == "unchanged"
    assert result["changed_fields"] == []
    assert result["backup"] is None
    assert not settings_routes.BACKUP_DIR.exists()


async def test_settings_rejects_scalar_section(settings_file):
    with pytest.raises(HTTPException) as error:
        await settings_routes.get_section("config_version", user={})
    assert error.value.status_code == 422


async def test_settings_save_activates_values_and_advances_revision_once(settings_file):
    from utils.configs import EnvConfig

    before = EnvConfig.REVISION
    body = settings_routes.SectionUpdate(config={"agent_job_timeout_seconds": 50})
    updated = await settings_routes.update_section("limits", body, user={})
    assert EnvConfig.AGENT_JOB_TIMEOUT_SECONDS == 50
    assert updated["config_revision"] == before + 1 == EnvConfig.REVISION
    unchanged = await settings_routes.update_section("limits", body, user={})
    assert unchanged["config_revision"] == before + 1
    assert unchanged["activation"] == "unchanged"


def test_settings_backups_keep_latest_ten_with_unique_names(settings_file):
    names = [settings_routes._backup_config().name for _ in range(12)]
    assert len(set(names)) == 12
    backups = {path.name for path in settings_routes.BACKUP_DIR.iterdir()}
    assert backups == set(names[-10:])


async def test_settings_reader_waits_until_failed_reload_has_rolled_back(settings_file, monkeypatch):
    published = threading.Event()
    release = threading.Event()
    persist = settings_routes._persist_section
    original = tomllib.loads(settings_file.read_text())

    def persist_and_wait(*args):
        result = persist(*args)
        published.set()
        if not release.wait(timeout=5):
            raise AssertionError("test did not release activation")
        return result

    def reload(config):
        if config != original:
            raise RuntimeError("cannot activate")

    monkeypatch.setattr(settings_routes, "_persist_section", persist_and_wait)
    monkeypatch.setattr(settings_routes, "_reload_env_config", reload)
    update = asyncio.create_task(settings_routes.update_section(
        "limits", settings_routes.SectionUpdate(config={"agent_job_timeout_seconds": 50}), user={},
    ))
    assert await asyncio.to_thread(published.wait, 5)
    read = asyncio.create_task(settings_routes.get_settings(user={}))
    await asyncio.sleep(0)
    assert not read.done()
    release.set()
    with pytest.raises(HTTPException):
        await update
    assert (await read)["config"] == original
