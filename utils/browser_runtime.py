"""进程内唯一的 Playwright 浏览器入口。

``utils.browser_capture``（网页截图/录屏/取数）与 ``utils.markdown_render``
（Markdown/HTML 渲染）都委托本模块获取 Chromium，因此单进程最多只驻留一个
浏览器进程，且两者共享同一份探活与崩溃重启逻辑。

启动参数统一采用带 WebGL 支持的一组：Markdown 渲染链里的 Mermaid/ECharts
以及 ``browser_capture`` 的网页可视化都依赖 GPU/WebGL，缺少这些参数时
headless Chromium 可能拒绝初始化 WebGL 上下文。
"""

import logging
from asyncio import Lock
from contextlib import suppress
from typing import Any

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# GPU/WebGL 相关参数，两类调用方都必须保留。
_BROWSER_ARGS = (
    "--use-gl=angle",
    "--enable-webgl",
    "--ignore-gpu-blocklist",
)

_browser: Any = None
_playwright: Any = None
_browser_lock = Lock()


def _is_connected(browser: Any) -> bool:
    """判断浏览器进程是否仍然存活。"""
    try:
        return bool(browser.is_connected())
    except Exception:
        return False


async def _launch_locked() -> Any:
    """在已持有 ``_browser_lock`` 的前提下（重新）启动浏览器。"""
    global _browser, _playwright
    if _browser is not None:
        if _is_connected(_browser):
            with suppress(Exception):
                await _browser.close()
        _browser = None
    if _playwright is not None:
        with suppress(Exception):
            await _playwright.stop()
        _playwright = None
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True, args=list(_BROWSER_ARGS))
    return _browser


async def get_browser() -> Any:
    """返回共享浏览器实例（延迟初始化，线程安全，探活失败时自动重启）。"""
    global _browser
    async with _browser_lock:
        if _browser is None or not _is_connected(_browser):
            logger.info("Playwright 浏览器已初始化")
            return await _launch_locked()
        return _browser


async def restart_browser() -> Any:
    """强制重启浏览器进程，返回新实例。"""
    async with _browser_lock:
        browser = await _launch_locked()
        logger.info("Playwright 浏览器已重新启动")
        return browser


async def close_browser() -> None:
    """关闭共享浏览器并停止 Playwright（进程退出时调用）。"""
    global _browser, _playwright
    async with _browser_lock:
        if _browser is not None:
            with suppress(Exception):
                await _browser.close()
            _browser = None
            logger.info("Playwright 浏览器已关闭")
        if _playwright is not None:
            with suppress(Exception):
                await _playwright.stop()
            _playwright = None
