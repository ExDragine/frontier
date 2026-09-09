# ruff: noqa: S101

import asyncio
from types import SimpleNamespace

import pytest
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError

from utils.agents.execution import managed_agent_turn
from utils.agents.tool_errors import ToolExecutionUncertainError, tool_error_middleware


def request(name):
    return SimpleNamespace(tool=None, tool_call={"name": name, "id": "call-1", "args": {}})


@pytest.mark.asyncio
async def test_query_error_is_sanitized_and_not_retried():
    calls = []

    async def fail(_request):
        calls.append(1)
        raise ValueError("secret-api-key /private/file")

    message = await tool_error_middleware(read_only_tools=["lookup"]).awrap_tool_call(request("lookup"), fail)
    assert calls == [1]
    assert message.status == "error"
    assert message.tool_call_id == "call-1"
    assert "参数" in message.content
    assert "secret" not in message.content
    assert "/private" not in message.content


@pytest.mark.asyncio
async def test_write_failure_halts_instead_of_inviting_repeat():
    calls = []

    async def fail(_request):
        calls.append(1)
        raise TimeoutError("platform response with secrets")

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None):
        await tool_error_middleware().awrap_tool_call(request("delete_group_file"), fail)
        raise AssertionError("must not continue")

    result = await turn([], "1", "User")
    assert calls == [1]
    assert result["error_code"] == "tool_execution_uncertain"
    assert "核实" in result["response"]["messages"][0].content
    assert "secrets" not in str(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [
    asyncio.CancelledError(),
    ModelCallLimitExceededError(1, 1, None, 1),
    ToolExecutionUncertainError("write"),
])
async def test_control_flow_and_budget_errors_propagate(error):
    async def fail(_request):
        raise error

    with pytest.raises(type(error)):
        await tool_error_middleware(all_read_only=True).awrap_tool_call(request("read_file"), fail)
