# ruff: noqa: S101

"""Verify the runtime gateway bridges neutral identity into the legacy graph."""

from __future__ import annotations

import pytest

from utils.agent_protocol import AgentArtifact, ConversationRef, Participant
from utils.agents.runtime_gateway import AgentRuntimeRequest, FrontierAgentRuntime


@pytest.mark.asyncio
async def test_runtime_maps_neutral_feishu_identity_without_group_semantics():
    captured: dict[str, object] = {}

    class Cognitive:
        async def chat_agent(self, messages, **kwargs):
            captured["messages"] = messages
            captured.update(kwargs)
            return {
                "response": {"messages": []},
                "uni_messages": [],
                "should_reply": False,
            }

    conversation = ConversationRef(
        platform="feishu",
        account_id="app-1",
        tenant_id="tenant-1",
        kind="thread",
        conversation_id="chat-1",
    )
    principal = Participant(id="user-1", display_name="Alice", role="member")

    await FrontierAgentRuntime(Cognitive()).run(
        AgentRuntimeRequest(
            prompt="hello",
            conversation=conversation,
            principal=principal,
            capabilities=frozenset({"common.weather"}),
            workspace_key="feishu:tenant-1:thread:chat-1",
        )
    )

    assert captured["user_id"] == "user-1"
    assert captured["user_name"] == "Alice"
    assert captured["group_id"] is None
    assert captured["group_member_role"] == "member"
    assert captured["thread_id_override"] == "feishu:tenant-1:thread:chat-1"
    assert captured["conversation"] is conversation
    assert captured["principal"] is principal
    assert captured["capabilities"] == frozenset({"common.weather"})
    assert captured["workspace_key_override"] == "feishu:tenant-1:thread:chat-1"


@pytest.mark.asyncio
async def test_runtime_derives_legacy_qq_group_id_from_neutral_conversation():
    captured: dict[str, object] = {}

    class Cognitive:
        async def chat_agent(self, _messages, **kwargs):
            captured.update(kwargs)
            return {"response": {"messages": []}, "uni_messages": [], "should_reply": False}

    await FrontierAgentRuntime(Cognitive()).run(
        AgentRuntimeRequest(
            prompt="hello",
            conversation=ConversationRef(
                platform="qq",
                account_id="bot-1",
                kind="group",
                conversation_id="123",
            ),
            principal=Participant(id="456", display_name="Bob", role="member"),
        )
    )

    assert captured["user_id"] == "456"
    assert captured["group_id"] == 123
    assert captured["group_member_role"] == "member"


@pytest.mark.asyncio
async def test_runtime_derives_platform_scoped_workspace_when_key_is_omitted():
    captured: dict[str, object] = {}

    class Cognitive:
        async def chat_agent(self, _messages, **kwargs):
            captured.update(kwargs)
            return {"response": {"messages": []}, "uni_messages": [], "should_reply": False}

    conversation = ConversationRef(
        platform="feishu",
        account_id="app-1",
        tenant_id="tenant-1",
        kind="thread",
        conversation_id="chat/1",
    )
    await FrontierAgentRuntime(Cognitive()).run(
        AgentRuntimeRequest(
            prompt="hello",
            conversation=conversation,
            principal=Participant(id="user-1", display_name="Alice"),
        )
    )

    workspace_key = captured["workspace_key_override"]
    assert isinstance(workspace_key, str)
    assert workspace_key.startswith("workspace-h-")
    assert "/" not in workspace_key
    assert captured["thread_id_override"] == workspace_key


@pytest.mark.asyncio
async def test_runtime_forwards_platform_tool_overrides():
    captured: dict[str, object] = {}

    class Cognitive:
        async def chat_agent(self, _messages, **kwargs):
            captured.update(kwargs)
            return {"response": {"messages": []}, "uni_messages": [], "should_reply": False}

    tool = object()
    await FrontierAgentRuntime(Cognitive()).run(
        AgentRuntimeRequest(prompt="hello", tool_overrides=(tool,))
    )

    assert captured["tool_overrides"] == (tool,)


@pytest.mark.asyncio
async def test_runtime_prompt_returns_neutral_artifacts_without_platform_conversion():
    class Cognitive:
        async def chat_agent(self, _messages, **kwargs):
            return {
                "response": {"messages": [{"content": "done"}]},
                "artifacts": [
                    AgentArtifact(
                        kind="image",
                        data=b"image",
                        mime_type="image/png",
                    )
                ],
                "should_reply": True,
            }

    result = await FrontierAgentRuntime(Cognitive()).prompt(
        AgentRuntimeRequest(prompt="hello")
    )

    assert result.text == "done"
    assert result.artifacts[0].kind == "image"
    assert result.artifacts[0].data == b"image"
