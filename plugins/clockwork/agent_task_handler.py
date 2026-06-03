"""统一自动任务 Agent 执行 handler。"""

import json
import time

from nonebot import get_bot, logger
from nonebot.adapters.milky.message import MessageSegment
from nonebot_plugin_alconna import Target, UniMessage

from utils.agents import FrontierCognitive
from utils.configs import EnvConfig
from utils.database import build_message_metadata
from policy import engine as policy_engine
from policy.decisions import Verdict
from policy.snapshots import OutputSnapshot
from utils.message import extract_message_text, outgoing_message_content

from .task_models import TaskRunResult


def _target(metadata):
    if metadata.target_type == "group":
        return Target.group(str(metadata.target_id))
    if metadata.target_type == "user":
        return Target.user(str(metadata.target_id))
    raise ValueError(f"不支持的任务目标类型: {metadata.target_type}")


async def _send_final_text(metadata, target: Target, final_text: str, mention_user_id: str | None) -> None:
    if metadata.target_type == "group" and mention_user_id:
        await get_bot().send_group_message(
            group_id=int(metadata.target_id),
            message=[
                MessageSegment.mention(int(mention_user_id)),
                MessageSegment.text(f" {final_text}"),
            ],
        )
        return
    await UniMessage.text(final_text).send(target=target)


async def run_agent_task(job_id: str = "", **kwargs) -> TaskRunResult:
    """执行统一自动任务：跑 Agent，并把最终结果投递到任务目标。"""
    from plugins.clockwork import task_manager

    metadata = await task_manager.get_task_metadata(job_id)
    if not metadata:
        raise RuntimeError(f"任务 {job_id} 缺少 ScheduledTaskMetadata")
    if metadata.archived:
        raise RuntimeError(f"任务 {job_id} 已归档")

    target = _target(metadata)
    group_id = int(metadata.target_id) if metadata.target_type == "group" else None
    owner_user_id = metadata.owner_user_id or str(metadata.target_id)
    mention_user_id = metadata.owner_user_id
    now_ms = int(time.time() * 1000)
    messages = [
        {
            "role": "user",
            "content": json.dumps(
                {
                    "metadata": build_message_metadata(
                        timestamp_ms=now_ms,
                        user_id=owner_user_id,
                        group_id=group_id,
                        user_name=f"ScheduledTask:{job_id}",
                    ),
                    "is_current": True,
                    "content": metadata.prompt,
                },
                ensure_ascii=False,
            ),
        }
    ]

    cognitive = FrontierCognitive()
    result = await cognitive.chat_agent(
        messages,
        owner_user_id,
        f"ScheduledTask:{job_id}",
        EnvConfig.AGENT_CAPABILITY,
        group_id=group_id,
        query_text=metadata.prompt,
        thread_id_override=f"scheduled-task:{job_id}",
    )
    if not isinstance(result, dict) or "response" not in result:
        raise RuntimeError("Agent 自动任务没有返回有效响应")

    messages_sent = 0
    if metadata.delivery_mode != "none":
        for artifact in result.get("uni_messages", []) or []:
            if isinstance(artifact, UniMessage):
                await artifact.send(target=target)
                messages_sent += 1

    response = result.get("response") or {}
    response_messages = response.get("messages") or []
    output_summary = ""
    if response_messages:
        output_summary = outgoing_message_content(response_messages[-1]).strip()

    final_text = output_summary
    if output_summary:
        output_decision = await policy_engine.intervene("output", OutputSnapshot(
            user_id=owner_user_id,
            group_id=group_id,
            text=output_summary,
        ))
        if output_decision.verdict == Verdict.DENY:
            final_text = output_decision.message
    if metadata.delivery_mode == "final" and final_text:
        await _send_final_text(metadata, target, final_text, mention_user_id)
        messages_sent += 1
    elif metadata.delivery_mode not in {"final", "none"}:
        logger.warning(f"任务 {job_id} 使用未知 delivery_mode={metadata.delivery_mode!r}，已跳过最终投递")

    groups_sent = [int(metadata.target_id)] if metadata.target_type == "group" and messages_sent else []
    return TaskRunResult(
        groups_sent=groups_sent,
        messages_sent=messages_sent,
        output_summary=output_summary[:1000] if output_summary else None,
    )
