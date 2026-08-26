# ruff: noqa: S101

import types
from pathlib import Path
from typing import Any, cast

import pytest
from sqlmodel import create_engine

from utils import database as db_module
from utils import message as message_module
from utils.configs import EnvConfig
from utils.database import Message, MessageAttachment, MessageDatabase
from utils.message_normalizer import NORMALIZED_VERSION, segments_to_raw_json
from utils.reply_context import (
    _format_quote,
    build_reply_context,
    hydrate_recent_media_context,
    requests_recent_media,
)


async def _async_result(value):
    return value


async def _build_reply_context(
    bot: object,
    event: object,
    reply_seq: int,
    group_id: int | None,
    messages_db: object,
    *,
    load_images: bool = True,
    workspace_key: str | None = None,
    memory_dir: str | Path | None = None,
):
    """Adapt structurally complete test doubles at the production API boundary."""
    return await build_reply_context(
        bot,
        cast(Any, event),
        reply_seq,
        group_id,
        cast(Any, messages_db),
        load_images=load_images,
        workspace_key=workspace_key,
        memory_dir=memory_dir,
    )


def test_partial_quoted_image_persistence_keeps_all_original_markers():
    payload = _format_quote(
        message_id=1,
        role="user",
        user_id=10,
        display_name="Alice",
        nickname=None,
        card=None,
        text="[图片:猫]\n[图片:狗]",
        image_count=1,
        missing_images=0,
    )

    assert payload["content"] == "[图片:猫]\n[图片:狗]\n[引用消息包含图片 1 张]"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("帮我分析一下", True),
        ("看看刚才的文件", True),
        ("summarize it", True),
        ("今天天气怎么样", False),
    ],
)
def test_requests_recent_media_is_deterministic(text, expected):
    assert requests_recent_media(text) is expected


@pytest.mark.asyncio
async def test_hydrate_recent_media_context_reuses_reply_hydrator(monkeypatch, tmp_path):
    from utils import reply_context

    calls = {}

    class DummyMessagesDb:
        async def select_recent_media_message(self, **kwargs):
            calls["select"] = kwargs
            return types.SimpleNamespace(msg_id=77)

    async def fake_build_reply_context(*args, **kwargs):
        calls["hydrate"] = (args, kwargs)
        return {"attachments": [{"kind": "file", "path": "/memory/group-123/report.txt"}]}, [b"image"]

    monkeypatch.setattr(reply_context, "build_reply_context", fake_build_reply_context)
    event = types.SimpleNamespace(data=types.SimpleNamespace(message_scene="group", peer_id=123))
    images, found = await hydrate_recent_media_context(
        object(),
        cast(Any, event),
        user_id=111,
        group_id=123,
        before_time=1_000_000,
        messages_db=cast(Any, DummyMessagesDb()),
        workspace_key="group-123",
        memory_dir=tmp_path / "group-123",
    )

    assert found is True
    assert images == [b"image"]
    assert calls["select"] == {
        "user_id": 111,
        "group_id": 123,
        "before_time": 1_000_000,
        "after_time": 700_000,
        "limit": 20,
    }
    assert calls["hydrate"][0][2:4] == (77, 123)
    assert calls["hydrate"][1]["workspace_key"] == "group-123"


