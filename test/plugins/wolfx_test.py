# ruff: noqa: S101

import asyncio
import datetime
import importlib
import json
import sys
import types
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "plugins"

plugins_pkg = types.ModuleType("plugins")
plugins_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("plugins", plugins_pkg)

wolfx_pkg = types.ModuleType("plugins.wolfx")
wolfx_pkg.__path__ = [str(PACKAGE_ROOT / "wolfx")]
sys.modules.setdefault("plugins.wolfx", wolfx_pkg)

cenc_client = importlib.import_module("plugins.wolfx.cenc_client")
cenc_handler = importlib.import_module("plugins.wolfx.cenc_handler")

CENC_PING_COMMAND = cenc_client.CENC_PING_COMMAND
CENC_QUERY_COMMAND = cenc_client.CENC_QUERY_COMMAND
CencWebSocketService = cenc_client.CencWebSocketService


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []

    async def send(self, message):
        self.sent.append(message)

    async def recv(self):
        message = self.messages.pop(0)
        if isinstance(message, BaseException):
            raise message
        return message


class FakeEventDatabase:
    def __init__(self):
        self.value = None

    async def select(self, name):
        assert name == "eq_cenc"
        return self.value

    async def insert(self, name, event_id):
        assert name == "eq_cenc"
        self.value = event_id

    async def update(self, name, event_id):
        assert name == "eq_cenc"
        self.value = event_id


def _cenc_payload(
    *,
    event_id="event-1",
    report_id="report-1",
    report_num=1,
    report_time="2026-07-21 12:00:00",
    magnitude=4.2,
):
    return {
        "type": "cenc_eew",
        "ID": report_id,
        "EventID": event_id,
        "ReportTime": report_time,
        "ReportNum": report_num,
        "OriginTime": "2026-07-21 11:59:30",
        "HypoCenter": "测试震中",
        "Latitude": 30.5,
        "Longitude": 104.1,
        "Magnitude": magnitude,
        "Depth": None,
        "MaxIntensity": None,
    }


@pytest.mark.asyncio
async def test_consume_queries_handles_heartbeat_and_survives_handler_error():
    events = []

    async def handler(data, *, is_snapshot):
        events.append((data["EventID"], is_snapshot))
        if data["EventID"] == "event-1":
            raise RuntimeError("bad event")

    websocket = FakeWebSocket(
        [
            json.dumps({"type": "heartbeat", "timestamp": "1"}),
            json.dumps({"type": "pong", "timestamp": "2"}),
            json.dumps({"type": "unknown"}),
            b"binary",
            "not-json",
            json.dumps(["not", "an", "object"]),
            json.dumps({"type": "cenc_eew", "EventID": "event-1"}),
            json.dumps({"type": "cenc_eew", "EventID": "event-2"}),
            asyncio.CancelledError(),
        ]
    )
    service = CencWebSocketService(receive_timeout=1)
    service._handler = handler

    with pytest.raises(asyncio.CancelledError):
        await service._consume(websocket)

    assert websocket.sent == [CENC_QUERY_COMMAND, CENC_PING_COMMAND]
    assert events == [("event-1", True), ("event-2", False)]


@pytest.mark.asyncio
async def test_connection_failures_use_exponential_backoff():
    attempts = []
    delays = []

    class FailingConnection:
        async def __aenter__(self):
            attempts.append("connect")
            raise OSError("offline")

        async def __aexit__(self, *_args):
            return False

    def connector(*_args, **_kwargs):
        return FailingConnection()

    async def sleep(delay):
        delays.append(delay)
        if len(delays) == 2:
            raise asyncio.CancelledError

    service = CencWebSocketService(
        connector=connector,
        sleep=sleep,
        jitter=lambda lower, _upper: lower,
    )

    with pytest.raises(asyncio.CancelledError):
        await service._run()

    assert attempts == ["connect", "connect"]
    assert delays == [0.75, 1.5]


@pytest.mark.asyncio
async def test_start_is_singleton_and_stop_cancels_listener(monkeypatch):
    service = CencWebSocketService()
    started = asyncio.Event()

    async def blocked_run():
        started.set()
        await asyncio.Future()

    async def handler(_data, *, is_snapshot):
        return is_snapshot

    monkeypatch.setattr(service, "_run", blocked_run)

    assert service.start(handler) is True
    assert service.start(handler) is False
    await started.wait()
    assert service.is_running is True

    await service.stop()

    assert service.is_running is False
    assert service.is_connected is False


