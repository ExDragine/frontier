"""Measure real local ASR CPU/memory pressure without loading production config.

Output: JSON samples and a standalone HTML report. No private QQ audio is read.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import html
import io
import json
import os
import platform
import statistics
import sys
import time
import wave
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

import psutil

ROOT = Path(__file__).resolve().parents[1]


def _cpu_name() -> str:
    if os.name == "nt":
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
    return platform.processor()


def _wav(pcm: bytes) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(pcm)
    return output.getvalue()


async def _measure(label, inputs, settings, transcribe):
    parent = psutil.Process()
    baseline = parent.memory_info().rss
    sampled = {"peak_rss": baseline, "peak_private": 0, "peak_children": 0, "peak_recognizers": 0, "cpu_seconds": 0.0}
    last_cpu = {}
    finished = asyncio.Event()

    async def sample():
        while not finished.is_set():
            children = parent.children(recursive=True)
            recognizers = 0
            rss = private = 0
            for process in [parent, *children]:
                try:
                    memory = process.memory_info()
                    recognizers += process.name().lower().startswith("llama-funasr-sensevoice")
                    rss += memory.rss
                    private += getattr(memory, "private", getattr(memory, "data", 0))
                    times = process.cpu_times()
                    cpu = times.user + times.system
                    previous = last_cpu.get(process.pid, cpu if process.pid == parent.pid else 0.0)
                    sampled["cpu_seconds"] += max(0, cpu - previous)
                    last_cpu[process.pid] = cpu
                except psutil.Error:
                    continue
            sampled["peak_rss"] = max(sampled["peak_rss"], rss)
            sampled["peak_private"] = max(sampled["peak_private"], private)
            sampled["peak_children"] = max(sampled["peak_children"], len(children))
            sampled["peak_recognizers"] = max(sampled["peak_recognizers"], recognizers)
            await asyncio.sleep(0.04)

    monitor = asyncio.create_task(sample())
    started = time.perf_counter()

    async def recognize(data):
        try:
            return {"status": "success", **asdict(await transcribe(data, settings=settings))}
        except Exception as exc:
            return {"status": "failed", "code": getattr(exc, "code", type(exc).__name__)}

    try:
        results = await asyncio.gather(*(recognize(data) for data in inputs))
    finally:
        elapsed = time.perf_counter() - started
        finished.set()
        await monitor
    successful = [result for result in results if result["status"] == "success"]
    durations = sum(result["audio_seconds"] for result in successful)
    return {
        "case": label,
        "requests": len(inputs),
        "wall_seconds": elapsed,
        "peak_rss_mib": sampled["peak_rss"] / 1024**2,
        "incremental_rss_mib": (sampled["peak_rss"] - baseline) / 1024**2,
        "peak_private_mib": sampled["peak_private"] / 1024**2,
        "cpu_seconds_sampled": sampled["cpu_seconds"],
        "average_cores_sampled": sampled["cpu_seconds"] / elapsed,
        "peak_children": sampled["peak_children"],
        "peak_active_recognizers": sampled["peak_recognizers"],
        "rtf_including_queue_load_decode": elapsed / durations if durations else None,
        "results": results,
    }


def _write_report(path, report):
    rows = []
    for case in report["cases"]:
        rtf = case["rtf_including_queue_load_decode"]
        codes = ", ".join(item["status"] + (":" + item["code"] if "code" in item else "") for item in case["results"])
        rows.append(
            f"<tr><td>{html.escape(case['case'])}</td><td>{case['requests']}</td>"
            f"<td>{case['wall_seconds']:.2f}</td><td>{case['peak_rss_mib']:.1f}</td>"
            f"<td>{case['peak_private_mib']:.1f}</td><td>{case['average_cores_sampled']:.2f}</td>"
            f"<td>{f'{rtf:.3f}' if rtf is not None else '—'}</td><td>{html.escape(codes)}</td></tr>"
        )
    text = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>SenseVoiceSmall Q8 本地语音识别资源报告</title>
<style>body{{font:16px/1.7 system-ui;max-width:1200px;margin:36px auto;padding:0 24px;color:#182230}}
table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:10px;border:1px solid #d8dee8;text-align:left}}
th{{background:#eef3f8}}code,pre{{background:#f3f5f8;padding:10px}}p{{max-width:1050px}}</style>
<h1>SenseVoiceSmall Q8 本地语音识别资源报告</h1>
<p>时间：{html.escape(report["time"])}。硬件：{html.escape(report["hardware"]["cpu"])}；
{report["hardware"]["memory_gib"]:.1f} GiB；{html.escape(report["hardware"]["os"])}。
ASR 最多使用 {report["settings"]["max_cpu_cores"]} 个逻辑 CPU，全局并发 1。</p>
<p>使用公开模型示例音频，30 秒和 120 秒样本由同一语音重复构造。
RSS/私有提交内存为基准程序与其子进程之和，每 40ms 采样；CPU 时间也由采样估计，短进程可能漏计。
每条请求都包含模型加载、解码与排队，未将系统文件缓存当作冷磁盘加载。
这里不是 6 核 Intel、8GB 目标机的实测，也没有对 Windows 或整台机器施加 8GB 内存限制。</p>
<table><tr><th>用例</th><th>请求数</th><th>总耗时/s</th><th>峰值 RSS/MiB</th>
<th>峰值私有内存/MiB</th><th>平均 CPU 核数/估计</th><th>RTF</th><th>结果</th></tr>{"".join(rows)}</table>
<p>RTF = 总耗时 / 成功识别的音频总时长，越小越快。并发用例展示排队后的总吞吐，
每条请求延迟和转写结果见配套 JSON。静音预期返回 no_speech，超长音频预期拒绝。
首次请求是本次进程的首次调用；并非操作系统启动后的冷缓存测试。</p>
<p>运行方式为按需启动 CLI、完成即退出；空闲时没有常驻识别模型进程。
峰值不包含生产机器人、QQ、浏览器及 Windows 的内存。建议在目标机用相同脚本复测，
并保留足够的系统与应用可用内存，确认没有持续分页。</p>
<p>这是识别资源报告；不包含尚未选定的语音合成模型，也不是识别准确率基准。</p>
<h2>可复现参数</h2><pre>{html.escape(json.dumps(report["settings"], ensure_ascii=False, indent=2))}</pre>
</html>"""
    path.write_text(text, encoding="utf-8")


