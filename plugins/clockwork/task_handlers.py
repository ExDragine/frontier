"""定时任务处理函数"""

import datetime
import inspect
import json
import traceback
import zoneinfo
from dataclasses import dataclass
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader
from nonebot import get_bot, logger
from nonebot_plugin_alconna import Image, Target, Text, UniMessage
from pydantic import BaseModel, Field

from tools import agent_tools
from utils.agents import assistant_agent
from utils.configs import EnvConfig
from utils.database import EventDatabase
from utils.render import html_to_image, playwright_render

from .task_models import TaskRunResult

# 共享的资源
event_database = EventDatabase()
transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)
tools = agent_tools.mcp_tools + agent_tools.web_tools
PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
DAILY_NEWS_SEARCH_TOOL_NAMES = {"tavily_search", "web_search_exa"}

NEWS_HISTORY_KEY = "daily_news_recent_titles"


async def _load_recent_titles() -> list[str]:
    """读取最近一次推送中报道过的新闻标题，用于去重。"""
    data = await event_database.select(NEWS_HISTORY_KEY)
    if not data:
        return []
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return []


async def _save_recent_titles(titles: list[str]) -> None:
    """保存本次推送的新闻标题，供下次去重使用。"""
    data = json.dumps(titles, ensure_ascii=False)
    try:
        await event_database.insert(NEWS_HISTORY_KEY, data)
    except Exception:
        await event_database.update(NEWS_HISTORY_KEY, data)


class TopStory(BaseModel):
    title: str = Field(description="新闻标题")
    summary: str = Field(description="不超过130个中文字符，包含关键背景、进展和结果")
    impact: str = Field(description="一句话说明影响或后续观察点，不超过60个中文字符")
    sources: list[str] = Field(description="来源名称列表")


class WorthReadingStory(BaseModel):
    category: str = Field(description="短分类标签，如 科技/经济/国际")
    title: str = Field(description="新闻标题")
    summary: str = Field(description="不超过110个中文字符，包含具体进展、背景和影响")
    sources: list[str] = Field(description="来源名称列表")


class DailyNewsPayload(BaseModel):
    top_stories: list[TopStory] = Field(description="今日要闻，4-6条")
    worth_reading: list[WorthReadingStory] = Field(description="值得一看，10-12条")


@dataclass
class DailyNewsArtifacts:
    today: str
    period: str
    report_time: str
    material: str
    payload: DailyNewsPayload
    html: str


def load_daily_news_css() -> str:
    return (TEMPLATES_DIR / "daily_news.css").read_text(encoding="utf-8")


def _daily_news_tools(available_tools=None) -> list:
    available_tools = list(tools if available_tools is None else available_tools)
    search_tools = [tool for tool in available_tools if getattr(tool, "name", "") in DAILY_NEWS_SEARCH_TOOL_NAMES]
    return search_tools or available_tools


def _source_text(value) -> str:
    if isinstance(value, list):
        return "、".join(str(source).strip() for source in value if str(source).strip())
    if value is None:
        return ""
    return str(value).strip()


def _normalise_news_items(items, *, include_category: bool = False) -> list[dict]:
    if not isinstance(items, list):
        return []

    normalised = []
    for item in items:
        if isinstance(item, BaseModel):
            item = item.model_dump()
        if not isinstance(item, dict):
            continue
        news_item = {
            "title": str(item.get("title", "")).strip(),
            "summary": str(item.get("summary", "")).strip(),
            "impact": str(item.get("impact", "")).strip(),
            "source_text": _source_text(item.get("sources")),
        }
        if include_category:
            news_item["category"] = str(item.get("category", "")).strip()
        normalised.append(news_item)
    return normalised


def render_daily_news_html(payload: dict | BaseModel, *, current_time: str, period: str, report_time: str) -> str:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("daily_news.html")
    return template.render(
        current_time=current_time,
        period=period,
        report_time=report_time,
        top_stories=_normalise_news_items(payload.get("top_stories")),
        worth_reading=_normalise_news_items(payload.get("worth_reading"), include_category=True),
    )


def daily_news_format_prompt(today: str, period: str, report_time: str) -> str:
    return f"""你是新闻简报格式化编辑。请只根据用户提供的纯文本素材包，整理成严格 JSON。

要求：
1. 输出必须符合 DailyNewsPayload schema，不要输出 Markdown、HTML 或解释文字。
2. 今日要闻选 4-6 条；值得一看选 10-12 条。
3. 摘要使用简体中文，保持客观、具体，不添加素材包之外的新事实。
4. sources 只放来源名称，不要放 URL。
5. 如果素材不足，可以保留较少条目，但不要编造。

简报日期：{today}
简报类型：{period}
生成时间：北京时间 {report_time}
"""


def daily_news_context(now_cn: datetime.datetime | None = None) -> tuple[datetime.datetime, str, str, str]:
    now_cn = (now_cn or datetime.datetime.now()).astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
    today = now_cn.strftime("%Y年%m月%d日")
    period = "早报" if now_cn.hour < 18 else "晚报"
    report_time = now_cn.strftime("%H:%M")
    return now_cn, today, period, report_time


