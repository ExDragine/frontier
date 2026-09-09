# ruff: noqa: S101

import asyncio
import threading
from types import SimpleNamespace

import pytest

from utils import message


async def _stage(tmp_path, *, message_id, value):
    return await message.stage_message_files(
        object(),
        [
            message.MessageFileItem(
                file_id=None, file_name="report.txt", file_size=1, url=f"https://example.com/{value}"
            )
        ],
        memory_dir=tmp_path,
        workspace_key="group-1",
        message_time=123,
        message_id=message_id,
        user_id="2",
        group_id=1,
    )


@pytest.fixture
def downloaded_files(monkeypatch):
    async def download(url):
        return SimpleNamespace(content=url.rsplit("/", 1)[-1].encode())

    monkeypatch.setattr(message.httpx_client, "get", download)


@pytest.mark.asyncio
async def test_same_millisecond_messages_have_distinct_staging_paths(downloaded_files, tmp_path):
    first, second = await asyncio.gather(
        _stage(tmp_path, message_id=10, value="first"),
        _stage(tmp_path, message_id=11, value="second"),
    )

    assert first[0].virtual_path == "/memory/group-1/files/123-m10/report.txt"
    assert second[0].virtual_path == "/memory/group-1/files/123-m11/report.txt"
    assert first[0].local_path.read_bytes() == b"first"
    assert second[0].local_path.read_bytes() == b"second"


@pytest.mark.asyncio
async def test_concurrent_restoration_reserves_paths_before_worker_writes(downloaded_files, monkeypatch, tmp_path):
    barrier = threading.Barrier(2)
    original = message._write_staged_file

    def write(path, data):
        barrier.wait(timeout=3)
        original(path, data)

    monkeypatch.setattr(message, "_write_staged_file", write)
    first, second = await asyncio.gather(
        _stage(tmp_path, message_id=10, value="first"),
        _stage(tmp_path, message_id=10, value="second"),
    )

    assert first[0].local_path != second[0].local_path
    assert first[0].local_path.read_bytes() == b"first"
    assert second[0].local_path.read_bytes() == b"second"


@pytest.mark.asyncio
async def test_cancelled_write_finishes_before_staging_cleanup(downloaded_files, monkeypatch, tmp_path):
    started = threading.Event()
    release = threading.Event()
    original = message._write_staged_file

    def write(path, data):
        started.set()
        if not release.wait(timeout=3):
            raise AssertionError("test did not release writer")
        original(path, data)

    monkeypatch.setattr(message, "_write_staged_file", write)
    task = asyncio.create_task(_stage(tmp_path, message_id=10, value="first"))
    try:
        assert await asyncio.to_thread(started.wait, 3)
        task.cancel()
        await asyncio.sleep(0)
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert list(tmp_path.rglob("*.txt")) == []
