# ruff: noqa: S101

from utils.memory_types import MemoryAnalyzeResult, MemoryCategory, MemoryRecord, MemoryScope, MemorySearchItem


def test_memory_analyze_result_normalizes():
    result = MemoryAnalyzeResult(should_memory=False, memory_content="  hi ", slot_key="  ")
    assert result.memory_content == ""
    assert result.slot_key == "general"
    assert result.is_group_fact is False


def test_memory_analyze_result_scores_and_category():
    result = MemoryAnalyzeResult(
        should_memory=True,
        memory_content="test",
        category="PROFILE",
        importance="not-a-number",
        confidence=2,
    )
    assert result.category == MemoryCategory.PROFILE
    assert result.importance == 0.5
    assert result.confidence == 1.0


def test_memory_models_construct():
    record = MemoryRecord(
        memory_id="id",
        content="content",
        scope=MemoryScope.USER,
        owner_user_id="u",
        category=MemoryCategory.OTHER,
        slot_key="general",
        created_at=1,
        updated_at=2,
    )
    assert record.status.value == "active"

    item = MemorySearchItem(
        memory_id="id",
        content="content",
        scope=MemoryScope.USER,
        category=MemoryCategory.OTHER,
        slot_key="slot",
        updated_at=1,
        importance=0.5,
        confidence=0.5,
        score=0.9,
    )
    assert item.score == 0.9
