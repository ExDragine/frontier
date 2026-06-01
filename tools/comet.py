from langchain.tools import tool
from nonebot import logger

from utils.http_client import get_http_client

_COMET_BASE = "https://cobs.si/api"
httpx_client = get_http_client("comet")


@tool(response_format="content")
async def comet_information(name: str) -> str:
    """
    获取彗星信息。
    Args:
        name: 彗星名称
    Returns:
        彗星信息
    """
    try:
        resp = await httpx_client.get(f"{_COMET_BASE}/comet.api", params={"des": name})
        data = resp.json()
        obj = data["object"]
        return f"彗星 {obj['fullname']} 亮度 {obj['current_mag']}"
    except Exception as e:
        logger.error("Comet info error", exc_info=e)
        return f"❌ 彗星信息失败: {e}"


@tool(response_format="content")
async def comet_list(cur_mag: int = 15) -> str:
    """
    获取彗星列表。
    Args:
        cur_mag: 星等亮度（默认 15）
    Returns:
        彗星列表
    """
    try:
        resp = await httpx_client.get(f"{_COMET_BASE}/comet_list.api", params={"cur-mag": cur_mag})
        objs = resp.json().get("objects", [])
        return "\n".join(o["fullname"] for o in objs)
    except Exception as e:
        logger.error("Comet list error", exc_info=e)
        return f"❌ 彗星列表失败: {e}"
