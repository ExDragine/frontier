import heapq
import time
from collections import defaultdict


class _GroupMessageHeap:
    """单个群的复读小顶堆"""
    def __init__(self, capacity: int = 10, threshold: int = 3):
        self.capacity = capacity
        self.threshold = threshold
        self.counts = defaultdict(int)  # 消息 -> 次数
        self.heap = []  # (次数, 时间戳, 消息)

    def add(self, message: str) -> bool:
        now = time.time()
        self.counts[message] += 1
        count = self.counts[message]

        heapq.heappush(self.heap, (count, now, message))

        # 保持堆容量
        while len(self.counts) > self.capacity:
            _, _, msg_to_remove = heapq.heappop(self.heap)
            if msg_to_remove in self.counts:
                del self.counts[msg_to_remove]

        # 达到阈值触发
        if count >= self.threshold:
            del self.counts[message]
            self.heap = [(c, t, m) for (c, t, m) in self.heap if m != message]
            heapq.heapify(self.heap)
            return True

        return False


class RepeatMessageHeap:
    """多群复读堆管理器"""
    def __init__(self, capacity: int = 10, threshold: int = 3):
        self.capacity = capacity
        self.threshold = threshold
        self.groups: dict[int, _GroupMessageHeap] = {}

    def add(self, group_id: int, message: str) -> bool:
        """按群ID管理，每个群有独立堆"""
        heap = self.groups.setdefault(
            group_id, _GroupMessageHeap(self.capacity, self.threshold)
        )
        return heap.add(message)
