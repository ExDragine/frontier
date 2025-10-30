import datetime
import zoneinfo

import httpx
from nonebot import logger, require

from tools import agent_tools
from utils.agents import cognitive
from utils.configs import EnvConfig
from utils.database import EventDatabase
from utils.markdown_render import markdown_to_image
from utils.render import playwright_render

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import Image, Target, Text, UniMessage  # noqa: E402
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

event_database = EventDatabase()
httpx_client = httpx.AsyncClient(http2=True)
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
    intro = f"NASA每日一图\n{content['title']}\n{content['explanation']}"
    slm_reply = await cognitive("翻译用户给出的天文相关的内容为中文，只返回翻译结果，保留专有词汇为英文", intro)
    messages: list[UniMessage] = [
        UniMessage(Text(slm_reply if slm_reply else intro)),
        UniMessage(Image(url=content["url"])),
    ]
    for message in messages:
        for group in EnvConfig.APOD_GROUP_ID:
            await message.send(target=Target.group(str(group)))


@scheduler.scheduled_job(trigger="cron", hour="8,12,18", minute="30", misfire_grace_time=180)
async def earth_now():
    url = "https://www.storm-chasers.cn/wp-content/uploads/satimgs/Composite_TVIS_FDLK.jpg"
    content = None
    for _i in range(3):
        try:
            response = await httpx_client.get(url)
            response.raise_for_status()
            content = response.content
            break
        except httpx.HTTPError as e:
            logger.warning(f"获取Earth Now图片失败: {e}", "准备重试...")
            continue
    if not content:
        return
    slm_reply = await cognitive(
        "你负责优化用户输入的内容，根据内容给出不超过15字的适用于社交聊天的优化后的内容",
        f"现在是{datetime.datetime.now().astimezone(zoneinfo.ZoneInfo('Asia/Shanghai')).hour}点半，来看看半个钟前的地球吧",
    )
    messages: list[UniMessage] = [
        UniMessage(
            Text(slm_reply if slm_reply else "来看看半个钟前的地球吧"),
        ),
        UniMessage(Image(raw=content)),
    ]
    for message in messages:
        for group in EnvConfig.EARTH_NOW_GROUP_ID:
            await message.send(target=Target.group(str(group)))


@scheduler.scheduled_job(trigger="interval", minutes=5, misfire_grace_time=60)
async def eq_usgs():
    USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"
    EVENT_NAME = "eq_usgs"
    new_id = await event_database.select(EVENT_NAME)
    response = await httpx_client.get(USGS_API_URL)
    content: dict = response.json()

    if not content or not content.get("features"):
        logger.info("USGS 没有新的地震")
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
        logger.info("USGS 没有新的地震")
        return
    logger.info(f"检测到{properties['place']}发生{properties['mag']}级地震")
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


@scheduler.scheduled_job("cron", hour="9,17", minute="18", misfire_grace_time=120)
async def daily_news():
    logger.info("开始获取每日新闻摘要")
    system_prompt = f"""
    Now is {datetime.datetime.now().astimezone(zoneinfo.ZoneInfo("Asia/Shanghai")).strftime("%Y年%m月%d日")}
    You are a news summary expert who collects the latest news from the internet,
    summarizes each piece into a concise summary of no more than 200 words, 
    ensuring it covers the main facts and key information. 
    The content should be output in a clean Markdown format.
    This content is for direct output, so do not add any irrelevant content outside of the main summary.
    Reply in Simplified Chinese.
    """
    user_prompt = f"请总结今天{'早上' if datetime.datetime.now().astimezone(zoneinfo.ZoneInfo('Asia/Shanghai')).hour < 12 else '下午'}的全球范围内15条主要新闻。"
    summary = await cognitive(system_prompt, user_prompt, use_model=EnvConfig.BASIC_MODEL, tools=tools)
    if summary:
        message = UniMessage().image(raw=await markdown_to_image(summary))
        for group in EnvConfig.NEWS_SUMMARY_GROUP_ID:
            await message.send(target=Target.group(str(group)))
