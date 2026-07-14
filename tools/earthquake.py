from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from utils.http_client import get_http_client

CENC_EARTHQUAKE_CATALOG_URL = "https://www.cenc.ac.cn/prodlaunch-web-backend/open/data/catalogs"
USGS_SIGNIFICANT_MONTH_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")
httpx_client = get_http_client("earthquake")


@tool(response_format="content")
async def get_china_earthquake() -> str:
    """获取中国地震台网最近 7 条地震信息。

    Returns:
        str: 纯文本地震信息
    """
    today = datetime.now(CHINA_TIMEZONE).date()
    response = await httpx_client.get(
        CENC_EARTHQUAKE_CATALOG_URL,
        params={
            "orderBy": "id",
            "isAsc": "false",
            "startMg": 3,
            "endMg": 10,
            "startTime": f"{today - timedelta(days=30):%Y-%m-%d} 00:00:00",
            "endTime": f"{today:%Y-%m-%d} 23:59:59",
            "locationRange": 1,
        },
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        return "中国地震台网返回了无法识别的数据。"
    if data.get("code") != 0:
        return f"中国地震台网查询失败：{data.get('message') or '未知错误'}"
    if not isinstance(data.get("data"), list):
        return "中国地震台网返回了无法识别的数据。"

    events = [event for event in data["data"] if isinstance(event, dict)][:7]
    if not events:
        return "暂未获取到中国地震台网地震信息。"

    lines = [f"中国地震台网最近地震信息（{len(events)} 条）："]
    for index, event in enumerate(events, start=1):
        time = event.get("oriTime") or "时间未知"
        location = event.get("locName") or "地点未知"
        magnitude = event.get("magnitude") or "未知"
        magnitude_text = f"{magnitude:.1f}" if isinstance(magnitude, int | float) else magnitude
        depth = event.get("focDepth")
        if isinstance(depth, int | float):
            depth_text = f"深度 {depth:g} 千米"
        elif depth:
            depth_text = f"深度 {depth} 千米"
        else:
            depth_text = "深度未知"
        lines.append(f"{index}. {time}｜{location}｜M{magnitude_text}｜{depth_text}")

    return "\n".join(lines)


@tool(response_format="content")
async def get_usgs_significant_earthquakes() -> str:
    """获取全球过去一个月内的全部重大地震信息。

    Returns:
        str: 按发生时间倒序排列的纯文本地震信息
    """
    response = await httpx_client.get(USGS_SIGNIFICANT_MONTH_URL)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("features"), list):
        return "USGS 返回了无法识别的数据。"

    events = [feature for feature in data["features"] if isinstance(feature, dict)]
    events.sort(
        key=lambda feature: (
            feature.get("properties", {}).get("time", 0) if isinstance(feature.get("properties"), dict) else 0
        ),
        reverse=True,
    )
    if not events:
        return "USGS 过去一个月内暂无重大地震。"

    alert_labels = {
        "green": "绿色",
        "yellow": "黄色",
        "orange": "橙色",
        "red": "红色",
    }
    lines = [f"USGS 过去一个月重大地震（{len(events)} 条，时间均为北京时间）："]
    for index, event in enumerate(events, start=1):
        properties = event.get("properties")
        properties = properties if isinstance(properties, dict) else {}
        geometry = event.get("geometry")
        geometry = geometry if isinstance(geometry, dict) else {}
        coordinates = geometry.get("coordinates")

        event_time = properties.get("time")
        if isinstance(event_time, int | float):
            time_text = (
                datetime.fromtimestamp(event_time / 1000, tz=UTC)
                .astimezone(CHINA_TIMEZONE)
                .strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            time_text = "时间未知"

        magnitude = properties.get("mag")
        magnitude_text = f"{magnitude:.1f}" if isinstance(magnitude, int | float) else "未知"
        place = properties.get("place") or "地点未知"
        depth = coordinates[2] if isinstance(coordinates, list | tuple) and len(coordinates) >= 3 else None
        depth_text = f"深度 {depth:g} 千米" if isinstance(depth, int | float) else "深度未知"
        significance = properties.get("sig")
        significance_text = f"显著性 {significance}" if isinstance(significance, int | float) else "显著性未知"
        alert = alert_labels.get(properties.get("alert"), "未发布")
        tsunami = "有" if properties.get("tsunami") == 1 else "无"
        lines.append(
            f"{index}. {time_text}｜{place}｜M{magnitude_text}｜{depth_text}｜"
            f"{significance_text}｜PAGER {alert}｜海啸标记：{tsunami}"
        )

    return "\n".join(lines)
