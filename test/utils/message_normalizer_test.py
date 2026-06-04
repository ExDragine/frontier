# ruff: noqa: S101

import types

import pytest

from utils.message_normalizer import NORMALIZED_VERSION, normalize_segments, segments_to_raw_json


@pytest.mark.asyncio
async def test_normalize_segments_expands_nested_forward_and_returns_derived_nodes():
    class DummyBot:
        async def get_forwarded_messages(self, forward_id):
            if forward_id == "outer":
                return [
                    types.SimpleNamespace(
                        sender_name="Alice",
                        time=1714521600,
                        segments=[{"type": "text", "data": {"text": "外层"}}],
                    ),
                    types.SimpleNamespace(
                        sender_name="Bob",
                        time=1714521601,
                        segments=[
                            {
                                "type": "forward",
                                "data": {"forward_id": "inner", "title": "内层标题", "summary": "1条"},
                            }
                        ],
                    ),
                ]
            if forward_id == "inner":
                return [
                    types.SimpleNamespace(
                        sender_name="Carol",
                        time=1714521602,
                        segments=[{"type": "text", "data": {"text": "内层"}}],
                    )
                ]
            raise AssertionError(forward_id)

    result = await normalize_segments(
        DummyBot(),
        [{"type": "forward", "data": {"forward_id": "outer", "title": "外层标题", "summary": "2条"}}],
    )

    assert result.normalized_version == NORMALIZED_VERSION
    assert result.status == "complete"
    assert "[合并转发:外层标题 - 2条]" in result.content
    assert "Alice: 外层" in result.content
    assert "Bob: [合并转发:内层标题 - 1条]" in result.content
    assert "Carol: 内层" in result.content
    assert [node.sender_name for node in result.derived_messages] == ["Alice", "Bob", "Carol"]
    assert result.derived_messages[1].forward_id == "outer"
    assert result.derived_messages[2].forward_id == "inner"


def test_segments_to_raw_json_preserves_forward_id():
    raw = segments_to_raw_json([{"type": "forward", "data": {"forward_id": "fwd-1"}}])

    assert "fwd-1" in raw
