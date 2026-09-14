"""QQ Agent gateway handling."""

import re
import time
from pathlib import Path
from typing import Any

from nonebot.adapters.milky.event import MessageEvent
from pydantic import BaseModel, Field

from utils.configs import EnvConfig
from utils.database import GroupSettingsManager, MessageDatabase, get_engine
from utils.signal_llm import signal_structured

messages_db = MessageDatabase()


REPLY_CHECK_MIN_TEXT_LENGTH = 8


REPLY_CHECK_GROUP_COOLDOWN_SECONDS = 120


REPLY_CHECK_ASSISTANT_REPLY_COOLDOWN_SECONDS = 20 * 60


REPLY_CHECK_ACTIVE_GROUP_WINDOW_SECONDS = 60


REPLY_CHECK_ACTIVE_GROUP_MESSAGE_LIMIT = 20


REPLY_CHECK_STRONG_KEYWORDS = (
    "求助",
    "救命",
    "帮忙",
    "帮我",
    "谁知道",
    "有没有人知道",
    "报错",
    "失败",
    "崩了",
    "卡住",
    "不会",
    "不懂",
    "问一下ai",
    "问一下 ai",
    "机器人看看",
    "有没有bot",
    "有没有 bot",
)


REPLY_CHECK_QUESTION_KEYWORDS = (
    "?",
    "？",
    "怎么",
    "为什么",
    "为啥",
    "哪里",
    "如何",
    "能不能",
    "有没有",
    "什么",
    "哪个",
    "咋",
)


ACTIVE_TRIGGER_STOP_KEYWORDS = (
    "别回",
    "不要回",
    "不用回",
    "无需回复",
    "别说话",
    "不要说话",
    "别理",
    "闭嘴",
    "停止回复",
    "别回复",
)


ACTIVE_TRIGGER_LOW_INFO_PHRASES = {
    "h",
    "hh",
    "hhh",
    "哈哈",
    "哈哈哈",
    "哈哈哈哈",
    "笑死",
    "草",
    "乐",
    "好",
    "好的",
    "收到",
    "嗯",
    "嗯嗯",
    "哦",
    "噢",
    "啊",
    "诶",
    "在吗",
    "在不在",
}


ACTIVE_TRIGGER_STRIP_CHARS = " \t\r\n:：,，.。!！?？~～…、/\\|[]()（）【】"


_reply_check_last_checked_at: dict[int, float] = {}


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with true, either reply with false"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


def _reply_check_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content or "")

    parts = []
    for item in content:
        if not isinstance(item, dict):
            parts.append(str(item))
            continue
        item_type = item.get("type")
        if item_type == "text":
            parts.append(str(item.get("text", "")))
        elif item_type:
            labels = {
                "image": "图片",
                "image_url": "图片",
                "audio": "语音",
                "video": "视频",
                "file": "文件",
            }
            parts.append(f"[{labels.get(item_type, item_type)}]")
    return "\n".join(part for part in parts if part)


def _looks_like_reply_check_candidate(text: str, *, active_group: bool) -> bool:
    compact_text = "".join(text.lower().split())
    if not compact_text:
        return False

    has_strong_signal = any(keyword in compact_text for keyword in REPLY_CHECK_STRONG_KEYWORDS)
    if active_group:
        return has_strong_signal

    if has_strong_signal:
        return True
    if len(compact_text) < REPLY_CHECK_MIN_TEXT_LENGTH:
        return False
    return any(keyword in compact_text for keyword in REPLY_CHECK_QUESTION_KEYWORDS)


def _active_trigger_content(plaintext: str, wake_words: list[str]) -> str:
    text = plaintext.strip()
    for wake_word in sorted((word for word in wake_words if word), key=len, reverse=True):
        if text.startswith(wake_word):
            return text[len(wake_word) :].strip(ACTIVE_TRIGGER_STRIP_CHARS)
    return text.strip(ACTIVE_TRIGGER_STRIP_CHARS)


def _message_gateway_user_id(event: MessageEvent) -> int | str:
    user_id_raw = event.get_user_id()
    try:
        return int(user_id_raw)
    except ValueError:
        return user_id_raw


def _message_gateway_blocked_by_access_policy(group_id: int, user_id: int | str) -> bool:
    if group_id != 0 and EnvConfig.AGENT_WHITELIST_MODE and group_id not in EnvConfig.AGENT_WHITELIST_GROUP_LIST:
        return True
    if group_id in EnvConfig.AGENT_BLACKLIST_GROUP_LIST:
        return True
    if EnvConfig.AGENT_WHITELIST_MODE and user_id not in EnvConfig.AGENT_WHITELIST_PERSON_LIST:
        return True
    return user_id in EnvConfig.AGENT_BLACKLIST_PERSON_LIST


