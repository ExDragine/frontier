from httpx import Client
from langchain.tools import tool
from nonebot import logger

http_client = Client(timeout=30)


# 彗星工具
class CometTool:
    BASE = "https://cobs.si/api"

    def __init__(self, client: Client):
        self.client = client

    def info(self, name: str) -> str:
        try:
            resp = self.client.get(f"{self.BASE}/comet.api", params={"des": name})
            data = resp.json()
            obj = data["object"]
            return f"彗星 {obj['fullname']} 亮度 {obj['current_mag']}"
        except Exception as e:
            logger.error("Comet info error", exc_info=e)
            return f"❌ 彗星信息失败: {e}"

    def list(self, max_mag: int = 15) -> str:
        try:
            resp = self.client.get(f"{self.BASE}/comet_list.api", params={"cur-mag": max_mag})
            objs = resp.json().get("objects", [])
            return "\n".join(o["fullname"] for o in objs)
        except Exception as e:
            logger.error("Comet list error", exc_info=e)
            return f"❌ 彗星列表失败: {e}"


comet_tool = CometTool(http_client)


@tool(response_format="content")
async def comet_information(name: str) -> str:
    """
    获取彗星信息
    Args:
        name: 彗星名称
    Returns:
        彗星信息
    """
    return comet_tool.info(name)


@tool(response_format="content")
async def comet_list(cur_mag: int = 15) -> str:
    """
    获取彗星列表
    Args:
        cur_mag: 星等亮度(默认15)
    Returns:
        彗星列表
    """
    return comet_tool.list(cur_mag)
