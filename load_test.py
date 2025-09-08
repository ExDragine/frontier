"""简单压测脚本

默认目标：每秒 60 个请求

功能：
- 使用 `httpx` 的异步客户端（如果可用），否则回退到 `requests` + 线程池。
- 支持命令行参数：--url, --qps, --duration, --concurrency, --timeout
- 统计成功/失败、平均/分位延迟

示例：
        python load_test.py --qps 60 --duration 60
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import statistics
import time

DEFAULT_URL = "https://dify.bbgame.global/v1/workflows/run"
DEFAULT_HEADERS = {
    "Authorization": "Bearer app-wyoSo08t0xcWUQPL16gckF2r",
    "Content-Type": "application/json",
}

DEFAULT_BODY = {
    "inputs": {
        "complaint_id": 100001,
        "conversations": [
            {
                "content": "test-conversation-content",
                "conversation_id": 10000101,
                "create_time": "2025-09-08 15:53:56.5555937",
            }
        ],
        "game_id": 59,
        "language": "zh_CN",
        "message_text": "111",
    },
    "response_mode": "blocking",
    "trace_id": "9d46a663-c46a-4ace-a764-f0034089b47e",
    "user": "bbgame-complaint-center",
}


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="简单压测脚本：支持 httpx 异步或 requests 线程回退")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--qps", type=int, default=60, help="目标每秒请求数")
    p.add_argument("--duration", type=int, default=60, help="压测持续秒数")
    p.add_argument("--concurrency", type=int, default=200, help="最大并发请求数")
    p.add_argument("--timeout", type=float, default=15.0, help="单次请求超时（秒）")
    return p.parse_args()


class Stats:
    def __init__(self) -> None:
        self.latencies: list[float] = []
        self.success = 0
        self.failure = 0
        self._lock = asyncio.Lock()

    async def add(self, latency: float | None, ok: bool) -> None:
        async with self._lock:
            if latency is not None:
                self.latencies.append(latency)
            if ok:
                self.success += 1
            else:
                self.failure += 1

    def report(self) -> str:
        total = self.success + self.failure
        if self.latencies:
            avg = statistics.mean(self.latencies)
            p95 = statistics.quantiles(self.latencies, n=100)[94]
            p99 = statistics.quantiles(self.latencies, n=100)[98]
        else:
            avg = p95 = p99 = 0.0
        return (
            f"total={total}, success={self.success}, failure={self.failure}, "
            f"avg={avg * 1000:.2f}ms p95={p95 * 1000:.2f}ms p99={p99 * 1000:.2f}ms"
        )


async def run_with_httpx(
    url: str, headers: dict, body: dict, qps: int, duration: int, concurrency: int, timeout: float
) -> None:
    import httpx

    stats = Stats()
    semaphore = asyncio.Semaphore(concurrency)

    async def do_request(client: httpx.AsyncClient) -> None:
        start = time.perf_counter()
        try:
            resp = await client.post(url, headers=headers, json=body, timeout=timeout)
            latency = time.perf_counter() - start
            ok = resp.status_code == 200
            await stats.add(latency, ok)
        except Exception:
            await stats.add(None, False)

    async with httpx.AsyncClient() as client:
        tasks: list[asyncio.Task] = []
        interval = 1.0 / qps
        stop_at = time.perf_counter() + duration
        # schedule requests at steady QPS
        while time.perf_counter() < stop_at:
            await semaphore.acquire()

            async def wrapper() -> None:
                try:
                    await do_request(client)
                finally:
                    semaphore.release()

            tasks.append(asyncio.create_task(wrapper()))
            await asyncio.sleep(interval)

        # 等待所有任务完成（但不要无限期等待）
        await asyncio.gather(*tasks, return_exceptions=True)

    print("finished:", stats.report())


def run_with_requests(
    url: str, headers: dict, body: dict, qps: int, duration: int, concurrency: int, timeout: float
) -> None:
    import concurrent.futures

    import requests

    stats = {
        "latencies": [],
        "success": 0,
        "failure": 0,
    }

    def do_request() -> None:
        start = time.perf_counter()
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
            latency = time.perf_counter() - start
            stats["latencies"].append(latency)
            if resp.status_code == 200:
                stats["success"] += 1
            else:
                stats["failure"] += 1
        except Exception:
            stats["failure"] += 1

    interval = 1.0 / qps
    total_requests = int(qps * duration)
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = []
        for _ in range(total_requests):
            futures.append(ex.submit(do_request))
            time.sleep(interval)
        for _ in concurrent.futures.as_completed(futures):
            pass

    lat = stats["latencies"]
    if lat:
        avg = statistics.mean(lat)
        p95 = statistics.quantiles(lat, n=100)[94]
        p99 = statistics.quantiles(lat, n=100)[98]
    else:
        avg = p95 = p99 = 0.0

    total = stats["success"] + stats["failure"]
    print(
        f"total={total}, success={stats['success']}, failure={stats['failure']}, avg={avg * 1000:.2f}ms p95={p95 * 1000:.2f}ms p99={p99 * 1000:.2f}ms"
    )


def main() -> int:
    args = build_args()
    url = args.url
    qps = args.qps
    duration = args.duration
    concurrency = args.concurrency
    timeout = args.timeout

    # try async httpx first
    try:
        importlib.import_module("httpx")
        print("Using async httpx client")
        asyncio.run(run_with_httpx(url, DEFAULT_HEADERS, DEFAULT_BODY, qps, duration, concurrency, timeout))
        return 0
    except Exception:
        # fallback to requests
        print("httpx not available or failed to import, falling back to requests + threads")
        run_with_requests(url, DEFAULT_HEADERS, DEFAULT_BODY, qps, duration, concurrency, timeout)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
