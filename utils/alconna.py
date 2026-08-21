"""nonebot_plugin_alconna 统一导入入口。

所有需要用到 nonebot_plugin_alconna 的模块从此文件导入，
避免在每个文件中重复 noqa: E402 模式。

注意：require("nonebot_plugin_alconna") 必须在插件 __init__.py 中调用
（NoneBot 插件发现阶段），不在本模块中调用。
"""

from nonebot_plugin_alconna import (  # noqa: E402
    AlconnaQuery,
    At,
    Image,
    Query,
    Target,
    Text,
    UniMessage,
    Video,
    on_alconna,
)

__all__ = [
    "AlconnaQuery",
    "At",
    "Image",
    "Query",
    "Target",
    "Text",
    "UniMessage",
    "Video",
    "on_alconna",
]
