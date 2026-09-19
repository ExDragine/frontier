"""Per-target QQ delivery. Ambiguous timeouts become unknown and are not auto-retried."""
import asyncio,time
from nonebot import get_bot
from nonebot_plugin_alconna import Target,UniMessage
async def deliver(repo,report,targets,cfg):
 await repo.stage_deliveries(report["id"],[str(x) for x in targets],time.time()+cfg.catchup_seconds)
 sent=[]
 for row in await repo.deliveries(report["id"]):
  if row["target"] not in {str(x) for x in targets}:continue
  token=await repo.claim_delivery(report["id"],row["target"],ttl=cfg.send_timeout+10,max_attempts=cfg.max_delivery_attempts)
  if not token:continue
  try:
   msg=UniMessage().image(raw=report["image"]) if report.get("image") else UniMessage.text(__import__("plugins.news.rendering",fromlist=["render_text"]).render_text(report))
   async with asyncio.timeout(cfg.send_timeout): result=await msg.send(target=Target.group(row["target"]),bot=get_bot(cfg.bot_id) if cfg.bot_id else None)
   receipt=str(getattr(result,"message_id",getattr(result,"message_seq",""))) or None
   await repo.finish_delivery(report["id"],row["target"],token,"sent",receipt=receipt);sent.append(int(row["target"]))
  except asyncio.TimeoutError:
   await asyncio.shield(repo.finish_delivery(report["id"],row["target"],token,"unknown",error="send_timeout"))
  except Exception as ex:
   await repo.finish_delivery(report["id"],row["target"],token,"failed",error=type(ex).__name__,retry_delay=cfg.retry_delay)
 return sent
