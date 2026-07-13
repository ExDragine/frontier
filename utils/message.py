import ast
import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from langchain.messages import AIMessage
from nonebot import logger
from nonebot.adapters.milky.event import MessageEvent
from nonebot.exception import ActionFailed
from PIL import Image as PILImage
from pydantic import BaseModel, Field

from utils.alconna import Image, UniMessage, Video
from utils.configs import EnvConfig
from utils.context_check import ImageCheck, TextCheck
from utils.database import GroupSettingsManager, MessageDatabase, get_engine
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
        except TypeError, AttributeError:
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


def _active_trigger_content(plaintext: str, wake_words: list[str]) -> str:
    text = plaintext.strip()
    for wake_word in sorted((word for word in wake_words if word), key=len, reverse=True):
        if text.startswith(wake_word):
            return text[len(wake_word) :].strip(ACTIVE_TRIGGER_STRIP_CHARS)
    return text.strip(ACTIVE_TRIGGER_STRIP_CHARS)


def _compact_active_trigger_text(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.lower())


def _active_trigger_has_stop_intent(compact_text: str) -> bool:
    return any(keyword in compact_text for keyword in ACTIVE_TRIGGER_STOP_KEYWORDS)


def _active_trigger_is_low_information(compact_text: str) -> bool:
    return compact_text in ACTIVE_TRIGGER_LOW_INFO_PHRASES


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


def _auto_reply_group_allowed(group_id: int) -> bool:
    if group_id in EnvConfig.AGENT_AUTO_REPLY_BLACKLIST_GROUP_LIST:
        return False
    if EnvConfig.AGENT_AUTO_REPLY_WHITELIST_MODE:
        return group_id in EnvConfig.AGENT_AUTO_REPLY_WHITELIST_GROUP_LIST
    return True


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


async def _active_trigger_should_reply(plaintext: str, wake_words: list[str]) -> bool:
    trigger_text = _active_trigger_content(plaintext, wake_words)
    compact_text = _compact_active_trigger_text(trigger_text)
    if not compact_text:
        return False
    if _active_trigger_has_stop_intent(compact_text):
        return False
    if _active_trigger_is_low_information(compact_text):
        return False
    return True


MediaItem = bytes | bytearray | Callable[[], Awaitable[bytes | None]]
FILE_URL_FIELDS = ("temp_url", "url", "download_url", "download_uri")


@dataclass(frozen=True, slots=True)
class MessageFileItem:
    file_id: str | None
    file_name: str
    file_size: int
    file_hash: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class StagedMessageFile:
    file_name: str
    file_size: int
    virtual_path: str
    local_path: Path


def _media_downloader(url: str, label: str) -> Callable[[], Awaitable[bytes | None]]:
    async def _download() -> bytes | None:
        try:
            return (await httpx_client.get(url)).content
        except Exception as exc:
            logger.warning("下载%s失败: %s", label, exc)
            return None

    return _download


def _first_file_url(data: dict) -> str | None:
    for field in FILE_URL_FIELDS:
        value = data.get(field)
        if value:
            return str(value)
    return None


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except TypeError, ValueError:
        return 0


def extract_message_files(messages: list[dict]) -> list[MessageFileItem]:
    files: list[MessageFileItem] = []
    for message in messages:
        if message.get("type") != "file":
            continue
        msg_data = message.get("data", {})
        file_hash = msg_data.get("file_hash")
        files.append(
            MessageFileItem(
                file_id=str(file_id) if (file_id := msg_data.get("file_id")) else None,
                file_name=str(msg_data.get("file_name") or "file"),
                file_size=_int_or_zero(msg_data.get("file_size")),
                file_hash=str(file_hash) if file_hash is not None else None,
                url=_first_file_url(msg_data),
            )
        )
    return files


async def _message_file_download_url(
    bot,
    file_item: MessageFileItem,
    *,
    user_id: str | int,
    group_id: int | None,
) -> str | None:
    if file_item.url:
        return file_item.url
    if not file_item.file_id:
        return None
    try:
        if group_id is not None:
            return await bot.get_group_file_download_url(group_id=int(group_id), file_id=file_item.file_id)
        if file_item.file_hash is None:
            logger.warning(f"私聊文件缺少 file_hash 字段，无法获取下载链接: {file_item.file_name}")
            return None
        return await bot.get_private_file_download_url(
            user_id=int(user_id),
            file_id=file_item.file_id,
            file_hash=file_item.file_hash,
        )
    except Exception as exc:
        logger.warning(f"获取文件下载链接失败 {file_item.file_name}: {type(exc).__name__}: {exc}")
        return None


