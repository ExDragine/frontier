"""Direct search-provider collection with fallback."""
import asyncio,datetime as dt,hashlib,os
from urllib.parse import urlsplit
from .schemas import Article,canonical_url,compact,eligible
class SourceError(RuntimeError):
 def __init__(self,code,retryable=False): super().__init__(code); self.retryable=retryable
def pub(v):
 if not isinstance(v,str):return None
 try:
  x=dt.datetime.fromisoformat(v.replace("Z","+00:00")); return x.astimezone(dt.UTC) if x.tzinfo else None
 except ValueError:return None
class SearchSource:
 urls={"exa":"https://api.exa.ai/search","tavily":"https://api.tavily.com/search"}
 def __init__(self,name,key,client,cfg): self.name,self.key,self.client,self.cfg=name,key,client,cfg
 async def search(self,q,e):
  if not self.key: raise SourceError("missing_key")
  if self.name=="exa":
   h={"x-api-key":self.key}; b={"query":q,"type":"auto","numResults":self.cfg.source_results,"startPublishedDate":e.start.isoformat(),"endPublishedDate":e.scheduled_at.isoformat(),"contents":{"text":True}}
  else:
   h={"Authorization":f"Bearer {self.key}"}; b={"query":q,"topic":"news","max_results":self.cfg.source_results,"include_raw_content":True,"start_date":e.start.date().isoformat(),"end_date":e.scheduled_at.date().isoformat()}
  async with asyncio.timeout(self.cfg.source_timeout): r=await self.client.post(self.urls[self.name],headers=h,json=b,timeout=self.cfg.source_timeout)
  if r.status_code>=400: raise SourceError(f"http_{r.status_code}",r.status_code==429 or r.status_code>=500)
  data=r.json(); out=[]; now=dt.datetime.now(dt.UTC)
  for x in data.get("results",[])[:self.cfg.source_results]:
   try:
    url=canonical_url(str(x.get("url",""))); title=compact(str(x.get("title","")))[:300]; text=compact(str(x.get("text") or x.get("raw_content") or x.get("content") or ""))[:6000]
    fp=hashlib.sha256((title+"\n"+text).encode()).hexdigest(); aid=hashlib.sha256((url+fp).encode()).hexdigest()[:32]
    out.append(Article(article_id=aid,url=url,title=title,text=text,source=urlsplit(url).hostname or self.name,provider=self.name,published_at=pub(x.get("publishedDate") or x.get("published_date")),fetched_at=now,fingerprint=fp))
   except (ValueError,TypeError): pass
  return out
class SourcePool:
 def __init__(self,sources,cfg): self.sources,self.cfg,self.errors=sources,cfg,[]
 async def collect(self,e,seen):
  async def one(q):
   for s in self.sources:
    for n in range(2):
     try:
      x=eligible(await s.search(q,e),e,seen)
      if x:return x
     except SourceError as ex:
      self.errors.append(f"{s.name}:{ex}")
      if not ex.retryable:break
     except Exception as ex:self.errors.append(f"{s.name}:{type(ex).__name__}")
     if n==0:await asyncio.sleep(1)
   return []
  batches=await asyncio.gather(*(one(q) for q in self.cfg.queries))
  return eligible([x for b in batches for x in b],e,seen)[:40]
def configured_sources(client,cfg):
 return SourcePool([SearchSource(n,os.getenv(f"{n.upper()}_API_KEY",""),client,cfg) for n in cfg.sources],cfg)
