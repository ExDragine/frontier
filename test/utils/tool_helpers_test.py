# ruff: noqa: S101

import base64

import pytest
from langchain_core.messages import HumanMessage


def test_tool_state_view_extracts_user_and_decodes_media():
    from utils.tool_helpers import ToolStateView

    image_payload = b"image-bytes"
    video_payload = b"video-bytes"
    state = {
        "context": {"user_id": "ctx-user"},
        "messages": [
            {"role": "assistant", "content": "old"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{base64.b64encode(image_payload).decode()}",
                    },
                    {
                        "type": "video_url",
                        "video_url": {"url": f"data:video/mp4;base64,{base64.b64encode(video_payload).decode()}"},
                    },
                ],
            },
        ],
    }

    view = ToolStateView(state)

    assert view.user_id == "ctx-user"
    assert [item.data for item in view.iter_media("image_url", "image_url", "data:image/")] == [image_payload]
    assert [item.data for item in view.iter_media("video_url", "video_url", "data:video/")] == [video_payload]


def test_tool_state_view_prefers_injected_binary_inputs():
    from utils.tool_helpers import ToolStateView

    view = ToolStateView({"user_id": "u1", "image_inputs": [b"first", b"latest"]})

    media = view.latest_binary("image_inputs", "image/jpeg")

    assert view.user_id == "u1"
    assert media is not None
    assert media.data == b"latest"
    assert media.mime_type == "image/jpeg"


def test_tool_state_view_decodes_standard_media_blocks():
    from utils.tool_helpers import ToolStateView

    state = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "base64": base64.b64encode(b"standard-image").decode(),
                        "mime_type": "image/png",
                    },
                    {
                        "type": "video",
                        "base64": base64.b64encode(b"standard-video").decode(),
                        "mime_type": "video/mp4",
                    },
                ],
            }
        ]
    }

    view = ToolStateView(state)

    assert [item.data for item in view.iter_media("image_url", "image_url", "data:image/")] == [b"standard-image"]
    assert [item.data for item in view.iter_media("video_url", "video_url", "data:video/")] == [b"standard-video"]


@pytest.mark.parametrize("as_object", [False, True])
def test_tool_state_view_skips_pinned_skill_instructions(as_object):
    from utils.tool_helpers import ToolStateView

    messages = [
        {"role": "user", "content": [{
            "type": "image", "base64": base64.b64encode(b"original").decode(), "mime_type": "image/png",
        }]},
        {"role": "user", "content": "composition instructions", "additional_kwargs": {"lc_source": "pinned_skill"}},
    ]
    if as_object:
        messages = [HumanMessage(**{key: value for key, value in message.items() if key != "role"}) for message in messages]
    view = ToolStateView({"messages": messages})

    assert [item.data for item in view.iter_media("image_url", "image_url", "data:image/")] == [b"original"]


def test_tool_state_view_does_not_reuse_images_from_an_older_request():
    from utils.tool_helpers import ToolStateView

    view = ToolStateView({"messages": [
        {"role": "user", "content": [{
            "type": "image", "base64": base64.b64encode(b"old").decode(), "mime_type": "image/png",
        }]},
        {"role": "user", "content": "a new text-only request"},
        {"role": "user", "content": "instructions", "additional_kwargs": {"lc_source": "pinned_skill"}},
    ]})

    assert view.latest_user_content == "a new text-only request"
    assert list(view.iter_media("image_url", "image_url", "data:image/")) == []
