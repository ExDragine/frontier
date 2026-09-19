# ruff: noqa: S101
"""Exercise real checkpoint serialization and delta restoration outside test stubs."""

import subprocess
import sys
from pathlib import Path


def test_real_bounded_checkpointer_contract(tmp_path):
    script = r'''
import asyncio
import sys
sys.path.insert(0, sys.argv[1])
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from deepagents.graph import DeepAgentState
from utils.agents.checkpoints import BoundedMemorySaver
from utils.agents.session_errors import CheckpointCapacityExceeded

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

class Artifact:
    pass

@tool(response_format='content_and_artifact')
def read_value() -> tuple:
    """Return a synthetic artifact."""
    return 'value', Artifact()

async def main():
    saver = BoundedMemorySaver()
    saver.register('thread', limit=10_000_000, total_limit=20_000_000)
    config = {'configurable': {'thread_id': 'thread'}}
    for index in range(28):
        model = Model(responses=[
            AIMessage(content='', tool_calls=[{'name': 'read_value', 'args': {}, 'id': f'call-{index}'}]),
            AIMessage(content=f'reply-{index}'),
        ])
        graph = create_agent(model, tools=[read_value], state_schema=DeepAgentState, checkpointer=saver,
            middleware=[ModelCallLimitMiddleware(run_limit=2, exit_behavior='error'),
                        ToolCallLimitMiddleware(run_limit=1, exit_behavior='error')])
        response = await graph.ainvoke({'messages': [{'role': 'user', 'content': str(index), 'id': f'input-{index}'}]}, config)
        assert response['messages'][-1].content == f'reply-{index}'
        assert any(isinstance(m.artifact, Artifact) for m in response['messages'] if isinstance(m, ToolMessage))
        snapshot = await graph.aget_state(config)
        assert not snapshot.next
        assert len([m for m in snapshot.values['messages'] if m.type == 'human']) == index + 1
        assert all(m.artifact is None for m in snapshot.values['messages'] if isinstance(m, ToolMessage))
    assert saver.size() > 0
    # Updating a known message replaces it, including after a DeltaChannel snapshot.
    final = snapshot.values['messages'][-1]
    await graph.aupdate_state(config, {'messages': [AIMessage(content='delivered', id=final.id)]})
    assert (await graph.aget_state(config)).values['messages'][-1].content == 'delivered'
    await saver.adelete_thread('thread')
    assert await saver.aget_tuple(config) is None
    assert saver.size() == 0
    saver.register('small', limit=1024, total_limit=20_000_000)
    graph = create_agent(Model(responses=[AIMessage(content='unused')]), checkpointer=saver)
    try:
        await graph.ainvoke({'messages': [{'role': 'user', 'content': 'x' * 2000}]}, {'configurable': {'thread_id': 'small'}})
    except CheckpointCapacityExceeded:
        pass
    else:
        raise AssertionError('capacity was not enforced')
    assert saver.size() <= 1024
    await saver.adelete_thread('small')
    assert saver.size() == 0

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_frontier_hot_turns_delivery_and_artifacts(tmp_path):
    script = r'''
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from utils.agents import cognitive
from utils.agents.sessions import SessionManager, SessionKey, HistoryBoundary, database_message_id
from utils.configs import EnvConfig, SessionConfig

prompts = []
roles = []
class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
    def _generate(self, messages, *args, **kwargs):
        prompts.append(messages)
        return super()._generate(messages, *args, **kwargs)

from nonebot_plugin_alconna.uniseg import UniMessage
sys.modules['utils.alconna'] = SimpleNamespace(UniMessage=UniMessage)

@tool
async def get_recent_conversation(config: RunnableConfig) -> str:
    """Read synthetic context."""
    roles.append(config['configurable']['group_member_role'])
    return 'context'

@tool(response_format='content_and_artifact')
async def create_picture() -> tuple:
    """Create a synthetic transport artifact."""
    return 'picture ready', UniMessage.image(raw=b'synthetic image')

def msg(identifier, content):
    return {'role': 'user', 'content': content, 'id': database_message_id('99', identifier)}

