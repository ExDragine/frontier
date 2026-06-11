# Agent 流式进度事件 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `chat_agent()` 从 `ainvoke` 迁移到 `astream_events(v3)`，让私聊用户在执行期间看到 Agent 进度（思考中、调用工具、启动子代理）。

**Architecture:** 在 `chat_agent()` 内部新增 `_collect_progress()` 消费 `astream_events` v3 的三个 projection（messages / tool_calls / subagents），生成 `ProgressEvent` 并通过可选回调 `progress_reporter` 推送给调用方。`stream.output` 路径保持不变，后处理逻辑零改动。

**Tech Stack:** LangChain Deep Agents `astream_events(v3)`, asyncio.create_task, Python dataclass

**Spec:** `docs/superpowers/specs/2026-06-11-agent-streaming-progress-design.md`

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `utils/agents.py` | ProgressEvent 类型、`_collect_progress`、`_collect_output`、`chat_agent()` 改造 |
| `plugins/agent/__init__.py` | 私聊 reporter 实现、透传 `progress_reporter` 参数 |
| `test/utils/agents_test.py` | 单元测试 |

所有逻辑集中在现有文件内，不新增文件。

---

### Task 1: 定义 ProgressEvent 类型和 ProgressReporter 别名

**Files:**
- Modify: `utils/agents.py:8`（imports 区域）
- Modify: `utils/agents.py:31`（在 `UniMessage = None` 之后插入）

- [ ] **Step 1: 更新 imports**

将 `utils/agents.py` 第 8 行：
```python
from typing import Any
```

替换为：
```python
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal
```

- [ ] **Step 2: 在 `UniMessage = None` 之后插入 ProgressEvent 和类型别名**

在 `utils/agents.py` 第 31 行 `UniMessage = None` 之后，`VISION_OMITTED_NOTICE = "..."` 之前插入：

```python
ProgressReporter = Callable[["ProgressEvent"], Awaitable[None]]


@dataclass
class ProgressEvent:
    """agent 执行过程中的用户可读进度事件。

    reporter 层根据 type 决定是否向用户展示。当前私聊 reporter 消费
    thinking / subagent_start / tool_call，其余类型预留。
    """

    type: Literal[
        "thinking",  # Agent 开始思考（stream.messages 首个 LLM 消息）
        "tool_call",  # 工具开始执行（stream.tool_calls 新条目）
        "tool_result",  # 工具执行完成（预留）
        "subagent_start",  # 子代理启动（stream.subagents 新条目）
        "subagent_done",  # 子代理完成（预留）
        "text_delta",  # 段落级文本增量（预留，markdown 结构不能拆）
        "done",  # 执行完成或出错（预留）
    ]
    message: str  # 用户可读的中文描述
    detail: dict[str, Any] | None = None  # 结构化附加信息
```

- [ ] **Step 3: 验证语法**

```bash
python -c "from utils.agents import ProgressEvent, ProgressReporter; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add utils/agents.py
git commit -m "feat: add ProgressEvent type and ProgressReporter alias"
```

---

### Task 2: 实现 _emit 和 _collect_progress

**Files:**
- Modify: `utils/agents.py`（在 `CustomAgentState` 类附近插入两个独立函数）

- [ ] **Step 1: 在 `_parse_structured_response_from_messages` 之后插入 `_emit`**

在 `utils/agents.py` 的 `_parse_structured_response_from_messages` 函数结束（约第 136 行，该函数的 `raise KeyError(...)` 之后空行处）插入：

```python
async def _emit_progress(reporter: ProgressReporter | None, event: ProgressEvent) -> None:
    """安全调用 reporter —— reporter 自身异常不中断 agent 执行。"""
    if reporter is None:
        return
    try:
        await reporter(event)
    except Exception as e:
        logger.warning(f"Progress reporter 调用失败: {type(e).__name__}: {e}")
```

