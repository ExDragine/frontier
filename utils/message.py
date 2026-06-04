import ast
import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from io import BytesIO
from types import SimpleNamespace
from typing import Any, Literal

from nonebot import logger
from nonebot.adapters.milky.event import MessageEvent
from nonebot.exception import ActionFailed
from PIL import Image
from pydantic import BaseModel, Field

from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.context_check import ImageCheck, TextCheck
from utils.database import MessageDatabase
from utils.http_client import get_http_client
from utils.markdown_render import markdown_to_image, markdown_to_text
from utils.signal_llm import signal_structured

httpx_client = get_http_client("message")
messages_db = MessageDatabase()
text_det = TextCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
image_det = ImageCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
OUTPUT_RISK_BLOCKED_MESSAGE = "这段回复刚才试图表演高危动作，已经被我按住了。换个问法，我们继续。"
MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS = 3
MESSAGE_IMAGE_RENDER_RETRY_DELAY_SECONDS = 0.5
MESSAGE_IMAGE_RENDER_TEXT_LENGTH_THRESHOLD = 500
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
_BLOCK_MATH_RE = re.compile(r"(?<!\\)\$\$(?!\$).+?(?<!\\)\$\$", re.DOTALL)
_INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?![\s\d$])[^$\n]+?(?<!\\)\$(?!\w)")
_LATEX_DELIMITED_MATH_RE = re.compile(r"\\\[(.|\n)+?\\\]|\\\((.|\n)+?\\\)")
_LATEX_COMMAND_RE = re.compile(
    r"\\(?:"
    r"alpha|beta|gamma|delta|theta|lambda|mu|pi|sigma|Delta|Omega|"
    r"frac|sqrt|sum|prod|int|lim|begin\{(?:equation|align|matrix|pmatrix|bmatrix|cases)\}"
    r")\b"
)
_MARKDOWN_TABLE_RE = re.compile(r"(?m)^\s*\|?.+\|.+\|?\s*\n\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_MERMAID_FENCE_RE = re.compile(r"(?im)^\s*```+\s*mermaid\b")
_MERMAID_DIAGRAM_RE = re.compile(
    r"(?im)"
    r"^\s*(?:graph|flowchart)\s+(?:TB|TD|BT|RL|LR)\b|"
    r"^\s*(?:sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|gantt|journey|gitGraph|mindmap|timeline)\b|"
    r"^\s*pie\s+(?:title\b)?.*"
)


_TEXT_CONTENT_BLOCK_TYPES = {"text", "output_text"}


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with true, either reply with false"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


def extract_message_text(content: Any) -> str:
    """从消息 content 中提取纯文本（str / content blocks / 对象）。"""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        item_type = content.get("type")
        if item_type in _TEXT_CONTENT_BLOCK_TYPES or (item_type is None and "text" in content):
            return str(content.get("text", ""))
        if "content" in content:
            return extract_message_text(content.get("content"))
        return "" if item_type is not None else str(content or "")
    if isinstance(content, list):
        return "\n".join(part for item in content if (part := extract_message_text(item)))

    text = getattr(content, "text", None)
    if callable(text):
        try:
            text = text()
        except TypeError:
            text = None
    if text:
        return extract_message_text(text)
    if hasattr(content, "content"):
        return extract_message_text(content.content)
    return str(content or "")


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


def _message_has_hard_to_text_content(content: str) -> bool:
    return any(
        pattern.search(content)
        for pattern in (
            _BLOCK_MATH_RE,
            _INLINE_MATH_RE,
            _LATEX_DELIMITED_MATH_RE,
            _LATEX_COMMAND_RE,
            _MARKDOWN_TABLE_RE,
            _MERMAID_FENCE_RE,
            _MERMAID_DIAGRAM_RE,
        )
    )


def _message_should_render_as_image(content: str) -> bool:
    if _message_has_hard_to_text_content(content):
        return True
    return len(content) >= MESSAGE_IMAGE_RENDER_TEXT_LENGTH_THRESHOLD


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


MediaItem = bytes | bytearray | Callable[[], Awaitable[bytes | None]]


def _media_downloader(url: str, label: str) -> Callable[[], Awaitable[bytes | None]]:
    async def _download() -> bytes | None:
        try:
            return (await httpx_client.get(url)).content
        except Exception as exc:
            logger.warning("下载%s失败: %s", label, exc)
            return None

    return _download


async def _resolve_media_item(item: MediaItem) -> bytes | None:
    if isinstance(item, bytes):
        return item
    if isinstance(item, bytearray):
        return bytes(item)
    if callable(item):
        try:
            return await item()
        except Exception as exc:
            logger.warning("下载媒体失败: %s: %s", type(exc).__name__, exc)
            return None
    logger.debug("忽略未知媒体项类型: %s", type(item).__name__)
    return None


async def download_media(
    image_items: list[MediaItem] | None = None,
    audio_items: list[MediaItem] | None = None,
    video_items: list[MediaItem] | None = None,
) -> tuple[list[bytes], list[bytes], list[bytes]]:
    """并行解析 message_extract 返回的 lazy 媒体项。

    兼容旧调用方测试桩直接返回 bytes 的情况；真实消息中通常是 async callable。
    """
    results: tuple[list[bytes], list[bytes], list[bytes]] = ([], [], [])
    buckets = (image_items or [], audio_items or [], video_items or [])
    tasks: list[tuple[int, Awaitable[bytes | None]]] = []

    for bucket_index, bucket in enumerate(buckets):
        for item in bucket:
            tasks.append((bucket_index, _resolve_media_item(item)))

    if not tasks:
        return results

    resolved = await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
    for (bucket_index, _task), value in zip(tasks, resolved, strict=True):
        if isinstance(value, Exception):
            logger.warning("下载媒体失败: %s: %s", type(value).__name__, value)
            continue
        if value and isinstance(value, bytes):
            results[bucket_index].append(value)
    return results


async def message_extract(  # noqa: C901
    messages: list[dict],
) -> tuple[str, list[MediaItem], list[MediaItem], list[MediaItem]]:
    """提取消息中的文本和媒体内容。

    Args:
        messages: 消息段列表,每个消息段包含 type 和 data 字段

    Returns:
        tuple: (文本内容, image_downloaders, audio_downloaders, video_downloaders)
        媒体项是 async callable，调用后返回 bytes 或 None。
        调用方应在网关通过后再下载媒体，避免浪费带宽。
    """
    text_parts: list[str] = []
    image_downloaders: list[MediaItem] = []
    audio_downloaders: list[MediaItem] = []
    video_downloaders: list[MediaItem] = []

    for message in messages:
        msg_type = message.get("type")
        msg_data = message.get("data", {})

        match msg_type:
            case "text":
                if text_content := msg_data.get("text"):
                    text_parts.append(text_content)

            case "mention":
                if user_id := msg_data.get("user_id"):
                    text_parts.append(f"@{user_id}")

            case "mention_all":
                text_parts.append("@全体成员")

            case "face":
                face_id = msg_data.get("face_id", "")
                is_large = msg_data.get("is_large", False)
                face_type = "超级表情" if is_large else "表情"
                text_parts.append(f"[{face_type}:{face_id}]")

            case "reply":
                message_seq = msg_data.get("message_seq")
                if message_seq:
                    text_parts.append(f"[回复消息:{message_seq}]")

            case "image":
                if temp_url := msg_data.get("temp_url"):
                    image_downloaders.append(_media_downloader(temp_url, "图片"))
                elif summary := msg_data.get("summary"):
                    text_parts.append(f"[图片:{summary}]")

            case "record":
                if temp_url := msg_data.get("temp_url"):
                    audio_downloaders.append(_media_downloader(temp_url, "语音"))
                else:
                    duration = msg_data.get("duration", 0)
                    text_parts.append(f"[语音:{duration}秒]")

            case "video":
                if temp_url := msg_data.get("temp_url"):
                    video_downloaders.append(_media_downloader(temp_url, "视频"))
                else:
                    duration = msg_data.get("duration", 0)
                    text_parts.append(f"[视频:{duration}秒]")

            case "file":
                file_name = msg_data.get("file_name", "")
                file_size = msg_data.get("file_size", 0)
                text_parts.append(f"[文件:{file_name} ({file_size}字节)]")

            case "forward":
                title = msg_data.get("title", "")
                summary = msg_data.get("summary", "")
                text_parts.append(f"[合并转发:{title} - {summary}]")

            case "market_face":
                summary = msg_data.get("summary", "")
                text_parts.append(f"[市场表情:{summary}]")

            case "light_app":
                app_name = msg_data.get("app_name", "")
                text_parts.append(f"[小程序:{app_name}]")

            case "xml":
                service_id = msg_data.get("service_id", "")
                text_parts.append(f"[XML消息:{service_id}]")

            case _:
                logger.debug(f"未处理的消息类型: {msg_type}")

    text = "".join(text_parts) if text_parts else ""

    return text, image_downloaders, audio_downloaders, video_downloaders


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
    if callable(text_attr):
        try:
            content = text_attr()
        except TypeError:
            content = None
        if not content and hasattr(raw, "content"):
            content = raw.content
    elif text_attr:
        content = text_attr
    elif hasattr(raw, "content"):
        content = raw.content
    else:
        content = raw
    if isinstance(content, str) and content:
        try:
            parsed = ast.literal_eval(content)
            if isinstance(parsed, dict) and "content" in parsed:
                content = parsed["content"]
        except (ValueError, SyntaxError) as e:
            logger.debug(f"消息内容不是字典字面量，使用原始内容: {type(e).__name__}")
        except Exception as e:
            # 意外错误
            logger.warning(f"解析消息内容时出现意外错误: {type(e).__name__}: {e}")
    return extract_message_text(content)


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
        if not _message_should_render_as_image(content):
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


async def message_gateway(event: MessageEvent, messages: list) -> bool:
    group_id = event.data.group.group_id if event.data.group else 0
    user_id = _message_gateway_user_id(event)
    if _message_gateway_blocked_by_access_policy(group_id, user_id):
        return False
    if event.is_tome() or event.to_me:
        return True
    plaintext = event.get_plaintext().strip()
    if plaintext.startswith(EnvConfig.BOT_NAME):
        return True
    if group_id != 0:
        return await _reply_check_should_reply(group_id, plaintext, messages)
    return False


async def message_check(text: str | None, images: list[bytes] | None) -> Literal["Safe", "Controversial", "Unsafe"]:
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
