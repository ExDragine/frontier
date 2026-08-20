# ruff: noqa: S101, S105

import base64
import json
from types import SimpleNamespace

import pytest

from utils.agents.acp import AcpAgent, AcpAgentService, AcpInputMedia, load_acp_config
from utils.agents.acp.service import AcpConfigurationError


class _Model:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _RequestError(Exception):
    @classmethod
    def method_not_found(cls, method):
        return cls(method)


class _FakeConnection:
    def __init__(self, client, *, image=True, audio=False, auth_methods=()):
        self.client = client
        self.image = image
        self.audio = audio
        self.auth_methods = auth_methods
        self.initializations = []
        self.authentications = []
        self.new_sessions = []
        self.prompts = []
        self.cancelled = 0

    async def initialize(self, **kwargs):
        self.initializations.append(kwargs)
        return SimpleNamespace(
            protocol_version=1,
            agent_capabilities=SimpleNamespace(
                prompt_capabilities=SimpleNamespace(image=self.image, audio=self.audio)
            ),
            auth_methods=[SimpleNamespace(id=method) for method in self.auth_methods],
        )

    async def authenticate(self, **kwargs):
        self.authentications.append(kwargs)
        return SimpleNamespace()

    async def new_session(self, **kwargs):
        self.new_sessions.append(kwargs)
        return SimpleNamespace(session_id="session-1")

    async def prompt(self, *, session_id, prompt):
        self.prompts.append((session_id, prompt))
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="agent_thought_chunk",
                content=SimpleNamespace(type="text", text="private reasoning"),
            ),
        )
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="agent_message_chunk",
                message_id="message-1",
                content=SimpleNamespace(type="text", text="我先检查。"),
            ),
        )
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="tool_call",
                tool_call_id="tool-1",
                title="Read files",
            ),
        )
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="tool_call_update",
                tool_call_id="tool-1",
                title=None,
                status="completed",
            ),
        )
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="agent_message_chunk",
                message_id="message-2",
                content=SimpleNamespace(type="text", text="最终"),
            ),
        )
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="agent_message_chunk",
                message_id="message-2",
                content=SimpleNamespace(type="text", text="回复"),
            ),
        )
        await self.client.session_update(
            session_id,
            SimpleNamespace(
                session_update="agent_message_chunk",
                message_id="message-2",
                content=SimpleNamespace(
                    type="image",
                    data=base64.b64encode(b"image-bytes").decode(),
                    mime_type="image/png",
                ),
            ),
        )
        return SimpleNamespace(stop_reason="end_turn")

    async def cancel(self, **_kwargs):
        self.cancelled += 1


class _FakeManager:
    def __init__(self, connection):
        self.connection = connection
        self.closed = 0

    async def __aenter__(self):
        return self.connection, SimpleNamespace(stderr=None)

    async def __aexit__(self, *_args):
        self.closed += 1


def _fake_sdk(created, *, image=True, audio=False, auth_methods=()):
    sdk = SimpleNamespace()
    sdk.PROTOCOL_VERSION = 1
    sdk.RequestError = _RequestError
    sdk.RequestPermissionResponse = _Model
    sdk.schema = SimpleNamespace(
        AllowedOutcome=_Model,
        DeniedOutcome=_Model,
        DeclineElicitationResponse=_Model,
        ClientCapabilities=_Model,
        FileSystemCapabilities=_Model,
        Implementation=_Model,
    )
    sdk.text_block = lambda text: SimpleNamespace(type="text", text=text)
    sdk.image_block = lambda data, mime_type: SimpleNamespace(type="image", data=data, mime_type=mime_type)
    sdk.audio_block = lambda data, mime_type: SimpleNamespace(type="audio", data=data, mime_type=mime_type)

    def spawn_agent_process(client, command, *args, **kwargs):
        connection = _FakeConnection(client, image=image, audio=audio, auth_methods=auth_methods)
        manager = _FakeManager(connection)
        created.append((command, args, kwargs, connection, manager, client))
        return manager

    sdk.spawn_agent_process = spawn_agent_process
    return sdk


def _write_config(path, *, policy="deny", auth_method=None):
    agent = {
        "command": "demo-acp",
        "args": ["--stdio"],
        "env": {"DEMO": "1"},
        "permission_policy": policy,
        "timeout_seconds": 10,
    }
    if auth_method is not None:
        agent["auth_method"] = auth_method
    path.write_text(
        json.dumps(
            {
                "default": "demo",
                "agents": {"demo": agent},
            }
        ),
        encoding="utf-8",
    )


def test_load_acp_config_validates_default_and_policy(tmp_path):
    path = tmp_path / "acp.json"
    _write_config(path, policy="allow_once")

    config = load_acp_config(path)

    assert config.default_agent == "demo"
    assert config.agents["demo"].args == ("--stdio",)
    assert config.agents["demo"].permission_policy == "allow_once"

    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["agents"]["demo"]["permission_policy"] = "ask"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(AcpConfigurationError, match="permission_policy"):
        load_acp_config(path)


