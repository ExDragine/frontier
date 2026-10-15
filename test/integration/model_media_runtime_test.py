# ruff: noqa: S101
"""Exercise a real LangChain model/tool/model cycle without network calls."""

import subprocess
import sys
from pathlib import Path

import pytest


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
from utils.agents.media_inputs import MediaInputMiddleware
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

    graph = create_agent(model, tools=[read_test_image], middleware=[
        MediaInputMiddleware("test", max_images=4, max_bytes=1024 * 1024)
    ])
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


@pytest.mark.parametrize("case", ["latest_image", "byte_budget", "no_vision"])
def test_real_read_file_offload_rehydrates_before_production_media_boundary(tmp_path, case):
    script = r'''
import asyncio
import sys
from io import BytesIO
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from PIL import Image
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from utils.agents import inputs
from utils.agents.media_inputs import MediaInputMiddleware
from utils.media import inline_media_bytes, media_block_kind

case = sys.argv[2]
inputs.model_supports = lambda *args, **kwargs: case != "no_vision"
root = Path("workspace").resolve()
root.mkdir()
for name, color in [("old.png", "red"), ("new.png", "blue")]:
    Image.new("RGB", (4, 4), color).save(root / name)
seen = []

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

def images(messages):
    return [block for message in messages if isinstance(message.content, list)
            for block in message.content if media_block_kind(block) == "image"]

async def main():
    backend = FilesystemBackend(root_dir=root)
    model = Model(responses=[
        AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"file_path": "/old.png"}, "id": "old"}]),
        AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"file_path": "/new.png"}, "id": "new"}]),
        AIMessage(content="done"),
    ])
    graph = create_deep_agent(model=model, backend=backend, subagents=[], middleware=[
        FilesystemMiddleware(backend=backend, offload_binary_content=True),
        MediaInputMiddleware("test", max_images=1, max_bytes=1 if case == "byte_budget" else 1024 * 1024),
    ])
    result = await graph.ainvoke({"messages": [{"role": "user", "content": "Compare the two files"}]})
    assert result["messages"][-1].content == "done"
    assert len(seen) == 3
    if case == "latest_image":
        first = images(seen[1])
        assert len(first) == 1, str(seen[1])[-6000:]
        data, mime = inline_media_bytes(first[0])
        assert mime == "image/png" and data == (root / "old.png").read_bytes()
        latest = images(seen[2])
        assert len(latest) == 1
        data, mime = inline_media_bytes(latest[0])
        assert mime == "image/png" and data == (root / "new.png").read_bytes()
    else:
        assert not images(seen[1]) and not images(seen[2])
        notice = "不支持视觉" if case == "no_vision" else "媒体未内联"
        assert notice in str(seen[2])
    assert [m.tool_call_id for m in seen[2] if isinstance(m, ToolMessage)] == ["old", "new"]
    # Offloaded persisted results remain references; model-bound changes must
    # neither erase the original files nor rewrite the checkpoint's tool IDs.
    assert (root / "old.png").read_bytes()[:4] == b"\x89PNG"
    assert not any(inline_media_bytes(block) for block in images(result["messages"]))
asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2]), case],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_message_tool_stages_other_members_image_then_read_file_reaches_model(tmp_path):
    script = r'''
import asyncio
import importlib.util
import json
import sys
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
repo = Path(sys.argv[1])
sys.path.insert(0, str(repo))
import nonebot
nonebot.init(driver="nonebot.drivers.fastapi:Driver", log_level="WARNING")
from PIL import Image
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from utils.agent_context import FrontierRuntimeContext
from utils.agent_protocol import ConversationRef
from utils.agents import inputs
from utils.agents.media_inputs import MediaInputMiddleware
from utils.database import MessageDatabase
from utils.media import inline_media_bytes, media_block_kind
from plugins.agent import reply_context
from plugins.agent.message_normalizer import NORMALIZED_VERSION

# Import the real decorated tool without initializing unrelated tool discovery.
spec = importlib.util.spec_from_file_location("message_tools_contract", repo / "tools/milky_message.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
schema = mod.get_message.tool_call_schema.model_json_schema()["properties"]
assert {"include_attachments", "attachment_index"} <= schema.keys()
assert "runtime" not in schema and "config" not in schema

root = Path("sandbox").resolve()
memory = root / "memory/group-123"
memory.mkdir(parents=True)
inputs.model_supports = lambda *args, **kwargs: True
original = BytesIO()
Image.new("RGB", (4, 4), "green").save(original, format="BMP")
downloads = []
async def download(bot, segment):
    downloads.append(segment["data"]["resource_id"])
    return original.getvalue()
reply_context._download_milky_image = download
mod.get_bot = lambda account=None: SimpleNamespace(self_id="999")
seen = []

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(messages)
        if len(seen) == 2:
            result = json.loads(next(m.content for m in reversed(messages) if isinstance(m, ToolMessage)))
            assert result["sender_user_id"] == 111 and result["message_seq"] == 77
            item = result["attachments"][0]
            assert item["segment_index"] == 1 and item["status"] == "ready"
            self.responses[1] = AIMessage(content="", tool_calls=[{
                "name": "read_file", "args": {"file_path": item["path"]}, "id": "read-image",
            }])
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

async def main():
    db = MessageDatabase()
    await db.insert(
        time=1000, msg_id=77, user_id=111, sender_user_id=111, bot_user_id=999,
        group_id=123, user_name="Alice", role="user", content="Alice's image",
        normalized_version=NORMALIZED_VERSION, normalized_status="complete",
        raw_segments_json=json.dumps([
            {"type": "text", "data": {"text": "look"}},
            {"type": "image", "data": {"resource_id": "alice-picture"}},
        ]),
    )
    backend = FilesystemBackend(root_dir=root)
    model = Model(responses=[
        AIMessage(content="", tool_calls=[{
            "name": "get_message", "args": {"message_scene": "group", "message_seq": 77,
                                             "include_attachments": True, "attachment_index": 1}, "id": "get-image",
        }]), AIMessage(content="placeholder"), AIMessage(content="done"),
    ])
    graph = create_deep_agent(
        model=model, tools=[mod.get_message], backend=backend, subagents=[],
        context_schema=FrontierRuntimeContext,
        middleware=[FilesystemMiddleware(backend=backend, offload_binary_content=True),
                    MediaInputMiddleware("test", max_images=4, max_bytes=1024 * 1024)],
    )
    context = FrontierRuntimeContext("456", 123, None, str(root), ConversationRef("qq", "999", "group", "123"))
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "Explain Alice's image in message 77"}]},
        config={"configurable": {"user_id": "456", "group_id": 123, "virtual_roots": {"/memory/group-123/": str(memory)}}},
        context=context,
    )
    assert result["messages"][-1].content == "done" and len(seen) == 3
    blocks = [block for m in seen[-1] if isinstance(m.content, list)
              for block in m.content if media_block_kind(block) == "image"]
    assert len(blocks) == 1, str(seen[-1])[-3000:]
    data, mime = inline_media_bytes(blocks[0])
    assert mime == "image/jpeg" and data != original.getvalue()
    assert downloads == ["alice-picture"]
asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
