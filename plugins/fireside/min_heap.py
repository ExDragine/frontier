import heapq
import time
from collections import defaultdict


class _GroupMessageHeap:
    def __init__(self, capacity: int = 10, threshold: int = 3, time_window: float = 60.0):
        self.capacity = capacity
        self.threshold = threshold
        self.time_window = time_window  # 60秒时间窗口
        self.counts = defaultdict(int)
        self.heap = []
        self.message_times = defaultdict(list)  # 记录每条消息的时间戳

    def add(self, message: str) -> bool:
        now = time.time()

        # ✅ 清理过期的消息计数
        self.message_times[message] = [
            t for t in self.message_times[message]
            if now - t < self.time_window
        ]
        self.counts[message] = len(self.message_times[message])

        # 添加新消息时间
        self.message_times[message].append(now)
        self.counts[message] += 1
        count = self.counts[message]

        heapq.heappush(self.heap, (count, now, message))

        # 清理堆中的过期数据
        while self.heap and now - self.heap[0][1] > self.time_window:
            heapq.heappop(self.heap)

        # 保持容量
        while len(self.counts) > self.capacity:
            _, _, msg_to_remove = heapq.heappop(self.heap)
            if msg_to_remove in self.counts:
                del self.counts[msg_to_remove]
                del self.message_times[msg_to_remove]

        # 达到阈值触发
        if count >= self.threshold:
            del self.counts[message]
            del self.message_times[message]
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
