import ast
import asyncio
import re
import time
from io import BytesIO
from types import SimpleNamespace
from typing import Any, Literal

import httpx
from nonebot import logger, require
from nonebot.adapters.milky.event import MessageEvent
from nonebot.exception import ActionFailed
from PIL import Image
from pydantic import BaseModel, Field

from utils.configs import EnvConfig
from utils.context_check import ImageCheck, TextCheck
from utils.database import MessageDatabase
from utils.markdown_render import markdown_to_image, markdown_to_text
from utils.signal_llm import signal_structured

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)
messages_db = MessageDatabase()
text_det = TextCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
image_det = ImageCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
OUTPUT_RISK_BLOCKED_MESSAGE = "这段回复刚才试图表演高危动作，已经被我按住了。换个问法，我们继续。"
MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS = 3
MESSAGE_IMAGE_RENDER_RETRY_DELAY_SECONDS = 0.5
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
        elif item_type == "image_url":
            parts.append("[图片]")
        elif item_type:
            parts.append(f"[{item_type}]")
    return "\n".join(part for part in parts if part)


def _reply_check_on_cooldown(group_id: int, now: float) -> bool:
    last_checked_at = _reply_check_last_checked_at.get(group_id)
    return last_checked_at is not None and now - last_checked_at < REPLY_CHECK_GROUP_COOLDOWN_SECONDS


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
    if _reply_check_on_cooldown(group_id, now):
        return False
    _reply_check_last_checked_at[group_id] = now

    reply_check_messages = [
        *messages,
        {"role": "user", "content": str({"metadata": {}, "content": plaintext})},
    ]
    temp_conv: list[dict] = reply_check_messages[-5:]
    plain_conv = "\n".join(_reply_check_content_text(conv.get("content", "")) for conv in temp_conv)
    with open("prompts/reply_check.md", encoding="utf-8") as f:
        system_prompt = f.read().format(name=EnvConfig.BOT_NAME)
    reply_check: ReplyCheck = await signal_structured(system_prompt, plain_conv, ReplyCheck)
    return reply_check.should_reply == "true" and reply_check.confidence > 0.5


async def aclose_http_client() -> None:
    await httpx_client.aclose()


async def message_extract(messages: list[dict]) -> tuple[str, list[bytes], list[bytes], list[bytes]]:
    """提取消息中的文本和媒体内容

    Args:
        messages: 消息段列表,每个消息段包含 type 和 data 字段

    Returns:
        tuple: (文本内容, 图片列表, 语音列表, 视频列表)
    """
    text_parts = []
    images, audio, video = [], [], []

    for message in messages:
        msg_type = message.get("type")
        msg_data = message.get("data", {})

        match msg_type:
            case "text":
                # 文本消息段
                if text_content := msg_data.get("text"):
                    text_parts.append(text_content)

            case "mention":
                # 提及消息段
                if user_id := msg_data.get("user_id"):
                    text_parts.append(f"@{user_id}")

            case "mention_all":
                # 提及全体消息段
                text_parts.append("@全体成员")

            case "face":
                # 表情消息段
                face_id = msg_data.get("face_id", "")
                is_large = msg_data.get("is_large", False)
                face_type = "超级表情" if is_large else "表情"
                text_parts.append(f"[{face_type}:{face_id}]")

            case "reply":
                # 回复消息段
                message_seq = msg_data.get("message_seq")
                if message_seq:
                    text_parts.append(f"[回复消息:{message_seq}]")

            case "image":
                # 图片消息段
                if temp_url := msg_data.get("temp_url"):
                    try:
                        image_content = (await httpx_client.get(temp_url)).content
                        images.append(image_content)
                    except Exception as e:
                        logger.warning(f"下载图片失败: {e}")
                        if summary := msg_data.get("summary"):
                            text_parts.append(f"[图片:{summary}]")

            case "record":
                # 语音消息段
                if temp_url := msg_data.get("temp_url"):
                    try:
                        audio_content = (await httpx_client.get(temp_url)).content
                        audio.append(audio_content)
                    except Exception as e:
                        logger.warning(f"下载语音失败: {e}")
                        duration = msg_data.get("duration", 0)
                        text_parts.append(f"[语音:{duration}秒]")

            case "video":
                # 视频消息段
                if temp_url := msg_data.get("temp_url"):
                    try:
                        video_content = (await httpx_client.get(temp_url)).content
                        video.append(video_content)
                    except Exception as e:
                        logger.warning(f"下载视频失败: {e}")
                        duration = msg_data.get("duration", 0)
                        text_parts.append(f"[视频:{duration}秒]")

            case "file":
                # 文件消息段
                file_name = msg_data.get("file_name", "")
                file_size = msg_data.get("file_size", 0)
                text_parts.append(f"[文件:{file_name} ({file_size}字节)]")

            case "forward":
                # 合并转发消息段
                title = msg_data.get("title", "")
                summary = msg_data.get("summary", "")
                text_parts.append(f"[合并转发:{title} - {summary}]")

            case "market_face":
                # 市场表情消息段
                summary = msg_data.get("summary", "")
                text_parts.append(f"[市场表情:{summary}]")

            case "light_app":
                # 小程序消息段
                app_name = msg_data.get("app_name", "")
                text_parts.append(f"[小程序:{app_name}]")

            case "xml":
                # XML消息段
                service_id = msg_data.get("service_id", "")
                text_parts.append(f"[XML消息:{service_id}]")

            case _:
                # 未知类型
                logger.debug(f"未处理的消息类型: {msg_type}")

    # 合并所有文本部分
    text = "".join(text_parts) if text_parts else ""

    return text, images, audio, video


