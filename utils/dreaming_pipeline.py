"""Dreaming 后台记忆管道 — 每个自然日凌晨 4:00 异步整理记忆。

设计原理（对标 ChatGPT Dreaming V3）：
- 凌晨 4:00 全局跑一次，非侵入式，不阻塞对话
- 逐个对话范围 (user, group) 处理：拉新消息 → 提取事实 → 对比旧记忆 → 合并
- 处理时态推理：标记过期、更新 valid_until、检测状态变化（"要去" → "去过"）
- 清理孤立/低质量记忆

P0: Few-shot 提示词 — 3 类示例 + 常见错误模式，提升提取质量
P4: 自适应分档 — 高频对话分段提取、中频正常、低频规则匹配

与现有系统的关系：
- MemoryManager 负责存储和 CRUD（含 P1 交叉验证 + P2 语义去重 + P3 矛盾检测）
- DreamingPipeline 负责定时触发和编排（含 P0 + P4）
- APScheduler (via TaskManager) 负责 cron 调度
"""

import time
from typing import Any

from nonebot import logger

from utils.database import Message, MessageDatabase
from utils.memory_v3 import (
    MemoryEntry,
    MemoryExtractionResult,
    MemoryManager,
    _rule_based_extract,
    get_memory_manager,
)

# ── 常量 ──────────────────────────────────────────────────────────

_DREAMING_JOB_ID = "dreaming_daily_v3"
_DREAMING_JOB_NAME = "Dreaming 记忆整理 V3"
_LOOKBACK_HOURS = 26

_MAX_CONVERSATIONS = 50
_MIN_MESSAGES_TO_TRIGGER = 5
_MEMORIES_PER_CONVERSATION_LIMIT = 5

# P4: 自适应分档阈值
_HIGH_VOLUME_THRESHOLD = 100   # > 100 条消息 → 分段提取
_MEDIUM_VOLUME_THRESHOLD = 20  # 20-100 条 → 正常 LLM 提取
# < 20 条 → 规则优先

_SEGMENT_SIZE = 50              # 分段大小


# ── P0: Few-shot Dreaming 提示词 ──────────────────────────────────


def _dreaming_system_prompt() -> str:
    return (
        "你是 V3 记忆整理引擎（Dreaming Pipeline）。在用户安静时，"
        "你从最近聊天记录中提取、更新和修正结构化记忆。\n\n"
        "核心规则：\n"
        "1. fact_key 使用 snake_case 英文，如 'current_city', 'travel_plan_q3'\n"
        "2. 仅提取明确陈述的内容。禁止推测用户没有说过的事。\n"
        "3. 对未来事件设置 valid_until 为事件结束后的合理时间戳\n"
        "4. 识别时间演变：「我下周去北京」→ plan；下周后应自动变为「去过北京」→ experience\n"
        "5. 矛盾检测：如果新事实与旧事实矛盾，在 facts_to_evolve 中标记旧记忆\n"
        "6. 低置信度的隐含信息用 confidence=0.5-0.7 并标记 status=pending\n"
        "7. 对闲聊/无信息量的消息不提取任何记忆\n"
        "8. 从提问中提取出的信息不应归因于被问者："
        "「你喜欢吃辣吗？」— 这是提问者的兴趣，不是被问者的事实\n"
        "9. 临时情绪（今天心情不好、好累）用 temporal_nature=VOLATILE, valid_until=24小时后\n\n"
        "## 提取示例\n\n"
        "### 示例 1：明确陈述\n"
        "消息: [1001]: 我是程序员，主要写 Python，在北京工作\n"
        "提取:\n"
        "  - fact_key: 'occupation', fact_value: '程序员'\n"
        "    fact_category: PERSONAL_INFO, temporal_nature: LONG_TERM\n"
        "    source_type: EXPLICIT, confidence: 0.95\n"
        "  - fact_key: 'current_city', fact_value: '北京'\n"
        "    fact_category: PERSONAL_INFO, temporal_nature: LONG_TERM\n"
        "    source_type: EXPLICIT, confidence: 0.95\n"
        "  - fact_key: 'programming_language', fact_value: 'Python'\n"
        "    fact_category: KNOWLEDGE, temporal_nature: LONG_TERM\n"
        "    source_type: EXPLICIT, confidence: 0.95\n\n"
        "### 示例 2：隐含偏好（低置信度，标记 pending）\n"
        "消息: [1001]: 那个牛排馆不错，但素菜馆我更想去\n"
        "提取:\n"
        "  - fact_key: 'dietary_preference', fact_value: '倾向素食'\n"
        "    fact_category: PREFERENCE, temporal_nature: LONG_TERM\n"
        "    source_type: IMPLIED, confidence: 0.65\n"
        "    status: pending\n\n"
        "### 示例 3：不应提取的情况\n"
        "消息: [1001]: 哈哈哈哈哈\n"
        "消息: [1001]: 今天天气不错\n"
        "消息: [主播]: 关注主播不迷路\n"
        "消息: [1002]: 你喜欢吃辣吗？\n"
        "→ 不提取任何记忆（无信息量 / 不是目标用户的发言 / 是提问）\n\n"
        "## 常见错误（必须避免）\n"
        "❌ 不要从提问中提取：「你喜欢吃辣吗？」→ 不提取\n"
        "❌ 不要提取机器人自己的信息\n"
        "❌ 不要提取群公告、系统消息\n"
        "❌ 不要为闲聊设置高置信度\n\n"
        "fact_category: personal_info | preference | plan | experience | knowledge | relationship\n"
        "temporal_nature: permanent | long_term | time_bound | volatile\n"
        "source_type: explicit | implied | conversation | inferred\n"
    )


