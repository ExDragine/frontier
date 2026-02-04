import ast
import asyncio
from io import BytesIO

import httpx
from nonebot import logger, require
from nonebot.adapters.milky.event import MessageEvent
from nonebot.exception import ActionFailed
from PIL import Image
from pydantic import BaseModel, Field

from utils.agents import assistant_agent
from utils.configs import EnvConfig
from utils.context_check import ImageCheck, TextCheck
from utils.markdown_render import markdown_to_image, markdown_to_text

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)
text_det = TextCheck()
image_det = ImageCheck()


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with true, either reply with false"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


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


async def send_messages(group_id: int | None, message_id, response: dict[str, list]):
    if content := response["messages"][-1].content:
        try:
            content = ast.literal_eval(content)["content"]
        except (ValueError, SyntaxError, KeyError) as e:
            # Content不是字典字面量，使用原始内容
            logger.debug(f"消息内容不是字典字面量，使用原始内容: {type(e).__name__}")
        except Exception as e:
            # 意外错误
            logger.warning(f"解析消息内容时出现意外错误: {type(e).__name__}: {e}")

        should_send_text = len(content) < 500 or group_id in EnvConfig.RAW_MESSAGE_GROUP_ID
        if should_send_text:
            text_content = (await markdown_to_text(content)).rstrip("\r\n").strip()
            messages = UniMessage.reply(str(message_id)) + UniMessage.text(text_content)
            try:
                await messages.send()
                return
            except ActionFailed as e:
                logger.warning(f"文本消息发送失败，尝试图片回退: {e}")

        result = await markdown_to_image(content)
        if not result:
            logger.error(f"图片生成失败 (内容长度: {len(content)})")
            # 尝试发送错误提示
            try:
                fallback_msg = UniMessage.reply(str(message_id)) + UniMessage.text("❌ 消息生成失败，请稍后重试。")
                await fallback_msg.send()
            except ActionFailed as e:
                logger.error(f"错误消息发送失败: {e}")
            return

        messages = UniMessage.reply(str(message_id)) + UniMessage.image(raw=result)
        try:
            await messages.send()
        except ActionFailed as e:
            logger.error(f"图片消息发送失败: {e}")
            # 最后尝试发送截断的文本
            try:
                text_content = (await markdown_to_text(content)).rstrip("\r\n").strip()
                truncated = text_content[:500] + "..." if len(text_content) > 500 else text_content
                fallback = UniMessage.reply(str(message_id)) + UniMessage.text(truncated)
                await fallback.send()
            except Exception as final_e:
                logger.error(f"所有消息发送尝试都失败: {final_e}")


async def message_gateway(event: MessageEvent, messages: list):
    group_id = event.data.group.group_id if event.data.group else 0
    user_id = event.get_user_id()

    if EnvConfig.AGENT_WITHELIST_MODE and group_id in EnvConfig.AGENT_WITHELIST_GROUP_LIST:
        pass
    if group_id in EnvConfig.AGENT_BLACKLIST_GROUP_LIST:
        return False
    if EnvConfig.AGENT_WITHELIST_MODE and user_id in EnvConfig.AGENT_WITHELIST_PERSON_LIST:
        pass
    if user_id in EnvConfig.AGENT_BLACKLIST_PERSON_LIST:
        return False
    if event.is_tome() or event.to_me:
        return True
    if event.get_plaintext().startswith(EnvConfig.BOT_NAME):
        return True
    if group_id in EnvConfig.TEST_GROUP_ID:
        messages.append({"role": "user", "content": str({"metadata": {}, "content": event.get_plaintext().strip()})})
        temp_conv: list[dict] = messages[-5:]
        plain_conv = "\n".join(str(conv.get("content", "")) for conv in temp_conv)
        with open("prompts/reply_check.txt", encoding="utf-8") as f:
            system_prompt = f.read().format(name={EnvConfig.BOT_NAME})
        reply_check: ReplyCheck = await assistant_agent(system_prompt, plain_conv, response_format=ReplyCheck)
        return reply_check.should_reply == "true" and reply_check.confidence > 0.5
    return False


async def message_check(text: str | None, images: list | None) -> bool:
    if text:
        safe_label, categories = await text_det.predict(text)
        if safe_label != "Safe":
            warning_msg = (
                f"⚠️ 该消息被检测为 {safe_label}，涉及类别: {', '.join(categories) if categories else '未知'}。"
            )
            logger.info(warning_msg)
            return False
        return True
    if images:
        for image in images:
            image = Image.open(BytesIO(image))
            det_result = await image_det.predict(image)
            if det_result == "nsfw":
                logger.info("检测到瑟瑟")
                return False
    return True
