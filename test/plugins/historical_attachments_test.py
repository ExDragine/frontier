# ruff: noqa: S101

import asyncio
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlmodel import create_engine

from plugins.agent import attachments, historical_attachments, reply_context
from plugins.agent.message_normalizer import NORMALIZED_VERSION
from plugins.agent.reply_context import MessageSource
from utils.database import Message, MessageDatabase


@pytest.fixture
def database():
    db = MessageDatabase()
    db.engine = create_engine("sqlite://")
    Message.metadata.create_all(db.engine)
    return db


async def _store(db, segments, *, group_id=123, user_id=111, sender_user_id=111, bot_user_id=999):
    return await db.insert(
        time=1000, msg_id=77, user_id=user_id, sender_user_id=sender_user_id, group_id=group_id,
        bot_user_id=bot_user_id, user_name="Alice", role="user", content="附件 " + "[图片]" * len(segments),
        raw_segments_json=json.dumps(segments), normalized_version=NORMALIZED_VERSION, normalized_status="complete",
    )


def _image_bytes(color="blue", format="PNG"):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color).save(buffer, format=format)
    return buffer.getvalue()


def _image(resource_id):
    return {"type": "image", "data": {"resource_id": resource_id}}


async def _load(db, memory_dir, *, bot=None, source=None, index=None):
    source = source or MessageSource("999", "group", 123)
    return await historical_attachments.load_historical_attachments(
        bot or object(), source, 77, db,
        workspace_key="group-123" if source.group_id is not None else "dm-456",
        memory_dir=memory_dir, attachment_index=index,
    )


@pytest.mark.asyncio
async def test_partial_download_keeps_original_indices_and_reuses_cached_selection(database, tmp_path, monkeypatch):
    segments = [{"type": "text", "data": {"text": "两张图"}}, _image("missing"), _image("dog")]
    stored = await _store(database, segments)
    calls = []

    async def download(_bot, segment):
        resource = segment["data"]["resource_id"]
        calls.append(resource)
        return _image_bytes() if resource == "dog" else None

    monkeypatch.setattr(reply_context, "_download_milky_image", download)
    result = await _load(database, tmp_path)
    assert result["sender_user_id"] == 111
    assert [(item["segment_index"], item["status"]) for item in result["attachments"]] == [(1, "unavailable"), (2, "ready")]
    path = result["attachments"][1]["path"]
    assert path.startswith("/memory/group-123/")
    records = await database.select_attachments_by_msg_time(1000, message_id=stored.message_id)
    assert len(records) == 1
    assert json.loads(records[0].metadata_json) == {"segment_index": 2}
    assert Path(records[0].physical_path).read_bytes() == _image_bytes()
    repeated = await _load(database, tmp_path, index=2)
    assert repeated["attachments"][0]["path"] == path
    assert calls == ["missing", "dog"]
    assert "error" in await _load(database, tmp_path, index=0)
    assert calls == ["missing", "dog"]


@pytest.mark.asyncio
async def test_partial_history_cache_does_not_hide_other_images_in_later_reply(database, tmp_path, monkeypatch):
    await _store(database, [_image("cat"), _image("dog")])

    async def download(_bot, segment):
        return _image_bytes("red" if segment["data"]["resource_id"] == "cat" else "blue")

    monkeypatch.setattr(reply_context, "_download_milky_image", download)
    await _load(database, tmp_path, index=1)
    _, images = await reply_context.load_message_context(object(), MessageSource("999", "group", 123), 77, database)
    assert images == [_image_bytes("red"), _image_bytes("blue")]


@pytest.mark.asyncio
async def test_file_refresh_cache_missing_file_and_private_self_sender(database, tmp_path, monkeypatch):
    await _store(database, [{"type": "file", "data": {
        "file_id": "f", "file_hash": "hash", "file_name": "report.txt", "url": "https://stale.test/file",
    }}], group_id=None, user_id=456, sender_user_id=999)
    refreshed = []

    async def refresh(**kwargs):
        refreshed.append(kwargs)
        return "https://fresh.test/file"

    async def download(url, name):
        assert url == "https://fresh.test/file" and name == "report.txt"
        return b"report data"

    monkeypatch.setattr(attachments, "_download_file_bytes", download)
    bot = SimpleNamespace(get_private_file_download_url=refresh)
    source = MessageSource("999", "friend", 456)
    first = await _load(database, tmp_path, bot=bot, source=source)
    assert first["attachments"][0]["status"] == "ready"
    await _load(database, tmp_path, bot=bot, source=source)
    assert refreshed == [{"user_id": 456, "file_id": "f", "file_hash": "hash", "is_self_send": True}]
    Path(next(tmp_path.rglob("report.txt"))).unlink()
    await _load(database, tmp_path, bot=bot, source=source)
    assert len(refreshed) == 2


