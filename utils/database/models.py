"""SQLModel tables and the plain result types returned by the store.

Models keep their historical definition order so generated table metadata and
column order stay identical to the previous single-module implementation.
"""

from dataclasses import dataclass

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel

MESSAGE_SOURCE_TYPE_NORMAL = "message"
MESSAGE_SOURCE_TYPE_FORWARD_NODE = "forward_node"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    model: str


class Message(SQLModel, table=True):
    __table_args__ = (
        Index("ux_message_platform_key", "platform_key", unique=True),
        {"sqlite_autoincrement": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    time: int
    platform_key: str | None = None
    parent_message_id: int | None = None
    msg_id: int | None = Field(default=None)
    user_id: int = Field(index=True)
    group_id: int | None = Field(default=None, index=True)
    user_name: str | None
    role: str
    content: str
    model_content: str | None = None
    raw_segments_json: str | None = None
    normalized_version: int = 0
    normalized_status: str = "legacy"
    source_type: str = MESSAGE_SOURCE_TYPE_NORMAL
    parent_msg_id: int | None = None
    parent_msg_time: int | None = None
    parent_forward_id: str | None = None
    user_nickname: str | None = None
    user_card: str | None = None
    reply_context_json: str | None = None
    sender_user_id: int | None = None
    bot_user_id: int | None = None
    directly_mentions_bot: bool = False


@dataclass(frozen=True, slots=True)
class MessageSearchResult:
    """A message hit with optional FTS ranking metadata."""

    message: Message
    score: float | None = None
    snippet: str | None = None


def resolve_message_sender_user_id(message: Message) -> int | None:
    """Return the real author while safely handling legacy private assistants."""
    sender_user_id = getattr(message, "sender_user_id", None)
    if sender_user_id is not None:
        return int(sender_user_id)
    if getattr(message, "group_id", None) is None and getattr(message, "role", "user") == "assistant":
        # Legacy private assistant rows stored the peer in user_id to preserve
        # scope. Treat the author as unknown instead of impersonating that peer.
        return None
    return int(message.user_id)


@dataclass(frozen=True, slots=True)
class MessageInsertResult:
    message_id: int
    time: int
    inserted: bool


class TimeStamp(SQLModel, table=True):
    name: str = Field(primary_key=True, index=True)
    id: str | None


class MessageAttachment(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("physical_path", "msg_time", name="uq_messageattachment_path_msg_time"),
    )

    id: int | None = Field(default=None, primary_key=True)
    msg_time: int = Field(index=True)
    message_id: int | None = Field(default=None, index=True)
    msg_id: int | None = Field(default=None, index=True)
    user_id: int = Field(index=True)
    group_id: int | None = Field(default=None, index=True)
    workspace_key: str = Field(index=True)
    kind: str = Field(index=True)
    source_type: str = "message"
    file_name: str
    mime_type: str | None = None
    file_size: int | None = None
    sha256: str | None = None
    physical_path: str
    virtual_path: str
    created_at: int
    expires_at: int
    metadata_json: str = "{}"


class GroupSettings(SQLModel, table=True):
    __tablename__ = "group_settings"
    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    key: str = Field(index=True)
    value: str
    updated_at: int
