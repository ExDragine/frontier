# ruff: noqa: S101
"""Run dependency contracts in fresh interpreters, outside unit-test module stubs."""

import subprocess
import sys
from pathlib import Path


def test_real_deep_agent_stream_and_media_artifact(tmp_path):
    script = r'''
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, sys.argv[1])
import nonebot
nonebot.init(driver="nonebot.drivers.fastapi:Driver", log_level="WARNING")
nonebot.require("nonebot_plugin_alconna")

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from nonebot_plugin_alconna import UniMessage
from utils.agents import cognitive
from utils.agents.runtime import conversation_workspace_key
from utils.configs import EnvConfig

class ContractModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

@tool(response_format="content_and_artifact")
def illustration() -> tuple[str, UniMessage]:
    """Return a locally generated image for the dependency contract."""
    return "image ready", UniMessage.image(raw=b"contract-image")

model = ContractModel(responses=[
    AIMessage(content="", tool_calls=[{"name": "illustration", "args": {}, "id": "image-1"}]),
    AIMessage(content="contract completed"),
])
cognitive.create_llm = lambda **kwargs: model
cognitive.agent_tools = SimpleNamespace(restricted_tools=[])
EnvConfig.ADVAN_MODEL = "contract-model"
EnvConfig.AGENT_JOB_TIMEOUT_SECONDS = 30
agent = object.__new__(cognitive.FrontierCognitive)
agent.tools = [illustration]
agent.ptc_tools = []
agent.research_subagent = None
agent.document_subagent = None
agent.working_dir = str(Path.cwd() / "sandbox")
agent.load_system_prompt = lambda group_id: "Answer the current request."

result = asyncio.run(agent.chat_agent(
    [{"role": "user", "content": "Create an illustration."}],
    user_id="contract", user_name="Contract", enable_acp_subagents=False,
))
assert not result.get("error"), result
assert result["status"] == "success", result
assert result["response"]["messages"][-1].content == "contract completed", result
assert result["uni_messages"][0][0].raw == b"contract-image", result
workspace_key = conversation_workspace_key("contract", None)
assert (Path(agent.working_dir) / "memory" / workspace_key / "SOUL.md").is_file()
'''
    result = subprocess.run(  # noqa: S603 - fixed script and repository path
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_milky_13_adapter_and_tool_schemas(tmp_path):
    script = r'''
import asyncio
import sys
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])

from nonebot.adapters.milky.event import EVENT_CLASSES, GroupDisbandEvent, MessageEvent
from nonebot.adapters.milky.message import Message
from tools import milky_message, milky_file

event = MessageEvent.model_validate({
    "time": 123, "self_id": 999,
    "data": {"message_scene": "friend", "peer_id": 456, "message_seq": 1,
             "sender_id": 456, "time": 123,
             "segments": [{"type": "markdown", "data": {"content": "# hello"}}]},
})
assert event.data.segments[0]["data"]["content"] == "# hello"
assert event.message[0].type == "markdown"
assert EVENT_CLASSES["group_disband"] is GroupDisbandEvent
assert "runtime" not in milky_file.persist_group_file.tool_call_schema.model_json_schema()["properties"]
assert "is_self_send" in milky_file.get_private_file_download_url.args

calls = []
async def send(**kwargs):
    message = kwargs["message"]
    assert isinstance(message, Message)
    elements = message.to_elements()
    assert elements[0]["data"]["messages"][0]["time"] == 123
    calls.append(kwargs)
    return SimpleNamespace(message_seq=9, time=456)

milky_message.get_bot = lambda: SimpleNamespace(send_group_message=send)
async def run():
    result = await milky_message.send_forwarded_message.ainvoke({
        "messages": [{"user_id": 456, "sender_name": "Alice", "text": "hello", "time": 123}],
        "message_scene": "group", "peer_id": 789,
    })
    assert "message_seq=9" in result
    assert calls[0]["group_id"] == 789
asyncio.run(run())
'''
    result = subprocess.run(  # noqa: S603 - fixed script and repository path
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