def _dreaming_user_prompt(
    recent_messages: str,
    existing_memories: str,
    lookback_start: str,
    lookback_end: str,
    target_user_id: int,
    is_group: bool = False,
) -> str:
    scope_note = (
        f"## 提取范围\n\n"
        f"目标用户：user_id={target_user_id}\n"
        f"⚠️ 以下是群聊记录，包含多个用户的发言。"
        f"请**只提取目标用户（user_id={target_user_id}）的个人信息**，"
        f"其他用户的发言仅用于理解对话上下文。"
        f"不要提取其他用户的记忆。\n\n"
        if is_group
        else ""
    )

    return (
        f"{scope_note}"
        f"## 最近消息（{lookback_start} ~ {lookback_end}）\n\n"
        f"{recent_messages}\n\n"
        f"## 该用户现有记忆\n\n"
        f"{existing_memories if existing_memories else '（无已有记忆）'}\n\n"
        "请从最近消息中提取**目标用户**的结构化记忆，同时检测以下情况：\n"
        "- 需要更新的旧事实（facts_to_evolve）\n"
        "- 需要废弃的旧事实（facts_to_deprecate）\n\n"
        "返回格式：MemoryExtractionResult (memories + facts_to_evolve + facts_to_deprecate)\n\n"
        "参考上方系统提示中的 3 个示例进行提取。"
    )


# ── Pipeline 核心 ─────────────────────────────────────────────────


