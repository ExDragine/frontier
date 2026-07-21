# ruff: noqa: S101

import pytest

from utils import markdown_render


class _MarkdownDummyPage:
    def __init__(self):
        self.routes = []
        self.selectors = []

    async def goto(self, *_args, **_kwargs):
        return None

    async def route(self, pattern, handler):
        self.routes.append((pattern, handler))

    async def set_viewport_size(self, *_args, **_kwargs):
        return None

    async def wait_for_load_state(self, *_args, **_kwargs):
        return None

    async def wait_for_function(self, *_args, **_kwargs):
        return None

    async def wait_for_timeout(self, *_args, **_kwargs):
        return None

    async def evaluate(self, expression, *_args, **_kwargs):
        if "__FRONTIER_RENDER__" in expression:
            return []
        return 100

    async def wait_for_selector(self, selector, *_args, **_kwargs):
        self.selectors.append(selector)
        return None

    async def screenshot(self, **_kwargs):
        return b"img"

    def on(self, *_args, **_kwargs):
        return None


class _MarkdownDummyBrowser:
    def __init__(self):
        self.page = None

    async def new_page(self, viewport=None):
        self.page = _MarkdownDummyPage()
        return self.page


class _MarkdownDummyChromium:
    def __init__(self):
        self.browser = None

    async def launch(self, headless=True):
        self.browser = _MarkdownDummyBrowser()
        return self.browser


class _MarkdownDummyPlaywright:
    def __init__(self):
        self.chromium = _MarkdownDummyChromium()


class _MarkdownDummyPlaywrightFactory:
    def __init__(self):
        self.playwright = None

    async def start(self):
        self.playwright = _MarkdownDummyPlaywright()
        return self.playwright


@pytest.mark.asyncio
async def test_markdown_to_text_basic():
    text = await markdown_render.markdown_to_text("# Title\n\nHello")
    assert "Title" in text
    assert "Hello" in text


@pytest.mark.asyncio
async def test_markdown_to_image_calls(monkeypatch, tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "markdown_assets").mkdir()
    (tmp_path / "templates" / "markdown_render.html").write_text(
        "<html><body>{style_block}{asset_style_url}{asset_script_url}{html_content}</body></html>",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "markdown_render.css").write_text("", encoding="utf-8")
    (tmp_path / "templates" / "markdown_assets" / "markdown-render.css").write_text("", encoding="utf-8")
    (tmp_path / "templates" / "markdown_assets" / "markdown-render.js").write_text(
        "window.__FRONTIER_RENDER__ = {state: 'ready', errors: []};",
        encoding="utf-8",
    )
    (tmp_path / "cache").mkdir()

    factory = _MarkdownDummyPlaywrightFactory()
    monkeypatch.setattr(markdown_render, "async_playwright", lambda: factory)
    monkeypatch.setattr(markdown_render, "_browser", None)
    monkeypatch.setattr(markdown_render, "TEMPLATES_DIR", tmp_path / "templates")
    monkeypatch.setattr(markdown_render, "CACHE_DIR", tmp_path / "cache")

    result = await markdown_render.markdown_to_image("```mermaid\nA-->B\n```")
    assert result == b"img"
    assert list((tmp_path / "cache").glob("*.html")) == []

    page = factory.playwright.chromium.browser.page
    assert "html[data-frontier-ready='true']" in page.selectors
    assert len(page.routes) == 1
    assert "https?" in page.routes[0][0].pattern


def test_markdown_renderer_uses_only_local_bundled_assets():
    template = (markdown_render.TEMPLATES_DIR / "markdown_render.html").read_text(encoding="utf-8")
    source = (markdown_render.PROJECT_ROOT / "renderer" / "src" / "main.js").read_text(encoding="utf-8")

    assert "https://" not in template
    assert "http://" not in template
    assert "unpkg" not in template
    assert "{asset_style_url}" in template
    assert "{asset_script_url}" in template
    assert (markdown_render.TEMPLATES_DIR / "markdown_assets" / "markdown-render.css").is_file()
    assert (markdown_render.TEMPLATES_DIR / "markdown_assets" / "markdown-render.js").is_file()
    assert "SVGRenderer" in source
    assert 'renderer: "svg"' in source
    assert "createElementNS" not in source
