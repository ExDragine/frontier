import httpx
from langchain_core.tools import tool
from nonebot import require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMsg  # noqa: E402
from nonebot_plugin_alconna.uniseg import UniMessage  # noqa: E402


@tool(response_format="content_and_artifact")
async def station_location(name) -> tuple[str, UniMsg | None]:
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
        return "空间站位置获取成功", UniMessage.image(raw=content)
    else:
        return "空间站位置获取失败", None
