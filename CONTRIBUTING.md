# Contributing to Frontier

Frontier is a NoneBot2/Milky bot with a large integration surface. Keep
changes small and preserve the platform-neutral boundary in
`utils/agent_protocol/`.

## Local setup

```bash
uv sync --locked --group dev
uv run playwright install
cp .env.example .env
cp env.toml.example env.toml
```

Do not commit `.env`, `env.toml`, `mcp.json`, `acp.json`, databases, caches, or
private chat data. The example files are the source of truth for configuration
shape.

## Before opening a pull request

Run the same checks as CI:

```bash
uv run --locked ruff format --check scripts/check_local_links.py
uv run --locked ruff check .
uv run --locked ty check utils/agent_context.py utils/harness_profiles.py utils/mcp.py \
  utils/agents/inputs.py utils/agents/execution.py utils/agents/runtime.py \
  utils/agents/runtime_gateway.py utils/delivery.py \
  plugins/dashboard/api/settings_routes.py
uv run --locked python scripts/check_local_links.py
uv run --locked pytest test/ -q
npm ci --prefix renderer
npm run build:check --prefix renderer
```

When changing the renderer, regenerate the checked-in assets and review the
resulting diff. When changing configuration or a message boundary, add a
focused regression test. Avoid broad formatting churn and do not include real
credentials in fixtures or logs.

## Change descriptions

Commit messages should state the affected area and the behavior change, for
example `fix(news): preserve a rejected draft for re-editing`. Pull requests
should explain why the change is needed, what it changes, and which checks
were run.
