import datetime
import hashlib
import json
import platform
import zoneinfo

import httpx
import pytz
from mcp.server.fastmcp import FastMCP
from pypinyin import lazy_pinyin

mcp = FastMCP(
    name="simple_mcp",
    dependencies=["langchain_core.messages"],
)


@mcp.tool()
def simple_calculator(expression: str) -> str:
    """
    执行简单的数学运算

    Args:
        expression: 数学表达式，如 '2 + 3 * 4'

    Returns:
        计算结果
    """
    # 安全性检查：只允许基本的数学字符
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "❌ 表达式包含不允许的字符。仅支持数字和基本运算符 (+, -, *, /, (), 空格)"

    try:
        # 使用eval计算，但已经过安全性检查
        result = eval(expression)
        return f"""🧮 计算结果:
表达式: {expression}
结果: {result}
"""
    except ZeroDivisionError:
        return "❌ 除零错误"
    except SyntaxError:
        return "❌ 表达式语法错误"
    except Exception as e:
        return f"❌ 计算失败: {e}"


@mcp.tool()
def text_count(text: str) -> str:
    """
    统计文本中的字符数、单词数和行数

    Args:
        text: 要统计的文本内容

    Returns:
        包含统计信息的字符串
    """
    char_count = len(text)
    word_count = len(text.split())
    line_count = text.count("\n") + 1

    return f"""文本统计结果:
📊 字符数: {char_count}
📝 单词数: {word_count}  
📄 行数: {line_count}
"""


@mcp.tool()
def calculate_hash(text: str, algorithm: str = "sha256") -> str:
    """
    计算文本的哈希值

    Args:
        text: 要计算哈希的文本
        algorithm: 哈希算法，支持 'md5', 'sha1', 'sha256'

    Returns:
        计算出的哈希值
    """
    algorithm = algorithm.lower()

    try:
        if algorithm == "md5":
            hash_obj = hashlib.md5()
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1()
        elif algorithm == "sha256":
            hash_obj = hashlib.sha256()
        else:
            return f"❌ 不支持的哈希算法: {algorithm}。支持的算法: md5, sha1, sha256"

        hash_obj.update(text.encode("utf-8"))
        hash_value = hash_obj.hexdigest()

        return f"""🔐 哈希计算结果:
算法: {algorithm.upper()}
原文: {text[:50]}{"..." if len(text) > 50 else ""}
哈希值: {hash_value}
"""

    except Exception as e:
        return f"❌ 哈希计算失败: {e}"


@mcp.tool()
def string_operations(text: str, operation: str, **kwargs) -> str:
    """
    字符串操作工具

    Args:
        text: 要处理的文本
        operation: 操作类型 ('upper', 'lower', 'title', 'reverse', 'replace')
        **kwargs: 额外参数，如replace操作的old和new参数

    Returns:
        处理后的文本
    """
    try:
        if operation == "upper":
            result = text.upper()
        elif operation == "lower":
            result = text.lower()
        elif operation == "title":
            result = text.title()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "replace":
            old = kwargs.get("old", "")
            new = kwargs.get("new", "")
            if not old:
                return "❌ replace操作需要指定old参数"
            result = text.replace(old, new)
        else:
            return f"❌ 不支持的操作: {operation}。支持的操作: upper, lower, title, reverse, replace"

        return f"""✨ 字符串操作结果:
操作: {operation}
原文: {text}
结果: {result}
"""
    except Exception as e:
        return f"❌ 字符串操作失败: {e}"


@mcp.tool()
def mars_weather():
    """获取火星天气"""
    response = httpx.get("https://mars.nasa.gov/rss/api/?feed=weather&category=msl&feedtype=json", timeout=30).json()
    data = f"{response['descriptions']}\n{response['soles'][0]}"
    return data


