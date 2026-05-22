# SQLite Performance Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Frontier's SQLite-backed message, image-memory, dashboard, and clockwork task performance while staying compatible with the current SQLModel architecture.

**Architecture:** Centralize SQLite engine creation and connection initialization, add query-shaped indexes, instrument representative query plans, and introduce FTS5 only after baseline improvements are verified. SQLite 3.51.2 is treated as a patch release over 3.51.0, so the plan uses 3.51.0 features only when compile options prove they are enabled.

**Tech Stack:** Python 3.14, SQLModel, SQLAlchemy, SQLite 3.51.2, pytest, optional FTS5/carray/percentile compile-time extensions.

---

## Current Findings

- The hot table is `message`; normal request flow writes a user message, optionally writes `messageimage` rows, then reads recent conversation context.
- The main slow-path risks are `ORDER BY time DESC LIMIT N` after filtering by `group_id` or `user_id`, reply-check count/latest queries, `LIKE '%keyword%'` searches, image cleanup by `expires_at`, and task history ordering.
- The current live `frontier.db` is tiny, so performance work should be verified with synthetic data and `EXPLAIN QUERY PLAN`, not perceived latency.
- Current database pragmas observed from `frontier.db`: `journal_mode=delete`, `synchronous=FULL`, `cache_size=-2000`, `foreign_keys=0`, `wal_autocheckpoint=1000`.

## SQLite 3.51.x Feature Notes

- SQLite 3.51.2 is a stability release. It fixes a deadlock in broken POSIX lock detection and problems in the 3.51.0 EXISTS-to-JOIN optimization.
- SQLite 3.51.0 adds `jsonb_each()` and `jsonb_tree()`. These help only if the app stores and queries JSONB; Frontier currently builds message metadata at read time and does not need them in the first optimization pass.
- `carray` and `percentile` are now in the amalgamation, but both are disabled by default and require compile-time flags. They must be discovered with `PRAGMA compile_options` before use.
- 3.51.0 includes performance improvements for read transaction commits, empty-table joins, scalar subquery evaluation, and some window function queries. These are engine-level gains, not replacements for correct app indexes.
- `PRAGMA wal_checkpoint=NOOP` exists for WAL monitoring without checkpoint work. It is useful for diagnostics, not as the default checkpoint strategy.
- FTS5 is still the right feature for chat search; it is not new in 3.51.x, but the 3.51.1 patch fixed an `fts5vocab` issue exposed by new optimizer behavior.

## Files

- Modify: `utils/database.py` for shared engine creation, SQLite connection pragmas, schema/index bootstrap, and message query changes.
- Modify: `plugins/dashboard/db.py` to reuse the shared engine.
- Modify: `plugins/clockwork/__init__.py` to reuse the shared engine.
- Modify: `plugins/clockwork/task_manager.py` only if task-history indexes or metadata-query improvements require local schema bootstrap.
- Create: `test/utils/database_performance_test.py` for compile option checks, index existence checks, and query-plan regression tests.
- Optional later create: `utils/message_search.py` or a focused section in `utils/database.py` for FTS5 search, depending on implementation scope.

## Phase 1: Baseline And Capability Discovery

- [ ] Add a diagnostic helper that reports `sqlite_version()`, `PRAGMA compile_options`, `PRAGMA journal_mode`, `PRAGMA synchronous`, `PRAGMA foreign_keys`, `PRAGMA wal_autocheckpoint`, and `PRAGMA module_list`.
- [ ] Verify whether the runtime has `ENABLE_FTS5`, `ENABLE_CARRAY`, and `ENABLE_PERCENTILE`.
- [ ] Add synthetic benchmark fixtures with at least 100k `message` rows across multiple `group_id` and `user_id` values.
- [ ] Capture `EXPLAIN QUERY PLAN` for:
  - Recent group context: `WHERE group_id = ? AND time < ? ORDER BY time DESC LIMIT ?`
  - Recent private context: `WHERE user_id = ? AND group_id IS NULL AND time < ? ORDER BY time DESC LIMIT ?`
  - Reply check count: `WHERE group_id = ? AND time >= ?`
  - Latest assistant reply: `WHERE group_id = ? AND role = ? ORDER BY time DESC LIMIT 1`
  - Quoted message lookup: `WHERE group_id = ? AND msg_id = ? ORDER BY time DESC LIMIT 1`
  - Image cleanup: `WHERE expires_at < ?`
  - Task history: `WHERE job_id = ? ORDER BY execution_time DESC LIMIT ?`

## Phase 2: Shared Engine And Pragmas

- [ ] Add a single `get_engine()` function in `utils/database.py`.
- [ ] Configure SQLAlchemy connection events to run:
  - `PRAGMA foreign_keys=ON`
  - `PRAGMA busy_timeout=5000`
  - `PRAGMA journal_mode=WAL`
  - `PRAGMA synchronous=NORMAL`
  - `PRAGMA temp_store=MEMORY`
  - `PRAGMA optimize=0x10002` on long-lived connection startup
