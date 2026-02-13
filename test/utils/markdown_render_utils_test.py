# ruff: noqa: S101

import pytest
import types

from utils import markdown_render


@pytest.mark.asyncio
async def test_markdown_to_text_basic():
    text = await markdown_render.markdown_to_text("# Title\n\nHello")
    assert "Title" in text
    assert "Hello" in text


@pytest.mark.asyncio
async def test_markdown_to_image_calls(monkeypatch, tmp_path):
    async def fake_start():
        class DummyBrowser:
            async def new_page(self, viewport=None):
                return DummyPage()

        class DummyPlaywright:
            def __init__(self):
                async def launch(headless=True):
                    return DummyBrowser()

                self.chromium = types.SimpleNamespace(launch=launch)

        return DummyPlaywright()

    class DummyPage:
        async def goto(self, *_args, **_kwargs):
            return None

        async def set_viewport_size(self, *_args, **_kwargs):
            return None

        async def wait_for_load_state(self, *_args, **_kwargs):
            return None

        async def wait_for_function(self, *_args, **_kwargs):
            return None

        async def wait_for_timeout(self, *_args, **_kwargs):
            return None

        async def evaluate(self, *_args, **_kwargs):
            return 100

        async def wait_for_selector(self, *_args, **_kwargs):
            return None

        async def screenshot(self, **_kwargs):
            return b"img"

        def on(self, *_args, **_kwargs):
            return None

    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "markdown_render.html").write_text(
        "<html><body>{style_block}{html_content}</body></html>",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "markdown_render.css").write_text("", encoding="utf-8")
    (tmp_path / "cache").mkdir()

    def fake_async_playwright():
        return types.SimpleNamespace(start=fake_start)

    monkeypatch.setattr(markdown_render, "async_playwright", fake_async_playwright)
    markdown_render.browser = None
    markdown_render.page = None

    result = await markdown_render.markdown_to_image("```mermaid\nA-->B\n```")
    assert result == b"img"
