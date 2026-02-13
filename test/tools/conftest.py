# ruff: noqa: S101

import importlib
import importlib.util
import sys
import types
from itertools import count
from pathlib import Path

import pytest


def _module_exists(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def _install_module(name: str, module: types.ModuleType) -> None:
    sys.modules[name] = module
    if "." in name:
        parent, child = name.rsplit(".", 1)
        parent_module = sys.modules.get(parent)
        if parent_module is None:
            parent_module = types.ModuleType(parent)
            _install_module(parent, parent_module)
        setattr(parent_module, child, module)


def _make_alconna_module() -> types.ModuleType:
    alconna = types.ModuleType("nonebot_plugin_alconna")

    class Image:
        def __init__(self, url=None, raw=None):
            self.url = url
            self.raw = raw

    class Target:
        def __init__(self, id=None):
            self.id = id

    class Text:
        def __init__(self, text: str = ""):
            self.text = text

    class UniMessage:
        def __init__(self, content=None):
            self.content = content

        @classmethod
        def image(cls, url=None, raw=None):
            return cls({"type": "image", "url": url, "raw": raw})

        @classmethod
        def audio(cls, url=None, raw=None):
            return cls({"type": "audio", "url": url, "raw": raw})

        @classmethod
        def video(cls, url=None, raw=None):
            return cls({"type": "video", "url": url, "raw": raw})

        @classmethod
        def emoji(cls, id=None):
            return cls({"type": "emoji", "id": id})

        @classmethod
        def text(cls, text: str):
            return cls({"type": "text", "text": text})

        async def send(self, *args, **kwargs):
            return None

    alconna.Image = Image
    alconna.Target = Target
    alconna.Text = Text
    alconna.UniMessage = UniMessage
    return alconna


def _install_fallback_stubs() -> None:
    if not _module_exists("nonebot_plugin_alconna"):
        _install_module("nonebot_plugin_alconna", _make_alconna_module())

    if not _module_exists("pypinyin"):
        pypinyin = types.ModuleType("pypinyin")
        pypinyin.lazy_pinyin = lambda text: [text]
        _install_module("pypinyin", pypinyin)

    if not _module_exists("dotenv"):
        dotenv = types.ModuleType("dotenv")
        dotenv.load_dotenv = lambda *args, **kwargs: None
        _install_module("dotenv", dotenv)

    if not _module_exists("langchain_tavily"):
        tavily = types.ModuleType("langchain_tavily")

        class _Base:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        tavily.TavilySearch = _Base
        tavily.TavilyExtract = _Base
        tavily.TavilyCrawl = _Base
        tavily.TavilyMap = _Base
        _install_module("langchain_tavily", tavily)

    if not _module_exists("langchain_mcp_adapters.client"):
        client_mod = types.ModuleType("langchain_mcp_adapters.client")

        class MultiServerMCPClient:
            def __init__(self, *_args, **_kwargs):
                pass

            async def get_tools(self):
                return []

        client_mod.MultiServerMCPClient = MultiServerMCPClient
        _install_module("langchain_mcp_adapters.client", client_mod)

    if not _module_exists("langgraph.prebuilt"):
        prebuilt = types.ModuleType("langgraph.prebuilt")
        prebuilt.InjectedState = lambda key: key
        _install_module("langgraph.prebuilt", prebuilt)

    if not _module_exists("langchain_community.document_loaders"):
        loaders = types.ModuleType("langchain_community.document_loaders")

        class _Loader:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def load(self):
                return []

        loaders.ArxivLoader = _Loader
        loaders.BiliBiliLoader = _Loader
        loaders.WikipediaLoader = _Loader
        _install_module("langchain_community.document_loaders", loaders)
    else:
        loaders = importlib.import_module("langchain_community.document_loaders")
        if not hasattr(loaders, "ArxivLoader"):
            loaders.ArxivLoader = type(
                "ArxivLoader", (), {"__init__": lambda self, *a, **k: None, "load": lambda self: []}
            )
        if not hasattr(loaders, "WikipediaLoader"):
            loaders.WikipediaLoader = type(
                "WikipediaLoader",
                (),
                {"__init__": lambda self, *a, **k: None, "load": lambda self: []},
            )

    if not _module_exists("bs4"):
        bs4 = types.ModuleType("bs4")

        class BeautifulSoup:
            def __init__(self, *_args, **_kwargs):
                pass

            def select(self, *_args, **_kwargs):
                return []

        bs4.BeautifulSoup = BeautifulSoup
        _install_module("bs4", bs4)

    if not _module_exists("playwright.async_api"):
        async_api = types.ModuleType("playwright.async_api")

        def async_playwright():
            raise RuntimeError("playwright is not available in test fallback")

        async_api.async_playwright = async_playwright
        _install_module("playwright.async_api", async_api)


_install_fallback_stubs()


@pytest.fixture
def load_tool_module():
    repo_root = Path(__file__).resolve().parents[2]
    tools_dir = repo_root / "tools"
    idx_gen = count()

    def _load(name: str):
        module_path = tools_dir / f"{name}.py"
        unique_name = f"test_tools_{name}_{next(idx_gen)}"
        spec = importlib.util.spec_from_file_location(unique_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载模块: {module_path}")
        module = importlib.util.module_from_spec(spec)

        old_alconna = sys.modules.get("nonebot_plugin_alconna")
        sys.modules["nonebot_plugin_alconna"] = _make_alconna_module()

        old_nonebot_require = None
        old_plugin_require = None
        try:
            import nonebot
            import nonebot.plugin.load as plugin_load

            old_nonebot_require = getattr(nonebot, "require", None)
            old_plugin_require = getattr(plugin_load, "require", None)
            plugin_load.require = lambda *_args, **_kwargs: None
            nonebot.require = plugin_load.require
        except Exception:
            nonebot = None
            plugin_load = None

        try:
            sys.modules[unique_name] = module
            spec.loader.exec_module(module)
            return module
        finally:
            if old_alconna is None:
                sys.modules.pop("nonebot_plugin_alconna", None)
            else:
                sys.modules["nonebot_plugin_alconna"] = old_alconna

            if old_nonebot_require is not None and old_plugin_require is not None:
                try:
                    plugin_load.require = old_plugin_require
                    nonebot.require = old_nonebot_require
                except Exception:
                    pass

    return _load
