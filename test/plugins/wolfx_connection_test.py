# ruff: noqa: S101

import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest
from websockets.asyncio.client import ClientProtocol
from websockets.uri import parse_uri

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "plugins"
plugins_pkg = types.ModuleType("plugins")
plugins_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("plugins", plugins_pkg)
wolfx_pkg = types.ModuleType("plugins.wolfx")
wolfx_pkg.__path__ = [str(PACKAGE_ROOT / "wolfx")]
sys.modules.setdefault("plugins.wolfx", wolfx_pkg)

cenc_client = importlib.import_module("plugins.wolfx.cenc_client")


@pytest.mark.asyncio
async def test_safe_client_connection_handles_loss_before_connection_made():
    connection = cenc_client._SafeClientConnection(ClientProtocol(parse_uri("ws://localhost")))

    # websockets initializes recv_messages from connection_made. Simulate a
    # reset before that callback, which is the production failure path.
    assert not hasattr(connection, "recv_messages")
    connection.connection_lost(ConnectionResetError("peer reset"))

    assert connection.protocol.state.name == "CLOSED"


@pytest.mark.asyncio
async def test_closed_recv_assembler_is_idempotent():
    assembler = cenc_client._ClosedRecvAssembler()
    assembler.close()
    assembler.close()
    await asyncio.sleep(0)
