"""Platform-neutral values used at the Agent boundary.

The types in this module intentionally contain no NoneBot, Milky, LangChain, or
platform SDK objects.  Platform adapters translate their native events into
these values and translate :class:`AgentResponse` back into native messages.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class ConversationRef:
    """Opaque identity of a conversation on a particular platform.

    IDs are strings even when the underlying platform uses integers.  Keeping
    the platform and account in the identity prevents IDs from different
    adapters from sharing workspaces or checkpoints accidentally.
    """

    platform: str
    account_id: str
    kind: str
    conversation_id: str
    tenant_id: str | None = None
    parent_id: str | None = None


@dataclass(frozen=True, slots=True)
class Participant:
    """A user, bot, or other actor that can author a message."""

    id: str
    display_name: str
    role: str | None = None
    permissions: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class MessageRef:
    """Opaque reference to a message that belongs to a conversation."""

    platform: str
    conversation: ConversationRef
    message_id: str


@dataclass(frozen=True, slots=True)
class MessagePart:
    """Marker base class for normalized inbound message parts."""


@dataclass(frozen=True, slots=True)
class TextPart(MessagePart):
    text: str


@dataclass(frozen=True, slots=True)
class MediaPart(MessagePart):
    """A media payload that may be in memory or addressed by a URL."""

    data: bytes | None = None
    mime_type: str | None = None
    url: str | None = None
    name: str | None = None


@dataclass(frozen=True, slots=True)
class ImagePart(MediaPart):
    pass


@dataclass(frozen=True, slots=True)
class AudioPart(MediaPart):
    pass


@dataclass(frozen=True, slots=True)
class VideoPart(MediaPart):
    pass


@dataclass(frozen=True, slots=True)
class FilePart(MediaPart):
    pass


@dataclass(frozen=True, slots=True)
class MentionPart(MessagePart):
    """A mention of a participant in the normalized message."""

    participant_id: str
    display_name: str | None = None
    is_agent: bool = False


@dataclass(frozen=True, slots=True)
class QuotePart(MessagePart):
    """A quoted message and its normalized content, when available."""

    message_ref: MessageRef | None = None
    parts: tuple[MessagePart, ...] = ()


type MessagePartType = (
    TextPart | ImagePart | AudioPart | VideoPart | FilePart | MentionPart | QuotePart
)


@dataclass(frozen=True, slots=True)
class InboundMessage:
    """A platform-neutral message received by the application layer."""

    message_id: str
    conversation: ConversationRef
    sender: Participant
    created_at: datetime
    parts: tuple[MessagePart, ...]
    reply_to: MessageRef | None = None
    mentions_agent: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A normalized message suitable for an Agent history snapshot."""

    role: str
    content: str | tuple[MessagePart, ...]
    message_id: str | None = None
    conversation: ConversationRef | None = None
    sender: Participant | None = None
    created_at: datetime | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


# A stored message has the same neutral shape as a history message for now.
# Keeping the alias lets a future persistence adapter introduce a richer model
# without changing the ports in this first migration step.
type StoredMessage = ChatMessage


@dataclass(frozen=True, slots=True)
class HistoryQuery:
    """Scope and bounds for loading an Agent history snapshot."""

    conversation: ConversationRef
    limit: int = 50
    before: datetime | None = None
    after: datetime | None = None


@dataclass(frozen=True, slots=True)
class GateDecision:
    """Result of a platform reply policy decision."""

    should_reply: bool
    reason: str | None = None

    @property
    def allowed(self) -> bool:
        """Compatibility spelling for callers that express a gate as access."""

        return self.should_reply


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """Input contract passed from the application layer to Agent Core."""

    request_id: str
    current: InboundMessage
    history: tuple[ChatMessage, ...]
    workspace_key: str
    capabilities: frozenset[str]
    execution_profile: str
    allow_silent_reply: bool = False
    session_turn: object | None = None


@dataclass(frozen=True, slots=True)
class AgentArtifact:
    """A platform-neutral generated attachment."""

    kind: str
    data: bytes
    mime_type: str
    name: str | None = None
    # Remote and local sources are optional compatibility fields for tools
    # that return a URL/path instead of inline bytes.  Platform adapters decide
    # how to deliver them; the Agent Core never constructs a platform message.
    url: str | None = None
    path: str | None = None


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """Result returned by Agent Core before platform delivery."""

    text: str
    artifacts: tuple[AgentArtifact, ...] = ()
    status: str = "success"
    should_reply: bool = True
    run_id: str | None = None
    usage: Mapping[str, object] = field(default_factory=dict)


class DeliveryStatus(StrEnum):
    """Outcome of an attempted platform delivery."""

    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    """Delivery outcome with opaque references to messages sent by a platform."""

    status: DeliveryStatus
    message_refs: tuple[MessageRef, ...] = ()
    errors: tuple[str, ...] = ()


__all__ = [
    "AgentArtifact",
    "AgentRequest",
    "AgentResponse",
    "AudioPart",
    "ChatMessage",
    "ConversationRef",
    "DeliveryReceipt",
    "DeliveryStatus",
    "FilePart",
    "GateDecision",
    "HistoryQuery",
    "ImagePart",
    "InboundMessage",
    "MediaPart",
    "MentionPart",
    "MessagePart",
    "MessagePartType",
    "MessageRef",
    "Participant",
    "QuotePart",
    "StoredMessage",
    "TextPart",
    "VideoPart",
]
