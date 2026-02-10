import os
import shutil
import time

# from signal import SIGINT
from git import Repo
from nonebot import get_driver, logger, on_command, require
from nonebot.adapters.milky.event import MessageEvent
from nonebot.permission import SUPERUSER

from plugins.watchtower.environment_check import system_check
from utils.configs import EnvConfig
from utils.memory import get_memory_service
from utils.message import (
    message_extract,
)

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import Target, UniMessage  # noqa: E402

driver = get_driver()
updater = on_command("update", priority=1, block=True, aliases={"更新"}, permission=SUPERUSER)
setting = on_command("model", priority=2, block=True, aliases={"模型", "模型设置"})
memory = get_memory_service()


@driver.on_startup
async def on_startup():
    system_check()
    os.makedirs("./cache", exist_ok=True)
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
    if not os.path.exists("env.toml"):
        shutil.copy("env.toml.example", "env.toml")
    if not os.path.exists("mcp.json"):
        shutil.copy("mcp.json.example", "mcp.json")
    try:
        memory.ensure_schema_ready()
    except Exception as e:
        logger.error(f"❌ memory schema 初始化失败: {type(e).__name__}: {e}")


@driver.on_bot_connect
async def on_bot_connect():
    if os.path.exists(".lock"):
        with open(".lock", encoding="utf-8") as f:
            start_time = f.read()
        os.remove(".lock")
        for group_id in EnvConfig.ANNOUNCE_GROUP_ID:
            await UniMessage.text(f"✅ 更新完成！ 用时{int(time.time() - float(start_time))}秒").send(
                target=Target.group(str(group_id))
            )


@updater.handle()
async def handle_updater(event: MessageEvent):
    """处理更新命令"""
    try:
        logger.info("开始执行更新操作...")
        with open(".lock", "w", encoding="utf-8") as f:
            f.write(str(time.time()))
        await UniMessage.text("🔄 开始更新...").send()

        repo = Repo(".")
        repo.git.checkout()
        pull_result = repo.git.pull(rebase=True)
        logger.info(f"Git pull 结果: {pull_result}")
        # pid = os.getpid()
        # os.kill(pid, SIGINT)

    except Exception as e:
        logger.error(f"更新失败: {e}")
        await UniMessage.text(f"❌ 更新失败: {str(e)}").send()


@setting.handle()
async def handle_setting(event: MessageEvent):
    text, images, *_ = await message_extract(event.data.segments)
    text = text.replace("/model", "")
    if not text:
        await UniMessage.text(
            f"当前默认使用的模型为: {EnvConfig.ADVAN_MODEL}\n当前辅助模型为:{EnvConfig.BASIC_MODEL}\n当前绘图模型为:{EnvConfig.PAINT_MODEL}"
        ).send()
