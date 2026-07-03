# ruff: noqa: S101


import types

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebot_plugin_alconna import UniMessage
from nonebug import App

from plugins import toolbox
from plugins.toolbox import on_startup


@pytest.mark.asyncio
async def test_on_startup_creates_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "env.toml.example").write_text("", encoding="utf-8")
    (tmp_path / "mcp.json.example").write_text("{}", encoding="utf-8")
    (tmp_path / ".env.example").write_text("", encoding="utf-8")
    (tmp_path / "cache").mkdir()

    await on_startup()
    assert (tmp_path / "env.toml").exists()
    assert (tmp_path / "mcp.json").exists()
    assert (tmp_path / ".env").exists()


@pytest.mark.asyncio
async def test_handle_setting_default(monkeypatch):
    async def fake_message_extract(*_args, **_kwargs):
        return "", [], [], []

    monkeypatch.setattr("plugins.toolbox.message_extract", fake_message_extract)

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)

        incoming = IncomingMessage(
            message_scene="group",
            peer_id=123,
            message_seq=1,
            sender_id=456,
            time=0,
            segments=[{"type": "text", "data": {"text": "/model"}}],
            friend=None,
            group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
            group_member=Member(
                user_id=456,
                nickname="u",
                sex="unknown",
                group_id=123,
                card="",
                title="",
                level="0",
                role="member",
                join_time=0,
                last_sent_time=0,
                shut_up_end_time=0,
            ),
        )
        event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

        async def fake_send(self, *args, **kwargs):
            return None

        monkeypatch.setattr(UniMessage, "send", fake_send)
        ctx.receive_event(bot, event)
        ctx.should_finished()


def test_collect_update_commits_returns_empty_for_same_head():
    assert toolbox.collect_update_commits("abc", "abc") == []


def test_collect_update_commits_reads_git_range(monkeypatch):
    commits = [
        types.SimpleNamespace(hexsha="1234567890", summary="add changelog", message="add changelog\n\nbody one"),
        types.SimpleNamespace(hexsha="abcdef1234", summary="fix update", message="fix update\n\nbody two"),
    ]

    class DummyRepo:
        def iter_commits(self, rev, max_count):
            assert rev == "old..new"
            assert max_count == 20
            return commits

    monkeypatch.setattr(toolbox, "Repo", lambda *_args, **_kwargs: DummyRepo())

    result = toolbox.collect_update_commits("old", "new")

    assert [commit.short_hash for commit in result] == ["1234567", "abcdef1"]
    assert [commit.subject for commit in result] == ["add changelog", "fix update"]
    assert [commit.body for commit in result] == ["body one", "body two"]


def test_collect_update_commits_returns_empty_on_git_error(monkeypatch):
    class BrokenRepo:
        def iter_commits(self, *_args, **_kwargs):
            raise RuntimeError("git failed")

    monkeypatch.setattr(toolbox, "Repo", lambda *_args, **_kwargs: BrokenRepo())

    assert toolbox.collect_update_commits("old", "new") == []


@pytest.mark.asyncio
async def test_summarize_update_commits_calls_llm(monkeypatch):
    captured = {}

    async def fake_assistant_agent(system_prompt, user_prompt, **kwargs):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        captured["kwargs"] = kwargs
        return "- 新增更新日志"

    monkeypatch.setattr(toolbox, "_call_assistant_agent", fake_assistant_agent)

    result = await toolbox.summarize_update_commits(
        [
            toolbox.CommitInfo(short_hash="1234567", subject="add changelog", body="body"),
            toolbox.CommitInfo(short_hash="abcdef1", subject="fix update", body=""),
        ]
    )

    assert result == "- 新增更新日志"
    assert "add changelog" in captured["user_prompt"]
    assert "fix update" in captured["user_prompt"]
    assert captured["kwargs"]["tools"] is None
    assert captured["kwargs"]["temperature"] == 0


@pytest.mark.asyncio
async def test_summarize_update_commits_returns_none_on_llm_failure(monkeypatch):
    async def broken_assistant_agent(*_args, **_kwargs):
        raise RuntimeError("llm failed")

    monkeypatch.setattr(toolbox, "_call_assistant_agent", broken_assistant_agent)

    result = await toolbox.summarize_update_commits(
        [toolbox.CommitInfo(short_hash="1234567", subject="add changelog", body="")]
    )

    assert result is None


