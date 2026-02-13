# ruff: noqa: S101

from utils.memory import MemoryServiceV2
from utils.memory_types import MemoryCategory, MemoryScope, MemorySearchItem


def build_service() -> MemoryServiceV2:
    service = MemoryServiceV2.__new__(MemoryServiceV2)
    service.privacy_mode = "balanced"
    service.default_task_ttl_days = 30
    service.max_injected_memories = 4
    return service


def make_item(scope: MemoryScope, idx: int, score: float) -> MemorySearchItem:
    return MemorySearchItem(
        memory_id=f"id-{scope.value}-{idx}",
        content=f"memory-{idx}",
        scope=scope,
        category=MemoryCategory.OTHER,
        slot_key=f"slot-{idx}",
        updated_at=1_700_000_000_000 + idx,
        importance=0.5,
        confidence=0.5,
        score=score,
    )


def test_privacy_filter_rejects_high_sensitive():
    service = build_service()
    allow, content, reason = service.apply_privacy_filter("api_key=sk-ABCDEFGHIJK1234567890")
    assert allow is False
    assert content == ""
    assert reason == "high_sensitive"


def test_privacy_filter_masks_medium_sensitive_in_balanced_mode():
    service = build_service()
    allow, content, reason = service.apply_privacy_filter("我的手机号是13812345678，邮箱是abc@example.com")
    assert allow is True
    assert reason == "masked"
    assert "138****5678" in content
    assert "a***@example.com" in content


def test_default_expires_at_by_category():
    service = build_service()
    assert service.default_expires_at(MemoryCategory.PREFERENCE, "用户喜欢简洁回复") is None

    task_expire = service.default_expires_at(MemoryCategory.TASK, "记住这个任务")
    assert task_expire is not None
    assert task_expire > service.now_ms()

    deadline_expire = service.default_expires_at(MemoryCategory.DEADLINE, "项目截止日期 2026-03-01")
    assert deadline_expire is not None


def test_group_fact_detection():
    service = build_service()
    assert service.should_store_group_memory("这条是本群规则，后续都按这个来", False) is True
    assert service.should_store_group_memory("我今天吃了面条", False) is False


def test_allocate_budget_prefers_3_user_plus_1_group():
    service = build_service()
    user_items = [make_item(MemoryScope.USER, idx, 0.9 - idx * 0.1) for idx in range(4)]
    group_items = [make_item(MemoryScope.GROUP, idx, 0.8 - idx * 0.1) for idx in range(2)]
    selected = service._allocate_budget(user_items, group_items, max_items=4)
    assert len(selected) == 4
    assert sum(1 for item in selected if item.scope == MemoryScope.USER) >= 3
    assert sum(1 for item in selected if item.scope == MemoryScope.GROUP) >= 1


def test_supersede_slot_records_marks_previous_active_record():
    service = build_service()
    now_ms = service.now_ms()

    class FakeCollection:
        def __init__(self):
            self.updated_payload = None

        def get(self, **_kwargs):
            return {
                "ids": ["old-id"],
                "metadatas": [{"slot_key": "profile.name", "status": "active"}],
                "documents": ["旧记忆"],
            }

        def update(self, ids, metadatas, documents):
            self.updated_payload = {
                "ids": ids,
                "metadatas": metadatas,
                "documents": documents,
            }

    collection = FakeCollection()
    service._supersede_slot_records(collection, MemoryScope.USER, "profile.name", now_ms)
    assert collection.updated_payload is not None
    assert collection.updated_payload["ids"] == ["old-id"]
    assert collection.updated_payload["metadatas"][0]["status"] == "superseded"
    assert collection.updated_payload["metadatas"][0]["updated_at"] == now_ms


def test_soft_delete_requires_group_permission():
    service = build_service()
    service.user_collection_name = lambda _user_id: "mem_user_u1"
    service.group_collection_name = lambda _group_id: "mem_group_1"

    def fake_get_record(collection_name, _memory_id):
        if collection_name == "mem_group_1":
            return object(), {"metadata": {"owner_user_id": "u1"}, "document": "群记忆"}
        return None, None

    service._get_record_payload_sync = fake_get_record
    service._soft_delete_in_collection = lambda *_args, **_kwargs: True

    success, message = service._soft_delete_sync(
        memory_id="group-memory",
        user_id="u1",
        group_id=1,
        allow_group_delete=False,
        preferred_scope=MemoryScope.GROUP,
    )
    assert success is False
    assert "无权限删除群记忆" in message
