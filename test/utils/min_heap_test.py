# ruff: noqa: S101

from utils.min_heap import RepeatMessageHeap


def test_repeat_message_heap_triggers_after_threshold():
    heap = RepeatMessageHeap(capacity=10, threshold=3)

    assert heap.add(912579570, "1") is False
    assert heap.add(912579570, "1") is False
    assert heap.add(912579570, "1") is True
    assert heap.add(912579570, "1") is False
