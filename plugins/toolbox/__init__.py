# ruff: noqa: E402

import os
import shutil
import subprocess
import time
from pathlib import Path
from signal import SIGINT

from git import Repo
from nonebot import get_driver, logger, on_command, require
from nonebot.adapters.milky.event import GroupMessageEvent, MessageEvent
from nonebot.permission import SUPERUSER

require("nonebot_plugin_alconna")

from utils.alconna import Target, UniMessage
from utils.configs import EnvConfig
from utils.database import GroupSettingsManager, get_engine
from utils.markdown_render import html_to_image
from utils.message import (
    message_extract,
)

driver = get_driver()
updater = on_command("update", priority=1, block=True, aliases={"更新"}, permission=SUPERUSER)
setting = on_command("model", priority=2, block=True, aliases={"模型", "模型设置"})
set_cmd = on_command("set", priority=2, block=True, aliases={"设置"})
vehelp_cmd = on_command("vehelp", priority=2, block=True, aliases={"专业模式", "vep菜单"})
restart = on_command("restart", priority=3, block=True, aliases={"重启"}, permission=SUPERUSER)

SKILL_CREATOR_URL = "https://gh-proxy.org/https://github.com/anthropics/skills.git"
SKILL_CREATOR_PATH = os.path.join(".", "cache", "sandbox", "skills", "skill-creator")

# vehelp 菜单缓存（内存级，bot 停止自动释放）
_vep_menu_cache: bytes | None = None
_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


async def _get_vep_menu() -> bytes:
    """返回 vep 参数菜单截图（首次渲染后缓存）。"""
    global _vep_menu_cache
    if _vep_menu_cache is not None:
        return _vep_menu_cache
    html = (_TEMPLATES_DIR / "vep_menu.html").read_text(encoding="utf-8")
    image = await html_to_image(html, width=480)
    _vep_menu_cache = image
    logger.info("vep 菜单已渲染并缓存")
    return image


SET_WAKE_KEY = "wake_word"


def _is_group_admin_or_owner(event: MessageEvent) -> bool:
    """检查发送者是否为群主或管理员。"""
    if not isinstance(event, GroupMessageEvent):
        return False
    member = event.data.group_member
    if member and member.role in ("admin", "owner"):
        return True
    return False


def _group_settings() -> GroupSettingsManager:
    return GroupSettingsManager(get_engine())


# ── /set wake ──────────────────────────────────────────────


async def _set_wake_show(group_id: int) -> str:
    words = _group_settings().get(group_id, SET_WAKE_KEY)
    if not words:
        return f"当前群未设置唤醒词，使用默认唤醒词「{EnvConfig.BOT_NAME}」。"
    return f"当前群唤醒词：{', '.join(words)}"


async def _set_wake_add(group_id: int, word: str) -> str:
    if not word.strip():
        return "⚠️ 唤醒词不能为空。"
    word = word.strip()
    existing = _group_settings().get(group_id, SET_WAKE_KEY)
    if word in existing:
        return f"⚠️ 唤醒词「{word}」已存在。当前唤醒词：{', '.join(existing)}"
    _group_settings().set(group_id, SET_WAKE_KEY, word)
    updated = _group_settings().get(group_id, SET_WAKE_KEY)
    return f"✅ 唤醒词「{word}」已添加。当前唤醒词：{', '.join(updated)}"


async def _set_wake_remove(group_id: int, word: str) -> str:
    word = word.strip()
    if not word:
        return "⚠️ 要移除的唤醒词不能为空。"
    removed = _group_settings().remove(group_id, SET_WAKE_KEY, word)
    if not removed:
        existing = _group_settings().get(group_id, SET_WAKE_KEY)
        if existing:
            return f"⚠️ 未找到唤醒词「{word}」。当前唤醒词：{', '.join(existing)}"
        return f"⚠️ 未找到唤醒词「{word}」，且当前群未设置任何唤醒词。"
    words = _group_settings().get(group_id, SET_WAKE_KEY)
    if words:
        return f"✅ 唤醒词「{word}」已移除。当前唤醒词：{', '.join(words)}"
    return f"✅ 唤醒词「{word}」已移除。将使用默认唤醒词「{EnvConfig.BOT_NAME}」。"


async def _set_wake_clear(group_id: int) -> str:
    count = _group_settings().clear(group_id, SET_WAKE_KEY)
    if count == 0:
        return f"当前群未设置唤醒词，无需清空。使用默认唤醒词「{EnvConfig.BOT_NAME}」。"
    return f"✅ 已清空 {count} 个唤醒词，将使用默认唤醒词「{EnvConfig.BOT_NAME}」。"


