"""DeepSeek Harness command."""

from __future__ import annotations

from nonebot import get_driver, logger, on_command
from nonebot.adapters.milky.event import MessageEvent

from utils.agents import ProgressEvent, ProgressReporter, agent_thread_id, run_serialized
from utils.agents.dsh import DshAgent, dsh_service
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.message import message_extract, outgoing_message_content, sanitize_outgoing_text, send_messages

dsh_command = on_command("dsh", priority=2, block=True)
dsh_agent = DshAgent()
driver = get_driver()


def _scope(user_id: str, group_id: int | None) -> tuple[str, str]:
    workspace_key = f"group:{group_id}" if group_id is not None else f"dm:{user_id}"
    session_id = f"frontier-{agent_thread_id(user_id, group_id).hex}"
    return workspace_key, session_id


def _progress_reporter(group_id: int | None) -> ProgressReporter:
    sent_thinking = False

    async def reporter(event: ProgressEvent) -> None:
        nonlocal sent_thinking
        if group_id is not None:
            if event.type == "thinking" and not sent_thinking:
                sent_thinking = True
                await UniMessage.text("🧪 DSH 正在执行实验任务…").send()
            return
        if event.type in {"thinking", "tool_call", "subagent_start", "subagent_done"}:
            await UniMessage.text(f"🧪 {event.message}").send()

    return reporter


@dsh_command.handle()
async def handle_dsh(event: MessageEvent) -> None:
    text, *_ = await message_extract(event.data.segments)
    prompt = text.strip()
    for prefix in ("/dsh", "dsh"):
        if prompt.lower().startswith(prefix):
            prompt = prompt[len(prefix) :].strip()
            break
    if not prompt:
        await UniMessage.text("🧪 用法：/dsh <任务描述>\n该命令仅在独立实验工作区中运行。").send()
        return

    user_id = event.get_user_id()
    group_id = event.data.group.group_id if event.data.group else None
    workspace_key, session_id = _scope(user_id, group_id)
    result = await run_serialized(
        f"dsh:{session_id}",
        dsh_agent.chat_agent(
            prompt,
            workspace_key=workspace_key,
            session_id=session_id,
            progress_reporter=_progress_reporter(group_id),
        ),
        timeout=float(EnvConfig.AGENT_JOB_TIMEOUT_SECONDS) + 10,
    )
    response = result.get("response") if isinstance(result, dict) else None
    messages = response.get("messages") if isinstance(response, dict) else None
    if not messages:
        await UniMessage.text("🧪 DSH 没有返回可发送的内容。").send()
        return
    content = outgoing_message_content(messages[-1])
    sanitized = await sanitize_outgoing_text(content)
    if sanitized != content:
        from langchain.messages import AIMessage

        messages[-1] = AIMessage(content=sanitized)
    if result.get("error"):
        logger.warning("DSH command returned an error response")
    await send_messages(group_id, event.data.message_seq, response)


@driver.on_shutdown
async def shutdown_dsh() -> None:
    await dsh_service.close()
