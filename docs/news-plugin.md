# News plugin operations

The production path is:

Clockwork -> `plugins.news.scheduler` -> research Agent -> DeepSeek Search/Fetch tools -> evidence validation -> `news.db` archive -> render -> per-target delivery.

The research Agent owns search planning and source selection. It receives only the configured edition window, calls `deepseek_web_search` first, fetches important pages with `deepseek_web_fetch`, and returns structured stories whose evidence points to the original source URL. The scheduler still keeps the durable archive, image rendering, per-group delivery state, and explicit retry behavior from the standalone pipeline.

## Configuration

Copy `news.toml.example` to `news.toml` when overrides are needed. If `model` and `provider` are empty, the plugin reuses `env.toml`'s `daily_news_model` and `daily_news_model_provider`. The Agent's search tools use the independent `[search]` configuration and its provider API key; they do not depend on Exa MCP or the main model's built-in `web_search`.

`workspace_dir` is used for bounded DeepSeek page previews and must point to a writable Frontier workspace. Search and fetch failures are returned as errors and are not treated as an empty evidence set. Results outside the edition window or without a usable date are excluded before the report is archived.

## Delivery semantics

A report is archived before delivery. Each QQ group has its own state. `sent` is terminal; `failed` may be retried explicitly. A previously sent edition is reused without sending it again. Clockwork records a failed task result when any requested target lacks a confirmed `sent` state.

## Recovery and retention

The generation lease and `generation_timeout` cover research and all editing attempts. Each source article may support only one story across both sections, including supplementary citations. If an Agent draft repeats a source, contains invalid evidence, or has too few supported stories, the editor receives the validation error and reuses the collected, dated evidence to produce a corrected draft. `max_generation_attempts` bounds the total number of drafts, including the initial Agent draft; it does not rerun searches on each editing attempt. Valid drafts are archived immediately. Too few dated sources, an exhausted draft budget, or a timeout marks the report failed, and the next invocation may recollect. Retention removes inactive reports and delivery rows after `retention_days`.

## Operator commands

```
/news latest
/news status
/news preview
/news retry <group-id>
```

The `/news preview` command uses a separate preview archive and does not deliver to subscribed groups.
