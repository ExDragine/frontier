# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from utils.agent_context import FrontierRuntimeContext
from utils.media_access import MEDIA_ACCESS_DENIED


@pytest.fixture(params=["paint", "video"])
def media_tool(request, load_tool_module, monkeypatch):
    module = load_tool_module(request.param)
    for name, value in {
        "PAINT_MODULE_ENABLED": True,
        "VIDEO_MODULE_ENABLED": True,
        "PAINT_WHITELIST_MODE": True,
        "PAINT_WHITELIST_PERSON_LIST": [],
        "PAINT_WHITELIST_GROUP_LIST": [],
        "PAINT_BLACKLIST_PERSON_LIST": [],
        "PAINT_BLACKLIST_GROUP_LIST": [],
    }.items():
        monkeypatch.setattr(module.EnvConfig, name, value)
    return module, getattr(module, f"get_{request.param}")


@pytest.mark.asyncio
@pytest.mark.parametrize("policy, identity", [
    ({}, {}),
    ({}, {"user_id": "456", "group_id": 123}),
    ({"PAINT_WHITELIST_PERSON_LIST": [789]}, {"user_id": "456"}),
    ({"PAINT_WHITELIST_GROUP_LIST": [999]}, {"user_id": "456", "group_id": 123}),
    ({"PAINT_WHITELIST_GROUP_LIST": [0, "0"]}, {"user_id": "456", "group_id": 0}),
    ({"PAINT_WHITELIST_PERSON_LIST": [456], "PAINT_BLACKLIST_PERSON_LIST": ["456"]}, {"user_id": "456"}),
    ({"PAINT_WHITELIST_PERSON_LIST": [456], "PAINT_BLACKLIST_GROUP_LIST": ["123"]}, {"user_id": "456", "group_id": 123}),
    ({"PAINT_WHITELIST_GROUP_LIST": [123], "PAINT_BLACKLIST_PERSON_LIST": [456]}, {"user_id": "456", "group_id": "123"}),
    ({"PAINT_WHITELIST_MODE": False, "PAINT_BLACKLIST_PERSON_LIST": [456]}, {"user_id": "456"}),
    ({"PAINT_WHITELIST_MODE": False, "PAINT_BLACKLIST_GROUP_LIST": [123]}, {"user_id": "456", "group_id": "123"}),
])
async def test_denied_media_tools_stop_before_media_processing(media_tool, monkeypatch, policy, identity):
    module, invoke = media_tool
    for name, value in policy.items():
        monkeypatch.setattr(module.EnvConfig, name, value)

    def unexpected_state(_state):
        pytest.fail("denied media tool inspected media or consumed rate limit")

    monkeypatch.setattr(module, "ToolStateView", unexpected_state)
    text, artifact = await invoke("a cat", config={"configurable": identity})

    assert text == MEDIA_ACCESS_DENIED
    assert artifact is None


@pytest.mark.asyncio
@pytest.mark.parametrize("policy, identity", [
    ({"PAINT_WHITELIST_MODE": False}, {}),
    ({"PAINT_WHITELIST_PERSON_LIST": [456]}, {"user_id": "456"}),
    ({"PAINT_WHITELIST_PERSON_LIST": ["456"]}, {"user_id": 456, "group_id": 999}),
    ({"PAINT_WHITELIST_GROUP_LIST": [123]}, {"user_id": "456", "group_id": "123"}),
    ({"PAINT_WHITELIST_GROUP_LIST": ["123"]}, {"user_id": "456", "group_id": 123}),
])
async def test_allowed_media_tools_generate(media_tool, monkeypatch, policy, identity):
    module, invoke = media_tool
    for name, value in policy.items():
        monkeypatch.setattr(module.EnvConfig, name, value)
    calls = []

    async def fake_paint(prompt, images):
        calls.append(prompt)
        return b"image"

    async def fake_video(prompt, **_kwargs):
        calls.append(prompt)
        return SimpleNamespace(raw=b"video")

    service = "paint" if invoke.name == "get_paint" else "generate_video"
    monkeypatch.setattr(module, service, fake_paint if service == "paint" else fake_video)
    text, artifact = await invoke("a cat", config={"configurable": identity})

    assert calls == ["a cat"]
    assert text != MEDIA_ACCESS_DENIED
    assert artifact is not None


@pytest.mark.asyncio
async def test_media_tool_ignores_whitelisted_mutable_state(media_tool, monkeypatch):
    module, invoke = media_tool
    monkeypatch.setattr(module.EnvConfig, "PAINT_WHITELIST_PERSON_LIST", [456])
    monkeypatch.setattr(module.EnvConfig, "PAINT_WHITELIST_GROUP_LIST", [123])

    text, artifact = await invoke("a cat", state={"user_id": "456", "group_id": 123})

    assert text == MEDIA_ACCESS_DENIED
    assert artifact is None


@pytest.mark.asyncio
async def test_media_tool_prefers_frozen_identity_to_config(media_tool, monkeypatch):
    module, invoke = media_tool
    monkeypatch.setattr(module.EnvConfig, "PAINT_WHITELIST_PERSON_LIST", [456])
    monkeypatch.setattr(module.EnvConfig, "PAINT_WHITELIST_GROUP_LIST", [123])
    runtime = SimpleNamespace(context=FrontierRuntimeContext("789", 999, None, "."))

    text, artifact = await invoke(
        "a cat",
        config={"configurable": {"user_id": "456", "group_id": 123}},
        runtime=runtime,
    )

    assert text == MEDIA_ACCESS_DENIED
    assert artifact is None


def test_media_tool_schema_hides_identity_and_runtime(media_tool):
    _module, invoke = media_tool
    assert not {"state", "runtime", "user_id", "group_id"} & invoke.args.keys()