- [ ] **Step 2: 插入 `_collect_progress` 函数**

紧跟 `_emit_progress` 之后插入：

```python
async def _collect_progress(stream, reporter: ProgressReporter | None) -> None:
    """消费 astream_events v3 的三个 projection，生成 ProgressEvent。

    独立任务运行，异常不传播到 output 收集路径。
    每个 projection consumer 有独立的 try/except 保护。
    """
    if reporter is None:
        return

    async def consume_subagents() -> None:
        async for subagent in stream.subagents:
            await _emit_progress(
                reporter,
                ProgressEvent(
                    type="subagent_start",
                    message=f"{subagent.name} 已启动",
                    detail={"name": subagent.name},
                ),
            )

    async def consume_tool_calls() -> None:
        async for tool_call in stream.tool_calls:
            await _emit_progress(
                reporter,
                ProgressEvent(
                    type="tool_call",
                    message=f"正在调用工具：{tool_call.tool_name}",
                    detail={"tool_name": tool_call.tool_name},
                ),
            )

    async def consume_messages() -> None:
        first_message = True
        text_buffer: str = ""
        async for message in stream.messages:
            if first_message:
                await _emit_progress(
                    reporter,
                    ProgressEvent(type="thinking", message="正在思考…"),
                )
                first_message = False
            # text_delta 累积并按段落切分（代码保留，reporter 层暂不消费）
            async for chunk in message.text:
                text_buffer += chunk
                while "\n\n" in text_buffer:
                    idx = text_buffer.index("\n\n")
                    paragraph = text_buffer[:idx].strip()
                    text_buffer = text_buffer[idx + 2:]
                    if paragraph:
                        await _emit_progress(
                            reporter,
                            ProgressEvent(type="text_delta", message=paragraph),
                        )

    async def _safe(coro) -> None:
        try:
            await coro
        except Exception as e:
            logger.warning(f"Progress collector 异常: {type(e).__name__}: {e}")

    await asyncio.gather(
        _safe(consume_subagents()),
        _safe(consume_tool_calls()),
        _safe(consume_messages()),
    )
```

- [ ] **Step 3: 验证语法**

```bash
python -c "from utils.agents import _collect_progress, _emit_progress; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add utils/agents.py
git commit -m "feat: implement _collect_progress and _emit_progress for stream event consumption"
```

---

### Task 3: 改造 chat_agent() 使用 astream_events

**Files:**
- Modify: `utils/agents.py:360-488`（`chat_agent` 方法签名 + 执行部分）

- [ ] **Step 1: 修改方法签名，增加 `progress_reporter` 参数**

将 `utils/agents.py` 第 360 行：
```python
    async def chat_agent(
        self,
        messages,
        user_id,
        user_name,
        capability: str = "none",
        group_id: int | None = None,
        image_inputs: list[bytes] | None = None,
        video_inputs: list[bytes] | None = None,
        thread_id_override: uuid.UUID | str | None = None,
        wake_word: str | None = None,
        group_member_role: str | None = None,
    ):
```

替换为：
```python
    async def chat_agent(
        self,
        messages,
        user_id,
        user_name,
        capability: str = "none",
        group_id: int | None = None,
        image_inputs: list[bytes] | None = None,
        video_inputs: list[bytes] | None = None,
        thread_id_override: uuid.UUID | str | None = None,
        wake_word: str | None = None,
        group_member_role: str | None = None,
        progress_reporter: ProgressReporter | None = None,
    ):
```

- [ ] **Step 2: 替换 ainvoke 为 astream_events + 双路消费**

将 `utils/agents.py` 第 461-464 行：
```python
            response = await agent.ainvoke(
                input=input_data,
                config=config,
            )
```

替换为：
```python
            stream = await agent.astream_events(
                input_data,
                config=config,
                version="v3",
            )
            progress_task = asyncio.create_task(
                _collect_progress(stream, progress_reporter)
            )
            response = await stream.output
            await progress_task
```

