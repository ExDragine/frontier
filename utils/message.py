import ast
import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from io import BytesIO
from typing import Any, Literal

from nonebot import logger
from PIL import Image as PILImage

from utils.alconna import Image, UniMessage, Video
from utils.configs import EnvConfig
from utils.context_check import ImageCheck, TextCheck
from utils.delivery import DeliveryResult
from utils.http_client import get_http_client
from utils.markdown_render import markdown_to_image, markdown_to_text

httpx_client = get_http_client("message")
text_det: TextCheck | None = None
image_det: ImageCheck | None = None
_text_det_lock = asyncio.Lock()
_image_det_lock = asyncio.Lock()
_text_det_retry_at = 0.0
_image_det_retry_at = 0.0
CONTENT_CHECK_RETRY_COOLDOWN_SECONDS = 60.0
OUTPUT_RISK_BLOCKED_MESSAGE = "这段回复刚才试图表演高危动作，已经被我按住了。换个问法，我们继续。"
MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS = 3
MESSAGE_IMAGE_RENDER_RETRY_DELAY_SECONDS = 0.5
MESSAGE_IMAGE_RENDER_TEXT_LENGTH_THRESHOLD = 500
_RICH_MARKDOWN_FENCE_RE = re.compile(r"(?im)^\s*```+\s*(?:chart|stats|timeline)\b")
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
            _RICH_MARKDOWN_FENCE_RE,
        )
    )


def _message_should_render_as_image(content: str) -> bool:
    if _message_has_hard_to_text_content(content):
        return True
    return len(content) >= MESSAGE_IMAGE_RENDER_TEXT_LENGTH_THRESHOLD


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
        tasks.extend((bucket_index, _resolve_media_item(item)) for item in bucket)

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
            case "markdown":
                if content := msg_data.get("content"):
                    text_parts.append(content)

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


def _artifact_messages(artifact: UniMessage) -> list[UniMessage]:
    """Split multiple media while preserving every caption and segment in order."""
    if sum(isinstance(segment, (Image, Video)) for segment in artifact) <= 1:
        return [artifact]
    messages: list[UniMessage] = []
    segments = []
    has_media = False
    for segment in artifact:
        is_media = isinstance(segment, (Image, Video))
        if is_media and has_media:
            messages.append(UniMessage(segments))
            segments = []
        segments.append(segment)
        has_media = has_media or is_media
    if segments:
        messages.append(UniMessage(segments))
    return messages


async def send_artifacts(artifacts: list[object]) -> DeliveryResult:
    """Send typed artifacts serially; stop after a failure to preserve ordering."""
    result = DeliveryResult()
    for artifact in artifacts:
        if not isinstance(artifact, UniMessage):
            logger.warning("忽略不可发送的工具工件类型: %s", type(artifact).__name__)
            continue
        for message in _artifact_messages(artifact):
            if not message:
                continue
            try:
                await message.send()
            except Exception as exc:
                logger.exception("工件发送失败: %s", type(exc).__name__)
                return result.combine(DeliveryResult(attempted=1, errors=(type(exc).__name__,)))
            result = result.combine(DeliveryResult(attempted=1, sent=1))
    return result


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
    detector = await _get_text_detector()
    if detector is None:
        return content

    try:
        safe_label, categories = await detector.predict(content)
    except Exception as e:
        _mark_text_detector_failed()
        logger.exception(f"文本内容检查失败，已按放行策略处理: {type(e).__name__}: {e}")
        return content
    if safe_label == "Unsafe":
        logger.warning(f"⚠️ 模型输出命中文本风险审核，已拦截: {categories}")
        return OUTPUT_RISK_BLOCKED_MESSAGE
    return content


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


def _receipt_message_ids(receipt: object) -> tuple[int, ...]:
    """Read Milky message sequences without letting an absent receipt retry a send."""
    sequences = []
    for result in getattr(receipt, "msg_ids", None) or []:
        sequence = getattr(result, "message_seq", None)
        if isinstance(sequence, int) and not isinstance(sequence, bool):
            sequences.append(sequence)
    return tuple(sequences)


