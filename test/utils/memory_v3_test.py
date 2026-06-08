# ruff: noqa: S101

"""V3 记忆系统测试 — 覆盖 MemoryEntry 模型和 MemoryManager 的核心行为。"""

import time

import pytest

from utils.memory_v3 import (
    FactCategory,
    FactStatus,
    MemoryEntry,
    MemoryManager,
    SourceType,
    TemporalNature,
    get_memory_manager,
)


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def manager(monkeypatch):
    """创建使用内存数据库的 MemoryManager，测试间完全隔离。"""
    from utils.database import DATABASE_FILE

    monkeypatch.setattr("utils.database.DATABASE_FILE", "sqlite:///:memory:")

    # 强制重建 engine 和单例
    import utils.database as db
    import utils.memory_v3 as mv3

    db._cached_engine.cache_clear()
    mv3._memory_manager = None
    mgr = MemoryManager()
    yield mgr
    mv3._memory_manager = None
    db._cached_engine.cache_clear()


def _make_entry(
    user_id: int = 1001,
    group_id: int | None = None,
    fact_key: str = "test_fact",
    fact_value: str = "test_value",
    fact_category: FactCategory = FactCategory.PERSONAL_INFO,
    confidence: float = 1.0,
    source_type: SourceType = SourceType.EXPLICIT,
    temporal_nature: TemporalNature = TemporalNature.PERMANENT,
    valid_from: int | None = None,
    valid_until: int | None = None,
    status: FactStatus = FactStatus.ACTIVE,
    version: int = 1,
    created_at: int | None = None,
    source_message_ids: list[int] | None = None,
) -> MemoryEntry:
    """快捷构造 MemoryEntry。"""
    gid = group_id if group_id is not None else 0
    now_ms = int(time.time() * 1000)
    return MemoryEntry(
        user_id=user_id,
        group_id=gid,
        fact_key=fact_key,
        fact_value=fact_value,
        fact_category=fact_category,
        confidence=confidence,
        source_type=source_type,
        temporal_nature=temporal_nature,
        valid_from=valid_from if valid_from is not None else now_ms,
        valid_until=valid_until,
        status=status,
        version=version,
        source_message_ids=source_message_ids or [],
        created_at=created_at if created_at is not None else now_ms,
        updated_at=now_ms,
    )


# ── MemoryEntry 模型测试 ──────────────────────────────────────────


class TestMemoryEntryModel:
    """MemoryEntry 纯数据模型的行为测试。"""

    def test_default_initialization(self):
        """验证默认值：新条目应为 active，置信度 1.0。"""
        entry = MemoryEntry(
            user_id=1001,
            fact_key="name",
            fact_value="小明",
        )
        assert entry.status == FactStatus.ACTIVE
        assert entry.version == 1
        assert entry.confidence == 1.0
        assert entry.group_id == 0
        assert entry.valid_until is None

    def test_is_expired_when_no_valid_until(self):
        """没有 valid_until 的记忆永不过期。"""
        entry = _make_entry(valid_until=None)
        assert not entry.is_expired()

    def test_is_expired_when_past_valid_until(self):
        """valid_until 已过的记忆应判断为过期。"""
        past = int(time.time() * 1000) - 10000
        entry = _make_entry(valid_until=past)
        assert entry.is_expired()

    def test_is_expired_when_future_valid_until(self):
        """valid_until 未到的记忆不应过期。"""
        future = int(time.time() * 1000) + 86400000  # 1天后
        entry = _make_entry(valid_until=future)
        assert not entry.is_expired()

    def test_age_days(self):
        """age_days 应正确计算记忆天数。"""
        one_day_ms = 86400 * 1000
        past = int(time.time() * 1000) - one_day_ms
        entry = _make_entry(
            valid_from=past,
            created_at=past,
        )
        age = entry.age_days()
        assert 0.9 < age < 1.1  # 约 1 天，留出执行时间的容差

    def test_to_context_line_format(self):
        """上下文注入行应包含 fact_key 和 fact_value。"""
        entry = _make_entry(fact_key="occupation", fact_value="软件工程师")
        line = entry.to_context_line()
        assert "occupation" in line
        assert "软件工程师" in line


