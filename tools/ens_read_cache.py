"""ENS 会话缓存读取工具。

用户首次 ve/vep 查询后，结果自动写入会话缓存。
追问时 Agent 调用本工具读取缓存文字参考回答，或重发视频/截图。
"""

import contextvars
import time as _time

from langchain_core.tools import tool
from nonebot import logger

from utils.ens_gate import _ens_session_store

try:
    from langchain_core.runnables.config import var_child_runnable_config as _lc_config_var
except Exception:
    _lc_config_var = None

from utils.alconna import UniMessage


def _current_thread_id() -> str:
    """从 LangChain config 中提取当前会话 thread_id。"""
    if _lc_config_var is not None:
        try:
            cfg = _lc_config_var.get()
            if cfg:
                return str(cfg["configurable"]["thread_id"])
        except Exception:
            pass
    return "unknown"


@tool(response_format="content_and_artifact")
async def ens_read_cache(return_artifact: bool = False) -> tuple[str, UniMessage | None]:
    """读取当前会话最近一次 ve/vep 查询返回的文字摘要和媒体。

    当用户追问他上次 ENS 查询结果时（如"这个数据什么意思"、"坐标对吗"、
    "数据时间是什么时候"、"当时数值多少"等），优先调用本工具获取缓存文字作为参考。
    工具返回的文字描述了上次查询的场景、坐标、数据值和时间，Agent 依据它组织回复。

    当用户追问要求重看视频/截图时（如"视频再发一下"、"图呢"），
    调用本工具并传 return_artifact=True。

    本工具只读取缓存，不会触发浏览器操作。如果缓存为空，
    告知用户发送 ve/vep 前缀的新消息来查询。

    禁止在 ens_normal / ens_professional 同一轮对话的回复中再次调用本工具。
    用户发起新一轮 ve/vep 查询时已有新的视频返回，不需要再读缓存重发。

    Args:
        return_artifact: 是否同时返回缓存的视频/截图。用户只想看数据时传 False，
                         用户要求重看视频/截图时传 True。
    """
    thread_id = _current_thread_id()
    entry = _ens_session_store.get(thread_id)
    if entry is None:
        return (
            "当前会话没有 ENS 查询缓存。请告知用户：这条消息没有 ve/vep 前缀，"
            "如果想看地球可视化数据，请发 ve/vep 开头的消息；如果想查别的信息直接说就行。",
            None,
        )

    text = f"[缓存可用] {entry['text']}"
    if return_artifact:
        artifact_type = entry.get("artifact_type", "video")
        artifact_bytes = entry.get("artifact_bytes")
        if artifact_bytes is None:
            return f"{text}\n[缓存媒体暂不可用，请用户重新发 ve/vep 查询]", None
        if artifact_type == "image":
            return text, UniMessage.image(raw=artifact_bytes)
        return text, UniMessage.video(raw=artifact_bytes)

    return text, None
