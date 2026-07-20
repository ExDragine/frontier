# ruff: noqa: E402

"""Wolfx real-time earthquake feeds."""

from nonebot import get_driver, logger, require

require("nonebot_plugin_alconna")

from .cenc_client import cenc_websocket_service
from .cenc_handler import process_cenc_event

driver = get_driver()


@driver.on_startup
async def start_wolfx_service() -> None:
    if cenc_websocket_service.start(process_cenc_event):
        logger.info("Wolfx CENC WebSocket 监听服务已启动")
    else:
        logger.debug("Wolfx CENC WebSocket 监听服务已在运行")


@driver.on_shutdown
async def stop_wolfx_service() -> None:
    await cenc_websocket_service.stop()
