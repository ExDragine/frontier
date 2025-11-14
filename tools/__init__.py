from .adapter import send_audio, send_emoji, send_image, send_video
from .aurora import aurora_live
from .bilibili import get_bilibili_video_info
from .calculator import simple_calculator
from .comet import comet_information, comet_list
from .earthquake import get_china_earthquake, get_japan_earthquake
from .heavens_above import station_location
from .mcp_client import mcp_get_tools
from .paint import get_paint
from .radar import get_static_china_radar
from .rocket import rocket_launches
from .satellite import get_fy4b_cloud_map, get_fy4b_geos_cloud_map, get_himawari_satellite_image
from .space_weather import (
    geospace,
    goes_suvi,
    noaa_enlil_predict,
    planets_weather,
    realtime_solarwind,
    soho_realtime_solarwind,
    solar_flare,
    solar_image,
    sunspot,
    swpc_page,
)
from .tavily import tavily_crawl, tavily_extract, tavily_map, tavily_search
from .weather import get_wind_map, mars_weather


class ModuleTools:
    def __init__(self):
        self.mcp_tools = mcp_get_tools()
        self.local_tools = [
            get_static_china_radar,
            get_fy4b_cloud_map,
            get_fy4b_geos_cloud_map,
            get_bilibili_video_info,
            get_paint,
            get_himawari_satellite_image,
            get_china_earthquake,
            get_japan_earthquake,
            aurora_live,
            station_location,
            simple_calculator,
            comet_information,
            comet_list,
            rocket_launches,
            mars_weather,
            solar_flare,
            realtime_solarwind,
            soho_realtime_solarwind,
            geospace,
            noaa_enlil_predict,
            solar_image,
            goes_suvi,
            sunspot,
            swpc_page,
            planets_weather,
            get_wind_map,
            tavily_search,
            tavily_extract,
            tavily_crawl,
            tavily_map,
            send_image,
            send_audio,
            send_video,
            send_emoji,
        ]
        self.all_tools = self.mcp_tools + self.local_tools
        self.web_tools = [tavily_search, tavily_extract, tavily_crawl, tavily_map]


agent_tools = ModuleTools()
