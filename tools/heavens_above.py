import httpx
from langchain.tools import tool
from nonebot import require

from utils.staged_artifacts import stage_artifact_response

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)


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
        return stage_artifact_response("空间站位置获取成功", UniMessage.image(raw=content))
    else:
        return "空间站位置获取失败", None


async def aclose_http_client() -> None:
    await httpx_client.aclose()
