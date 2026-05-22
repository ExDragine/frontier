# ruff: noqa: E402, I001

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.database import (
    cleanup_task_execution_history,
    get_database_diagnostics,
    get_engine,
    run_database_maintenance,
)


def _retention_cutoff(days: int | None) -> int | None:
    if days is None:
        return None
    return int(time.time()) - days * 86400


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and maintain the Frontier SQLite database.")
    parser.add_argument("--database-url", default=None, help="SQLAlchemy database URL, defaults to frontier.db.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("diagnose", help="Print database diagnostics as JSON.")

    maintain_parser = subparsers.add_parser("maintain", help="Run PRAGMA optimize and optional WAL checkpoint.")
    maintain_parser.add_argument("--checkpoint", action="store_true", help="Run a passive WAL checkpoint.")

    cleanup_parser = subparsers.add_parser("cleanup-history", help="Prune task execution history.")
    cleanup_parser.add_argument("--older-than-days", type=int, default=None, help="Delete rows older than this many days.")
    cleanup_parser.add_argument("--keep-per-job", type=int, default=None, help="Keep only the newest N rows per job.")

    args = parser.parse_args()
    engine = get_engine(args.database_url)

    if args.command == "diagnose":
        print(json.dumps(get_database_diagnostics(engine), ensure_ascii=False, indent=2, default=str))
        return

    if args.command == "maintain":
        print(json.dumps(run_database_maintenance(engine, checkpoint=args.checkpoint), ensure_ascii=False, indent=2))
        return

    if args.command == "cleanup-history":
        cutoff = _retention_cutoff(args.older_than_days)
        deleted = cleanup_task_execution_history(engine, older_than=cutoff, keep_per_job=args.keep_per_job)
        payload = {
            "deleted": deleted,
            "older_than": cutoff,
            "older_than_iso": datetime.datetime.fromtimestamp(cutoff).isoformat() if cutoff is not None else None,
            "keep_per_job": args.keep_per_job,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