async def main():
    EnvConfig.SESSIONS = settings = SessionConfig(enabled=True)
    EnvConfig.REVISION = 1
    EnvConfig.ADVAN_MODEL = 'contract-model'
    EnvConfig.AGENT_MODEL_CALL_LIMIT = 2
    EnvConfig.AGENT_TOOL_CALL_LIMIT = 1
    manager = SessionManager()
    agent = object.__new__(cognitive.FrontierCognitive)
    agent.tools = [get_recent_conversation, create_picture]
    agent.ptc_tools = []
    agent.document_subagent = None
    agent.working_dir = str(Path.cwd() / 'sandbox')
    agent.load_system_prompt = lambda _: 'Answer only the current request.'
    cognitive.agent_tools = SimpleNamespace(restricted_tools=[])
    first_thread = None
    for number, user, input_id, role in [(0, '10', 1, 'admin'), (1, '11', 4, 'member')]:
        lease = manager.begin(SessionKey('99', user, 20), HistoryBoundary(input_id, 1000 + number * 2000), settings, 1)
        if number:
            assert lease.hot and lease.entry.thread_id == first_thread
        else:
            first_thread = lease.entry.thread_id
        model = Model(responses=[
            AIMessage(content='', tool_calls=[{'name': 'get_recent_conversation', 'args': {}, 'id': f'call-{number}'}]),
            AIMessage(content=f'unreviewed-{number}')], profile={'max_input_tokens': 64000})
        cognitive.create_llm = lambda **_: model
        inputs = [msg(1, 'first')] if not number else [msg(2, 'background-only'),
            {'role': 'assistant', 'content': 'audited-0', 'id': database_message_id('99', 3)}, msg(4, 'current')]
        result = await agent.chat_agent(inputs, user_id=user, user_name=user, group_id=20,
            group_member_role=role, session_turn=lease, enable_acp_subagents=False)
        assert result['status'] == 'success', result
        assert result['usage']['model_calls'] == 2, result
        assert lease.entry.state == 'awaiting_delivery'
        assert not result['uni_messages']
        if number:
            text = str([m.content for m in prompts[-2]])
            assert 'audited-0' in text and 'unreviewed-0' not in text, text
            assert text.count('background-only') == 1, text
            assert text.count('audited-0') == 1, text
        await manager.finish(lease, delivered=True, content=f'audited-{number}', message_id=input_id + 2,
            delivered_at=1100 + number * 2000)
    assert roles == ['admin', 'member'], roles
    # Current media can be sent even though saved tool messages have no artifact.
    lease = manager.begin(SessionKey('99', '10', 20), HistoryBoundary(7, 5000), settings, 1)
    model = Model(responses=[AIMessage(content='', tool_calls=[{'name': 'create_picture', 'args': {}, 'id': 'media'}]),
                            AIMessage(content='done')], profile={'max_input_tokens': 64000})
    cognitive.create_llm = lambda **_: model
    result = await agent.chat_agent([msg(7, 'draw')], user_id='10', user_name='10', group_id=20,
        session_turn=lease, enable_acp_subagents=False)
    assert result['status'] == 'success', result
    assert len(result['uni_messages']) == 1, result
    await manager.finish(lease, delivered=True, content='done', message_id=8, delivered_at=5100)
    assert not manager.entries and manager.saver.size() == 0
    # A queued request predating the last delivery must not inherit that reply.
    lease = manager.begin(SessionKey('99', '10', 20), HistoryBoundary(9, 6000), settings, 1)
    lease.valid_result = True
    await manager.finish(lease, silent=True, delivered_at=6100)
    queued = manager.begin(SessionKey('99', '11', 20), HistoryBoundary(10, 6050), settings, 1)
    assert not queued.hot
    assert manager.metrics['snapshot_conflict'] == 1
    await manager.finish(queued)
    assert not manager.entries

    # Nested Deep Agent namespaces must use the registered parent thread budget.
    agent.document_subagent = {'name': 'document-agent', 'description': 'Read synthetic documents.',
        'model': Model(responses=[AIMessage(content='child result')]), 'tools': []}
    lease = manager.begin(SessionKey('99', '10', 20), HistoryBoundary(11, 7000), settings, 1)
    model = Model(responses=[AIMessage(content='', tool_calls=[{'name': 'task',
        'args': {'description': 'read', 'subagent_type': 'document-agent'}, 'id': 'nested'}]), AIMessage(content='child complete')])
    cognitive.create_llm = lambda **_: model
    result = await agent.chat_agent([msg(11, 'inspect')], user_id='10', user_name='10', group_id=20,
        session_turn=lease, enable_acp_subagents=False)
    assert result['status'] == 'success', result
    assert result['usage']['model_calls'] == 3, result
    await manager.finish(lease, delivered=True, content='child complete', message_id=12, delivered_at=7100)

    entered, cancelled = asyncio.Event(), asyncio.Event()
    @tool
    async def slow_query() -> str:
        """Wait for a synthetic read."""
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
        return 'unreachable'

    agent.tools = [slow_query]
    agent.document_subagent = None
    lease = manager.begin(SessionKey('99', '10', 20), HistoryBoundary(13, 8000), settings, 1)
    model = Model(responses=[AIMessage(content='', tool_calls=[{'name': 'slow_query', 'args': {}, 'id': 'slow'}])])
    cognitive.create_llm = lambda **_: model
    running = asyncio.create_task(agent.chat_agent([msg(13, 'wait')], user_id='10', user_name='10', group_id=20,
        session_turn=lease, enable_acp_subagents=False))
    await asyncio.wait_for(entered.wait(), 10)
    running.cancel()
    try:
        await running
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError('cancellation was swallowed')
    await asyncio.wait_for(cancelled.wait(), 10)
    await manager.finish(lease)
    await asyncio.sleep(0.05)
    assert not manager.entries and manager.saver.size() == 0

    from langgraph.types import interrupt
    @tool
    async def approval() -> str:
        """Pause for an unsupported approval."""
        return interrupt('approval')

    agent.tools = [approval]
    lease = manager.begin(SessionKey('99', '10', 20), HistoryBoundary(14, 9000), settings, 1)
    model = Model(responses=[AIMessage(content='', tool_calls=[{'name': 'approval', 'args': {}, 'id': 'approval'}])])
    cognitive.create_llm = lambda **_: model
    result = await agent.chat_agent([msg(14, 'approve')], user_id='10', user_name='10', group_id=20,
        session_turn=lease, enable_acp_subagents=False)
    assert result['status'] == 'failed' and result['error_code'] == 'session_interrupted', result
    await manager.finish(lease)
    assert not manager.entries and manager.saver.size() == 0

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_session_storage_stays_bounded_across_rotations(tmp_path):
    script = r'''
import asyncio
import gc
import json
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from deepagents.graph import DeepAgentState
from utils.agents.sessions import SessionManager, SessionKey, HistoryBoundary
from utils.configs import EnvConfig, SessionConfig

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

async def main():
    now = [0.0]
    manager = SessionManager(clock=lambda: now[0])
    EnvConfig.SESSIONS = settings = SessionConfig(enabled=True, max_generation_turns=2, max_sessions=2,
        max_session_bytes=1_000_000, max_total_bytes=2_000_000, private_idle_seconds=10)
    samples, number = [], 0
    for batch in range(12):
        for peer in range(4):
            for turn in range(3):
                number += 1
                lease = manager.begin(SessionKey('99', str(peer)), HistoryBoundary(number, number * 1000), settings, 1)
                graph = create_agent(Model(responses=[AIMessage(content='answer ' * 128)]),
                    state_schema=DeepAgentState, checkpointer=manager.saver)
                await graph.ainvoke({'messages': [{'role': 'user', 'content': 'context ' * 128, 'id': lease.current_id}]},
                    {'configurable': {'thread_id': lease.entry.thread_id}})
                lease.valid_result = True
                await manager.finish(lease, silent=True)
                assert manager.saver.size() <= settings.max_total_bytes
                assert len(manager.entries) <= settings.max_sessions
        now[0] += 11
        manager.sweep(settings)
        assert not manager.entries and manager.saver.size() == 0
        gc.collect()
        rss = next(int(line.split()[1]) for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:'))
        samples.append(rss)
    assert manager.metrics['rotated'] == 48, manager.metrics
    assert manager.metrics['expired'] == 24, manager.metrics
    assert manager.metrics['evicted'] == 24, manager.metrics
    print(json.dumps({'turns': number, 'rss_kib_by_batch': samples, 'cache': manager.snapshot()}))

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout)
