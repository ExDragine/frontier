"""Compatibility tests for the neutral Agent runtime request context."""

# ruff: noqa: S101

import pytest

from utils.agent_protocol import ConversationRef, Participant
from utils.agents.runtime_gateway import AgentRuntimeMedia, AgentRuntimeRequest

_NEUTRAL_FIELDS = ("conversation", "principal", "capabilities", "workspace_key")


@pytest.mark.xfail(
    condition=not all(hasattr(AgentRuntimeRequest, field) for field in _NEUTRAL_FIELDS),
    reason="AgentRuntimeRequest neutral context fields are introduced incrementally",
    strict=False,
)
def test_runtime_request_accepts_neutral_context_and_preserves_legacy_fields() -> None:
    conversation = ConversationRef(
        platform="feishu",
        account_id="bot-1",
        kind="thread",
        conversation_id="chat-1",
        tenant_id="tenant-1",
    )
    principal = Participant(
        id="user-1",
        display_name="Alice",
        role="member",
        permissions=frozenset({"chat.read"}),
    )
    image = AgentRuntimeMedia(kind="image", data=b"image", mime_type="image/png")

    request = AgentRuntimeRequest(
        session_id="session-1",
        prompt="hello",
        images=(image,),
        audio=(),
        messages=({"role": "user", "content": "hello"},),
        user_id="user-1",
        user_name="Alice",
        group_id=42,
        group_member_role="member",
        capability="common.weather",
        access_profile="frontier",
        enable_acp_subagents=True,
        allow_silent_reply=True,
        image_inputs=(b"legacy-image",),
        audio_inputs=(b"legacy-audio",),
        video_inputs=(b"legacy-video",),
        conversation=conversation,
        principal=principal,
        capabilities=frozenset({"common.weather", "platform.feishu"}),
        workspace_key="feishu:tenant-1:thread:chat-1",
    )

    assert request.conversation is conversation
    assert request.principal is principal
    assert request.capabilities == frozenset({"common.weather", "platform.feishu"})
    assert request.workspace_key == "feishu:tenant-1:thread:chat-1"

    # Existing ACP/QQ fields remain available alongside the neutral context.
    assert request.session_id == "session-1"
    assert request.prompt == "hello"
    assert request.images == (image,)
    assert request.messages == ({"role": "user", "content": "hello"},)
    assert request.user_id == "user-1"
    assert request.user_name == "Alice"
    assert request.group_id == 42
    assert request.group_member_role == "member"
    assert request.capability == "common.weather"
    assert request.access_profile == "frontier"
    assert request.enable_acp_subagents is True
    assert request.allow_silent_reply is True
    assert request.image_inputs == (b"legacy-image",)
    assert request.audio_inputs == (b"legacy-audio",)
    assert request.video_inputs == (b"legacy-video",)


@pytest.mark.xfail(
    condition=not all(hasattr(AgentRuntimeRequest, field) for field in _NEUTRAL_FIELDS),
    reason="AgentRuntimeRequest neutral context fields are introduced incrementally",
    strict=False,
)
def test_runtime_request_keeps_legacy_constructor_compatible() -> None:
    """New neutral fields should have defaults for existing callers."""

    request = AgentRuntimeRequest(session_id="legacy-session", prompt="legacy prompt")

    assert request.session_id == "legacy-session"
    assert request.prompt == "legacy prompt"
    assert request.images == ()
    assert request.messages == ()
    assert request.user_id is None
    assert request.group_id is None
    assert request.group_member_role is None
    assert request.conversation is None
    assert request.principal is None
    assert request.capabilities == frozenset()
    assert request.workspace_key is None
