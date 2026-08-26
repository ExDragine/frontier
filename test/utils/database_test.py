# ruff: noqa: S101

import asyncio
import json
import threading
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import event, inspect, text
from sqlmodel import Session, create_engine, select

from utils import database as db_module
from utils.agents.message_envelope import (
    build_agent_attachment_payload,
    build_agent_message_payload,
    serialize_agent_payload,
)
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
    migrate_legacy_attachment_workspaces,
    migrate_legacy_scope_directories,
)
from utils.media import resolve_media
from utils.message_normalizer import NORMALIZED_VERSION, DerivedMessage


@pytest.fixture
def memory_engine(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    return engine


def _wire_text(message: dict[str, object]) -> str:
    content = message["content"]
    if isinstance(content, str):
        return content
    assert isinstance(content, list) and len(content) == 1
    block = content[0]
    assert isinstance(block, dict) and block.get("type") == "text"
    return str(block["text"])


def _wire_payload(message: dict[str, object]) -> dict:
    return json.loads(_wire_text(message))


def test_legacy_attachments_migrate_to_distinct_group_and_private_workspaces(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    legacy_root = Path("cache/sandbox/memory/123/images")
    (tmp_path / legacy_root).mkdir(parents=True)
    (tmp_path / legacy_root / "group.png").write_bytes(b"group")
    (tmp_path / legacy_root / "private.png").write_bytes(b"private")

    with Session(memory_engine) as session:
        session.add_all(
            [
                Message(
                    time=1000,
                    msg_id=1,
                    user_id=9,
                    group_id=123,
                    user_name="Group member",
                    role="user",
                    content="[图片]",
                ),
                Message(
                    time=2000,
                    msg_id=2,
                    user_id=123,
                    group_id=None,
                    user_name="Private peer",
                    role="user",
                    content="[图片]",
                ),
                MessageAttachment(
                    msg_time=1000,
                    msg_id=1,
                    user_id=9,
                    group_id=123,
                    workspace_key="123",
                    kind="image",
                    file_name="group.png",
                    physical_path=str(legacy_root / "group.png"),
                    virtual_path="/memory/123/images/group.png",
                    created_at=1000,
                    expires_at=9_999_999_999_999,
                ),
                MessageAttachment(
                    msg_time=2000,
                    msg_id=2,
                    user_id=123,
                    group_id=None,
                    workspace_key="123",
                    kind="image",
                    file_name="private.png",
                    physical_path=str(legacy_root / "private.png"),
                    virtual_path="/memory/123/images/private.png",
                    created_at=2000,
                    expires_at=9_999_999_999_999,
                ),
            ]
        )
        session.commit()

    assert migrate_legacy_attachment_workspaces(memory_engine) == 2

    with Session(memory_engine) as session:
        attachments = session.exec(select(MessageAttachment).order_by(MessageAttachment.msg_time)).all()
        messages = session.exec(select(Message).order_by(Message.time)).all()
    assert [attachment.workspace_key for attachment in attachments] == ["group-123", "dm-123"]
    assert [attachment.virtual_path for attachment in attachments] == [
        "/memory/group-123/images/group.png",
        "/memory/dm-123/images/private.png",
    ]
    assert (tmp_path / "cache/sandbox/memory/group-123/images/group.png").read_bytes() == b"group"
    assert (tmp_path / "cache/sandbox/memory/dm-123/images/private.png").read_bytes() == b"private"
    assert not (tmp_path / legacy_root / "group.png").exists()
    assert not (tmp_path / legacy_root / "private.png").exists()
    assert all(message.token_estimate_version == db_module.MESSAGE_TOKEN_ESTIMATE_VERSION for message in messages)


def test_unambiguous_legacy_soul_and_workspace_are_migrated(memory_engine, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Message.metadata.create_all(memory_engine)
    with Session(memory_engine) as session:
        session.add(
            Message(
                time=1000,
                msg_id=1,
                user_id=9,
                group_id=123,
                user_name="Member",
                role="user",
                content="hello",
            )
        )
        session.commit()

    legacy_memory = tmp_path / "cache/sandbox/memory/123"
    legacy_workspace = tmp_path / "cache/sandbox/workspaces/123"
    (legacy_memory / "notes").mkdir(parents=True)
    legacy_workspace.mkdir(parents=True)
    (legacy_memory / "SOUL.md").write_text("旧群聊人设", encoding="utf-8")
    (legacy_memory / "notes/context.md").write_text("上下文", encoding="utf-8")
    (legacy_workspace / "result.txt").write_text("工作结果", encoding="utf-8")

    assert migrate_legacy_scope_directories(memory_engine) == (1, 0)

    assert not legacy_memory.exists()
    assert not legacy_workspace.exists()
    assert (tmp_path / "cache/sandbox/memory/group-123/SOUL.md").read_text(encoding="utf-8") == "旧群聊人设"
    assert (tmp_path / "cache/sandbox/memory/group-123/notes/context.md").read_text(encoding="utf-8") == "上下文"
    assert (tmp_path / "cache/sandbox/workspaces/group-123/result.txt").read_text(encoding="utf-8") == "工作结果"


def test_legacy_attachment_source_is_kept_while_any_row_still_references_it(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    source_path = Path("cache/sandbox/memory/123/files/shared.txt")
    (tmp_path / source_path).parent.mkdir(parents=True)
    (tmp_path / source_path).write_text("shared", encoding="utf-8")
    with Session(memory_engine) as session:
        session.add_all(
            [
                MessageAttachment(
                    msg_time=1000,
                    user_id=9,
                    group_id=123,
                    workspace_key="123",
                    kind="file",
                    file_name="shared.txt",
                    physical_path=str(source_path),
                    virtual_path="/memory/123/files/shared.txt",
                    created_at=1000,
                    expires_at=9_999_999_999_999,
                ),
                MessageAttachment(
                    msg_time=2000,
                    user_id=9,
                    group_id=123,
                    workspace_key="external",
                    kind="file",
                    file_name="shared.txt",
                    physical_path=str(source_path),
                    virtual_path="/external/shared.txt",
                    created_at=1000,
                    expires_at=9_999_999_999_999,
                ),
            ]
        )
        session.commit()

    assert migrate_legacy_attachment_workspaces(memory_engine) == 1

    assert (tmp_path / source_path).read_text(encoding="utf-8") == "shared"
    with Session(memory_engine) as session:
        paths = session.exec(select(MessageAttachment.physical_path)).all()
    assert str(source_path) in paths
    assert "cache/sandbox/memory/group-123/files/shared.txt" in paths
    assert migrate_legacy_scope_directories(memory_engine) == (0, 0)
    assert (tmp_path / source_path).read_text(encoding="utf-8") == "shared"


def test_legacy_attachment_migration_merges_existing_typed_target(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    legacy_path = Path("cache/sandbox/memory/123/files/a.txt")
    typed_path = Path("cache/sandbox/memory/group-123/files/a.txt")
    for path in (legacy_path, typed_path):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("same", encoding="utf-8")
    with Session(memory_engine) as session:
        session.add_all(
            [
                MessageAttachment(
                    msg_time=1000,
                    user_id=9,
                    group_id=123,
                    workspace_key="123",
                    kind="file",
                    file_name="a.txt",
                    physical_path=str(legacy_path),
                    virtual_path="/memory/123/files/a.txt",
                    created_at=100,
                    expires_at=500,
                ),
                MessageAttachment(
                    msg_time=1000,
                    user_id=9,
                    group_id=123,
                    workspace_key="group-123",
                    kind="file",
                    file_name="a.txt",
                    physical_path=str(typed_path),
                    virtual_path="/memory/group-123/files/a.txt",
                    created_at=200,
                    expires_at=400,
                ),
            ]
        )
        session.commit()

    assert migrate_legacy_attachment_workspaces(memory_engine) == 1

    with Session(memory_engine) as session:
        rows = session.exec(select(MessageAttachment)).all()
    assert len(rows) == 1
    assert rows[0].physical_path == str(typed_path)
    assert rows[0].created_at == 100
    assert rows[0].expires_at == 500
    assert not (tmp_path / legacy_path).exists()
    assert (tmp_path / typed_path).read_text(encoding="utf-8") == "same"


def test_ambiguous_legacy_scope_is_left_for_manual_merge(memory_engine, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Message.metadata.create_all(memory_engine)
    with Session(memory_engine) as session:
        session.add_all(
            [
                Message(
                    time=1000,
                    msg_id=1,
                    user_id=9,
                    group_id=123,
                    user_name="Member",
                    role="user",
                    content="group",
                ),
                Message(
                    time=2000,
                    msg_id=2,
                    user_id=123,
                    group_id=None,
                    user_name="Peer",
                    role="user",
                    content="private",
                ),
            ]
        )
        session.commit()
    legacy_memory = tmp_path / "cache/sandbox/memory/123"
    legacy_memory.mkdir(parents=True)
    (legacy_memory / "SOUL.md").write_text("归属不明", encoding="utf-8")

    assert migrate_legacy_scope_directories(memory_engine) == (0, 1)
    assert (legacy_memory / "SOUL.md").read_text(encoding="utf-8") == "归属不明"


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
        "user_nickname",
        "user_card",
        "reply_context_json",
        "model_content",
        "sender_user_id",
        "bot_user_id",
        "directly_mentions_bot",
        "context_updated_at",
    }.issubset(columns)
    with memory_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT normalized_version, normalized_status, source_type, sender_user_id "
                "FROM message WHERE time = 1000"
            )
        ).one()
    assert row == (0, "legacy", MESSAGE_SOURCE_TYPE_NORMAL, 1)


def test_ensure_conversation_summary_schema_adds_invalidation_state(memory_engine):
    with memory_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE conversation_summary (
                    id INTEGER PRIMARY KEY,
                    scope_type TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    source_start_time INTEGER NOT NULL,
                    source_end_time INTEGER NOT NULL,
                    source_message_count INTEGER NOT NULL,
                    source_token_count INTEGER NOT NULL,
                    summary_text TEXT NOT NULL,
                    estimated_tokens INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    prompt_version INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
        )

    db_module.ensure_conversation_summary_schema(memory_engine)

    columns = {column["name"] for column in inspect(memory_engine).get_columns("conversation_summary")}
    indexes = {index["name"] for index in inspect(memory_engine).get_indexes("conversation_summary")}
    assert "invalidated_at" in columns
    assert "ix_conversation_summary_scope_valid_version" in indexes
    assert "ix_conversation_summary_scope_bucket" in indexes


@pytest.mark.asyncio
async def test_conversation_scopes_with_messages_returns_only_active_normal_scopes(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    await database.insert(1000, 1, 10, None, "Private", "user", "private")
    await database.insert(1100, 2, 20, 123, "Group", "user", "group")
    await database.insert(900, 3, 30, 456, "Old", "user", "outside")
    await database.insert(
        1200,
        4,
        40,
        789,
        "Derived",
        "user",
        "derived",
        source_type=MESSAGE_SOURCE_TYPE_FORWARD_NODE,
    )

    scopes = await database.conversation_scopes_with_messages(start_time=1000, end_time=1200)

    assert scopes == [(10, None), (0, 123)]


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
    assert [message.content for message in private_page] == ["group history", "private history"]
    assert [message.content for message in group_page] == ["group reply", "group history"]
    assert await database.context_token_total(user_id=10, group_id=None) == sum(
        message.estimated_tokens for message in private_page
    )

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
async def test_summary_source_cas_holds_sqlite_write_lock_until_insert(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'summary-cas.db'}",
        connect_args={"check_same_thread": False},
    )
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    ConversationSummary.metadata.create_all(engine)
    await database.insert(1000, 1, 10, 123, "Alice", "user", "original")
    source = await database.select_context_page(user_id=10, group_id=123)
    source_context = {message.time: message.context_updated_at for message in source}
    summary = ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=1,
        source_start_time=1000,
        source_end_time=1000,
        source_message_count=1,
        source_token_count=10,
        summary_text="Alice 发送了 original。",
        estimated_tokens=10,
        model="summary-model",
        created_at=2000,
    )

    summary_insert_started = threading.Event()
    update_started = threading.Event()
    release_summary_insert = threading.Event()

    def pause_summary_insert(_conn, _cursor, statement, _parameters, _context, _executemany):
        normalized = statement.lstrip().casefold()
        if normalized.startswith("insert into conversation_summary"):
            summary_insert_started.set()
            release_summary_insert.wait(timeout=2)
        elif normalized.startswith("update message set"):
            update_started.set()

    event.listen(engine, "before_cursor_execute", pause_summary_insert)
    append_task = asyncio.create_task(
        database.append_conversation_summary(
            summary,
            expected_version=0,
            expected_source_context=source_context,
        )
    )
    update_task = None
    try:
        assert await asyncio.to_thread(summary_insert_started.wait, 2)

        async def update_source():
            await database.update_message_normalization(
                time=1000,
                content="changed",
                raw_segments_json=None,
                normalized_version=1,
                normalized_status="complete",
            )

        update_task = asyncio.create_task(update_source())
        assert await asyncio.to_thread(update_started.wait, 2)
        await asyncio.sleep(0.05)
        assert not update_task.done()
    finally:
        release_summary_insert.set()

    assert await append_task is True
    assert update_task is not None
    await update_task
    assert await database.latest_conversation_summary(scope_type="group", scope_id="123") is None
    invalidated = await database.latest_conversation_summary(
        scope_type="group",
        scope_id="123",
        include_invalidated=True,
    )
    assert invalidated is not None
    assert invalidated.invalidated_at is not None


@pytest.mark.asyncio
async def test_group_source_change_invalidates_group_and_sender_private_summaries(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    await database.insert(1000, 1, 10, 123, "Alice", "user", "original")

    for scope_type, scope_id in (("group", "123"), ("private", "10")):
        summary = ConversationSummary(
            scope_type=scope_type,
            scope_id=scope_id,
            version=1,
            source_start_time=1000,
            source_end_time=1000,
            source_message_count=1,
            source_token_count=10,
            summary_text="Alice 发送了 original。",
            estimated_tokens=10,
            model="summary-model",
            created_at=2000,
        )
        assert await database.append_conversation_summary(summary, expected_version=0)

    await database.finalize_message_context(time=1000)

    for scope_type, scope_id in (("group", "123"), ("private", "10")):
        assert (
            await database.latest_conversation_summary(scope_type=scope_type, scope_id=scope_id)
            is None
        )
        invalidated = await database.latest_conversation_summary(
            scope_type=scope_type,
            scope_id=scope_id,
            include_invalidated=True,
        )
        assert invalidated is not None
        assert invalidated.invalidated_at is not None


@pytest.mark.asyncio
async def test_private_cross_scope_history_does_not_expose_group_attachment_paths(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    await database.insert(1000, 1, 10, None, "Alice", "user", "[图片:私聊图]")
    await database.insert(
        1100,
        2,
        10,
        123,
        "Alice",
        "user",
        "[图片:群聊图]",
        reply_context_json=serialize_agent_payload(
            {
                "schema": "frontier.qq_message_ref.v1",
                "message_id": "99",
                "sender": {"user_id": "20", "display_name": "Bob", "role": "user"},
                "content": "Bob 在群里的原话",
            }
        ),
    )
    await database.insert_media(
        msg_time=1000,
        msg_id=1,
        user_id=10,
        group_id=None,
        media=[resolve_media(b"private-image", "image")],
    )
    await database.insert_media(
        msg_time=1100,
        msg_id=2,
        user_id=10,
        group_id=123,
        media=[resolve_media(b"group-image", "image")],
    )

    records = await database.select_context_page(user_id=10, group_id=None, ascending=True)
    rendered = await database.prepare_message_records(
        records,
        accessible_workspace_key="dm-10",
    )
    payloads = {_wire_payload(message)["message_id"]: _wire_payload(message) for message in rendered}

    assert payloads["1"]["content"] == "[消息内容见附件]"
    assert payloads["1"]["attachments"][0]["path"].startswith("/memory/dm-10/")
    assert payloads["2"]["content"] == "[图片:群聊图]"
    assert "attachments" not in payloads["2"]
    assert "reply_to" not in payloads["2"]
    assert "Bob 在群里的原话" not in _wire_text(rendered[1])


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

    payloads = [_wire_payload(message) for message in prepared]
    attachments = [attachment for payload in payloads for attachment in payload.get("attachments", [])]
    assert len(attachments) == 12
    assert all(attachment["path"].startswith("/memory/dm-1/images/") for attachment in attachments)
    assert "base64" not in "".join(_wire_text(message) for message in prepared)


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

    payload = _wire_payload(prepared[0])
    assert payload["attachments"] == [
        {
            "kind": "image",
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
    await database.insert(1000, 101, 7, 123, "Alice", "user", "[图片]")
    initial = (await database.select_context_page(user_id=7, group_id=123))[0]

    paths = await database.insert_images(1000, 7, 123, [b"image-bytes"])

    expected_path = Path("cache/sandbox/memory/group-123/images/1000_0.jpg")
    assert paths == [str(expected_path)]
    assert (tmp_path / expected_path).read_bytes() == b"image-bytes"

    attachments = await database.select_image_attachments_by_msg_time(1000)
    assert len(attachments) == 1
    attachment = attachments[0]
    assert attachment.kind == "image"
    assert attachment.physical_path == str(expected_path)
    assert attachment.virtual_path == "/memory/group-123/images/1000_0.jpg"
    assert attachment.file_size == len(b"image-bytes")
    refreshed = (await database.select_context_page(user_id=7, group_id=123))[0]
    assert refreshed.model_content == ""
    assert refreshed.estimated_tokens > initial.estimated_tokens


@pytest.mark.asyncio
async def test_concurrent_image_cache_writes_share_one_attachment_row(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.db'}")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    db_module.ensure_database_performance_indexes(engine)
    await database.insert(1000, 101, 7, 123, "Alice", "user", "[图片]")

    results = await asyncio.gather(
        database.insert_images(1000, 7, 123, [b"same-image"]),
        database.insert_images(1000, 7, 123, [b"same-image"]),
    )

    assert results[0] == results[1]
    with Session(engine) as session:
        rows = session.exec(select(MessageAttachment)).all()
    assert len(rows) == 1
    assert rows[0].physical_path == "cache/sandbox/memory/group-123/images/1000_0.jpg"


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
    assert (tmp_path / "cache/sandbox/memory/dm-1/audio/1000_0.wav").is_file()
    assert (tmp_path / "cache/sandbox/memory/dm-1/videos/1000_1.mp4").is_file()


@pytest.mark.asyncio
async def test_insert_media_removes_new_files_when_database_indexing_fails(
    monkeypatch,
    memory_engine,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    def fail_refresh(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(db_module, "_refresh_message_model_states", fail_refresh)

    with pytest.raises(RuntimeError, match="database unavailable"):
        await database.insert_media(
            msg_time=1000,
            msg_id=101,
            user_id=1,
            group_id=None,
            media=[resolve_media(b"RIFF" + b"\x00" * 4 + b"WAVE", "audio")],
        )

    assert not (tmp_path / "cache/sandbox/memory/dm-1/audio/1000_0.wav").exists()
    with Session(memory_engine) as session:
        assert session.exec(select(MessageAttachment)).all() == []


@pytest.mark.asyncio
async def test_cleanup_expired_attachments_deletes_only_db_tracked_files(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
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
async def test_cleanup_keeps_file_until_last_attachment_reference_expires(
    monkeypatch,
    memory_engine,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    shared_path = Path("cache/sandbox/memory/group-123/files/shared.txt")
    (tmp_path / shared_path).parent.mkdir(parents=True)
    (tmp_path / shared_path).write_text("shared", encoding="utf-8")
    with Session(memory_engine) as session:
        session.add_all(
            [
                MessageAttachment(
                    msg_time=1000,
                    user_id=7,
                    group_id=123,
                    workspace_key="group-123",
                    kind="file",
                    file_name="shared.txt",
                    physical_path=str(shared_path),
                    virtual_path="/memory/group-123/files/shared.txt",
                    created_at=1,
                    expires_at=1,
                ),
                MessageAttachment(
                    msg_time=2000,
                    user_id=7,
                    group_id=123,
                    workspace_key="group-123",
                    kind="file",
                    file_name="shared.txt",
                    physical_path=str(shared_path),
                    virtual_path="/memory/group-123/files/shared.txt",
                    created_at=1,
                    expires_at=100,
                ),
            ]
        )
        session.commit()

    assert await database.cleanup_expired_attachments(now_ms=2) == 1
    assert (tmp_path / shared_path).is_file()
    assert await database.cleanup_expired_attachments(now_ms=101) == 1
    assert not (tmp_path / shared_path).exists()


@pytest.mark.asyncio
async def test_prepare_message_before_time_excludes_current_and_later_group_messages(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 201, 10, 123, "Old", "user", "old message")
    await database.insert(2000, 202, 10, 123, "Alice", "user", "alice current")
    await database.insert(2001, 203, 20, 123, "Bob", "user", "bob concurrent")

    prepared = await database.prepare_message(user_id=10, group_id=123, query_numbers=10, before_time=2000)

    content = _wire_text(prepared[0])
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
    group_payload = _wire_payload(group_prepared[0])
    assert group_payload["schema"] == "frontier.qq_message.v1"
    assert group_payload["chat"]["type"] == "group"
    assert group_payload["chat"]["group_id"] == "123"
    assert group_payload["sender"]["user_id"] == "10"

    private_prepared = await database.prepare_message(user_id=20, query_numbers=10, before_time=4000)
    private_payload = _wire_payload(private_prepared[0])
    assert private_payload["chat"]["type"] == "private"
    assert "group_id" not in private_payload["chat"]
    assert private_payload["sender"]["user_id"] == "20"


@pytest.mark.asyncio
async def test_prepare_message_preserves_group_participant_boundaries_and_unicode(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(
        1000,
        201,
        10,
        123,
        "项目经理",
        "user",
        "我提议周日出发",
        user_nickname="Alice",
        user_card="项目经理",
    )
    reply_to = {
        "schema": "frontier.qq_message_ref.v1",
        "message_id": "201",
        "sender": {"user_id": "10", "display_name": "项目经理", "role": "user"},
        "content": "我提议周日出发",
    }
    await database.insert(
        2000,
        202,
        20,
        123,
        "Bob",
        "user",
        "我没有同意负责订车",
        reply_context_json=serialize_agent_payload(reply_to),
    )

    prepared = await database.prepare_message_records(
        await database.select_context_page(user_id=10, group_id=123, ascending=True)
    )

    assert len(prepared) == 2
    alice = _wire_payload(prepared[0])
    bob = _wire_payload(prepared[1])
    assert alice["sender"] == {
        "user_id": "10",
        "display_name": "项目经理",
        "role": "user",
        "nickname": "Alice",
    }
    assert bob["sender"]["user_id"] == "20"
    assert bob["reply_to"] == reply_to
    assert "我提议周日出发" in _wire_text(prepared[0])
    assert "\\u6211" not in _wire_text(prepared[0])


@pytest.mark.asyncio
async def test_private_assistant_envelope_uses_real_sender_without_changing_scope(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 1, 20, None, "Alice", "user", "你好")
    await database.insert(
        2000,
        None,
        20,
        None,
        "Assistant",
        "assistant",
        "你好呀",
        sender_user_id=999,
    )
    await database.insert(3000, None, 30, None, "Assistant", "assistant", "legacy reply")

    records = await database.select_context_page(user_id=20, group_id=None, ascending=True)
    prepared = await database.prepare_message_records(records)

    assert [record.user_id for record in records] == [20, 20]
    assistant = _wire_payload(prepared[1])
    assert assistant["sender"] == {
        "user_id": "999",
        "display_name": "Assistant",
        "role": "assistant",
    }

    legacy = await database.select_context_page(user_id=30, group_id=None, ascending=True)
    legacy_payload = _wire_payload((await database.prepare_message_records(legacy))[0])
    assert legacy_payload["sender"]["role"] == "assistant"
    assert "user_id" not in legacy_payload["sender"]


@pytest.mark.asyncio
async def test_persisted_bot_context_renders_identically_as_history(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(
        1000,
        9,
        20,
        123,
        "Alice",
        "user",
        "@999 你怎么看？",
        sender_user_id=20,
        bot_user_id=999,
        directly_mentions_bot=True,
    )

    records = await database.select_context_page(user_id=20, group_id=123, ascending=True)
    rendered = (await database.prepare_message_records(records))[0]
    payload = _wire_payload(rendered)
    current_wire_payload = serialize_agent_payload(
        build_agent_message_payload(
            timestamp_ms=1000,
            msg_id=9,
            user_id=20,
            group_id=123,
            user_name="Alice",
            role="user",
            content="@999 你怎么看？",
            bot_user_id=999,
            directly_mentions_bot=True,
        )
    )

    assert "is_current" not in payload
    assert payload["bot_context"] == {"user_id": "999", "directly_mentioned": True}
    assert payload["content"].startswith("[你被主动@了，这条消息是明确对你说的]\n")
    assert _wire_text(rendered) == current_wire_payload


@pytest.mark.asyncio
async def test_empty_current_message_renders_identically_as_history(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    await database.insert(1000, 9, 20, None, "Alice", "user", "", sender_user_id=20, bot_user_id=999)

    record = (await database.select_context_page(user_id=20, group_id=None, ascending=True))[0]
    rendered = (await database.prepare_message_records([record]))[0]
    current = serialize_agent_payload(
        build_agent_message_payload(
            timestamp_ms=1000,
            msg_id=9,
            user_id=20,
            group_id=None,
            user_name="Alice",
            role="user",
            content="",
            bot_user_id=999,
        )
    )

    assert _wire_text(rendered) == current
    assert _wire_payload(rendered)["content"] == "[用户叫了你一声]"


@pytest.mark.asyncio
async def test_finalized_attachment_message_renders_identically_as_history(memory_engine, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    await database.insert(
        1000,
        9,
        20,
        123,
        "Alice",
        "user",
        "[图片]",
        sender_user_id=20,
        bot_user_id=999,
    )
    image_path = Path("cache/sandbox/memory/123/images/1000_0.png")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"image")
    await database.insert_attachment(
        msg_time=1000,
        msg_id=9,
        user_id=20,
        group_id=123,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/123/images/1000_0.png",
        file_name="1000_0.png",
        mime_type="image/png",
        file_size=5,
        expires_at=9_999_999_999_999,
    )
    await database.finalize_message_context(time=1000)

    record = (await database.select_context_page(user_id=20, group_id=123, ascending=True))[0]
    rendered = (await database.prepare_message_records([record]))[0]
    attachment = dict(
        build_agent_attachment_payload(
            kind="image",
            mime_type="image/png",
            file_name="1000_0.png",
            path="/memory/123/images/1000_0.png",
        )
    )
    current = serialize_agent_payload(
        build_agent_message_payload(
            timestamp_ms=1000,
            msg_id=9,
            user_id=20,
            group_id=123,
            user_name="Alice",
            role="user",
            content="",
            attachments=[attachment],
            bot_user_id=999,
        )
    )

    assert _wire_text(rendered) == current
    assert record.content == "[图片]"
    assert record.model_content == ""
    search_results = await database.search_messages(
        group_id=123,
        user_id=20,
        content_query="[图片]",
        limit=10,
    )
    assert [message.content for message in search_results] == ["[图片]"]
    assert record.token_estimate_version == db_module.MESSAGE_TOKEN_ESTIMATE_VERSION
    assert record.estimated_tokens == db_module.estimate_stored_message_tokens(
        "",
        "Alice",
        serialized_payload=current,
    )


@pytest.mark.asyncio
async def test_select_recent_media_message_is_sender_and_workspace_scoped(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    image_raw = json.dumps([{"type": "image", "data": {"resource_id": "image-1"}}])
    file_raw = json.dumps(
        [{"type": "file", "data": {"file_id": "file-1", "file_hash": "hash-1"}}]
    )
    await database.insert(1000, 10, 1, 123, "Alice", "user", "[图片]", raw_segments_json=image_raw)
    await database.insert(1500, 11, 2, 123, "Bob", "user", "[图片]", raw_segments_json=image_raw)
    await database.insert(1800, 12, 1, 123, "Alice", "user", "普通文本", raw_segments_json="[]")
    await database.insert(2000, 13, 1, None, "Alice", "user", "[文件]", raw_segments_json=file_raw)

    group_match = await database.select_recent_media_message(
        user_id=1,
        group_id=123,
        before_time=3000,
        after_time=0,
    )
    private_match = await database.select_recent_media_message(
        user_id=1,
        group_id=None,
        before_time=3000,
        after_time=0,
    )
    expired_match = await database.select_recent_media_message(
        user_id=1,
        group_id=123,
        before_time=3000,
        after_time=1001,
    )

    assert group_match is not None and group_match.msg_id == 10
    assert private_match is not None and private_match.msg_id == 13
    assert expired_match is None


@pytest.mark.asyncio
async def test_partial_image_persistence_keeps_every_original_marker(memory_engine, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    await database.insert(
        1000,
        9,
        20,
        123,
        "Alice",
        "user",
        "[图片:猫]\n[图片:狗]",
        sender_user_id=20,
    )
    image_path = Path("cache/sandbox/memory/group-123/images/1000_0.png")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"image")
    await database.insert_attachment(
        msg_time=1000,
        msg_id=9,
        user_id=20,
        group_id=123,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/group-123/images/1000_0.png",
        file_name="1000_0.png",
        mime_type="image/png",
        file_size=5,
        expires_at=9_999_999_999_999,
    )

    record = (await database.select_context_page(user_id=20, group_id=123, ascending=True))[0]
    rendered = (await database.prepare_message_records([record]))[0]

    assert record.model_content is None
    assert _wire_payload(rendered)["content"] == "[图片:猫]\n[图片:狗]"


@pytest.mark.asyncio
async def test_finalize_message_context_can_clear_preliminary_reply_snapshot(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    await database.insert(
        1000,
        9,
        20,
        123,
        "Alice",
        "user",
        "正文",
        reply_context_json=serialize_agent_payload({"content": "预取引用"}),
    )

    await database.finalize_message_context(time=1000, reply_context_json=None)

    record = (await database.select_context_page(user_id=20, group_id=123, ascending=True))[0]
    rendered = (await database.prepare_message_records([record]))[0]
    assert record.reply_context_json is None
    assert "reply_to" not in _wire_payload(rendered)
    assert record.estimated_tokens == db_module.estimate_stored_message_tokens(
        record.content,
        record.user_name,
        serialized_payload=_wire_text(rendered),
    )


@pytest.mark.asyncio
async def test_attachment_cleanup_restores_raw_image_marker_and_recomputes_estimate(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    await database.insert(1000, 9, 20, 123, "Alice", "user", "[图片]", sender_user_id=20)

    image_path = Path("cache/sandbox/memory/123/images/1000_0.png")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"image")
    await database.insert_attachment(
        msg_time=1000,
        msg_id=9,
        user_id=20,
        group_id=123,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/123/images/1000_0.png",
        file_name="1000_0.png",
        mime_type="image/png",
        file_size=5,
        expires_at=1,
    )
    await database.finalize_message_context(time=1000)

    before = (await database.select_context_page(user_id=20, group_id=123, ascending=True))[0]
    assert before.model_content == ""
    before_estimate = before.estimated_tokens

    assert await database.cleanup_expired_attachments(now_ms=2) == 1

    after = (await database.select_context_page(user_id=20, group_id=123, ascending=True))[0]
    rendered = (await database.prepare_message_records([after]))[0]
    assert after.content == "[图片]"
    assert after.model_content is None
    assert _wire_payload(rendered)["content"] == "[图片]"
    assert "attachments" not in _wire_payload(rendered)
    assert after.token_estimate_version == db_module.MESSAGE_TOKEN_ESTIMATE_VERSION
    assert after.estimated_tokens == db_module.estimate_stored_message_tokens(
        after.content,
        after.user_name,
        serialized_payload=_wire_text(rendered),
    )
    assert after.estimated_tokens < before_estimate


@pytest.mark.asyncio
async def test_prepare_message_ignores_stale_model_content_when_attachment_file_is_missing(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    await database.insert(1000, 9, 20, 123, "Alice", "user", "[图片]", sender_user_id=20)
    await database.insert_attachment(
        msg_time=1000,
        msg_id=9,
        user_id=20,
        group_id=123,
        kind="image",
        physical_path="cache/sandbox/memory/123/images/missing.png",
        virtual_path="/memory/123/images/missing.png",
        file_name="missing.png",
        mime_type="image/png",
        file_size=5,
        expires_at=9_999_999_999_999,
    )
    await database.finalize_message_context(time=1000)

    record = (await database.select_context_page(user_id=20, group_id=123, ascending=True))[0]
    assert record.model_content == ""
    payload = _wire_payload((await database.prepare_message_records([record]))[0])
    assert payload["content"] == "[图片]\n[image附件已过期]"
    assert "attachments" not in payload


@pytest.mark.asyncio
async def test_private_reply_lookup_is_isolated_by_peer(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 7, 111, None, "Alice", "user", "Alice private")
    await database.insert(2000, 7, 222, None, "Bob", "user", "Bob private")

    alice = await database.select_by_msg_id(msg_id=7, group_id=None, peer_user_id=111)
    bob = await database.select_by_msg_id(msg_id=7, group_id=None, peer_user_id=222)

    assert alice is not None and alice.content == "Alice private"
    assert bob is not None and bob.content == "Bob private"

    with pytest.raises(ValueError, match="peer_user_id"):
        await database.select_by_msg_id(msg_id=7, group_id=None)


@pytest.mark.asyncio
async def test_message_token_estimate_covers_reply_snapshot_and_normalization_updates(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    reply_to = {
        "schema": "frontier.qq_message_ref.v1",
        "sender": {"user_id": "10", "display_name": "Alice", "role": "user"},
        "content": "引用正文" * 1000,
    }

    await database.insert(
        1000,
        8,
        20,
        123,
        "Bob",
        "user",
        "收到",
        reply_context_json=serialize_agent_payload(reply_to),
    )
    before = (await database.select_context_page(user_id=20, group_id=123))[0]
    assert before.estimated_tokens > 1000

    await database.update_message_normalization(
        time=1000,
        content="更新后的长正文" * 1000,
        raw_segments_json=None,
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    after = (await database.select_context_page(user_id=20, group_id=123))[0]
    assert after.estimated_tokens > before.estimated_tokens
    assert after.token_estimate_version == db_module.MESSAGE_TOKEN_ESTIMATE_VERSION


@pytest.mark.asyncio
async def test_normalization_refresh_preserves_existing_attachment_derived_state(
    memory_engine,
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)
    await database.insert(1000, 8, 20, 123, "Bob", "user", "旧正文\n[图片]")
    image_path = Path("cache/sandbox/memory/123/images/1000_0.png")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"image")
    await database.insert_attachment(
        msg_time=1000,
        msg_id=8,
        user_id=20,
        group_id=123,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/123/images/1000_0.png",
        file_name="1000_0.png",
        mime_type="image/png",
        file_size=5,
        expires_at=9_999_999_999_999,
    )

    await database.update_message_normalization(
        time=1000,
        content="新正文\n[图片]",
        raw_segments_json=None,
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )

    record = (await database.select_context_page(user_id=20, group_id=123))[0]
    rendered = (await database.prepare_message_records([record]))[0]
    assert record.model_content == "新正文"
    assert _wire_payload(rendered)["content"] == "新正文"
    assert len(_wire_payload(rendered)["attachments"]) == 1
    assert record.estimated_tokens == db_module.estimate_stored_message_tokens(
        record.content,
        record.user_name,
        serialized_payload=_wire_text(rendered),
    )


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
    assert "derived content" in _wire_text(prepared[0])


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