@pytest.mark.asyncio
async def test_cenc_event_is_sent_once_and_continues_after_group_error(monkeypatch):
    database = FakeEventDatabase()
    rendered = []
    sent_targets = []

    async def fake_render(name, payload):
        rendered.append((name, payload))
        return b"earthquake-image"

    class DummyTarget:
        @staticmethod
        def group(group_id):
            return f"group:{group_id}"

    class DummyUniMessage:
        def image(self, *, raw):
            assert raw == b"earthquake-image"
            return self

        async def send(self, *, target):
            if target == "group:101":
                raise RuntimeError("send failed")
            sent_targets.append(target)

    monkeypatch.setattr(cenc_handler, "event_database", database)
    monkeypatch.setattr(cenc_handler, "playwright_render", fake_render)
    monkeypatch.setattr(cenc_handler, "Target", DummyTarget)
    monkeypatch.setattr(cenc_handler, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(cenc_handler.EnvConfig, "EARTHQUAKE_GROUP_ID", [101, 202])

    first = await cenc_handler.process_cenc_event(_cenc_payload())
    duplicate = await cenc_handler.process_cenc_event(
        _cenc_payload(report_id="report-2", report_num=2, magnitude=4.5)
    )

    assert not hasattr(cenc_handler, "httpx_client")
    assert json.loads(database.value) == ["event-1"]
    assert len(rendered) == 1
    assert rendered[0][0] == "eq_cenc"
    assert rendered[0][1]["depth"] is None
    assert sent_targets == ["group:202"]
    assert first.groups_sent == [202]
    assert duplicate.messages_sent == 0
    assert duplicate.output_summary == "cenc ignored: duplicate event"


@pytest.mark.asyncio
async def test_cenc_low_magnitude_can_be_promoted_by_later_report(monkeypatch):
    database = FakeEventDatabase()
    rendered = []

    async def fake_render(*_args, **_kwargs):
        rendered.append(True)
        return b"earthquake-image"

    class DummyUniMessage:
        def image(self, *, raw):
            return self

        async def send(self, *, target):
            raise AssertionError(f"no groups configured, unexpected target {target}")

    monkeypatch.setattr(cenc_handler, "event_database", database)
    monkeypatch.setattr(cenc_handler, "playwright_render", fake_render)
    monkeypatch.setattr(cenc_handler, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(cenc_handler.EnvConfig, "EARTHQUAKE_GROUP_ID", [])

    below_threshold = await cenc_handler.process_cenc_event(_cenc_payload(magnitude=2.9))
    promoted = await cenc_handler.process_cenc_event(
        _cenc_payload(report_id="report-2", report_num=2, magnitude=3.1)
    )

    assert below_threshold.output_summary == "cenc ignored: below threshold"
    assert json.loads(database.value) == ["event-1"]
    assert rendered == [True]
    assert promoted.output_summary == "cenc sent 0 group(s)"


@pytest.mark.asyncio
async def test_cenc_snapshot_freshness_and_invalid_payload(monkeypatch):
    database = FakeEventDatabase()
    rendered = []
    now_cn = datetime.datetime(2026, 7, 21, 12, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))

    async def fake_render(*_args, **_kwargs):
        rendered.append(True)
        return b"earthquake-image"

    class DummyUniMessage:
        def image(self, *, raw):
            return self

        async def send(self, *, target):
            raise AssertionError(f"no groups configured, unexpected target {target}")

    monkeypatch.setattr(cenc_handler, "event_database", database)
    monkeypatch.setattr(cenc_handler, "playwright_render", fake_render)
    monkeypatch.setattr(cenc_handler, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(cenc_handler.EnvConfig, "EARTHQUAKE_GROUP_ID", [])

    stale = await cenc_handler.process_cenc_event(
        _cenc_payload(event_id="stale", report_time="2026-07-21 12:00:00"),
        is_snapshot=True,
        now_cn=now_cn,
    )
    fresh = await cenc_handler.process_cenc_event(
        _cenc_payload(event_id="fresh", report_time="2026-07-21 12:25:00"),
        is_snapshot=True,
        now_cn=now_cn,
    )
    invalid_time = await cenc_handler.process_cenc_event(
        _cenc_payload(event_id="invalid-time", report_time="not-a-time"),
        is_snapshot=True,
        now_cn=now_cn,
    )
    invalid_payload = await cenc_handler.process_cenc_event({"type": "cenc_eew"})

    assert stale.output_summary == "cenc snapshot baseline stored"
    assert fresh.output_summary == "cenc sent 0 group(s)"
    assert invalid_time.output_summary == "cenc snapshot baseline stored"
    assert invalid_payload.output_summary == "cenc ignored: invalid payload"
    assert json.loads(database.value) == ["stale", "fresh", "invalid-time"]
    assert rendered == [True]


@pytest.mark.asyncio
async def test_cenc_dedup_history_blocks_late_revision_after_another_event(monkeypatch):
    database = FakeEventDatabase()
    rendered = []

    async def fake_render(*_args, **_kwargs):
        rendered.append(True)
        return b"earthquake-image"

    class DummyUniMessage:
        def image(self, *, raw):
            return self

        async def send(self, *, target):
            raise AssertionError(f"no groups configured, unexpected target {target}")

    monkeypatch.setattr(cenc_handler, "event_database", database)
    monkeypatch.setattr(cenc_handler, "playwright_render", fake_render)
    monkeypatch.setattr(cenc_handler, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(cenc_handler.EnvConfig, "EARTHQUAKE_GROUP_ID", [])

    await cenc_handler.process_cenc_event(_cenc_payload(event_id="event-a"))
    await cenc_handler.process_cenc_event(_cenc_payload(event_id="event-b"))
    late_revision = await cenc_handler.process_cenc_event(
        _cenc_payload(event_id="event-a", report_id="late-report", report_num=3, magnitude=4.8)
    )

    assert json.loads(database.value) == ["event-a", "event-b"]
    assert rendered == [True, True]
    assert late_revision.output_summary == "cenc ignored: duplicate event"
