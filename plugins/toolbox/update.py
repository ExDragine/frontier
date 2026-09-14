"""Toolbox update commands and supporting logic."""

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from signal import SIGINT

from git import Repo
from nonebot import get_driver, logger, on_command
from nonebot.adapters.milky.event import MessageEvent
from nonebot.permission import SUPERUSER

from utils.alconna import Target, UniMessage
from utils.configs import EnvConfig

driver = get_driver()


updater = on_command("update", priority=1, block=True, aliases={"更新"}, permission=SUPERUSER)


restart = on_command("restart", priority=3, block=True, aliases={"重启"}, permission=SUPERUSER)


MAX_UPDATE_CHANGELOG_COMMITS = 20


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


@restart.handle()
async def handle_restart(event: MessageEvent):
    # 重启Windows
    if os.name == "nt":
        shutdown_executable = shutil.which("shutdown") or "shutdown"
        subprocess.Popen([shutdown_executable, "/r", "/t", "0"])  # noqa: S603