def test_load_acp_config_inherits_only_explicit_environment(tmp_path, monkeypatch):
    path = tmp_path / "acp.json"
    _write_config(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["agents"]["demo"]["env"] = {}
    raw["agents"]["demo"]["inherit_env"] = ["DEMO_API_KEY"]
    path.write_text(json.dumps(raw), encoding="utf-8")
    monkeypatch.setenv("DEMO_API_KEY", "secret")

    agent = load_acp_config(path).agents["demo"]

    assert agent.environment == {"DEMO_API_KEY": "secret"}
    monkeypatch.delenv("DEMO_API_KEY")
    with pytest.raises(AcpConfigurationError, match="DEMO_API_KEY"):
        _ = agent.environment


@pytest.mark.asyncio
async def test_service_reuses_session_and_keeps_only_final_agent_messages(tmp_path):
    config_path = tmp_path / "acp.json"
    _write_config(config_path)
    created = []
    sdk = _fake_sdk(created)
    service = AcpAgentService(root_dir=tmp_path / "cache", config_path=config_path, sdk_loader=lambda: sdk)
    progress = []

    async def reporter(event):
        progress.append(event)

    media = (AcpInputMedia(kind="image", data=b"input", mime_type="image/png"),)
    first = await service.run("first", workspace_key="dm:1", media=media, progress_reporter=reporter)
    second = await service.run("second", workspace_key="dm:1")

    assert first.final_response == second.final_response == "最终回复"
    assert first.artifacts[0].data == b"image-bytes"
    assert len(created) == 1
    _command, args, kwargs, connection, _manager, _client = created[0]
    assert args == ("--stdio",)
    assert kwargs["env"] == {"DEMO": "1"}
    assert len(connection.new_sessions) == 1
    assert connection.prompts[0][1][0].text == "first"
    assert connection.prompts[0][1][1].type == "image"
    assert [event.type for event in progress] == [
        "thinking",
        "assistant_preamble",
        "tool_call",
        "tool_result",
    ]

    await service.close()
    assert created[0][4].closed == 1


@pytest.mark.asyncio
async def test_service_omits_unadvertised_media_and_denies_permissions(tmp_path):
    config_path = tmp_path / "acp.json"
    _write_config(config_path)
    created = []
    sdk = _fake_sdk(created, image=False, audio=False)
    service = AcpAgentService(root_dir=tmp_path / "cache", config_path=config_path, sdk_loader=lambda: sdk)

    media = (
        AcpInputMedia(kind="image", data=b"input", mime_type="image/png"),
        AcpInputMedia(kind="audio", data=b"audio", mime_type="audio/wav"),
    )
    await service.run("inspect", workspace_key="dm:1", media=media)
    connection = created[0][3]
    prompt = connection.prompts[0][1]
    assert len(prompt) == 1
    assert "1 张图片" in prompt[0].text
    assert "1 段音频" in prompt[0].text

    client = created[0][5]
    response = await client.request_permission(
        "session-1",
        SimpleNamespace(),
        [SimpleNamespace(kind="allow_once", option_id="yes")],
    )
    assert response.outcome.outcome == "cancelled"
    await service.close()


@pytest.mark.asyncio
async def test_allow_once_policy_selects_only_allow_once_option(tmp_path):
    config_path = tmp_path / "acp.json"
    _write_config(config_path, policy="allow_once")
    created = []
    sdk = _fake_sdk(created)
    service = AcpAgentService(root_dir=tmp_path / "cache", config_path=config_path, sdk_loader=lambda: sdk)
    await service.run("inspect", workspace_key="dm:1")

    response = await created[0][5].request_permission(
        "session-1",
        SimpleNamespace(),
        [
            SimpleNamespace(kind="allow_always", option_id="always"),
            SimpleNamespace(kind="allow_once", option_id="once"),
        ],
    )

    assert response.outcome.outcome == "selected"
    assert response.outcome.option_id == "once"
    await service.close()


@pytest.mark.asyncio
async def test_service_uses_configured_auth_method_and_cleans_inactive_workspace(tmp_path):
    config_path = tmp_path / "acp.json"
    _write_config(config_path, auth_method="login")
    created = []
    sdk = _fake_sdk(created, auth_methods=("login",))
    service = AcpAgentService(root_dir=tmp_path / "cache", config_path=config_path, sdk_loader=lambda: sdk)

    await service.run("inspect", workspace_key="dm:1")
    scope_id = service._scope_id("dm:1")
    workspace = tmp_path / "cache" / "workspaces" / scope_id
    assert created[0][3].authentications == [{"method_id": "login"}]
    assert workspace.is_dir()

    assert await service.cleanup_cache() == 1
    assert created[0][4].closed == 1
    assert not workspace.exists()
    await service.close()


@pytest.mark.asyncio
async def test_acp_agent_adapts_service_result():
    class FakeService:
        async def run(self, *_args, **_kwargs):
            return SimpleNamespace(final_response="answer", stop_reason="end_turn", artifacts=())

    result = await AcpAgent(FakeService()).chat_agent("task", workspace_key="dm:1")

    assert result["response"]["messages"][0].content == "answer"
    assert result["uni_messages"] == []
    assert "error" not in result