> **注意**：`astream_events` 的参数名在 deepagents 中可能是 `input` 而非 `input_data`。如果语法验证报错 `unexpected keyword argument 'input_data'`，改为 `input=input_data`。先按当前位置参数 `input_data` 编写，由验证步骤确认。

- [ ] **Step 3: 验证语法**

```bash
python -c "import ast; ast.parse(open('utils/agents.py').read()); print('Syntax OK')"
```

- [ ] **Step 4: 运行现有测试确保不破坏向后兼容**

```bash
python -m pytest test/utils/agents_test.py -x -q
```

预期：所有现有测试通过（`chat_agent` 测试不传 `progress_reporter`，行为与之前完全一致）。

- [ ] **Step 5: Commit**

```bash
git add utils/agents.py
git commit -m "feat: migrate chat_agent from ainvoke to astream_events v3"
```

---

### Task 4: 在 plugin 层实现私聊 reporter

**Files:**
- Modify: `plugins/agent/__init__.py:17`（imports）
- Modify: `plugins/agent/__init__.py:128-138`（`_process_agent_request` 中调用 `chat_agent` 的部分）

- [ ] **Step 1: 添加 import**

在 `plugins/agent/__init__.py` 第 17 行：
```python
from utils.agents import FrontierCognitive, _agent_thread_id, run_serialized
```

替换为：
```python
from utils.agents import FrontierCognitive, ProgressEvent, _agent_thread_id, run_serialized
```

- [ ] **Step 2: 在 `_process_agent_request` 函数之前插入私聊 reporter**

在 `plugins/agent/__init__.py` 的 `_group_member_role` 函数之后（约第 79 行），`_process_agent_request` 函数之前插入：

```python
async def _private_chat_reporter(event: ProgressEvent) -> None:
    """私聊场景的进度事件消费者 —— 向用户发送当前 Agent 正在做什么。

    消费的事件：
    - thinking → "🤔 正在思考…"
    - subagent_start → "🔍 {name} 已启动"
    - tool_call → "🔧 正在调用工具：{tool_name}"

    静默的事件（理由）：
    - subagent_done / tool_result → 避免冗余和内部数据泄露
    - text_delta → markdown 有结构，拆开发送会破坏格式
    - done → 最终结果由现有 send_messages 流程处理
    """
    match event.type:
        case "thinking":
            await UniMessage.text("🤔 正在思考…").send()
        case "subagent_start":
            await UniMessage.text(f"🔍 {event.message}").send()
        case "tool_call":
            await UniMessage.text(f"🔧 {event.message}").send()
        case "subagent_done" | "tool_result" | "text_delta" | "done":
            pass
```

- [ ] **Step 3: 在调用 chat_agent 时传入 reporter**

在 `plugins/agent/__init__.py` 的 `_process_agent_request` 中（约第 128 行），修改 `chat_agent` 调用：

当前代码：
```python
    result = await f_cognitive.chat_agent(
        messages,
        context.user_id,
        context.user_name,
        capability,
        group_id=context.group_id,
        image_inputs=context.quoted_images + context.images,
        video_inputs=context.videos,
        wake_word=triggered_wake or None,
        group_member_role=_group_member_role(context.event),
    )
```

替换为：
```python
    result = await f_cognitive.chat_agent(
        messages,
        context.user_id,
        context.user_name,
        capability,
        group_id=context.group_id,
        image_inputs=context.quoted_images + context.images,
        video_inputs=context.videos,
        wake_word=triggered_wake or None,
        group_member_role=_group_member_role(context.event),
        progress_reporter=_private_chat_reporter if context.group_id is None else None,
    )
```

- [ ] **Step 4: 验证语法**

```bash
python -c "import ast; ast.parse(open('plugins/agent/__init__.py').read()); print('Syntax OK')"
```

- [ ] **Step 5: Commit**

