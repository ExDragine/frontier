# ruff: noqa: S101

import importlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr


@pytest.mark.asyncio
async def test_arxiv_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("arxiv")

    class DummyLoader:
        def __init__(self, query):
            self.query = query

        def load(self):
            return [{"title": "A", "query": self.query}]

    monkeypatch.setattr(mod, "ArxivLoader", DummyLoader)
    result = await mod.get_arxiv_paper_info("llm")
    parsed = json.loads(result)
    assert parsed[0]["query"] == "llm"


def test_bilibili_extract_info(load_tool_module):
    mod = load_tool_module("bilibili")
    data = mod.extract_info(
        {
            "title": "标题",
            "url": "https://b23.tv/test",
            "owner": {"name": "UP", "mid": 1},
            "stat": {"view": 10},
            "dimension": {"width": 1920, "height": 1080},
            "pages": [{"part": "P1"}],
            "pubdate": 1700000000,
        }
    )
    assert data["标题"] == "标题"
    assert data["UP主"].startswith("UP")
    assert data["视频分辨率"] == "1920x1080"


@pytest.mark.asyncio
async def test_bilibili_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("bilibili")

    class DummyLoader:
        def __init__(self, urls):
            self.urls = urls

        def load(self):
            return [SimpleNamespace(metadata={"title": "Video", "url": self.urls[0], "pages": []})]

    monkeypatch.setattr(mod, "BiliBiliLoader", DummyLoader)
    result = await mod.get_bilibili_video_info("https://b23.tv/x")
    parsed = json.loads(result)
    assert parsed["标题"] == "Video"
    assert parsed["视频链接"] == "https://b23.tv/x"


def test_safe_eval_success_and_invalid(load_tool_module):
    mod = load_tool_module("calculator")
    assert mod.safe_eval("1+2*3") == 7.0

    with pytest.raises(ValueError):
        mod.safe_eval("__import__('os').system('echo hi')")


@pytest.mark.asyncio
async def test_simple_calculator(load_tool_module):
    mod = load_tool_module("calculator")
    ok = await mod.simple_calculator("2**3")
    fail = await mod.simple_calculator("a+b")
    assert "计算结果" in ok
    assert "计算失败" in fail


@pytest.mark.asyncio
async def test_wikipedia_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("wikipedia")

    class DummyLoader:
        def __init__(self, **_kwargs):
            pass

        def load(self):
            return [
                SimpleNamespace(metadata={"title": "Earth", "source": "https://wiki/Earth"}, page_content="planet")
            ]

    monkeypatch.setattr(mod, "WikipediaLoader", DummyLoader)
    result = await mod.get_wikipedia_pages("earth")
    assert "Title: Earth" in result
    assert "URL: https://wiki/Earth" in result


@pytest.mark.asyncio
async def test_deepseek_balance_tool_formats_balance(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr("sk-test"), raising=False)
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_BASE", "", raising=False)

    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "is_available": True,
                "balance_infos": [
                    {
                        "currency": "CNY",
                        "total_balance": "110.00",
                        "granted_balance": "10.00",
                        "topped_up_balance": "100.00",
                    }
                ],
            }

    class DummyClient:
        async def get(self, url, headers):
            captured["url"] = url
            captured["headers"] = headers
            return DummyResponse()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert captured["url"] == "https://api.deepseek.com/user/balance"
    assert captured["headers"] == {"Authorization": "Bearer sk-test"}
    assert "DeepSeek API 余额：可用" in result
    assert "- CNY 总余额 110.00，赠金 10.00，充值 100.00" in result


@pytest.mark.asyncio
async def test_deepseek_balance_tool_reports_missing_key(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr(""), raising=False)

    result = await mod.get_deepseek_api_balance()

    assert result == "未配置 DeepSeek API Key：请在 env.toml 的 [key].deepseek_api_key 中填写。"


@pytest.mark.asyncio
async def test_deepseek_balance_tool_normalizes_configured_base_url(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr("sk-test"), raising=False)
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1", raising=False)

    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"is_available": False, "balance_infos": []}

    class DummyClient:
        async def get(self, url, headers):
            captured["url"] = url
            return DummyResponse()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert captured["url"] == "https://api.deepseek.com/user/balance"
    assert result == "DeepSeek API 余额：不可用\n余额明细：无"


@pytest.mark.asyncio
async def test_deepseek_balance_tool_reports_http_error(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr("sk-test"), raising=False)

    class DummyClient:
        async def get(self, url, headers):
            raise httpx.ConnectError("network down")

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert result == "获取 DeepSeek API 余额失败: network down"


