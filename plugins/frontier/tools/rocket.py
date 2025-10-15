import datetime

from httpx import AsyncClient, Client
from langchain.tools import tool
from nonebot import logger

# 常量配置
TLP_LAUNCH_URL = "https://tlpnetwork.com/api/launches"

# 全局 HTTP 客户端复用
http_client = Client(timeout=30)
async_http_client = AsyncClient(timeout=30, http2=True)


# 火箭发射
@tool(response_format="content")
async def rocket_launches(days: int = 3) -> str:
    """
    获取火箭发射信息
    Args:
        days: 天数(默认3)
    Returns:
        火箭发射信息
    """
    if not 1 <= days <= 7:
        return "❌ 天数1-7"
    try:
        now = datetime.datetime.now(datetime.UTC)
        end = now + datetime.timedelta(days=days)
        payload = {"net": {"gte": now.isoformat(), "lte": end.isoformat()}}
        resp = await async_http_client.post(TLP_LAUNCH_URL, json=payload)
        resp.raise_for_status()
        missions = resp.json()
        if not missions:
            return f"🚀 未来{days}天无发射"
        lines = [f"{m['name']} @ {m['net']}" for m in missions]
        return "\n".join(lines)
    except Exception as e:
        logger.error("Rocket error", exc_info=e)
        return f"❌ 火箭信息失败: {e}"
