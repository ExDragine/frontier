# ruff: noqa: S101

import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import inspect, text
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import (
    MESSAGE_SOURCE_TYPE_FORWARD_NODE,
    MESSAGE_SOURCE_TYPE_NORMAL,
    ConversationSummary,
    GroupSettings,
    GroupSettingsManager,
    Message,
    MessageAttachment,
    MessageDatabase,
    TimeStamp,
)
from utils.media import resolve_media
from utils.message_normalizer import NORMALIZED_VERSION, DerivedMessage


@pytest.fixture
def memory_engine(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    return engine


def test_ensure_message_schema_adds_normalization_columns(memory_engine):
    with memory_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE message (
                    time INTEGER NOT NULL PRIMARY KEY,
                    msg_id INTEGER,
                    user_id INTEGER NOT NULL,
                    group_id INTEGER,
                    user_name VARCHAR,
                    role VARCHAR NOT NULL,
                    content VARCHAR NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO message (time, msg_id, user_id, group_id, user_name, role, content)
                VALUES (1000, 10, 1, 123, 'Alice', 'user', 'legacy')
                """
            )
        )

    db_module.ensure_message_schema(memory_engine)

    columns = {column["name"] for column in inspect(memory_engine).get_columns("message")}
    assert {
        "raw_segments_json",
        "normalized_version",
        "normalized_status",
        "source_type",
        "parent_msg_id",
        "parent_msg_time",
        "parent_forward_id",
        "estimated_tokens",
        "token_estimate_version",
    }.issubset(columns)
    with memory_engine.connect() as conn:
        row = conn.execute(
            text("SELECT normalized_version, normalized_status, source_type FROM message WHERE time = 1000")
        ).one()
    assert row == (0, "legacy", MESSAGE_SOURCE_TYPE_NORMAL)


@pytest.mark.asyncio
async def test_conversation_context_queries_are_scope_isolated_and_versioned(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 1, 10, None, "Alice", "user", "private history")
    await database.insert(1100, 2, 10, 123, "Alice", "user", "group history")
    await database.insert(1200, 3, 20, 123, "Bob", "user", "group reply")

    private_page = await database.select_context_page(user_id=10, group_id=None)
    group_page = await database.select_context_page(user_id=10, group_id=123)
    assert [message.content for message in private_page] == ["private history"]
    assert [message.content for message in group_page] == ["group reply", "group history"]
    assert await database.context_token_total(user_id=10, group_id=None) > 0

    first = ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=1,
        source_start_time=1100,
        source_end_time=1100,
        source_message_count=1,
        source_token_count=10,
        summary_text="Alice 提出了一个问题。",
        estimated_tokens=10,
        model="summary-model",
        created_at=2000,
    )
    assert await database.append_conversation_summary(first, expected_version=0) is True
    assert (
        await database.append_conversation_summary(first.model_copy(update={"id": None}), expected_version=0) is False
    )
    latest = await database.latest_conversation_summary(scope_type="group", scope_id="123")
    assert latest is not None
    assert latest.version == 1
    assert latest.source_end_time == 1100


@pytest.mark.asyncio
async def test_message_database_select_and_prepare(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1, 101, 1, None, "u1", "user", "hello")
    await database.insert(2, 102, 1, None, "u1", "user", "world")
    await database.insert(3, 103, 1, 5, "u1", "user", "group")

    user_messages = await database.select(user_id=1)
    assert len(user_messages) == 3

    group_messages = await database.select(group_id=5)
    assert len(group_messages) == 1

    assert await database.select() is None

    prepared = await database.prepare_message(user_id=1)
    assert prepared
    assert prepared[0]["role"] == "user"


@pytest.mark.asyncio
async def test_prepare_message_references_all_available_images_without_inlining(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    for msg_time in range(1, 13):
        await database.insert(msg_time, 100 + msg_time, 1, None, "u1", "user", f"history-{msg_time}")
        await database.insert_images(msg_time, 1, None, [f"image-{msg_time}".encode()])
    await database.insert(13, 113, 1, None, "u1", "user", "current")

    prepared = await database.prepare_message(user_id=1, query_numbers=20)

    payloads = [json.loads(line) for message in prepared for line in message["content"].splitlines()]
    attachments = [attachment for payload in payloads for attachment in payload.get("attachments", [])]
    assert len(attachments) == 12
    assert all(attachment["path"].startswith("/memory/1/images/") for attachment in attachments)
    assert "base64" not in "".join(message["content"] for message in prepared)


@pytest.mark.asyncio
async def test_prepare_message_injects_images_from_message_attachments(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    image_path = Path("cache/sandbox/memory/1/images/1000_0.jpg")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"attachment-image")
    await database.insert(1000, 101, 1, None, "u1", "user", "history")
    await database.insert_attachment(
        msg_time=1000,
        msg_id=101,
        user_id=1,
        group_id=None,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/1/images/1000_0.jpg",
        file_name="1000_0.jpg",
        file_size=len(b"attachment-image"),
        expires_at=9_999_999_999_999,
    )
    await database.insert(2000, 102, 1, None, "u1", "user", "current")

    prepared = await database.prepare_message(user_id=1, query_numbers=10, before_time=2000)

    assert isinstance(prepared[0]["content"], str)
    payload = json.loads(prepared[0]["content"])
    assert payload["attachments"] == [
        {
            "kind": "image",
            "mime_type": None,
            "file_name": "1000_0.jpg",
            "path": "/memory/1/images/1000_0.jpg",
        }
    ]


@pytest.mark.asyncio
async def test_insert_images_records_memory_file_attachment(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    paths = await database.insert_images(1000, 7, 123, [b"image-bytes"])

    expected_path = Path("cache/sandbox/memory/123/images/1000_0.jpg")
    assert paths == [str(expected_path)]
    assert (tmp_path / expected_path).read_bytes() == b"image-bytes"

    attachments = await database.select_image_attachments_by_msg_time(1000)
    assert len(attachments) == 1
    attachment = attachments[0]
    assert attachment.kind == "image"
    assert attachment.physical_path == str(expected_path)
    assert attachment.virtual_path == "/memory/123/images/1000_0.jpg"
    assert attachment.file_size == len(b"image-bytes")


@pytest.mark.asyncio
async def test_repair_legacy_media_attachments_corrects_suffix_and_mime(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    image_buffer = BytesIO()
    Image.new("RGB", (2, 2), "blue").save(image_buffer, format="PNG")
    legacy_path = Path("cache/sandbox/memory/1/images/1000_0.jpg")
    (tmp_path / legacy_path).parent.mkdir(parents=True)
    (tmp_path / legacy_path).write_bytes(image_buffer.getvalue())
    await database.insert_attachment(
        msg_time=1000,
        msg_id=101,
        user_id=1,
        group_id=None,
        kind="image",
        physical_path=str(legacy_path),
        virtual_path="/memory/1/images/1000_0.jpg",
        file_name=legacy_path.name,
        file_size=len(image_buffer.getvalue()),
        expires_at=9_999_999_999_999,
        mime_type="image/jpeg",
    )

    verified, corrected = await database.repair_legacy_media_attachments()
    attachments = await database.select_image_attachments_by_msg_time(1000)

    assert (verified, corrected) == (1, 2)
    assert not (tmp_path / legacy_path).exists()
    assert (tmp_path / "cache/sandbox/memory/1/images/1000_0.png").is_file()
    assert attachments[0].file_name == "1000_0.png"
    assert attachments[0].mime_type == "image/png"
    assert json.loads(attachments[0].metadata_json)["media_type_verified"] is True
    assert await database.repair_legacy_media_attachments() == (0, 0)


@pytest.mark.asyncio
async def test_insert_media_persists_audio_and_video_with_detected_types(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    attachments = await database.insert_media(
        msg_time=1000,
        msg_id=101,
        user_id=1,
        group_id=None,
        media=[
            resolve_media(b"RIFF" + b"\x00" * 4 + b"WAVE", "audio"),
            resolve_media(b"\x00\x00\x00\x18ftypisom", "video"),
        ],
    )

    assert [(item.kind, item.mime_type) for item in attachments] == [
        ("audio", "audio/wav"),
        ("video", "video/mp4"),
    ]
    assert (tmp_path / "cache/sandbox/memory/1/audio/1000_0.wav").is_file()
    assert (tmp_path / "cache/sandbox/memory/1/videos/1000_1.mp4").is_file()


@pytest.mark.asyncio
async def test_cleanup_expired_attachments_deletes_only_db_tracked_files(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    MessageAttachment.metadata.create_all(memory_engine)

    tracked = Path("cache/sandbox/memory/123/images/expired.jpg")
    untracked = Path("cache/sandbox/memory/123/images/keep.jpg")
    (tmp_path / tracked).parent.mkdir(parents=True)
    (tmp_path / tracked).write_bytes(b"old")
    (tmp_path / untracked).write_bytes(b"keep")

    await database.insert_attachment(
        msg_time=1000,
        msg_id=50,
        user_id=7,
        group_id=123,
        kind="image",
        physical_path=str(tracked),
        virtual_path="/memory/123/images/expired.jpg",
        file_name="expired.jpg",
        file_size=3,
        expires_at=1,
    )

    deleted = await database.cleanup_expired_attachments(now_ms=2)

    assert deleted == 1
    assert not (tmp_path / tracked).exists()
    assert (tmp_path / untracked).exists()
    assert await database.select_image_attachments_by_msg_time(1000) == []


@pytest.mark.asyncio
async def test_prepare_message_before_time_excludes_current_and_later_group_messages(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 201, 10, 123, "Old", "user", "old message")
    await database.insert(2000, 202, 10, 123, "Alice", "user", "alice current")
    await database.insert(2001, 203, 20, 123, "Bob", "user", "bob concurrent")

    prepared = await database.prepare_message(user_id=10, group_id=123, query_numbers=10, before_time=2000)

    content = prepared[0]["content"]
    assert "old message" in content
    assert "alice current" not in content
    assert "bob concurrent" not in content


@pytest.mark.asyncio
async def test_prepare_message_includes_chat_scope_metadata(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 201, 10, 123, "Alice", "user", "group old")
    await database.insert(2000, 202, 10, 123, "Alice", "user", "group current")
    await database.insert(3000, 301, 20, None, "Bob", "user", "private old")
    await database.insert(4000, 302, 20, None, "Bob", "user", "private current")

    group_prepared = await database.prepare_message(user_id=10, group_id=123, query_numbers=10, before_time=2000)
    group_payload = json.loads(group_prepared[0]["content"])
    assert group_payload["metadata"]["chat_type"] == "group"
    assert group_payload["metadata"]["group_id"] == 123
    assert group_payload["metadata"]["user_id"] == "10"

    private_prepared = await database.prepare_message(user_id=20, query_numbers=10, before_time=4000)
    private_payload = json.loads(private_prepared[0]["content"])
    assert private_payload["metadata"]["chat_type"] == "private"
    assert private_payload["metadata"]["group_id"] is None
    assert private_payload["metadata"]["user_id"] == "20"


@pytest.mark.asyncio
async def test_select_by_msg_id_returns_message_from_same_group(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1, 200, 1, 10, "Alice", "user", "wrong group")
    await database.insert(2, 200, 2, 20, "Bob", "user", "quoted message")

    result = await database.select_by_msg_id(msg_id=200, group_id=20)

    assert result is not None
    assert result.content == "quoted message"


@pytest.mark.asyncio
async def test_prepare_message_excludes_forward_node_derived_records(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(
        1000,
        10,
        1,
        123,
        "Alice",
        "user",
        "parent\n[合并转发]\nBob: derived content",
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    await database.replace_derived_messages(
        parent_msg_time=1000,
        parent_msg_id=10,
        user_id=1,
        group_id=123,
        role="user",
        derived_messages=[
            DerivedMessage(
                sender_name="Bob",
                content="derived content",
                raw_segments_json="[]",
                forward_id="fwd-1",
            )
        ],
        normalized_version=NORMALIZED_VERSION,
    )
    await database.insert(2000, 11, 1, 123, "Alice", "user", "current")

    selected = await database.select(group_id=123, query_numbers=10)
    prepared = await database.prepare_message(user_id=1, group_id=123, query_numbers=10, before_time=2000)
    search_results = await database.search_messages(group_id=123, user_id=1, content_query="derived content", limit=10)

    assert all(message.source_type != MESSAGE_SOURCE_TYPE_FORWARD_NODE for message in selected)
    assert all(message.source_type == MESSAGE_SOURCE_TYPE_NORMAL for message in search_results)
    assert [message.msg_id for message in search_results] == [10]
    assert len(prepared) == 1
    assert "derived content" in prepared[0]["content"]


@pytest.mark.asyncio
async def test_search_messages_filters_history_by_scope_name_id_and_content(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 10, 1, 123, "Alice", "user", "今天讨论 Python 搜索")
    await database.insert(2000, 11, 2, 123, "Bob", "user", "无关内容")
    await database.insert(3000, 12, 1, 123, "Alice", "user", "另一个 keyword")
    await database.insert(3500, 15, 0, 123, "Assistant", "assistant", "Python 助手回答")
    await database.insert(4000, 13, 3, 999, "Mallory", "user", "Python 但在其他群")
    await database.insert(5000, 14, 1, None, "Alice", "user", "private Python")

    group_content = await database.search_messages(group_id=123, user_id=1, content_query="Python", limit=10)
    assert [message.msg_id for message in group_content] == [15, 10]

    alice_messages = await database.search_messages(group_id=123, user_id=1, target_user_name="Ali", limit=10)
    assert [message.msg_id for message in alice_messages] == [12, 10]

    exact_message = await database.search_messages(group_id=123, user_id=1, msg_id=11, limit=10)
    assert [message.user_name for message in exact_message] == ["Bob"]

    assistant_messages = await database.search_messages(group_id=123, user_id=1, role="assistant", limit=10)
    assert [message.msg_id for message in assistant_messages] == [15]

    second_page = await database.search_messages(group_id=123, user_id=1, limit=2, offset=2)
    assert [message.msg_id for message in second_page] == [11, 10]

    private_messages = await database.search_messages(group_id=None, user_id=1, content_query="Python", limit=10)
    assert [message.msg_id for message in private_messages] == [14]


@pytest.mark.asyncio
async def test_count_group_messages_since(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 10, 1, 123, "Alice", "user", "old")
    await database.insert(2000, 11, 2, 123, "Bob", "user", "recent")
    await database.insert(3000, 12, 3, 123, "Assistant", "assistant", "recent assistant")
    await database.insert(4000, 13, 4, 999, "Mallory", "user", "other group")

    count = await database.count_group_messages_since(group_id=123, since_time=1500)

    assert count == 2


@pytest.mark.asyncio
async def test_latest_group_role_message_time(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 10, 1, 123, "Assistant", "assistant", "old assistant")
    await database.insert(2000, 11, 2, 123, "Alice", "user", "user")
    await database.insert(3000, 12, 3, 123, "Assistant", "assistant", "latest assistant")
    await database.insert(4000, 13, 4, 999, "Assistant", "assistant", "other group")

    latest_time = await database.latest_group_role_message_time(group_id=123, role="assistant")

    assert latest_time == 3000


@pytest.mark.asyncio
async def test_event_database_ops(monkeypatch, memory_engine):
    database = db_module.EventDatabase()
    database.engine = memory_engine
    TimeStamp.metadata.create_all(memory_engine)

    await database.insert("event", "1")
    assert await database.select("event") == "1"
    await database.update("event", "2")
    assert await database.select("event") == "2"
    await database.delete("event")
    assert await database.select("event") is None


# ── GroupSettingsManager 测试 ────────────────────────────────


class TestGroupSettingsManager:
    def test_get_returns_empty_list_when_no_settings(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        assert manager.get(123, "wake_word") == []

    def test_set_and_get_single_wake_word(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(123, "wake_word", "小天")
        assert manager.get(123, "wake_word") == ["小天"]

    def test_set_multiple_wake_words(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(123, "wake_word", "小天")
        manager.set(123, "wake_word", "小助手")
        words = manager.get(123, "wake_word")
        assert sorted(words) == ["小助手", "小天"]

    def test_different_groups_have_different_settings(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(111, "wake_word", "群A")
        manager.set(222, "wake_word", "群B")
        assert manager.get(111, "wake_word") == ["群A"]
        assert manager.get(222, "wake_word") == ["群B"]

    def test_different_keys_are_independent(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(123, "wake_word", "小天")
        manager.set(123, "model", "gpt-4")
        assert manager.get(123, "wake_word") == ["小天"]
        assert manager.get(123, "model") == ["gpt-4"]

    def test_remove_existing_word(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(123, "wake_word", "小天")
        manager.set(123, "wake_word", "小助手")
        assert manager.remove(123, "wake_word", "小天") is True
        assert manager.get(123, "wake_word") == ["小助手"]

    def test_remove_nonexistent_word_returns_false(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        assert manager.remove(123, "wake_word", "不存在") is False

    def test_clear_removes_all_for_key(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        manager.set(123, "wake_word", "小天")
        manager.set(123, "wake_word", "小助手")
        manager.set(123, "model", "gpt-4")
        count = manager.clear(123, "wake_word")
        assert count == 2
        assert manager.get(123, "wake_word") == []
        assert manager.get(123, "model") == ["gpt-4"]  # 不影响其他 key

    def test_clear_empty_returns_zero(self, memory_engine):
        GroupSettings.metadata.create_all(memory_engine)
        manager = GroupSettingsManager(memory_engine)
        assert manager.clear(123, "wake_word") == 0
