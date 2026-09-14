# ruff: noqa: S101
"""Exercise Frontier client/server through the official SDK and real stdio."""

import asyncio
import json
import sys
from pathlib import Path

import pytest
from acp.experimental.v2 import schema

from plugins.acp.service import AcpAgentService, AcpInputMedia

_PEER = Path(__file__).resolve().parents[1] / "fixtures" / "acp_contract_agent.py"


def _configure(path, tmp_path, version, *, timeout=10, peer_version=None):
    path.write_text(json.dumps({"default": "test", "agents": {"test": {
        "command": sys.executable,
        "args": [str(_PEER), str(peer_version or version)],
        "env": {"FRONTIER_CONFIG": str(tmp_path / "env.toml")},
        "protocol_version": version,
        "timeout_seconds": timeout,
    }}}))


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [1, 2])
async def test_real_stdio_protocol_roundtrip_and_cancel(tmp_path, version):
    path = tmp_path / "acp.json"
    _configure(path, tmp_path, version)
    service = AcpAgentService(root_dir=tmp_path / "workspace", config_path=path)
    try:
        result = await asyncio.wait_for(service.run(
            "hello", workspace_key="group:1", media=(AcpInputMedia("image", b"image", "image/png"),),
        ), 15)
        assert result.final_response == "echo:hello"
        assert result.artifacts[0].data == b"contract-image"
        assert result.stop_reason == "end_turn"
        runtime = next(iter(service._runtimes.values()))
        second = await service.run("again", workspace_key="group:1")
        assert second.final_response == "echo:again"
        assert next(iter(service._runtimes.values())) is runtime
        if version == 2:
            native = runtime.connection.connection
            listed = await native.list_sessions(schema.ListSessionsRequest())
            assert [session.session_id for session in listed.sessions] == [runtime.session_id]
            replayed = []
            original_update = runtime.client.session_update

            async def record(notification):
                replayed.append(notification.update)
                await original_update(notification)

            runtime.client.session_update = record
            await native.close_session(schema.CloseSessionRequest(session_id=runtime.session_id))
            await native.resume_session(schema.ResumeSessionRequest(
                session_id=runtime.session_id, cwd=listed.sessions[0].cwd,
            ))
            assert replayed == []
            await native.resume_session(schema.ResumeSessionRequest(
                session_id=runtime.session_id, cwd=listed.sessions[0].cwd,
                replay_from=schema.ReplayFromStartVariant(),
            ))
            assert sum(update.session_update == "user_message" for update in replayed) == 2
            assert replayed[-1].state == "idle"
            assert replayed[-1].stop_reason == "end_turn"
        thinking = asyncio.Event()

        async def report(event):
            if event.type == "thinking":
                thinking.set()

        pending = asyncio.create_task(service.run("wait", workspace_key="group:1", progress_reporter=report))
        await asyncio.wait_for(thinking.wait(), 10)
        assert not pending.done()  # v2 ACK is not completion
        assert await service.cancel(workspace_key="group:1") == 1
        cancelled = await asyncio.wait_for(pending, 10)
        assert cancelled.stop_reason == "cancelled"
    finally:
        processes = [runtime.process for runtime in service._runtimes.values()]
        await service.close()
        assert all(process.returncode is not None for process in processes)


@pytest.mark.asyncio
async def test_protocol_config_change_restarts_runtime(tmp_path):
    path = tmp_path / "acp.json"
    _configure(path, tmp_path, 1)
    service = AcpAgentService(root_dir=tmp_path / "workspace", config_path=path)
    try:
        await service.run("v1", workspace_key="dm:1")
        old = next(iter(service._runtimes.values()))
        _configure(path, tmp_path, 2)
        result = await service.run("v2", workspace_key="dm:1")
        assert result.final_response == "echo:v2"
        assert next(iter(service._runtimes.values())) is not old
        assert old.process.returncode is not None
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_v2_timeout_discards_process_and_allows_retry(tmp_path):
    path = tmp_path / "acp.json"
    _configure(path, tmp_path, 2, timeout=1)
    service = AcpAgentService(root_dir=tmp_path / "workspace", config_path=path)
    try:
        await service.run("warmup", workspace_key="group:1")
        old = next(iter(service._runtimes.values()))
        with pytest.raises(TimeoutError):
            await service.run("wait", workspace_key="group:1")
        assert service._runtimes == {}
        assert old.process.returncode is not None
        result = await service.run("retry", workspace_key="group:1")
        assert result.final_response == "echo:retry"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_v2_rejects_v1_peer_without_running_prompt(tmp_path):
    path = tmp_path / "acp.json"
    _configure(path, tmp_path, 2, peer_version=1)
    service = AcpAgentService(root_dir=tmp_path / "workspace", config_path=path)
    try:
        with pytest.raises(Exception, match="info|protocol|version"):
            await service.run("must not run", workspace_key="dm:1")
        assert service._runtimes == {}
    finally:
        await service.close()
