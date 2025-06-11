import time
from typing import Optional

from langchain_core.tools import tool
from nonebot import logger, require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMsg  # noqa: E402
from nonebot_plugin_alconna.uniseg import UniMessage  # noqa: E402


@tool(response_format="content_and_artifact")
async def aurora_live() -> tuple[str, Optional[UniMsg]]:
    """获取北极光实时图像

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 图片消息段)
    """
    start_time = time.time()
    logger.info("🛠️ 调用工具: aurora_live")

    try:
        url = "https://auroramax.phys.ucalgary.ca/recent/recent_1080p.jpg"
        result = UniMessage.image(url=url)
        end_time = time.time()
        logger.info(f"✅ 工具执行成功: aurora_live (耗时: {end_time - start_time:.2f}s)")
        return "成功获取北极光实时图像", result
    except Exception as e:
        end_time = time.time()
        logger.error(f"💥 工具执行异常: aurora_live - {str(e)} (耗时: {end_time - start_time:.2f}s)")
        return f"获取北极光实时图像失败: {str(e)}", None
