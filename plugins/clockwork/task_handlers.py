"""定时任务处理函数"""

import asyncio
import datetime
from io import BytesIO

from nonebot import get_bot, logger
from nonebot_plugin_alconna import Image, Target, Text, UniMessage
from PIL import Image as PILImage

from utils.agents import assistant_agent
from utils.configs import EnvConfig
from utils.database import EventDatabase
from utils.http_client import HTTPError, get_http_client
from utils.markdown_render import html_to_image, playwright_render
from utils.timeutil import SHANGHAI

from .task_models import TaskRunResult

# 共享的资源
event_database = EventDatabase()
httpx_client = get_http_client("task_handlers")


async def apod_everyday(**kwargs):
    """NASA每日一图 - 每天19:00推送"""
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": EnvConfig.NASA_API_KEY.get_secret_value()}
    response = await httpx_client.get(url, params=params)
    content = response.json()
    image = (await httpx_client.get(content["url"])).content
    intro = f"NASA每日一图\n{content['title']}\n{content['explanation']}"
    slm_reply = await assistant_agent("翻译用户给出的天文相关的内容为中文，只返回翻译结果，保留专有词汇为英文", intro)
    messages: list[UniMessage] = [
        UniMessage(Text(slm_reply or intro)),
        UniMessage(Image(raw=image)),
    ]
    for message in messages:
        for group in EnvConfig.APOD_GROUP_ID:
            await message.send(target=Target.group(str(group)))


