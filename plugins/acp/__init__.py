"""ACP Agent bridge command."""

from __future__ import annotations

from dataclasses import dataclass

from nonebot import get_driver, logger, on_command
from nonebot.adapters.milky.event import MessageEvent

from utils.agents import ProgressEvent, ProgressReporter
from utils.agents.acp import AcpAgent, AcpConfigurationError, AcpInputMedia, acp_service
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.media import resolve_media
from utils.message import (
    download_media,
    message_extract,
    outgoing_message_content,
    sanitize_outgoing_text,
    send_artifacts,
    send_messages,
)

acp_command = on_command("acp", priority=2, block=True)
acp_agent = AcpAgent()
driver = get_driver()

_USAGE = (
    "🔌 用法：\n"
    "/acp <任务>\n"
    "/acp --agent <名称> <任务>\n"
    "/acp --list\n"
    "/acp --cancel [--agent <名称>]\n"
    "/acp --reset [--agent <名称>]"
)


@dataclass(frozen=True, slots=True)
class _ParsedCommand:
    action: str
    agent_name: str | None
    prompt: str


def _strip_prefix(text: str) -> str:
    value = text.strip()
    for prefix in ("/acp", "acp"):
        if value.lower().startswith(prefix):
            return value[len(prefix) :].strip()
    return value


def _parse_command(text: str) -> _ParsedCommand:
    remaining = _strip_prefix(text)
    action = "run"
    agent_name: str | None = None
    while remaining.startswith("--"):
        option, separator, tail = remaining.partition(" ")
        if option.startswith("--agent="):
            agent_name = option.removeprefix("--agent=").strip() or None
            remaining = tail.strip() if separator else ""
            continue
        if option == "--agent":
            value, value_separator, value_tail = tail.strip().partition(" ")
            agent_name = value or None
            remaining = value_tail.strip() if value_separator else ""
            continue
        if option in {"--list", "--cancel", "--reset", "--help"}:
            action = option.removeprefix("--")
            remaining = tail.strip() if separator else ""
            continue
        break
    return _ParsedCommand(action=action, agent_name=agent_name, prompt=remaining)


def _scope(event: MessageEvent) -> tuple[str, int | None]:
    group_id = event.data.group.group_id if event.data.group else None
    workspace_key = f"group:{group_id}" if group_id is not None else f"dm:{event.get_user_id()}"
    return workspace_key, group_id


def _has_agent_access(event: MessageEvent) -> bool:
    group_id = event.data.group.group_id if event.data.group else 0
    raw_user_id = event.get_user_id()
    try:
        user_id: int | str = int(raw_user_id)
    except ValueError:
        user_id = raw_user_id
    if group_id != 0 and EnvConfig.AGENT_WHITELIST_MODE and group_id not in EnvConfig.AGENT_WHITELIST_GROUP_LIST:
        return False
    if group_id in EnvConfig.AGENT_BLACKLIST_GROUP_LIST:
        return False
    if EnvConfig.AGENT_WHITELIST_MODE and user_id not in EnvConfig.AGENT_WHITELIST_PERSON_LIST:
        return False
    return user_id not in EnvConfig.AGENT_BLACKLIST_PERSON_LIST


def _progress_reporter(group_id: int | None) -> ProgressReporter:
    async def reporter(event: ProgressEvent) -> None:
        # 群聊统一静默处理中间事件，只在任务结束后发送最终结果。
        if group_id is not None:
            return
        if event.type not in {"thinking", "tool_call", "tool_result", "assistant_preamble"}:
            return
        message = await sanitize_outgoing_text(event.message)
        if message:
            await UniMessage.text(f"🔌 {message}").send()

    return reporter


def _input_media(images: list[bytes], audios: list[bytes]) -> tuple[AcpInputMedia, ...]:
    items: list[AcpInputMedia] = []
    for data in images:
        media = resolve_media(data, "image")
        items.append(AcpInputMedia(kind="image", data=media.data, mime_type=media.mime_type))
    for data in audios:
        media = resolve_media(data, "audio")
        items.append(AcpInputMedia(kind="audio", data=media.data, mime_type=media.mime_type))
    return tuple(items)


async def _handle_control(parsed: _ParsedCommand, workspace_key: str) -> bool:
    if parsed.action == "help":
        await UniMessage.text(_USAGE).send()
        return True
    if parsed.action == "list":
        default, agents = acp_service.available_agents()
        rendered = "、".join(f"{name}（默认）" if name == default else name for name in agents)
        await UniMessage.text(f"🔌 已配置的 ACP Agent：{rendered}").send()
        return True
    if parsed.action == "cancel":
        count = await acp_service.cancel(workspace_key=workspace_key, agent_name=parsed.agent_name)
        message = "已发送取消请求。" if count else "当前没有正在运行的 ACP 任务。"
        await UniMessage.text(f"🔌 {message}").send()
        return True
    if parsed.action == "reset":
        count = await acp_service.reset(workspace_key=workspace_key, agent_name=parsed.agent_name)
        message = f"已重置 {count} 个 ACP 会话。" if count else "当前没有可重置的 ACP 会话。"
        await UniMessage.text(f"🔌 {message}").send()
        return True
    return False


async def _send_result(result: dict, *, group_id: int | None, message_seq: int) -> None:
    artifacts = result.get("uni_messages", [])
    if artifacts:
        await send_artifacts(artifacts)
    response = result.get("response")
    if not isinstance(response, dict):
        if not artifacts:
            await UniMessage.text("🔌 ACP Agent 没有返回可发送的内容。").send()
        return
    messages = response.get("messages")
    if not messages:
        if not artifacts:
            await UniMessage.text("🔌 ACP Agent 没有返回可发送的内容。").send()
        return
    content = outgoing_message_content(messages[-1])
    sanitized = await sanitize_outgoing_text(content)
    if sanitized != content:
        from langchain.messages import AIMessage

        messages[-1] = AIMessage(content=sanitized or "")
    if result.get("error"):
        logger.warning("ACP command returned an error response")
    if sanitized:
        await send_messages(group_id, message_seq, response)


@acp_command.handle()
async def handle_acp(event: MessageEvent) -> None:
    if not _has_agent_access(event):
        await UniMessage.text("🔌 没有权限使用 ACP Agent。").send()
        return
    text, image_items, audio_items, video_items = await message_extract(event.data.segments)
    parsed = _parse_command(text)
    workspace_key, group_id = _scope(event)

    try:
        if await _handle_control(parsed, workspace_key):
            return
    except AcpConfigurationError as exc:
        await UniMessage.text(f"🔌 ACP 配置错误：{exc}").send()
        return

    if not parsed.prompt:
        await UniMessage.text(_USAGE).send()
        return

    images, audios, videos = await download_media(image_items, audio_items, video_items)
    prompt = parsed.prompt
    if videos:
        prompt = f"{prompt}\n\n[ACP v1 不支持视频输入，已省略 {len(videos)} 段视频。]"
    result = await acp_agent.chat_agent(
        prompt,
        workspace_key=workspace_key,
        agent_name=parsed.agent_name,
        media=_input_media(images, audios),
        progress_reporter=_progress_reporter(group_id),
    )
    await _send_result(result, group_id=group_id, message_seq=event.data.message_seq)


@driver.on_shutdown
async def shutdown_acp() -> None:
    await acp_service.close()