- [ ] Keep `wal_autocheckpoint=1000` initially; only tune after WAL file growth is observed.
- [ ] Use the shared engine from dashboard and clockwork instead of creating independent default engines.
- [ ] Add a shutdown or periodic maintenance hook that runs `PRAGMA optimize`.

## Phase 3: Query-Shaped Indexes

- [ ] Add idempotent index bootstrap using `CREATE INDEX IF NOT EXISTS`.
- [ ] Add message indexes:
  - `ix_message_group_time ON message(group_id, time DESC)`
  - `ix_message_user_group_time ON message(user_id, group_id, time DESC)`
  - `ix_message_group_role_time ON message(group_id, role, time DESC)`
  - `ix_message_group_msg_id_time ON message(group_id, msg_id, time DESC)`
  - Optional private partial index: `ix_message_private_user_time ON message(user_id, time DESC) WHERE group_id IS NULL`
- [ ] Add image indexes:
  - `ix_messageimage_msg_time_index ON messageimage(msg_time, "index")`
  - `ix_messageimage_expires_at ON messageimage(expires_at)`
  - Optional unique index: `ux_messageimage_msg_time_index ON messageimage(msg_time, "index")`
- [ ] Add task indexes:
  - `ix_taskhistory_job_time ON taskexecutionhistory(job_id, execution_time DESC)`
  - `ix_taskhistory_status_time ON taskexecutionhistory(status, execution_time DESC)` if status filtering is common.
- [ ] Run `PRAGMA optimize` immediately after index creation.

## Phase 4: Query And Write-Path Refinement

- [ ] Fix truthiness filters in message selection so `group_id=0` or `user_id=0` cannot accidentally skip indexed branches; use `is not None`.
- [ ] Keep recent-context reads in descending index order and reverse in Python only after fetching the limited result set.
- [ ] Replace image insert's per-image preselect with a unique index plus upsert if SQLite/SQLAlchemy support is clean in this environment.
- [ ] Batch image metadata inserts in one transaction; keep file writes outside or before DB transaction rollback-sensitive sections.
- [ ] Consider merging reply-check `count_group_messages_since` and `latest_group_role_message_time` into one small method only if profiling shows two round trips matter.
- [ ] Move heavy cleanup and long search operations away from request-critical message handling.

## Phase 5: FTS5 Chat Search

- [ ] Enable only if `PRAGMA compile_options` or a smoke query confirms FTS5 is available.
- [ ] Create an external-content FTS5 table for `message(content)` with unindexed metadata columns for `time`, `group_id`, `user_id`, `role`, and `user_name`.
- [ ] For Chinese-heavy chat, prefer `tokenize='trigram'` for substring-like search; accept larger index size. For English-heavy content, `unicode61` is smaller.
- [ ] Backfill FTS rows from existing `message` rows.
- [ ] Maintain FTS with triggers or explicit writes in `MessageDatabase.insert`.
- [ ] Route `search_messages(content_query=...)` through FTS5 when available; fall back to current `LIKE` when unavailable.
- [ ] Add tests proving search result ordering and permission scoping match current behavior.

## Phase 6: Optional 3.51.x Extensions

- [ ] Use `percentile` only if `ENABLE_PERCENTILE` is present and dashboard/statistics need p50/p95 task duration or message latency metrics.
- [ ] Do not use `carray` from Python unless the binding exposes `sqlite3_carray_bind()` or a vetted adapter is added; normal SQLAlchemy expanding parameters are simpler.
- [ ] Defer `jsonb_each()` and `jsonb_tree()` until the app stores queryable JSONB fields. They are not useful for current message metadata because metadata is generated in Python at read time.
- [ ] Use `PRAGMA wal_checkpoint=NOOP` for diagnostics to inspect WAL state without performing checkpoint work.

## Phase 7: Verification

- [ ] Run `pytest test/utils/database_test.py -q`.
- [ ] Run new performance-plan tests in `test/utils/database_performance_test.py`.
- [ ] Run dashboard/clockwork tests that touch shared engines:
  - `pytest test/plugins/dashboard_routes_test.py test/plugins/clockwork_test.py -q`
- [ ] Compare before/after `EXPLAIN QUERY PLAN`; expected plans should use the new composite indexes and avoid temp B-trees for hot `ORDER BY` queries.
- [ ] Smoke test startup against a copy of `frontier.db`.
- [ ] Confirm WAL creates `frontier.db-wal` and `frontier.db-shm`, and that shutdown/checkpoint behavior does not leave unbounded WAL growth.

## Rollback Plan

- [ ] Keep all schema changes idempotent.
- [ ] If WAL causes deployment issues, switch back with `PRAGMA journal_mode=DELETE`.
- [ ] If an added index causes write amplification without read benefit, drop that specific index after comparing query plans.
- [ ] If FTS5 increases database size too much, disable FTS routing and drop the FTS virtual table plus triggers.