```bash
git add plugins/agent/__init__.py
git commit -m "feat: add private chat progress reporter, wire into _process_agent_request"
```

---

### Task 5: 编写单元测试

**Files:**
- Modify: `test/utils/agents_test.py`（末尾追加新测试函数）

- [ ] **Step 1: 测试 ProgressEvent 构造**

在 `test/utils/agents_test.py` 末尾追加：

```python
class TestProgressEvent:
    """ProgressEvent 类型单元测试。"""

    def test_construct_minimal(self):
        from utils.agents import ProgressEvent

        event = ProgressEvent(type="thinking", message="test")
        assert event.type == "thinking"
        assert event.message == "test"
        assert event.detail is None

    def test_construct_with_detail(self):
        from utils.agents import ProgressEvent

        event = ProgressEvent(
            type="tool_call",
            message="test",
            detail={"tool_name": "search"},
        )
        assert event.detail == {"tool_name": "search"}

    def test_all_type_literals_valid(self):
        from utils.agents import ProgressEvent

        valid_types = [
            "thinking", "tool_call", "tool_result",
            "subagent_start", "subagent_done", "text_delta", "done",
        ]
        for t in valid_types:
            event = ProgressEvent(type=t, message="test")
            assert event.type == t
```

- [ ] **Step 2: 运行测试验证**

```bash
python -m pytest test/utils/agents_test.py::TestProgressEvent -v
```

预期：3 passed

- [ ] **Step 3: 测试 _emit_progress 安全模式**

在 `TestProgressEvent` 类之后追加：

```python
class TestEmitProgress:
    """_emit_progress 安全调用测试。"""

    @pytest.mark.asyncio
    async def test_does_nothing_when_reporter_is_none(self):
        from utils.agents import ProgressEvent, _emit_progress

        event = ProgressEvent(type="thinking", message="test")
        # 不应抛异常
        await _emit_progress(None, event)

    @pytest.mark.asyncio
    async def test_calls_reporter_with_event(self):
        from utils.agents import ProgressEvent, _emit_progress

        received: list[ProgressEvent] = []

        async def reporter(e: ProgressEvent) -> None:
            received.append(e)

        event = ProgressEvent(type="thinking", message="hello")
        await _emit_progress(reporter, event)
        assert len(received) == 1
        assert received[0] is event

    @pytest.mark.asyncio
    async def test_reporter_exception_does_not_propagate(self):
        from utils.agents import ProgressEvent, _emit_progress

        async def failing_reporter(_e: ProgressEvent) -> None:
            raise RuntimeError("boom")

        event = ProgressEvent(type="thinking", message="test")
        # 不应抛异常
        await _emit_progress(failing_reporter, event)
```

- [ ] **Step 4: 运行测试验证**

```bash
python -m pytest test/utils/agents_test.py::TestEmitProgress -v
```

预期：3 passed

- [ ] **Step 5: 测试 _collect_progress 与 mock stream**

在 `TestEmitProgress` 类之后追加：

