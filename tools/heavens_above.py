from langchain_core.tools import tool

from utils.alconna import UniMessage
from utils.http_client import get_http_client

httpx_client = get_http_client("heavens_above")


@tool(response_format="content_and_artifact")
async def station_location(name) -> tuple[str, UniMessage | None]:
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
    content = (await httpx_client.get(ENDPOINT)).content
    if content:
        return "空间站位置获取成功", UniMessage.image(raw=content)
    else:
        return "空间站位置获取失败", None