async def earth_now(**kwargs):
    """实时地球图 - 每天8:30、12:30、18:30推送"""
    url = "https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG"
    content = None
    try:
        response = await httpx_client.get(url)
        response.raise_for_status()
        # 确保完整读取响应体
        content = await response.aread()
    except HTTPError as e:
        logger.warning(f"获取Earth Now图片失败: {e}", "准备重试...")
    if not content:
        return

    with PILImage.open(BytesIO(content)) as image:
        resized = image.resize(
            (max(1, image.width // 4), max(1, image.height // 4)),
            PILImage.Resampling.LANCZOS,
        ).convert("RGB")
        output = BytesIO()
        resized.save(output, format="JPEG", quality=90)
        content = output.getvalue()

    messages: list[UniMessage] = [
        UniMessage(
            Text("来看看半个钟前的地球吧"),
        ),
        UniMessage(Image(raw=content)),
    ]
    for message in messages:
        for group in EnvConfig.EARTH_NOW_GROUP_ID:
            await message.send(target=Target.group(str(group)))


async def eq_usgs(**kwargs):
    """美国地震速报 - 每5分钟检测"""
    USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"
    EVENT_NAME = "eq_usgs"
    new_id = await event_database.select(EVENT_NAME)
    response = await httpx_client.get(USGS_API_URL)
    content: dict = response.json()

    if not content or not content.get("features"):
        logger.debug("USGS API 返回空数据或缺少 features，跳过")
        return

    # 获取最新的地震数据
    data = content["features"][0]
    event_id = str(data["id"])
    properties = data["properties"]
    coordinates = data["geometry"]["coordinates"]

    # 检查是否是新地震且震级大于限制
    if new_id != event_id:
        if not await event_database.select(EVENT_NAME):
            await event_database.insert(EVENT_NAME, event_id)
        else:
            await event_database.update(EVENT_NAME, event_id)
    else:
        logger.debug(f"USGS 地震已处理过 (event_id={event_id})，跳过")
        return
    logger.debug(f"检测到{properties['place']}发生{properties['mag']}级地震")
    # 准备详细信息
    detail = [
        {
            "label": "⏱️发震时间",
            "value": datetime.datetime.fromtimestamp(properties["time"] / 1000)
            .astimezone(SHANGHAI)
            .strftime("%Y-%m-%d %H:%M:%S"),
        },
        {"label": "🗺️震中位置", "value": properties["place"]},
        {"label": "🌐纬度", "value": coordinates[1]},
        {"label": "🌐经度", "value": coordinates[0]},
    ]

    # 如果有海啸警报，添加警告信息
    if properties.get("tsunami") == 1:
        detail.append({"label": "🌊警告", "value": "可能发生海啸"})

    # 如果有烈度信息，添加烈度数据
    if properties.get("mmi"):
        detail.append({"label": "💢最大烈度", "value": f"{properties['mmi']}"})

    img = await playwright_render(
        EVENT_NAME,
        {
            "title": "USGS地震速报",
            "detail": detail,
            "latitude": coordinates[1],
            "longitude": coordinates[0],
            "magnitude": properties["mag"],
            "depth": coordinates[2],
        },
    )

    if img:
        message = UniMessage().image(raw=img)
        for group in EnvConfig.EARTHQUAKE_GROUP_ID:
            await message.send(target=Target.group(str(group)))


async def daily_news(**kwargs):
    """Compatibility wrapper for databases that still reference the legacy handler."""
    from plugins.news.scheduler import daily_news as run_news
    return await run_news(**kwargs)


async def happy_new_year(**kwargs):
    """新年贺词 - 2026年2月16日23:59:59发送"""
    message = UniMessage().text("新年快乐！祝大家在新的一年里身体健康，万事如意！🎉🎊")
    milky_bot = get_bot()
    group_list = await milky_bot.get_group_list()
    for group in group_list:
        await message.send(target=Target.group(str(group.group_id)))


async def _send_merchant_alert(image: bytes, hit_names: str) -> list[int]:
    groups_sent: list[int] = []
    for group in EnvConfig.NRC_MERCHANT_GROUP_ID:
        try:
            if hit_names:
                await UniMessage.text(f"⚠️ 远行商人上架提醒：{hit_names} 已上架！").send(
                    target=Target.group(str(group))
                )
            await UniMessage.image(raw=image).send(target=Target.group(str(group)))
            groups_sent.append(int(group))
        except Exception as e:
            logger.error(f"NRC 商人提醒推送到群 {group} 失败: {e}")

    return groups_sent


def _merchant_period_end(now: datetime.datetime) -> datetime.datetime | None:
    for hour in (8, 12, 16, 20):
        if hour <= now.hour < hour + 4:
            start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            return start + datetime.timedelta(hours=4)
    return None


async def nrc_merchant_alert(**kwargs):
    """远行商人商品提醒推送 - 每天8:10、12:10、16:10、20:10触发首次访问。

    每个时段（4小时）内若两个 API 均返回无效商品数据，每30分钟重试直至时段结束。
    首次判定双 API 均无效时向配置群发送失联提示，后续重试失败静默。
    """
    from tools.NRCmerchant_current import (
        ALERT_TARGET_ITEMS,
        _load_css,
        _render_html,
        fetch_merchant_data_with_fallback,
    )

    now = datetime.datetime.now(SHANGHAI)

    period_end = _merchant_period_end(now)
    if period_end is None:
        logger.debug(f"NRC 商人提醒：当前时间 {now.strftime('%H:%M')} 不在任何推送时段内")
        return None

    first_failure_notified = False

    while True:
        now = datetime.datetime.now(SHANGHAI)
        if now >= period_end:
            logger.debug(f"NRC 商人提醒：已超出时段 {period_end.strftime('%H:%M')}，停止重试")
            break

        data, source = await fetch_merchant_data_with_fallback()

        if data and data.get("items"):
            items = data.get("items", [])
            hits = [item for item in items if item.get("name") in ALERT_TARGET_ITEMS]
            hit_names = "、".join(item["name"] for item in hits) if hits else ""

            html = _render_html(data)
            css = _load_css()
            image = await html_to_image(html, css=css, width=480)

            groups_sent = await _send_merchant_alert(image, hit_names)

            msg_count = len(groups_sent) * (2 if hits else 1)
            return TaskRunResult(
                groups_sent=groups_sent,
                messages_sent=msg_count,
                output_summary=f"nrc_merchant_alert [{source}] → {hit_names or '无目标'} ({groups_sent})",
            )

        # 双 API 均无效
        if not first_failure_notified:
            first_failure_notified = True
            for group in EnvConfig.NRC_MERCHANT_GROUP_ID:
                try:
                    await UniMessage.text("😭当前已和远行商人失去链接").send(target=Target.group(str(group)))
                except Exception as e:
                    logger.error(f"NRC 商人失联消息推送到群 {group} 失败: {e}")

        next_retry = datetime.datetime.now(SHANGHAI) + datetime.timedelta(minutes=30)
        if next_retry >= period_end:
            logger.debug(
                f"NRC 商人提醒：下次重试 {next_retry.strftime('%H:%M')} 超出时段 {period_end.strftime('%H:%M')}，停止"
            )
            break

        logger.info(
            f"NRC 商人提醒：30分钟后重试 "
            f"(当前 {datetime.datetime.now(SHANGHAI).strftime('%H:%M:%S')}, 时段结束 {period_end.strftime('%H:%M')})"
        )
        await asyncio.sleep(30 * 60)
