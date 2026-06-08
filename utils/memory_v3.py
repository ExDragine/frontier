# ruff: noqa: C901
"""
V3 结构化记忆系统 — 带时效性、置信度、版本追踪和语义去重。

设计原理（对标 ChatGPT Dreaming V3）：
- 每个 MemoryEntry 有 valid_from/valid_until，追踪事实的时间演变
  例：「7月要去新加坡」→ 7月后自动变为「去过新加坡」
- 版本链追踪同一事实的演化，旧版本标记为 superseded 而非删除
- 置信度评分区分「明确陈述」vs「隐含偏好」vs「推断」
- 交叉验证：pending 记忆需多来源独立确认才升级
- 矛盾检测：值变化 + 方向相反时双方降级为 pending
- 语义去重：同 fact_category 内检测不同 fact_key 的语义相似项

架构：
  MemoryEntry (SQLModel)  →  MemoryManager (CRUD + 时态推理 + 语义去重)
        ↓
  build_context_injection()  →  System prompt 注入
        ↓
  DreamingPipeline (clockwork cron 4:00) → 批量后台整理
"""

import time
from enum import StrEnum

from nonebot import logger
from sqlmodel import JSON, Column, Field, Session, SQLModel, select

# 延迟导入避免触发 database.py 的循环依赖和模块级副作用
# get_engine 在 MemoryManager.__init__ 中按需调用


# ── 枚举定义 ──────────────────────────────────────────────────────


class FactCategory(StrEnum):
    """记忆分类 — 不同类型有不同的生命周期策略。"""

    PERSONAL_INFO = "personal_info"      # 姓名、年龄、职业、地点
    PREFERENCE = "preference"            # 喜好、习惯、交流风格
    PLAN = "plan"                        # 未来计划（自动有过期检测）
    EXPERIENCE = "experience"            # 过往经历
    KNOWLEDGE = "knowledge"              # 用户传授给 bot 的知识
    RELATIONSHIP = "relationship"        # 用户之间的关系


class FactStatus(StrEnum):
    """事实状态 — 追踪生命周期的核心枚举。"""

    ACTIVE = "active"           # 当前有效
    EXPIRED = "expired"         # 时效已过（valid_until < now）
    SUPERSEDED = "superseded"   # 被新版本取代
    DEPRECATED = "deprecated"   # 用户明确删除或降级
    PENDING = "pending"         # 待验证（低置信度，等待更多证据确认）


class SourceType(StrEnum):
    """记忆来源 — 影响初始置信度。"""

    EXPLICIT = "explicit"          # 用户明确陈述「我是素食者」
    IMPLIED = "implied"            # 从行为推断「总是拒绝含肉的推荐」
    CONVERSATION = "conversation"  # 对话上下文中提及
    INFERRED = "inferred"          # LLM 从多轮对话中推断


class TemporalNature(StrEnum):
    """时间性质 — 决定 valid_until 的生成策略。"""

    PERMANENT = "permanent"       # 永久（姓名、生日）
    LONG_TERM = "long_term"       # 长期但可能变（职业、居住地）
    TIME_BOUND = "time_bound"     # 有时效（计划、事件）
    VOLATILE = "volatile"         # 短期有效（当前情绪、临时状态）


# ── 初始置信度映射 ────────────────────────────────────────────────

_SOURCE_CONFIDENCE = {
    SourceType.EXPLICIT: 0.95,
    SourceType.IMPLIED: 0.70,
    SourceType.CONVERSATION: 0.60,
    SourceType.INFERRED: 0.45,
}

_PENDING_CONFIDENCE_THRESHOLD = 0.50
_CONFIRMED_CONFIDENCE_THRESHOLD = 0.70

# P1: 交叉验证最少独立来源数
_MIN_INDEPENDENT_SOURCES = 3      # PENDING → ACTIVE 至少需要
_MIN_SOURCES_FOR_CONFIRM = 2      # 至少2个来源才可以从 inferred 升级

