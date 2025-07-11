"""
AI插件主文件
包含NoneBot插件的注册和处理逻辑
"""

import os

from git import Repo
from nonebot import logger, on_message, require
from nonebot.internal.adapter import Event

from plugins.frontier.markdown_render import markdown_to_image

from .cognitive import react_agent

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (  # noqa: E402
    Alconna,
    UniMessage,
    on_alconna,
)

# 修复命令注册 - 使用正确的 Alconna 语法
updater = on_alconna(
    Alconna("更新"),  # 简化命令定义
    aliases={"update"},  # 使用 aliases 参数添加别名
    priority=1,  # 调整优先级，使其高于普通消息处理器
    block=True,
    use_cmd_start=True,  # 启用命令前缀
)

# 或者使用字符串形式的命令定义（推荐）
# updater = on_alconna(
#     "更新",
#     aliases={"update"},
#     priority=1,
#     block=True,
#     use_cmd_start=True
# )

common = on_message(priority=10)


@updater.handle()
async def handle_updater():
    """处理更新命令"""
    try:
        logger.info("开始执行更新操作...")
        await UniMessage.text("🔄 开始更新...").send()

        # 执行 git pull
        repo = Repo(".")
        pull_result = repo.git.pull(rebase=True)
        logger.info(f"Git pull 结果: {pull_result}")

        # 执行同步依赖
        sync_result = os.system("uv sync")
        logger.info(f"UV sync 结果: {sync_result}")

        if sync_result == 0:  # 检查命令执行结果
            await UniMessage.text("✅ 更新完成！").send()
        else:
            await UniMessage.text("⚠️ 依赖同步可能有问题，请检查日志").send()

    except Exception as e:
        logger.error(f"更新失败: {e}")
        await UniMessage.text(f"❌ 更新失败: {str(e)}").send()


@common.handle()
async def handle_common(event: Event):
    """处理普通消息"""
    # message = event.get_message()
    texts = event.get_message().extract_plain_text()
    images = []
    # if len(message) > 1:
    #     for attachment in message:
    #         if attachment.type == "image":
    #             if image_url := attachment.data.get("url"):
    #                 async with httpx.AsyncClient() as client:
    #                     image = await client.get(image_url)
    #                     images.append(
    #                         {
    #                             "type": "image_url",
    #                             "image_url": f"data:image/jpeg;base64,{base64.b64encode(image.content).decode()}",
    #                         }
    #                     )
    messages = [{"role": "user", "content": [{"type": "text", "text": texts}] + images}]
    await common.send("正在烧烤🔮")

    try:
        result = await react_agent(messages)

        # 处理新的返回值结构
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
            tool_calls_summary = result.get("tool_calls_summary")
            artifacts: list[UniMessage] | None = result.get("uni_messages", [])

            # 记录工具调用信息 - 添加空值检查
            if tool_calls_summary and tool_calls_summary.get("total_tool_calls", 0) > 0:
                tools_used = ", ".join(tool_calls_summary.get("tools_used", []))
                logger.info(f"🎯 本次对话使用了 {tool_calls_summary['total_tool_calls']} 个工具: {tools_used}")

            # 首先发送所有的 UniMessage 工件（图片、视频等）
            if artifacts:
                logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
                for artifact in artifacts:
                    if isinstance(artifact, UniMessage):
                        # 发送 UniMessage 工件
                        await artifact.send()

            # 然后发送文本响应
            if "messages" in response and response["messages"]:
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
                elif not artifacts:  # 只有在没有媒体工件时才发送"没有返回内容"
                    await common.finish("处理完成，但没有返回内容")
            elif not artifacts:  # 只有在没有媒体工件时才发送"没有返回内容"
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
                        await UniMessage.text(last_message.content).send()
                    else:
                        await common.finish("处理完成，但没有返回内容")
                else:
                    await common.finish("处理完成，但没有返回内容")
            else:
                await common.finish("处理完成，但返回格式异常")

    except Exception as e:
        result = await markdown_to_image(e)
        if result:
            await UniMessage.image(raw=result).send()
            await common.finish("处理过程中发生错误，已生成错误图片")

        await UniMessage.text(f"貌似什么东西坏了: {e}").send()