@mcp.tool()
async def rocket_launches(days: int = 3) -> str:
    """
    获取未来几天的火箭发射计划

    Args:
        days: 查询未来几天的发射计划，默认3天,范围1-7天

    Returns:
        火箭发射计划信息
    """
    if days < 1 or days > 7:
        return "❌ 查询天数必须在1-7天之间"

    try:
        now = datetime.datetime.now(pytz.UTC)
        now_str = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        tomorrow = now + datetime.timedelta(days=days)
        target_str = tomorrow.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        ENDPOINT = "https://tlpnetwork.com/api/launches"
        HEADERS = {
            "Accept": "application/json",  # 明确只接受JSON
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Type": "application/json",
            "Origin": "https://tlpnetwork.com",
            "Referer": "https://tlpnetwork.com/launches",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        }
        DATA = {"net": {"gte": f"{now_str}", "lte": f"{target_str}"}}

        # 使用异步请求，明确处理编码
        async with httpx.AsyncClient() as client:
            response = await client.post(ENDPOINT, headers=HEADERS, json=DATA)
            response.raise_for_status()

            # 检查响应内容类型
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return f"❌ 服务器返回了非JSON内容: {content_type}"

            # 处理编码问题
            try:
                # 先尝试直接解析JSON
                missions = response.json()
            except UnicodeDecodeError:
                # 如果编码有问题，尝试手动处理
                content_bytes = response.content
                # 尝试不同的编码
                for encoding in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
                    try:
                        content_text = content_bytes.decode(encoding)
                        missions = json.loads(content_text)
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                else:
                    return "❌ 无法解析服务器响应内容编码"

        # 检查是否有发射计划
        if not missions:
            return f"🚀 未来{days}天内没有火箭发射计划"

        # 格式化输出
        message = f"🚀 未来{days}天火箭发射计划:\n\n"
        for mission in missions:
            launch_time = datetime.datetime.fromisoformat(mission["net"]).astimezone(
                zoneinfo.ZoneInfo("Asia/Shanghai")
            )
            message += f"🌟 {mission['name']}\n"
            message += f"📅 发射时间: {launch_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n\n"

        return message.strip()

    except httpx.HTTPStatusError as e:
        return f"❌ 请求失败: HTTP {e.response.status_code}"
    except httpx.RequestError as e:
        return f"❌ 网络请求错误: {str(e)}"
    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}"
    except KeyError as e:
        return f"❌ 数据格式错误，缺少字段: {str(e)}"
    except UnicodeDecodeError as e:
        return f"❌ 编码错误: {str(e)}"
    except Exception as e:
        return f"❌ 获取火箭发射信息失败: {str(e)}"

@mcp.tool()
def comet_information(name):
    """
    获取彗星信息

    Args:
        name: 彗星名称

    Returns:
        彗星信息
    """
    print(name)
    ENDPOINT = "https://cobs.si/api/comet.api"
    params = {
        "des": name,
    }
    content = httpx.get(ENDPOINT, params=params).json()
    try:
        comet_obj = content["object"]
    except KeyError:
        print(content)
        return "列表获取错误"
    message = (
        f"名称:{comet_obj['fullname']}\n"
        f"ID:{comet_obj['id']}\n"
        f"MPC名称:{comet_obj['mpc_name']}\n"
        f"ICQ名称:{comet_obj['icq_name']}\n"
        f"当前星等:{comet_obj['current_mag']}\n"
        f"近日点时间:{comet_obj['perihelion_date']}\n"
        f"近日点亮度:{comet_obj['perihelion_mag']}\n"
        f"峰值亮度:{comet_obj['peak_mag']}\n"
        f"峰值亮度时间:{comet_obj['peak_mag_date']}\n"
        f"可观测:{'是' if comet_obj['is_observed'] else '否'}\n"
        f"活动情况:{'活动' if comet_obj['is_active'] else '非活动'}"
    )
    return message

@mcp.tool()
def comet_list(cur_mag=15):
    """
    获取可见彗星列表

    Args:
        cur_mag: 最大星等

    Returns:
        可见彗星列表
    """
    ENDPOINT = "https://cobs.si/api/comet_list.api"
    params = {
        "type": "C",
        "alt-des": True,
        "cur-mag": cur_mag,
        "is-observed": True,
        "is-active": True,
        "page": 1,
    }
    content = httpx.get(ENDPOINT, params=params).json()
    try:
        objects = content["objects"]
    except KeyError:
        print(content)
        return "列表获取错误"
    if objects:
        message = "\n".join(
            (
                f"名称:{comet_obj['fullname']}\n"
                f"ID:{comet_obj['id']}\n"
                f"MPC名称:{comet_obj['mpc_name']}\n"
                f"ICQ名称:{comet_obj['icq_name']}\n"
                f"当前星等:{comet_obj['current_mag']}\n"
                f"近日点时间:{comet_obj['perihelion_date']}\n"
                f"近日点亮度:{comet_obj['perihelion_mag']}\n"
                f"峰值亮度:{comet_obj['peak_mag']}\n"
                f"峰值亮度时间:{comet_obj['peak_mag_date']}\n"
                f"可观测:{'是' if comet_obj['is_observed'] else '否'}\n"
                f"活动情况:{'活动' if comet_obj['is_active'] else '非活动'}\n"
                for comet_obj in objects
            )
        )
        return message