def test_mcp_get_tools(load_tool_module, monkeypatch):
    Path("mcp.json").write_text("{}", encoding="utf-8")
    mod = load_tool_module("mcp_client")

    class DummyClient:
        async def get_tools(self):
            return ["a", "b"]

    monkeypatch.setattr(mod, "client", DummyClient())
    tools = mod.mcp_get_tools()
    assert tools == ["a", "b"]


def test_module_tools_groups_tools_by_domain(monkeypatch):
    class FakeBaseTool:
        def __init__(self, name: str):
            self.name = name

    langchain_tools = sys.modules.get("langchain.tools")
    if langchain_tools is None:
        langchain_tools = types.ModuleType("langchain.tools")
        sys.modules["langchain.tools"] = langchain_tools
    monkeypatch.setattr(langchain_tools, "BaseTool", FakeBaseTool, raising=False)

    package_name = "test_tools_grouping_pkg"
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    fake_modules = {
        "adapter": types.SimpleNamespace(send_image=FakeBaseTool("send_image")),
        "calculator": types.SimpleNamespace(simple_calculator=FakeBaseTool("simple_calculator")),
        "milky_file": types.SimpleNamespace(upload_group_file=FakeBaseTool("upload_group_file")),
        "milky_friend": types.SimpleNamespace(send_friend_nudge=FakeBaseTool("send_friend_nudge")),
        "milky_group": types.SimpleNamespace(set_group_name=FakeBaseTool("set_group_name")),
        "milky_message": types.SimpleNamespace(get_message=FakeBaseTool("get_message")),
        "milky_system": types.SimpleNamespace(get_login_info=FakeBaseTool("get_login_info")),
        "deepseek_balance": types.SimpleNamespace(get_deepseek_api_balance=FakeBaseTool("get_deepseek_api_balance")),
        "arxiv": types.SimpleNamespace(get_arxiv_paper_info=FakeBaseTool("get_arxiv_paper_info")),
        "aurora": types.SimpleNamespace(aurora_live=FakeBaseTool("aurora_live")),
        "earthquake": types.SimpleNamespace(get_china_earthquake=FakeBaseTool("get_china_earthquake")),
        "paint": types.SimpleNamespace(get_paint=FakeBaseTool("get_paint")),
        "video": types.SimpleNamespace(get_video=FakeBaseTool("get_video")),
        "memory": types.SimpleNamespace(search_messages=FakeBaseTool("search_messages")),
        "iching": types.SimpleNamespace(iching_divination=FakeBaseTool("iching_divination")),
        "unknown_local": types.SimpleNamespace(mystery_tool=FakeBaseTool("mystery_tool")),
    }

    def fake_iter_modules(_paths):
        return [types.SimpleNamespace(name=name) for name in fake_modules]

    original_import_module = importlib.import_module

    def fake_import_module(name, package=None):
        if package == package_name and name.startswith("."):
            return fake_modules[name[1:]]
        return original_import_module(name, package)

    monkeypatch.setattr("pkgutil.iter_modules", fake_iter_modules)
    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    mcp_module = types.ModuleType(f"{package_name}.mcp_client")
    mcp_module.mcp_get_tools = lambda: [FakeBaseTool("mcp_tool")]
    monkeypatch.setitem(sys.modules, f"{package_name}.mcp_client", mcp_module)

    spec = importlib.util.spec_from_file_location(
        package_name,
        tools_dir / "__init__.py",
        submodule_search_locations=[str(tools_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, package_name, module)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    groups = module.agent_tools.subagent_tools

    assert {tool.name for tool in module.agent_tools.main_tools} == {
        "send_image",
        "simple_calculator",
        "upload_group_file",
        "send_friend_nudge",
        "set_group_name",
        "get_message",
        "get_login_info",
        "get_deepseek_api_balance",
        "get_paint",
        "get_video",
        "mcp_tool",
        "search_messages",
        "mystery_tool",
        "get_arxiv_paper_info",
        "aurora_live",
        "get_china_earthquake",
        "iching_divination",
    }
    assert {tool.name for tool in groups["research"]} == {"get_arxiv_paper_info"}
    assert {tool.name for tool in groups["astro"]} == {"aurora_live"}
    assert {tool.name for tool in groups["earth"]} == {"get_china_earthquake"}
    assert {tool.name for tool in groups["media"]} == set()
    assert {tool.name for tool in groups["memory"]} == {"search_messages"}
    assert {tool.name for tool in groups["divination"]} == {"iching_divination"}
    assert {tool.name for tool in groups["external"]} == {"mcp_tool"}
    assert {tool.name for tool in module.agent_tools.web_tools} == set()
    assert "mcp_tool" in {tool.name for tool in module.agent_tools.all_tools}
