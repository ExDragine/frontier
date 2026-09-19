"""Durable report and per-target delivery state."""

import asyncio
import json
import sqlite3
import time
import uuid
from pathlib import Path

from .schemas import Edition


class NewsRepository:
    def __init__(self, path="news.db"):
        self.path = str(path)

    async def _run(self, operation):
        def work():
            database = sqlite3.connect(self.path, timeout=5)
            database.row_factory = sqlite3.Row
            try:
                database.execute("BEGIN IMMEDIATE")
                result = operation(database)
                database.commit()
                return result
            except BaseException:
                database.rollback()
                raise
            finally:
                database.close()

        return await asyncio.to_thread(work)

    async def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        def create(database):
            database.execute(
                """CREATE TABLE IF NOT EXISTS news_reports(
                id TEXT PRIMARY KEY, board TEXT, namespace TEXT, scheduled_at REAL,
                status TEXT, stage TEXT, evidence TEXT, payload TEXT, image BLOB,
                error TEXT, lease TEXT, lease_until REAL DEFAULT 0, updated_at REAL)"""
            )
            database.execute(
                """CREATE TABLE IF NOT EXISTS news_deliveries(
                report_id TEXT, target TEXT, state TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0, next_attempt REAL DEFAULT 0, deadline REAL,
                lease TEXT, lease_until REAL DEFAULT 0, receipt TEXT, error TEXT,
                updated_at REAL, PRIMARY KEY(report_id,target))"""
            )

        await self._run(create)

    @staticmethod
    def _decode(row):
        if not row:
            return None
        result = dict(row)
        for key in ("evidence", "payload"):
            result[key] = json.loads(result[key]) if result[key] else None
        return result

    async def get(self, report_id):
        return await self._run(
            lambda database: self._decode(
                database.execute(
                    "SELECT * FROM news_reports WHERE id=?", (report_id,)
                ).fetchone()
            )
        )

    async def latest(self, board):
        query = (
            "SELECT * FROM news_reports WHERE board=? AND namespace='published' "
            "AND status IN ('ready','degraded') ORDER BY scheduled_at DESC LIMIT 1"
        )
        return await self._run(
            lambda database: self._decode(database.execute(query, (board,)).fetchone())
        )

    async def claim(self, edition: Edition, ttl=330):
        now = time.time()
        token = uuid.uuid4().hex

        def claim_report(database):
            database.execute(
                "INSERT OR IGNORE INTO news_reports VALUES"
                "(?,?,?,?,?,'collect','[]',NULL,NULL,NULL,NULL,0,?)",
                (
                    edition.report_id,
                    edition.board,
                    edition.namespace,
                    edition.scheduled_at.timestamp(),
                    "pending",
                    now,
                ),
            )
            changed = database.execute(
                "UPDATE news_reports SET status='generating',lease=?,lease_until=?,updated_at=? "
                "WHERE id=? AND status NOT IN ('ready','degraded') AND lease_until<=?",
                (token, now + ttl, now, edition.report_id, now),
            ).rowcount
            return token if changed else None

        return await self._run(claim_report)

    async def checkpoint(
        self, report_id, token, stage, articles=None, payload=None, status="generating"
    ):
        now = time.time()

        def save(database):
            row = database.execute(
                "SELECT evidence,payload FROM news_reports "
                "WHERE id=? AND lease=? AND lease_until>?",
                (report_id, token, now),
            ).fetchone()
            if not row:
                raise RuntimeError("news lease lost")
            evidence = (
                json.dumps(
                    [article.model_dump(mode="json") for article in articles],
                    ensure_ascii=False,
                )
                if articles is not None
                else row["evidence"]
            )
            data = (
                json.dumps(payload.model_dump(mode="json"), ensure_ascii=False)
                if payload is not None
                else row["payload"]
            )
            done = status in {"ready", "degraded"}
            database.execute(
                "UPDATE news_reports SET stage=?,status=?,evidence=?,payload=?,lease=?,"
                "lease_until=?,updated_at=? WHERE id=? AND lease=?",
                (
                    stage,
                    status,
                    evidence,
                    data,
                    None if done else token,
                    0 if done else now + 330,
                    now,
                    report_id,
                    token,
                ),
            )

        await self._run(save)

    async def fail(self, report_id, token, error):
        now = time.time()
        await self._run(
            lambda database: database.execute(
                "UPDATE news_reports SET status='failed',error=?,lease=NULL,"
                "lease_until=0,updated_at=? WHERE id=? AND lease=?",
                (error[:200], now, report_id, token),
            ).rowcount
        )

    async def set_image(self, report_id, image):
        await self._run(
            lambda database: database.execute(
                "UPDATE news_reports SET image=?,updated_at=? WHERE id=?",
                (image, time.time(), report_id),
            ).rowcount
        )

    async def stage_deliveries(self, report_id, targets, deadline):
        now = time.time()

        def stage(database):
            for target in sorted(set(targets)):
                database.execute(
                    "INSERT OR IGNORE INTO news_deliveries"
                    "(report_id,target,deadline,updated_at) VALUES(?,?,?,?)",
                    (report_id, target, deadline, now),
                )

        await self._run(stage)

    async def deliveries(self, report_id):
        return await self._run(
            lambda database: [
                dict(row)
                for row in database.execute(
                    "SELECT * FROM news_deliveries WHERE report_id=? ORDER BY target",
                    (report_id,),
                ).fetchall()
            ]
        )

    async def claim_delivery(self, report_id, target, ttl=60, max_attempts=3):
        now = time.time()
        token = uuid.uuid4().hex

        def claim_target(database):
            database.execute(
                "UPDATE news_deliveries SET state='unknown',"
                "error='expired_inflight_send',updated_at=? "
                "WHERE state='sending' AND lease_until<=?",
                (now, now),
            )
            changed = database.execute(
                "UPDATE news_deliveries SET state='sending',attempts=attempts+1,"
                "lease=?,lease_until=?,updated_at=? WHERE report_id=? AND target=? "
                "AND state IN ('pending','failed') AND next_attempt<=? "
                "AND deadline>? AND attempts<?",
                (
                    token,
                    now + ttl,
                    now,
                    report_id,
                    target,
                    now,
                    now,
                    max_attempts,
                ),
            ).rowcount
            return token if changed else None

        return await self._run(claim_target)

    async def finish_delivery(
        self, report_id, target, token, state, receipt=None, error=None, retry_delay=60
    ):
        now = time.time()
        await self._run(
            lambda database: database.execute(
                "UPDATE news_deliveries SET state=?,receipt=?,error=?,next_attempt=?,"
                "lease=NULL,lease_until=0,updated_at=? "
                "WHERE report_id=? AND target=? AND lease=?",
                (
                    state,
                    receipt,
                    error,
                    now + retry_delay,
                    now,
                    report_id,
                    target,
                    token,
                ),
            ).rowcount
        )

    async def retry_failed(self, report_id, targets, deadline):
        now = time.time()

        def requeue(database):
            for target in targets:
                database.execute(
                    "UPDATE news_deliveries SET state='pending',attempts=0,next_attempt=0,"
                    "deadline=?,updated_at=? WHERE report_id=? AND target=? AND state='failed'",
                    (deadline, now, report_id, target),
                )

        await self._run(requeue)
