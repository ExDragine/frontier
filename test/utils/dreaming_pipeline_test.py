# ruff: noqa: S101

"""DreamingPipeline 测试 — 覆盖凌晨 4:00 记忆管道的核心流程。"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import create_engine

from utils.database import Message
from utils.memory_v3 import (
    FactCategory,
    FactStatus,
    MemoryEntry,
    MemoryExtractionResult,
    MemoryManager,
    SourceType,
    TemporalNature,
    get_memory_manager,
)


# ── Helpers ────────────────────────────────────────────────────────


def _build_message(
    time_ms: int,
    user_id: int = 1001,
    group_id: int | None = None,
    content: str = "hello",
    role: str = "user",
    msg_id: int = 1,
    user_name: str = "TestUser",
) -> Message:
    return Message(
        time=time_ms,
        msg_id=msg_id,
        user_id=user_id,
        group_id=group_id,
        user_name=user_name,
        role=role,
        content=content,
        source_type="message",
    )


def _make_entry(
    user_id: int = 1001,
    group_id: int | None = None,
    fact_key: str = "test_fact",
    fact_value: str = "test_value",
    **kwargs,
) -> MemoryEntry:
    now_ms = int(time.time() * 1000)
    return MemoryEntry(
        user_id=user_id,
        group_id=group_id if group_id is not None else 0,
        fact_key=fact_key,
        fact_value=fact_value,
        fact_category=kwargs.pop("fact_category", FactCategory.PERSONAL_INFO),
        confidence=kwargs.pop("confidence", 1.0),
        source_type=kwargs.pop("source_type", SourceType.EXPLICIT),
        temporal_nature=kwargs.pop("temporal_nature", TemporalNature.PERMANENT),
        valid_from=kwargs.pop("valid_from", now_ms),
        valid_until=kwargs.pop("valid_until", None),
        status=kwargs.pop("status", FactStatus.ACTIVE),
        version=kwargs.pop("version", 1),
        created_at=kwargs.pop("created_at", now_ms),
        updated_at=kwargs.pop("updated_at", now_ms),
        **kwargs,
    )


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def manager(monkeypatch):
    """内存数据库的 MemoryManager。"""
    import utils.database as db
    import utils.memory_v3 as mv3

    monkeypatch.setattr("utils.database.DATABASE_FILE", "sqlite:///:memory:")
    db._cached_engine.cache_clear()
    mv3._memory_manager = None
    mgr = MemoryManager()
    yield mgr
    mv3._memory_manager = None
    db._cached_engine.cache_clear()


@pytest.fixture
def dummy_messages_db():
    """提供可控消息的假 MessageDatabase。"""

    class DummyMessageDb:
        def __init__(self):
            self.messages: list[Message] = []
            self.active_conversations: list[dict] = []

        async def select_by_time_range(self, **kwargs):
            return self.messages

        async def get_active_conversations_since(self, **kwargs):
            return self.active_conversations

        @staticmethod
        def format_for_llm(messages):
            lines = []
            for m in messages:
                lines.append(f"[{m.user_name}]: {m.content}")
            return "\n".join(lines)

    return DummyMessageDb()


# ── Pipeline 加载辅助 ─────────────────────────────────────────────


def _load_pipeline(monkeypatch, dummy_db, manager):
    """加载 DreamingPipeline 并注入假依赖。"""

    import utils.memory_v3 as mv3
    import utils.dreaming_pipeline as dp

    monkeypatch.setattr(mv3, "_memory_manager", manager)
    manager._cache.clear()

    # P2: 测试环境下跳过语义去重（不需要 LLM）
    monkeypatch.setattr(manager, "resolve_semantic_dedup", AsyncMock(return_value=None))

    pipeline = dp.DreamingPipeline()
    pipeline._messages = dummy_db
    return pipeline


# ── 测试 ───────────────────────────────────────────────────────────


class TestDreamingPipeline:
    """核心管道流程测试。"""

    @pytest.mark.asyncio
    async def test_no_active_conversations_skips(self, monkeypatch, dummy_messages_db, manager):
        """无活跃对话时应跳过 Dreaming。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        dummy_messages_db.active_conversations = []

        result = await pipeline.run()

        assert result is not None
        assert "no new messages" in result["output_summary"].lower()
        assert result["messages_sent"] == 0

    @pytest.mark.asyncio
    async def test_conversation_below_threshold_skipped(self, monkeypatch, dummy_messages_db, manager):
        """消息数不足的对话不处理。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        dummy_messages_db.active_conversations = [
            {"user_id": 1001, "group_id": None, "message_count": 2,
             "earliest_time": 0, "latest_time": 0}
        ]

        result = await pipeline.run()
        assert "处理" not in result["output_summary"]  # 全部跳过

    @pytest.mark.asyncio
    async def test_extract_and_merge_single_conversation(self, monkeypatch, dummy_messages_db, manager):
        """单对话提取 + 合并流程。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)

        now_ms = int(time.time() * 1000)
        dummy_messages_db.active_conversations = [
            {"user_id": 1001, "group_id": None, "message_count": 10,
             "earliest_time": now_ms - 3600000, "latest_time": now_ms}
        ]
        dummy_messages_db.messages = [
            _build_message(now_ms, content="我是素食者，不吃任何肉"),
            _build_message(now_ms + 1000, content="好啊，给你推荐几个素菜馆"),
        ]

        # ── 拦截 LLM 提取 ──
        mock_result = MemoryExtractionResult(
            memories=[
                _make_entry(
                    fact_key="dietary_preference",
                    fact_value="素食",
                    fact_category=FactCategory.PREFERENCE,
                    source_type=SourceType.EXPLICIT,
                    confidence=0.95,
                )
            ],
            facts_to_evolve=[],
            facts_to_deprecate=[],
        )

        with patch.object(pipeline, "_extract_memories", new=AsyncMock(return_value=mock_result)):
            result = await pipeline.run()

        # 验证输出摘要
        assert "Dreaming 完成" in result["output_summary"]
        assert result["messages_sent"] == 0

        # ── TODO: 验证合并结果 ──
        # 你应该验证 MemoryManager 中现在包含了提取的记忆。
        # 提示：调用 manager.get_active_memories(user_id=1001)
        # 确认返回的记忆包含 dietary_preference → 素食

    @pytest.mark.asyncio
    async def test_extract_llm_failure_is_tolerated(self, monkeypatch, dummy_messages_db, manager):
        """LLM 失败应被弹性处理，不中断管道，管道正常完成。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        now_ms = int(time.time() * 1000)

        dummy_messages_db.active_conversations = [
            {"user_id": 1001, "group_id": None, "message_count": 10,
             "earliest_time": now_ms - 3600000, "latest_time": now_ms}
        ]
        dummy_messages_db.messages = [_build_message(now_ms)]

        with patch.object(
            pipeline, "_extract_memories",
            new=AsyncMock(side_effect=RuntimeError("LLM timeout"))
        ):
            result = await pipeline.run()

        # 管道应完成（不崩溃），但该对话被静默跳过
        assert "Dreaming 完成" in result["output_summary"]
        # 单对话错误被内部消化，不影响整体（弹性设计）
        assert result["messages_sent"] == 0

    @pytest.mark.asyncio
    async def test_prune_expired_memories(self, monkeypatch, dummy_messages_db, manager):
        """Dreaming 管道结束时自动清理过期记忆。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        now_ms = int(time.time() * 1000)
        past_ms = now_ms - 10000

        # 预埋一条过期记忆
        expired = _make_entry(
            user_id=1001,
            fact_key="old_event",
            fact_value="上周的聚会",
            temporal_nature=TemporalNature.TIME_BOUND,
            valid_until=past_ms,
        )
        manager.upsert_memory(expired)

        dummy_messages_db.active_conversations = [
            {"user_id": 1001, "group_id": None, "message_count": 10,
             "earliest_time": now_ms - 3600000, "latest_time": now_ms}
        ]
        dummy_messages_db.messages = [_build_message(now_ms)]

        with patch.object(pipeline, "_extract_memories", new=AsyncMock(return_value=None)):
            await pipeline.run()

        # 过期记忆应已被清理
        active = manager.get_active_memories(user_id=1001)
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_facts_evolution_chain(self, monkeypatch, dummy_messages_db, manager):
        """事实演化：旧记忆被新记忆取代后保留版本历史。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        now_ms = int(time.time() * 1000)

        # ── 预埋旧记忆 ──
        old = _make_entry(
            user_id=1001,
            fact_key="travel_plan",
            fact_value="要去新加坡",
            fact_category=FactCategory.PLAN,
            temporal_nature=TemporalNature.TIME_BOUND,
            valid_until=now_ms + 86400000,
        )
        manager.upsert_memory(old)

        dummy_messages_db.active_conversations = [
            {"user_id": 1001, "group_id": None, "message_count": 10,
             "earliest_time": now_ms - 3600000, "latest_time": now_ms}
        ]
        dummy_messages_db.messages = [
            _build_message(now_ms, content="我从新加坡回来了，热死了"),
        ]

        # ── LLM 返回演化后的记忆 ──
        mock_result = MemoryExtractionResult(
            memories=[
                _make_entry(
                    fact_key="travel_plan",  # 同 key → 版本升级
                    fact_value="去过新加坡（2026年6月）",
                    fact_category=FactCategory.EXPERIENCE,
                    temporal_nature=TemporalNature.LONG_TERM,
                    valid_until=None,
                )
            ],
            facts_to_evolve=[
                {"fact_key": "travel_plan", "new_value": "去过新加坡（2026年6月）",
                 "reason": "旅行计划已完成，转为经历"}
            ],
            facts_to_deprecate=[],
        )

        with patch.object(pipeline, "_extract_memories", new=AsyncMock(return_value=mock_result)):
            await pipeline.run()

        # ── TODO: 验证版本链 ──
        # 调用 manager.get_memory_history(user_id=1001, fact_key="travel_plan")
        # 验证：
        # 1. v1 被标记为 SUPERSEDED，状态从 PLAN → 被取代
        # 2. v2 是 ACTIVE 状态，值为 "去过新加坡（2026年6月）"
        # 3. v1.superseded_by == v2.id

    @pytest.mark.asyncio
    async def test_group_chat_pulls_all_user_messages(self, monkeypatch, dummy_messages_db, manager):
        """群聊拉全群消息（不按 user 过滤），私聊才按 user 过滤。"""
        now_ms = int(time.time() * 1000)
        call_args: dict = {}

        class TrackingDb(dummy_messages_db.__class__):
            async def select_by_time_range(self, **kwargs):
                call_args.update(kwargs)
                return dummy_messages_db.messages

        tracked_db = TrackingDb()
        tracked_db.messages = dummy_messages_db.messages

        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        pipeline._messages = tracked_db

        # ── 群聊场景 ──
        tracked_db.active_conversations = [
            {"user_id": 1001, "group_id": 123, "message_count": 10,
             "earliest_time": now_ms - 3600000, "latest_time": now_ms}
        ]
        tracked_db.messages = [
            _build_message(now_ms, user_id=1001, group_id=123, content="我是素食者"),
            _build_message(now_ms + 1, user_id=1002, group_id=123, content="那火锅怎么办"),
            _build_message(now_ms + 2, user_id=1001, group_id=123, content="有素火锅啊"),
        ]

        with patch.object(pipeline, "_extract_memories", new=AsyncMock(return_value=None)):
            await pipeline.run()

        # 群聊：传了 group_id 但不传 user_id → 拿到全群消息
        assert call_args.get("group_id") == 123
        assert call_args.get("user_id") is None

        # ── 私聊场景 ──
        call_args.clear()
        tracked_db.active_conversations = [
            {"user_id": 1001, "group_id": None, "message_count": 10,
             "earliest_time": now_ms - 3600000, "latest_time": now_ms}
        ]
        tracked_db.messages = [
            _build_message(now_ms, user_id=1001, group_id=None, content="你好"),
        ]

        with patch.object(pipeline, "_extract_memories", new=AsyncMock(return_value=None)):
            await pipeline.run()

        # 私聊：传了 user_id 但不传 group_id → 只拿该用户的消息
        assert call_args.get("user_id") == 1001
        assert call_args.get("group_id") is None

    @pytest.mark.asyncio
    async def test_dreaming_prompt_includes_target_user_scope(self, monkeypatch, dummy_messages_db, manager):
        """群聊的提取提示词应包含目标用户 ID 和范围说明。"""
        pipeline = _load_pipeline(monkeypatch, dummy_messages_db, manager)
        now_ms = int(time.time() * 1000)

        # 直接测试 _dreaming_user_prompt 输出
        from utils.dreaming_pipeline import _dreaming_user_prompt

        prompt = _dreaming_user_prompt(
            recent_messages="[1001]: 我是素食者\n[1002]: 好的",
            existing_memories="",
            lookback_start="06-07 00:00",
            lookback_end="06-08 04:00",
            target_user_id=1001,
            is_group=True,
        )

        assert "user_id=1001" in prompt
        assert "只提取目标用户" in prompt
        assert "其他用户的发言仅用于理解对话上下文" in prompt

        # 私聊不应包含群聊限定说明
        prompt_private = _dreaming_user_prompt(
            recent_messages="[1001]: 你好",
            existing_memories="",
            lookback_start="06-07 00:00",
            lookback_end="06-08 04:00",
            target_user_id=1001,
            is_group=False,
        )

        assert "只提取目标用户" not in prompt_private


# ── Handler 入口测试 ───────────────────────────────────────────────


class TestDreamingHandler:
    """run_dreaming_pipeline 入口函数测试。"""

    @pytest.mark.asyncio
    async def test_run_dreaming_pipeline_entrypoint(self, monkeypatch, dummy_messages_db, manager):
        """run_dreaming_pipeline 应能被直接 await 调用。"""
        import utils.memory_v3 as mv3
        import utils.dreaming_pipeline as dp

        dummy_messages_db.active_conversations = []

        def patched_init(self):
            self._memory = mv3.get_memory_manager()
            self._memory.resolve_semantic_dedup = AsyncMock(return_value=None)
            self._messages = dummy_messages_db
            self._basic_model = None
            self._model_loaded = False

        monkeypatch.setattr(dp.DreamingPipeline, "__init__", patched_init)

        result = await dp.run_dreaming_pipeline()
        assert result is not None
        assert "output_summary" in result


# ── P0: Few-shot 提示词测试 ──────────────────────────────────────


class TestFewShotPrompts:
    """P0 few-shot 提示词内容和格式测试。"""

    def test_system_prompt_includes_examples(self):
        """系统提示词应包含 3 类示例。"""
        from utils.dreaming_pipeline import _dreaming_system_prompt

        prompt = _dreaming_system_prompt()
        assert "示例 1" in prompt
        assert "示例 2" in prompt
        assert "示例 3" in prompt
        assert "常见错误" in prompt
        assert "不要从提问" in prompt

    def test_system_prompt_includes_category_docs(self):
        """系统提示词应包含 fact_category / temporal_nature 说明。"""
        from utils.dreaming_pipeline import _dreaming_system_prompt

        prompt = _dreaming_system_prompt()
        assert "fact_category" in prompt
        assert "temporal_nature" in prompt
        assert "source_type" in prompt

    def test_user_prompt_references_examples(self):
        """用户提示词应引导 LLM 参考系统提示中的示例。"""
        from utils.dreaming_pipeline import _dreaming_user_prompt

        prompt = _dreaming_user_prompt(
            recent_messages="test", existing_memories="", lookback_start="", lookback_end="",
            target_user_id=1001, is_group=False,
        )
        assert "示例" in prompt


# ── P4: 自适应分档 + 规则提取测试 ─────────────────────────────────


class TestAdaptiveExtraction:
    """P4 自适应分档和规则提取。"""

    def test_rule_based_extract_matches_keywords(self):
        """规则提取应匹配「我是」、「我喜欢」等关键词模式。"""
        from utils.memory_v3 import _rule_based_extract
        from utils.database import Message

        now_ms = int(time.time() * 1000)
        messages = [
            Message(time=now_ms, user_id=1001, role="user", user_name="Test",
                    content="我是程序员，在北京工作"),
        ]

        result = _rule_based_extract(messages, user_id=1001, group_id=None)
        assert result is not None
        assert len(result.memories) >= 1
        assert any("程序员" in m.fact_value for m in result.memories)

    @pytest.mark.asyncio
    async def test_rule_based_extract_marks_as_pending(self, monkeypatch, dummy_messages_db, manager):
        """规则提取的结果应是 PENDING 状态（低置信度，等更多证据）。"""
        from utils.memory_v3 import _rule_based_extract
        from utils.database import Message

        now_ms = int(time.time() * 1000)
        messages = [
            Message(time=now_ms, user_id=1001, role="user",
                    content="我喜欢火锅"),
        ]

        result = _rule_based_extract(messages, user_id=1001, group_id=None)
        assert result is not None
        for mem in result.memories:
            assert mem.status == FactStatus.PENDING
            assert mem.confidence == pytest.approx(0.55)

    @pytest.mark.asyncio
    async def test_rule_based_extract_skips_noise(self, monkeypatch, dummy_messages_db, manager):
        """闲聊/无信息消息不应触发规则提取。"""
        from utils.memory_v3 import _rule_based_extract
        from utils.database import Message

        now_ms = int(time.time() * 1000)
        messages = [
            Message(time=now_ms, user_id=1001, role="user", content="哈哈哈"),
            Message(time=now_ms, user_id=1001, role="user", content="今天天气不错"),
        ]

        result = _rule_based_extract(messages, user_id=1001, group_id=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_rule_based_extract_excludes_other_users(self, monkeypatch, dummy_messages_db, manager):
        """规则提取不提取非目标用户的消息。"""
        from utils.memory_v3 import _rule_based_extract
        from utils.database import Message

        now_ms = int(time.time() * 1000)
        messages = [
            Message(time=now_ms, user_id=1002, role="user",
                    content="我是程序员（但这不应该被提取）"),
        ]

        result = _rule_based_extract(messages, user_id=1001, group_id=None)
        assert result is None


# ── P0+P1 集成：规则提取 → 证据累积 → 升级 ─────────────────────


class TestRuleToEvidencePipeline:
    """低频对话：规则提取 PENDING → 多次出现 → 升级 ACTIVE。"""

    def test_rule_extract_then_accumulate_upgrades(self, monkeypatch, dummy_messages_db, manager):
        """规则提取 + accumulate_evidence 多轮后达成交叉验证。"""
        from utils.memory_v3 import _rule_based_extract
        from utils.database import Message

        now_ms = int(time.time() * 1000)

        # 第一轮：规则提取到 "我喜欢火锅"
        messages_1 = [
            Message(time=now_ms, msg_id=1, user_id=1001, role="user",
                    content="我喜欢火锅"),
        ]
        result_1 = _rule_based_extract(messages_1, user_id=1001, group_id=None)
        assert result_1 and result_1.memories
        mem_1 = result_1.memories[0]
        mem_1.confidence = 0.55
        mem_1.status = FactStatus.PENDING
        manager.upsert_memory(mem_1)

        # 第二轮：再次出现
        new_entry = _make_entry(
            user_id=1001,
            fact_key=mem_1.fact_key,
            fact_value=mem_1.fact_value,
            confidence=0.55,
            source_type=SourceType.IMPLIED,
            source_message_ids=[2],
            status=FactStatus.PENDING,
        )

        updated = manager.accumulate_evidence(user_id=1001, group_id=None, entry=new_entry)
        assert updated.confidence > 0.55

        # 第三轮
        new_entry_2 = _make_entry(
            user_id=1001,
            fact_key=mem_1.fact_key,
            fact_value=mem_1.fact_value,
            confidence=0.70,
            source_type=SourceType.IMPLIED,
            source_message_ids=[3],
            status=FactStatus.PENDING,
        )
        updated_2 = manager.accumulate_evidence(user_id=1001, group_id=None, entry=new_entry_2)
        assert updated_2.confidence >= 0.70

        # 置信度够了 + 2 个来源 → 可以升级
        count = manager.upgrade_pending_memories(user_id=1001)
        assert count == 1


# ── Task 注册配置测试 ──────────────────────────────────────────────


def test_build_dreaming_task_config(monkeypatch):
    """验证生成的 TaskConfig 参数正确。"""
    import utils.database as db
    import utils.dreaming_pipeline as dp

    monkeypatch.setattr("utils.database.DATABASE_FILE", "sqlite:///:memory:")
    db._cached_engine.cache_clear()

    config = dp.build_dreaming_task_config(db.get_engine())
    assert config["job_id"] == "dreaming_daily_v3"
    assert config["trigger_type"] == "cron"
    assert config["trigger_args"]["hour"] == "4"
    assert config["misfire_grace_time"] == 1800
    assert config["handler_module"] == "utils.dreaming_pipeline"
    assert config["handler_function"] == "run_dreaming_pipeline"

    db._cached_engine.cache_clear()
