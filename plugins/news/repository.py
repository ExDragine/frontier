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
                attempts INTEGER DEFAULT 0, lease TEXT, lease_until REAL DEFAULT 0,
                error TEXT, updated_at REAL, PRIMARY KEY(report_id,target))"""
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

    async def complete(self, report_id, token, status, articles, payload):
        """Persist a finished report; fails if the generation lease was lost."""
        now = time.time()
        evidence = json.dumps(
            [article.model_dump(mode="json") for article in articles],
            ensure_ascii=False,
        )
        data = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False)

        def save(database):
            changed = database.execute(
                "UPDATE news_reports SET stage='complete',status=?,evidence=?,payload=?,"
                "lease=NULL,lease_until=0,updated_at=?,error=NULL "
                "WHERE id=? AND lease=? AND lease_until>?",
                (status, evidence, data, now, report_id, token, now),
            ).rowcount
            if not changed:
                raise RuntimeError("news lease lost")

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

    async def stage_deliveries(self, report_id, targets):
        now = time.time()

        def stage(database):
            for target in sorted(set(targets)):
                database.execute(
                    "INSERT OR IGNORE INTO news_deliveries"
                    "(report_id,target,updated_at) VALUES(?,?,?)",
                    (report_id, target, now),
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

    async def mark_delivery(self, report_id, target, state, error=None):
        now = time.time()
        await self._run(
            lambda database: database.execute(
                "UPDATE news_deliveries SET state=?,error=?,attempts=attempts+1,updated_at=? "
                "WHERE report_id=? AND target=?",
                (state, error, now, report_id, target),
            ).rowcount
        )

    async def retry_failed(self, report_id, targets):
        now = time.time()

        def requeue(database):
            requeued = []
            for target in targets:
                changed = database.execute(
                    "UPDATE news_deliveries SET state='pending',updated_at=? "
                    "WHERE report_id=? AND target=? AND state='failed'",
                    (now, report_id, target),
                ).rowcount
                if changed:
                    requeued.append(target)
            return requeued

        return await self._run(requeue)

    async def prune(self, retention_days):
        now = time.time()
        cutoff = now - retention_days * 86400

        def remove(database):
            rows = database.execute(
                "SELECT id FROM news_reports WHERE updated_at<? AND lease_until<=? "
                "AND NOT EXISTS (SELECT 1 FROM news_deliveries WHERE report_id=news_reports.id "
                "AND (updated_at>=? OR state='pending'))",
                (cutoff, now, cutoff),
            ).fetchall()
            for row in rows:
                database.execute("DELETE FROM news_deliveries WHERE report_id=?", (row["id"],))
                database.execute("DELETE FROM news_reports WHERE id=?", (row["id"],))
            return len(rows)

        return await self._run(remove)