@pytest.mark.asyncio
async def test_build_reply_context_expands_forwarded_messages_into_message_db():
    inserted = {}

    class DummyMessagesDb:
        async def select_by_msg_id(self, *, msg_id, group_id):
            return None

        async def insert(self, **kwargs):
            inserted.update(kwargs)

        async def replace_derived_messages(self, **kwargs):
            inserted["derived_messages"] = kwargs["derived_messages"]

        async def insert_images(self, **_kwargs):
            raise AssertionError("forward text expansion should not create image files")

    class DummyBot:
        async def get_message(self, **_kwargs):
            return types.SimpleNamespace(
                message_seq=900,
                sender_id=111,
                time=1714521600,
                segments=[
                    {
                        "type": "forward",
                        "data": {
                            "forward_id": "outer",
                            "title": "聊天记录",
                            "summary": "2条消息",
                        },
                    }
                ],
                group_member=types.SimpleNamespace(nickname="Alice", card="项目经理"),
                friend=None,
            )

        async def get_forwarded_messages(self, *, forward_id):
            if forward_id == "outer":
                return [
                    types.SimpleNamespace(
                        message_seq=1,
                        sender_name="Bob",
                        time=1714521601,
                        segments=[{"type": "text", "data": {"text": "外层消息"}}],
                    ),
                    types.SimpleNamespace(
                        message_seq=2,
                        sender_name="Carol",
                        time=1714521602,
                        segments=[
                            {
                                "type": "forward",
                                "data": {
                                    "forward_id": "inner",
                                    "title": "嵌套聊天",
                                    "summary": "1条消息",
                                },
                            }
                        ],
                    ),
                ]
            if forward_id == "inner":
                return [
                    types.SimpleNamespace(
                        message_seq=3,
                        sender_name="Dana",
                        time=1714521603,
                        segments=[{"type": "text", "data": {"text": "内层消息"}}],
                    )
                ]
            raise AssertionError(f"unexpected forward_id={forward_id}")

    event = types.SimpleNamespace(
        self_id="1",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(DummyBot(), event, 900, 123, DummyMessagesDb())

    assert images == []
    assert quote_payload is not None
    assert quote_payload["schema"] == "frontier.qq_message_ref.v1"
    assert quote_payload["sender"]["user_id"] == "111"
    assert quote_payload["sender"]["display_name"] == "项目经理"
    assert quote_payload["sender"]["nickname"] == "Alice"
    assert "Bob: 外层消息" in quote_payload["content"]
    assert "Carol: [合并转发:嵌套聊天 - 1条消息]" in quote_payload["content"]
    assert "Dana: 内层消息" in quote_payload["content"]
    assert inserted["content"].count("内层消息") == 1
    assert inserted["content"] in quote_payload["content"]
    assert len(inserted["derived_messages"]) == 3


@pytest.mark.asyncio
async def test_private_reply_context_selects_only_current_peer(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    await database.insert(1000, 7, 111, None, "Alice", "user", "Alice private")
    await database.insert(2000, 7, 222, None, "Bob", "user", "Bob private")

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise AssertionError("peer-scoped database record should be used")

    event = types.SimpleNamespace(
        self_id="999",
        reply=None,
        data=types.SimpleNamespace(message_scene="friend", peer_id=111),
    )

    quote_payload, images = await _build_reply_context(
        DummyBot(),
        event,
        7,
        None,
        database,
        load_images=False,
    )

    assert images == []
    assert quote_payload is not None
    assert quote_payload["sender"]["user_id"] == "111"
    assert quote_payload["content"] == "Alice private"


@pytest.mark.asyncio
async def test_fetched_private_assistant_quote_separates_scope_and_sender():
    inserted = {}

    class DummyMessagesDb:
        async def select_by_msg_id(self, *, msg_id, group_id, peer_user_id):
            assert (msg_id, group_id, peer_user_id) == (7, None, 111)
            return None

        async def insert(self, **kwargs):
            inserted.update(kwargs)

        async def replace_derived_messages(self, **_kwargs):
            return None

    class DummyBot:
        async def get_message(self, **_kwargs):
            return types.SimpleNamespace(
                message_seq=7,
                sender_id=999,
                time=1714521600,
                segments=[{"type": "text", "data": {"text": "机器人旧回复"}}],
                group_member=None,
                friend=types.SimpleNamespace(nickname="Frontier"),
            )

    event = types.SimpleNamespace(
        self_id="999",
        reply=None,
        data=types.SimpleNamespace(message_scene="friend", peer_id=111),
    )

    quote_payload, images = await _build_reply_context(
        DummyBot(),
        event,
        7,
        None,
        DummyMessagesDb(),
        load_images=False,
    )

    assert images == []
    assert inserted["user_id"] == 111
    assert inserted["sender_user_id"] == 999
    assert inserted["bot_user_id"] == 999
    assert inserted["directly_mentions_bot"] is False
    assert inserted["role"] == "assistant"
    assert quote_payload is not None
    assert quote_payload["sender"]["user_id"] == "999"
    assert quote_payload["sender"]["display_name"] == EnvConfig.BOT_NAME


@pytest.mark.asyncio
async def test_build_reply_context_loads_quoted_images_from_attachments(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    MessageAttachment.metadata.create_all(engine)

    image_path = Path("cache/sandbox/memory/123/images/500_0.jpg")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"quoted-image")
    await database.insert(
        time=500,
        msg_id=900,
        user_id=111,
        group_id=123,
        user_name="Alice",
        role="user",
        content="看图",
    )
    await database.insert_attachment(
        msg_time=500,
        msg_id=900,
        user_id=111,
        group_id=123,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/123/images/500_0.jpg",
        file_name="500_0.jpg",
        file_size=len(b"quoted-image"),
        expires_at=9_999_999_999_999,
    )

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise AssertionError("cached attachment should avoid fetching quoted message")

    event = types.SimpleNamespace(
        self_id="1",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(DummyBot(), event, 900, 123, database)

    assert images == [b"quoted-image"]
    assert quote_payload is not None
    assert quote_payload["sender"]["display_name"] == "Alice"
    assert "[图片]" not in quote_payload["content"]
    assert "[引用消息包含图片 1 张]" in quote_payload["content"]
    assert quote_payload["media"] == {"image_count": 1}


@pytest.mark.asyncio
async def test_build_reply_context_reuses_cached_quoted_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)

    memory_dir = tmp_path / "cache/sandbox/memory/group-123"
    file_path = memory_dir / "files/500/report.pdf"
    file_path.parent.mkdir(parents=True)
    file_path.write_bytes(b"quoted-file")
    await database.insert(
        time=500,
        msg_id=900,
        user_id=111,
        group_id=123,
        user_name="Alice",
        role="user",
        content="[文件:report.pdf (11字节)]",
        raw_segments_json=segments_to_raw_json(
            [{"type": "file", "data": {"file_id": "file-1", "file_name": "report.pdf", "file_size": 11}}]
        ),
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    await database.insert_attachment(
        msg_time=500,
        msg_id=900,
        user_id=111,
        group_id=123,
        kind="file",
        physical_path=str(file_path),
        virtual_path="/memory/group-123/files/500/report.pdf",
        file_name="report.pdf",
        file_size=11,
        mime_type="application/pdf",
        expires_at=9_999_999_999_999,
    )

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise AssertionError("cached file should avoid fetching quoted message")

        async def get_group_file_download_url(self, **_kwargs):
            raise AssertionError("cached file should avoid refreshing its URL")

    event = types.SimpleNamespace(
        self_id="999",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )
    quote_payload, images = await _build_reply_context(
        DummyBot(),
        event,
        900,
        123,
        database,
        workspace_key="group-123",
        memory_dir=memory_dir,
    )

    assert images == []
    assert quote_payload is not None
    assert quote_payload["attachments"] == [
        {
            "kind": "file",
            "file_name": "report.pdf",
            "path": "/memory/group-123/files/500/report.pdf",
            "mime_type": "application/pdf",
        }
    ]


@pytest.mark.asyncio
async def test_build_reply_context_downloads_and_indexes_quoted_group_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    file_segment = {
        "type": "file",
        "data": {
            "file_id": "file-1",
            "file_name": "report.txt",
            "file_size": 11,
            "temp_url": "https://expired.example/report.txt",
        },
    }
    await database.insert(
        time=500,
        msg_id=900,
        user_id=111,
        group_id=123,
        user_name="Alice",
        role="user",
        content="[文件:report.txt (11字节)]",
        raw_segments_json=segments_to_raw_json([file_segment]),
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    calls: list[tuple] = []

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise AssertionError("stored raw segments should be sufficient")

        async def get_group_file_download_url(self, *, group_id, file_id):
            calls.append(("refresh", group_id, file_id))
            return "https://fresh.example/report.txt"

    async def fake_get(url):
        calls.append(("download", url))
        return types.SimpleNamespace(content=b"quoted-file")

    monkeypatch.setattr(message_module.httpx_client, "get", fake_get)
    event = types.SimpleNamespace(
        self_id="999",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )
    memory_dir = tmp_path / "cache/sandbox/memory/group-123"

    phase_one_payload, phase_one_images = await _build_reply_context(
        DummyBot(),
        event,
        900,
        123,
        database,
        load_images=False,
        workspace_key="group-123",
        memory_dir=memory_dir,
    )
    assert phase_one_payload is not None
    assert "attachments" not in phase_one_payload
    assert phase_one_images == []
    assert calls == []

    quote_payload, images = await _build_reply_context(
        DummyBot(),
        event,
        900,
        123,
        database,
        workspace_key="group-123",
        memory_dir=memory_dir,
    )

    assert images == []
    assert calls == [
        ("refresh", 123, "file-1"),
        ("download", "https://fresh.example/report.txt"),
    ]
    assert quote_payload is not None
    assert quote_payload["attachments"][0]["path"] == "/memory/group-123/files/500/report.txt"
    assert (memory_dir / "files/500/report.txt").read_bytes() == b"quoted-file"
    records = await database.select_attachments_by_msg_time(500)
    assert [(record.kind, record.file_name) for record in records] == [("file", "report.txt")]


@pytest.mark.asyncio
async def test_build_reply_context_refreshes_private_quoted_file_with_peer_hash(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    await database.insert(
        time=500,
        msg_id=900,
        user_id=111,
        group_id=None,
        user_name="Alice",
        role="user",
        content="[文件:private.txt (12字节)]",
        raw_segments_json=segments_to_raw_json(
            [
                {
                    "type": "file",
                    "data": {
                        "file_id": "private-1",
                        "file_hash": "hash-1",
                        "file_name": "private.txt",
                        "file_size": 12,
                    },
                }
            ]
        ),
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    calls: list[tuple] = []

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise AssertionError("stored raw segments should be sufficient")

        async def get_private_file_download_url(self, *, user_id, file_id, file_hash):
            calls.append((user_id, file_id, file_hash))
            return "https://fresh.example/private.txt"

    async def fake_get(url):
        assert url == "https://fresh.example/private.txt"
        return types.SimpleNamespace(content=b"private-file")

    monkeypatch.setattr(message_module.httpx_client, "get", fake_get)
    event = types.SimpleNamespace(
        self_id="999",
        reply=None,
        data=types.SimpleNamespace(message_scene="friend", peer_id=111),
    )
    memory_dir = tmp_path / "cache/sandbox/memory/dm-111"
    quote_payload, images = await _build_reply_context(
        DummyBot(),
        event,
        900,
        None,
        database,
        workspace_key="dm-111",
        memory_dir=memory_dir,
    )

    assert images == []
    assert calls == [(111, "private-1", "hash-1")]
    assert quote_payload is not None
    assert quote_payload["attachments"][0]["path"] == "/memory/dm-111/files/500/private.txt"
    assert (memory_dir / "files/500/private.txt").read_bytes() == b"private-file"


@pytest.mark.asyncio
async def test_build_reply_context_marks_unavailable_unindexed_image():
    class DummyMessagesDb:
        async def select_by_msg_id(self, *, msg_id, group_id):
            assert (msg_id, group_id) == (900, 123)
            return types.SimpleNamespace(
                time=500,
                msg_id=900,
                user_id=111,
                group_id=123,
                user_name="Alice",
                role="user",
                content="[图片:照片]",
                raw_segments_json=None,
                normalized_version=NORMALIZED_VERSION,
                normalized_status="complete",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            return []

        def load_attachment_files(self, records):
            assert records == []
            return [], 0

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise RuntimeError("quoted message expired")

    event = types.SimpleNamespace(
        self_id="1",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(DummyBot(), event, 900, 123, DummyMessagesDb())

    assert images == []
    assert quote_payload is not None
    assert "[图片:照片]" not in quote_payload["content"]
    assert "[引用消息包含图片，但图片已失效]" in quote_payload["content"]


@pytest.mark.asyncio
async def test_build_reply_context_restores_image_directly_from_raw_milky_segments(monkeypatch):
    from utils import reply_context

    cached = {}

    class DummyMessagesDb:
        async def select_by_msg_id(self, *, msg_id, group_id):
            return types.SimpleNamespace(
                time=500,
                msg_id=msg_id,
                user_id=111,
                group_id=group_id,
                user_name="Alice",
                user_nickname=None,
                user_card=None,
                sender_user_id=111,
                role="user",
                content="[图片:照片]",
                raw_segments_json=segments_to_raw_json(
                    [
                        {
                            "type": "image",
                            "data": {
                                "resource_id": "resource-1",
                                "temp_url": "https://expired.example/image.jpg",
                                "summary": "照片",
                            },
                        }
                    ]
                ),
                normalized_version=NORMALIZED_VERSION,
                normalized_status="complete",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            return []

        def load_attachment_files(self, records):
            assert records == []
            return [], 0

        async def insert_images(self, **kwargs):
            cached.update(kwargs)

    class DummyBot:
        async def get_message(self, **_kwargs):
            raise AssertionError("raw Milky segments should avoid fetching the whole message")

        async def get_resource_temp_url(self, *, resource_id):
            assert resource_id == "resource-1"
            return "https://fresh.example/image.jpg"

    async def fake_get(url):
        if "expired" in url:
            raise RuntimeError("expired")
        assert url == "https://fresh.example/image.jpg"
        return types.SimpleNamespace(content=b"restored-image")

    monkeypatch.setattr(reply_context._httpx_client, "get", fake_get)
    monkeypatch.setattr(EnvConfig, "IMAGE_ENABLED", True)
    event = types.SimpleNamespace(
        self_id="999",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(
        DummyBot(), event, 900, 123, DummyMessagesDb()
    )

    assert images == [b"restored-image"]
    assert cached["images"] == [b"restored-image"]
    assert quote_payload is not None
    assert quote_payload["media"] == {"image_count": 1}


@pytest.mark.asyncio
async def test_reply_image_cache_failure_keeps_markers_and_still_uses_fetched_image(monkeypatch):
    from utils import reply_context

    class DummyMessagesDb:
        async def select_by_msg_id(self, *, msg_id, group_id):
            assert (msg_id, group_id) == (900, 123)
            return types.SimpleNamespace(
                time=500,
                msg_id=900,
                user_id=111,
                group_id=123,
                user_name="Alice",
                user_nickname=None,
                user_card=None,
                sender_user_id=111,
                role="user",
                content="[图片:照片]",
                raw_segments_json=None,
                normalized_version=NORMALIZED_VERSION,
                normalized_status="complete",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            return []

        def load_attachment_files(self, records):
            assert records == []
            return [], 0

        async def insert_images(self, **_kwargs):
            raise OSError("disk full")

    class DummyBot:
        async def get_message(self, **_kwargs):
            return types.SimpleNamespace(message_seq=900)

    monkeypatch.setattr(
        reply_context,
        "_extract_milky_message_content",
        lambda *_args, **_kwargs: _async_result(("[图片:照片]", [b"fetched-image"], 0)),
    )
    monkeypatch.setattr(EnvConfig, "IMAGE_ENABLED", True)
    event = types.SimpleNamespace(
        self_id="1",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(DummyBot(), event, 900, 123, DummyMessagesDb())

    assert images == [b"fetched-image"]
    assert quote_payload is not None
    assert quote_payload["content"] == "[图片:照片]"
    assert "media" not in quote_payload


@pytest.mark.asyncio
async def test_partial_reply_image_cache_is_not_overwritten_by_remote_subset(monkeypatch):
    from utils import reply_context

    insert_called = False

    class DummyMessagesDb:
        async def select_by_msg_id(self, *, msg_id, group_id):
            return types.SimpleNamespace(
                time=500,
                msg_id=msg_id,
                user_id=111,
                group_id=group_id,
                user_name="Alice",
                user_nickname=None,
                user_card=None,
                sender_user_id=111,
                role="user",
                content="[图片:甲]\n[图片:乙]",
                raw_segments_json=None,
                normalized_version=NORMALIZED_VERSION,
                normalized_status="complete",
            )

        async def select_image_attachments_by_msg_time(self, _msg_time):
            return [types.SimpleNamespace(file_name="500_0.jpg")]

        def load_attachment_files(self, _records):
            return [b"cached-image"], 1

        async def insert_images(self, **_kwargs):
            nonlocal insert_called
            insert_called = True

    class DummyBot:
        async def get_message(self, **_kwargs):
            return types.SimpleNamespace(message_seq=900)

    monkeypatch.setattr(
        reply_context,
        "_extract_milky_message_content",
        lambda *_args, **_kwargs: _async_result(("", [b"remote-a", b"remote-b"], 0)),
    )
    event = types.SimpleNamespace(
        self_id="1",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(DummyBot(), event, 900, 123, DummyMessagesDb())

    assert images == [b"remote-a", b"remote-b"]
    assert insert_called is False
    assert quote_payload is not None
    assert quote_payload["media"] == {"image_count": 1, "missing_image_count": 1}


@pytest.mark.asyncio
async def test_build_reply_context_rebuilds_stale_forward_quote_from_raw_segments(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)

    await database.insert(
        time=500,
        msg_id=900,
        user_id=111,
        group_id=123,
        user_name="Alice",
        role="user",
        content="[合并转发:旧标题 - 旧摘要]",
        raw_segments_json=segments_to_raw_json(
            [
                {
                    "type": "forward",
                    "data": {"forward_id": "outer", "title": "新标题", "summary": "1条"},
                }
            ]
        ),
        normalized_version=0,
        normalized_status="complete",
    )

    class DummyBot:
        async def get_forwarded_messages(self, *, forward_id):
            assert forward_id == "outer"
            return [
                types.SimpleNamespace(
                    sender_name="Bob",
                    time=1714521600,
                    segments=[{"type": "text", "data": {"text": "完整内容"}}],
                )
            ]

        async def get_message(self, **_kwargs):
            raise AssertionError("raw_segments_json should be enough to rebuild")

    event = types.SimpleNamespace(
        self_id="1",
        reply=None,
        data=types.SimpleNamespace(message_scene="group", peer_id=123),
    )

    quote_payload, images = await _build_reply_context(DummyBot(), event, 900, 123, database)
    stored = await database.select_by_msg_id(msg_id=900, group_id=123)

    assert images == []
    assert quote_payload is not None
    assert "Bob: 完整内容" in quote_payload["content"]
    assert "旧摘要" not in quote_payload["content"]
    assert stored is not None
    assert stored.normalized_version == NORMALIZED_VERSION
    assert "Bob: 完整内容" in stored.content
