# ruff: noqa: S101
"""Verify isolated imports and real NoneBot registration after component moves."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _run(tmp_path, script):
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(_ROOT), "FRONTIER_CONFIG": str(tmp_path / "env.toml")},
        capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_message_components_import_without_registering_plugins(tmp_path):
    _run(tmp_path, """
import sys
from plugins.agent import attachments, chat_context, gateway, message_normalizer, reply_context
import plugins.toolbox
assert 'plugins.agent.handlers' not in sys.modules
assert 'plugins.toolbox.settings' not in sys.modules
assert 'plugins.toolbox.update' not in sys.modules
assert 'plugins.acp.commands' not in sys.modules
import nonebot
try:
    nonebot.get_driver()
except ValueError:
    pass
else:
    raise AssertionError('Importing message components initialized NoneBot')
""")


@pytest.mark.parametrize("first,second", [
    ("plugins.agent", "plugins.toolbox"),
    ("plugins.toolbox", "plugins.agent"),
])
def test_nonebot_registers_moved_commands_in_either_order(tmp_path, first, second):
    _run(tmp_path, f"""
import nonebot
nonebot.init(driver='nonebot.drivers.fastapi:Driver', log_level='WARNING')
assert nonebot.load_plugin({first!r}) is not None
assert nonebot.load_plugin({second!r}) is not None
from plugins.agent import handlers
from plugins.toolbox import menu, settings, update
agent = nonebot.get_plugin('agent')
toolbox = nonebot.get_plugin('toolbox')
assert handlers.common in agent.matcher
assert handlers.group_disband in agent.matcher
assert all(command in toolbox.matcher for command in (
    menu.vehelp_cmd, settings.model_cmd, settings.settings, update.updater, update.restart,
))
assert nonebot.require('plugins.agent') is agent.module
assert nonebot.require('plugins.toolbox') is toolbox.module
""")