async def _download_file_bytes(url: str, file_name: str) -> bytes | None:
    try:
        response = await httpx_client.get(url)
        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            raise_for_status()
        return response.content
    except Exception as exc:
        logger.warning(f"下载文件失败 {file_name}: {type(exc).__name__}: {exc}")
        return None


def _safe_attachment_file_name(file_name: str) -> str:
    safe_name = Path(str(file_name).replace("\\", "/")).name.strip()
    return safe_name or "file"


def _unique_attachment_path(directory: Path, file_name: str) -> Path:
    original = Path(file_name)
    stem = original.stem or "file"
    suffix = original.suffix
    candidate = directory / file_name
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


async def stage_message_files(
    bot,
    file_items: list[MessageFileItem],
    *,
    memory_dir: str | Path,
    workspace_key: str,
    user_id: str | int,
    group_id: int | None,
) -> list[StagedMessageFile]:
    """Download incoming file segments into the agent memory files directory."""
    if not file_items:
        return []

    memory_path = Path(memory_dir)
    files_dir = memory_path / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    staged_files: list[StagedMessageFile] = []

    for file_item in file_items:
        url = await _message_file_download_url(bot, file_item, user_id=user_id, group_id=group_id)
        if not url:
            logger.warning(f"文件缺少可下载链接，无法注入工作区: {file_item.file_name}")
            continue
        file_bytes = await _download_file_bytes(url, file_item.file_name)
        if file_bytes is None:
            continue

        safe_name = _safe_attachment_file_name(file_item.file_name)
        target_path = _unique_attachment_path(files_dir, safe_name)
        target_path.write_bytes(file_bytes)
        virtual_path = f"/memory/{workspace_key}/{target_path.relative_to(memory_path).as_posix()}"
        staged_files.append(
            StagedMessageFile(
                file_name=target_path.name,
                file_size=file_item.file_size,
                virtual_path=virtual_path,
                local_path=target_path,
            )
        )

    return staged_files


def format_staged_message_files(staged_files: list[StagedMessageFile]) -> str:
    lines = []
    for staged_file in staged_files:
        size_label = f" ({staged_file.file_size}字节)" if staged_file.file_size else ""
        lines.append(f"[文件:{staged_file.file_name}{size_label}，已保存到工作区 {staged_file.virtual_path}]")
    return "\n".join(lines)


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
    """发送提取到的工件。多段媒体 UniMessage 拆分为独立消息串行发送。"""

    parallel_tasks = []
    serial_artifacts: list[UniMessage] = []

    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            media_segs = [s for s in artifact if isinstance(s, (Image, Video))]
            if len(media_segs) > 1:
                # 多段媒体：拆为独立 UniMessage，串行发送以保证顺序
                serial_artifacts.extend(UniMessage([seg]) for seg in media_segs)
                continue
        try:
            parallel_tasks.append(asyncio.create_task(artifact.send()))
        except Exception as e:
            logger.exception("创建发送任务失败: %s", e)

    if parallel_tasks:
        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logger.exception("发送工件时发生错误: %s", res)

    for single in serial_artifacts:
        try:
            await single.send()
        except Exception as e:
            logger.exception("发送多段工件时发生错误: %s", e)


def outgoing_message_content(raw: Any) -> str:
    text_attr = getattr(raw, "text", None)
    if text_attr is not None and not callable(text_attr):
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
    return AIMessage(content=sanitized)


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
    if group_id == 0 and (event.is_tome() or event.to_me):
        return True
    plaintext = event.get_plaintext().strip()
    wake_words = _get_wake_words(group_id)
    active_triggered = event.is_tome() or event.to_me or any(plaintext.startswith(w) for w in wake_words)
    if active_triggered:
        if group_id != 0:
            return await _active_trigger_should_reply(plaintext, wake_words)
        return True
    if group_id != 0 and _auto_reply_group_allowed(group_id):
        return await _reply_check_should_reply(group_id, plaintext, messages)
    return False


def _get_wake_words(group_id: int) -> list[str]:
    """获取群级别的唤醒词列表。数据库中有自定义唤醒词时返回，否则 fallback 到 BOT_NAME。"""
    if group_id == 0:
        return [EnvConfig.BOT_NAME]
    words = GroupSettingsManager(get_engine()).get(group_id, "wake_word")
    return words if words else [EnvConfig.BOT_NAME]


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
            image = PILImage.open(BytesIO(image))
            det_result = await image_det.predict(image)
            if det_result == "nsfw":
                return "Unsafe"
    return "Safe"
