"""Streaming progress events for Deep Agent execution."""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Literal

from nonebot import logger

from utils.progress_messages import subagent_message, tool_message


@dataclass
class ProgressEvent:
    """Agent 执行过程中的用户可读进度事件。"""

    type: Literal[
        "thinking",
        "tool_call",
        "tool_result",
        "subagent_start",
        "subagent_done",
        "assistant_preamble",
        "text_delta",
        "done",
    ]
    message: str
    detail: dict[str, Any] | None = None


ProgressReporter = Callable[[ProgressEvent], Awaitable[None]]


async def emit_progress(reporter: ProgressReporter | None, event: ProgressEvent) -> None:
    """安全调用 reporter，reporter 自身异常不中断 Agent 执行。"""
    if reporter is None:
        return
    try:
        await reporter(event)
    except Exception as exc:
        logger.warning(f"Progress reporter 调用失败: {type(exc).__name__}: {exc}")


async def collect_progress(stream, reporter: ProgressReporter | None) -> None:  # noqa: C901
    """消费 astream_events v3 projections 并生成用户可读进度事件。"""

    async def consume_subagents() -> None:
        last_subagent_event: tuple[str, str] | None = None
        async for subagent in stream.subagents:
            name = subagent.name
            raw_status = getattr(subagent, "status", None)
            status = raw_status.lower() if isinstance(raw_status, str) else "started"
            terminal = status in {"completed", "complete", "done", "failed", "error"}
            phase = "done" if terminal else "start"
            event_key = (name, phase)
            if event_key == last_subagent_event:
                continue
            last_subagent_event = event_key
            if terminal:
                failed = status in {"failed", "error"}
                await emit_progress(
                    reporter,
                    ProgressEvent(
                        type="subagent_done",
                        message=f"{name} {'执行失败' if failed else '已完成'}",
                        detail={"name": name, "status": status},
                    ),
                )
                continue
            await emit_progress(
                reporter,
                ProgressEvent(
                    type="subagent_start",
                    message=subagent_message(name),
                    detail={"name": name},
                ),
            )

    async def consume_tool_calls() -> None:
        last_tool_name: str | None = None
        async for tool_call in stream.tool_calls:
            tool_name = tool_call.tool_name
            if tool_name != last_tool_name:
                last_tool_name = tool_name
                await emit_progress(
                    reporter,
                    ProgressEvent(
                        type="tool_call",
                        message=tool_message(tool_name),
                        detail={"tool_name": tool_name},
                    ),
                )
            completed = getattr(tool_call, "completed", None)
            error = getattr(tool_call, "error", None)
            failed = isinstance(error, BaseException) or (isinstance(error, str) and bool(error))
            if completed is True or failed:
                await emit_progress(
                    reporter,
                    ProgressEvent(
                        type="tool_result",
                        message=f"{tool_name} {'执行失败' if failed else '已完成'}",
                        detail={"tool_name": tool_name, "success": not failed},
                    ),
                )

    async def consume_messages() -> None:
        first_message = True
        async for message in stream.messages:
            if first_message:
                await emit_progress(reporter, ProgressEvent(type="thinking", message="正在思考…"))
                first_message = False
            message_text = ""
            text_buffer = ""
            async for chunk in message.text:
                message_text += chunk
                text_buffer += chunk
                while "\n\n" in text_buffer:
                    index = text_buffer.index("\n\n")
                    paragraph = text_buffer[:index].strip()
                    text_buffer = text_buffer[index + 2 :]
                    if paragraph:
                        await emit_progress(reporter, ProgressEvent(type="text_delta", message=paragraph))

            # 每个 stream.messages 条目对应一次模型调用。只有带工具调用的
            # AI 文本才是“边做边说”的过程发言；无工具调用的消息是终止回复，
            # 继续交给正常的最终回复链路，避免重复发送。
            try:
                tool_calls = await message.tool_calls
            except (AttributeError, TypeError):
                tool_calls = getattr(getattr(message, "output_message", None), "tool_calls", None)
            except Exception as exc:
                logger.debug(f"读取模型消息工具调用失败，跳过过程发言: {type(exc).__name__}: {exc}")
                tool_calls = None

            preamble = message_text.strip()
            if preamble and tool_calls:
                await emit_progress(
                    reporter,
                    ProgressEvent(
                        type="assistant_preamble",
                        message=preamble,
                        detail={"tool_call_count": len(tool_calls)},
                    ),
                )

    async def safe_consume(coro) -> None:
        try:
            await coro
        except Exception as exc:
            logger.warning(f"Progress collector 异常: {type(exc).__name__}: {exc}")

    await asyncio.gather(
        safe_consume(consume_subagents()),
        safe_consume(consume_tool_calls()),
        safe_consume(consume_messages()),
    )


async def finish_progress_collection(progress_task: asyncio.Task) -> None:
    """短暂排空已关闭的 projection，然后停止卡住的 collector。"""
    try:
        await asyncio.wait_for(progress_task, timeout=1)
    except TimeoutError:
        logger.debug("Progress projections 未在响应完成后及时关闭，已停止收集")
    finally:
        if not progress_task.done():
            progress_task.cancel()
            with suppress(asyncio.CancelledError):
                await progress_task
