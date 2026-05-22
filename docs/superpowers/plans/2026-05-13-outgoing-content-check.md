# Outgoing Content Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Default startup to the Hugging Face mirror and block unsafe model-generated chat text before it is sent.

**Architecture:** Reuse the existing content-check detector instances in `utils.message`. Keep all output moderation as a send-time guard in `plugins/agent/__init__.py`, covering both quick `pre_response` text and final agent responses.

**Tech Stack:** Python, NoneBot matcher tests with `nonebug`, pytest, shell startup script.

---

## File Structure

- Modify `run.sh`: export `HF_ENDPOINT` with a default mirror value before `uv sync` or `nb run`.
- Modify `run.ps1`: set the same default without overwriting an explicit caller value.
- Modify `Dockerfile`: set the same default for container startup.
- Modify `utils/message.py`: add output text sanitization helpers and reuse send-message content extraction.
- Modify `plugins/agent/__init__.py`: sanitize `choice.pre_response` and final response messages before sending and storing.
- Modify `test/utils/message_test.py`: add output sanitizer unit tests.
- Modify `test/plugins/agent_image_memory_test.py`: add integration tests for short reply and final response output sanitization.
- Create `test/run_script_test.py`: verify startup scripts set `HF_ENDPOINT`.

### Task 1: Add Failing Tests

- [ ] Add `test_sanitize_outgoing_text_blocks_unsafe_output` and `test_sanitize_outgoing_text_allows_controversial_output` in `test/utils/message_test.py`.
- [ ] Add `test_agent_choice_short_reply_sanitizes_unsafe_output` and `test_process_agent_request_sanitizes_final_response` in `test/plugins/agent_image_memory_test.py`.
- [ ] Add `test_run_sh_sets_default_hf_endpoint_before_startup_work` and `test_run_ps1_sets_default_hf_endpoint_without_overwriting_existing_value` in `test/run_script_test.py`.
- [ ] Run the focused tests and confirm they fail because the sanitizer and startup export are not implemented yet.

### Task 2: Implement Output Sanitizer

- [ ] Add `OUTPUT_RISK_BLOCKED_MESSAGE` to `utils/message.py`.
- [ ] Extract the existing `send_messages()` raw-message text parsing into `outgoing_message_content(raw)`.
- [ ] Add `sanitize_outgoing_text(content)` that checks only text output and replaces `Unsafe` with the fixed notice.
- [ ] Add `sanitize_outgoing_message(raw)` that returns either the original raw message or a replacement text message carrying the block notice.
- [ ] Update `send_messages()` to use `outgoing_message_content(raw)`.

### Task 3: Wire Send-Time Checks

- [ ] Import `sanitize_outgoing_message` and `sanitize_outgoing_text` in `plugins/agent/__init__.py`.
- [ ] Sanitize `response["messages"][-1]` before assistant insert and `send_messages()`.
- [ ] Sanitize `choice.pre_response` before `UniMessage.text(...).send()` and assistant insert.

### Task 4: Startup Environment

- [ ] Add `export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"` near the top of `run.sh`.
- [ ] Change `run.ps1` to set `$env:HF_ENDPOINT` only when it is unset.
- [ ] Add `ENV HF_ENDPOINT="https://hf-mirror.com"` to `Dockerfile`.

### Task 5: Verify

- [ ] Run the focused tests.
- [ ] Run related message and agent tests.
- [ ] Run formatting/lint checks if available.
