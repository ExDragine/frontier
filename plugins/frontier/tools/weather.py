from functools import lru_cache

from httpx import AsyncClient, Client
from langchain.tools import tool
from nonebot import logger
from pypinyin import lazy_pinyin

http_client = Client(timeout=30)
async_http_client = AsyncClient(timeout=30, http2=True)

NASA_WEATHER_URL = "https://mars.nasa.gov/rss/api/?feed=weather&category=msl&feedtype=json"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search?format=json"
OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@lru_cache(maxsize=32)
def geocode(city_name: str) -> tuple[float, float]:
    """返回 (latitude, longitude)，未找到抛出 ValueError"""
    name_py = "".join(lazy_pinyin(city_name))
    resp = http_client.get(f"{GEOCODE_URL}?name={name_py}&count=1&language=en")
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results")
    if not results:
        raise ValueError(f"未找到城市: {city_name}")
    loc = results[0]
    return loc["latitude"], loc["longitude"]


# 通用 JSON 获取
async def fetch_json(url: str, client: AsyncClient, **kwargs) -> dict:
    resp = await client.get(url, **kwargs)
    resp.raise_for_status()
    return resp.json()


# 天气与天文工具封装
class WeatherTool:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def current(self, city: str) -> str:
        try:
            lat, lon = geocode(city)
            url = f"{OPEN_METEO_WEATHER_URL}?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            data = await fetch_json(url, self.client)
            cw = data["current_weather"]
            return f"🌤 {city} {cw['temperature']}℃ 风速{cw['windspeed']}m/s"
        except Exception as e:
            logger.error("Weather error", exc_info=e)
            return f"❌ 获取天气失败: {e}"

    async def forecast(self, city: str, days: int) -> str:
        try:
            lat, lon = geocode(city)
            url = f"{OPEN_METEO_WEATHER_URL}?latitude={lat}&longitude={lon}&forecast_days={days}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            data = await fetch_json(url, self.client)
            daily = data["daily"]
            lines = [
                f"第{i + 1}天: 高{daily['temperature_2m_max'][i]}℃ 低{daily['temperature_2m_min'][i]}℃"
                for i in range(days)
            ]
            return "\n".join(lines)
        except Exception as e:
            logger.error("Forecast error", exc_info=e)
            return f"❌ 获取预报失败: {e}"


weather_tool = WeatherTool(async_http_client)


@tool(response_format="content")
async def get_current_weather(city_name: str) -> str:
    """
    获取城市天气
    Args:
        city_name: 城市名称
    Returns:
        城市天气
    """
    return await weather_tool.current(city_name)


@tool(response_format="content")
async def get_future_weather(city_name: str, days: int) -> str:
    """
    获取城市未来天气
    Args:
        city_name: 城市名称
        days: 未来天数
    Returns:
        未来天气
    """
    return await weather_tool.forecast(city_name, days)


# 火星天气
@tool(response_format="content")
async def mars_weather() -> str:
    """
    获取火星天气
    Returns:
        火星天气
    """
    try:
        resp = http_client.get(NASA_WEATHER_URL)
        resp.raise_for_status()
        data = resp.json()
        return f"火星天气: {data['descriptions']}"
    except Exception as e:
        logger.error("Mars weather error", exc_info=e)
        return f"❌ 火星天气失败: {e}"