# P3: 矛盾检测 — 语义对立词对
_CONTRADICTION_PATTERNS: list[tuple[str, str]] = [
    ("是", "不是"), ("有", "没有"), ("喜欢", "讨厌"),
    ("喜欢", "不喜欢"), ("会", "不会"), ("能", "不能"),
    ("去", "不去"), ("吃", "不吃"), ("喝", "不喝"),
    ("做", "不做"), ("在", "不在"), ("可以", "不可以"),
]
# P3: 矛盾连续时双方置信度乘数（各打5折）
_CONTRADICTION_CONFIDENCE_MULTIPLIER = 0.5


# ── 数据模型 ──────────────────────────────────────────────────────


class MemoryEntry(SQLModel, table=True):
    """V3 结构化记忆条目。

    设计要点：
    - valid_from/valid_until 定义事实的有效时间窗口
    - status 追踪生命周期（active → expired | superseded | deprecated）
    - version + superseded_by 形成版本链，保留演化历史
    - confidence 用于排序和过滤低质量记忆
    """

    __tablename__ = "memory_entry_v3"

    id: int | None = Field(default=None, primary_key=True)

    # ── 归属 ──
    user_id: int
    group_id: int = Field(default=0)  # 0 = 私聊

    # ── 事实内容 ──
    fact_key: str                           # 唯一标识，如 "travel_plan_2026q3"
    fact_value: str                         # 事实值，如 "新加坡"
    fact_category: FactCategory = Field(default=FactCategory.PERSONAL_INFO)
    temporal_nature: TemporalNature = Field(default=TemporalNature.PERMANENT)

    # ── 可信度 ──
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_type: SourceType = Field(default=SourceType.EXPLICIT)

    # ── 溯源 ──
    source_message_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    extraction_prompt: str | None = None  # 记录提取时用的提示词版本

    # ── 时效性（Unix 毫秒时间戳） ──
    valid_from: int = Field(default_factory=lambda: int(time.time() * 1000))
    valid_until: int | None = None  # None = 永久有效

    # ── 生命周期 ──
    status: FactStatus = Field(default=FactStatus.ACTIVE)
    version: int = Field(default=1)
    superseded_by: int | None = None  # 指向取代此记忆的新 MemoryEntry.id

    # ── 元数据 ──
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))

    # ── 复合索引，加速常见查询 ──
    __table_args__ = (
        None,
    )

    def is_expired(self, now_ms: int | None = None) -> bool:
        """检查本条记忆是否已过期。"""
        if self.valid_until is None:
            return False
        now = now_ms or int(time.time() * 1000)
        return now > self.valid_until

    def age_days(self, now_ms: int | None = None) -> float:
        """记忆创建以来的天数。"""
        now = now_ms or int(time.time() * 1000)
        return (now - self.created_at) / (1000 * 86400)

    def to_context_line(self) -> str:
        """生成用于 system prompt 注入的单行描述。"""
        return f"- {self.fact_key}: {self.fact_value}"


class MemoryExtractionResult(SQLModel):
    """从单轮对话中批量提取的记忆片段。"""

    memories: list[MemoryEntry] = Field(default_factory=list)
    facts_to_evolve: list[dict] = Field(default_factory=list)
    facts_to_deprecate: list[str] = Field(default_factory=list)


class SemanticDedupResult(SQLModel):
    """语义去重 LLM 返回。"""

    matched_fact_key: str = Field(default="NONE", description="匹配的已有 fact_key，无匹配则为 NONE")


# ── 管理器 ────────────────────────────────────────────────────────


