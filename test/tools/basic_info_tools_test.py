# ruff: noqa: S101

import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from utils.http_client import ConnectError


@pytest.mark.asyncio
async def test_deepseek_balance_tool_formats_balance(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod, "get_provider_profile", lambda _name: {"api_key": "sk-test", "base_url": ""})

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
    monkeypatch.setattr(mod, "get_provider_profile", lambda _name: {"api_key": "", "base_url": ""})

    result = await mod.get_deepseek_api_balance()

    assert result == "未配置 DeepSeek API Key：请在 env.toml 的 [providers.deepseek].api_key 中填写。"


@pytest.mark.asyncio
async def test_deepseek_balance_tool_normalizes_configured_base_url(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(
        mod,
        "get_provider_profile",
        lambda _name: {"api_key": "sk-test", "base_url": "https://api.deepseek.com/v1"},
    )

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
    monkeypatch.setattr(mod, "get_provider_profile", lambda _name: {"api_key": "sk-test", "base_url": ""})

    class DummyClient:
        async def get(self, url, headers):
            raise ConnectError("network down")

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert result == "获取 DeepSeek API 余额失败: network down"


def test_mcp_get_tools(load_tool_module, monkeypatch):
    Path("mcp.json").write_text("{}", encoding="utf-8")

    class FakeMultiServerMCPClient:
        def __init__(self, _config):
            pass

    client_module = types.ModuleType("langchain_mcp_adapters.client")
    client_module.MultiServerMCPClient = FakeMultiServerMCPClient
    monkeypatch.setitem(sys.modules, "langchain_mcp_adapters.client", client_module)
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

    langchain_core_tools = sys.modules.get("langchain_core.tools")
    if langchain_core_tools is None:
        langchain_core_tools = types.ModuleType("langchain_core.tools")
        sys.modules["langchain_core.tools"] = langchain_core_tools
    monkeypatch.setattr(langchain_core_tools, "BaseTool", FakeBaseTool, raising=False)

    package_name = "test_tools_grouping_pkg"
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    fake_modules = {
        "adapter": types.SimpleNamespace(send_image=FakeBaseTool("send_image")),
        "milky_file": types.SimpleNamespace(upload_group_file=FakeBaseTool("upload_group_file")),
        "milky_friend": types.SimpleNamespace(send_friend_nudge=FakeBaseTool("send_friend_nudge")),
        "milky_group": types.SimpleNamespace(set_group_name=FakeBaseTool("set_group_name")),
        "milky_message": types.SimpleNamespace(get_message=FakeBaseTool("get_message")),
        "milky_system": types.SimpleNamespace(get_login_info=FakeBaseTool("get_login_info")),
        "deepseek_balance": types.SimpleNamespace(get_deepseek_api_balance=FakeBaseTool("get_deepseek_api_balance")),
        "aurora": types.SimpleNamespace(aurora_live=FakeBaseTool("aurora_live")),
        "satellite": types.SimpleNamespace(
            get_fy4b_satellite_image=FakeBaseTool("get_fy4b_satellite_image"),
        ),
        "earthquake": types.SimpleNamespace(
            get_china_earthquake=FakeBaseTool("get_china_earthquake"),
            get_usgs_significant_earthquakes=FakeBaseTool("get_usgs_significant_earthquakes"),
        ),
        "radar": types.SimpleNamespace(
            get_available_china_radar_areas=FakeBaseTool("get_available_china_radar_areas"),
            get_static_china_radar=FakeBaseTool("get_static_china_radar"),
        ),
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
        "aurora_live",
        "get_fy4b_satellite_image",
        "get_china_earthquake",
        "get_usgs_significant_earthquakes",
        "get_available_china_radar_areas",
        "get_static_china_radar",
        "iching_divination",
    }
    assert "research" not in groups
    assert {tool.name for tool in groups["astro"]} == {
        "aurora_live",
        "get_fy4b_satellite_image",
    }
    assert {tool.name for tool in groups["earth"]} == {
        "get_china_earthquake",
        "get_usgs_significant_earthquakes",
        "get_available_china_radar_areas",
        "get_static_china_radar",
    }
    assert {tool.name for tool in groups["media"]} == set()
    assert {tool.name for tool in groups["memory"]} == {"search_messages"}
    assert {tool.name for tool in groups["divination"]} == {"iching_divination"}
    assert {tool.name for tool in groups["external"]} == {"mcp_tool"}
    assert {tool.name for tool in module.agent_tools.web_tools} == set()
    assert "mcp_tool" in {tool.name for tool in module.agent_tools.all_tools}
