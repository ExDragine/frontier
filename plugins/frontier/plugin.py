"""
AI插件主文件
包含NoneBot插件的注册和处理逻辑
"""

import base64

import httpx
from git import Repo
from nonebot import logger, on_message, require

from nonebot.adapters.qq import MessageEvent, MessageSegment
from nonebot.adapters.qq.exception import ActionFailed
from plugins.frontier.markdown_render import markdown_to_image

from .cognitive import react_agent

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna, Alconna, UniMessage, Args


# 注册命令处理器 - 使用正确的 Alconna 语法
updater = on_alconna(
    Alconna("更新", ["update"]),
    priority=0,
    block=True
)

debugger = on_alconna(
    Alconna("测试", Args["content", str, "请输入测试内容"], ["test"]),
    priority=1,
    block=True
)

common = on_message(priority=5)


@updater.handle()
async def handle_updater(event: MessageEvent):
    """处理更新命令"""
    try:
        repo = Repo(".")
        repo.git.pull(rebase=True)
        await UniMessage.text("✅ 正在更新...").send(at_sender=False, reply_to=True)
    except Exception as e:
        logger.error(f"更新失败: {e}")
        await UniMessage.text(f"❌ 更新失败: {str(e)}").send(at_sender=False, reply_to=True)


@debugger.handle()
async def handle_debugger(event: MessageEvent, content: str = Args["content"]):
    """处理测试命令"""
    if not content:
        await UniMessage.text("请输入测试内容").send(at_sender=False, reply_to=True)
        return

    logger.info(f"收到测试参数: {content}")
    await UniMessage.text(f"收到参数: {content}").send(at_sender=False, reply_to=True)


@common.handle()
async def handle_common(event: MessageEvent):
    """处理普通消息"""
    message = event.get_message()

    texts = event.get_message().extract_plain_text()
    images = []
    if len(message) > 1:
        for attachment in message:
            if attachment.type == "image":
                if image_url := attachment.data.get("url"):
                    async with httpx.AsyncClient() as client:
                        image = await client.get(image_url)
                        images.append(
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64.b64encode(image.content).decode()}",
                            }
                        )
    messages = [{"role": "user", "content": [{"type": "text", "text": texts}] + images}]
    await common.send("正在烧烤🔮")

    try:
        result = await react_agent(messages)

        # 处理新的返回值结构
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
            tool_calls_summary = result.get("tool_calls_summary")
            message_segments = result.get("message_segments", [])

            # 记录工具调用信息 - 添加空值检查
            if tool_calls_summary and tool_calls_summary.get("total_tool_calls", 0) > 0:
                tools_used = ", ".join(tool_calls_summary.get("tools_used", []))
                logger.info(f"🎯 本次对话使用了 {tool_calls_summary['total_tool_calls']} 个工具: {tools_used}")

            # 首先发送所有的 MessageSegment 工件（图片、视频等）
            if message_segments:
                logger.info(f"📤 发送 {len(message_segments)} 个媒体工件")
                for segment in message_segments:
                    await common.send(segment)

            # 然后发送文本响应
            if "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                if hasattr(last_message, "content") and last_message.content.strip():
                    if len(last_message.content) > 300:
                        try:
                            result = await markdown_to_image(last_message.content)
                            if result:
                                await common.finish(MessageSegment.file_image(result), at_sender=False)
                        except ActionFailed:
                            await common.finish("貌似出了点问题")
                    else:
                        try:
                            await common.finish(MessageSegment.text(last_message.content))
                        except ActionFailed:
                            result = await markdown_to_image(last_message.content)
                            if result:
                                await common.finish(MessageSegment.file_image(result))
                elif not message_segments:  # 只有在没有媒体工件时才发送"没有返回内容"
                    await common.finish("处理完成，但没有返回内容")
            elif not message_segments:  # 只有在没有媒体工件时才发送"没有返回内容"
                await common.finish("处理完成，但没有返回内容")

        # 兼容旧的返回值格式（字符串）
        elif isinstance(result, str):
            await common.finish(result)

        # 兼容旧的返回值格式（直接的响应对象）
        else:
            if hasattr(result, "get") and "messages" in result:
                messages_list = result.get("messages", [])
                if messages_list:  # 确保列表不为空
                    last_message = messages_list[-1]
                    if hasattr(last_message, "content"):
                        await common.finish(MessageSegment.text(last_message.content))
                    else:
                        await common.finish("处理完成，但没有返回内容")
                else:
                    await common.finish("处理完成，但没有返回内容")
            else:
                await common.finish("处理完成，但返回格式异常")

    except ActionFailed:
        await common.finish("貌似什么东西坏了")
