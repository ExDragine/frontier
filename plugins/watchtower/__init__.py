import os

import dotenv
from git import Repo
from nonebot import get_driver, logger, on_command, require
from nonebot.internal.adapter import Event
from nonebot.permission import SUPERUSER

from plugins.watchtower.environment_check import system_check
from utils.config import EnvConfig
from utils.message import (
    message_extract,
)

dotenv.load_dotenv()
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import Target, UniMessage  # noqa: E402

driver = get_driver()
updater = on_command("更新", priority=1, block=True, aliases={"update"}, permission=SUPERUSER)
setting = on_command("model", priority=2, block=True, aliases={"模型", "模型设置"})


@driver.on_startup
async def on_startup():
    system_check()
    os.makedirs("./cache", exist_ok=True)


@driver.on_bot_connect
async def on_bot_connect():
    if os.path.exists(".lock"):
        os.remove(".lock")
        for group_id in EnvConfig.ANNOUNCE_GROUP_ID:
            await UniMessage.text("✅ 更新完成！").send(target=Target.group(str(group_id)))


@updater.handle()
async def handle_updater(event: Event):
    """处理更新命令"""
    try:
        logger.info("开始执行更新操作...")
        with open(".lock", "w") as f:
            f.write("lock")
        await UniMessage.text("🔄 开始更新...").send()

        repo = Repo(".")
        repo.git.checkout()
        pull_result = repo.git.pull(rebase=True)
        logger.info(f"Git pull 结果: {pull_result}")
        exit(0)

    except Exception as e:
        logger.error(f"更新失败: {e}")
        await UniMessage.text(f"❌ 更新失败: {str(e)}").send()


@setting.handle()
async def handle_setting(event: Event):
    text, images = await message_extract(event)
    text = text.replace("/model", "")
    if not text:
        await UniMessage.text(
            f"当前默认使用的模型为: {EnvConfig.OPENAI_MODEL}\n当前辅助模型为:{EnvConfig.BASIC_MODEL}\n当前绘图模型为:{EnvConfig.PAINT_MODEL}"
        ).send()
