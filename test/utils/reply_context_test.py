# ruff: noqa: S101

import types
from pathlib import Path

import pytest
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import Message, MessageAttachment, MessageDatabase
from utils.message_normalizer import NORMALIZED_VERSION, segments_to_raw_json
from utils.reply_context import build_reply_context


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
                group_member=types.SimpleNamespace(nickname="Alice"),
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

    quote_text, images = await build_reply_context(DummyBot(), event, 900, 123, DummyMessagesDb())

    assert images == []
    assert "Bob: 外层消息" in quote_text
    assert "Carol: [合并转发:嵌套聊天 - 1条消息]" in quote_text
    assert "Dana: 内层消息" in quote_text
    assert inserted["content"].count("内层消息") == 1
    assert inserted["content"] in quote_text
    assert len(inserted["derived_messages"]) == 3


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

    quote_text, images = await build_reply_context(DummyBot(), event, 900, 123, database)

    assert images == [b"quoted-image"]
    assert "用户(Alice): 看图" in quote_text
    assert "[图片]" not in quote_text
    assert "[下方已附加引用图片 1 张]" in quote_text


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

    quote_text, images = await build_reply_context(DummyBot(), event, 900, 123, DummyMessagesDb())

    assert images == []
    assert "[图片:照片]" not in quote_text
    assert "[引用消息包含图片，但图片已失效]" in quote_text


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

    quote_text, images = await build_reply_context(DummyBot(), event, 900, 123, database)
    stored = await database.select_by_msg_id(msg_id=900, group_id=123)

    assert images == []
    assert "Bob: 完整内容" in quote_text
    assert "旧摘要" not in quote_text
    assert stored is not None
    assert stored.normalized_version == NORMALIZED_VERSION
    assert "Bob: 完整内容" in stored.content