@set_cmd.handle()
async def handle_set(event: MessageEvent):
    text, *_ = await message_extract(event.data.segments)
    text = text.removeprefix("/set").removeprefix("设置").strip()

    group_id = event.data.group.group_id if event.data.group else 0
    if group_id == 0:
        await UniMessage.text("⚠️ 此命令仅支持群聊。").send()
        return

    # 尝试匹配旧命令别名 /set model
    if text.startswith("model ") or text == "model":
        await _handle_set_model(event, text.removeprefix("model").strip())
        return

    # /set wake ...
    if not text.startswith("wake"):
        await UniMessage.text(
            "可用子命令：\n"
            "/set wake              — 查看当前唤醒词\n"
            "/set wake add <词>     — 添加唤醒词\n"
            "/set wake remove <词>  — 移除唤醒词\n"
            "/set wake clear        — 清空唤醒词"
        ).send()
        return

    args = text.removeprefix("wake").strip()

    # /set wake — 查看
    if not args:
        await UniMessage.text(await _set_wake_show(group_id)).send()
        return

    # 写操作需要管理员权限
    if not _is_group_admin_or_owner(event):
        await UniMessage.text("⚠️ 只有群主或管理员才能修改唤醒词。").send()
        return

    # /set wake clear
    if args == "clear":
        await UniMessage.text(await _set_wake_clear(group_id)).send()
        return

    # /set wake add <词>
    if args.startswith("add "):
        await UniMessage.text(await _set_wake_add(group_id, args.removeprefix("add "))).send()
        return
    if args.startswith("add"):
        # "add" 后必须有内容
        await UniMessage.text("⚠️ 用法：/set wake add <唤醒词>").send()
        return

    # /set wake remove <词>
    if args.startswith("remove "):
        await UniMessage.text(await _set_wake_remove(group_id, args.removeprefix("remove "))).send()
        return
    if args.startswith("remove"):
        await UniMessage.text("⚠️ 用法：/set wake remove <唤醒词>").send()
        return

    # 未知子命令
    await UniMessage.text(
        "用法：\n"
        "/set wake              — 查看唤醒词\n"
        "/set wake add <词>     — 添加\n"
        "/set wake remove <词>  — 移除\n"
        "/set wake clear        — 清空"
    ).send()


# ── /set model (保留旧兼容) ─────────────────────────────────


async def _handle_set_model(event: MessageEvent, model_text: str):
    """/set model 的过渡兼容处理，提示用户使用 /model 或待实现群级别 model。"""
    await UniMessage.text(
        f"当前默认模型为: {EnvConfig.ADVAN_MODEL}\n"
        f"当前辅助模型为: {EnvConfig.BASIC_MODEL}\n"
        f"当前绘图模型为: {EnvConfig.PAINT_MODEL}\n\n"
        "提示：使用 /model 命令查看或切换模型。"
    ).send()


# ── 原有命令 ────────────────────────────────────────────────


def clone_skill_creator():
    """将 anthropics/skills 仓库中的 skill-creator 克隆到 skills 目录。"""
    target = os.path.abspath(SKILL_CREATOR_PATH)
    if os.path.exists(target):
        logger.info("skill-creator 已存在，跳过克隆")
        return

    logger.info("正在克隆 skill-creator...")
    temp_dir = os.path.join(os.path.abspath("cache/sandbox"), ".skills-temp")
    git_executable = shutil.which("git")
    if git_executable is None:
        logger.error("未找到 git，无法克隆 skill-creator")
        return
    try:
        subprocess.run(  # noqa: S603
            [git_executable, "clone", "--depth", "1", SKILL_CREATOR_URL, temp_dir],
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
            f"当前默认模型为: {EnvConfig.ADVAN_MODEL}\n"
            f"当前辅助模型为: {EnvConfig.BASIC_MODEL}\n"
            f"当前绘图模型为: {EnvConfig.PAINT_MODEL}\n"
            f"当前视频模型为: {EnvConfig.VIDEO_MODEL}"
        ).send()


@restart.handle()
async def handle_restart(event: MessageEvent):
    # 重启Windows
    if os.name == "nt":
        shutdown_executable = shutil.which("shutdown") or "shutdown"
        subprocess.Popen([shutdown_executable, "/r", "/t", "0"])  # noqa: S603


@vehelp_cmd.handle()
async def handle_vehelp():
    """返回 vep 专业模式参数菜单截图（首次渲染后缓存）。"""
    try:
        image = await _get_vep_menu()
        await UniMessage.text("ve专业模式参数菜单：").send()
        await UniMessage.image(raw=image).send()
    except Exception as e:
        logger.error(f"vehelp 菜单渲染失败: {e}")
        await UniMessage.text(f"菜单加载失败: {e}").send()
