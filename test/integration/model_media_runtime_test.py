# ruff: noqa: S101
"""Exercise a real LangChain model/tool/model cycle without network calls."""

import subprocess
import sys
from pathlib import Path


def test_real_tool_images_are_normalized_before_next_model_call(tmp_path):
    script = r'''
import asyncio
import base64
import sys
from io import BytesIO
sys.path.insert(0, sys.argv[1])
from PIL import Image
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from utils.agents import inputs
from utils.media import inline_media_bytes

inputs.model_supports = lambda *args, **kwargs: True
raw = BytesIO()
Image.new("RGB", (4, 4), "red").save(raw, format="BMP")
block = {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(raw.getvalue()).decode()}}
seen = []
class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

@tool
def read_test_image() -> list:
    """Read an image for the model."""
    return [block]

async def main():
    model = Model(responses=[
        AIMessage(content="", tool_calls=[{"name": "read_test_image", "args": {}, "id": "read-1"}]),
        AIMessage(content="done"),
    ])
    graph = create_agent(model, tools=[read_test_image], middleware=[inputs.ModelMediaMiddleware("test")])
    result = await graph.ainvoke({"messages": [{"role": "user", "content": "read the image"}]})
    assert result["messages"][-1].content == "done"
    assert len(seen) == 2
    tool = next(message for message in seen[-1] if isinstance(message, ToolMessage))
    data, mime = inline_media_bytes(tool.content[0])
    assert tool.tool_call_id == "read-1" and mime == "image/jpeg"
    with Image.open(BytesIO(data)) as image:
        image.load()
        assert image.format == "JPEG"
    # Boundary conversion does not overwrite the persisted tool result.
    original = next(message for message in result["messages"] if isinstance(message, ToolMessage))
    assert inline_media_bytes(original.content[0])[0] == raw.getvalue()
asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
