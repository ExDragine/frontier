# Domain Tool Subagents Design

## Goal

Move most local tools out of the main deep agent tool list and into domain-specific subagents. The main agent should make routing decisions, keep lightweight utility tools, and delegate specialized work to focused agents.

## Context

`tools.__init__` currently discovers all local LangChain tools and exposes them through `agent_tools.all_tools`. `FrontierCognitive` passes that complete list directly to `create_deep_agent`, while `utils.subagents` only defines a fact-checking subagent with web tools. This creates a large tool selection surface for every request.

## Domain Groups

The first split is module based and intentionally conservative:

- `research`: `arxiv`, `bilibili`, `wikipedia`, `tavily`
- `astro`: `aurora`, `comet`, `heavens_above`, `rocket`, `satellite`, `space_weather`
- `earth`: `earthquake`, `radar`, `weather`
- `main`: `adapter`, `calculator`, `reminder`, `paint`, `video`
- `memory`: `message_summary`
- `divination`: `iching`, `tarot`
- `external`: MCP tools whose runtime names are not known during local module discovery

The `adapter` tools stay on the main agent because they construct outgoing `UniMessage` artifacts. `paint` and `video` also stay on the main agent because they need direct access to the current multimodal message state (`image_inputs`, `video_inputs`, and image message parts), which subagent handoffs do not preserve reliably.

## Architecture

`tools.__init__` will own tool grouping. It will still expose `local_tools`, `web_tools`, `mcp_tools`, and `all_tools` for compatibility, and will add:

- `main_tools`
- `subagent_tools: dict[str, list[BaseTool]]`

`utils.subagents` will own subagent construction and prompts. It will expose a `get_domain_subagents()` function returning all configured domain subagents, including the existing fact-checking subagent and a constrained `general-purpose` override with no tools.

`FrontierCognitive` will pass `agent_tools.main_tools` to the main deep agent and `get_domain_subagents()` to `subagents`.

## Data Flow

1. Tool discovery imports each `tools/*.py` module.
2. Discovered tools are assigned to a group by module name.
3. `FrontierCognitive` receives only `main_tools`.
4. Domain subagents receive their grouped tool lists.
5. Clockwork keeps using `agent_tools.mcp_tools + agent_tools.web_tools`; that path is not changed.

## Error Handling

Unknown local tool modules default to `main` rather than being dropped. Unknown MCP tools go to `external`.

If a domain group has no tools in tests or partial environments, its subagent remains constructible with an empty list. This keeps unit tests stable and avoids import-time branching.

## Testing

Tests should verify:

- Module-based grouping assigns tools to the expected groups and preserves compatibility lists.
- `get_domain_subagents()` creates the expected subagent names and uses the grouped tools.
- `FrontierCognitive` passes `main_tools` to `create_deep_agent` and includes the domain subagents.
- Existing clockwork and agent tests still pass.
