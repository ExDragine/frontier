"""Durable report and per-target delivery state."""
import asyncio,json,sqlite3,time,uuid
from pathlib import Path
from .schemas import Article,Edition,NewsPayload
class NewsRepository:
 def __init__(self,path="news.db"): self.path=str(path)
 async def _run(self,fn):
  def work():
   db=sqlite3.connect(self.path,timeout=5); db.row_factory=sqlite3.Row
   try: db.execute("BEGIN IMMEDIATE"); out=fn(db); db.commit(); return out
   except BaseException: db.rollback(); raise
   finally: db.close()
  return await asyncio.to_thread(work)
 async def initialize(self):
  Path(self.path).parent.mkdir(parents=True,exist_ok=True)
  def op(db):
   db.execute("""CREATE TABLE IF NOT EXISTS news_reports(id TEXT PRIMARY KEY,board TEXT,namespace TEXT,scheduled_at REAL,status TEXT,stage TEXT,evidence TEXT,payload TEXT,image BLOB,error TEXT,lease TEXT,lease_until REAL DEFAULT 0,updated_at REAL)""")
   db.execute("""CREATE TABLE IF NOT EXISTS news_deliveries(report_id TEXT,target TEXT,state TEXT DEFAULT 'pending',attempts INTEGER DEFAULT 0,next_attempt REAL DEFAULT 0,deadline REAL,lease TEXT,lease_until REAL DEFAULT 0,receipt TEXT,error TEXT,updated_at REAL,PRIMARY KEY(report_id,target))""")
  await self._run(op)
 def _decode(self,row):
  if not row:return None
  d=dict(row)
  for k in ("evidence","payload"): d[k]=json.loads(d[k]) if d[k] else None
  return d
 async def get(self,rid): return await self._run(lambda db:self._decode(db.execute("SELECT * FROM news_reports WHERE id=?",(rid,)).fetchone()))
 async def latest(self,board):
  return await self._run(lambda db:self._decode(db.execute("SELECT * FROM news_reports WHERE board=? AND namespace='published' AND status IN ('ready','degraded') ORDER BY scheduled_at DESC LIMIT 1",(board,)).fetchone()))
 async def claim(self,e:Edition,ttl=330):
  now=time.time(); token=uuid.uuid4().hex
  def op(db):
   db.execute("INSERT OR IGNORE INTO news_reports VALUES(?,?,?,?,?,'collect','[]',NULL,NULL,NULL,NULL,0,?)",(e.report_id,e.board,e.namespace,e.scheduled_at.timestamp(),"pending",now))
   n=db.execute("UPDATE news_reports SET status='generating',lease=?,lease_until=?,updated_at=? WHERE id=? AND status NOT IN ('ready','degraded') AND lease_until<=?",(token,now+ttl,now,e.report_id,now)).rowcount
   return token if n else None
  return await self._run(op)
 async def checkpoint(self,rid,token,stage,articles=None,payload=None,status="generating"):
  now=time.time()
  def op(db):
   row=db.execute("SELECT evidence,payload FROM news_reports WHERE id=? AND lease=? AND lease_until>?",(rid,token,now)).fetchone()
   if not row: raise RuntimeError("news lease lost")
   evidence=json.dumps([a.model_dump(mode="json") for a in articles],ensure_ascii=False) if articles is not None else row["evidence"]
   data=json.dumps(payload.model_dump(mode="json"),ensure_ascii=False) if payload is not None else row["payload"]
   done=status in ("ready","degraded")
   db.execute("UPDATE news_reports SET stage=?,status=?,evidence=?,payload=?,lease=?,lease_until=?,updated_at=? WHERE id=? AND lease=?",(stage,status,evidence,data,None if done else token,0 if done else now+330,now,rid,token))
  await self._run(op)
 async def fail(self,rid,token,error):
  await self._run(lambda db:db.execute("UPDATE news_reports SET status='failed',error=?,lease=NULL,lease_until=0,updated_at=? WHERE id=? AND lease=?",(error[:200],time.time(),rid,token)).rowcount)
 async def set_image(self,rid,image): await self._run(lambda db:db.execute("UPDATE news_reports SET image=?,updated_at=? WHERE id=?",(image,time.time(),rid)).rowcount)
 async def stage_deliveries(self,rid,targets,deadline):
  now=time.time()
  await self._run(lambda db:[db.execute("INSERT OR IGNORE INTO news_deliveries(report_id,target,deadline,updated_at) VALUES(?,?,?,?)",(rid,t,deadline,now)) for t in sorted(set(targets))])
 async def deliveries(self,rid): return await self._run(lambda db:[dict(r) for r in db.execute("SELECT * FROM news_deliveries WHERE report_id=? ORDER BY target",(rid,)).fetchall()])
 async def claim_delivery(self,rid,target,ttl=60,max_attempts=3):
  now=time.time(); token=uuid.uuid4().hex
  def op(db):
   db.execute("UPDATE news_deliveries SET state='unknown',error='expired_inflight_send',updated_at=? WHERE state='sending' AND lease_until<=?",(now,now))
   n=db.execute("UPDATE news_deliveries SET state='sending',attempts=attempts+1,lease=?,lease_until=?,updated_at=? WHERE report_id=? AND target=? AND state IN ('pending','failed') AND next_attempt<=? AND deadline>? AND attempts<?",(token,now+ttl,now,rid,target,now,now,max_attempts)).rowcount
   return token if n else None
  return await self._run(op)
 async def finish_delivery(self,rid,target,token,state,receipt=None,error=None,retry_delay=60):
  await self._run(lambda db:db.execute("UPDATE news_deliveries SET state=?,receipt=?,error=?,next_attempt=?,lease=NULL,lease_until=0,updated_at=? WHERE report_id=? AND target=? AND lease=?",(state,receipt,error,time.time()+retry_delay,time.time(),rid,target,token)).rowcount)
 async def retry_failed(self,rid,targets,deadline):
  await self._run(lambda db:[db.execute("UPDATE news_deliveries SET state='pending',attempts=0,next_attempt=0,deadline=?,updated_at=? WHERE report_id=? AND target=? AND state='failed'",(deadline,time.time(),rid,t)) for t in targets])
