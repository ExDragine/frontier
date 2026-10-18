# ruff: noqa: S101
"""Reference images survive the real Agent's pinned skills and blob offload."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("supports_vision", [False, True])
@pytest.mark.parametrize("mode", ["auto", "edit"])
def test_real_agent_keeps_original_images_for_editing(tmp_path, supports_vision, mode):
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
from langchain_core.messages import AIMessage, ToolMessage
from PIL import Image
from tools import paint as paint_tool
from utils.agents import cognitive, inputs
from utils.configs import EnvConfig
from utils.media import inline_media_bytes, resolve_media, standard_media_block

supports_vision, mode = sys.argv[2] == 'True', sys.argv[3]
inputs.model_supports = lambda *args, **kwargs: supports_vision
originals = []
for color in ('blue', 'green'):
    stream = io.BytesIO()
    Image.new('RGB', (4, 4), color).save(stream, format='PNG')
    originals.append(stream.getvalue())
calls, seen = [], []

async def synthetic_paint(prompt, references):
    calls.append((prompt, references))
    return originals[0]
paint_tool.paint = synthetic_paint

async def no_capture(_text):
    return set()
cognitive.detect_browser_capture_intent = no_capture

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

async def main():
    EnvConfig.ADVAN_MODEL = 'contract-model'
    EnvConfig.PAINT_MODULE_ENABLED = True
    EnvConfig.PAINT_WHITELIST_MODE = False
    EnvConfig.PAINT_BLACKLIST_PERSON_LIST = []
    EnvConfig.PAINT_BLACKLIST_GROUP_LIST = []
    EnvConfig.PAINT_RATE_LIMIT_MAX_REQUESTS = 100
    EnvConfig.AGENT_JOB_TIMEOUT_SECONDS = 20
    EnvConfig.AGENT_MODEL_CALL_LIMIT = 3
    EnvConfig.AGENT_TOOL_CALL_LIMIT = 5
    args = {'prompt': 'change only the background'}
    if mode == 'edit':
        args['mode'] = 'edit'
    model = Model(responses=[
        AIMessage(content='', tool_calls=[{'name': 'get_paint', 'args': args, 'id': 'paint-1'}]),
        AIMessage(content='image ready'),
    ])
    cognitive.create_llm = lambda **kwargs: model
    cognitive.agent_tools = SimpleNamespace(restricted_tools=[])
    agent = object.__new__(cognitive.FrontierCognitive)
    agent.tools = [paint_tool.get_paint]
    agent.document_subagent = None
    agent.working_dir = str(Path.cwd() / 'sandbox')
    agent.load_system_prompt = lambda group_id: 'Edit the provided images.'
    messages = [
        {'role': 'user', 'content': 'old unrelated request'},
        {'role': 'assistant', 'content': 'old reply'},
        {'role': 'user', 'content': [
            {'type': 'text', 'text': 'change only the background, using the current and quoted images'},
            *[standard_media_block(resolve_media(raw, 'image')) for raw in originals],
        ]},
    ]
    result = await agent.chat_agent(messages, image_inputs=originals, user_id='contract',
                                    user_name='Contract', enable_acp_subagents=False)
    assert calls == [('change only the background', originals)], (mode, supports_vision, calls)
    assert result['status'] == 'success' and len(result['artifacts']) == 1, result
    assert result['artifacts'][0].data == originals[0], result
    assert len(seen) == 2 and any(
        message.additional_kwargs.get('lc_source') == 'pinned_skill' for message in seen[0]
    ), seen
    if supports_vision:
        assert any(Path(agent.working_dir).rglob('blobs/*')), 'binary offload must be exercised'
    else:
        assert not any(inline_media_bytes(block) for message in seen[0]
                       if isinstance(message.content, list) for block in message.content)
    tools = [message for message in seen[-1] if isinstance(message, ToolMessage)]
    assert len(tools) == 1 and '成功编辑图片' in tools[0].content, tools

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2]), str(supports_vision), mode],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
