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


def _webm_to_mp4_bytes(webm_path: str, mp4_path: str) -> bytes:
    """使用 imageio-ffmpeg 将 webm 转为 mp4 写入 mp4_path，读回后返回 bytes。"""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-i",
        webm_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-y",
        mp4_path,
    ]
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
        post_wait_ms: wait_selector 命中后额外等待毫秒数

    Returns:
        PNG 格式的截图字节数据
    """

    async def _do_screenshot() -> bytes:
        logger.info(f"正在打开网页并截图: {url}")
        browser = await _get_browser()
        page = await browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            if post_wait_ms:
                if hard_wait:
                    await page.wait_for_timeout(post_wait_ms)
                else:
                    try:
                        await page.wait_for_function(
                            "document.body && (document.body.innerText.trim().length > 20"
                            " || document.querySelector('img,canvas,video'))",
                            timeout=post_wait_ms,
                        )
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
) -> bytes:
    """录制指定 URL 的网页视频，返回 mp4 字节数据。

    Playwright 原生输出 webm 至 TemporaryDirectory，
    context.close() 后通过 imageio-ffmpeg stdout 管道转为 mp4 bytes，
    TemporaryDirectory 退出时自动清理 webm 源文件，全程 mp4 不落盘。

    内置浏览器崩溃重试机制：若浏览器进程在录制期间崩溃，自动重启后重试一次。

    Args:
        url: 目标网页 URL（支持 http/https/file 协议）
        duration: 录制时长（秒）
        width: 视口宽度（像素）
        height: 视口高度（像素）
        wait_until: 页面加载等待策略（load / domcontentloaded / networkidle）
        timeout: 导航超时毫秒数

    Returns:
        mp4 格式的视频字节数据
    """

    async def _do_record() -> bytes:
        logger.info(f"正在打开网页并录屏: {url}")
        browser = await _get_browser()

        # 预热
        warmup_context = await browser.new_context(
            viewport={"width": width, "height": height},
        )
        try:
            warmup_page = await warmup_context.new_page()
            await warmup_page.goto(url, wait_until=wait_until, timeout=timeout)
            if wait_selector:
                await warmup_page.wait_for_selector(wait_selector, timeout=timeout)
            if post_wait_ms:
                if hard_wait:
                    await warmup_page.wait_for_timeout(post_wait_ms)
                else:
                    try:
                        await warmup_page.wait_for_function(
                            "document.body && (document.body.innerText.trim().length > 20"
                            " || document.querySelector('img,canvas,video'))",
                            timeout=post_wait_ms,
                        )
                    except Exception:
                        pass
        finally:
            await warmup_context.close()

        # 正式录制：缓存已热，二次导航秒加载，录制时长 ≈ duration
        with tempfile.TemporaryDirectory() as video_dir:
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=video_dir,
                record_video_size={"width": width, "height": height},
            )
            try:
                page = await context.new_page()
                await page.goto(url, wait_until=wait_until, timeout=timeout)
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=timeout)
                if post_wait_ms:
                    if hard_wait:
                        await page.wait_for_timeout(post_wait_ms)
                    else:
                        try:
                            await page.wait_for_function(
                                "document.body && (document.body.innerText.trim().length > 20"
                                " || document.querySelector('img,canvas,video'))",
                                timeout=post_wait_ms,
                            )
                        except Exception:
                            pass
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
            mp4_bytes = _webm_to_mp4_bytes(webm_path, mp4_path)
        logger.info(f"录屏完成: {len(mp4_bytes)} bytes")
        return mp4_bytes

    return await _run_with_crash_retry(_do_record)


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