```python
class TestCollectProgress:
    """_collect_progress 消费 astream_events v3 projection 的测试。"""

    @staticmethod
    def _mock_stream(*, subagents=(), tool_calls=(), messages=()):
        """构造一个与 astream_events v3 接口兼容的 mock stream。"""

        class _AsyncIter:
            def __init__(self, items):
                self._items = list(items)

            def __aiter__(self):
                return self

            async def __anext__(self):
                if not self._items:
                    raise StopAsyncIteration
                return self._items.pop(0)

        class MockStream:
            subagents = _AsyncIter(subagents)
            tool_calls = _AsyncIter(tool_calls)
            messages = _AsyncIter(messages)

        return MockStream()

    @pytest.mark.asyncio
    async def test_noop_when_reporter_is_none(self):
        from utils.agents import _collect_progress

        stream = self._mock_stream()
        # 不应抛异常
        await _collect_progress(stream, None)

    @pytest.mark.asyncio
    async def test_emits_thinking_on_first_message(self):
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        mock_text = MagicMock()
        mock_text.__aiter__.return_value = iter([])  # 空文本迭代器

        mock_msg = MagicMock()
        mock_msg.text = mock_text

        stream = self._mock_stream(messages=[mock_msg])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        thinking_calls = [
            c for c in reporter.call_args_list
            if c[0][0].type == "thinking"
        ]
        assert len(thinking_calls) == 1

    @pytest.mark.asyncio
    async def test_emits_subagent_start(self):
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        mock_sub = MagicMock()
        mock_sub.name = "research"

        stream = self._mock_stream(subagents=[mock_sub])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        subagent_calls = [
            c for c in reporter.call_args_list
            if c[0][0].type == "subagent_start"
        ]
        assert len(subagent_calls) == 1
        assert subagent_calls[0][0][0].detail["name"] == "research"

    @pytest.mark.asyncio
    async def test_emits_tool_call(self):
        from unittest.mock import MagicMock

        from utils.agents import _collect_progress

        mock_tc = MagicMock()
        mock_tc.tool_name = "web_search"

        stream = self._mock_stream(tool_calls=[mock_tc])
        reporter = MagicMock()

        await _collect_progress(stream, reporter)

        tool_calls = [
            c for c in reporter.call_args_list
            if c[0][0].type == "tool_call"
        ]
        assert len(tool_calls) == 1
        assert tool_calls[0][0][0].detail["tool_name"] == "web_search"

    @pytest.mark.asyncio
    async def test_one_consumer_failure_does_not_block_others(self):
        from unittest.mock import MagicMock

        import utils.agents as agents_mod

        # 让 tool_calls 迭代器抛异常
        class _FailingIter:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise RuntimeError("tool_call projection failed")

        mock_msg = MagicMock()
        mock_msg.text = MagicMock()
        mock_msg.text.__aiter__.return_value = iter([])

        stream = self._mock_stream(messages=[mock_msg])
        stream.tool_calls = _FailingIter()  # 替换为失败的
        reporter = MagicMock()

        # 不应抛异常，thinking 事件仍应被发出
        await agents_mod._collect_progress(stream, reporter)

        thinking_calls = [
            c for c in reporter.call_args_list
            if c[0][0].type == "thinking"
        ]
        assert len(thinking_calls) == 1, "thinking event should still emit even if tool_calls fails"
```

- [ ] **Step 6: 运行测试验证**

```bash
python -m pytest test/utils/agents_test.py::TestCollectProgress -v
```

预期：5 passed

- [ ] **Step 7: 测试 chat_agent 向后兼容（不传 progress_reporter）**

在 `TestCollectProgress` 类之后追加：

