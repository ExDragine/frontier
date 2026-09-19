# News plugin operations

The production path is now: Clockwork -> plugins.news.scheduler -> direct Exa/Tavily search -> evidence-bounded editor -> archive -> render -> per-target delivery.

## Configuration
Copy news.toml.example to news.toml when overrides are needed. Without it, the plugin reuses env.toml's daily_news model/provider. Search credentials are environment variables EXA_API_KEY and TAVILY_API_KEY.

## Delivery semantics
A report is archived before delivery. Each QQ group has its own state. sent is terminal; failed may be retried explicitly; a timed-out/in-flight delivery becomes unknown and is never automatically retried because the platform may already have accepted it.

## Operator commands
/news latest
/news status
/news preview
/news retry <group-id>

## Rollback
Point the daily_news task handler back to plugins.clockwork.task_handlers/daily_news only after reverting the compatibility wrapper. The new news.db is independent and may be retained for audit.
