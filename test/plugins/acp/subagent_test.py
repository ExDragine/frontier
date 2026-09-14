# ruff: noqa: S101

import types
from typing import Any, cast

import pytest

from plugins.acp import subagent as acp_subagents
from plugins.acp.service import AcpAgentConfig, AcpArtifact, AcpRunResult


@pytest.mark.asyncio
async def test_acp_subagent_is_opt_in_and_persists_media(tmp_path):
    class FakeService:
        def __init__(self):
            self.calls = []

        def subagent_configs(self):
            return (
                (
                    "demo",
                    AcpAgentConfig(
                        command="demo-acp",
                        description="Delegate complex work",
                        expose_as_subagent=True,
                    ),
                ),
            )

        async def run(self, prompt, **kwargs):
            self.calls.append((prompt, kwargs))
            return AcpRunResult(
                final_response="delegated answer",
                stop_reason="end_turn",
                artifacts=(AcpArtifact("image", b"image-data", "image/png"),),
            )

    service = FakeService()
    subagents = acp_subagents.build_acp_subagents(cast(Any, service))
    result = await subagents[0]["runnable"].ainvoke(
        {"messages": [types.SimpleNamespace(content="do the work")]},
        config={
            "configurable": {
                "thread_id": "thread-1",
                "workspace_dir": str(tmp_path),
            }
        },
    )

    assert subagents[0]["name"] == "acp-demo"
    assert subagents[0]["description"] == "Delegate complex work"
    assert service.calls[0][0] == "do the work"
    assert service.calls[0][1]["workspace_key"] == "deepagent:thread-1:demo"
    assert "delegated answer" in result["messages"][0].content
    artifact_path = result["messages"][0].content.split("- /", 1)[1]
    assert (tmp_path / artifact_path).read_bytes() == b"image-data"