@pytest.mark.asyncio
async def test_platform_only_history_is_persisted_without_prefetching_all_images(database, tmp_path, monkeypatch):
    fetches = []

    async def fetch(**kwargs):
        fetches.append(kwargs)
        return SimpleNamespace(
            message_seq=77, sender_id=111, time=1, friend=None, group_member=None,
            segments=[_image(str(i)) for i in range(6)],
        )

    downloads = []

    async def download(_bot, segment):
        downloads.append(segment["data"]["resource_id"])
        return _image_bytes()

    monkeypatch.setattr(reply_context, "_download_milky_image", download)
    result = await _load(database, tmp_path, bot=SimpleNamespace(get_message=fetch))
    assert len(result["attachment_refs"]) == 6 and len(result["attachments"]) == 4
    assert downloads == ["0", "1", "2", "3"]
    assert fetches == [{"message_scene": "group", "peer_id": 123, "message_seq": 77}]


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [RuntimeError("db failure"), asyncio.CancelledError()])
async def test_index_failure_cleans_staged_bytes(database, tmp_path, monkeypatch, error):
    await _store(database, [_image("one")])

    async def download(*args):
        return _image_bytes()

    async def fail(**kwargs):
        raise error

    monkeypatch.setattr(reply_context, "_download_milky_image", download)
    monkeypatch.setattr(database, "insert_attachment", fail)
    if isinstance(error, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await _load(database, tmp_path)
    else:
        result = await _load(database, tmp_path)
        assert result["attachments"][0]["status"] == "unavailable"
    assert not [path for path in (tmp_path / "files").rglob("*") if path.is_file()]


@pytest.mark.asyncio
async def test_other_bot_record_is_not_read(database, tmp_path):
    await _store(database, [_image("one")], bot_user_id=888)
    assert "error" in await _load(database, tmp_path)


@pytest.mark.asyncio
async def test_legacy_unsupported_image_cache_is_converted_for_read_file(database, tmp_path, monkeypatch):
    stored = await _store(database, [_image("offline")])
    old = await attachments.stage_message_bytes(
        _image_bytes(format="BMP"), "legacy_0.bmp", memory_dir=tmp_path, workspace_key="group-123", message_id=stored.message_id,
    )
    await database.insert_attachment(
        msg_time=1000, message_id=stored.message_id, msg_id=77, user_id=111, group_id=123, kind="image",
        physical_path=str(old.local_path), virtual_path=old.virtual_path, file_name=old.file_name,
        mime_type="image/bmp", file_size=old.file_size, expires_at=9999999999999,
    )

    async def no_network(*args):
        pytest.fail("a valid cache should not need the platform")

    monkeypatch.setattr(reply_context, "_download_milky_image", no_network)
    result = await _load(database, tmp_path)
    item = result["attachments"][0]
    assert item["status"] == "ready" and item["path"].endswith(".jpg")
    assert item["mime_type"] == "image/jpeg"
    assert old.local_path.read_bytes()[:2] == b"BM"
    records = await database.select_attachments_by_msg_time(1000, message_id=stored.message_id)
    assert len(records) == 1 and records[0].virtual_path == item["path"]
    with Image.open(tmp_path / item["path"].removeprefix("/memory/group-123/")) as image:
        assert image.format == "JPEG"


@pytest.mark.asyncio
async def test_invalid_image_is_not_reported_as_readable(database, tmp_path, monkeypatch):
    await _store(database, [_image("broken")])

    async def download(*args):
        return b"<html>expired resource</html>"

    monkeypatch.setattr(reply_context, "_download_milky_image", download)
    result = await _load(database, tmp_path)
    assert result["attachments"][0]["status"] == "unavailable"
    assert not (tmp_path / "files").exists()


@pytest.mark.asyncio
async def test_normal_history_exposes_refs_without_downloading_or_foreign_paths(database):
    await _store(database, [_image("offline")])
    message = await database.select_by_msg_id(msg_id=77, group_id=123)
    history = await database.prepare_message_records([message], accessible_workspace_key="group-123")
    payload = json.loads(history[0]["content"])
    assert payload["attachment_refs"] == [{"segment_index": 0, "kind": "image"}]
    assert "offline" not in history[0]["content"]
    foreign = await database.prepare_message_records([message], accessible_workspace_key="dm-111")
    assert "attachment_refs" not in json.loads(foreign[0]["content"])


@pytest.mark.asyncio
async def test_legacy_text_only_record_refreshes_original_segments(database, tmp_path, monkeypatch):
    await database.insert(
        time=1000, msg_id=77, user_id=111, group_id=123, user_name="Alice",
        bot_user_id=999, role="user", content="[图片]", normalized_status="legacy",
    )

    async def fetch(**kwargs):
        return SimpleNamespace(segments=[_image("old")])

    async def download(*args):
        return _image_bytes()

    monkeypatch.setattr(reply_context, "_download_milky_image", download)
    result = await _load(database, tmp_path, bot=SimpleNamespace(get_message=fetch))
    assert result["attachments"][0]["status"] == "ready"
    record = await database.select_by_msg_id(msg_id=77, group_id=123)
    assert json.loads(record.raw_segments_json) == [_image("old")]