class DreamingPipeline:
    """在每个自然日凌晨 4:00 执行的记忆整理管道。

    处理流程（对每个活跃对话）：
    1. RECALL  — 拉取回溯窗口内的新消息（P4 自适应分档）
    2. EXTRACT — LLM 提取新事实（P0 few-shot 提示词）或规则匹配
    3. COMPARE — MemoryManager 内置 P2 语义去重 + P3 矛盾检测
    4. MERGE   — try accumulate_evidence → upsert_memory（自动版本链）
    5. PRUNE   — 清理过期和孤立记忆
    """

    def __init__(self) -> None:
        self._memory: MemoryManager = get_memory_manager()
        self._messages: MessageDatabase = MessageDatabase()
        self._basic_model: str | None = None
        self._model_loaded = False

    # ── APScheduler 入口（由 clockwork 调用）──────────────────────

    async def run(self, **kwargs) -> dict[str, Any] | None:
        """凌晨 4:00 的定时入口，由 TaskManager 调度。"""
        try:
            from utils.configs import EnvConfig
            self._basic_model = EnvConfig.BASIC_MODEL
        except Exception:
            self._basic_model = None

        start = time.monotonic()
        logger.info("[Dreaming] 开始每日记忆整理...")

        total_processed = 0
        total_extracted = 0
        total_evolved = 0
        total_deduped = 0
        errors = 0

        lookback_ms = _LOOKBACK_HOURS * 3600 * 1000
        since_time = int(time.time() * 1000) - lookback_ms

        try:
            conversations = await self._messages.get_active_conversations_since(
                since_time=since_time,
                max_scopes=_MAX_CONVERSATIONS,
            )
        except Exception as exc:
            logger.error(f"[Dreaming] 查询活跃对话失败: {exc}")
            return {"output_summary": f"Dreaming failed: query error - {exc}", "messages_sent": 0}

        if not conversations:
            logger.info("[Dreaming] 无新消息，跳过本次 Dreaming")
            return {"output_summary": "Dreaming skipped: no new messages", "messages_sent": 0}

        logger.info(f"[Dreaming] 发现 {len(conversations)} 个活跃对话")

        # Step 2-5: 逐个对话处理（P4 自适应分档）
        for conv in conversations:
            user_id = conv["user_id"]
            group_id = conv["group_id"]
            msg_count = conv["message_count"]

            if msg_count < _MIN_MESSAGES_TO_TRIGGER:
                continue

            try:
                extracted, deduped = await self._process_conversation(user_id, group_id)
                total_processed += 1
                if extracted:
                    total_extracted += len(extracted.memories)
                    total_evolved += len(extracted.facts_to_evolve) + len(extracted.facts_to_deprecate)
                total_deduped += deduped
            except Exception as exc:
                errors += 1
                logger.error(f"[Dreaming] 对话处理失败 user={user_id} group={group_id}: {exc}")

        # Step 5: 全局清理
        pruned = 0
        for conv in conversations:
            if conv["message_count"] < _MIN_MESSAGES_TO_TRIGGER:
                continue
            try:
                n = self._memory.check_and_evolve_expired(
                    user_id=conv["user_id"], group_id=conv["group_id"],
                )
                pruned += n
                if n:
                    self._memory.upgrade_pending_memories(
                        user_id=conv["user_id"], group_id=conv["group_id"],
                    )
            except Exception as exc:
                logger.error(f"[Dreaming] 清理过期记忆失败 user={conv['user_id']}: {exc}")

        elapsed = time.monotonic() - start
        summary = (
            f"Dreaming 完成: {total_processed} 对话, "
            f"{total_extracted} 条新记忆, "
            f"{total_evolved} 条演化, "
            f"{total_deduped} 条语义去重, "
            f"{pruned} 条过期清理, "
            f"{errors} 个错误, "
            f"耗时 {elapsed:.1f}s"
        )
        logger.info(f"[Dreaming] {summary}")
        return {"output_summary": summary, "messages_sent": 0}

    # ── P4: 自适应分档处理 ────────────────────────────────────────

    async def _process_conversation(
        self, user_id: int, group_id: int | None
    ) -> tuple[MemoryExtractionResult | None, int]:
        """处理单个对话范围的 Dreaming，返回 (提取结果, 去重次数)。

        P4 自适应策略：
        - > 100 条消息：分段 LLM 提取 → 合并结果
        - 20-100 条：正常 LLM 提取
        - 5-19 条：规则优先 + LLM 兜底（同一数据，成本极低时也可跑 LLM）
        """
        now_ms = int(time.time() * 1000)
        lookback_ms = _LOOKBACK_HOURS * 3600 * 1000
        since_time = now_ms - lookback_ms

        # RECALL
        if group_id is not None:
            messages = await self._messages.select_by_time_range(
                start_time=since_time, end_time=now_ms,
                group_id=group_id, limit=200,
            )
        else:
            messages = await self._messages.select_by_time_range(
                start_time=since_time, end_time=now_ms,
                user_id=user_id, limit=200,
            )
        if not messages:
            return None, 0

        msg_count = len(messages)
        formatted = MessageDatabase.format_for_llm(messages)
        if not formatted.strip():
            return None, 0

        # 已有记忆
        existing = self._memory.get_active_memories(user_id, group_id)
        existing_context = "\n".join(
            f"- [{e.fact_category.value}] {e.fact_key}: {e.fact_value}"
            f" (置信度: {e.confidence:.0%})"
            for e in existing[:15]
        )

        from datetime import datetime, timedelta, timezone
        shanghai = timezone(timedelta(hours=8))
        lookback_start = datetime.fromtimestamp(since_time / 1000, tz=shanghai).strftime("%m-%d %H:%M")
        lookback_end = datetime.fromtimestamp(now_ms / 1000, tz=shanghai).strftime("%m-%d %H:%M")

        # ── P4: 根据消息量选择策略 ──
        if msg_count > _HIGH_VOLUME_THRESHOLD:
            result = await self._extract_high_volume(
                messages, existing_context, lookback_start, lookback_end,
                user_id, group_id,
            )
        elif msg_count >= _MEDIUM_VOLUME_THRESHOLD:
            result = await self._extract_medium_volume(
                formatted, existing_context, lookback_start, lookback_end,
                user_id, group_id,
            )
        else:
            # 低频：规则提取 + LLM 兜底
            rule_result = _rule_based_extract(messages, user_id, group_id)
            # 同时跑 LLM（规则提取结果作为参考注入已有记忆上下文）
            llm_result = await self._extract_medium_volume(
                formatted, existing_context, lookback_start, lookback_end,
                user_id, group_id,
            )
            if llm_result and rule_result:
                # 合并：LLM 结果优先，规则结果去重后追加
                rule_keys = {m.fact_key for m in rule_result.memories}
                for mem in llm_result.memories:
                    if mem.fact_key not in rule_keys:
                        rule_result.memories.append(mem)
                result = rule_result
            else:
                result = llm_result or rule_result

        if result is None or not result.memories:
            return None, 0

        # ── MERGE: 使用 P1 证据累积 + P2 语义去重 ──
        merged_count = 0
        deduped_count = 0
        for mem in result.memories[: _MEMORIES_PER_CONVERSATION_LIMIT]:
            # P1: 先尝试证据累积（同 key 的 pending 记忆）
            accumulated = self._memory.accumulate_evidence(user_id, group_id, mem)
            if accumulated is not mem:
                # 成功累积到已有 pending → 跳过 upsert
                merged_count += 1
                continue

            # P2: 异步语义去重
            dedup_key = await self._memory.resolve_semantic_dedup(mem)
            if dedup_key is not None:
                mem.fact_key = dedup_key
                deduped_count += 1

            # 正常 upsert（含 P3 矛盾检测）
            self._memory.upsert_memory(mem)
            merged_count += 1

        return result, deduped_count

    # ── P4: 高频分段提取 ─────────────────────────────────────────

    async def _extract_high_volume(
        self,
        messages: list[Message],
        existing_context: str,
        lookback_start: str,
        lookback_end: str,
        user_id: int,
        group_id: int | None,
    ) -> MemoryExtractionResult | None:
        """> 100 条消息：分段提取 + 结果合并。

        每段 _SEGMENT_SIZE 条，逐段调用 LLM，最后合并。
        每段的已有记忆上下文包含前一段的提取结果。
        """
        all_memories: list[MemoryEntry] = []
        all_evolve: list[dict] = []
        all_deprecate: list[str] = []

        accumulated_context = existing_context

        for seg_start in range(0, len(messages), _SEGMENT_SIZE):
            segment = messages[seg_start: seg_start + _SEGMENT_SIZE]
            formatted = MessageDatabase.format_for_llm(segment)

            result = await self._extract_memories(
                formatted, accumulated_context, lookback_start, lookback_end,
                user_id, group_id,
            )
            if result:
                all_memories.extend(result.memories)
                all_evolve.extend(result.facts_to_evolve)
                all_deprecate.extend(result.facts_to_deprecate)
                # 将本段提取结果追加到上下文
                accumulated_context += "\n" + "\n".join(
                    f"- [{m.fact_category.value}] {m.fact_key}: {m.fact_value}"
                    for m in result.memories[:5]
                )

        if not all_memories:
            return None

        # 段间去重：同 fact_key 取 latest
        seen: dict[str, MemoryEntry] = {}
        for mem in all_memories:
            if mem.fact_key in seen:
                # 后提取的覆盖先提取的（更近的消息可能有更准确的版本）
                if mem.version > seen[mem.fact_key].version:
                    seen[mem.fact_key] = mem
            else:
                seen[mem.fact_key] = mem

        return MemoryExtractionResult(
            memories=list(seen.values()),
            facts_to_evolve=all_evolve,
            facts_to_deprecate=all_deprecate,
        )

    # ── P4: 中频正常提取 ─────────────────────────────────────────

    async def _extract_medium_volume(
        self,
        formatted: str,
        existing_context: str,
        lookback_start: str,
        lookback_end: str,
        user_id: int,
        group_id: int | None,
    ) -> MemoryExtractionResult | None:
        """20-100 条消息：正常 LLM 提取 + 弹性错误处理。"""
        try:
            return await self._extract_memories(
                formatted, existing_context, lookback_start, lookback_end,
                user_id, group_id,
            )
        except Exception as exc:
            logger.error(f"[Dreaming] 中频提取失败 user={user_id}: {exc}")
            return None

    # ── LLM 提取（P0 few-shot 提示词） ──────────────────────────────

    async def _extract_memories(
        self,
        messages_text: str,
        existing_context: str,
        lookback_start: str,
        lookback_end: str,
        user_id: int,
        group_id: int | None,
    ) -> MemoryExtractionResult | None:
        """调用 SignalLLM 提取结构化记忆。"""
        from utils.configs import EnvConfig
        from utils.signal_llm import SignalLLM

        is_group = group_id is not None
        signal = SignalLLM(model=EnvConfig.SIGNAL_MODEL, timeout=60)
        result = await signal.structured(
            system_prompt=_dreaming_system_prompt(),
            user_prompt=_dreaming_user_prompt(
                messages_text, existing_context, lookback_start, lookback_end,
                target_user_id=user_id, is_group=is_group,
            ),
            schema=MemoryExtractionResult,
        )
        if result is None:
            return None

        # 标准化每条记忆的元数据
        now_ms = int(time.time() * 1000)
        for mem in result.memories:
            if mem.user_id == 0:
                mem.user_id = user_id
            if mem.group_id == 0:
                mem.group_id = group_id or 0
            if mem.created_at == 0:
                mem.created_at = now_ms
            if mem.valid_from == 0:
                mem.valid_from = now_ms

        return result


# ── TaskManager 注册辅助 ──────────────────────────────────────────


def build_dreaming_task_config(engine) -> dict:
    return {
        "job_id": _DREAMING_JOB_ID,
        "name": _DREAMING_JOB_NAME,
        "description": "每天凌晨4:00自动整理所有用户的长期记忆",
        "handler_module": "utils.dreaming_pipeline",
        "handler_function": "run_dreaming_pipeline",
        "trigger_type": "cron",
        "trigger_args": {"hour": "4", "minute": "0", "timezone": "Asia/Shanghai"},
        "group_ids": [],
        "enabled": True,
        "misfire_grace_time": 1800,
    }


# ── 独立的 handler 入口（供 APScheduler 直接调用）─────────────────


async def run_dreaming_pipeline(**kwargs) -> dict | None:
    """APScheduler-compatible 入口函数。"""
    pipeline = DreamingPipeline()
    return await pipeline.run(**kwargs)
