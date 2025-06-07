from plugins.frontier.tools.aurora import aurora_live
from plugins.frontier.tools.earthquake import get_china_earthquake, get_japan_earthquake
from plugins.frontier.tools.heavens_above import station_location
from plugins.frontier.tools.mcp_client import mcp_get_tools
from plugins.frontier.tools.paint import paint
from plugins.frontier.tools.radar import get_static_china_radar
from plugins.frontier.tools.satellite import get_fy4b_cloud_map, get_fy4b_geos_cloud_map, get_himawari_satellite_image
from plugins.frontier.tools.web_extract import web_extract


class ModuleTools:
    def __init__(self):
        self.mcp_tools = mcp_get_tools()
        self.local_tools = [
            get_static_china_radar,
            get_fy4b_cloud_map,
            get_fy4b_geos_cloud_map,
            paint,
            get_himawari_satellite_image,
            get_china_earthquake,
            get_japan_earthquake,
            web_extract,
            aurora_live,
            station_location,
        ]
        self.all_tools = self.mcp_tools + self.local_tools
