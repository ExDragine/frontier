import os
import shutil
import subprocess
import time
from signal import SIGINT

from git import Repo
from nonebot import get_driver, logger, on_command
from nonebot.adapters.milky.event import MessageEvent
from nonebot.permission import SUPERUSER

from utils.alconna import Target, UniMessage
from utils.configs import EnvConfig
from utils.message import (
    message_extract,
)

driver = get_driver()
updater = on_command("update", priority=1, block=True, aliases={"更新"}, permission=SUPERUSER)
setting = on_command("model", priority=2, block=True, aliases={"模型", "模型设置"}, permission=SUPERUSER)

SKILL_CREATOR_URL = "https://gh-proxy.org/https://github.com/anthropics/skills.git"
SKILL_CREATOR_PATH = os.path.join(".", "cache", "sandbox", "skills", "skill-creator")


def clone_skill_creator():
    """将 anthropics/skills 仓库中的 skill-creator 克隆到 skills 目录。"""
    target = os.path.abspath(SKILL_CREATOR_PATH)
    if os.path.exists(target):
        logger.info("skill-creator 已存在，跳过克隆")
        return

    logger.info("正在克隆 skill-creator...")
    temp_dir = os.path.join(os.path.abspath("cache/sandbox"), ".skills-temp")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", SKILL_CREATOR_URL, temp_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        source = os.path.join(temp_dir, "skills", "skill-creator")
        if os.path.exists(source):
            shutil.copytree(source, target)
            logger.info("skill-creator 克隆完成")
        else:
            logger.warning(f"skill-creator 子目录不存在于仓库中: {source}")
    except subprocess.CalledProcessError as e:
        logger.error(f"克隆 skill-creator 失败: {e.stderr}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@driver.on_startup
async def on_startup():
    os.makedirs("./cache", exist_ok=True)
    os.makedirs("./sandbox", exist_ok=True)
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
    if not os.path.exists("env.toml"):
        shutil.copy("env.toml.example", "env.toml")
    if not os.path.exists("mcp.json"):
        shutil.copy("mcp.json.example", "mcp.json")
    clone_skill_creator()


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
        pid = os.getpid()
        os.kill(pid, SIGINT)
        exit(1)

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
