"""Playwright 浏览器截图与录屏模块。

为 Agent 工具提供网页截图和视频录制能力，自动管理浏览器生命周期：
- 检测浏览器进程是否存活，若无则自动初始化
- 执行前自动检测浏览器存活状态
- 浏览器崩溃时自动重启并重试一次
"""

import logging
import os
import subprocess
import tempfile
import time
from asyncio import Lock
from collections.abc import Callable
from typing import Any

import imageio_ffmpeg
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

_browser: Any = None
_playwright: Any = None
_browser_lock = Lock()

# 浏览器崩溃相关的错误消息特征
_CRASH_MSG_SNIPPETS = (
    "Browser closed",
    "Target closed",
    "Target page, context or browser has been closed",
    "Connection closed",
    "Browser has been closed",
    "Protocol error",
)


class PageLoadTimeoutError(RuntimeError):
    """页面加载超时，携带当前状态截图供工具层回退使用。"""

    def __init__(self, message: str, screenshot_bytes: bytes):
        super().__init__(message)
        self.screenshot_bytes = screenshot_bytes


def _is_crash_error(error: Exception) -> bool:
    """判断是否为浏览器崩溃类错误。"""
    return any(snippet in str(error) for snippet in _CRASH_MSG_SNIPPETS)


async def _get_browser():
    """返回持久化浏览器实例（延迟初始化，线程安全）。"""
    global _browser, _playwright
    async with _browser_lock:
        connected = False
        if _browser is not None:
            try:
                connected = _browser.is_connected()
            except Exception:
                connected = False
        if not connected:
            if _playwright is not None:
                try:
                    await _playwright.stop()
                except Exception:
                    pass
                _playwright = None
            _browser = None
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    "--use-gl=angle",
                    "--enable-webgl",
                    "--ignore-gpu-blocklist",
                ],
            )
            logger.info("Playwright 浏览器已初始化")
        return _browser


async def _is_browser_alive() -> bool:
    """检测浏览器进程是否存活。"""
    if _browser is None:
        return False
    try:
        return _browser.is_connected()
    except Exception:
        return False


async def _restart_browser():
    """强制重启浏览器进程。"""
    global _browser, _playwright
    async with _browser_lock:
        if _browser is not None:
            try:
                await _browser.close()
            except Exception:
                pass
            _browser = None
        if _playwright is not None:
            try:
                await _playwright.stop()
            except Exception:
                pass
            _playwright = None
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--use-gl=angle",
                "--enable-webgl",
                "--ignore-gpu-blocklist",
            ],
        )
        logger.info("Playwright 浏览器已重新启动")


async def _wait_for_page_ready(
    page,
    *,
    wait_selector: str | None = None,
    post_wait_ms: int = 500,
    hard_wait: bool = False,
    ready_timeout: int = 15000,
    wait_function: str | None = None,
) -> bool:
    """等待页面核心内容渲染就绪，返回 True（就绪）或 False（超时）。

    若指定 wait_selector → 等该选择器出现。
    若 hard_wait=True → 直接 wait_for_timeout(post_wait_ms)。
    默认方案B → 等可见媒体元素（img/canvas/video）出现，或文本量够 + networkidle。
    若指定 wait_function → 执行自定义 JS 等待条件（如等待 loading 指示器消失）。
    """
    try:
        if wait_selector:
            await page.wait_for_selector(wait_selector, timeout=ready_timeout)
        if wait_function:
            await page.wait_for_function(wait_function, timeout=ready_timeout)
        if post_wait_ms:
            if hard_wait:
                await page.wait_for_timeout(post_wait_ms)
            else:
                await page.wait_for_function(
                    "document.body && (document.body.innerText.trim().length > 20"
                    " || document.querySelector('img,canvas,video'))",
                    timeout=post_wait_ms,
                )
        return True
    except Exception:
        return False


async def _extract_page_data(page) -> dict:
    """从已加载完成的页面提取关键数据（坐标、数值、时间等）。

    ⚠️ 当前仅内置了地球可视化站点的 DOM 选择器。
    其他网站调用 page_data_out={} 会返回空 dict，不影响截图/录屏核心流程。

    如需支持更多网站的数据提取，在本函数内按 page.url 做域名分发，
    各自写对应的 JS 选择器即可，无需修改 screenshot/record_video 签名。
    """
    return await page.evaluate(
        """() => {
            const r = {};
            // spotlight-a — 主数据行（如风速）
            const rowA = document.querySelector('#spotlight-panel [data-name="spotlight-a"]');
            if (rowA && !rowA.hasAttribute('hidden')) {
                const valA = rowA.querySelector('div[aria-label]');
                if (valA) r['spotA.value'] = valA.getAttribute('aria-label');
                const labelA = rowA.querySelector('[data-name="product-label"]');
                if (labelA) r['spotA.label'] = labelA.textContent.trim();
            }
            // spotlight-b — 叠加层数据行（如温度、体感温度）
            const rowB = document.querySelector('#spotlight-panel [data-name="spotlight-b"]');
            if (rowB && !rowB.hasAttribute('hidden')) {
                const valB = rowB.querySelector('div[aria-label]');
                if (valB) r['spotB.value'] = valB.getAttribute('aria-label');
                const labelB = rowB.querySelector('[data-name="product-label"]');
                if (labelB) r['spotB.label'] = labelB.textContent.trim();
            }
            // 坐标
            const coords = document.querySelector('#spotlight-panel [data-name="spotlight-coords"]');
            if (coords) r.coords = coords.textContent.trim();
            // 数据时间
            const allDivs = document.querySelectorAll('div');
            allDivs.forEach(el => {
                const t = (el.textContent || '').trim();
                if (/^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2} Local$/.test(t)) r.time = t;
            });
            // 数据异常状态
            const statusCard = document.querySelector('[data-name="status-card"]');
            if (statusCard && statusCard.style.display !== 'none') {
                const field = statusCard.querySelector('.field');
                if (field) r.status_error = field.textContent.trim();
            }
            return r;
        }"""
    )


