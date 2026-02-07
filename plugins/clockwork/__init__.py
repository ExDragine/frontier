import datetime
import zoneinfo

import httpx
from nonebot import logger, require

from tools import agent_tools
from utils.agents import assistant_agent
from utils.configs import EnvConfig
from utils.database import EventDatabase
from utils.markdown_render import markdown_to_image
from utils.render import playwright_render

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import Image, Target, Text, UniMessage  # noqa: E402
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

event_database = EventDatabase()
transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)
tools = agent_tools.mcp_tools + agent_tools.web_tools


async def github_post_news():
    GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
    query = """
    query {
        repository(owner:"UnrealUpdateTracker", name:"UnrealEngine") {
            discussions(first: 5) {
                node {
                    title
                    createdAt
                    body
                }
            }
        }
    }
    """
    response = await httpx_client.post(
        GITHUB_GRAPHQL_URL,
        headers={"Authorization": f"Bearer {EnvConfig.GITHUB_PAT.get_secret_value()}"},
        json={"query": query},
    )
    print(response.json())


@scheduler.scheduled_job("cron", hour="19", misfire_grace_time=60)
async def apod_everyday():
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": EnvConfig.NASA_API_KEY.get_secret_value()}
    response = await httpx_client.get(url, params=params)
    content = response.json()
    image = (await httpx_client.get(content["url"])).content
    intro = f"NASA每日一图\n{content['title']}\n{content['explanation']}"
    slm_reply = await assistant_agent("翻译用户给出的天文相关的内容为中文，只返回翻译结果，保留专有词汇为英文", intro)
    messages: list[UniMessage] = [
        UniMessage(Text(slm_reply if slm_reply else intro)),
        UniMessage(Image(raw=image)),
    ]
    for message in messages:
        for group in EnvConfig.APOD_GROUP_ID:
            await message.send(target=Target.group(str(group)))


@scheduler.scheduled_job(trigger="cron", hour="8,12,18", minute="30", misfire_grace_time=180)
async def earth_now():
    url = "https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG"
    content = None
    try:
        response = await httpx_client.get(url)
        response.raise_for_status()
        # 确保完整读取响应体
        content = await response.aread()
    except httpx.HTTPError as e:
        logger.warning(f"获取Earth Now图片失败: {e}", "准备重试...")
    if not content:
        return
    messages: list[UniMessage] = [
        UniMessage(
            Text("来看看半个钟前的地球吧"),
        ),
        UniMessage(Image(raw=content)),
    ]
    for message in messages:
        for group in EnvConfig.EARTH_NOW_GROUP_ID:
            await message.send(target=Target.group(str(group)))


@scheduler.scheduled_job(trigger="interval", minutes=1, misfire_grace_time=30)
async def eq_cenc():
    URL = "https://api.wolfx.jp/cenc_eew.json"
    EVENT_NAME = "eq_cenc"
    new_id = await event_database.select(EVENT_NAME)
    response = await httpx_client.get(URL)
    content: dict = response.json()

    if not content:
        logger.debug("CENC 没有新的地震")
        return None

    # 获取最新的地震数据
    data = content
    event_id = str(data["ID"])

    # 检查是否是新地震且震级大于限制
    if new_id != event_id:
        if not await event_database.select(EVENT_NAME):
            await event_database.insert(EVENT_NAME, event_id)
        else:
            await event_database.update(EVENT_NAME, event_id)
    else:
        logger.debug("CENC 没有新的地震")
        return
    logger.info(f"检测到{data['HypoCenter']}发生{data['Magnitude']}级地震")
    if int(data["Magnitude"]) < 3:
        logger.debug("震级低于3级，忽略此次地震")
        return
    # 准备详细信息
    detail = [
        {"label": "⏱️发震时间", "value": data["OriginTime"]},
        {"label": "🗺️震中位置", "value": data["HypoCenter"]},
        {"label": "🌐纬度", "value": data["Latitude"]},
        {"label": "🌐经度", "value": data["Longitude"]},
    ]
    # 如果有烈度信息，添加烈度数据
    if data.get("MaxIntensity"):
        detail.append({"label": "💢最大烈度", "value": f"{data['MaxIntensity']}"})

    img = await playwright_render(
        EVENT_NAME,
        {
            "title": "CENC地震速报",
            "detail": detail,
            "latitude": data["Latitude"],
            "longitude": data["Longitude"],
            "magnitude": data["Magnitude"],
            "depth": data["Depth"],
        },
    )

    if img:
        message = UniMessage().image(raw=img)
        for group in EnvConfig.EARTHQUAKE_GROUP_ID:
            await message.send(target=Target.group(str(group)))


@scheduler.scheduled_job(trigger="interval", minutes=5, misfire_grace_time=60)
async def eq_usgs():
    USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"
    EVENT_NAME = "eq_usgs"
    new_id = await event_database.select(EVENT_NAME)
    response = await httpx_client.get(USGS_API_URL)
    content: dict = response.json()

    if not content or not content.get("features"):
        logger.debug("USGS 没有新的地震")
        return None

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
        logger.debug("USGS 没有新的地震")
        return
    logger.debug(f"检测到{properties['place']}发生{properties['mag']}级地震")
    # 准备详细信息
    detail = [
        {
            "label": "⏱️发震时间",
            "value": datetime.datetime.fromtimestamp(properties["time"] / 1000)
            .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
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


@scheduler.scheduled_job("cron", hour="9,18", minute="30", misfire_grace_time=120)
async def daily_news():
    logger.info("开始获取每日新闻摘要")
    today = datetime.datetime.now().astimezone(zoneinfo.ZoneInfo("Asia/Shanghai")).strftime("%Y年%m月%d日")
    with open("prompts/daily_news.txt", encoding="utf-8") as f:
        system_prompt = f.read().format(current_time=today)
    user_prompt = f"请总结今天{'早上' if datetime.datetime.now().astimezone(zoneinfo.ZoneInfo('Asia/Shanghai')).hour < 12 else '下午'}的主要新闻。"
    summary = await assistant_agent(system_prompt, user_prompt, use_model=EnvConfig.ADVAN_MODEL, tools=tools)
    if summary:
        message = UniMessage().image(raw=await markdown_to_image(summary))
        for group in EnvConfig.NEWS_SUMMARY_GROUP_ID:
            await message.send(target=Target.group(str(group)))
