from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client

httpx_client = get_http_client("weather")

NASA_WEATHER_URL = "https://mars.nasa.gov/rss/api/?feed=weather&category=msl&feedtype=json"


# 火星天气
@tool(response_format="content")
async def mars_weather() -> str:
    """
    获取火星天气
    Returns:
        火星天气
    """
    try:
        resp = await httpx_client.get(NASA_WEATHER_URL)
        resp.raise_for_status()
        data = resp.json()
        return f"火星天气: {data['descriptions']}"
    except Exception as e:
        logger.error("Mars weather error", exc_info=e)
        return f"❌ 火星天气失败: {e}"


@tool(response_format="content_and_artifact")
async def get_wind_map(name: str) -> tuple[str, UniMessage | None]:
    """
    获取风切变或涡旋图像

    Args:
        name (str): 图像名称，字符串类型，只有风切图和涡旋图两种选择

    Returns:
        tuple[str, UniMessage | None]: 返回构建好的消息串
    """
    url = {
        "风切图": "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmssht.GIF",
        "wind_shear": "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmssht.GIF",
        "涡旋图": "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsvor.GIF",
        "vorticity": "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsvor.GIF",
    }
    if name not in url:
        return "❌ 图像名称无效", None
    return "获取成功", UniMessage.image(url=url[name])
