"""
AI插件主文件
包含NoneBot插件的注册和处理逻辑
"""

import base64

import httpx
from git import Repo
from nonebot import logger, on_command, on_message

# from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.adapters.qq import Message, MessageEvent, MessageSegment
from nonebot.adapters.qq.exception import ActionFailed
from nonebot.params import CommandArg

from plugins.frontier.markdown_render import markdown_to_image

from .cognitive import react_agent

# 注册命令处理器
updater = on_command("更新", aliases={"update"}, priority=0, block=True)
trigger = on_command("测试", aliases={"test"}, priority=1, block=True)
common = on_message(priority=5)


@updater.handle()
async def handle_updater(event: MessageEvent):
    repo = Repo(".")
    repo.git.pull(rebase=True)
    await updater.finish("正在更新...")


@trigger.handle()
async def handle_trigger(event: MessageEvent, args: Message = CommandArg()):
    if not args:
        await trigger.finish("请输入参数")

    # 将消息转换为字符串
    arg_str = args.extract_plain_text()
    print(f"收到参数: {arg_str}")
    # 使用 MessageSegment 构建回复消息
    await trigger.finish(MessageSegment.text(f"收到参数: {arg_str}"))


@common.handle()
async def handle_trigger2(event: MessageEvent):
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
    await trigger.send("正在烧烤🔮")

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

                # 可选：向用户显示工具调用信息
                # tool_info = f"🛠️ 使用了工具: {tools_used}"
                # await trigger.send(tool_info)

            # 首先发送所有的 MessageSegment 工件（图片、视频等）
            if message_segments:
                logger.info(f"📤 发送 {len(message_segments)} 个媒体工件")
                for segment in message_segments:
                    await trigger.send(segment)

            # 然后发送文本响应
            if "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                if hasattr(last_message, "content") and last_message.content.strip():
                    if len(last_message.content) > 300:
                        try:
                            result = await markdown_to_image(last_message.content)
                            if result:
                                await trigger.finish(MessageSegment.file_image(result), at_sender=False)
                        except ActionFailed:
                            await trigger.finish("貌似出了点问题")
                    else:
                        try:
                            await trigger.finish(MessageSegment.text(last_message.content))
                        except ActionFailed:
                            result = await markdown_to_image(last_message.content)
                            if result:
                                await trigger.finish(MessageSegment.file_image(result))
                elif not message_segments:  # 只有在没有媒体工件时才发送"没有返回内容"
                    await trigger.finish("处理完成，但没有返回内容")
            elif not message_segments:  # 只有在没有媒体工件时才发送"没有返回内容"
                await trigger.finish("处理完成，但没有返回内容")

        # 兼容旧的返回值格式（字符串）
        elif isinstance(result, str):
            await trigger.finish(result)

        # 兼容旧的返回值格式（直接的响应对象）
        else:
            if hasattr(result, "get") and "messages" in result:
                messages_list = result.get("messages", [])
                if messages_list:  # 确保列表不为空
                    last_message = messages_list[-1]
                    if hasattr(last_message, "content"):
                        await trigger.finish(MessageSegment.text(last_message.content))
                    else:
                        await trigger.finish("处理完成，但没有返回内容")
                else:
                    await trigger.finish("处理完成，但没有返回内容")
            else:
                await trigger.finish("处理完成，但返回格式异常")

    except ActionFailed:
        await trigger.finish("貌似什么东西坏了")
