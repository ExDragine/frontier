from langchain.tools import tool
from nonebot import logger, require

from utils.staged_artifacts import load_staged_artifact

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402


@tool(response_format="content_and_artifact")
async def send_staged_artifact(artifact_id: str) -> tuple[str, UniMessage | None]:
    """发送子代理工具暂存在本地的图片、视频、文件或复合消息。

    Args:
        artifact_id: 子代理工具结果中 staged_artifact 标签里的 artifact_id
    """
    try:
        artifact = load_staged_artifact(artifact_id, uni_message_cls=UniMessage)
    except FileNotFoundError:
        return f"暂存内容不存在或已过期：{artifact_id}", None
    except ValueError as exc:
        return f"暂存内容 ID 无效：{exc}", None
    except Exception as exc:
        logger.exception(f"读取暂存内容失败: {artifact_id}")
        return f"读取暂存内容失败：{type(exc).__name__}", None
    return f"已读取暂存内容：{artifact_id}", artifact
