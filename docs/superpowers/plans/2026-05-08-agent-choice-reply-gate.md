# AgentChoice Reply Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `AgentChoice` into a reply gate and pass configured agent capability directly to the main agent.

**Architecture:** Keep the existing message gateway and queue behavior. `handle_common()` performs a pre-queue AgentChoice reply classification after `message_gateway()`, and `_process_agent_request()` invokes `chat_agent()` with `EnvConfig.AGENT_CAPABILITY`.

**Tech Stack:** Python, NoneBot matcher tests with `nonebug`, Pydantic structured responses, pytest.

---

## File Structure

- Modify `plugins/agent/__init__.py`: replace `AgentChoice.agent_capability` with `AgentChoice.should_reply`; add a pre-queue reply gate; pass configured capability directly in `_process_agent_request()`.
- Modify `prompts/agent_choice.md`: replace model capability router prompt with no-reply/continue classifier prompt.
- Modify `test/plugins/agent_image_memory_test.py`: add regression tests for capability passthrough and no-reply finish behavior.
- Modify `env.toml.example`: remove `auto` from the documented capability values.

### Task 1: Add Regression Tests

**Files:**
- Test: `test/plugins/agent_image_memory_test.py`

- [ ] **Step 1: Write failing tests**

Add two async tests:

```python
@pytest.mark.asyncio
async def test_agent_choice_false_finishes_before_queue(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    calls = {"queue": 0}

    class DummyQueue:
        async def submit(self, *_args, **_kwargs):
            calls["queue"] += 1

    class DummyMessagesDb:
        async def insert(self, **_kwargs):
            return None

        async def insert_images(self, **_kwargs):
            return []

        async def prepare_message(self, *_args, **_kwargs):
            return [{"role": "assistant", "content": "{'content': '前一个问题已经回答完毕'}"}]

    async def fake_assistant_agent(*_args, **_kwargs):
        return agent.AgentChoice(should_reply=False)

    monkeypatch.setattr(agent, "agent_queue", DummyQueue())
    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "assistant_agent", fake_assistant_agent)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")

    # Build a normal NoneBot MessageEvent, then assert ctx.should_finished().

    assert calls["queue"] == 0
```

```python
@pytest.mark.asyncio
async def test_process_agent_request_passes_configured_capability_directly(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    captured = {}

    class DummyMessagesDb:
        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def insert(self, **_kwargs):
            return None

    class DummyCognitive:
        async def chat_agent(self, *_args, **kwargs):
            captured["capability"] = _args[3]
            return {"response": {"messages": [types.SimpleNamespace(text="ok")]}, "uni_messages": []}

    async def fake_assistant_agent(*_args, **_kwargs):
        raise AssertionError("AgentChoice should not select the reasoning capability")

    monkeypatch.setattr(agent, "messages_db", DummyMessagesDb())
    monkeypatch.setattr(agent, "f_cognitive", DummyCognitive())
    monkeypatch.setattr(agent, "assistant_agent", fake_assistant_agent)
    monkeypatch.setattr(agent, "send_messages", _noop)
    monkeypatch.setattr(agent, "send_artifacts", _noop)
    monkeypatch.setattr(agent.EnvConfig, "AGENT_CAPABILITY", "high")

    context = agent.AgentRequestContext(
        bot=None,
        event=types.SimpleNamespace(self_id="1"),
        user_id="456",
        user_name="Bob",
        event_id=1,
        group_id=123,
        msg_time=1000,
        text="继续解释一下",
        quoted_images=[],
        images=[],
        videos=[],
    )

    await agent._process_agent_request(context)

    assert captured["capability"] == "high"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest test/plugins/agent_image_memory_test.py::test_process_agent_request_passes_configured_capability_directly test/plugins/agent_image_memory_test.py::test_agent_choice_false_finishes_before_queue -v
```

Expected: tests fail because `AgentChoice` does not accept `should_reply` yet and the matcher does not have a pre-queue no-reply finish path.

### Task 2: Implement Reply Gate

**Files:**
- Modify: `plugins/agent/__init__.py`
- Modify: `prompts/agent_choice.md`

- [ ] **Step 1: Update `AgentChoice` schema**

Change the model to:

```python
class AgentChoice(BaseModel):
    should_reply: bool = Field(
        description=(
            "Whether the assistant should continue the conversation. "
            "False when the latest user input is only evaluation, acknowledgement, or useless statement "
            "after the previous issue has been resolved."
        )
    )
```

- [ ] **Step 2: Update `_process_agent_request()`**

Replace the capability-routing branch with:

```python
    capability = EnvConfig.AGENT_CAPABILITY
```

- [ ] **Step 3: Add pre-queue reply gate in `handle_common()`**

Create the `AgentRequestContext`, call `_agent_choice_should_reply(context, messages)`, and run `await common.finish()` when the result is false before calling `agent_queue.submit()`.

- [ ] **Step 4: Update `prompts/agent_choice.md`**

Use a plain text transcript as classifier input and a strict JSON response schema:

```json
{"should_reply": true}
```

and explicit false criteria for already-finished conversations followed by evaluation, acknowledgement, or useless statements.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest test/plugins/agent_image_memory_test.py::test_process_agent_request_passes_configured_capability_directly test/plugins/agent_image_memory_test.py::test_agent_choice_false_finishes_before_queue -v
```

Expected: both tests pass.

### Task 3: Regression Verification

**Files:**
- Test: `test/plugins/agent_image_memory_test.py`

- [ ] **Step 1: Run the full agent plugin test file**

Run:

```bash
python -m pytest test/plugins/agent_image_memory_test.py -v
```

Expected: all tests in the file pass.

- [ ] **Step 2: Inspect diff**

Run:

```bash
git diff -- plugins/agent/__init__.py prompts/agent_choice.md test/plugins/agent_image_memory_test.py docs/superpowers/specs/2026-05-08-agent-choice-reply-gate-design.md docs/superpowers/plans/2026-05-08-agent-choice-reply-gate.md
```

Expected: diff is limited to the reply-gate change, prompt update, tests, and docs.
