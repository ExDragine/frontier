# ruff: noqa: S101
"""Verify media authorization and injected identities with real LangChain tools."""

import subprocess
import sys
from pathlib import Path


def test_media_policy_in_real_agent_tools(tmp_path):
    script = r'''
import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

repo = Path(sys.argv[1])
sys.path.insert(0, str(repo))
import nonebot
nonebot.init(driver="nonebot.drivers.fastapi:Driver", log_level="WARNING")
nonebot.require("nonebot_plugin_alconna")
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from utils.agent_context import FrontierRuntimeContext
from utils.configs import EnvConfig
from utils.media_access import MEDIA_ACCESS_DENIED

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

async def main():
    for name in ("paint", "video"):
        spec = importlib.util.spec_from_file_location(f"media_contract_{name}", repo / f"tools/{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        tool = getattr(module, f"get_{name}")
        properties = tool.tool_call_schema.model_json_schema()["properties"]
        assert set(properties) == {"prompt", "mode" if name == "paint" else "input_type"}, properties
        service_calls, limit_calls = [], []

        async def paint(prompt, images):
            service_calls.append(prompt)
            return b"image"

        async def video(prompt, **kwargs):
            service_calls.append(prompt)
            return SimpleNamespace(raw=b"video", url=None)

        def check(*args, **kwargs):
            limit_calls.append(args)
            return SimpleNamespace(allowed=True)

        if name == "paint":
            module.paint = paint
        else:
            module.generate_video = video
        setattr(module, f"{name}_rate_limiter", SimpleNamespace(check=check))

        async def invoke(user_id, group_id, configured_identity):
            model = Model(responses=[
                AIMessage(content="", tool_calls=[{"name": tool.name, "args": {"prompt": "a cat"}, "id": "media"}]),
                AIMessage(content="done"),
            ])
            graph = create_agent(model, tools=[tool], context_schema=FrontierRuntimeContext)
            result = await graph.ainvoke(
                {"messages": [{"role": "user", "content": "generate media"}]},
                config={"configurable": configured_identity},
                context=FrontierRuntimeContext(user_id, group_id, None, "."),
            )
            assert result["messages"][-1].content == "done"
            return next(m for m in result["messages"] if isinstance(m, ToolMessage))

        EnvConfig.reload({"config_version": 2, "paint_policy": {
            "whitelist_mode": True, "whitelist_group_list": [123], "blacklist_person_list": [456],
        }})
        denied = await invoke("456", 123, {"user_id": "789", "group_id": 123})
        assert denied.content == MEDIA_ACCESS_DENIED and denied.artifact is None
        assert not service_calls and not limit_calls

        allowed = await invoke("789", 123, {"user_id": "456", "group_id": 999})
        assert allowed.content != MEDIA_ACCESS_DENIED and allowed.artifact is not None
        assert service_calls == ["a cat"] and len(limit_calls) == 1

        # The same imported tool must immediately respect a reloaded policy.
        EnvConfig.reload({"config_version": 2, "paint_policy": {"whitelist_mode": True}})
        denied = await invoke("789", 123, {"user_id": "789", "group_id": 123})
        assert denied.content == MEDIA_ACCESS_DENIED and denied.artifact is None
        assert service_calls == ["a cat"] and len(limit_calls) == 1

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