@pytest.mark.asyncio
async def test_handle_updater_persists_update_context_for_startup_changelog(monkeypatch):
    sent_texts = []

    class DummyMessage:
        def __init__(self, text):
            self.text = text

        async def send(self, *args, **kwargs):
            sent_texts.append(self.text)

    class DummyUniMessage:
        @classmethod
        def text(cls, text):
            return DummyMessage(text)

    class DummyGit:
        def __init__(self, repo):
            self.repo = repo

        def checkout(self):
            return None

        def pull(self, rebase):
            assert rebase is True
            self.repo.head.commit.hexsha = "new"
            return "updated"

    class DummyRepo:
        def __init__(self, *_args, **_kwargs):
            self.head = types.SimpleNamespace(commit=types.SimpleNamespace(hexsha="old"))
            self.git = DummyGit(self)

    event = types.SimpleNamespace(data=types.SimpleNamespace(group=types.SimpleNamespace(group_id=123)))

    monkeypatch.setattr(toolbox, "Repo", DummyRepo)
    monkeypatch.setattr(toolbox, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(toolbox.os, "kill", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(toolbox, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)), raising=False)

    with pytest.raises(SystemExit):
        await toolbox.handle_updater(event)

    assert "🔄 开始更新..." in sent_texts
    lock_info = toolbox.read_update_lock(open(".lock", encoding="utf-8").read())
    assert lock_info.old_head == "old"
    assert lock_info.trigger_group_id == 123