async def send_artifacts(artifacts):
    """发送提取到的工件（并行发送）"""

    tasks = []
    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            try:
                tasks.append(asyncio.create_task(artifact.send()))
            except Exception as e:
                logger.exception("创建发送任务失败: %s", e)

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            logger.exception("发送工件时发生错误: %s", res)


def outgoing_message_content(raw: Any) -> str:
    text_attr = getattr(raw, "text", None)
    content = str(text_attr) if text_attr is not None else getattr(raw, "content", "")
    if content:
        try:
            content = ast.literal_eval(content)["content"]
        except (ValueError, SyntaxError, KeyError) as e:
            logger.debug(f"消息内容不是字典字面量，使用原始内容: {type(e).__name__}")
        except Exception as e:
            # 意外错误
            logger.warning(f"解析消息内容时出现意外错误: {type(e).__name__}: {e}")
    return str(content or "")


async def sanitize_outgoing_text(content: str | None) -> str | None:
    if not content or not EnvConfig.CONTENT_CHECK_ENABLED:
        return content
    if text_det is None:
        logger.warning("CONTENT_CHECK_ENABLED is True but text detector is None; allowing outgoing text")
        return content

    safe_label, categories = await text_det.predict(content)
    if safe_label == "Unsafe":
        logger.warning(f"⚠️ 模型输出命中文本风险审核，已拦截: {categories}")
        return OUTPUT_RISK_BLOCKED_MESSAGE
    return content


async def sanitize_outgoing_message(raw: Any) -> Any:
    content = outgoing_message_content(raw)
    sanitized = await sanitize_outgoing_text(content)
    if sanitized == content:
        return raw
    return SimpleNamespace(text=sanitized)


async def _markdown_to_image_with_retry(content: str) -> bytes | None:
    last_error: Exception | None = None
    for attempt in range(1, MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS + 1):
        try:
            result = await markdown_to_image(content)
        except Exception as e:
            last_error = e
            logger.warning(
                f"消息图片渲染失败，第 {attempt}/{MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS} 次: {type(e).__name__}: {e}"
            )
        else:
            if result:
                if attempt > 1:
                    logger.info(f"消息图片渲染重试成功，第 {attempt}/{MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS} 次")
                return result
            logger.warning(f"消息图片渲染返回空，第 {attempt}/{MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS} 次")

        if attempt < MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS:
            await asyncio.sleep(MESSAGE_IMAGE_RENDER_RETRY_DELAY_SECONDS * attempt)

    if last_error is not None:
        logger.error(f"消息图片渲染最终失败: {type(last_error).__name__}: {last_error}")
    return None


async def send_messages(group_id: int | None, message_id, response: dict[str, list]):
    raw = response["messages"][-1]
    content = outgoing_message_content(raw)
    if content:
        pattern = re.compile(r"\$(.*?)\$")
        matches = pattern.findall(content)
        if len(content) < 500 or group_id in EnvConfig.RAW_MESSAGE_GROUP_ID and not matches:
            text_content = (await markdown_to_text(content)).rstrip("\r\n").strip()
            messages = (
                UniMessage.reply(str(message_id)) + UniMessage.text(text_content)
                if group_id
                else UniMessage.text(text_content)
            )
            try:
                await messages.send()
                return
            except ActionFailed as e:
                logger.warning(f"文本消息发送失败，尝试图片回退: {e}")

        result = await _markdown_to_image_with_retry(content)
        if not result:
            logger.error(f"图片生成失败 (内容长度: {len(content)})")
            # 尝试发送错误提示
            try:
                fallback_msg = UniMessage.reply(str(message_id)) + UniMessage.text("❌ 消息生成失败，请稍后重试。")
                await fallback_msg.send()
            except ActionFailed as e:
                logger.error(f"错误消息发送失败: {e}")
            return
        messages = (
            UniMessage.reply(str(message_id)) + UniMessage.image(raw=result)
            if group_id
            else UniMessage.image(raw=result)
        )
        try:
            await messages.send()
        except ActionFailed as e:
            logger.error(f"图片消息发送失败: {e}")


async def message_gateway(event: MessageEvent, messages: list):
    group_id = event.data.group.group_id if event.data.group else 0
    user_id = _message_gateway_user_id(event)
    if _message_gateway_blocked_by_access_policy(group_id, user_id):
        return False
    if event.is_tome() or event.to_me:
        return True
    plaintext = event.get_plaintext().strip()
    if plaintext.startswith(EnvConfig.BOT_NAME):
        return True
    if group_id in EnvConfig.TEST_GROUP_ID:
        return await _reply_check_should_reply(group_id, plaintext, messages)
    return False


async def message_check(text: str | None, images: list | None) -> Literal["Safe", "Controversial", "Unsafe"]:
    if not EnvConfig.CONTENT_CHECK_ENABLED:
        return "Safe"
    if text_det is None or image_det is None:
        logger.warning("CONTENT_CHECK_ENABLED is True but detectors are None; returning Safe")
        return "Safe"
    if text:
        safe_label, categories = await text_det.predict(text)
        return safe_label
    if images:
        for image in images:
            image = Image.open(BytesIO(image))
            det_result = await image_det.predict(image)
            if det_result == "nsfw":
                return "Unsafe"
    return "Safe"
