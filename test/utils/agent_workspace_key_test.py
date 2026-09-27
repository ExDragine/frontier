"""Workspace keys remain deterministic and safe for filesystem use."""

# ruff: noqa: S101

from utils.agents.runtime import conversation_workspace_key, normalize_workspace_key


def test_safe_workspace_key_is_preserved() -> None:
    assert normalize_workspace_key("feishu:tenant-1:thread:chat-1") == (
        "feishu:tenant-1:thread:chat-1"
    )


def test_unsafe_workspace_key_is_hashed() -> None:
    key = normalize_workspace_key("feishu:tenant/../other:chat")
    assert key.startswith("workspace-h-")
    assert "/" not in key
    assert ".." not in key
    assert normalize_workspace_key("feishu:tenant/../other:chat") == key


def test_legacy_conversation_keys_remain_stable() -> None:
    assert conversation_workspace_key("123", None) == "dm-123"
    assert conversation_workspace_key("user", 123) == "group-123"
