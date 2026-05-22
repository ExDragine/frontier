# Domain Tool Subagents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the current all-tools main deep agent into focused domain subagents while keeping lightweight utility tools on the main agent.

**Architecture:** Add module-based tool grouping in `tools.__init__`, then construct domain subagents from those groups in `utils.subagents`. Wire `FrontierCognitive` to use `agent_tools.main_tools` and `get_domain_subagents()` without changing individual tool implementations.

**Tech Stack:** Python, LangChain `BaseTool`, DeepAgents subagent dictionaries, pytest, ruff.

---

## File Structure

- Modify `tools/__init__.py`
  - Add module-to-group mapping.
  - Add `main_tools` and `subagent_tools`.
  - Preserve existing `local_tools`, `web_tools`, `mcp_tools`, and `all_tools`.
- Modify `utils/subagents.py`
  - Add domain subagent factory helpers.
  - Keep `get_fact_check_subagent()`.
  - Add `get_domain_subagents()`.
- Modify `utils/agents.py`
  - Use `agent_tools.main_tools` for the main agent.
  - Use `get_domain_subagents()` for subagents.
- Modify `test/conftest.py`
  - Extend `tools.agent_tools` stub with `main_tools` and `subagent_tools`.
- Add or modify tests in `test/tools/basic_info_tools_test.py` and `test/utils/agents_test.py`.

## Tasks

### Task 1: Tool Grouping

- [ ] Write a failing test that loads `tools.__init__` with fake tool modules and asserts `main_tools` and `subagent_tools` contain the expected group assignments.
- [ ] Run the test and verify it fails because `main_tools` or `subagent_tools` is missing.
- [ ] Implement module-based grouping in `tools.__init__`.
- [ ] Run the grouping test and verify it passes.

### Task 2: Domain Subagents

- [ ] Write failing tests for `get_domain_subagents()` that assert the expected subagent names and grouped tool lists.
- [ ] Run the tests and verify they fail because `get_domain_subagents()` is missing.
- [ ] Implement domain subagent factory functions in `utils.subagents`.
- [ ] Extend the `tools.agent_tools` test stub.
- [ ] Run the subagent tests and verify they pass.

### Task 3: Main Agent Wiring

- [ ] Write a failing test that verifies `FrontierCognitive` uses `agent_tools.main_tools` and includes domain subagents.
- [ ] Run the test and verify it fails because `FrontierCognitive` still uses `agent_tools.all_tools` or the old single subagent list.
- [ ] Update `utils.agents` to import `get_domain_subagents()` and use `agent_tools.main_tools`.
- [ ] Run the main agent wiring test and verify it passes.

### Task 4: Verification

- [ ] Run `pytest test/tools/basic_info_tools_test.py test/utils/agents_test.py -v`.
- [ ] Run `pytest test/utils/agent_queue_test.py test/plugins/agent_image_memory_test.py -v`.
- [ ] Run `ruff check tools/__init__.py utils/subagents.py utils/agents.py test/conftest.py test/tools/basic_info_tools_test.py test/utils/agents_test.py`.
- [ ] Inspect `git diff -- tools/__init__.py utils/subagents.py utils/agents.py test/conftest.py test/tools/basic_info_tools_test.py test/utils/agents_test.py`.
