"""Compare the current candidate gate with a local Laya reply-gate model.

This is an offline smoke evaluation over the checked-in, synthetic fixture. It
does not claim production accuracy; replace the fixture with redacted and
human-labeled traffic before enabling a canary.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from plugins.agent.gateway import _looks_like_reply_check_candidate  # noqa: E402
from utils.decision import LayaDecisionProvider, score_reply_gate  # noqa: E402


def _load_cases(path: Path) -> list[dict[str, Any]]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def _metrics(labels: list[bool], predictions: list[bool]) -> dict[str, float | int]:
    pairs = zip(labels, predictions, strict=True)
    tp = sum(label and prediction for label, prediction in pairs)
    pairs = zip(labels, predictions, strict=True)
    tn = sum(not label and not prediction for label, prediction in pairs)
    pairs = zip(labels, predictions, strict=True)
    fp = sum(not label and prediction for label, prediction in pairs)
    pairs = zip(labels, predictions, strict=True)
    fn = sum(label and not prediction for label, prediction in pairs)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "accuracy": (tp + tn) / len(labels) if labels else 0.0,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "positive_predictions": tp + fp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percentile)))
    return ordered[index]


async def _evaluate(cases: list[dict[str, Any]], *, model: str, threshold: float) -> dict[str, Any]:
    labels = [bool(case["label"]) for case in cases]
    baseline = [
        _looks_like_reply_check_candidate(str(case["text"]), active_group=bool(case.get("active_group", False)))
        for case in cases
    ]
    provider = LayaDecisionProvider(model=model)
    laya_predictions = []
    laya_labels = []
    probabilities = []
    latencies = []
    errors = []
    for case in cases:
        try:
            score = await score_reply_gate(provider, str(case["text"]), case.get("history", ()), threshold=threshold)
        except Exception as error:  # noqa: BLE001 - report per-case evaluation failures
            errors.append({"text": case["text"], "error": f"{type(error).__name__}: {error}"})
            continue
        if score.probability is None:
            errors.append({"text": case["text"], "error": "Decision provider refused"})
            continue
        laya_predictions.append(score.should_reply)
        laya_labels.append(bool(case["label"]))
        probabilities.append(score.probability)
        latencies.append(score.decision.latency_ms)

    result: dict[str, Any] = {
        "cases": len(cases),
        "model": model,
        "threshold": threshold,
        "baseline_candidate_gate": _metrics(labels, baseline),
        "laya": {
            "evaluated": len(laya_predictions),
            "metrics": _metrics(laya_labels, laya_predictions),
            "threshold_sweep": {
                f"{candidate:.1f}": _metrics(
                    laya_labels,
                    [probability > candidate for probability in probabilities],
                )
                for candidate in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
            },
            "mean_probability": statistics.mean(probabilities) if probabilities else None,
            "mean_latency_ms": statistics.mean(latencies) if latencies else None,
            "cold_start_latency_ms": latencies[0] if latencies else None,
            "warm_mean_latency_ms": statistics.mean(latencies[1:]) if len(latencies) > 1 else None,
            "p95_latency_ms": _percentile(latencies[1:], 0.95) if len(latencies) > 1 else None,
            "errors": errors,
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="auto")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "benchmarks" / "reply_gate_cases.jsonl",
    )
    args = parser.parse_args()
    result = asyncio.run(_evaluate(_load_cases(args.cases), model=args.model, threshold=args.threshold))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