```python
class TestChatAgentStreaming:
    """chat_agent 流式改造的集成测试。"""

    @pytest.mark.asyncio
    async def test_no_reporter_behavior_unchanged(self, monkeypatch):
        """不传 progress_reporter 时，chat_agent 行为与 ainvoke 时期一致。"""
        from unittest.mock import AsyncMock, MagicMock

        import utils.agents as agents_mod

        # Mock create_deep_agent 返回的 agent
        mock_stream = MagicMock()
        # stream.output 返回最终 state
        mock_stream.output = AsyncMock(return_value={
            "messages": [AIMessage(content="hello")],
            "user_id": "123",
            "group_id": None,
        })

        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=mock_stream)

        monkeypatch.setattr(agents_mod, "create_deep_agent", MagicMock(return_value=mock_agent))
        monkeypatch.setattr(agents_mod, "_build_agent_backend", MagicMock())
        monkeypatch.setattr(agents_mod, "_agent_thread_id", MagicMock(return_value=uuid.uuid4()))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "load_system_prompt", lambda *a, **kw: "You are a bot.")
        monkeypatch.setattr(agents_mod.FrontierCognitive, "extract_uni_messages", AsyncMock(return_value=[]))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "clean_staged_artifact_handoffs", lambda self, msg: msg)

        cognitive = agents_mod.FrontierCognitive()
        result = await cognitive.chat_agent(
            messages=[{"role": "user", "content": "hi"}],
            user_id="123",
            user_name="tester",
            progress_reporter=None,  # 不传 reporter
        )

        assert isinstance(result, dict)
        assert "response" in result
        assert "total_time" in result
        assert "uni_messages" in result
        # 验证 astream_events 被调用
        mock_agent.astream_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_reporter_receives_events(self, monkeypatch):
        """传入 progress_reporter 时，应收到进度事件。"""
        from unittest.mock import AsyncMock, MagicMock, call

        import utils.agents as agents_mod

        # 构造一个能 yield 一个 mock message 的 stream
        mock_text = MagicMock()
        mock_text.__aiter__.return_value = iter(["hello "])

        mock_msg = MagicMock()
        mock_msg.text = mock_text

        # Mock stream 的 _AsyncIter 实现（在 _mock_stream 中已用）
        class _AsyncIter:
            def __init__(self, items):
                self._items = list(items)

            def __aiter__(self):
                return self

            async def __anext__(self):
                if not self._items:
                    raise StopAsyncIteration
                return self._items.pop(0)

        mock_stream = MagicMock()
        mock_stream.messages = _AsyncIter([mock_msg])
        mock_stream.tool_calls = _AsyncIter([])
        mock_stream.subagents = _AsyncIter([])
        mock_stream.output = AsyncMock(return_value={
            "messages": [AIMessage(content="hello")],
            "user_id": "123",
            "group_id": None,
        })

        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=mock_stream)

        monkeypatch.setattr(agents_mod, "create_deep_agent", MagicMock(return_value=mock_agent))
        monkeypatch.setattr(agents_mod, "_build_agent_backend", MagicMock())
        monkeypatch.setattr(agents_mod, "_agent_thread_id", MagicMock(return_value=uuid.uuid4()))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "load_system_prompt", lambda *a, **kw: "You are a bot.")
        monkeypatch.setattr(agents_mod.FrontierCognitive, "extract_uni_messages", AsyncMock(return_value=[]))
        monkeypatch.setattr(agents_mod.FrontierCognitive, "clean_staged_artifact_handoffs", lambda self, msg: msg)

        reporter = MagicMock()

        cognitive = agents_mod.FrontierCognitive()
        result = await cognitive.chat_agent(
            messages=[{"role": "user", "content": "hi"}],
            user_id="123",
            user_name="tester",
            progress_reporter=reporter,
        )

        assert "response" in result
        # reporter 应至少收到 thinking 事件
        event_types = [c[0][0].type for c in reporter.call_args_list]
        assert "thinking" in event_types, f"Expected 'thinking' in {event_types}"
```

- [ ] **Step 8: 运行测试验证**

```bash
python -m pytest test/utils/agents_test.py::TestChatAgentStreaming -v
```

预期：2 passed

- [ ] **Step 9: 运行全部 agent 测试确保无回归**

```bash
python -m pytest test/utils/agents_test.py -v
```

预期：所有测试通过。

- [ ] **Step 10: Commit**

```bash
git add test/utils/agents_test.py
git commit -m "test: add unit tests for ProgressEvent, _collect_progress, and streaming chat_agent"
```

---

### Task 6: 最终验证与文档

- [ ] **Step 1: 运行全量 agent 和 plugin 测试**

```bash
python -m pytest test/utils/agents_test.py test/plugins/clockwork_test.py -v
```

- [ ] **Step 2: 运行 lint 检查**

```bash
ruff check utils/agents.py plugins/agent/__init__.py test/utils/agents_test.py
```

- [ ] **Step 3: Commit final touch-ups（如有）**

```bash
git add -u && git commit -m "chore: final lint and test verification for agent streaming"
```
