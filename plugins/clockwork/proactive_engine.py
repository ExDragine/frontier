"""主动智能引擎 — 上下文感知的主动消息推送。

从定时广播（每日新闻、APOD）升级为智能评估 — 检测不活跃群组的摘要机会、
话题提醒、异常告警等场景，仅在合适时机主动发言。

设计原则：
- 每个评估周期先做廉价的 DB 查询判断是否需要，再决定是否跑 Agent
- 所有主动发言都受频率限制，避免骚扰
- 与现有 clockwork 调度系统无缝集成
"""

from __future__ import annotations

import datetime
import time
import zoneinfo
from dataclasses import dataclass, field
from typing import Any

from nonebot import get_bot, logger

from utils.configs import EnvConfig
from utils.database import MessageDatabase
from policy import engine as policy_engine
from policy.decisions import Verdict
from policy.snapshots import OutputSnapshot
from utils.message import extract_message_text

# ═══════════════════════════════════════════════════════════════════════════════
# 配置常量
# ═══════════════════════════════════════════════════════════════════════════════

# 每个群每个场景的最小间隔（秒）
DEFAULT_COOLDOWNS: dict[str, int] = {
    "group_summary": 3600 * 6,       # 群摘要：6 小时
    "unanswered_question": 3600 * 2, # 未回答问题：2 小时
    "activity_spike": 3600,          # 异常活跃：1 小时
    "topic_mention": 3600 * 3,       # 话题提醒：3 小时
    "return_welcome": 3600 * 12,     # 回归欢迎：12 小时
}

# 触发阈值
SUMMARY_MIN_INACTIVE_SECONDS = 3600 * 2   # 群静默 2 小时后考虑摘要
SUMMARY_MIN_MESSAGES = 20                  # 至少 20 条未读消息才摘要
ACTIVITY_SPIKE_MULTIPLIER = 5.0            # 消息量超过平均值 5 倍视为异常
UNANSWERED_QUESTION_HOURS = 1              # 1 小时内的未回答问题

# 深夜静默时段（服务端本地时间），不发送主动消息
QUIET_HOURS_START = 23  # 23:00
QUIET_HOURS_END = 8     # 08:00

PROACTIVE_SYSTEM_PROMPT = (
    "你是一个友好的群聊助手，名叫{name}。你现在要发送一条主动消息给群成员。\n"
    "消息应该自然、简短、有用，不要显得像机器人通知。\n"
    "用口语化的中文，保持轻松友好的语气。\n"
    "如果是摘要，突出群友们讨论的有趣话题。\n"
    "如果是提醒，温和地提及而不是催促。"
)


@dataclass
class GroupActivitySnapshot:
    """群组活动快照，用于判断是否触发主动行为。"""

    group_id: int
    message_count_since: int          # 自某时间点以来的消息数
    unique_speakers: int              # 唯一发言人数
    last_message_time: int            # 最后消息时间（毫秒）
    avg_message_rate_per_hour: float  # 平均每小时消息数
    current_rate_per_hour: float      # 最近窗口每小时消息数


@dataclass
class ProactiveDecision:
    """主动行为决策结果。"""

    should_act: bool
    scenario: str = ""
    context: dict[str, Any] = field(default_factory=dict)


