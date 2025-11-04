import time
from collections import defaultdict


class _GroupMessageHeap:
    """单个群的复读计数器"""
    def __init__(self, capacity: int = 10, threshold: int = 3, time_window: float = 60.0):
        self.capacity = capacity
        self.threshold = threshold
        self.time_window = time_window
        # 存储每条消息的时间戳列表
        self.message_times: dict[str, list[float]] = defaultdict(list)

    def add(self, message: str) -> bool:
        """
        添加消息，如果达到阈值返回 True
        """
        now = time.time()

        # 清理该消息的过期时间戳
        self.message_times[message] = [
            t for t in self.message_times[message]
            if now - t < self.time_window
        ]

        # 添加新时间戳
        self.message_times[message].append(now)
        count = len(self.message_times[message])

        # 达到阈值，触发复读并清空计数
        if count >= self.threshold:
            del self.message_times[message]
            return True

        # 清理旧消息，保持容量限制
        if len(self.message_times) > self.capacity:
            # 找到最旧的消息
            oldest_msg = min(
                self.message_times.keys(),
                key=lambda m: self.message_times[m][0] if self.message_times[m] else float('inf')
            )
            del self.message_times[oldest_msg]

        return False


class RepeatMessageHeap:
    """多群复读堆管理器"""
    def __init__(self, capacity: int = 10, threshold: int = 3, time_window: float = 60.0):
        self.capacity = capacity
        self.threshold = threshold
        self.time_window = time_window
        self.groups: dict[int, _GroupMessageHeap] = {}

    def add(self, group_id: int, message: str) -> bool:
        """按群ID管理，每个群有独立计数"""
        if group_id not in self.groups:
            self.groups[group_id] = _GroupMessageHeap(
                self.capacity, self.threshold, self.time_window
            )
        return self.groups[group_id].add(message)
