# ruff: noqa: S101
"""Real media artifacts survive recoverable source errors and virtual path routing."""

import subprocess
import sys
from pathlib import Path


def test_real_media_tools_preserve_artifacts_and_platform_write_boundaries(tmp_path):
    script = r'''
import asyncio
import io
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, sys.argv[1])
import nonebot
nonebot.init(driver='~fastapi', log_level='ERROR')
nonebot.require('nonebot_plugin_alconna')

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from PIL import Image
from tools import adapter, paint as paint_tool, video as video_tool
from utils.agents import cognitive
from utils.configs import EnvConfig

buffer = io.BytesIO()
Image.new('RGB', (4, 4), 'blue').save(buffer, format='PNG')
png = buffer.getvalue()
calls = []

async def synthetic_paint(prompt, refs):
    calls.append('paint')
    return png
paint_tool.paint = synthetic_paint

async def no_capture(_text):
    return set()
cognitive.detect_browser_capture_intent = no_capture

def forbidden_platform():
    raise AssertionError('Media artifact builders must not call QQ APIs')
adapter.get_bot = forbidden_platform

@tool
async def platform_write() -> str:
    """Simulate a write that fails after it may have taken effect."""
    calls.append('write')
    raise ValueError('private failure after a platform write')

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

def call(name, args, identifier):
    return AIMessage(content='', tool_calls=[{'name': name, 'args': args, 'id': identifier}])

async def run(extra=None):
    responses = [call('get_paint', {'prompt': 'synthetic'}, 'paint-1')]
    if extra is not None:
        responses.append(call(extra[0], extra[1], 'extra-1'))
    responses.append(AIMessage(content='image ready'))
    model = Model(responses=responses)
    cognitive.create_llm = lambda **kwargs: model
    cognitive.agent_tools = SimpleNamespace(restricted_tools=[])
    agent = object.__new__(cognitive.FrontierCognitive)
    agent.tools = [paint_tool.get_paint, platform_write, *[
        getattr(adapter, name) for name in ('send_image', 'send_audio', 'send_voice', 'send_video')
    ]]
    agent.document_subagent = None
    agent.working_dir = str(Path.cwd() / 'sandbox')
    agent.load_system_prompt = lambda group_id: 'Return the requested image.'
    return await agent.chat_agent([{'role': 'user', 'content': 'draw'}], user_id='contract',
                                  user_name='Contract', enable_acp_subagents=False)

async def main():
    EnvConfig.ADVAN_MODEL = 'contract-model'
    EnvConfig.PAINT_MODULE_ENABLED = True
    EnvConfig.PAINT_WHITELIST_MODE = False
    EnvConfig.PAINT_BLACKLIST_PERSON_LIST = []
    EnvConfig.PAINT_BLACKLIST_GROUP_LIST = []
    EnvConfig.PAINT_RATE_LIMIT_MAX_REQUESTS = 100
    EnvConfig.AGENT_JOB_TIMEOUT_SECONDS = 20
    EnvConfig.AGENT_MODEL_CALL_LIMIT = 5
    EnvConfig.AGENT_TOOL_CALL_LIMIT = 10

    assert '自动发送' in paint_tool.get_paint.description
    assert '无需再调用 send_image' in paint_tool.get_paint.description
    assert '自动发送' in video_tool.get_video.description
    assert '无需再调用 send_video' in video_tool.get_video.description

    # A generated image is returned exactly once, without a second send tool.
    result = await run()
    assert result['status'] == 'success', result
    assert len(result['artifacts']) == 1 and result['artifacts'][0].data == png, result
    assert calls == ['paint'], calls
    assert result['usage']['model_calls'] == 2, result

    invalid_calls = [(name, {'source': '/missing-private-media.png'})
                     for name in ('send_image', 'send_audio', 'send_voice', 'send_video')]
    invalid_calls += [
        ('send_image', {'source': 'https://[invalid'}),
        ('send_image', {'source': 'data:image/png;base64,private-image'}),
        ('send_image', {}),
        ('send_image', {'source': 42}),
    ]
    for extra in invalid_calls:
        calls.clear()
        result = await run(extra)
        assert result['status'] == 'success', (extra, result)
        assert result['usage']['model_calls'] == 3, (extra, result)
        assert len(result['artifacts']) == 1 and result['artifacts'][0].data == png, (extra, result)
        assert calls == ['paint'], (extra, calls)

    # Existing files on both mounts remain real Path-backed artifacts all the way
    # through the graph and neutral conversion, with no immediate platform sends.
    workspace_key = cognitive.conversation_workspace_key('contract', None)
    for folder, source in (
        (f'workspaces/{workspace_key}', '/existing.png'),
        (f'memory/{workspace_key}', f'/memory/{workspace_key}/existing.png'),
    ):
        path = Path.cwd() / 'sandbox' / folder / 'existing.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)
        for name, kind in (('send_image', 'image'), ('send_audio', 'audio'),
                           ('send_voice', 'audio'), ('send_video', 'video')):
            calls.clear()
            result = await run((name, {'source': source}))
            assert result['status'] == 'success', result
            assert len(result['artifacts']) == 2, (name, source, result)
            assert result['artifacts'][0].data == png, result
            assert result['artifacts'][1].kind == kind, result
            assert result['artifacts'][1].path == str(path), result
            assert calls == ['paint'], calls

    # Do not generalize recoverability to writes or restart the graph after them.
    calls.clear()
    result = await run(('platform_write', {}))
    assert result['error_code'] == 'tool_execution_uncertain', result
    assert result['usage']['model_calls'] == 2, result
    assert calls == ['paint', 'write'], calls
    assert 'private failure' not in str(result), result

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
