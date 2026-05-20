import ast
import asyncio
import re
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
from utils.markdown_render import markdown_to_image, markdown_to_text
from utils.signal_llm import signal_structured

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)
text_det = TextCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
image_det = ImageCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
OUTPUT_RISK_BLOCKED_MESSAGE = "这段回复刚才试图表演高危动作，已经被我按住了。换个问法，我们继续。"
MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS = 3
MESSAGE_IMAGE_RENDER_RETRY_DELAY_SECONDS = 0.5


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with true, either reply with false"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


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
                f"消息图片渲染失败，第 {attempt}/{MESSAGE_IMAGE_RENDER_MAX_ATTEMPTS} 次: "
                f"{type(e).__name__}: {e}"
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
    user_id_raw = event.get_user_id()
    try:
        user_id: int | str = int(user_id_raw)
    except ValueError:
        user_id = user_id_raw

    if group_id != 0 and EnvConfig.AGENT_WHITELIST_MODE and group_id not in EnvConfig.AGENT_WHITELIST_GROUP_LIST:
        return False
    if group_id in EnvConfig.AGENT_BLACKLIST_GROUP_LIST:
        return False
    if EnvConfig.AGENT_WHITELIST_MODE and user_id not in EnvConfig.AGENT_WHITELIST_PERSON_LIST:
        return False
    if user_id in EnvConfig.AGENT_BLACKLIST_PERSON_LIST:
        return False
    if event.is_tome() or event.to_me:
        return True
    if event.get_plaintext().startswith(EnvConfig.BOT_NAME):
        return True
    if group_id in EnvConfig.TEST_GROUP_ID:
        reply_check_messages = [
            *messages,
            {"role": "user", "content": str({"metadata": {}, "content": event.get_plaintext().strip()})},
        ]
        temp_conv: list[dict] = reply_check_messages[-5:]
        plain_conv = "\n".join(str(conv.get("content", "")) for conv in temp_conv)
        with open("prompts/reply_check.md", encoding="utf-8") as f:
            system_prompt = f.read().format(name={EnvConfig.BOT_NAME})
        reply_check: ReplyCheck = await signal_structured(system_prompt, plain_conv, ReplyCheck)
        return reply_check.should_reply == "true" and reply_check.confidence > 0.5
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
