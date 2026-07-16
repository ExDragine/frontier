"""GCJ-02 坐标 → 位置描述（LLM 辅助逆地理编码）。

API 返回的台风坐标为 GCJ-02 坐标系，此模块通过轻量 LLM 调用
查询坐标对应的海域或行政区划名称。

注意：不使用 with_structured_output，因为 DeepSeek 思考模式不
支持 tool_choice 和 response_format: json_object，改为直接文本调用。
"""

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from utils.configs import EnvConfig
from utils.llm_factory import create_llm

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "你是一个逆地理编码助手。根据提供的 GCJ-02 经纬度坐标，"
    "判断该位置所在的海域或行政区划。\n"
    "返回 20 字以内的简短描述。\n"
    "规则：\n"
    "- 如果在海域（海洋区域），直接返回海域名，如「菲律宾海」「东海」「巴士海峡」\n"
    "- 如果在中国城市/陆地，格式为「中国+省级行政单位+市级行政单位」，"
    "如「中国台湾省台北市」「中国海南省三沙市」\n"
    "- 如果在外国城市/陆地，格式为「国家+城市名」，如「菲律宾马尼拉」「日本东京」"
)


def _trim_description(text: str) -> str:
    """清洗并截断 LLM 返回的描述文本。"""
    text = text.strip().strip('"').strip("'").strip()
    # 如果有多行只取第一行
    text = text.split("\n")[0]
    # 去掉可能的编号前缀如 "1. " 或 "- "
    text = re.sub(r"^[\d\-*]+\.?\s*", "", text)
    return text[:25]  # 略放宽到 25 字


async def reverse_geocode(lat: float, lng: float) -> str:
    """查询 GCJ-02 坐标对应的海域或行政区划描述。

    规则：
    - 海域 → 直接返回海域名，如「菲律宾海」「东海」「巴士海峡」
    - 中国城市 → 「中国+省级行政单位+市级行政单位」
      e.g.「中国台湾省台北市」「中国海南省三沙市」
    - 外国城市 → 「国家+城市名」
      e.g.「菲律宾马尼拉」「日本东京」

    Args:
        lat: 纬度
        lng: 经度

    Returns:
        25 字以内的简短位置描述。LLM 调用失败时返回空字符串。
    """
    try:
        llm = create_llm(
            model=EnvConfig.SIGNAL_MODEL,
            provider=EnvConfig.SIGNAL_MODEL_PROVIDER,
            temperature=0.1,
            streaming=False,
        )
        response = await llm.ainvoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=f"经纬度 ({lat:.2f}, {lng:.2f}) GCJ-02 坐标位于哪里？"),
            ]
        )
        desc = _trim_description(response.content)
        logger.debug("逆地理编码: (%.2f, %.2f) → %s", lat, lng, desc)
        return desc
    except Exception as e:
        logger.warning("逆地理编码 LLM 调用失败: %s", e)
        return ""
