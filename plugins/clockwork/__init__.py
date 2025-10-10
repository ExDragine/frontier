import os

import dotenv
import httpx
from nonebot import require

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


@scheduler.scheduled_job("cron", hour="19")
async def apod_everyday():
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": os.getenv("NASA_API_KEY", "DEMO_KEY")}
    response = httpx.get(url, params=params).json()
    title = f"【NASA Astronomy Picture of the Day】\n{response['title']}\n{response['explanation']}"
    image_url = response["url"]
    message = UniMessage([Text(title), Image(url=image_url)])
    await message.send(target=Target.group(os.getenv("APOD_GROUP_ID", "")))


@scheduler.scheduled_job(trigger="cron", hour="8,12,18", minute="30")
async def earth_now():
    URL = "https://www.storm-chasers.cn/wp-content/uploads/satimgs/Composite_TVIS_FDLK.jpg"
    message = UniMessage([Text("半个钟之前的地球"), Image(url=URL)])
    await message.send(target=Target.group(os.getenv("EARTH_NOW_GROUP_ID", "")))
