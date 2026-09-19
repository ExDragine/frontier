"""News production plugin. Importing pure components has no runtime side effects."""

if globals().get("__plugin__") is not None:
    from nonebot import require

    require("nonebot_plugin_alconna")
    from . import commands as commands