class MemoryManager:
    """管理 V3 记忆的存储、查询、时态推理和上下文注入。

    设计要点：
    - 所有写操作通过 Session 管理
    - 缓存热点数据：活跃记忆按 (user_id, group_id) 缓存
    - 时态推理：自动检测过期事实，标记 pending → active 的升级
    - 交叉验证：pending 记忆需多来源独立确认才升级（P1）
    - 语义去重：同 category 内检测相似 key-value 并合并（P2）
    - 矛盾检测：值变化方向相反时降级双方置信度（P3）
    """

    def __init__(self) -> None:
        from utils.database import get_engine as _get_engine

        self._engine = _get_engine()
        MemoryEntry.metadata.create_all(self._engine)
        self._cache: dict[str, list[MemoryEntry]] = {}

    # ── 基础 CRUD ─────────────────────────────────────────────────

    def get_active_memories(
        self, user_id: int, group_id: int | None = None
    ) -> list[MemoryEntry]:
        """获取用户的所有活跃记忆，按置信度降序排列。"""
        gid = group_id or 0
        cache_key = f"{user_id}:{gid}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        with Session(self._engine) as session:
            stmt = (
                select(MemoryEntry)
                .where(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.group_id == gid,
                    MemoryEntry.status == FactStatus.ACTIVE,
                )
                .order_by(MemoryEntry.confidence.desc())
            )
            entries = list(session.exec(stmt).all())
            self._cache[cache_key] = entries
            return entries

    def get_memory_history(
        self, user_id: int, group_id: int | None = None, fact_key: str | None = None
    ) -> list[MemoryEntry]:
        """获取事实的完整版本历史（包括已过期/取代的）。"""
        gid = group_id or 0
        with Session(self._engine) as session:
            conditions = [
                MemoryEntry.user_id == user_id,
                MemoryEntry.group_id == gid,
            ]
            if fact_key:
                conditions.append(MemoryEntry.fact_key == fact_key)
            stmt = (
                select(MemoryEntry)
                .where(*conditions)
                .order_by(MemoryEntry.version.asc())
            )
            return list(session.exec(stmt).all())

    # ── P1: pending 证据累积 ──────────────────────────────────────────

    def find_pending_by_key(
        self, user_id: int, group_id: int | None, fact_key: str
    ) -> MemoryEntry | None:
        """查找同 key 的 pending 记忆（用于累积证据而非覆盖）。"""
        gid = group_id or 0
        with Session(self._engine) as session:
            return session.exec(
                select(MemoryEntry).where(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.group_id == gid,
                    MemoryEntry.fact_key == fact_key,
                    MemoryEntry.status == FactStatus.PENDING,
                )
            ).first()

    def accumulate_evidence(
        self,
        user_id: int,
        group_id: int | None,
        entry: MemoryEntry,
        confidence_boost: float = 0.15,
    ) -> MemoryEntry:
        """对已有的 pending 记忆累积证据：追加 source_message_ids 并提升置信度。

        这是交叉验证的核心机制：
        - 第 1 次出现：INFFERED(0.45) → PENDING(0.45)
        - 第 2 次独立确认：PENDING(0.45+0.15=0.60)
        - 第 3 次独立确认：PENDING(0.60+0.15=0.75) → upgrade_pending 升级为 ACTIVE

        返回更新后的 entry（若不存在 pending 则返回传入的 entry 不做修改）。
        """
        cache_key = f"{user_id}:{group_id or 0}"
        with Session(self._engine) as session:
            existing = session.exec(
                select(MemoryEntry).where(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.group_id == int(group_id or 0),
                    MemoryEntry.fact_key == entry.fact_key,
                    MemoryEntry.status == FactStatus.PENDING,
                )
            ).first()

            if existing is None:
                return entry  # 没有 pending 记录，走正常 upsert

            # 累积来源消息 ID（去重后重新赋值以触发 SQLAlchemy 变更检测）
            new_ids = [
                mid for mid in entry.source_message_ids
                if mid not in (existing.source_message_ids or [])
            ]
            if new_ids:
                existing.source_message_ids = list(existing.source_message_ids or []) + new_ids

            # 提升置信度（上限 1.0）
            existing.confidence = min(1.0, existing.confidence + confidence_boost)
            existing.updated_at = int(time.time() * 1000)

            source_count = len(existing.source_message_ids)
            # 来源足够多 → 从 INFERRED 升级为 IMPLIED
            if source_count >= _MIN_SOURCES_FOR_CONFIRM and existing.source_type == SourceType.INFERRED:
                existing.source_type = SourceType.IMPLIED

            session.add(existing)
            session.commit()
            session.refresh(existing)

            logger.debug(
                f"证据累积: {entry.fact_key} confidence={existing.confidence:.0%} "
                f"sources={source_count}"
            )
            self._invalidate_cache(cache_key)
            return existing

    # ── P2: 语义候选去重 ─────────────────────────────────────────

    def _get_active_in_category(
        self, user_id: int, group_id: int | None, fact_category: FactCategory
    ) -> list[MemoryEntry]:
        """获取同 category 内的所有活跃记忆（用作语义去重的候选集）。"""
        gid = group_id or 0
        with Session(self._engine) as session:
            return list(
                session.exec(
                    select(MemoryEntry).where(
                        MemoryEntry.user_id == user_id,
                        MemoryEntry.group_id == gid,
                        MemoryEntry.status == FactStatus.ACTIVE,
                        MemoryEntry.fact_category == fact_category,
                    )
                ).all()
            )

    async def resolve_semantic_dedup(
        self, new_entry: MemoryEntry
    ) -> str | None:
        """检查新记忆是否与已有的同 category 记忆语义重复。

        用 SignalLLM 一次性比较 new_entry 和所有候选记忆，
        返回命中的已有 fact_key（→ 走版本演化），或 None（→ 正常插入）。

        LLM 成本控制：只在候选集 ≥ 2 时才调用，单条候选直接文本对比。
        """
        candidates = self._get_active_in_category(
            new_entry.user_id, new_entry.group_id, new_entry.fact_category
        )

        # 过滤掉 self（同 key 已由 upsert 处理）
        candidates = [c for c in candidates if c.fact_key != new_entry.fact_key]
        if not candidates:
            return None

        # 单候选 → 快速文本对比
        if len(candidates) == 1:
            c = candidates[0]
            if self._is_near_duplicate_text(new_entry.fact_value, c.fact_value):
                return c.fact_key
            return None

        # 多候选 → LLM 批量比较
        try:
            from utils.configs import EnvConfig
            from utils.signal_llm import SignalLLM

            candidate_lines = "\n".join(
                f"- fact_key={c.fact_key}, fact_value={c.fact_value}"
                for c in candidates[:12]
            )

            prompt = (
                f"## 新记忆\n"
                f"fact_key: {new_entry.fact_key}\n"
                f"fact_value: {new_entry.fact_value}\n"
                f"fact_category: {new_entry.fact_category.value}\n\n"
                f"## 候选已有记忆（同一类别）\n"
                f"{candidate_lines}\n\n"
                "判断新记忆是否与上面任一候选记忆描述的是**同一个事实**（仅表达方式不同）。\n"
                "- 如果匹配：返回匹配的 fact_key（如 'dietary_preference'）\n"
                "- 如果不匹配：返回 'NONE'\n\n"
                "判断标准：\n"
                "- '住在北京' 和 'base in Beijing' → 同一个事实 → 返回已有 fact_key\n"
                "- '住在北京' 和 '在北京上过学' → 不同事实 → 返回 NONE\n"
                "- '喜欢 Python' 和 '用 Python 写代码' → 可能重叠但角度不同 → 返回 NONE\n\n"
                "只返回 fact_key 或 NONE，不要返回其他文字。"
            )

            signal = SignalLLM(model=EnvConfig.SIGNAL_MODEL, timeout=15)
            dedup_result = await signal.structured(
                system_prompt="你是语义去重引擎。判断两段文字是否描述同一事实。",
                user_prompt=prompt,
                schema=SemanticDedupResult,
            )

            if dedup_result is None:
                return None

            raw = dedup_result.matched_fact_key
            if raw and raw.upper() != "NONE":
                # 验证返回的 key 确实在候选集中
                if any(c.fact_key == raw for c in candidates):
                    return raw
            return None

        except Exception as exc:
            logger.debug(f"语义去重 LLM 调用失败: {exc}")
            return None

    @staticmethod
    def _is_near_duplicate_text(value_a: str, value_b: str) -> bool:
        """轻量文本去重：两段话足够相似 → 认为是重复。

        不使用 embedding，用 edit 距离 + 公共子串的简易策略。
        """
        a = value_a.lower().strip()
        b = value_b.lower().strip()
        if a == b:
            return True

        # 完全包含
        if a in b or b in a:
            return len(min(a, b, key=len)) >= 2

        # 公共词 ≥ 80%
        words_a = set(a.replace(",", " ").split())
        words_b = set(b.replace(",", " ").split())
        if not words_a or not words_b:
            return False
        intersection = words_a & words_b
        if len(intersection) == 0:
            return False
        overlap = len(intersection) / min(len(words_a), len(words_b))
        return overlap >= 0.8

    # ── P3: 矛盾检测 ──────────────────────────────────────────

    @staticmethod
    def _detect_contradiction(old_value: str, new_value: str) -> bool:
        """基于语义对立词的轻量矛盾检测。

        检查 old_value 和 new_value 是否存在方向相反的表述。
        例如："是素食者" vs "吃牛排" → 检测到「是/否」类对立。
        """
        old_lower = old_value.lower()
        new_lower = new_value.lower()

        for positive, negative in _CONTRADICTION_PATTERNS:
            # 旧值含正面词 + 新值含对应反面词 → 矛盾
            if positive in old_lower and negative in new_lower:
                return True
            # 旧值含反面词 + 新值含对应正面词 → 矛盾
            if negative in old_lower and positive in new_lower:
                return True

        return False

    # ── 核心 upsert（含 P3 矛盾检测）───────────────────────────

    def upsert_memory(self, entry: MemoryEntry) -> MemoryEntry:  # noqa: C901
        """插入或更新一条记忆。

        处理策略（按优先级）：
        1. 无冲突 → 直接插入
        2. 值完全相同 → 重新确认，提升置信度（不创建新版本）
        3. 值不同 + 语义矛盾 → 双方降级为 PENDING，置信度各打5折
        4. 值不同 + 非矛盾 → 版本演化（旧 SUPERSEDED → 新 ACTIVE）
        """
        entry.updated_at = int(time.time() * 1000)
        cache_key = f"{entry.user_id}:{entry.group_id}"
        now_ms = entry.updated_at

        with Session(self._engine) as session:
            existing = session.exec(
                select(MemoryEntry).where(
                    MemoryEntry.user_id == entry.user_id,
                    MemoryEntry.group_id == entry.group_id,
                    MemoryEntry.fact_key == entry.fact_key,
                    MemoryEntry.status == FactStatus.ACTIVE,
                )
            ).first()

            if existing is None:
                # ── 情况 1: 全新记忆 ──
                session.add(entry)
                session.commit()
                session.refresh(entry)
                self._invalidate_cache(cache_key)
                return entry

            # ── 值完全相同 → 重新确认（P1 交叉验证的同步入口） ──
            if existing.fact_value.strip() == entry.fact_value.strip():
                existing.confidence = min(1.0, existing.confidence + 0.05)
                existing.updated_at = now_ms

                # 合并来源消息 ID
                new_ids = [
                    mid for mid in entry.source_message_ids
                    if mid not in (existing.source_message_ids or [])
                ]
                if new_ids:
                    existing.source_message_ids = list(existing.source_message_ids or []) + new_ids

                # 来源足够多 → 升级 INFERRED → IMPLIED
                if (
                    len(existing.source_message_ids) >= _MIN_SOURCES_FOR_CONFIRM
                    and existing.source_type == SourceType.INFERRED
                ):
                    existing.source_type = SourceType.IMPLIED

                session.add(existing)
                session.commit()
                session.refresh(existing)

                logger.debug(
                    f"记忆重新确认: {entry.fact_key} confidence={existing.confidence:.0%} "
                    f"sources={len(existing.source_message_ids)}"
                )
                self._invalidate_cache(cache_key)
                return existing

            # ── 值不同 → 检查是否矛盾（P3） ──
            if self._detect_contradiction(existing.fact_value, entry.fact_value):
                existing.confidence *= _CONTRADICTION_CONFIDENCE_MULTIPLIER
                existing.status = FactStatus.PENDING
                existing.updated_at = now_ms

                entry.confidence *= _CONTRADICTION_CONFIDENCE_MULTIPLIER
                entry.status = FactStatus.PENDING
                entry.version = existing.version + 1

                session.add(existing)
                session.add(entry)
                session.flush()
                existing.superseded_by = entry.id
                session.add(existing)
                session.commit()
                session.refresh(entry)

                logger.warning(
                    f"矛盾检测: {entry.fact_key} "
                    f"v{existing.version}({existing.fact_value}) ↔ "
                    f"v{entry.version}({entry.fact_value}) "
                    f"双方降级为 PENDING"
                )
                self._invalidate_cache(cache_key)
                return entry

            # ── 值不同 + 非矛盾 → 正常版本演化 ──
            entry.version = existing.version + 1
            existing.status = FactStatus.SUPERSEDED
            existing.superseded_by = None
            existing.updated_at = now_ms
            session.add(existing)
            session.add(entry)
            session.flush()
            existing.superseded_by = entry.id
            session.add(existing)
            session.commit()
            session.refresh(entry)

            logger.debug(
                f"记忆演化: {entry.fact_key} v{existing.version}→v{entry.version} "
                f"({existing.fact_value} → {entry.fact_value})"
            )

        self._invalidate_cache(cache_key)
        return entry

    def deprecate_memory(self, entry_id: int) -> bool:
        """用户主动废弃一条记忆。"""
        with Session(self._engine) as session:
            entry = session.get(MemoryEntry, entry_id)
            if entry is None:
                return False
            entry.status = FactStatus.DEPRECATED
            entry.updated_at = int(time.time() * 1000)
            session.add(entry)
            session.commit()
            cache_key = f"{entry.user_id}:{entry.group_id}"
            self._invalidate_cache(cache_key)
            return True

    # ── 时态推理 ─────────────────────────────────────────────────

    def check_and_evolve_expired(self, user_id: int, group_id: int | None = None) -> int:
        """检查并标记已过期的记忆。

        仅处理 valid_until < now 的 TIME_BOUND / VOLATILE 记忆。
        PERMANENT 和 LONG_TERM 记忆不受影响。

        返回值：标记为过期的条目数。
        """
        now_ms = int(time.time() * 1000)
        gid = group_id or 0
        conditions = [
            MemoryEntry.user_id == user_id,
            MemoryEntry.group_id == gid,
            MemoryEntry.status == FactStatus.ACTIVE,
            MemoryEntry.valid_until.is_not(None),
            MemoryEntry.valid_until < now_ms,
        ]

        with Session(self._engine) as session:
            stmt = select(MemoryEntry).where(*conditions)
            expired = list(session.exec(stmt).all())
            for entry in expired:
                entry.status = FactStatus.EXPIRED
                entry.updated_at = now_ms
                session.add(entry)
            session.commit()
            if expired:
                self._invalidate_cache(f"{user_id}:{gid}")
                logger.info(f"标记 {len(expired)} 条过期记忆 user={user_id}")
            return len(expired)

    # ── P1: 置信度升级（含交叉验证）───────────────────────────────

    def upgrade_pending_memories(self, user_id: int, group_id: int | None = None) -> int:
        """将满足交叉验证条件的 pending 记忆升级为 active。

        升级条件（按来源多样性分档）：
        - INFERRED 来源（LLM 推测）：需要 ≥ _MIN_SOURCES_FOR_CONFIRM 个独立来源，
          且置信度 ≥ _CONFIRMED_CONFIDENCE_THRESHOLD
        - IMPLIED 来源（行为推断）：需要 ≥ _MIN_SOURCES_FOR_CONFIRM 个来源，
          或置信度 ≥ 0.80（用户已实质上多次确认）
        - EXPLICIT 来源（用户明确说）但置信度低于阈值 → 直接升级（用户已经说了）
        - 来源 < _MIN_SOURCES_FOR_CONFIRM → 保持 pending，等待更多证据

        返回值：升级为 active 的条目数。
        """
        gid = group_id or 0
        now_ms = int(time.time() * 1000)
        upgraded = 0

        with Session(self._engine) as session:
            stmt = select(MemoryEntry).where(
                MemoryEntry.user_id == user_id,
                MemoryEntry.group_id == gid,
                MemoryEntry.status == FactStatus.PENDING,
            )
            candidates = list(session.exec(stmt).all())

            for entry in candidates:
                source_count = len(entry.source_message_ids)
                should_upgrade = False

                if entry.source_type == SourceType.EXPLICIT:
                    # 用户明确陈述 → 不需要交叉验证，直接升级
                    should_upgrade = entry.confidence >= _PENDING_CONFIDENCE_THRESHOLD
                elif entry.source_type == SourceType.IMPLIED:
                    # 行为推断 → 需要多次独立确认或高置信度
                    should_upgrade = (
                        source_count >= _MIN_SOURCES_FOR_CONFIRM
                        or entry.confidence >= 0.80
                    ) and entry.confidence >= _CONFIRMED_CONFIDENCE_THRESHOLD
                elif entry.source_type in (SourceType.INFERRED, SourceType.CONVERSATION):
                    # LLM 推测 → 需要 ≥ _MIN_INDEPENDENT_SOURCES 个独立来源
                    should_upgrade = (
                        source_count >= _MIN_INDEPENDENT_SOURCES
                        and entry.confidence >= _CONFIRMED_CONFIDENCE_THRESHOLD
                    )
                else:
                    should_upgrade = entry.confidence >= _CONFIRMED_CONFIDENCE_THRESHOLD

                if should_upgrade:
                    entry.status = FactStatus.ACTIVE
                    entry.updated_at = now_ms
                    session.add(entry)
                    upgraded += 1
                    logger.info(
                        f"置信度升级: {entry.fact_key} PENDING→ACTIVE "
                        f"confidence={entry.confidence:.0%} sources={source_count}"
                    )

            session.commit()
            if upgraded:
                self._invalidate_cache(f"{user_id}:{gid}")

        return upgraded

    # ── 上下文注入 ────────────────────────────────────────────────

    def build_context_injection(
        self, user_id: int, group_id: int | None = None, max_entries: int = 15
    ) -> str:
        """构建用于 system prompt 的记忆上下文注入。

        策略：
        - 优先注入高置信度 + 高相关性的记忆
        - 按 fact_category 分组展示
        - 省略低置信度 (pending) 条目
        """
        entries = self.get_active_memories(user_id, group_id)

        # 过滤：只保留置信度 >= 确认阈值或用户明确陈述的记忆
        confident = [
            e for e in entries
            if e.confidence >= _CONFIRMED_CONFIDENCE_THRESHOLD
            or e.source_type == SourceType.EXPLICIT
        ][:max_entries]

        if not confident:
            return ""

        # 按类别分组
        grouped: dict[FactCategory, list[MemoryEntry]] = {}
        for e in confident:
            grouped.setdefault(e.fact_category, []).append(e)

        lines = ["## 长期记忆（V3）"]
        category_labels = {
            FactCategory.PERSONAL_INFO: "个人信息",
            FactCategory.PREFERENCE: "偏好习惯",
            FactCategory.PLAN: "计划安排",
            FactCategory.EXPERIENCE: "过往经历",
            FactCategory.KNOWLEDGE: "已知知识",
            FactCategory.RELATIONSHIP: "人际关系",
        }

        for cat, mems in grouped.items():
            label = category_labels.get(cat, cat.value)
            lines.append(f"### {label}")
            for m in mems:
                lines.append(m.to_context_line())

        return "\n".join(lines)

    # ── 缓存管理 ──────────────────────────────────────────────────

    def _invalidate_cache(self, cache_key: str) -> None:
        self._cache.pop(cache_key, None)

    def invalidate_all(self) -> None:
        self._cache.clear()

    # ── 实时提取（规则优先，零 LLM 成本） ──────────────────────────

    async def extract_from_conversation(
        self,
        user_id: int,
        group_id: int | None,
        user_message: str,
        assistant_response: str,
    ) -> MemoryExtractionResult:
        """每轮对话后异步提取记忆（纯规则匹配，不调 LLM）。

        设计决策：
        - 实时提取只用规则，零 LLM 成本。匹配「我是…」「我喜欢…」等
          明确陈述模式，标记为 EXPLICIT/ACTIVE，立即可用。
        - 隐含偏好、推断、多轮上下文 → 交给 DreamingPipeline（凌晨 4:00）
          用 P0 few-shot LLM 高质量处理。
        - 避免重复提取：同一条消息不在实时和 Dreaming 中各调一次 LLM。
        """
        from utils.database import Message

        now_ms = int(time.time() * 1000)
        gid = group_id or 0

        messages = [
            Message(
                time=now_ms, user_id=user_id, role="user",
                user_name="", content=user_message,
            )
        ]

        result = _rule_based_extract(messages, user_id, group_id)
        if result is None or not result.memories:
            return MemoryExtractionResult()

        # 规则只匹配明确陈述 → 标记为 high-confidence ACTIVE
        for mem in result.memories:
            mem.user_id = user_id
            mem.group_id = gid
            mem.source_type = SourceType.EXPLICIT
            mem.confidence = 0.90
            mem.status = FactStatus.ACTIVE
            if mem.created_at == 0:
                mem.created_at = now_ms
            if mem.valid_from == 0:
                mem.valid_from = now_ms

        for mem in result.memories:
            self.upsert_memory(mem)

        return result


