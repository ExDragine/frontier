"""Toolbox plugin registration; command modules own their supporting logic."""

if globals().get("__plugin__") is not None:
    from nonebot import require

    require("nonebot_plugin_alconna")

    from . import menu as menu
    from . import settings as settings
    from . import update as update