async def _benchmark(args, directory):
    import imageio_ffmpeg

    from utils.configs import SpeechRecognitionConfig
    from utils.speech_recognition import _run_process, transcribe_audio

    settings = SpeechRecognitionConfig(
        enabled=True,
        executable=str(args.executable.resolve()),
        model_path=str(args.model.resolve()),
        vad_model_path=str(args.vad.resolve()),
        max_cpu_cores=args.cores,
        timeout_seconds=args.timeout,
    )
    original = args.audio.read_bytes()
    decoded = directory / "reference.wav"
    await _run_process(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(args.audio.resolve()),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(decoded),
        ],
        cores=args.cores,
    )
    with wave.open(str(decoded), "rb") as source:
        pcm = source.readframes(source.getnframes())

    def repeat(seconds):
        size = seconds * 16000 * 2
        return _wav((pcm * (size // len(pcm) + 1))[:size])

    # Produce a genuine Tencent SILK clip with the locked codec dependency.
    import pysilk

    silk = io.BytesIO()
    pysilk.encode(io.BytesIO(pcm), silk, 16000, 24000, tencent=True)
    cases = [
        ("首次 MP3 请求", [original]),
        ("MP3 重复请求", [original]),
        ("Tencent SILK", [silk.getvalue()]),
        ("30 秒 WAV", [repeat(30)]),
        ("120 秒 WAV", [repeat(120)]),
        ("2 请求同时到达", [original] * 2),
        ("4 请求同时到达", [original] * 4),
        ("5 秒静音", [_wav(b"\0\0" * 16000 * 5)]),
        ("超长 121 秒", [repeat(121)]),
    ]
    results = []
    for label, inputs in cases:
        print(f"Running {label}...", flush=True)
        results.append(await _measure(label, inputs, settings, transcribe_audio))
    memory = psutil.virtual_memory()
    report = {
        "time": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "hardware": {
            "cpu": _cpu_name(),
            "os": platform.platform(),
            "logical_cpus": psutil.cpu_count(),
            "memory_gib": memory.total / 1024**3,
            "available_memory_gib_at_end": memory.available / 1024**3,
        },
        "settings": settings.model_dump(exclude={"enabled"}),
        "model_bytes": args.model.stat().st_size,
        "executable_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        "sampling_interval_seconds": 0.04,
        "median_single_short_seconds": statistics.median(item["wall_seconds"] for item in results[:3]),
        "cases": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(args.output / "report.html", report)
    print(f"Report: {args.output / 'report.html'}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = ROOT / "cache/speech/sensevoice"
    parser.add_argument("--executable", type=Path, default=base / "runtime/llama-funasr-sensevoice.exe")
    parser.add_argument("--model", type=Path, default=base / "sensevoice-small-q8.gguf")
    parser.add_argument("--vad", type=Path, default=base / "fsmn-vad.gguf")
    parser.add_argument("--audio", type=Path, required=True, help="Public or explicitly selected test audio")
    parser.add_argument("--cores", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path, default=ROOT / ".temp/sensevoice-benchmark")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    with TemporaryDirectory(prefix="frontier-asr-benchmark-") as temporary:
        directory = Path(temporary)
        config = directory / "env.toml"
        config.write_text(
            'config_version = 2\n[dashboard]\npassword="benchmark-only"\n'
            'jwt_secret="benchmark-isolated-secret-at-least-32-bytes"\n',
            encoding="utf-8",
        )
        os.environ["FRONTIER_CONFIG"] = str(config)
        report = asyncio.run(_benchmark(args, directory))
    unexpected = [
        case["case"] for case in report["cases"][:-2] if any(item["status"] != "success" for item in case["results"])
    ]
    if any(case["peak_active_recognizers"] > 1 for case in report["cases"]):
        unexpected.append("recognizer_concurrency_limit")
    for case, code in zip(report["cases"][-2:], ("no_speech", "audio_duration_limit"), strict=True):
        if case["results"] != [{"status": "failed", "code": code}]:
            unexpected.append(case["case"])
    if unexpected:
        raise SystemExit("Unexpected outcomes: " + ", ".join(unexpected))


if __name__ == "__main__":
    main()
