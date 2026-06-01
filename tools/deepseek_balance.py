from urllib.parse import urlparse, urlunparse

import httpx
from langchain.tools import tool
from nonebot import logger

from utils.configs import EnvConfig

DEFAULT_BALANCE_URL = "https://api.deepseek.com/user/balance"

from utils.http_client import get_http_client

httpx_client = get_http_client("deepseek_balance")



def _api_key_value() -> str:
    return EnvConfig.DEEPSEEK_API_KEY.get_secret_value().strip()


def _balance_url() -> str:
    raw_base = (EnvConfig.DEEPSEEK_API_BASE or "").strip()
    if not raw_base:
        return DEFAULT_BALANCE_URL

    parsed = urlparse(raw_base)
    if not parsed.scheme or not parsed.netloc:
        return DEFAULT_BALANCE_URL
    return urlunparse((parsed.scheme, parsed.netloc, "/user/balance", "", "", ""))


def _format_balance(data: dict) -> str:
    if not isinstance(data, dict):
        raise ValueError("响应不是 JSON 对象")

    available = "可用" if data.get("is_available") else "不可用"
    balance_infos = data.get("balance_infos")
    if not isinstance(balance_infos, list):
        raise ValueError("响应缺少 balance_infos 数组")
    if not balance_infos:
        return f"DeepSeek API 余额：{available}\n余额明细：无"

    lines = [f"DeepSeek API 余额：{available}"]
    for item in balance_infos:
        if not isinstance(item, dict):
            raise ValueError("balance_infos 包含非对象条目")
        currency = item.get("currency", "UNKNOWN")
        total = item.get("total_balance", "0")
        granted = item.get("granted_balance", "0")
        topped_up = item.get("topped_up_balance", "0")
        lines.append(f"- {currency} 总余额 {total}，赠金 {granted}，充值 {topped_up}")
    return "\n".join(lines)


@tool(response_format="content")
async def get_deepseek_api_balance() -> str:
    """查询 DeepSeek API 账户余额。"""
    api_key = _api_key_value()
    if not api_key:
        return "未配置 DeepSeek API Key：请在 env.toml 的 [key].deepseek_api_key 中填写。"

    try:
        response = await httpx_client.get(_balance_url(), headers={"Authorization": f"Bearer {api_key}"})
        response.raise_for_status()
        return _format_balance(response.json())
    except Exception as e:
        logger.error("DeepSeek balance query error", exc_info=e)
        return f"获取 DeepSeek API 余额失败: {e}"