@pytest.mark.asyncio
async def test_on_bot_connect_sends_pending_changelog_to_trigger_group(monkeypatch):
    completion_targets = []
    changelog_targets = []

    class DummyMessage:
        def __init__(self, text):
            self.text = text

        async def send(self, *args, **kwargs):
            completion_targets.append(kwargs.get("target"))

    class DummyUniMessage:
        @classmethod
        def text(cls, text):
            return DummyMessage(text)

    commits = [toolbox.CommitInfo(short_hash="1234567", subject="add changelog", body="")]

    async def fake_summarize_update_commits(received_commits):
        assert received_commits == commits
        return "- 新增更新日志"

    async def fake_send_update_changelog(group_id, changelog):
        changelog_targets.append((group_id, changelog))

    (toolbox.Path(".") / ".lock").write_text(
        '{"start_time": 100, "old_head": "old", "trigger_group_id": 123}',
        encoding="utf-8",
    )
    monkeypatch.setattr(toolbox, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(toolbox.EnvConfig, "ANNOUNCE_GROUP_ID", [456])
    monkeypatch.setattr(toolbox.time, "time", lambda: 110)
    monkeypatch.setattr(toolbox, "Repo", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(toolbox, "_current_head", lambda _repo: "new")
    monkeypatch.setattr(toolbox, "collect_update_commits", lambda old, new: commits)
    monkeypatch.setattr(toolbox, "summarize_update_commits", fake_summarize_update_commits)
    monkeypatch.setattr(toolbox, "send_update_changelog", fake_send_update_changelog)

    await toolbox.on_bot_connect()

    assert not (toolbox.Path(".") / ".lock").exists()
    assert completion_targets
    assert changelog_targets == [(123, "- 新增更新日志")]


@pytest.mark.asyncio
async def test_on_bot_connect_sends_changelog_when_announce_group_send_fails(monkeypatch):
    changelog_targets = []

    class DummyMessage:
        async def send(self, *args, **kwargs):
            raise RuntimeError("announce send failed")

    class DummyUniMessage:
        @classmethod
        def text(cls, _text):
            return DummyMessage()

    commits = [toolbox.CommitInfo(short_hash="1234567", subject="add changelog", body="")]

    async def fake_summarize_update_commits(received_commits):
        assert received_commits == commits
        return "- 新增更新日志"

    async def fake_send_update_changelog(group_id, changelog):
        changelog_targets.append((group_id, changelog))

    (toolbox.Path(".") / ".lock").write_text(
        '{"start_time": 100, "old_head": "old", "trigger_group_id": 123}',
        encoding="utf-8",
    )
    monkeypatch.setattr(toolbox, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(toolbox.EnvConfig, "ANNOUNCE_GROUP_ID", [456])
    monkeypatch.setattr(toolbox.time, "time", lambda: 110)
    monkeypatch.setattr(toolbox, "Repo", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(toolbox, "_current_head", lambda _repo: "new")
    monkeypatch.setattr(toolbox, "collect_update_commits", lambda old, new: commits)
    monkeypatch.setattr(toolbox, "summarize_update_commits", fake_summarize_update_commits)
    monkeypatch.setattr(toolbox, "send_update_changelog", fake_send_update_changelog)

    await toolbox.on_bot_connect()

    assert changelog_targets == [(123, "- 新增更新日志")]


@pytest.mark.asyncio
async def test_handle_updater_skips_changelog_without_group(monkeypatch):
    class DummyMessage:
        async def send(self, *args, **kwargs):
            return None

    class DummyUniMessage:
        @classmethod
        def text(cls, _text):
            return DummyMessage()

    class DummyGit:
        def checkout(self):
            return None

        def pull(self, rebase):
            return "updated"

    class DummyRepo:
        def __init__(self, *_args, **_kwargs):
            self.head = types.SimpleNamespace(commit=types.SimpleNamespace(hexsha="old"))
            self.git = DummyGit()

    async def fail_send_update_changelog(*_args, **_kwargs):
        raise AssertionError("private update should not send group changelog")

    event = types.SimpleNamespace(data=types.SimpleNamespace(group=None))

    monkeypatch.setattr(toolbox, "Repo", DummyRepo)
    monkeypatch.setattr(toolbox, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(toolbox, "collect_update_commits", lambda old, new: [])
    monkeypatch.setattr(toolbox, "send_update_changelog", fail_send_update_changelog)
    monkeypatch.setattr(toolbox.os, "kill", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(toolbox, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)), raising=False)

    with pytest.raises(SystemExit):
        await toolbox.handle_updater(event)


@pytest.mark.asyncio
async def test_handle_updater_skips_changelog_when_no_new_commits(monkeypatch):
    class DummyMessage:
        async def send(self, *args, **kwargs):
            return None

    class DummyUniMessage:
        @classmethod
        def text(cls, _text):
            return DummyMessage()

    class DummyGit:
        def checkout(self):
            return None

        def pull(self, rebase):
            return "Already up to date."

    class DummyRepo:
        def __init__(self, *_args, **_kwargs):
            self.head = types.SimpleNamespace(commit=types.SimpleNamespace(hexsha="same"))
            self.git = DummyGit()

    async def fail_summarize_update_commits(*_args, **_kwargs):
        raise AssertionError("no new commits should not be summarized")

    async def fail_send_update_changelog(*_args, **_kwargs):
        raise AssertionError("no new commits should not send changelog")

    event = types.SimpleNamespace(data=types.SimpleNamespace(group=types.SimpleNamespace(group_id=123)))

    monkeypatch.setattr(toolbox, "Repo", DummyRepo)
    monkeypatch.setattr(toolbox, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(toolbox, "summarize_update_commits", fail_summarize_update_commits)
    monkeypatch.setattr(toolbox, "send_update_changelog", fail_send_update_changelog)
    monkeypatch.setattr(toolbox.os, "kill", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(toolbox, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)), raising=False)

    with pytest.raises(SystemExit):
        await toolbox.handle_updater(event)


@pytest.mark.asyncio
async def test_handle_updater_skips_changelog_when_update_fails(monkeypatch):
    sent_texts = []

    class DummyMessage:
        def __init__(self, text):
            self.text = text

        async def send(self, *args, **kwargs):
            sent_texts.append(self.text)

    class DummyUniMessage:
        @classmethod
        def text(cls, text):
            return DummyMessage(text)

    class DummyGit:
        def checkout(self):
            return None

        def pull(self, rebase):
            raise RuntimeError("pull failed")

    class DummyRepo:
        def __init__(self, *_args, **_kwargs):
            self.head = types.SimpleNamespace(commit=types.SimpleNamespace(hexsha="old"))
            self.git = DummyGit()

    async def fail_send_update_changelog(*_args, **_kwargs):
        raise AssertionError("failed update should not send changelog")

    event = types.SimpleNamespace(data=types.SimpleNamespace(group=types.SimpleNamespace(group_id=123)))

    monkeypatch.setattr(toolbox, "Repo", DummyRepo)
    monkeypatch.setattr(toolbox, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(toolbox, "send_update_changelog", fail_send_update_changelog)

    await toolbox.handle_updater(event)

    assert not (toolbox.Path(".") / ".lock").exists()
    assert "❌ 更新失败: pull failed" in sent_texts
