from langchain.tools import tool
from nonebot import require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402


@tool(response_format="content_and_artifact")
async def send_image(url: str) -> tuple[str, UniMessage]:
    """发送图片工具
    Args:
        url (str): 图片URL
    Returns:
        tuple[str, UniMessage]: (描述信息, 图片消息段)
    """
    return "构建了一个图片消息", UniMessage.image(url=url)


@tool(response_format="content_and_artifact")
async def send_audio(url: str) -> tuple[str, UniMessage]:
    """发送音频工具
    Args:
        url (str): 音频URL
    Returns:
        tuple[str, UniMessage]: (描述信息, 音频消息段)
    """
    return "构建了一个音频消息", UniMessage.audio(url=url)


@tool(response_format="content_and_artifact")
async def send_video(url: str) -> tuple[str, UniMessage]:
    """发送视频工具
    Args:
        url (str): 视频URL
    Returns:
        tuple[str, UniMessage]: (描述信息, 视频消息段)
    """
    return "构建了一个视频消息", UniMessage.video(url=url)


@tool(response_format="content_and_artifact")
async def send_emoji(emoji_id: str) -> tuple[str, UniMessage]:
    """发送表情工具
    Args:
        emoji_id (str): 表情ID
    Returns:
        tuple[str, UniMessage]: (描述信息, 表情消息段)
    """
    return "构建了一个表情消息", UniMessage.emoji(id=emoji_id)