async def send_messages(group_id: int | None, message_id, response: dict[str, list]) -> DeliveryResult:
    """Deliver final text or its rendered image and report only actual content delivery."""
    raw_messages = response.get("messages", [])
    if not raw_messages:
        return DeliveryResult()
    content = outgoing_message_content(raw_messages[-1])
    if not content:
        return DeliveryResult()

    def with_reply(message: UniMessage) -> UniMessage:
        return UniMessage.reply(str(message_id)) + message if group_id is not None else message

    if not _message_should_render_as_image(content):
        try:
            text_content = (await markdown_to_text(content)).rstrip("\r\n").strip()
            receipt = await with_reply(UniMessage.text(text_content)).send()
            return DeliveryResult(attempted=1, sent=1, message_ids=_receipt_message_ids(receipt))
        except Exception as exc:
            logger.warning("文本消息发送失败，尝试图片回退: %s", type(exc).__name__)

    result = await _markdown_to_image_with_retry(content)
    if not result:
        logger.error("图片生成失败 (内容长度: %s)", len(content))
        errors = ("render_failed",)
        try:
            await with_reply(UniMessage.text("❌ 消息生成失败，请稍后重试。")).send()
        except Exception as exc:
            logger.error("错误消息发送失败: %s", type(exc).__name__)
            errors += (type(exc).__name__,)
        return DeliveryResult(attempted=1, errors=errors)
    try:
        receipt = await with_reply(UniMessage.image(raw=result)).send()
    except Exception as exc:
        logger.error("图片消息发送失败: %s", type(exc).__name__)
        return DeliveryResult(attempted=1, errors=(type(exc).__name__,))
    return DeliveryResult(attempted=1, sent=1, message_ids=_receipt_message_ids(receipt))


async def _get_text_detector() -> TextCheck | None:
    global text_det, _text_det_retry_at
    if not EnvConfig.CONTENT_CHECK_ENABLED:
        return None
    if text_det is not None:
        return text_det
    if time.monotonic() < _text_det_retry_at:
        return None
    async with _text_det_lock:
        if text_det is not None:
            return text_det
        if time.monotonic() < _text_det_retry_at:
            return None
        try:
            text_det = await asyncio.to_thread(TextCheck)
        except Exception as e:
            _text_det_retry_at = time.monotonic() + CONTENT_CHECK_RETRY_COOLDOWN_SECONDS
            logger.exception(f"文本内容检查模型加载失败，已按放行策略处理: {type(e).__name__}: {e}")
            return None
        _text_det_retry_at = 0.0
        return text_det


async def _get_image_detector() -> ImageCheck | None:
    global image_det, _image_det_retry_at
    if not EnvConfig.CONTENT_CHECK_ENABLED:
        return None
    if image_det is not None:
        return image_det
    if time.monotonic() < _image_det_retry_at:
        return None
    async with _image_det_lock:
        if image_det is not None:
            return image_det
        if time.monotonic() < _image_det_retry_at:
            return None
        try:
            image_det = await asyncio.to_thread(ImageCheck)
        except Exception as e:
            _image_det_retry_at = time.monotonic() + CONTENT_CHECK_RETRY_COOLDOWN_SECONDS
            logger.exception(f"图片内容检查模型加载失败，已按放行策略处理: {type(e).__name__}: {e}")
            return None
        _image_det_retry_at = 0.0
        return image_det


def _mark_text_detector_failed() -> None:
    global text_det, _text_det_retry_at
    text_det = None
    _text_det_retry_at = time.monotonic() + CONTENT_CHECK_RETRY_COOLDOWN_SECONDS


def _mark_image_detector_failed() -> None:
    global image_det, _image_det_retry_at
    image_det = None
    _image_det_retry_at = time.monotonic() + CONTENT_CHECK_RETRY_COOLDOWN_SECONDS


async def message_check(text: str | None, images: list[bytes] | None) -> Literal["Safe", "Controversial", "Unsafe"]:
    if not EnvConfig.CONTENT_CHECK_ENABLED:
        return "Safe"
    if text:
        detector = await _get_text_detector()
        if detector is None:
            return "Safe"
        try:
            safe_label, _categories = await detector.predict(text)
            return safe_label
        except Exception as e:
            _mark_text_detector_failed()
            logger.exception(f"文本内容检查失败，已按放行策略处理: {type(e).__name__}: {e}")
            return "Safe"
    if images:
        detector = await _get_image_detector()
        if detector is None:
            return "Safe"
        for image in images:
            try:
                image = PILImage.open(BytesIO(image))
                det_result = await detector.predict(image)
            except Exception as e:
                _mark_image_detector_failed()
                logger.exception(f"图片内容检查失败，已按放行策略处理: {type(e).__name__}: {e}")
                return "Safe"
            if det_result == "nsfw":
                return "Unsafe"
    return "Safe"
