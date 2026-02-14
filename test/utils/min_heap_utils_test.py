# ruff: noqa: S101

import time

from utils.min_heap import RepeatMessageHeap, _GroupMessageHeap


def test_group_message_heap_threshold_and_cleanup(monkeypatch):
    heap = _GroupMessageHeap(capacity=2, threshold=2, time_window=10)

    now = 1_000.0
    monkeypatch.setattr(time, "time", lambda: now)
    assert heap.add("hello") is False

    now += 1
    assert heap.add("hello") is True
    assert "hello" not in heap.message_times


def test_group_message_heap_capacity(monkeypatch):
    heap = _GroupMessageHeap(capacity=1, threshold=3, time_window=10)
    now = 1_000.0
    monkeypatch.setattr(time, "time", lambda: now)
    assert heap.add("first") is False

    now += 1
    assert heap.add("second") is False
    assert "first" not in heap.message_times


def test_repeat_message_heap_group_isolation(monkeypatch):
    heap = RepeatMessageHeap(capacity=2, threshold=2, time_window=10)
    now = 1_000.0
    monkeypatch.setattr(time, "time", lambda: now)

    assert heap.add(1, "same") is False
    assert heap.add(2, "same") is False
    now += 1
    assert heap.add(1, "same") is True
    assert heap.add(2, "same") is True
