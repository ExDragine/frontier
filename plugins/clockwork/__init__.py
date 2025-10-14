import os

import dotenv
import httpx
from nonebot import require

from plugins.frontier.slm import slm_cognitive

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
dotenv.load_dotenv()
from nonebot_plugin_alconna import Image, Target, Text, UniMessage  # noqa: E402
from nonebot_plugin_apscheduler import scheduler  # noqa: E402


async def github_post_news():
    GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
    GITHUB_PAT = os.getenv("GITHUB_PAT")
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
    response = httpx.post(GITHUB_GRAPHQL_URL, headers={"Authorization": f"Bearer {GITHUB_PAT}"}, json={"query": query})
    print(response.json())


@scheduler.scheduled_job("cron", hour="19", misfire_grace_time=60)
async def apod_everyday():
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": os.getenv("NASA_API_KEY", "DEMO_KEY")}
    response = httpx.get(url, params=params).json()
    intro = f"NASA每日一图\n{response['title']}\n{response['explanation']}"
    slm_reply = await slm_cognitive("翻译用户给出的天文相关的内容为中文，只返回翻译结果，保留专有词汇为英文", intro)
    messages: list[UniMessage] = [
        UniMessage(Text(slm_reply if slm_reply else intro)),
        UniMessage(Image(url=response["url"])),
    ]
    for message in messages:
        await message.send(target=Target.group(os.getenv("APOD_GROUP_ID", "")))


@scheduler.scheduled_job(trigger="cron", hour="8,12,18", minute="30", misfire_grace_time=180)
async def earth_now():
    url = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/1808x1808.jpg"
    slm_reply = await slm_cognitive("根据内容给出不超过15字的适用于社交聊天的优化后的内容", "来看看半个钟前的地球吧")
    messages: list[UniMessage] = [
        UniMessage(
            Text(slm_reply if slm_reply else "来看看半个钟前的地球吧"),
        ),
        UniMessage(Image(url=url)),
    ]
    for message in messages:
        await message.send(target=Target.group(os.getenv("EARTH_NOW_GROUP_ID", "")))
