# ruff: noqa: S101
"""Real LangChain/Deep Agents contracts, independent of unit-test stubs."""

import subprocess
import sys
from pathlib import Path


def test_real_agent_limits_errors_and_nested_usage(tmp_path):
    script = r'''
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, ToolException
from langgraph.errors import GraphInterrupt
from utils.agents import cognitive
from utils.agents.tool_errors import prepare_ptc_tools
from utils.configs import EnvConfig

class ContractModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

def message(content='', tools=None, tokens=10):
    return AIMessage(content=content, tool_calls=tools or [], usage_metadata={
        'input_tokens': tokens, 'output_tokens': 2, 'total_tokens': tokens + 2,
        'input_token_details': {'cache_read': 3},
        'output_token_details': {'reasoning': 1},
    })

calls = []
@tool
async def get_recent_conversation() -> str:
    """Read a synthetic conversation."""
    calls.append('read')
    raise RuntimeError('secret-api-key and private-user-content')

@tool
async def change_file() -> str:
    """Change a synthetic file."""
    calls.append('write')
    raise TimeoutError('secret-platform-token')

@tool
async def lookup() -> str:
    """Read synthetic data."""
    calls.append('lookup')
    return 'result'

def tool_call(name, identifier='call'):
    return {'name': name, 'args': {}, 'id': identifier}

async def run(responses, tools):
    model = ContractModel(responses=responses, tags=['frontier:main'])
    cognitive.create_llm = lambda **kwargs: model
    cognitive.agent_tools = SimpleNamespace(restricted_tools=[])
    EnvConfig.ADVAN_MODEL = 'contract-model'
    EnvConfig.AGENT_JOB_TIMEOUT_SECONDS = 20
    agent = object.__new__(cognitive.FrontierCognitive)
    agent.tools, agent.ptc_tools = tools, []
    agent.research_subagent = agent.document_subagent = None
    agent.working_dir = str(Path.cwd() / 'sandbox')
    agent.load_system_prompt = lambda group_id: 'Answer the current request.'
    return await agent.chat_agent([{'role': 'user', 'content': 'help'}], user_id='contract', user_name='Contract', enable_acp_subagents=False)

async def main():
    EnvConfig.AGENT_MODEL_CALL_LIMIT = 1
    result = await run([message(tools=[tool_call('lookup')]), message('unreachable')], [lookup])
    assert result['error_code'] == 'budget_exceeded', result
    assert result['usage']['model_calls'] == 1, result
    assert result['usage']['input_tokens'] == 10, result
    assert calls == ['lookup'], calls

    calls.clear()
    EnvConfig.AGENT_MODEL_CALL_LIMIT = 5
    EnvConfig.AGENT_TOOL_CALL_LIMIT = 1
    result = await run([message(tools=[tool_call('lookup', 'one'), tool_call('lookup', 'two')])], [lookup])
    assert result['error_code'] == 'budget_exceeded', result
    assert len(calls) <= 1, calls

    calls.clear()
    EnvConfig.AGENT_TOOL_CALL_LIMIT = 10
    result = await run([message(tools=[tool_call('get_recent_conversation')]), message('query unavailable')], [get_recent_conversation])
    assert result['status'] == 'success', result
    assert result['usage']['model_calls'] == 2, result
    assert calls == ['read'], calls
    assert 'secret' not in str(result), result

    calls.clear()
    result = await run([message(tools=[tool_call('change_file')]), message('must not execute')], [change_file])
    assert result['error_code'] == 'tool_execution_uncertain', result
    assert result['usage']['model_calls'] == 1, result
    assert calls == ['write'], calls
    assert 'secret' not in str(result), result

    # The PTC bridge calls .arun directly; its copied tool must sanitize there too.
    prepared = prepare_ptc_tools([get_recent_conversation])[0]
    assert prepared is not get_recent_conversation
    try:
        await prepared.arun({})
    except ToolException as exc:
        assert 'secret' not in str(exc)
        assert '查询工具暂时不可用' in str(exc)
    else:
        raise AssertionError('PTC failure was not surfaced')

    @tool
    def interrupt_sync() -> str:
        """Interrupt a synthetic synchronous query."""
        raise GraphInterrupt(())

    @tool
    async def interrupt_async() -> str:
        """Interrupt a synthetic asynchronous query."""
        raise GraphInterrupt(())

    for prepared in prepare_ptc_tools([interrupt_sync, interrupt_async]):
        try:
            await prepared.arun({})
        except GraphInterrupt:
            pass
        else:
            raise AssertionError('PTC swallowed a graph interrupt')

    child = create_agent(model=ContractModel(responses=[message('child', tokens=7)], tags=['frontier:research']))
    @tool
    async def delegate(config: RunnableConfig) -> str:
        """Delegate one synthetic research question."""
        await child.ainvoke({'messages': [{'role': 'user', 'content': 'research'}]}, config=config)
        return 'child complete'

    result = await run([message(tools=[tool_call('delegate')]), message('finished')], [delegate])
    assert result['status'] == 'success', result
    assert result['usage']['model_calls'] == 3, result
    assert result['usage']['input_tokens'] == 27, result
    assert result['usage']['output_tokens'] == 6, result
    assert result['usage']['cache_read_tokens'] == 9, result
    assert result['usage']['usage_missing_calls'] == 0, result
    assert {row['component'] for row in result['usage']['models']} == {'main', 'research'}, result

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_structured_output_bindings_keep_selected_endpoint(tmp_path):
    script = r'''
import sys
sys.path.insert(0, sys.argv[1])
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.configs import EnvConfig
from utils.llm_factory import structured_output_options

class Decision(BaseModel):
    allowed: bool

EnvConfig.LLM_PROVIDERS = {
    'openai': {'type': 'openai', 'api_mode': 'responses'},
    'deepseek': {'type': 'deepseek', 'api_mode': 'chat_completions'},
    'anthropic': {'type': 'anthropic', 'api_mode': 'messages'},
    'google': {'type': 'google', 'api_mode': 'generate_content'},
}
models = [
    ('openai', ChatOpenAI(model='gpt-5.4', api_key='test-key', profile={'structured_output': True})),
    ('deepseek', ChatDeepSeek(model='deepseek-v4-flash', api_key='test-key')),
    ('anthropic', ChatAnthropic(model='claude-sonnet-4-6', api_key='test-key', profile={'structured_output': True})),
    ('google', ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key='test-key')),
]
for provider, model in models:
    options = structured_output_options(model.model if provider != 'openai' else model.model_name, provider, model)
    if provider == 'deepseek':
        # V4 思考模式拒绝强制 tool_choice：Signal 只把 schema 放进提示词，
        # 请求里既没有工具绑定，也没有 response_format。
        assert options == {'method': 'text_json'}, options
        payload = model._get_request_payload([HumanMessage(content='判断')])
        assert 'tools' not in payload and 'tool_choice' not in payload, payload
        assert 'response_format' not in payload, payload
        continue
    runnable = model.with_structured_output(Decision, **options)
    assert runnable is not None
    if provider == 'openai':
        assert options == {'method': 'json_schema', 'strict': True}, options
    else:
        assert options == {'method': 'json_schema'}, options
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
