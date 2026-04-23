# ruff: noqa: S101

import base64
import importlib
import importlib.util
import sys
import types
from itertools import count
from pathlib import Path
from types import SimpleNamespace

import pytest


def _image_response(raw: bytes):
    return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(raw).decode("utf-8"))])


def _tiny_png_bytes() -> bytes:
    return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6f8AAAAASUVORK5CYII=")


@pytest.fixture
def load_wonderland_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "plugins/wonderland/__init__.py"
    idx_gen = count()

    async def fake_message_extract(_segments):
        return "", [], [], []

    def _load():
        unique_name = f"test_plugins_wonderland_{next(idx_gen)}"
        spec = importlib.util.spec_from_file_location(unique_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载模块: {module_path}")

        module = importlib.util.module_from_spec(spec)
        message_stub = types.ModuleType("utils.message")
        message_stub.message_extract = fake_message_extract

        old_message = sys.modules.get("utils.message")
        utils_pkg = importlib.import_module("utils")
        old_attr = getattr(utils_pkg, "message", None)
        sys.modules["utils.message"] = message_stub
        utils_pkg.message = message_stub
        old_nonebot_require = None
        old_plugin_require = None
        try:
            import nonebot
            import nonebot.plugin.load as plugin_load

            old_nonebot_require = getattr(nonebot, "require", None)
            old_plugin_require = getattr(plugin_load, "require", None)
            plugin_load.require = lambda *_args, **_kwargs: None
            nonebot.require = plugin_load.require
            sys.modules[unique_name] = module
            spec.loader.exec_module(module)
            return module
        finally:
            if old_message is None:
                sys.modules.pop("utils.message", None)
            else:
                sys.modules["utils.message"] = old_message
            if old_attr is None:
                delattr(utils_pkg, "message")
            else:
                utils_pkg.message = old_attr
            if old_nonebot_require is not None and old_plugin_require is not None:
                plugin_load.require = old_plugin_require
                nonebot.require = old_nonebot_require

    return _load


@pytest.mark.asyncio
async def test_paint_uses_images_generate_without_reference_images(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()
    calls = {}

    class DummyImages:
        async def generate(self, **kwargs):
            calls["generate"] = kwargs
            return _image_response(b"generated-image")

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = DummyImages()

    monkeypatch.setattr(wonderland, "AsyncClient", DummyClient)

    result = await wonderland.paint("a crystal fox")

    assert result == b"generated-image"
    assert calls["client"]["base_url"] == wonderland.EnvConfig.OPENAI_BASE_URL
    assert calls["client"]["api_key"] == wonderland.EnvConfig.OPENAI_API_KEY.get_secret_value()
    assert calls["generate"]["model"] == wonderland.EnvConfig.PAINT_MODEL
    assert calls["generate"]["prompt"] == "a crystal fox"
    assert calls["generate"]["response_format"] == "b64_json"


def test_strip_paint_prompt_handles_prefixed_text_without_whitespace(load_wonderland_module):
    wonderland = load_wonderland_module()

    assert wonderland.strip_paint_prompt("/画图一只猫") == "一只猫"
    assert wonderland.strip_paint_prompt("paint a crystal fox") == "a crystal fox"


@pytest.mark.asyncio
async def test_paint_uses_images_edit_with_reference_images(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()
    calls = {}

    class DummyImages:
        async def edit(self, **kwargs):
            calls["edit"] = kwargs
            return _image_response(b"edited-image")

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = DummyImages()

    monkeypatch.setattr(wonderland, "AsyncClient", DummyClient)

    result = await wonderland.paint("turn it into watercolor", [_tiny_png_bytes()])

    assert result == b"edited-image"
    assert calls["edit"]["model"] == wonderland.EnvConfig.PAINT_MODEL
    assert calls["edit"]["prompt"] == "turn it into watercolor"
    assert calls["edit"]["response_format"] == "b64_json"
    assert len(calls["edit"]["image"]) == 1
    filename, content, content_type = calls["edit"]["image"][0]
    assert filename == "reference-1.png"
    assert isinstance(content, bytes)
    assert content.startswith(b"\x89PNG\r\n\x1a\n")
    assert content_type == "image/png"


@pytest.mark.asyncio
async def test_paint_returns_none_when_images_api_fails(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()

    class DummyImages:
        async def generate(self, **_kwargs):
            raise RuntimeError("boom")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.images = DummyImages()

    monkeypatch.setattr(wonderland, "AsyncClient", DummyClient)

    result = await wonderland.paint("a crystal fox")

    assert result is None
