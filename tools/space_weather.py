import datetime
from typing import Literal

import httpx
from bs4 import BeautifulSoup
from langchain.tools import tool
from nonebot import require
from playwright.async_api import async_playwright

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import Image, UniMessage  # noqa: E402


@tool(response_format="content")
async def solar_flare():
    """
    获取最近7天的太阳耀斑数据

    Returns:
        str: 最近7天的太阳耀斑数据
    """
    # 获取最近7天的太阳耀斑数据
    today = datetime.datetime.now()
    before = today - datetime.timedelta(days=3)
    today_str = today.strftime("%Y-%m-%d")
    before_str = before.strftime("%Y-%m-%d")
    url = "https://api.nasa.gov/DONKI/FLR"
    params = {"startDate": before_str, "endDate": today_str, "api_key": "DEMO_KEY"}
    noticed: list[str] = []
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        flare_data = response.json()
    for event in flare_data:
        if event["classType"][:1] == "X":
            message = (
                f"发生时间:{event['beginTime']}\n"
                f"耀斑类型:{event['classType']}\n"
                f"来源:{event['activeRegionNum']}\n"
                f"参阅:{event['link']}\n"
            )
            noticed.append(message)
    if noticed:
        return "\n".join(noticed)
    else:
        return "最近没有X级别以上的FLR发生"


@tool(response_format="content")
async def realtime_solarwind():
    """
    获取实时太阳风数据

    Returns:
        str: 实时太阳风数据
    """
    MAG = "https://services.swpc.noaa.gov/text/rtsw/data/mag-2-hour.i.json"
    PLASMA = "https://services.swpc.noaa.gov/text/rtsw/data/plasma-2-hour.i.json"
    PLANETART_K = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    """
    MAG_5MIN = "https://services.swpc.noaa.gov/text/rtsw/data/mag-2-hour-5-minute.json"
    PLASMA_5MIN = "https://services.swpc.noaa.gov/text/rtsw/data/plasma-2-hour-5-minute.json"
    PLANETART_K_5MIN = "https://services.swpc.noaa.gov/text/rtsw/data/kp-2-hour-5-minute.json"
    """
    magnitude = (await httpx_client.get(MAG)).json()
    plasma = (await httpx_client.get(PLASMA)).json()
    planet_k = (await httpx_client.get(PLANETART_K)).json()
    time_tag = plasma[-1][0]
    speed = plasma[-1][1]
    density = plasma[-1][2]
    temperature = plasma[-1][3]
    quality = plasma[-1][4]
    source = plasma[-1][5]
    active = plasma[-1][6]
    message = (
        "> 太阳风信息\n"
        f"时间：{time_tag} (UTC)\n"
        f"速度：{speed} km/s\n"
        f"密度：{density} cm^3\n"
        f"温度：{temperature} K\n"
        f"是否活跃：{'是' if str(active) == '1' else '否'}\n"
        f"当前Kp: {planet_k[-1][1]}\n"
        f"行星际磁场总强: {magnitude[-1][1]}\n"
        f"数据质量: {'原始数据' if str(quality) == '0' else '校准数据'}\n"
        f"来源: {'ACE' if str(source) == '1' else 'DSCOVR'}\n"
    )
    return message


