import logging
import zoneinfo
from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool

from utils.http_client import get_http_client

logger = logging.getLogger(__name__)

# 常量配置
LAUNCH_API_URL = "https://ll.thespacedevs.com/2.3.0/launches/"

# 全局 HTTP 客户端复用
http_client = get_http_client("rocket")


# 火箭发射
@tool(response_format="content")
async def get_launches(days: int = 7):
    """获取未来指定天数内的火箭发射计划。
    Args:
        days (int): 未来天数，默认值为7天。
    Returns:
        str: 火箭发射计划的详细信息。"""
    messages = ""
    url = LAUNCH_API_URL

    now = datetime.now(UTC)

    # 构造查询参数
    params = {"net__gte": now.isoformat(), "net__lt": (now + timedelta(days=days)).isoformat(), "ordering": "net", "limit": 100}

    try:
        response = await http_client.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return f"❌ 请求失败: {response.status_code}"

        data = response.json()
        results = data.get("results", [])
        messages += f"✅ 未来 {days} 天共有 {data.get('count', len(results))} 次发射计划：\n\n"

        tz_cn = zoneinfo.ZoneInfo("Asia/Shanghai")

        for launch in results:
            # 1. 提取名称与载荷
            full_name = launch.get("name", "")
            if " | " in full_name:
                rocket, payload = full_name.split(" | ", 1)
            else:
                rocket = (launch.get("rocket") or {}).get("configuration", {}).get("name", full_name)
                payload = "N/A"

            # 2. 提取核心信息
            pad = launch.get("pad") or {}
            location = pad.get("location") or {}
            site = location.get("name") or pad.get("name") or "Unknown"
            company = (launch.get("launch_service_provider") or {}).get("name", "Unknown")
            net_str = launch.get("net")

            # 3. 时间与倒计时计算
            if net_str:
                t_utc = datetime.fromisoformat(net_str.replace("Z", "+00:00"))
                t_cn = t_utc.astimezone(tz_cn)

                diff = t_utc - now
                if diff.total_seconds() < 0:
                    countdown = "🚀 已发射"
                else:
                    d, s = diff.days, diff.seconds
                    h, m, s = s // 3600, (s % 3600) // 60, s % 60
                    countdown = f"⏱️ {d}天 {h}时 {m}分 {s}秒"

                time_str = t_cn.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "待定"
                countdown = "未知"

            # 4. 打印输出
            messages += (
                f"🚀 火箭: {rocket}\n"
                f"🌍 发射场: {site}\n"
                f"⏰ 时间: {time_str}\n"
                f"⏱️ 倒计时: {countdown}\n"
                f"📦 载荷: {payload}\n"
                f"🏢 公司: {company}\n\n"
            )
        return messages
    except Exception as e:
        logger.error("Failed to fetch launch schedule: %s", e)
        return f"❌ 获取发射计划时发生错误： {e}。"