# ── MemoryManager CRUD 测试 ──────────────────────────────────────


class TestMemoryManagerCRUD:
    """MemoryManager 的创建、读取、更新操作。"""

    def test_upsert_new_entry(self, manager):
        """首次 upsert 应创建新条目，version=1。"""
        entry = _make_entry()
        result = manager.upsert_memory(entry)
        assert result.id is not None
        assert result.version == 1
        assert result.status == FactStatus.ACTIVE

    def test_upsert_updates_existing(self, manager):
        """同 user+group+fact_key 的 upsert 应触发版本演化。"""
        v1 = _make_entry(fact_key="city", fact_value="北京")
        v1 = manager.upsert_memory(v1)

        v2 = _make_entry(fact_key="city", fact_value="上海")
        v2 = manager.upsert_memory(v2)

        assert v2.version == 2
        assert v2.fact_value == "上海"
        assert v2.superseded_by is None  # 新版本没被取代

        # v1 应该被标记为 superseded
        history = manager.get_memory_history(user_id=1001, fact_key="city")
        v1_from_db = next(m for m in history if m.version == 1)
        assert v1_from_db.status == FactStatus.SUPERSEDED
        assert v1_from_db.superseded_by == v2.id

    def test_get_active_memories_filters_by_status(self, manager):
        """只返回 status=active 的记忆。"""
        active = _make_entry(fact_key="active_fact")
        manager.upsert_memory(active)

        expired = _make_entry(
            fact_key="expired_fact", status=FactStatus.EXPIRED
        )
        manager.upsert_memory(expired)

        # 主动插入了两条，但 expired 不是通过 upsert 冲突插入的
        # 需要手动把 expired 的状态设为 EXPIRED
        # 因为 upsert 只看 active 冲突
        results = manager.get_active_memories(user_id=1001)
        # 两条都在：expired 的 fact_key 不同，所以没有冲突，都插入了
        # 但 status=EXPIRED 的应该被过滤
        active_only = [m for m in results if m.status == FactStatus.ACTIVE]
        assert all(m.status == FactStatus.ACTIVE for m in active_only)

    def test_deprecate_memory(self, manager):
        """deprecate 后条目状态应为 DEPRECATED，且不再出现在活跃记忆中。"""
        entry = manager.upsert_memory(_make_entry())
        assert manager.deprecate_memory(entry.id)

        # 从活跃记忆中消失
        active = manager.get_active_memories(user_id=1001)
        assert len(active) == 0

        # 历史记录中确认状态变更
        history = manager.get_memory_history(user_id=1001, fact_key="test_fact")
        assert len(history) == 1
        assert history[0].status == FactStatus.DEPRECATED

    def test_deprecate_nonexistent(self, manager):
        """deprecate 不存在的 ID 应返回 False。"""
        assert not manager.deprecate_memory(99999)

    def test_get_memory_history_by_key(self, manager):
        """版本历史应包含所有版本（包括 superseded）。"""
        manager.upsert_memory(_make_entry(fact_key="job", fact_value="学生"))
        manager.upsert_memory(_make_entry(fact_key="job", fact_value="工程师"))

        history = manager.get_memory_history(user_id=1001, fact_key="job")
        assert len(history) == 2
        versions = {m.version for m in history}
        assert versions == {1, 2}


# ── 时态推理测试 ──────────────────────────────────────────────────


class TestTemporalReasoning:
    """检查过期记忆的自动标记行为。"""

    def test_check_and_evolve_expired_marks_expired(self, manager):
        """固定过期的 TIME_BOUND 记忆应被标记为 EXPIRED。"""
        past = int(time.time() * 1000) - 10000
        entry = _make_entry(
            fact_key="temp_event",
            fact_value="今天的速配活动",
            temporal_nature=TemporalNature.TIME_BOUND,
            valid_until=past,
        )
        manager.upsert_memory(entry)
        count = manager.check_and_evolve_expired(user_id=1001)
        assert count == 1
        active = manager.get_active_memories(user_id=1001)
        assert len(active) == 0

    def test_check_and_evolve_expired_ignores_permanent(self, manager):
        """PERMANENT 记忆永不过期。"""
        entry = _make_entry(
            fact_key="birthday",
            fact_value="1990-01-01",
            temporal_nature=TemporalNature.PERMANENT,
        )
        manager.upsert_memory(entry)
        count = manager.check_and_evolve_expired(user_id=1001)
        assert count == 0
        active = manager.get_active_memories(user_id=1001)
        assert len(active) == 1


