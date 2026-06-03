# ruff: noqa: S101

import pytest

from policy.policies.access_control import AccessControlPolicy
from policy.decisions import Verdict
from policy.snapshots import InputSnapshot


def _snap(**overrides) -> InputSnapshot:
    defaults = dict(
        user_id="12345",
        group_id=1,
        chat_type="group",
        text="hello",
        is_at_bot=False,
        is_bot_name_prefix=False,
    )
    defaults.update(overrides)
    return InputSnapshot(**defaults)


@pytest.mark.asyncio
async def test_at_bot_is_allowed():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(is_at_bot=True)
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_bot_name_prefix_is_allowed():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(is_bot_name_prefix=True)
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_blacklist_denies():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [12345], "blacklist_groups": [], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "user_blacklisted"


@pytest.mark.asyncio
async def test_blacklist_group_denies():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [1], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "group_blacklisted"


@pytest.mark.asyncio
async def test_whitelist_mode_denies_unknown():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [99999], "whitelist_groups": [99999], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "not_whitelisted"


@pytest.mark.asyncio
async def test_whitelist_mode_allows_known_user():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [12345], "whitelist_groups": [], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_dm_allowed_when_person_whitelisted():
    """私聊时 group_id=None，只要用户在个人白名单中即可放行。"""
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [12345], "whitelist_groups": [99999], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(group_id=None, chat_type="private")
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_dm_denied_when_person_not_whitelisted():
    """私聊时 group_id=None，用户不在个人白名单中应拒绝。"""
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [99999], "whitelist_groups": [], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(group_id=None, chat_type="private")
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.DENY


@pytest.mark.asyncio
async def test_test_group_denies():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": [1]})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "test_group_no_reply"


@pytest.mark.asyncio
async def test_output_snapshot_skips():
    """非 InputSnapshot 时直接放行。"""
    from policy.snapshots import OutputSnapshot
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = OutputSnapshot(user_id="u1", group_id=None, text="response")
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW
