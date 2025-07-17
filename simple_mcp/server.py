import ast
import datetime
import hashlib
import logging
import operator as op
import platform
from functools import lru_cache

from httpx import AsyncClient, Client
from mcp.server.fastmcp import FastMCP
from pypinyin import lazy_pinyin

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量配置
NASA_WEATHER_URL = "https://mars.nasa.gov/rss/api/?feed=weather&category=msl&feedtype=json"
TLP_LAUNCH_URL = "https://tlpnetwork.com/api/launches"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search?format=json"
OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# 全局 HTTP 客户端复用
http_client = Client(timeout=30)
async_http_client = AsyncClient(timeout=30)

# 安全计算表达式
OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def safe_eval(expr: str) -> float:
    """使用 AST 安全解析数学表达式，仅支持+ - * / ** 和负号"""
    node = ast.parse(expr, mode="eval").body

    def _eval(n):
        # Python 3.8+: ast.Constant, Python <3.8: ast.Num
        if isinstance(n, ast.Constant):
            if isinstance(n.value, int | float):
                return n.value
            else:
                raise ValueError(f"Unsupported constant: {n.value}")
        if isinstance(n, ast.Constant):
            return n.n
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp):
            return OPS[type(n.op)](_eval(n.operand))
        raise ValueError(f"Unsupported expression: {n}")

    result = _eval(node)
    if not isinstance(result, int | float):
        raise ValueError(f"Expression did not evaluate to a number: {result!r}")
    return float(result)


# 地理编码缓存
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


# 实例化 MCP
mcp = FastMCP(name="simple_mcp", dependencies=["langchain_core.messages"])


@mcp.tool()
def simple_calculator(expression: str) -> str:
    """执行简单的数学运算"""
    try:
        result = safe_eval(expression)
        return f"🧮 计算结果: {expression} = {result}"
    except Exception as e:
        logger.error("Calc error", exc_info=e)
        return f"❌ 计算失败: {e}"


@mcp.tool()
def text_count(text: str) -> str:
    """统计字符、单词和行数"""
    char_count = len(text)
    word_count = len(text.split())
    line_count = text.count("\n") + 1
    return f"📊 字符: {char_count}，单词: {word_count}，行: {line_count}"


@mcp.tool()
def calculate_hash(text: str, algorithm: str = "sha256") -> str:
    """支持 md5、sha1、sha256"""
    alg = algorithm.lower()
    try:
        hash_obj = getattr(hashlib, alg)()
    except AttributeError:
        return f"❌ 不支持算法: {algorithm}"
    hash_obj.update(text.encode("utf-8"))
    return f"🔐 {alg.upper()} 哈希: {hash_obj.hexdigest()}"


@mcp.tool()
def string_operations(text: str, operation: str, **kwargs) -> str:
    """字符串操作: upper/lower/title/reverse/replace"""
    try:
        if operation == "replace":
            old = kwargs.get("old")
            new = kwargs.get("new")
            if not old:
                return "❌ replace 需要 old"
            if new is None:
                return "❌ replace 需要 new"
            res = text.replace(old, new)
        else:
            res = getattr(text, operation)()  # upper, lower, title
        return f"✨ 操作 {operation}: {res}"
    except Exception as e:
        logger.error("String op error", exc_info=e)
        return f"❌ 操作失败: {e}"


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


@mcp.tool()
async def weather(city_name: str) -> str:
    return await weather_tool.current(city_name)


@mcp.tool()
async def get_future_weather(city_name: str, days: int) -> str:
    return await weather_tool.forecast(city_name, days)


# 火星天气
@mcp.tool()
def mars_weather() -> str:
    try:
        resp = http_client.get(NASA_WEATHER_URL)
        resp.raise_for_status()
        data = resp.json()
        return f"火星天气: {data['descriptions']}"
    except Exception as e:
        logger.error("Mars weather error", exc_info=e)
        return f"❌ 火星天气失败: {e}"


# 火箭发射
@mcp.tool()
async def rocket_launches(days: int = 3) -> str:
    if not 1 <= days <= 7:
        return "❌ 天数1-7"
    try:
        now = datetime.datetime.now(datetime.UTC)
        end = now + datetime.timedelta(days=days)
        payload = {"net": {"gte": now.isoformat(), "lte": end.isoformat()}}
        resp = await async_http_client.post(TLP_LAUNCH_URL, json=payload)
        resp.raise_for_status()
        missions = resp.json()
        if not missions:
            return f"🚀 未来{days}天无发射"
        lines = [f"{m['name']} @ {m['net']}" for m in missions]
        return "\n".join(lines)
    except Exception as e:
        logger.error("Rocket error", exc_info=e)
        return f"❌ 火箭信息失败: {e}"


# 彗星工具
class CometTool:
    BASE = "https://cobs.si/api"

    def __init__(self, client: Client):
        self.client = client

    def info(self, name: str) -> str:
        try:
            resp = self.client.get(f"{self.BASE}/comet.api", params={"des": name})
            data = resp.json()
            obj = data["object"]
            return f"彗星 {obj['fullname']} 亮度 {obj['current_mag']}"
        except Exception as e:
            logger.error("Comet info error", exc_info=e)
            return f"❌ 彗星信息失败: {e}"

    def list(self, max_mag: int = 15) -> str:
        try:
            resp = self.client.get(f"{self.BASE}/comet_list.api", params={"cur-mag": max_mag})
            objs = resp.json().get("objects", [])
            return "\n".join(o["fullname"] for o in objs)
        except Exception as e:
            logger.error("Comet list error", exc_info=e)
            return f"❌ 彗星列表失败: {e}"


comet_tool = CometTool(http_client)


@mcp.tool()
def comet_information(name: str) -> str:
    return comet_tool.info(name)


@mcp.tool()
def comet_list(cur_mag: int = 15) -> str:
    return comet_tool.list(cur_mag)


# 系统信息
@mcp.resource("system://info")
def system_info() -> str:
    info = {
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "Arch": platform.machine(),
    }
    return "\n".join(f"{k}: {v}" for k, v in info.items())


# Prompt
@mcp.prompt()
def code_review_prompt(code: str, language: str = "python") -> str:
    return f"请审查以下{language}代码:\n```{language}\n{code}\n```"


if __name__ == "__main__":
    mcp.run()