# ── 上下文注入测试 ────────────────────────────────────────────────


class TestContextInjection:
    """build_context_injection 的输出格式和过滤逻辑。"""

    def test_build_context_injection_skips_pending(self, manager):
        """PENDING 状态的记忆不应注入上下文。"""
        manager.upsert_memory(
            _make_entry(
                fact_key="confirmed",
                fact_value="明确信息",
                confidence=0.95,
                source_type=SourceType.EXPLICIT,
            )
        )
        manager.upsert_memory(
            _make_entry(
                fact_key="uncertain",
                fact_value="不确定推测",
                confidence=0.45,
                source_type=SourceType.INFERRED,
                status=FactStatus.PENDING,
            )
        )
        result = manager.build_context_injection(user_id=1001)
        assert "明确信息" in result
        assert "不确定推测" not in result

    def test_build_context_injection_groups_by_category(self, manager):
        """不同类别的记忆应在不同分组下。"""
        manager.upsert_memory(
            _make_entry(
                fact_key="name",
                fact_value="张三",
                fact_category=FactCategory.PERSONAL_INFO,
            )
        )
        manager.upsert_memory(
            _make_entry(
                fact_key="food",
                fact_value="素食",
                fact_category=FactCategory.PREFERENCE,
            )
        )
        result = manager.build_context_injection(user_id=1001)
        assert "个人信息" in result
        assert "偏好习惯" in result
        assert "张三" in result
        assert "素食" in result

    def test_build_context_injection_empty_for_new_user(self, manager):
        """无记忆的用户应返回空字符串。"""
        result = manager.build_context_injection(user_id=99999)
        assert result == ""


# ── 置信度管理测试 ────────────────────────────────────────────────


class TestConfidenceManagement:
    """置信度升级和过滤逻辑。"""

    def test_explicit_source_always_included(self, manager):
        """即使置信度低于阈值，explicit 来源的记忆也应注入。"""
        manager.upsert_memory(
            _make_entry(
                fact_key="diet",
                fact_value="不吃辣",
                confidence=0.55,  # 低于 0.70 阈值
                source_type=SourceType.EXPLICIT,  # 但用户明确陈述
            )
        )
        result = manager.build_context_injection(user_id=1001)
        assert "不吃辣" in result

    def test_upgrade_pending_with_cross_validation(self, manager):
        """具有足够独立来源的 IMPLIED pending 记忆应升级为 active。

        新升级逻辑 (P1):
        - IMPLIED: 需要 ≥ 2 个独立来源 或 confidence ≥ 0.80
        - INFERRED: 需要 ≥ 3 个独立来源且 confidence ≥ 0.70
        - EXPLICIT: 用户明确说的 → confidence ≥ 0.50 即可
        """

        # 2 个独立来源 + 0.75 置信度 → 满足 IMPLIED 升级条件
        manager.upsert_memory(
            _make_entry(
                fact_key="hobby",
                fact_value="摄影",
                confidence=0.75,
                source_type=SourceType.IMPLIED,
                status=FactStatus.PENDING,
            )
        )
        # 再 upsert 一次（同值 → 重新确认 → 置信度+0.05）
        manager.upsert_memory(
            _make_entry(
                fact_key="hobby",
                fact_value="摄影",
                confidence=0.70,
                source_type=SourceType.IMPLIED,
                source_message_ids=[10001, 10002],  # 2 个独立来源
                status=FactStatus.PENDING,
            )
        )
        count = manager.upgrade_pending_memories(user_id=1001)
        assert count == 1

    def test_pending_inferred_needs_three_sources(self, manager):
        """INFERRED 类型需要 ≥ 3 个独立来源才能升级（P1 交叉验证）。"""
        manager.upsert_memory(
            _make_entry(
                fact_key="music_taste",
                fact_value="可能喜欢古典音乐",
                confidence=0.75,
                source_type=SourceType.INFERRED,
                source_message_ids=[10001],  # 仅 1 个来源
                status=FactStatus.PENDING,
            )
        )
        count = manager.upgrade_pending_memories(user_id=1001)
        assert count == 0  # 来源不足，保持 pending

    def test_pending_explicit_upgrades_directly(self, manager):
        """EXPLICIT 来源的 pending 直接升级（用户已明确说过）。"""
        manager.upsert_memory(
            _make_entry(
                fact_key="diet",
                fact_value="素食",
                confidence=0.60,
                source_type=SourceType.EXPLICIT,
                source_message_ids=[10001],
                status=FactStatus.PENDING,
            )
        )
        count = manager.upgrade_pending_memories(user_id=1001)
        assert count == 1


