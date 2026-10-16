# ruff: noqa: S101
"""Real tool schemas, HTTP serialization and a search/fetch/read_file cycle."""

import subprocess
import sys
from pathlib import Path


def test_search_fetch_and_full_page_read_in_real_agent(tmp_path):
    script = r"""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path
repo = Path(sys.argv[1])
sys.path.insert(0, str(repo))
from httpx2 import AsyncClient, MockTransport, Response
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from utils import deepseek_web as web
from utils.agent_context import FrontierRuntimeContext
from utils.configs import EnvConfig

spec = importlib.util.spec_from_file_location("search_tools_contract", repo / "tools/deepseek_search.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
schema = mod.deepseek_web_search.tool_call_schema.model_json_schema()["properties"]
assert schema["count"]["default"] == 20 and schema["count"]["maximum"] == 50
assert schema["need_content"]["default"] is False
assert not {"runtime", "config", "localization"} & schema.keys()
EnvConfig.reload({"config_version": 2, "providers": {"deepseek_responses": {"api_key": "contract-key"}},
                  "search": {"content_preview_chars": 256}})
root = Path("workspace").resolve()
root.mkdir()
calls, seen = [], []
full_page = "# Page\n" + "Relevant evidence.\n" * 300 + "TAIL_EVIDENCE"

def handler(request):
    body = json.loads(request.content)
    calls.append((str(request.url), body))
    assert request.headers["Authorization"] == "Bearer contract-key"
    assert request.headers["content-type"] == "application/json"
    if request.url.path.endswith("/search"):
        assert body == {"query": "test query", "count": 20, "need_content": False}
        return Response(200, json={"results": [{
            "title": f"Page {i}", "url": f"https://example.com/{i}", "summary": "Evidence summary",
            "snippet": "short", "content": "", "site_name": "Example", "date": None,
            "rerank_score": 2.4, "authority": 3,
        } for i in range(20)]})
    assert request.url.path == "/v1/tools/fetch" and body == {"url": "https://example.com/0"}
    return Response(200, json={"title": "Page 0", "content": full_page})

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(messages)
        if len(seen) in {2, 3}:
            data = json.loads(next(m.content for m in reversed(messages) if isinstance(m, ToolMessage)))
            assert data["status"] == "ok"
            if len(seen) == 2:
                assert data["count"] == 20
                tool_name, args = "deepseek_web_fetch", {"url": data["results"][0]["url"]}
            else:
                assert data["truncated"] and "TAIL_EVIDENCE" not in data["content"]
                tool_name, args = "read_file", {"file_path": data["content_path"], "limit": 1000}
            self.responses[self.i] = AIMessage(content="", tool_calls=[{"name": tool_name, "args": args, "id": f"call-{len(seen)}"}])
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

async def main():
    async with AsyncClient(transport=MockTransport(handler)) as client:
        web.get_http_client = lambda *args, **kwargs: client
        model = Model(responses=[AIMessage(content="", tool_calls=[{
            "name": "deepseek_web_search", "args": {"query": "test query"}, "id": "call-1",
        }]), AIMessage(content="placeholder"), AIMessage(content="placeholder"), AIMessage(content="done")])
        graph = create_deep_agent(model=model, tools=[mod.deepseek_web_search, mod.deepseek_web_fetch],
                                  subagents=[], backend=FilesystemBackend(root_dir=root),
                                  context_schema=FrontierRuntimeContext)
        result = await graph.ainvoke({"messages": [{"role": "user", "content": "Research and verify"}]},
                                    context=FrontierRuntimeContext("1", 123, None, str(root)))
        assert result["messages"][-1].content == "done" and len(seen) == 4
        last = next(m.content for m in reversed(seen[-1]) if isinstance(m, ToolMessage))
        assert "TAIL_EVIDENCE" in last, str(last)[-1500:]
        assert len(calls) == 2
asyncio.run(main())
"""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
