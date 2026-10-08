# Changelog

## Unreleased

- Updated the official model catalog to the October 8, 2026 snapshot with 18 new
  model cards, refreshed LobeHub display names, corrected DeepSeek token limits,
  and recorded the Intern-S2 and MiMo V2.5 lifecycle transitions.
- Removed QQ private and group progress messages (also for `/acp` tasks), including thinking, tool
  calls, subagent activity and assistant preambles, plus the group status
  classifier and its background task. Final replies, artifacts and failure
  notices retain their existing delivery behavior; ACP progress remains
  available through the optional runtime reporter.
- Added repository maintenance documentation and a local Markdown-link check.
- CI now checks Python formatting, local documentation links, and the bundled
  Markdown renderer in addition to lint, type, and test checks.
- Removed an unused callback payload from the usage accounting path while
  retaining the callback protocol required by LangChain.
- Cleared the Ruff import warning in `utils/agents/tool_errors.py` and removed
  the test and stub references left behind by the rubric/quickjs removal
  (`test/utils/agents_test.py`, `test/utils/configs_test.py`,
  `test/integration/agent_controls_test.py`, `test/stubs/install.py`).
- Made the suite portable on Windows: the attachment cache assertion in
  `test/utils/database_test.py` no longer depends on POSIX path separators, and
  the session rotation contract test no longer assumes Linux-only `/proc`.
- Aligned the documentation with the current code: the eight loaded plugins
  (including `plugins/news` and `plugins/wolfx`), the platform-neutral QQ path
  through `ConversationOrchestrator` and `FrontierAgentCore`, the real
  middleware chain, group and private final replies, media persistence
  through `insert_media`, and the `models/` catalog.
- Hardened Dashboard authentication: passwords are no longer compared as
  plaintext, a plaintext `[dashboard].password` is derived to a bcrypt hash in
  memory with a one-time warning, and bcrypt's 72-byte input limit is enforced.
- Restricted `/model` and `/acp` to superusers, and removed unused imports and
  three dead helpers from the QQ handler module.
- Finished the QQ handler cleanup: the dead `_execute_legacy_agent_request()`
  path and its three exclusive helpers are gone.
- Split the 2179-line `utils/database.py` into the `utils/database/` package
  (`engine`, `models`, `schema`, `fts`, `maintenance`, `rows`, `attachments`,
  `search`, `store`, `settings`, `events`). The largest module is now under 600
  lines; `import utils.database` and every previous public name resolve through
  the package facade.
- Plugin package entries register nothing on plain import: `clockwork`,
  `dashboard`, `playground` and `wolfx` install their matchers and lifecycle
  hooks only when NoneBot loads them, matching the existing `agent`, `acp`,
  `news` and `toolbox` guard.
- Dashboard front-end assets are local-first: `index.html` prefers the pinned
  files under `plugins/dashboard/web/vendor/` and otherwise falls back to the
  same pinned CDN versions, and `scripts/vendor_dashboard_assets.py` fetches
  them in one command.
- Removed the leftover PTC tool channel: `tools/__init__.py` no longer splits
  direct from PTC tools and `FrontierCognitive` keeps a single direct snapshot,
  so the one-shot read-only tools (`weather`, `earthquake`, `radar`, `iching`,
  `tarot`, `deepseek_balance`, the `milky_*` getters and the `scheduled_task`
  listings) are visible to the main Agent again instead of being dropped.
- The orchestrator, the `AgentCore` port and the runtime gateway support an
  optional progress reporter. QQ turns use the plain request/response shape;
  consumers that require streaming progress can still supply a reporter.
- Pruned dead code, dead configuration and compatibility shims across the
  repository (net −2.3k lines): removed the `StoredMessage` and
  `MessagePartType` aliases, `GateDecision.allowed`, `HistoryQuery.after` plus
  its two dead adapter filters, `TurnOutcome.delivered`, the leftovers in
  `neutral_core` (`_parts_text`, `_response_text`), the test-only
  `ModelMediaMiddleware`, `utils/ens_gate._ens_caller_allowed`, the clockwork
  `reminder_handler` module and `github_post_news` handler, the news
  `Verification` model and three unused delivery columns, the dashboard
  "memory" card that read a field the API never returned, and the
  `insert_images` fallback branch in the QQ handler. `EnvConfig.TEST_GROUP_ID`
  stays: it has no reader, but the configuration model forbids extra inputs, so
  dropping the field would stop existing `env.toml` files from loading.
- `utils/database/__init__.py` is now a plain 21-name re-export facade: the
  module-subclass `__setattr__` forwarding shim is gone and the single test
  that relied on package-wide monkeypatching patches the owning submodule.
- `_run_qq_neutral()` returns a single bool (the old `handled` flag was always
  True), `_qq_neutral_eligible()` lost its unused parameter, and QQ artifact
  delivery reuses the adapter's `send_qq_artifacts` instead of a second
  converter in the handler. `run_serialized()` accepts factories only, so the
  coroutine-disposal branch is gone.
- Shared helpers replace duplicated implementations: `utils/command_text.py`
  (command-prefix stripping, three call sites), `utils/timeutil.py`
  (`SHANGHAI` plus `add_daily_job`, used by the ACP lifecycle and the QQ daily
  cache cleanup), `utils/ens_common.py` (ENS wait, formatting, capture options
  and URL builders), `tools/_nrc_common.py` (NRC headers, templates, DANZU
  tables, CSS loading) and a single browser runtime behind `browser_capture`
  and `markdown_render`.
- The `radar` area table and the four `ens_normal` lookup tables moved to
  `data/radar_areas.json` and `data/ens/*.json`; `tools/iching.py` keeps only
  its three tools, with the reader in `tools/_iching_reader.py`.
- The suite dropped self-asserting cases, parametrised isomorphic ones and
  shares plugin/tool doubles through `test/plugins/conftest.py` and
  `test/tools/conftest.py`. `test/conftest.py` now ignores temp-database
  cleanup errors, so a Windows run needs no external plugin.
- `test/utils/agent_execution_test.py` no longer depends on module import
  order: its revision-rebuild case patched the configuration class object that
  the session-scoped reload had already replaced, so it only passed when
  another module imported the Agent graph first.

Earlier implementation notes live in `docs/` and are retained as design
history. They are not a promise that every historical experiment remains
enabled in the current runtime.
