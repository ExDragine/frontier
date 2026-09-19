# News plugin operations

The production path is now: Clockwork -> plugins.news.scheduler -> direct Exa/Tavily search -> evidence-bounded editor -> archive -> render -> per-target delivery.

## Configuration
Copy news.toml.example to news.toml when overrides are needed. Without it, the plugin reuses env.toml's daily_news model/provider. Search credentials are environment variables EXA_API_KEY and TAVILY_API_KEY.

## Delivery semantics
A report is archived before delivery. Each QQ group has its own state. sent is terminal; failed may be retried explicitly; a timed-out/in-flight delivery becomes unknown and is never automatically retried because the platform may already have accepted it.

If sending succeeds but recording the receipt fails, the delivery remains in-flight and becomes unknown when its lease expires. It never becomes a retryable failure. `/news retry` only requeues existing failed targets; it does not create a first delivery to a new group. Clockwork records a failed result when any requested target lacks a confirmed sent state, preserving the actual send count and per-target summary. A previously sent edition succeeds without sending again.

## Recovery and retention
Search results are merged and deduplicated before deciding whether to consult the next provider, up to target_stories. Each provider/query makes at most two attempts on retryable failures.

max_generation_attempts (default 3) bounds editorial/verification attempts per generation invocation, including validation of a recovered draft. Content rejection clears the draft and permits re-editing; a transport failure preserves the draft for the next invocation. The overall generation_timeout still bounds the entire operation. Generation checkpoints retain the original lease deadline.

Before generation, retention_days (default 30) removes inactive archives and their delivery rows after that many days without updates. Active generation/delivery leases and recently updated deliveries are protected. Images and text show the archived edition time in Beijing time.

## Operator commands
/news latest
/news status
/news preview
/news retry <group-id>

## Rollback
Point the daily_news task handler back to plugins.clockwork.task_handlers/daily_news only after reverting the compatibility wrapper. The new news.db is independent and may be retained for audit.
