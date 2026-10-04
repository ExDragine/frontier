# ruff: noqa: S101
"""Exercise the real DeepAgents RubricMiddleware outside repository stubs."""

import subprocess
import sys
from pathlib import Path


def test_real_rubric_lifecycle_and_failure_modes(tmp_path):
    script = r'''
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

from deepagents import RubricMiddleware
from deepagents.middleware.rubric import GraderResponse
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage


class MainModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class ScriptedRubric(RubricMiddleware):
    def __init__(self, verdicts, **kwargs):
        super().__init__(model="scripted-grader", **kwargs)
        self.verdicts = iter(verdicts)
        self.grader_calls = 0

    async def _ainvoke_grader(self, state, iteration, correction=None, context=None):
        del state, iteration, correction, context
        self.grader_calls += 1
        verdict = next(self.verdicts)
        if isinstance(verdict, BaseException):
            raise verdict
        return verdict


def verdict(result, *, passed):
    criteria = [{"name": "direct", "passed": passed}]
    if not passed:
        criteria[0]["gap"] = "answer the request directly"
    return GraderResponse(result=result, explanation=result, criteria=criteria)


async def run_agent(responses, verdicts, *, rubric=True, max_iterations=2):
    evaluations = []
    middleware = ScriptedRubric(
        verdicts,
        max_iterations=max_iterations,
        on_evaluation=evaluations.append,
    )
    agent = create_agent(
        model=MainModel(responses=responses),
        middleware=[middleware],
    )
    payload = {"messages": [{"role": "user", "content": "answer this"}]}
    if rubric:
        payload["rubric"] = "respond directly"
    result = await agent.ainvoke(payload)
    return result, middleware, evaluations


async def main():
    result, middleware, evaluations = await run_agent(
        [AIMessage(content="clear answer")],
        [verdict("satisfied", passed=True)],
    )
    assert result["messages"][-1].content == "clear answer"
    assert middleware.grader_calls == 1
    assert [item["result"] for item in evaluations] == ["satisfied"]

    result, middleware, evaluations = await run_agent(
        [AIMessage(content="incomplete"), AIMessage(content="complete")],
        [verdict("needs_revision", passed=False), verdict("satisfied", passed=True)],
    )
    assert result["messages"][-1].content == "complete"
    assert middleware.grader_calls == 2
    assert [item["result"] for item in evaluations] == ["needs_revision", "satisfied"]
    assert any(getattr(message, "name", None) == "rubric_grader" for message in result["messages"])

    result, middleware, evaluations = await run_agent(
        [AIMessage(content="last answer"), AIMessage(content="revised answer")],
        [verdict("needs_revision", passed=False), verdict("needs_revision", passed=False)],
        max_iterations=2,
    )
    assert result["messages"][-1].content == "revised answer"
    assert middleware.grader_calls == 2
    assert evaluations[-1]["result"] == "max_iterations_reached"

    result, middleware, evaluations = await run_agent(
        [AIMessage(content="provider answer")],
        [RuntimeError("grader unavailable")],
    )
    assert result["messages"][-1].content == "provider answer"
    assert middleware.grader_calls == 1
    assert evaluations[0]["result"] == "grader_error"

    result, middleware, evaluations = await run_agent(
        [AIMessage(content="ungraded answer")],
        [],
        rubric=False,
    )
    assert result["messages"][-1].content == "ungraded answer"
    assert middleware.grader_calls == 0
    assert evaluations == []


asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603 - fixed in-process contract script
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
