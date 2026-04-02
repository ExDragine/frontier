import zoneinfo
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from langchain.tools import tool

# 常量配置
TLP_LAUNCH_URL = "https://tlpnetwork.com/api/launches"

# 全局 HTTP 客户端复用
http_client = AsyncClient(timeout=30, http2=True)


# 火箭发射
@tool(response_format="content")
async def get_launches(days: int = 7):
    """获取未来指定天数内的火箭发射计划。
    Args:
        days (int): 未来天数，默认值为7天。
    Returns:
        str: 火箭发射计划的详细信息。"""
    messages = ""
    url = TLP_LAUNCH_URL

    now = datetime.now(UTC)

    # 构造查询参数 (注意：已移除 mode="list" 以便获取详细的国家和发射台信息)
    params = {"net__gte": now.isoformat(), "net__lt": (now + timedelta(days=days)).isoformat(), "ordering": "net"}

    try:
        response = await http_client.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return f"❌ 请求失败: {response.status_code}"

        data = response.json()
        results = data.get("results", [])
        messages += f"✅ 未来 {days} 天共有 {data['count']} 次发射计划：\n\n"

        tz_cn = zoneinfo.ZoneInfo("Asia/Shanghai")

        for launch in results:
            # 1. 提取名称与载荷
            full_name = launch.get("name", "")
            if " | " in full_name:
                rocket, payload = full_name.split(" | ", 1)
            else:
                rocket = launch.get("rocket", {}).get("configuration", {}).get("name", full_name)
                payload = "N/A"

            # 2. 提取核心信息
            country = launch.get("pad", {}).get("location", {}).get("country_code", "Unknown")
            company = launch.get("launch_service_provider", {}).get("name", "Unknown")
            net_str = launch.get("net")

            # 3. 时间与倒计时计算
            if net_str:
                t_utc = datetime.fromisoformat(net_str)
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
                f"🌍 国家: {country}\n"
                f"⏰ 时间: {time_str}\n"
                f"⏱️ 倒计时: {countdown}\n"
                f"📦 载荷: {payload}\n"
                f"🏢 公司: {company}\n\n"
            )
        return messages
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return f"❌ 获取发射计划时发生错误： {e}。"
