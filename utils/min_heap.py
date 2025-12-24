import heapq
import time
from collections import defaultdict


class _GroupMessageHeap:
    """单个群的复读计数器"""

    def __init__(self, capacity: int = 10, threshold: int = 3, time_window: float = 60.0):
        self.capacity = capacity
        self.threshold = threshold
        self.time_window = time_window
        self.message_times: dict[str, list[float]] = defaultdict(list)

    def add(self, message: str) -> bool:
        """添加消息，如果达到阈值返回 True"""
        now = time.time()

        # 清理该消息的过期时间戳
        self.message_times[message] = [t for t in self.message_times[message] if now - t < self.time_window]

        # 添加新时间戳
        self.message_times[message].append(now)
        count = len(self.message_times[message])

        # 达到阈值，触发复读并清空计数
        if count >= self.threshold:
            del self.message_times[message]
            return True

        # 清理旧消息，保持容量限制
        if len(self.message_times) > self.capacity:
            oldest_msg = min(
                self.message_times.keys(),
                key=lambda m: self.message_times[m][0] if self.message_times[m] else float("inf"),
            )
            del self.message_times[oldest_msg]

        return False

    def __repr__(self) -> str:
        """返回可读的字符串表示"""
        now = time.time()
        items = []
        for msg, times in self.message_times.items():
            # 截断消息内容，显示最近一次时间
            msg_short = msg[:20] + "..." if len(msg) > 20 else msg
            last_time = times[-1] if times else 0
            age = now - last_time
            items.append(f"'{msg_short}': {len(times)}次 ({age:.1f}s前)")

        return f"<GroupHeap: {len(self.message_times)}/{self.capacity} msgs, threshold={self.threshold}, [{', '.join(items)}]>"


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
            self.groups[group_id] = _GroupMessageHeap(self.capacity, self.threshold, self.time_window)
        return self.groups[group_id].add(message)

    def __repr__(self) -> str:
        """返回所有群的状态"""
        if not self.groups:
            return "<RepeatHeap: 无活跃群组>"

        group_stats = []
        for gid, heap in self.groups.items():
            group_stats.append(f"  群{gid}: {heap}")

        return f"<RepeatHeap: {len(self.groups)} 个群组>\n" + "\n".join(group_stats)
