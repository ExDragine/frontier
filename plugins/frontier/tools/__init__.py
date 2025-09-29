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
from .weather import mars_weather
from .web_extract import get_web_extract, tavily_crawl, tavily_extract, tavily_map, tavily_search


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
            get_web_extract,
            aurora_live,
            station_location,
            simple_calculator,
            comet_information,
            comet_list,
            rocket_launches,
            mars_weather,
            tavily_search,
            tavily_extract,
            tavily_crawl,
            tavily_map,
        ]
        self.all_tools = self.mcp_tools + self.local_tools
