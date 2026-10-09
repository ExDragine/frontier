# ruff: noqa: S101

import pytest

from utils import browser_runtime, markdown_render


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
        self.connected = True

    def is_connected(self):
        return self.connected

    async def close(self):
        self.connected = False

    async def new_page(self, viewport=None):
        self.page = _MarkdownDummyPage()
        return self.page


class _MarkdownDummyChromium:
    def __init__(self):
        self.browser = None
        self.launch_kwargs = None
        self.launch_calls = 0

    async def launch(self, **kwargs):
        self.launch_calls += 1
        self.launch_kwargs = kwargs
        self.browser = _MarkdownDummyBrowser()
        return self.browser


class _MarkdownDummyPlaywright:
    def __init__(self):
        self.chromium = _MarkdownDummyChromium()


class _MarkdownDummyPlaywrightFactory:
    def __init__(self):
        self.playwright = None
        self.start_calls = 0

    async def start(self):
        self.start_calls += 1
        self.playwright = _MarkdownDummyPlaywright()
        return self.playwright


@pytest.mark.asyncio
async def test_markdown_to_text_basic():
    text = await markdown_render.markdown_to_text("# Title\n\nHello")
    assert "Title" in text
    assert "Hello" in text


@pytest.mark.asyncio
async def test_markdown_to_text_preserves_link_addresses_and_copyable_code():
    text = await markdown_render.markdown_to_text(
        "[文档](https://example.com/docs?q=1&v=2)\n\n```python\nprint('hello')\n```"
    )
    assert "文档（https://example.com/docs?q=1&v=2）" in text
    assert "print('hello')" in text


@pytest.mark.asyncio
async def test_markdown_to_text_does_not_duplicate_autolink_addresses():
    text = await markdown_render.markdown_to_text("<https://example.com/docs>")
    assert text.count("https://example.com/docs") == 1


@pytest.mark.asyncio
async def test_markdown_to_text_keeps_component_content_and_media_sources_without_control_syntax():
    text = await markdown_render.markdown_to_text(
        '::card{title="比较" color="blue"}\n**正文** [文档](https://example.com/docs)\n::\n\n'
        '::image{url="https://example.com/picture.png" alt="图片说明"}\n::'
    )
    assert "比较" in text and "正文" in text and "图片说明" in text
    assert "文档（https://example.com/docs）" in text
    assert "https://example.com/picture.png" in text
    assert "::card" not in text and "data-rich" not in text


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
    monkeypatch.setattr(browser_runtime, "async_playwright", lambda: factory)
    monkeypatch.setattr(browser_runtime, "_browser", None)
    monkeypatch.setattr(markdown_render, "TEMPLATES_DIR", tmp_path / "templates")
    monkeypatch.setattr(markdown_render, "CACHE_DIR", tmp_path / "cache")

    result = await markdown_render.markdown_to_image("```mermaid\nA-->B\n```")
    assert result == b"img"
    assert list((tmp_path / "cache").glob("*.html")) == []

    assert factory.playwright is not None
    assert factory.playwright.chromium.browser is not None
    # markdown 渲染与 browser_capture 共用同一浏览器入口，GPU/WebGL 启动参数必须保留
    assert factory.playwright.chromium.launch_kwargs["headless"] is True
    assert "--enable-webgl" in factory.playwright.chromium.launch_kwargs["args"]
    page = factory.playwright.chromium.browser.page
    assert page is not None
    assert "html[data-frontier-ready='true']" in page.selectors
    assert len(page.routes) == 1
    assert "https?" in page.routes[0][0].pattern


@pytest.mark.asyncio
async def test_shared_browser_is_reused_and_restarted_after_disconnect(monkeypatch):
    """markdown/capture 共用同一浏览器入口：存活时复用，探活失败后重启。"""
    factory = _MarkdownDummyPlaywrightFactory()
    monkeypatch.setattr(browser_runtime, "async_playwright", lambda: factory)
    monkeypatch.setattr(browser_runtime, "_browser", None)

    first = await browser_runtime.get_browser()
    assert await browser_runtime.get_browser() is first
    assert factory.start_calls == 1

    first.connected = False  # 模拟浏览器进程崩溃
    restarted = await browser_runtime.get_browser()

    assert restarted is not first
    assert restarted.is_connected() is True
    assert factory.start_calls == 2  # 重启会重建 playwright driver 并重新 launch
    assert factory.playwright.chromium.launch_calls == 1
    assert "--enable-webgl" in factory.playwright.chromium.launch_kwargs["args"]

    await browser_runtime.close_browser()
    assert browser_runtime._browser is None
    assert browser_runtime._playwright is None


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
