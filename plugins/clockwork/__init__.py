import os

import dotenv
import httpx
from nonebot_plugin_alconna import Image, Target, Text, UniMessage
from nonebot_plugin_apscheduler import scheduler

dotenv.load_dotenv()


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


@scheduler.scheduled_job("cron", hour="18")
async def apod_everyday():
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": os.getenv("NASA_API_KEY", "DEMO_KEY"), "count": 1}
    response = httpx.get(url, params=params)
    title = response.json()["title"]
    image_url = response.json()["url"]
    message = UniMessage([Text(title), Image(url=image_url)])
    await message.send(target=Target.group(os.getenv("APOD_GROUP_ID", "")))