@tool(response_format="content")
async def soho_realtime_solarwind():
    """
    获取SOHO太阳风数据

    Returns:
        str: SOHO太阳风数据
    """
    ENDPOINT = "https://space.umd.edu/pm/pmsw.used"
    content = await httpx_client.get(ENDPOINT)
    if not isinstance(content, bytes):
        return str(content)
    decode_data = content.decode("utf-8").split("\n")
    parts = decode_data[-1].split()
    # 年和第几天转化为具体日期时间
    year = int(parts[0])
    day_of_year = int(parts[1].split(":")[0])
    time_str = parts[1].split(":")[1] + ":" + parts[1].split(":")[2] + ":" + parts[1].split(":")[3]
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(
        days=day_of_year - 1,
        hours=int(time_str.split(":")[0]),
        minutes=int(time_str.split(":")[1]),
        seconds=int(time_str.split(":")[2]),
    )
    date_utc_plus_8 = date + datetime.timedelta(hours=8)
    speed = float(parts[2])
    density = float(parts[3])
    proton_temperature = float(parts[4])
    angel = float(parts[5])
    mag_min = int(parts[6])
    mag_max = int(parts[7])

    message = (
        "> 太阳风信息\n"
        f"日期时间：{date_utc_plus_8}\n"
        f"速度：{speed} km/s\n"
        f"质子密度：{density} cm^3\n"
        f"质子热速度：{proton_temperature} km/s\n"
        f"太阳风速度矢量与磁场之间的角度：{angel} deg\n"
        f"磁场强度最小值：{mag_min} nT\n"
        f"磁场强度最大值：{mag_max} nT\n"
        "数据来源:https://space.umd.edu/pm/"
    )
    return message


@tool(response_format="content_and_artifact")
async def geospace() -> tuple[str, UniMessage]:
    """
    获取地球地磁场的径向速度，密度与压力图

    Returns:
        tuple[str, UniMessage]: 地磁场的径向速度，密度与压力图
    """
    urls = [
        "https://services.swpc.noaa.gov/images/animations/geospace/velocity/latest.png",
        "https://services.swpc.noaa.gov/images/animations/geospace/density/latest.png",
        "https://services.swpc.noaa.gov/images/animations/geospace/pressure/latest.png",
    ]
    message = "这是来自地磁场的径向速度，密度与压力图"
    return message, UniMessage([Image(url=url) for url in urls])


@tool(response_format="content_and_artifact")
async def noaa_enlil_predict() -> tuple[str, UniMessage]:
    """获取来自NOAA Enlil模型的太阳风密度与速度可视化预测图

    Returns:
        tuple[str, UniMessage]: 太阳风预测图
    """
    time = datetime.datetime.now(tz=datetime.UTC).strftime("%Y%m%dT%H")
    enlil = "https://services.swpc.noaa.gov/images/animations/enlil/"
    content = (await httpx_client.get(enlil)).content
    page = BeautifulSoup(content, "html.parser")
    images = []
    images = [a["href"] for a in page.select("a[href]")]
    link = images[-2][:17]
    link = f"{enlil}{link}{time}0000.jpg"
    return "这是当下的太阳风预测，基于NOAA Enlil模型", UniMessage(Image(url=link))


