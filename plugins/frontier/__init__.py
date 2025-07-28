import base64
import io
import subprocess

import httpx
from git import Repo
from nonebot import logger, on_message, require
from nonebot.internal.adapter import Event
from PIL import Image

from plugins.frontier.markdown_render import markdown_to_image

from .cognitive import intelligent_agent
from .context_check import context_checker

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (  # noqa: E402
    Alconna,
    UniMessage,
    on_alconna,
)

updater = on_alconna(
    Alconna("更新"),
    aliases={"update"},
    priority=1,
    block=True,
    use_cmd_start=True,
)


common = on_message(priority=10)


@updater.handle()
async def handle_updater():
    """处理更新命令"""
    try:
        logger.info("开始执行更新操作...")
        await UniMessage.text("🔄 开始更新...").send()

        repo = Repo(".")
        pull_result = repo.git.pull(rebase=True)
        logger.info(f"Git pull 结果: {pull_result}")
        sync_result = subprocess.run(["uv", "sync"], check=True)  # noqa: S603, S607
        logger.info(f"UV sync 结果: {sync_result}")

        if sync_result.returncode == 0:
            await UniMessage.text("✅ 更新完成！").send()
        else:
            await UniMessage.text(f"⚠️ 依赖同步可能有问题，请检查日志: \n{sync_result.stdout}").send()

    except Exception as e:
        logger.error(f"更新失败: {e}")
        await UniMessage.text(f"❌ 更新失败: {str(e)}").send()


async def message_extract(event: Event):
    message = event.get_message()
    texts = event.get_message().extract_plain_text()
    images = []
    if len(message) > 1:
        for attachment in message:
            if attachment.type == "image":
                if image_url := attachment.data.get("url"):
                    async with httpx.AsyncClient() as client:
                        response = await client.get(image_url)
                        sample = response.content
                        image = Image.open(io.BytesIO(sample))
                        await UniMessage.text(await context_checker(image)).send()
                        images.append(
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64.b64encode(sample).decode()}",
                            }
                        )
    return texts, images


async def send_artifacts(artifacts):
    """发送提取到的工件"""
    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            await artifact.send()


async def send_messages(response: dict):
    last_message = response["messages"][-1]
    if hasattr(last_message, "content") and last_message.content.strip():
        if len(last_message.content) > 300:
            try:
                result = await markdown_to_image(last_message.content)
                if result:
                    await UniMessage.image(raw=result).send()
            except Exception as e:
                await UniMessage.text(f"貌似出了点问题: {e}").send()
        else:
            try:
                await UniMessage.text(last_message.content).send()
            except Exception:
                # await UniMessage.text(f"貌似出了点问题: {e}").send()
                result = await markdown_to_image(last_message.content)
                if result:
                    await UniMessage.image(raw=result).send()


@common.handle()
async def handle_common(event: Event):
    """处理普通消息"""
    user_id = event.get_user_id()
    texts, images = await message_extract(event)
    messages = [{"role": "user", "content": [{"type": "text", "text": texts}]}]
    await common.send("正在烧烤🔮")

    try:
        result = await intelligent_agent(messages, user_id)

        # 处理新的返回值结构
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
            artifacts: list[UniMessage] | None = result.get("uni_messages", [])

            # 首先发送所有的 UniMessage 工件（图片、视频等）
            if artifacts:
                logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
                await send_artifacts(artifacts)

            # 然后发送文本响应
            if "messages" in response and response["messages"]:
                await send_messages(response)

    except Exception as e:
        result = await markdown_to_image(e)
        if result:
            await UniMessage.image(raw=result).send()
            await common.finish("处理过程中发生错误，已生成错误图片")

        await UniMessage.text(f"貌似什么东西坏了: {e}").send()
