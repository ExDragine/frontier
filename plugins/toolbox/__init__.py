# ruff: noqa: E402

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
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
MAX_UPDATE_CHANGELOG_COMMITS = 20

# vehelp 菜单缓存（内存级，bot 停止自动释放）
_vep_menu_cache: bytes | None = None
_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


@dataclass(frozen=True)
class CommitInfo:
    short_hash: str
    subject: str
    body: str


@dataclass(frozen=True)
class UpdateLockInfo:
    start_time: float
    old_head: str = ""
    trigger_group_id: int | None = None


async def _get_vep_menu() -> bytes:
    """返回 vep 参数菜单截图（首次渲染后缓存）。"""
    global _vep_menu_cache
    if _vep_menu_cache is not None:
        return _vep_menu_cache
    html = (_TEMPLATES_DIR / "vep_menu.html").read_text(encoding="utf-8")
    css_path = _TEMPLATES_DIR / "vep_menu.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else None
    image = await html_to_image(html, css=css, width=480)
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


def _current_head(repo: Repo) -> str:
    return str(repo.head.commit.hexsha)


def _commit_body(commit) -> str:
    message = str(getattr(commit, "message", "") or "")
    lines = message.splitlines()
    if not lines:
        return ""
    return "\n".join(lines[1:]).strip()


def collect_update_commits(old_head: str, new_head: str) -> list[CommitInfo]:
    """Collect commits introduced by the latest update range."""
    if not old_head or not new_head or old_head == new_head:
        return []
    try:
        repo = Repo(".")
        commits = repo.iter_commits(f"{old_head}..{new_head}", max_count=MAX_UPDATE_CHANGELOG_COMMITS)
        return [
            CommitInfo(
                short_hash=str(commit.hexsha)[:7],
                subject=str(getattr(commit, "summary", "") or "").strip(),
                body=_commit_body(commit),
            )
            for commit in commits
        ]
    except Exception as e:
        logger.warning(f"收集更新提交记录失败: {e}")
        return []


async def _call_assistant_agent(*args, **kwargs):
    from utils.agents import assistant_agent

    return await assistant_agent(*args, **kwargs)


def _format_commits_for_prompt(commits: list[CommitInfo]) -> str:
    blocks = []
    for commit in commits[:MAX_UPDATE_CHANGELOG_COMMITS]:
        body = f"\n{commit.body}" if commit.body else ""
        blocks.append(f"- {commit.short_hash} {commit.subject}{body}")
    return "\n".join(blocks)


async def summarize_update_commits(commits: list[CommitInfo]) -> str | None:
    if not commits:
        return None
    system_prompt = (
        "你是 Frontier QQ Bot 的更新日志编辑。"
        "只根据用户提供的 Git 提交记录，写一份发到群里的简短中文更新日志。"
        "输出 3-6 条短 bullet，语气轻量自然，不要编造提交记录外的信息，"
        "不要暴露密钥、配置值或内部敏感细节。"
    )
    user_prompt = f"请总结这次更新包含的变化：\n\n{_format_commits_for_prompt(commits)}"
    try:
        result = await _call_assistant_agent(system_prompt, user_prompt, tools=None, temperature=0)
    except Exception as e:
        logger.warning(f"生成更新日志失败: {e}")
        return None
    if not result:
        return None
    return str(result).strip() or None


async def send_update_changelog(group_id: int, changelog: str) -> None:
    if not group_id or not changelog:
        return
    await UniMessage.text(f"📦 本次小更新：\n{changelog}").send(target=Target.group(str(group_id)))


def write_update_lock(start_time: float, old_head: str, trigger_group_id: int | None) -> None:
    payload = {
        "start_time": start_time,
        "old_head": old_head,
        "trigger_group_id": trigger_group_id,
    }
    with open(".lock", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def read_update_lock(raw: str) -> UpdateLockInfo:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return UpdateLockInfo(start_time=float(raw))
    if not isinstance(payload, dict):
        return UpdateLockInfo(start_time=float(raw))
    trigger_group_id = payload.get("trigger_group_id")
    return UpdateLockInfo(
        start_time=float(payload.get("start_time", 0)),
        old_head=str(payload.get("old_head") or ""),
        trigger_group_id=int(trigger_group_id) if trigger_group_id else None,
    )


async def send_pending_update_changelog(lock_info: UpdateLockInfo) -> None:
    if not lock_info.old_head or not lock_info.trigger_group_id:
        return
    try:
        new_head = _current_head(Repo("."))
        commits = collect_update_commits(lock_info.old_head, new_head)
        changelog = await summarize_update_commits(commits) if commits else None
        if changelog:
            await send_update_changelog(lock_info.trigger_group_id, changelog)
    except Exception as e:
        logger.warning(f"启动后发送更新日志失败: {e}")


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
async def handle_set(event: MessageEvent):  # noqa: C901
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
            lock_info = read_update_lock(f.read())
        os.remove(".lock")
        for group_id in EnvConfig.ANNOUNCE_GROUP_ID:
            try:
                await UniMessage.text(f"✅ 更新完成！ 用时{int(time.time() - lock_info.start_time)}秒").send(
                    target=Target.group(str(group_id))
                )
            except Exception as e:
                logger.warning(f"发送更新完成通知到群 {group_id} 失败: {e}")
        await send_pending_update_changelog(lock_info)


@updater.handle()
async def handle_updater(event: MessageEvent):
    """处理更新命令"""
    try:
        logger.info("开始执行更新操作...")
        await UniMessage.text("🔄 开始更新...").send()

        repo = Repo(".")
        old_head = _current_head(repo)
        group = getattr(getattr(event, "data", None), "group", None)
        group_id = getattr(group, "group_id", None)
        write_update_lock(time.time(), old_head, int(group_id) if group_id else None)
        repo.git.checkout()
        pull_result = repo.git.pull(rebase=True)
        logger.info(f"Git pull 结果: {pull_result}")
        pid = os.getpid()
        os.kill(pid, SIGINT)
        exit(1)

    except Exception as e:
        if os.path.exists(".lock"):
            os.remove(".lock")
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
async def handle_vehelp(event: MessageEvent):
    """返回 vep 专业模式参数菜单截图（首次渲染后缓存）。"""
    try:
        image = await _get_vep_menu()
        await UniMessage.text("ve专业模式参数菜单：").send()
        await UniMessage.image(raw=image).send()
    except Exception as e:
        logger.error(f"vehelp 菜单渲染失败: {e}")
        await UniMessage.text(f"菜单加载失败: {e}").send()
