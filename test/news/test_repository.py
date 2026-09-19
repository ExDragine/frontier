# ruff: noqa: S101
import time
import pytest
from plugins.news.repository import NewsRepository
@pytest.mark.asyncio
async def test_failed_delivery_can_be_explicitly_requeued(tmp_path):
 r=NewsRepository(tmp_path/"news.db");await r.initialize()
 # State semantics are exercised through direct rows to keep this a repository contract test.
 now=time.time()
 await r._run(lambda db:db.execute("INSERT INTO news_reports(id,board,namespace,scheduled_at,status,stage,evidence,updated_at) VALUES('r','g','published',?,'ready','complete','[]',?)",(now,now)))
 await r.stage_deliveries("r",["1"],now+60)
 token=await r.claim_delivery("r","1");assert token
 await r.finish_delivery("r","1",token,"failed",error="x")
 await r.retry_failed("r",["1"],now+60)
 assert (await r.deliveries("r"))[0]["state"]=="pending"
@pytest.mark.asyncio
async def test_expired_inflight_is_unknown_not_retried(tmp_path):
 r=NewsRepository(tmp_path/"news.db");await r.initialize();now=time.time()
 await r._run(lambda db:db.execute("INSERT INTO news_reports(id,board,namespace,scheduled_at,status,stage,evidence,updated_at) VALUES('r','g','published',?,'ready','complete','[]',?)",(now,now)))
 await r.stage_deliveries("r",["1"],now+60);token=await r.claim_delivery("r","1",ttl=1);assert token
 await r._run(lambda db:db.execute("UPDATE news_deliveries SET lease_until=0 WHERE report_id='r'"))
 assert await r.claim_delivery("r","1") is None
 assert (await r.deliveries("r"))[0]["state"]=="unknown"