# ── 规则提取（实时 + Dreaming 低频共用） ──────────────────────────

_SIMPLE_EXTRACTION_PATTERNS: list[tuple[str, str, FactCategory, TemporalNature]] = [
    ("我是", "occupation", FactCategory.PERSONAL_INFO, TemporalNature.LONG_TERM),
    ("我在", "current_city", FactCategory.PERSONAL_INFO, TemporalNature.LONG_TERM),
    ("我喜欢", "preference", FactCategory.PREFERENCE, TemporalNature.LONG_TERM),
    ("我不喜欢", "dislike", FactCategory.PREFERENCE, TemporalNature.LONG_TERM),
    ("我住在", "residence", FactCategory.PERSONAL_INFO, TemporalNature.LONG_TERM),
    ("我的生日", "birthday", FactCategory.PERSONAL_INFO, TemporalNature.PERMANENT),
    ("我会", "skill", FactCategory.KNOWLEDGE, TemporalNature.LONG_TERM),
    ("我在学", "learning", FactCategory.KNOWLEDGE, TemporalNature.LONG_TERM),
    ("我下月", "plan", FactCategory.PLAN, TemporalNature.TIME_BOUND),
    ("我下周", "plan", FactCategory.PLAN, TemporalNature.TIME_BOUND),
    ("我明天", "plan", FactCategory.PLAN, TemporalNature.TIME_BOUND),
]


