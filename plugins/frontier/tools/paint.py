import time
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from nonebot import logger, require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMsg  # noqa: E402
from nonebot_plugin_alconna.uniseg import UniMessage  # noqa: E402


@tool(response_format="content_and_artifact")
async def get_paint(prompt: str) -> tuple[str, UniMsg | None]:
    """生成图片

    Args:
        prompt: 绘画提示词，以英文输入，描述尽可能详细，不少于50个单词

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 图片消息段)
    """
    start_time = time.time()
    logger.info(f"🛠️ 调用工具: paint, 参数: prompt={prompt}")

    try:
        response = httpx.get(
            f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1440&height=900&model=flux&nologo=true&enhance=true",
            timeout=30,
        )
        result = UniMessage.image(raw=response.content)
        end_time = time.time()
        logger.info(f"✅ 工具执行成功: paint (耗时: {end_time - start_time:.2f}s)")
        return f"成功生成图片，提示词：{prompt}", result
    except Exception as e:
        end_time = time.time()
        logger.error(f"💥 工具执行异常: paint - {str(e)} (耗时: {end_time - start_time:.2f}s)")
        return f"图片生成失败: {str(e)}", None
