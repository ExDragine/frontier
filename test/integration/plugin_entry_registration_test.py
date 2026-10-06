# ruff: noqa: S101
"""Package entries stay inert on plain import and register under the NoneBot loader."""

import os
import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _run(tmp_path, script):
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(_ROOT), "FRONTIER_CONFIG": str(tmp_path / "env.toml")},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_package_entries_register_nothing_on_plain_import(tmp_path):
    _run(tmp_path, """
import sys

from plugins.agent import attachments, chat_context, gateway, message_normalizer, reply_context
import plugins.clockwork
import plugins.dashboard
import plugins.playground
import plugins.wolfx

assert 'plugins.agent.handlers' not in sys.modules
assert 'plugins.playground.commands' not in sys.modules
assert 'plugins.clockwork.runtime' not in sys.modules
assert not hasattr(plugins.playground, 'paint_entry')
assert not hasattr(plugins.playground, 'notice')
assert not hasattr(plugins.clockwork, 'task_manager')
assert not hasattr(plugins.clockwork, 'engine')
assert not hasattr(plugins.dashboard, 'mount_dashboard')
assert not hasattr(plugins.wolfx, 'start_wolfx_service')

import nonebot
try:
    nonebot.get_driver()
except ValueError:
    pass
else:
    raise AssertionError('Importing plugin packages initialized NoneBot')
""")


@pytest.mark.parametrize("plugin", ["playground", "wolfx", "dashboard", "clockwork"])
def test_nonebot_loader_registers_each_package_entry(tmp_path, plugin):
    _run(tmp_path, f"""
import os
import pathlib

# The entries read EnvConfig while registering, so give them a v2 file.
pathlib.Path(os.environ['FRONTIER_CONFIG']).write_text('config_version = 2\\n', encoding='utf-8')

import nonebot
nonebot.init(driver='nonebot.drivers.fastapi:Driver', log_level='WARNING')
assert nonebot.load_plugin('plugins.{plugin}') is not None

if {plugin!r} == 'playground':
    from plugins.playground import commands
    registered = nonebot.get_plugin('playground').matcher
    assert commands.paint_entry in registered
    assert commands.notice in registered
elif {plugin!r} == 'wolfx':
    from plugins.wolfx import start_wolfx_service, stop_wolfx_service
    assert callable(start_wolfx_service) and callable(stop_wolfx_service)
elif {plugin!r} == 'dashboard':
    from plugins.dashboard import mount_dashboard
    assert callable(mount_dashboard)
else:
    from plugins.clockwork import runtime, task_manager
    assert task_manager is runtime.task_manager_instance
    assert callable(runtime.init_task_system)
    assert callable(runtime.shutdown_task_system)
""")