def _rule_based_extract(
    messages: list,
    user_id: int,
    group_id: int | None,
) -> MemoryExtractionResult | None:
    """对低频对话使用关键词规则快速提取。

    不用 LLM，直接字符串匹配。成本为零。
    提取结果是 PENDING 状态（Dreaming 侧使用），
    实时提取侧会覆盖为 EXPLICIT/ACTIVE。
    """
    now_ms = int(time.time() * 1000)
    extracted: list[MemoryEntry] = []

    for msg in messages:
        if msg.user_id != user_id:
            continue
        content = msg.content or ""
        if len(content) < 3:
            continue

        for keyword, fact_key, category, temporal in _SIMPLE_EXTRACTION_PATTERNS:
            idx = content.find(keyword)
            if idx == -1:
                continue

            after = content[idx + len(keyword):]
            for delim in ("。", "，", ",", ".", "\n", "！", "？", "!", "?"):
                if delim in after:
                    after = after[:after.index(delim)]
            value = after.strip()[:40]
            if len(value) < 1:
                continue

            entry = MemoryEntry(
                user_id=user_id,
                group_id=group_id or 0,
                fact_key=f"{fact_key}_{len(extracted)}",
                fact_value=value,
                fact_category=category,
                temporal_nature=temporal,
                confidence=0.55,
                source_type=SourceType.IMPLIED,
                source_message_ids=[int(msg.msg_id)] if getattr(msg, "msg_id", None) else [],
                status=FactStatus.PENDING,
                created_at=now_ms,
                valid_from=now_ms,
                valid_until=now_ms + 86400000 if temporal == TemporalNature.VOLATILE else None,
            )
            extracted.append(entry)
            break

    if not extracted:
        return None

    return MemoryExtractionResult(memories=extracted)



# ── 单例 ──────────────────────────────────────────────────────────

_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """获取全局 MemoryManager 单例。"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
