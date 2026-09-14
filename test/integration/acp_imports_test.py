# ruff: noqa: S101
"""ACP package must support both NoneBot loading and standalone Python imports."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _run(tmp_path, *args):
    env = {**os.environ, "PYTHONPATH": str(_ROOT), "FRONTIER_CONFIG": str(tmp_path / "env.toml")}
    result = subprocess.run(  # noqa: S603
        [sys.executable, *args], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_protocol_imports_do_not_register_nonebot_commands(tmp_path):
    _run(tmp_path, "-c", """
import sys
from plugins.acp import AcpAgent, AcpAgentService, FrontierAcpServer, FrontierAcpV2Server
from plugins.acp.client_v2 import FrontierAcpV2Client
from plugins.acp.subagent import build_acp_subagents
assert 'plugins.acp.commands' not in sys.modules
assert 'plugins.acp.lifecycle' not in sys.modules
import nonebot
try:
    nonebot.get_driver()
except ValueError:
    pass
else:
    raise AssertionError('ACP imports initialized NoneBot')
"""
    )


def test_nonebot_load_registers_acp_command_and_lifecycle(tmp_path):
    _run(tmp_path, "-c", """
import nonebot
nonebot.init(driver='nonebot.drivers.fastapi:Driver', log_level='WARNING')
plugin = nonebot.load_plugin('plugins.acp')
assert plugin is not None
from plugins.acp import commands, lifecycle, acp_service
assert commands.acp_command in plugin.matcher
assert commands.acp_agent.service is acp_service
assert lifecycle.acp_service is acp_service
assert nonebot.require('plugins.acp') is plugin.module
"""
    )


@pytest.mark.parametrize("entrypoint", [
    ["-m", "plugins.acp"],
    [str(_ROOT / "scripts/frontier_acp.py")],
])
def test_stdio_cli_help_needs_no_configuration(tmp_path, entrypoint):
    empty_dir = tmp_path / "no-config"
    empty_dir.mkdir()
    result = _run(empty_dir, *entrypoint, "--help")
    assert "--protocol-version {1,2}" in result.stdout
    assert "NoneBot" not in result.stdout
