# Changelog

## Unreleased

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
  middleware chain, group and private progress messages, media persistence
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
- Wire QQ progress messages back through the neutral boundary: the
  orchestrator, the `AgentCore` port and `AgentRuntimeRequest` now carry an
  optional progress reporter, so private `assistant_preamble`, thinking and
  tool-call messages plus the single group status message are emitted again.
  Callers that pass no reporter keep the plain request/response shape.

Earlier implementation notes live in `docs/` and are retained as design
history. They are not a promise that every historical experiment remains
enabled in the current runtime.
