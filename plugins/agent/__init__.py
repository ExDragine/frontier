"""QQ Agent plugin; pure message components can be imported without registration."""

if globals().get("__plugin__") is not None:
    from nonebot import require

    require("nonebot_plugin_alconna")
    require("nonebot_plugin_apscheduler")
    require("plugins.acp")

    from . import handlers as handlers

    # The Feishu adapter is intentionally not registered here.  Its protocol
    # and transport files remain a documented reference for a future host;
    # the QQ plugin must not mount a second platform implicitly.