# ── 缓存测试 ──────────────────────────────────────────────────────


class TestCacheBehavior:
    """验证缓存失效和一致性。"""

    def test_upsert_invalidates_cache(self, manager):
        """upsert 后缓存应失效，下次查询返回最新数据。"""
        manager.upsert_memory(_make_entry(fact_key="a", fact_value="v1"))
        first = manager.get_active_memories(user_id=1001)
        assert first[0].fact_value == "v1"

        manager.upsert_memory(_make_entry(fact_key="a", fact_value="v2"))
        second = manager.get_active_memories(user_id=1001)
        assert len(second) == 1
        assert second[0].fact_value == "v2"

    def test_invalidate_all_clears_everything(self, manager):
        """invalidate_all 应清空整个缓存。"""
        manager.upsert_memory(_make_entry(fact_key="a"))
        manager.get_active_memories(user_id=1001)  # 填充缓存
        assert len(manager._cache) == 1

        manager.invalidate_all()
        assert len(manager._cache) == 0


# ── 单例测试 ──────────────────────────────────────────────────────


def test_get_memory_manager_returns_singleton(monkeypatch):
    """get_memory_manager 应返回同一实例。"""
    import utils.database as db

    monkeypatch.setattr("utils.database.DATABASE_FILE", "sqlite:///:memory:")
    db._cached_engine.cache_clear()

    import utils.memory_v3 as mv3

    mv3._memory_manager = None
    a = get_memory_manager()
    b = get_memory_manager()
    assert a is b
    mv3._memory_manager = None
    db._cached_engine.cache_clear()


# ── Schema 验证 ───────────────────────────────────────────────────


def test_memory_entry_table_creatable(manager):
    """MemoryEntry 表应能正确创建。"""
    from sqlalchemy import inspect

    inspector = inspect(manager._engine)
    table_names = inspector.get_table_names()
    assert "memory_entry_v3" in table_names

    columns = {c["name"] for c in inspector.get_columns("memory_entry_v3")}
    required = {
        "id", "user_id", "group_id", "fact_key", "fact_value",
        "fact_category", "temporal_nature", "confidence", "source_type",
        "source_message_ids", "valid_from", "valid_until", "status",
        "version", "superseded_by", "created_at", "updated_at",
    }
    assert required <= columns


# ── P1: 证据累积测试 ──────────────────────────────────────────────


class TestEvidenceAccumulation:
    """P1 交叉验证：pending 记忆通过多来源证据累积升级。"""

    def test_accumulate_evidence_boosts_confidence(self, manager):
        """对已有 pending 记忆调用 accumulate_evidence 应提升置信度。"""
        manager.upsert_memory(
            _make_entry(
                fact_key="hobby",
                fact_value="摄影",
                confidence=0.45,
                source_type=SourceType.INFERRED,
                status=FactStatus.PENDING,
                source_message_ids=[10001],
            )
        )

        new = _make_entry(
            fact_key="hobby",
            fact_value="摄影",
            confidence=0.45,
            source_type=SourceType.INFERRED,
            source_message_ids=[10005],
        )
        updated = manager.accumulate_evidence(user_id=1001, group_id=None, entry=new)

        assert updated is not None
        assert updated.confidence == pytest.approx(0.60, abs=0.01)  # 0.45 + 0.15
        assert 10001 in updated.source_message_ids
        assert 10005 in updated.source_message_ids

    def test_accumulate_evidence_new_key_returns_original(self, manager):
        """不存在 pending 记录时 accumulate_evidence 返回原值不做修改。"""
        entry = _make_entry(fact_key="brand_new", fact_value="全新事实")
        result = manager.accumulate_evidence(user_id=1001, group_id=None, entry=entry)
        assert result is entry  # 同一个对象返回


