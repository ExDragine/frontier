# ruff: noqa: S101
"""Real LangChain/Deep Agents contracts, without model downloads or QQ writes."""

import os
import subprocess
import sys
from pathlib import Path


def test_real_agent_sends_speech_as_one_automatic_audio_artifact(tmp_path):
    script = r"""
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, sys.argv[1])
import nonebot
nonebot.init(driver='~fastapi', log_level='ERROR')
nonebot.require('nonebot_plugin_alconna')

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from tools import speech as speech_tool
from utils.agents import cognitive
from utils.configs import EnvConfig, SpeechSynthesisConfig
from utils.speech_synthesis import SynthesizedSpeech

calls = []
async def synthetic_speech(text, *, settings):
    calls.append((text, settings.enabled))
    return SynthesizedSpeech(b'wav', b'\x02#!SILK_V3voice', 0.2, 0.3)
speech_tool.synthesize_speech = synthetic_speech

class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

async def main():
    EnvConfig.ADVAN_MODEL = 'contract-model'
    EnvConfig.SPEECH_SYNTHESIS = SpeechSynthesisConfig(enabled=True)
    EnvConfig.PAINT_WHITELIST_MODE = False
    EnvConfig.PAINT_BLACKLIST_PERSON_LIST = []
    EnvConfig.PAINT_BLACKLIST_GROUP_LIST = []
    EnvConfig.AGENT_JOB_TIMEOUT_SECONDS = 20
    EnvConfig.AGENT_MODEL_CALL_LIMIT = 3
    EnvConfig.AGENT_TOOL_CALL_LIMIT = 5
    properties = speech_tool.get_speech.tool_call_schema.model_json_schema()['properties']
    assert set(properties) == {'text'}, properties
    model = Model(responses=[
        AIMessage(content='', tool_calls=[{'name': 'get_speech', 'args': {'text': 'hello'}, 'id': 'voice-1'}]),
        AIMessage(content='voice ready'),
    ])
    cognitive.create_llm = lambda **kwargs: model
    cognitive.agent_tools = SimpleNamespace(restricted_tools=[])
    agent = object.__new__(cognitive.FrontierCognitive)
    agent.tools = [speech_tool.get_speech]
    agent.document_subagent = None
    agent.working_dir = str(Path.cwd() / 'sandbox')
    agent.load_system_prompt = lambda group_id: 'Read the requested text aloud.'
    result = await agent.chat_agent(
        [{'role': 'user', 'content': 'Read hello aloud'}],
        user_id='contract', user_name='Contract', enable_acp_subagents=False,
    )
    assert calls == [('hello', True)], calls
    assert result['status'] == 'success' and len(result['artifacts']) == 1, result
    artifact = result['artifacts'][0]
    assert artifact.kind == 'audio' and artifact.data == b'\x02#!SILK_V3voice', artifact
    assert 'torch' not in sys.modules and 'onnxruntime' not in sys.modules

asyncio.run(main())
"""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
