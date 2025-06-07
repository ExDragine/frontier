import httpx
from langchain_core.tools import tool
from nonebot.adapters.qq.message import MessageSegment


@tool(response_format="content_and_artifact")
async def station_location(name):
    """
    获取空间站位置图像

    Args:
        name: 空间站名称

    Returns:
        空间站位置图像
    """
    stations = {"国际空间站": 25544, "天宫": 48274}
    ENDPOINT = (
        f"https://www.heavens-above.com/orbitdisplay.aspx?icon=default&width=300&height=300&satid={stations[name]}"
    )
    content = httpx.get(ENDPOINT, timeout=30).content
    if content:
        return "空间站位置获取成功", MessageSegment.file_image(content)
    else:
        return "空间站位置获取失败", None
