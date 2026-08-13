# ruff: noqa: S101

import base64


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
