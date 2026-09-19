# ruff: noqa: S101

import importlib
import importlib.util
import json
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


def test_mcp_get_tools_skips_failed_server(load_tool_module, monkeypatch, caplog):
    Path("mcp.json").write_text(
        json.dumps(
            {
                "healthy": {"url": "https://healthy.example/mcp", "transport": "http"},
                "broken": {"url": "https://broken.example/mcp", "transport": "http"},
            }
        ),
        encoding="utf-8",
    )

    calls = []

    class DummyClient:
        def __init__(self, entry):
            self.url = entry["url"]

        async def list_tools(self):
            calls.append(self.url)
            if "broken" in self.url:
                raise RuntimeError("connection closed")
            return ["a", "b"]

    adapter_module = types.ModuleType("utils.mcp")
    adapter_module.__dict__["build_mcp_adapter"] = DummyClient
    monkeypatch.setitem(sys.modules, "utils.mcp", adapter_module)
    mod = load_tool_module("mcp_client")
    tools = mod.mcp_get_tools()

    assert tools == ["a", "b"]
    assert calls == ["https://healthy.example/mcp", "https://broken.example/mcp"]
    assert mod.mcp_get_tools() is tools
    assert len(calls) == 2
    assert "MCP 服务 'broken' 加载失败，已跳过: RuntimeError: connection closed" in caplog.text


def test_mcp_example_only_uses_http_endpoints():
    example_path = Path(__file__).resolve().parents[2] / "mcp.json.example"
    config = json.loads(example_path.read_text(encoding="utf-8"))

    assert config
    for entry in config.values():
        assert entry["transport"] in {"http", "streamable_http"}
        assert entry["url"].startswith(("http://", "https://"))
        assert not {"command", "args", "env"} & entry.keys()