@mcp.tool()
def get_time() -> str:
    """
    获取当前时间

    Returns:
        当前时间字符串
    """
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"🕐 当前时间: {current_time}"
    except Exception as e:
        return f"❌ 获取时间失败: {str(e)}"


@mcp.tool()
async def weather(city_name: str) -> str:
    """
    获取当前天气

    Args:
        city_name: 城市名称

    Returns:
        天气信息
    """
    try:
        # 转换城市名为拼音
        city_name_pinyin = lazy_pinyin(city_name)
        city_name_pinyin = "".join(city_name_pinyin)

        async with httpx.AsyncClient() as client:
            # 获取地理位置
            location_response = await client.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={city_name_pinyin}&count=10&language=en&format=json"
            )
            location_data = location_response.json()

            if not location_data.get("results"):
                return f"❌ 未找到城市: {city_name}"

            location_data = location_data["results"][0]
            latitude = location_data["latitude"]
            longitude = location_data["longitude"]

            # 获取天气数据
            weather_response = await client.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&timezone=auto"
            )
            weather_data = weather_response.json()

            current_weather = weather_data["current_weather"]
            result = f"🌤️ 当前{city_name}的天气为{current_weather['temperature']}℃，风速为{current_weather['windspeed']}m/s，风向为{current_weather['winddirection']}°"
            return result

    except Exception as e:
        return f"❌ 获取{city_name}天气失败: {str(e)}"


@mcp.tool()
async def get_future_weather(city_name: str, days: int) -> str:
    """
    获取未来天气

    Args:
        city_name: 城市名称
        days: 预报天数

    Returns:
        未来天气信息
    """
    try:
        # 转换城市名为拼音
        city_name_pinyin = lazy_pinyin(city_name)
        city_name_pinyin = "".join(city_name_pinyin)

        async with httpx.AsyncClient() as client:
            # 获取地理位置
            location_response = await client.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={city_name_pinyin}&count=10&language=en&format=json"
            )
            location_data = location_response.json()

            if not location_data.get("results"):
                return f"❌ 未找到城市: {city_name}"

            location_data = location_data["results"][0]
            latitude = location_data["latitude"]
            longitude = location_data["longitude"]

            # 获取天气数据
            weather_response = await client.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&forecast_days={days}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
            )
            weather_data = weather_response.json()

            result = f"📅 {city_name}未来{days}天天气预报:\n"
            daily_data = weather_data["daily"]
            for i in range(days):
                result += f"第{i + 1}天: 天气代码{daily_data['weathercode'][i]}，最高气温{daily_data['temperature_2m_max'][i]}℃，最低气温{daily_data['temperature_2m_min'][i]}℃\n"

            return result.strip()

    except Exception as e:
        return f"❌ 获取{city_name}未来{days}天天气失败: {str(e)}"


@mcp.resource("system://info")
def system_info() -> str:
    """获取系统信息"""
    try:
        info = {
            "操作系统": f"{platform.system()} {platform.release()}",
            "Python版本": platform.python_version(),
            "处理器架构": platform.machine(),
            "主机名": platform.node(),
            "处理器": platform.processor(),
            "平台": platform.platform(),
        }

        result = "💻 系统信息:\n"
        for key, value in info.items():
            result += f"  {key}: {value}\n"

        return result
    except Exception as e:
        return f"❌ 获取系统信息失败: {e}"


@mcp.prompt()
def code_review_prompt(code: str, language: str = "python") -> str:
    """
    生成代码审查提示

    Args:
        code: 要审查的代码
        language: 编程语言
    """
    prompt_text = f"""请审查以下{language}代码并提供建议:

```{language}
{code}
```

请从以下方面进行审查:
1. 代码质量和可读性
2. 潜在的bug或安全问题  
3. 性能优化建议
4. 最佳实践建议
5. 代码风格和规范

请提供具体、可操作的改进建议。
"""

    return prompt_text


@mcp.prompt()
def text_analysis_prompt(text: str) -> str:
    """
    生成文本分析提示

    Args:
        text: 要分析的文本
    """
    prompt_text = f"""请分析以下文本:

"{text}"

请提供以下分析:
1. 文本主题和核心要点
2. 情感色彩分析
3. 关键词提取
4. 文本质量评估
5. 改进建议(如果适用)

请提供详细、准确的分析结果。
"""

    return prompt_text


if __name__ == "__main__":
    mcp.run()
