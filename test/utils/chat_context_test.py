# ruff: noqa: S101

import copy
import json

from plugins.agent.chat_context import build_chat_context
from utils.media import inline_media_bytes, resolve_media, standard_media_block


def _build(**kwargs):
    values = {
        "payload": {"content": "只看我这张", "msg_id": "latest"},
        "history": [],
        "images": [],
        "audio": [],
        "videos": [],
        "quoted_images": [],
        "recent_images": [],
        "max_bytes": 20,
        "max_images": 2,
    }
    return build_chat_context(**(values | kwargs))


def _media(messages):
    return [
        inline[0]
        for message in messages
        if isinstance(message["content"], list)
        for block in message["content"]
        if (inline := inline_media_bytes(block))
    ]


def test_current_media_reserves_shared_budget_before_quotes_and_history():
    history = [
        {"role": "user", "content": [standard_media_block(resolve_media(b"old", "image"))]},
    ]
    original = copy.deepcopy(history)
    result = _build(
        history=history,
        images=[b"current"],
        audio=[b"audio"],
        videos=[b"video"],
        quoted_images=[b"quote"],
        recent_images=[b"recent"],
        max_bytes=17,
        max_images=1,
    )

    assert _media(result) == [b"current", b"audio", b"video"]
    assert history == original
    payload = json.loads(result[-1]["content"][0]["text"])
    assert payload["response_scope"]["kind"] == "current_request"
    assert payload["response_scope"]["history"] == "background_only"
    assert payload["content"] == "只看我这张"


def test_remaining_budget_prefers_newest_history_without_changing_message_order():
    history = [
        {"role": "user", "content": [standard_media_block(resolve_media(data, "image"))]}
        for data in (b"older", b"newer")
    ]
    result = _build(history=history, images=[b"current"], max_images=2)

    assert _media(result) == [b"newer", b"current"]
    assert "历史媒体未内联" in result[0]["content"][0]["text"]


def test_oversized_current_image_does_not_exclude_a_smaller_current_image():
    result = _build(images=[b"too large", b"ok"], max_bytes=2)
    assert _media(result) == [b"ok"]


def test_remote_history_cannot_bypass_inline_budget():
    result = _build(
        history=[{"role": "user", "content": [{"type": "image_url", "image_url": "https://example.com/x"}]}],
    )
    assert result[0]["content"] == [{"type": "text", "text": "[历史媒体未内联；如有附件路径，可按需读取]"}]