def daily_news_research_prompts(
    today: str, period: str, report_time: str, recent_titles: list[str] | None = None
) -> tuple[str, str]:
    with open(PROMPTS_DIR / "daily_news.md", encoding="utf-8") as f:
        system_prompt = f.read().format(current_time=today)

    user_prompt = (
        f"请生成{today}全球与中国主要新闻{period}。"
        f"当前北京时间为{report_time}。"
        "请主动搜索最近24小时内的重要新闻，不需要再另行询问。"
    )

    if recent_titles:
        titles_text = "\n".join(f"  - {t}" for t in recent_titles)
        user_prompt += (
            f"\n\n⚠️ 以下是上一次推送中已经报道过的新闻标题，"
            f"请务必避免重复报道相同事件，优先搜索其他重要新闻：\n{titles_text}"
        )

    return system_prompt, user_prompt


async def build_daily_news_artifacts(
    now_cn: datetime.datetime | None = None, recent_titles: list[str] | None = None
) -> DailyNewsArtifacts | None:
    """构建日报素材包、结构化数据和 HTML；不发送消息。"""
    _now_cn, today, period, report_time = daily_news_context(now_cn)
    system_prompt, user_prompt = daily_news_research_prompts(
        today, period, report_time, recent_titles
    )

    material = await assistant_agent(
        system_prompt,
        user_prompt,
        use_model=EnvConfig.ADVAN_MODEL,
        tools=_daily_news_tools(),
    )
    if not material:
        logger.warning("每日新闻素材包为空，跳过推送")
        return None

    payload = await assistant_agent(
        daily_news_format_prompt(today, period, report_time),
        f"请把下面的新闻素材包整理成严格 JSON：\n\n{material}",
        use_model=EnvConfig.SIGNAL_MODEL,
        tools=None,
        response_format=DailyNewsPayload,
        temperature=0,
        model_kwargs={
            "response_format": {"type": "json_object"},
            "max_tokens": 8192,
        },
    )
    if not payload:
        return None

    html = render_daily_news_html(
        payload,
        current_time=today,
        period=period,
        report_time=report_time,
    )
    return DailyNewsArtifacts(
        today=today,
        period=period,
        report_time=report_time,
        material=material,
        payload=payload,
        html=html,
    )


async def aclose_http_client() -> None:
    await httpx_client.aclose()


async def github_post_news(**kwargs):
    """GitHub 新闻推送（未启用）"""
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
    logger.debug("GitHub GraphQL response: %s", response.text)


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
        UniMessage(Text(slm_reply if slm_reply else intro)),
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


async def eq_cenc(**kwargs):
    """中国地震速报 - 每分钟检测"""
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


async def eq_usgs(**kwargs):
    """美国地震速报 - 每5分钟检测"""
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


async def daily_news(**kwargs):  # noqa: C901
    """每日新闻摘要 - 每天9:00、21:00推送"""
    logger.info("开始获取每日新闻摘要")

    recent_titles = await _load_recent_titles()
    if "recent_titles" in inspect.signature(build_daily_news_artifacts).parameters:
        artifacts = await build_daily_news_artifacts(recent_titles=recent_titles)
    else:
        artifacts = await build_daily_news_artifacts()
    if not artifacts:
        return

    image = await html_to_image(artifacts.html, css=load_daily_news_css())
    message = UniMessage().image(raw=image)
    groups_sent: list[int] = []
    send_errors: list[Exception] = []
    for group in EnvConfig.NEWS_SUMMARY_GROUP_ID:
        try:
            await message.send(target=Target.group(str(group)))
            groups_sent.append(int(group))
        except Exception as e:
            send_errors.append(e)
            error_traceback = "".join(traceback.format_exception(e))
            logger.error(f"每日新闻推送到群 {group} 失败:\n{error_traceback}")

    if send_errors and not groups_sent:
        raise send_errors[0]

    # 保存本次推送的标题，供下次去重使用
    payload = artifacts.payload
    if isinstance(payload, BaseModel):
        payload = payload.model_dump()
    all_titles: list[str] = []
    for story in payload.get("top_stories", []):
        if title := story.get("title", "").strip():
            all_titles.append(title)
    for story in payload.get("worth_reading", []):
        if title := story.get("title", "").strip():
            all_titles.append(title)
    if all_titles:
        await _save_recent_titles(all_titles)

    return TaskRunResult(
        groups_sent=groups_sent,
        messages_sent=len(groups_sent),
        output_summary=f"daily_news sent {len(groups_sent)} group(s)",
    )


async def happy_new_year(**kwargs):
    """新年贺词 - 2026年2月16日23:59:59发送"""
    message = UniMessage().text("新年快乐！祝大家在新的一年里身体健康，万事如意！🎉🎊")
    milky_bot = get_bot()
    group_list = await milky_bot.get_group_list()
    for group in group_list:
        await message.send(target=Target.group(str(group.group_id)))