async def _run_with_crash_retry(action: Callable[[], Any]) -> Any:
    """执行浏览器操作，崩溃时自动重启并重试一次。"""
    try:
        return await action()
    except Exception as exc:
        if _is_crash_error(exc):
            logger.warning("浏览器崩溃 (%s)，正在重启并重试…", exc)
            await _restart_browser()
            return await action()
        raise


def _webm_to_mp4_bytes(
    webm_path: str, mp4_path: str, trim_start: float = 0, trim_duration: float | None = None
) -> bytes:
    """将 webm 转为 mp4，可选裁掉开头 trim_start 秒、保留 trim_duration 秒。"""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg]
    if trim_start > 0:
        cmd += ["-ss", str(trim_start)]
    cmd += ["-i", webm_path]
    if trim_duration is not None:
        cmd += ["-t", str(trim_duration)]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", "-y", mp4_path]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"视频转码失败: {result.stderr}")
    with open(mp4_path, "rb") as f:
        mp4_bytes = f.read()
    logger.info("视频转码完成: %s → %d bytes", webm_path, len(mp4_bytes))
    return mp4_bytes


async def screenshot(
    url: str,
    *,
    width: int = 1280,
    height: int = 720,
    full_page: bool = False,
    selector: str | None = None,
    wait_until: str = "networkidle",
    timeout: int = 30000,
    wait_selector: str | None = None,
    post_wait_ms: int = 500,
    hard_wait: bool = False,
    ready_timeout: int = 15000,
    wait_function: str | None = None,
    page_data_out: dict | None = None,
) -> bytes:
    """对指定 URL 进行网页截图，返回 PNG 字节数据。

    内置浏览器崩溃重试机制：若浏览器进程崩溃，自动重启后重试一次。

    Args:
        url: 目标网页 URL（支持 http/https/file 协议）
        width: 视口宽度（像素）
        height: 视口高度（像素）
        full_page: 截取完整页面而非仅视口区域
        selector: 仅截取指定 CSS 选择器对应的元素，为 None 时截取整个页面
        wait_until: 页面加载等待策略（load / domcontentloaded / networkidle）
        timeout: 导航超时毫秒数
        wait_selector: 导航后等待该 CSS 选择器出现（如 "canvas" 等待 WebGL 初始化）
        post_wait_ms: 内容就绪后额外等待毫秒数
        hard_wait: True=直接 sleep post_wait_ms，False=方案B 智能检测
        ready_timeout: _wait_for_page_ready 超时毫秒数
        wait_function: 自定义 JS 等待条件（如等待 loading 指示器消失）
        page_data_out: 传入 dict 时，将 _extract_page_data() 提取的数据写入该 dict。
            当前仅适配地球可视化站点，其他网站返回空 dict 不影响截图/录屏主流程。
            扩展新网站：在 _extract_page_data() 按域名分发即可，无需改本函数签名。

    Returns:
        PNG 格式的截图字节数据
    """

    async def _do_screenshot() -> bytes:
        logger.info(f"正在打开网页并截图: {url}")
        browser = await _get_browser()
        page = await browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            await _wait_for_page_ready(
                page,
                wait_selector=wait_selector,
                post_wait_ms=post_wait_ms,
                hard_wait=hard_wait,
                ready_timeout=ready_timeout,
                wait_function=wait_function,
            )
            if page_data_out is not None:
                try:
                    page_data_out.update(await _extract_page_data(page))
                except Exception:
                    pass
            if selector:
                element = await page.wait_for_selector(selector, timeout=timeout)
                if element is None:
                    raise RuntimeError(f"未找到选择器对应的元素: {selector}")
                result = await element.screenshot(type="png")
            else:
                result = await page.screenshot(full_page=full_page, type="png")
            logger.info(f"截图完成: {len(result)} bytes")
            return result
        finally:
            await page.close()

    return await _run_with_crash_retry(_do_screenshot)