def test_module_tools_groups_tools_by_domain(monkeypatch):
    class FakeBaseTool:
        def __init__(self, name: str, response_format: str | None = None):
            self.name = name
            self.response_format = response_format

    langchain_core_tools = sys.modules.get("langchain_core.tools")
    if langchain_core_tools is None:
        langchain_core_tools = types.ModuleType("langchain_core.tools")
        monkeypatch.setitem(sys.modules, "langchain_core.tools", langchain_core_tools)
    monkeypatch.setattr(langchain_core_tools, "BaseTool", FakeBaseTool, raising=False)

    package_name = "test_tools_grouping_pkg"
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    fake_modules = {
        "adapter": types.SimpleNamespace(send_image=FakeBaseTool("send_image")),
        "milky_file": types.SimpleNamespace(upload_group_file=FakeBaseTool("upload_group_file")),
        "milky_friend": types.SimpleNamespace(send_friend_nudge=FakeBaseTool("send_friend_nudge")),
        "milky_group": types.SimpleNamespace(set_group_name=FakeBaseTool("set_group_name")),
        "milky_message": types.SimpleNamespace(get_message=FakeBaseTool("get_message", "content")),
        "milky_system": types.SimpleNamespace(get_login_info=FakeBaseTool("get_login_info", "content")),
        "deepseek_balance": types.SimpleNamespace(
            get_deepseek_api_balance=FakeBaseTool("get_deepseek_api_balance", "content")
        ),
        "aurora": types.SimpleNamespace(aurora_live=FakeBaseTool("aurora_live")),
        "satellite": types.SimpleNamespace(
            get_fy4b_satellite_image=FakeBaseTool("get_fy4b_satellite_image"),
        ),
        "earthquake": types.SimpleNamespace(
            get_china_earthquake=FakeBaseTool("get_china_earthquake", "content"),
            get_usgs_significant_earthquakes=FakeBaseTool("get_usgs_significant_earthquakes", "content"),
        ),
        "radar": types.SimpleNamespace(
            get_available_china_radar_areas=FakeBaseTool("get_available_china_radar_areas", "content"),
            get_static_china_radar=FakeBaseTool("get_static_china_radar", "content_and_artifact"),
        ),
        "paint": types.SimpleNamespace(get_paint=FakeBaseTool("get_paint")),
        "video": types.SimpleNamespace(get_video=FakeBaseTool("get_video")),
        "memory": types.SimpleNamespace(
            get_recent_conversation=FakeBaseTool("get_recent_conversation", "content"),
            search_messages=FakeBaseTool("search_messages"),
            get_history_messages=FakeBaseTool("get_history_messages"),
        ),
        "iching": types.SimpleNamespace(iching_divination=FakeBaseTool("iching_divination", "content")),
        "unknown_local": types.SimpleNamespace(mystery_tool=FakeBaseTool("mystery_tool", "content")),
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
    mcp_module.__dict__["mcp_get_tools"] = lambda: [
        FakeBaseTool("mcp_tool"),
        FakeBaseTool("tavily_extract", "content"),
        FakeBaseTool("tavily_search", "content"),
        FakeBaseTool("web_search_exa", "content"),
        FakeBaseTool("web_fetch_exa", "content"),
    ]
    monkeypatch.setitem(sys.modules, f"{package_name}.mcp_client", mcp_module)

    spec = importlib.util.spec_from_file_location(
        package_name,
        tools_dir / "__init__.py",
        submodule_search_locations=[str(tools_dir)],
    )
    assert spec is not None
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
        "get_recent_conversation",
        "search_messages",
        "get_history_messages",
        "mcp_tool",
        "tavily_extract",
        "tavily_search",
        "web_search_exa",
        "web_fetch_exa",
        "mystery_tool",
        "aurora_live",
        "get_fy4b_satellite_image",
        "get_static_china_radar",
        "get_china_earthquake",
        "get_usgs_significant_earthquakes",
        "get_available_china_radar_areas",
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
    ptc_names = {tool.name for tool in module.agent_tools.ptc_tools}
    direct_names = {tool.name for tool in module.agent_tools.direct_tools}
    research_names = {tool.name for tool in module.agent_tools.research_tools}
    assert ptc_names == {
        "get_message",
        "get_login_info",
        "get_deepseek_api_balance",
        "get_china_earthquake",
        "get_usgs_significant_earthquakes",
        "get_available_china_radar_areas",
        "iching_divination",
    }
    assert direct_names == {
        "send_image",
        "upload_group_file",
        "send_friend_nudge",
        "set_group_name",
        "get_paint",
        "get_video",
        "mcp_tool",
        "mystery_tool",
        "aurora_live",
        "get_fy4b_satellite_image",
        "get_static_china_radar",
        "get_recent_conversation",
        "search_messages",
        "get_history_messages",
    }
    assert research_names == {"tavily_extract", "tavily_search", "web_search_exa", "web_fetch_exa"}
    assert ptc_names.isdisjoint(direct_names)
    assert ptc_names.isdisjoint(research_names)
    assert direct_names.isdisjoint(research_names)
    assert ptc_names | direct_names | research_names == {tool.name for tool in module.agent_tools.main_tools}
    assert {tool.name for tool in groups["memory"]} == {
        "get_recent_conversation",
        "search_messages",
        "get_history_messages",
    }
    assert {tool.name for tool in groups["divination"]} == {"iching_divination"}
    assert {tool.name for tool in groups["external"]} == {
        "mcp_tool",
        "tavily_extract",
        "tavily_search",
        "web_search_exa",
        "web_fetch_exa",
    }

    # Recovered discovery replaces the old registry without duplicating tools.
    registry = module.agent_tools
    revision = registry.revision
    registry._register_mcp_tools(registry.mcp_tools)
    assert registry.revision == revision
    recovered = FakeBaseTool("web_search_exa", "content")
    registry._register_mcp_tools([recovered])
    assert registry.revision == revision + 1
    assert registry.research_tools == [recovered]
    assert sum(tool is recovered for tool in registry.main_tools) == 1
    assert "mcp_tool" not in registry.tool_metadata
    assert "send_image" in {tool.name for tool in registry.main_tools}


@pytest.mark.asyncio
async def test_mcp_discovery_retries_failed_servers_after_backoff(load_tool_module, monkeypatch):
    calls = []
    recovered = False

    class Adapter:
        def __init__(self, entry):
            self.name = entry["url"]

        async def list_tools(self):
            calls.append(self.name)
            if self.name == "broken" and not recovered:
                raise ConnectionError("temporary")
            return [self.name]

    adapter_module = types.ModuleType("utils.mcp")
    adapter_module.build_mcp_adapter = Adapter
    monkeypatch.setitem(sys.modules, "utils.mcp", adapter_module)
    mod = load_tool_module("mcp_client")
    mod.tools_description = {name: {"transport": "http", "url": name} for name in ("healthy", "broken")}
    clock = [100.0]
    monkeypatch.setattr(mod, "time", types.SimpleNamespace(monotonic=lambda: clock[0]))
    first = await mod.mcp_get_tools_async()
    assert first == ["healthy"]
    assert await mod.mcp_get_tools_async() is first
    assert calls == ["healthy", "broken"]
    clock[0] = 130.0
    assert await mod.mcp_get_tools_async() is first
    assert calls == ["healthy", "broken", "broken"]
    recovered = True
    clock[0] = 189.0
    assert await mod.mcp_get_tools_async() is first
    clock[0] = 190.0
    tools = await mod.mcp_get_tools_async()
    assert tools == ["healthy", "broken"]
    assert await mod.mcp_get_tools_async() is tools
    assert calls == ["healthy", "broken", "broken", "broken"]
    assert mod._retry_at == {}


def test_mcp_config_accepts_string_auth_headers(load_tool_module, monkeypatch):
    adapter_module = types.ModuleType("utils.mcp")
    adapter_module.build_mcp_adapter = lambda entry: None
    monkeypatch.setitem(sys.modules, "utils.mcp", adapter_module)
    mod = load_tool_module("mcp_client")
    mod._validate_mcp_config({"exa": {
        "transport": "http", "url": "https://example.com/mcp",
        "headers": {"Authorization": "Bearer test-only"},
    }})


@pytest.mark.parametrize("entry,valid", [
    ({"url": "http://127.0.0.1:8000/mcp"}, True),
    ({"url": "https://example.com/mcp", "transport": "streamable_http"}, True),
    ({"url": "https://example.com/mcp", "transport": "sse"}, False),
    ({"transport": "stdio", "command": "uvx", "args": ["mcp-server-time"]}, False),
    ({"url": "https://example.com/mcp", "command": "python"}, False),
    ({"url": "https://example.com/mcp", "env": {}}, False),
    ({"transport": "http"}, False),
    ({"url": ""}, False),
    ({"url": "file:///tmp/server"}, False),
    ({"url": "https:///mcp"}, False),
    ({"url": "https://bad host/mcp"}, False),
    ({"url": "https://example.com:invalid/mcp"}, False),
    ({"url": "https://example.com/mcp", "headers": {"Authorization": 123}}, False),
    ({"url": "https://example.com/mcp", "startup_timeout_seconds": 301}, False),
])
def test_mcp_http_config_validation(load_tool_module, monkeypatch, entry, valid):
    adapter_module = types.ModuleType("utils.mcp")
    adapter_module.build_mcp_adapter = lambda entry: None
    monkeypatch.setitem(sys.modules, "utils.mcp", adapter_module)
    mod = load_tool_module("mcp_client")
    if valid:
        mod._validate_mcp_config({"server": entry})
    else:
        with pytest.raises(ValueError):
            mod._validate_mcp_config({"server": entry})


def test_mcp_config_errors_do_not_echo_credentials(load_tool_module, monkeypatch):
    adapter_module = types.ModuleType("utils.mcp")
    adapter_module.build_mcp_adapter = lambda entry: None
    monkeypatch.setitem(sys.modules, "utils.mcp", adapter_module)
    mod = load_tool_module("mcp_client")
    Path("mcp.json").write_text(json.dumps({"server": {
        "url": "https://example.com/mcp?key=secret-query",
        "headers": {"Authorization": "secret-header"}, "command": "uvx",
    }}))
    with pytest.raises(RuntimeError) as error:
        mod._load_and_validate()
    assert "secret-query" not in str(error.value)
    assert "secret-header" not in str(error.value)