@tool(response_format="content_and_artifact")
async def solar_image(imageType) -> tuple[str, UniMessage | None]:
    """
    # 太阳常用图像获取
    NATA：北半球今晚极光预测
    NATMA：北半球明天极光预测
    NOA：北半球极光预测
    SOA：南半球极光预测
    SN：太阳黑子图
    TL：过去五天发生的事件图
    IETL：过去三天发生的时间图以及未来两天展望
    GS1D：一天内太阳风速度以及地磁环境数据图表
    GS3D：三天内太阳风速度以及地磁环境数据图表
    GS7D：七天内太阳风速度以及地磁环境数据图表
    GS3H：三小时内太阳风速度以及地磁环境数据图表
    C2：SOHO C2日冕仪图像
    C3：SOHO C3日冕仪图像
    CCOR：搭载于GOES上的新一代紧凑型日冕仪图像（日冕仪图像优先用这个）
    SWX：X-ray通量，质子通量，地磁场活跃度综合图表
    HMIB：SDO HMI(Helioseismic and Magnetic Imager)图像

    Args:
        imageType (str): 图像类型，可选值：NATA、NATMA、NOA、SOA、SN、TL、IETL、GS1D、GS3D、GS7D、GS3H、C2、C3、CCOR、SSM、SWX、HMIB

    Returns:
        MessageSegment: 返回构建好的消息串
    """
    imagesURL = {
        "NATA": "https://services.swpc.noaa.gov/experimental/images/aurora_dashboard/tonights_static_viewline_forecast.png",  # NorthAmericanTonightAurora
        "NATMA": "https://services.swpc.noaa.gov/experimental/images/aurora_dashboard/tomorrow_nights_static_viewline_forecast.png",  # NorthAmericanTomorrowAurora
        "NOA": "https://services.swpc.noaa.gov/images/aurora-forecast-northern-hemisphere.jpg",  # NorthOvationAurora
        "SOA": "https://services.swpc.noaa.gov/images/aurora-forecast-southern-hemisphere.jpg",  # SouthOvationAurora
        "SN": "https://services.swpc.noaa.gov/images/synoptic-map.jpg",  # 手绘太阳黑子图
        "TL": "https://services.swpc.noaa.gov/images/notifications-timeline.png",  # 过去五天发生的事件图
        "IETL": "https://services.swpc.noaa.gov/images/notifications-in-effect-timeline.png",  # 过去三天发生的时间图以及未来两天展望
        "GS1D": "https://services.swpc.noaa.gov/images/geospace/geospace_1_day.png",  # 一天内太阳风速度以及地磁环境数据图表
        "GS3D": "https://services.swpc.noaa.gov/images/geospace/geospace_3_day.png",  # 三天内太阳风速度以及地磁环境数据图表
        "GS7D": "https://services.swpc.noaa.gov/images/geospace/geospace_7_day.png",  # 七天内太阳风速度以及地磁环境数据图表
        "GS3H": "https://services.swpc.noaa.gov/images/geospace/geospace_3_hour.png",  # 三 小时内内太阳风速度以及地磁环境数据图表
        "C2": "https://services.swpc.noaa.gov/images/animations/lasco-c2/latest.jpg",
        "C3": "https://services.swpc.noaa.gov/images/animations/lasco-c3/latest.jpg",
        "CCOR": "https://services.swpc.noaa.gov/images/animations/ccor1/latest.jpg",
        "SWX": "https://services.swpc.noaa.gov/images/swx-overview-small.gif",
        "HMIB": "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIB.jpg",
    }

    if imageType not in imagesURL:
        return "查无此图\n数据来源: NOAA SWPC", None
    return "获取成功", UniMessage.image(url=imagesURL[imageType])


@tool(response_format="content_and_artifact")
async def goes_suvi(
    type: Literal["094", "131", "171", "195", "284", "304", "map"] | None = "304",
) -> tuple[str, UniMessage | None]:
    """
    获取GOES-16/17 SUVI图像，有094、131、171、195、284、304、map七种波段的图像，map为根据日面特征生成的特征图

    Args:
        type (str): 图像类型，可选值：094、131、171、195、284、304、map

    Returns:
        tuple[str, UniMessage | None]: 返回构建好的消息串
    """
    if type not in ["94", "131", "171", "195", "284", "304", "map"]:
        return "查无此图\n数据来源: NOAA SWPC", None
    url = f"https://services.swpc.noaa.gov/images/animations/suvi/primary/{type}/latest.png"
    return "获取成功", UniMessage.image(url=url)