async def record_video(
    url: str,
    *,
    duration: int = 10,
    width: int = 1920,
    height: int = 1080,
    wait_until: str = "networkidle",
    timeout: int = 30000,
    wait_selector: str | None = None,
    post_wait_ms: int = 500,
    hard_wait: bool = False,
    ready_timeout: int = 15000,
    wait_function: str | None = None,
    page_data_out: dict | None = None,
) -> bytes:
    """录制指定 URL 的网页视频，返回 mp4 字节数据。

    单 Context 流程：导航 → 等页面就绪 → 录制 duration 秒。
    Playwright 原生输出 webm 至 TemporaryDirectory，转码为 mp4 后返回。

    内置浏览器崩溃重试机制：若浏览器进程在录制期间崩溃，自动重启后重试一次。

    若页面在 ready_timeout 内未就绪，抛出 PageLoadTimeoutError（携带当前状态截图）。

    Args:
        url: 目标网页 URL（支持 http/https/file 协议）
        duration: 录制时长（秒）
        width: 视口宽度（像素）
        height: 视口高度（像素）
        wait_until: 页面加载等待策略（load / domcontentloaded / networkidle）
        timeout: 导航超时毫秒数
        wait_selector: 导航后等待该 CSS 选择器出现（如 "canvas" 等待 WebGL 初始化）
        post_wait_ms: 内容就绪后额外等待毫秒数
        hard_wait: True=直接 sleep post_wait_ms，False=方案B 智能检测
        ready_timeout: _wait_for_page_ready 超时毫秒数
        wait_function: 自定义 JS 等待条件（如等待 loading 指示器消失）
        page_data_out: 传入 dict 时，将 _extract_page_data() 提取的数据写入该 dict。
            当前仅适配地球可视化站点，其他网站返回空 dict 不影响主流程。
            扩展新网站：在 _extract_page_data() 按域名分发即可，无需改本函数签名。

    Returns:
        mp4 格式的视频字节数据
    """

    async def _do_record() -> bytes:
        logger.info(f"正在打开网页并录屏: {url}")
        browser = await _get_browser()

        with tempfile.TemporaryDirectory() as video_dir:
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=video_dir,
                record_video_size={"width": width, "height": height},
            )
            _recording_start = time.time()
            try:
                page = await context.new_page()
                await page.goto(url, wait_until=wait_until, timeout=timeout)
                ready = await _wait_for_page_ready(
                    page,
                    wait_selector=wait_selector,
                    post_wait_ms=post_wait_ms,
                    hard_wait=hard_wait,
                    ready_timeout=ready_timeout,
                    wait_function=wait_function,
                )
                if not ready:
                    screenshot_bytes = await page.screenshot(type="png")
                    raise PageLoadTimeoutError(
                        f"页面加载超时 ({ready_timeout}ms): {url}",
                        screenshot_bytes,
                    )
                if page_data_out is not None:
                    try:
                        page_data_out.update(await _extract_page_data(page))
                    except Exception:
                        pass
                _ready_elapsed = time.time() - _recording_start
                await page.wait_for_timeout(duration * 1000)
            finally:
                await context.close()

            video_files = sorted(
                [f for f in os.listdir(video_dir) if f.endswith(".webm")],
                key=lambda f: os.path.getmtime(os.path.join(video_dir, f)),
            )
            if not video_files:
                raise FileNotFoundError(f"录屏未生成视频文件: {url}")
            webm_path = os.path.join(video_dir, video_files[-1])
            mp4_path = os.path.join(video_dir, "output.mp4")
            mp4_bytes = _webm_to_mp4_bytes(
                webm_path, mp4_path, trim_start=_ready_elapsed, trim_duration=float(duration)
            )
        logger.info(f"录屏完成: {len(mp4_bytes)} bytes (裁掉前 {_ready_elapsed:.1f}s 加载)")
        return mp4_bytes

    return await _run_with_crash_retry(_do_record)


async def fetch_data_only(
    url: str,
    *,
    width: int = 1920,
    height: int = 1080,
    wait_until: str = "networkidle",
    timeout: int = 60000,
    wait_selector: str | None = None,
    wait_function: str | None = None,
    post_wait_ms: int = 5000,
    hard_wait: bool = True,
    ready_timeout: int = 30000,
) -> dict:
    """仅导航到 URL 并提取页面数据，不截图不录屏。no_video 模式专用。"""

    async def _do_fetch() -> dict:
        logger.info(f"正在获取页面数据: {url}")
        browser = await _get_browser()
        page = await browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            await _wait_for_page_ready(
                page,
                wait_selector=wait_selector,
                post_wait_ms=post_wait_ms,
                hard_wait=hard_wait,
                ready_timeout=ready_timeout,
                wait_function=wait_function,
            )
            data = await _extract_page_data(page)
            logger.info(f"页面数据提取完成: {url}")
            return data
        finally:
            await page.close()

    return await _run_with_crash_retry(_do_fetch)


async def close_browser():
    """清理全局浏览器实例（进程退出时调用）。"""
    global _browser, _playwright
    async with _browser_lock:
        if _browser is not None:
            try:
                await _browser.close()
            except Exception:
                pass
            _browser = None
            logger.info("Playwright 浏览器已关闭")
        if _playwright is not None:
            try:
                await _playwright.stop()
            except Exception:
                pass
            _playwright = None
