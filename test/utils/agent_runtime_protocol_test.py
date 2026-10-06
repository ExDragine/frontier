"""Compatibility tests for the neutral Agent runtime request context.

Only the contracts this module actually owns are asserted here: that the
runtime request stays a constructible immutable value object with the legacy
ACP/QQ fields intact, and that the neutral identity fields stay optional for
existing callers.  How those fields are consumed is covered behaviourally by
``test/utils/agent_runtime_gateway_protocol_test.py``.
"""

# ruff: noqa: S101

import dataclasses

import pytest

from utils.agent_protocol import ConversationRef, Participant
from utils.agents.runtime_gateway import AgentRuntimeMedia, AgentRuntimeRequest


def test_runtime_request_is_a_frozen_slots_value_object() -> None:
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

    # Constructing with the full legacy + neutral surface keeps both field sets
    # available to callers; a removed or renamed field fails here loudly.
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
    assert request.workspace_key == "feishu:tenant-1:thread:chat-1"
    assert request.capabilities == frozenset({"common.weather", "platform.feishu"})

    assert not hasattr(request, "__dict__")  # slots
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.prompt = "changed"  # type: ignore[misc]


def test_runtime_request_keeps_legacy_constructor_compatible() -> None:
    """New neutral fields stay optional so existing ACP/QQ callers still work."""

    request = AgentRuntimeRequest(session_id="legacy-session", prompt="legacy prompt")

    assert request.session_id == "legacy-session"
    assert request.conversation is None
    assert request.principal is None
    assert request.capabilities == frozenset()
    assert request.workspace_key is None