@tool(response_format="content_and_artifact")
async def sunspot(source: Literal["SOHO", "SDO", "ASO-S"] | None) -> tuple[str, UniMessage | None]:
    """
    获取太阳黑子图像，支持SOHO、SDO、ASO-S三种来源

    Args:
        source (str): 图像来源，可选值：SOHO、SDO、ASO-S，优先级：SOHO > SDO > ASO-S

    Returns:
        tuple[str, UniMessage | None]: 返回构建好的消息串
    """
    if source == "":
        source = "SOHO"
    match source:
        case "SOHO":
            url = "https://soho.nascom.nasa.gov/data/synoptic/sunspots_earth/mdi_sunspots_1024.jpg"
            content = (await httpx_client.get(url)).content
            return "获取成功", UniMessage.image(raw=content)
        case "SDO":
            url = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_2048_HMIIC.jpg"
            content = (await httpx_client.get(url)).content
            return "获取成功", UniMessage.image(raw=content)
        case "ASO-S" | _:
            # 构造请求的基本信息
            url = "http://aso-s.pmo.ac.cn:80/asosToday/getLastImg"
            payload = {
                "basePath": "http://aso-s.pmo.ac.cn:80/",
                "imageType": "wst",
                "resolution": "",  # 请根据需要填入分辨率
            }
            aso_s_url = await httpx_client.post(url, data=payload)
            aso_s_img = (await httpx_client.get(aso_s_url.json()["msg"])).content
            return "获取成功", UniMessage.image(raw=aso_s_img)


@tool(response_format="content_and_artifact")
async def swpc_page() -> tuple[str, UniMessage | None]:
    """
    获取SWPC空间天气爱好者仪表盘图像

    Returns:
        tuple[str, UniMessage | None]: 空间天气爱好者仪表盘图像
    """
    message = None
    async with async_playwright() as p:
        try:
            browser = p.chromium
            browser = await browser.launch()
            page = await browser.new_page()
            # await page.set_viewport_size({"width": 304, "height": 367})
            await page.goto(
                "https://www.swpc.noaa.gov/communities/space-weather-enthusiasts-dashboard",
                timeout=120000,
                wait_until="networkidle",
            )
            await page.wait_for_timeout(10000)
            element_handle = await page.query_selector("id=region-content")
            if element_handle:
                picture = await element_handle.screenshot()
                message = picture
            await browser.close()
            return "获取成功", UniMessage.image(raw=message)
        except Exception:
            return "获取超时，请稍后再试", None


@tool(response_format="content_and_artifact")
async def planets_weather(planet) -> tuple[str, UniMessage | None]:
    """
    获取各个行星的基本数据和照片

    Args:
        planet (str): 行星名称，例如：太阳、水星、金星、地球、月球、火星、木星、土星、天王星、海王星、冥王星

    Returns:
        tuple[str, UniMessage | None]: 返回构建好的消息串
    """
    planets = [
        [
            "太阳",
            "15000000",
            "5600",
            "2.334*10^16 Pa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/sun.jpg",
        ],
        [
            "水星",
            "427",
            "-173",
            "0.5 nPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/mercury.jpg",
        ],
        [
            "金星",
            "483",
            "438",
            "9.3MPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/venus.jpg",
        ],
        [
            "地球",
            "55",
            "-89",
            "1 atm",
            "https://nssdc.gsfc.nasa.gov/planetary/image/earth.jpg",
        ],
        [
            "月球",
            "121",
            "-246",
            "0.3 nPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/moon.jpg",
        ],
        [
            "火星",
            "35",
            "-110",
            "636 Pa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/mars.jpg",
        ],
        [
            "木星",
            "-105",
            "-195",
            "600 kPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/jupiter.jpg",
        ],
        [
            "土星",
            "-122",
            "-185",
            "140 kPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/saturn.jpg",
        ],
        [
            "天王星",
            "47",
            "-220",
            "130 kPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/uranus.jpg",
        ],
        [
            "海王星",
            "-201",
            "-218",
            "500 kPa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/neptune.jpg",
        ],
        [
            "冥王星",
            "-218",
            "-240",
            "1 Pa",
            "https://nssdc.gsfc.nasa.gov/planetary/image/nh_pluto.jpg",
        ],
    ]
    for p in planets:
        if p[0] == planet:
            return f"> {p[0]}天气\n最高气温: {p[1]} ℃ / 最低气温 {p[2]} ℃\n气压: {p[3]}\n", UniMessage(Image(url=p[4]))
    return "你要找的是太阳系的货吗", None