async def _reply_check_group_is_active(group_id: int, now_ms: int) -> bool:
    since_time = now_ms - REPLY_CHECK_ACTIVE_GROUP_WINDOW_SECONDS * 1000
    message_count = await messages_db.count_group_messages_since(group_id=group_id, since_time=since_time)
    return message_count > REPLY_CHECK_ACTIVE_GROUP_MESSAGE_LIMIT


async def _reply_check_assistant_recently_replied(group_id: int, now_ms: int) -> bool:
    latest_time = await messages_db.latest_group_role_message_time(group_id=group_id, role="assistant")
    if latest_time is None:
        return False
    return now_ms - latest_time < REPLY_CHECK_ASSISTANT_REPLY_COOLDOWN_SECONDS * 1000


async def _reply_check_should_reply(group_id: int, plaintext: str, messages: list) -> bool:
    now_ms = int(time.time() * 1000)
    now = time.monotonic()
    active_group = await _reply_check_group_is_active(group_id, now_ms)
    if not _looks_like_reply_check_candidate(plaintext, active_group=active_group):
        return False
    if await _reply_check_assistant_recently_replied(group_id, now_ms):
        return False
    last_checked_at = _reply_check_last_checked_at.get(group_id)
    if last_checked_at is not None and now - last_checked_at < REPLY_CHECK_GROUP_COOLDOWN_SECONDS:
        return False
    _reply_check_last_checked_at[group_id] = now

    reply_check_messages = [
        *messages,
        {"role": "user", "content": str({"metadata": {}, "content": plaintext})},
    ]
    temp_conv: list[dict] = reply_check_messages[-5:]
    plain_conv = "\n".join(_reply_check_content_text(conv.get("content", "")) for conv in temp_conv)
    with open(Path(__file__).resolve().parent / "prompts" / "reply_check.md", encoding="utf-8") as f:
        system_prompt = f.read().format(name=EnvConfig.BOT_NAME)
    reply_check: ReplyCheck = await signal_structured(system_prompt, plain_conv, ReplyCheck)
    return reply_check.should_reply == "true" and reply_check.confidence > 0.5


async def _active_trigger_should_reply(plaintext: str, wake_words: list[str]) -> bool:
    trigger_text = _active_trigger_content(plaintext, wake_words)
    compact_text = re.sub(r"[\W_]+", "", trigger_text.lower())
    if not compact_text:
        # 仅发送唤醒词或只 @ Bot 时，NoneBot 可能已经把可见文本剥离为空。
        # 这仍然是一次明确的呼唤，应交给 Agent 自然回应。
        return True
    if any(keyword in compact_text for keyword in ACTIVE_TRIGGER_STOP_KEYWORDS):
        return False
    return compact_text not in ACTIVE_TRIGGER_LOW_INFO_PHRASES


async def message_gateway(event: MessageEvent, messages: list) -> bool:
    group_id = event.data.group.group_id if event.data.group else 0
    user_id = _message_gateway_user_id(event)
    if _message_gateway_blocked_by_access_policy(group_id, user_id):
        return False
    if group_id == 0 and (event.is_tome() or event.to_me):
        return True
    segments = getattr(event.data, "segments", [])
    # The adapter's get_plaintext() only includes text segments, not Markdown.
    plaintext = (
        "".join(
            str(segment.get("data", {}).get("content" if segment.get("type") == "markdown" else "text", ""))
            for segment in segments if segment.get("type") in {"text", "markdown"}
        ) if any(segment.get("type") == "markdown" for segment in segments) else event.get_plaintext()
    ).strip()
    wake_words = _get_wake_words(group_id)
    active_triggered = event.is_tome() or event.to_me or any(plaintext.startswith(w) for w in wake_words)
    if active_triggered:
        if group_id != 0:
            return await _active_trigger_should_reply(plaintext, wake_words)
        return True
    auto_reply_allowed = group_id not in EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST and (
        not EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE or group_id in EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST
    )
    if group_id != 0 and auto_reply_allowed:
        return await _reply_check_should_reply(group_id, plaintext, messages)
    return False


def _get_wake_words(group_id: int) -> list[str]:
    """获取群级唤醒词；数据库有自定义值时覆盖 .env 的 NICKNAME。"""
    if group_id == 0:
        return list(EnvConfig.BOT_NICKNAMES)
    words = GroupSettingsManager(get_engine()).get(group_id, "wake_word")
    return words or list(EnvConfig.BOT_NICKNAMES)

