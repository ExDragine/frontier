# ruff: noqa: S101

import types

import pytest

from utils.memory import MemoryServiceV2
from utils.memory_types import MemoryCategory, MemoryScope, MemoryStatus


class DummyCollection:
    def __init__(self, payload):
        self.payload = payload

    def get(self, **kwargs):
        return self.payload


class DummyClient:
    def __init__(self, payload):
        self.payload = payload

    def get_collection(self, name):
        return DummyCollection(self.payload)

    def get_or_create_collection(self, name):
        return DummyCollection(self.payload)


class DummyEmbeddings:
    def embed_documents(self, docs):
        return [[0.0] * 3 for _ in docs]


@pytest.fixture
def memory_service(monkeypatch):
    service = MemoryServiceV2()
    service.enabled = True
    service._embeddings = DummyEmbeddings()
    return service


def test_apply_privacy_filter_modes(memory_service):
    allow, content, reason = memory_service.apply_privacy_filter("sk-abcdef123456789012345")
    assert allow is False
    assert reason == "high_sensitive"

    memory_service.privacy_mode = "balanced"
    allow, content, reason = memory_service.apply_privacy_filter("我的电话是13800138000")
    assert allow is True
    assert "****" in content
    assert reason == "masked"

    memory_service.privacy_mode = "strict"
    allow, content, reason = memory_service.apply_privacy_filter("邮箱 test@example.com")
    assert allow is False
    assert reason == "medium_sensitive"


def test_normalize_slot_key_and_expires(memory_service, monkeypatch):
    key = memory_service.normalize_slot_key("", MemoryCategory.PROFILE, "Hello World")
    assert key.startswith("profile:")
    assert len(key) <= 96

    monkeypatch.setattr(memory_service, "now_ms", lambda: 1_000_000)
    expires = memory_service.default_expires_at(MemoryCategory.TASK, "完成于 2026-02-14")
    assert expires is not None

    no_expire = memory_service.default_expires_at(MemoryCategory.PROFILE, "Profile data")
    assert no_expire is None


def test_extract_items_from_query_filters(memory_service, monkeypatch):
    now = 1_000_000
    monkeypatch.setattr(memory_service, "now_ms", lambda: now)
    payload = {
        "ids": [["1", "2", "3"]],
        "documents": [["a", "b", "c"]],
        "metadatas": [
            [
                {
                    "status": MemoryStatus.ACTIVE.value,
                    "expires_at": now + 10_000,
                    "updated_at": now,
                    "importance": 0.5,
                    "confidence": 0.5,
                    "scope": MemoryScope.USER.value,
                    "category": MemoryCategory.OTHER.value,
                    "slot_key": "slot",
                    "owner_user_id": "u",
                },
                {
                    "status": MemoryStatus.DELETED.value,
                    "expires_at": now + 10_000,
                    "updated_at": now,
                    "importance": 0.5,
                    "confidence": 0.5,
                    "scope": MemoryScope.USER.value,
                    "category": MemoryCategory.OTHER.value,
                    "slot_key": "slot",
                    "owner_user_id": "u",
                },
                {
                    "status": MemoryStatus.ACTIVE.value,
                    "expires_at": now - 10,
                    "updated_at": now,
                    "importance": 0.5,
                    "confidence": 0.5,
                    "scope": MemoryScope.USER.value,
                    "category": MemoryCategory.OTHER.value,
                    "slot_key": "slot",
                    "owner_user_id": "u",
                },
            ]
        ],
        "distances": [[0.1, 0.2, 0.3]],
    }
    items = memory_service._extract_items_from_query(payload, MemoryScope.USER)
    assert len(items) == 1
    assert items[0].content == "a"


def test_format_helpers(memory_service):
    assert memory_service.format_for_injection([]) == ""

    record = types.SimpleNamespace(
        memory_id="m1",
        scope=MemoryScope.USER,
        category=MemoryCategory.OTHER,
        slot_key="slot",
        content="content",
    )
    injection = memory_service.format_for_injection([record])
    assert "Memory Context" in injection

    formatted = memory_service.format_memory_list([])
    assert "暂无" in formatted