class ProactiveEngine:
    """主动智能引擎 — 评估群组状态并触发合适的主动消息。"""

    def __init__(self, db: MessageDatabase | None = None) -> None:
        self._db = db or MessageDatabase()
        self._last_acted: dict[str, float] = {}  # key: "group_id:scenario" → timestamp

    # ── 公开 API ──────────────────────────────────────────────────────────

    async def evaluate_and_act(self, group_id: int) -> bool:
        """评估单个群组的所有主动场景，执行第一个符合条件的。

        仅在测试群中生效，深夜时段静默。
        """
        if group_id not in set(EnvConfig.TEST_GROUP_ID):
            return False
        if self._in_quiet_hours():
            return False

        snapshot = await self._snapshot(group_id)
        if snapshot is None:
            return False

        scenarios = [
            ("activity_spike", self._check_activity_spike),
            ("unanswered_question", self._check_unanswered_question),
            ("group_summary", self._check_group_summary),
        ]

        for scenario_name, check_fn in scenarios:
            decision = await check_fn(group_id, snapshot)
            if not decision.should_act:
                continue
            if not self._can_act(group_id, scenario_name):
                continue
            try:
                await self._execute_proactive_message(group_id, scenario_name, decision.context)
                self._record_action(group_id, scenario_name)
                return True
            except Exception as exc:
                logger.warning(f"主动引擎 [{scenario_name}] 群 {group_id} 执行失败: {exc}")
        return False

    async def evaluate_all_groups(self) -> dict[int, str]:
        """评估所有测试群组，返回 {group_id: triggered_scenario}。

        仅在 TEST_GROUP_ID 中配置的群组生效，深夜静默。
        """
        if self._in_quiet_hours():
            logger.debug("主动引擎：深夜静默时段，跳过评估")
            return {}

        results: dict[int, str] = {}
        groups = set(EnvConfig.TEST_GROUP_ID)
        for group_id in groups:
            if await self.evaluate_and_act(group_id):
                results[group_id] = "acted"
        return results

    # ── 场景检测 ──────────────────────────────────────────────────────────

    async def _check_activity_spike(
        self, group_id: int, snap: GroupActivitySnapshot
    ) -> ProactiveDecision:
        """检测群组异常活跃 — 可能有热点事件。"""
        if snap.avg_message_rate_per_hour <= 0:
            return ProactiveDecision(should_act=False)
        ratio = snap.current_rate_per_hour / max(snap.avg_message_rate_per_hour, 0.1)
        if ratio < ACTIVITY_SPIKE_MULTIPLIER:
            return ProactiveDecision(should_act=False)
        return ProactiveDecision(
            should_act=True,
            scenario="activity_spike",
            context={
                "group_id": group_id,
                "current_rate": snap.current_rate_per_hour,
                "avg_rate": snap.avg_message_rate_per_hour,
                "message_count": snap.message_count_since,
                "unique_speakers": snap.unique_speakers,
            },
        )

    async def _check_unanswered_question(
        self, group_id: int, snap: GroupActivitySnapshot
    ) -> ProactiveDecision:
        """检测是否有未被回复的问题。"""
        now_ms = int(time.time() * 1000)
        since_ms = now_ms - UNANSWERED_QUESTION_HOURS * 3600 * 1000
        messages = await self._db.select_by_time_range(
            start_time=since_ms,
            end_time=now_ms,
            group_id=group_id,
            limit=50,
        )
        if not messages:
            return ProactiveDecision(should_act=False)

        last_assistant_time = 0
        question_candidates: list[tuple[int, str]] = []
        for msg in messages:
            if msg.role == "assistant":
                last_assistant_time = max(last_assistant_time, msg.time)
            elif msg.role == "user" and msg.content:
                # 简单启发式：包含问号或疑问关键词
                if any(kw in (msg.content or "") for kw in ("?", "？", "怎么", "为什么", "有没有", "谁知道")):
                    question_candidates.append((msg.time, msg.content))

        # 只把最后一次助手回复之后出现的问题视为未回答。
        unanswered = [
            content for question_time, content in question_candidates
            if question_time > last_assistant_time
        ]
        if not unanswered:
            return ProactiveDecision(should_act=False)

        return ProactiveDecision(
            should_act=True,
            scenario="unanswered_question",
            context={
                "group_id": group_id,
                "unanswered_count": len(unanswered),
                "sample_question": unanswered[0][:200],
            },
        )

    async def _check_group_summary(
        self, group_id: int, snap: GroupActivitySnapshot
    ) -> ProactiveDecision:
        """检测适合发送群聊摘要的时机。"""
        now_ms = int(time.time() * 1000)
        inactive_duration = (now_ms - snap.last_message_time) / 1000

        if inactive_duration < SUMMARY_MIN_INACTIVE_SECONDS:
            return ProactiveDecision(should_act=False)
        if snap.message_count_since < SUMMARY_MIN_MESSAGES:
            return ProactiveDecision(should_act=False)

        return ProactiveDecision(
            should_act=True,
            scenario="group_summary",
            context={
                "group_id": group_id,
                "inactive_minutes": int(inactive_duration / 60),
                "message_count": snap.message_count_since,
                "unique_speakers": snap.unique_speakers,
            },
        )

    # ── 执行 ──────────────────────────────────────────────────────────────

    async def _execute_proactive_message(
        self, group_id: int, scenario: str, context: dict
    ) -> None:
        """生成并发送主动消息。"""
        prompt = self._build_prompt(scenario, context)
        system_prompt = PROACTIVE_SYSTEM_PROMPT.format(name=EnvConfig.BOT_NAME)

        from utils.llm_factory import create_llm

        llm = create_llm(
            model=EnvConfig.BASIC_MODEL,
            provider=EnvConfig.BASIC_MODEL_PROVIDER,
            endpoint=EnvConfig.BASIC_MODEL_ENDPOINT,
            streaming=False,
            max_retries=1,
            timeout=60,
        )
        result = await llm.ainvoke(
            [("system", system_prompt), ("human", prompt)]
        )
        text = extract_message_text(result).strip()
        if not text:
            return

        output_decision = await policy_engine.intervene("output", OutputSnapshot(
            user_id="system",
            group_id=group_id,
            text=text,
        ))
        if output_decision.verdict == Verdict.DENY:
            return
        text = output_decision.message if output_decision.verdict == Verdict.WARN else text
        if not text:
            return

        await get_bot().send_group_message(group_id=group_id, message=text)
        logger.info(f"主动引擎 [{scenario}] 已发送消息到群 {group_id}")

    def _build_prompt(self, scenario: str, context: dict) -> str:
        """根据场景构建 LLM 提示。"""
        base = f"群 {context['group_id']} 当前状态：\n"
        if scenario == "group_summary":
            return (
                f"{base}"
                f"群已经 {context['inactive_minutes']} 分钟没有新消息了。\n"
                f"在过去一段时间内有 {context['message_count']} 条消息，"
                f"来自 {context['unique_speakers']} 位群友。\n"
                f"请生成一段简短友好的群聊回顾或问候，让大家知道这个群还活跃着。"
            )
        if scenario == "activity_spike":
            return (
                f"{base}"
                f"最近消息量是平时的 {context['current_rate'] / max(context['avg_rate'], 0.1):.0f} 倍！\n"
                f"有 {context['unique_speakers']} 位群友在热烈讨论。\n"
                f"请用轻松的语气参与一下讨论（不要问'你们在聊什么'）。"
            )
        if scenario == "unanswered_question":
            return (
                f"{base}"
                f"群里有 {context['unanswered_count']} 个可能被忽略的问题。\n"
                f"例如：{context['sample_question'][:200]}\n"
                f"请尝试回答或引导讨论，用友好的口吻。"
            )
        return f"{base}请发送一条友好的问候。"

    # ── 频率控制 ──────────────────────────────────────────────────────────

    def _in_quiet_hours(self) -> bool:
        """深夜静默：23:00-08:00 不出声。"""
        hour = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")).hour
        return hour >= QUIET_HOURS_START or hour < QUIET_HOURS_END

    def _can_act(self, group_id: int, scenario: str) -> bool:
        key = f"{group_id}:{scenario}"
        cooldown = DEFAULT_COOLDOWNS.get(scenario, 3600)
        last = self._last_acted.get(key, 0)
        return time.monotonic() - last >= cooldown

    def _record_action(self, group_id: int, scenario: str) -> None:
        self._last_acted[f"{group_id}:{scenario}"] = time.monotonic()

    # ── 数据采集 ──────────────────────────────────────────────────────────

    async def _snapshot(self, group_id: int) -> GroupActivitySnapshot | None:
        """获取群组活动快照。"""
        now_ms = int(time.time() * 1000)

        # 最近 1 小时的活动
        recent_ms = now_ms - 3600 * 1000
        recent_count = await self._db.count_group_messages_since(
            group_id=group_id, since_time=recent_ms
        )

        # 最近 24 小时的活动（用于计算平均值）
        day_ms = now_ms - 86400 * 1000
        day_count = await self._db.count_group_messages_since(
            group_id=group_id, since_time=day_ms
        )

        # 最近一条消息时间
        last_time = await self._db.latest_group_role_message_time(
            group_id=group_id, role="user"
        )

        if last_time is None:
            return None  # 群组无消息记录

        # 最近消息的唯一发言人数
        recent_messages = await self._db.select_by_time_range(
            start_time=day_ms, end_time=now_ms, group_id=group_id, limit=500
        )
        unique_speakers = len({m.user_id for m in recent_messages})

        return GroupActivitySnapshot(
            group_id=group_id,
            message_count_since=day_count,
            unique_speakers=max(unique_speakers, 1),
            last_message_time=last_time,
            avg_message_rate_per_hour=day_count / 24.0,
            current_rate_per_hour=recent_count * 1.0,  # per hour in last hour
        )
