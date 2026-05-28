import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlmodel import Session, select

from utils.database import Message, MessageDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Chroma semantic indexes from SQLite messages.")
    parser.add_argument("--batch-size", type=int, default=16, help="SQLite rows to read per loop.")
    parser.add_argument("--embedding-batch-size", type=int, default=None, help="Texts to embed per model forward pass.")
    parser.add_argument("--device", default=None, help='Embedding device override, for example "cpu", "cuda", or "cuda:0".')
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    database = MessageDatabase()
    vector_index = database.get_vector_index()
    if not vector_index or not getattr(vector_index, "available", False):
        print("Chroma message vector index is unavailable.")
        return
    if args.embedding_batch_size is not None:
        vector_index.config.embedding_batch_size = max(1, args.embedding_batch_size)
    if args.device is not None:
        vector_index.config.embedding_device = args.device

    total = 0
    last_time = -1
    started_at = time.monotonic()
    with Session(database.engine) as session:
        while True:
            remaining = None if args.limit is None else max(0, args.limit - total)
            if remaining == 0:
                break
            batch_limit = min(args.batch_size, remaining) if remaining is not None else args.batch_size
            messages = session.exec(
                select(Message).where(Message.time > last_time).order_by(Message.time).limit(batch_limit)
            ).all()
            if not messages:
                break
            added = vector_index.add_messages(messages)
            total += added
            last_time = messages[-1].time
            print(f"indexed={total} last_time={last_time}")
            if added == 0:
                break

    print(f"finished indexed={total} elapsed={time.monotonic() - started_at:.2f}s")


if __name__ == "__main__":
    main()