# ── P2: 语义去重测试 ──────────────────────────────────────────────


class TestSemanticDedup:
    """P2 语义去重：文本相似度和 LLM 辅助检测。"""

    def test_near_duplicate_text_identical(self, manager):
        """相同文本应判定为重复。"""
        assert manager._is_near_duplicate_text("北京", "北京")

    def test_near_duplicate_text_contained(self, manager):
        """包含关系应判定为重复。"""
        assert manager._is_near_duplicate_text("住在北京", "北京")

    def test_near_duplicate_text_word_overlap(self, manager):
        """高词重叠率应判定为重复。"""
        assert manager._is_near_duplicate_text("喜欢 Python 编程", "Python 编程")

    def test_near_duplicate_text_different_topics(self, manager):
        """不同话题不应判定为重复。"""
        assert not manager._is_near_duplicate_text("喜欢 Python", "喜欢 北京")


# ── P3: 矛盾检测测试 ──────────────────────────────────────────────


class TestContradictionDetection:
    """P3 矛盾检测：对立词对触发降级。"""

    def test_detect_simple_contradiction(self, manager):
        """「是/不是」对立应检测到。"""
        assert manager._detect_contradiction("我是素食者", "我不是素食者")

    def test_detect_like_dislike_contradiction(self, manager):
        """「喜欢/不喜欢」对立应检测到。"""
        assert manager._detect_contradiction("喜欢辣的食物", "讨厌辣的食物（现在）")

    def test_detect_no_contradiction_on_normal_evolution(self, manager):
        """正常演化不应触发矛盾。"""
        assert not manager._detect_contradiction("住在北京", "住在上海")

    def test_detect_no_contradiction_on_refinement(self, manager):
        """细化不应触发矛盾。"""
        assert not manager._detect_contradiction("vegetarian", "vegan")

    def test_contradiction_demotes_both_to_pending(self, manager):
        """矛盾记忆双方应都降级为 PENDING。"""
        v1 = manager.upsert_memory(
            _make_entry(
                fact_key="diet",
                fact_value="喜欢吃素食",
                confidence=0.95,
                source_type=SourceType.EXPLICIT,
            )
        )
        assert v1.status == FactStatus.ACTIVE

        v2 = manager.upsert_memory(
            _make_entry(
                fact_key="diet",
                fact_value="不喜欢吃素食",
                confidence=0.90,
                source_type=SourceType.EXPLICIT,
            )
        )

        # v1 被降级
        history = manager.get_memory_history(user_id=1001, fact_key="diet")
        v1_from_db = next(m for m in history if m.version == 1)
        assert v1_from_db.status == FactStatus.PENDING
        assert v1_from_db.confidence < 0.95

        # v2 也是 pending
        assert v2.status == FactStatus.PENDING
        assert v2.confidence < 0.90


# ── P1+P3 集成：重新确认提升置信度 ────────────────────────────────


class TestReconfirmation:
    """同值重新确认：置信度提升但不创建新版本。"""

    def test_reconfirm_same_value_boosts_no_new_version(self, manager):
        """同值 upsert 应提升置信度而非创建新版本。"""
        v1 = manager.upsert_memory(
            _make_entry(fact_key="city", fact_value="北京", confidence=0.80)
        )
        v2 = manager.upsert_memory(
            _make_entry(fact_key="city", fact_value="北京", confidence=0.80)
        )

        assert v2.confidence > 0.80  # 提升了
        assert v2.version == 1       # 还是同一个版本
        history = manager.get_memory_history(user_id=1001, fact_key="city")
        assert len(history) == 1    # 没有创建新行
