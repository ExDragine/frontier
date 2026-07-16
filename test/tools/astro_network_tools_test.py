# ruff: noqa: S101

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_aurora_live_success_and_failure(load_tool_module, monkeypatch):
    mod = load_tool_module("aurora")

    text, artifact = await mod.aurora_live()
    assert "成功获取北极光实时图像" in text
    assert artifact.content["type"] == "image"

    def broken_image(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod.UniMessage, "image", broken_image)
    text2, artifact2 = await mod.aurora_live()
    assert "失败" in text2
    assert artifact2 is None


@pytest.mark.asyncio
async def test_comet_tool_info_and_list(load_tool_module, monkeypatch):
    mod = load_tool_module("comet")

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    class DummyClient:
        async def get(self, url, params):
            if "comet.api" in url:
                return DummyResp({"object": {"fullname": "C/2023 A3", "current_mag": 2.3}})
            return DummyResp({"objects": [{"fullname": "C/2023 A3"}, {"fullname": "1P/Halley"}]})

    monkeypatch.setattr(mod, "httpx_client", DummyClient())
    assert "C/2023 A3" in await mod.comet_information("A3")
    assert "1P/Halley" in await mod.comet_list()


@pytest.mark.asyncio
async def test_comet_tool_error(load_tool_module, monkeypatch):
    mod = load_tool_module("comet")

    class BadClient:
        async def get(self, *_args, **_kwargs):
            raise RuntimeError("network down")

    monkeypatch.setattr(mod, "httpx_client", BadClient())
    assert "失败" in await mod.comet_information("A3")
    assert "失败" in await mod.comet_list()


@pytest.mark.asyncio
async def test_station_location(load_tool_module, monkeypatch):
    mod = load_tool_module("heavens_above")

    class DummyResp:
        content = b"img"

    class DummyClient:
        async def get(self, *_args, **_kwargs):
            return DummyResp()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())
    text, artifact = await mod.station_location("国际空间站")
    assert text.startswith("空间站位置获取成功")
    assert artifact.content["raw"] == b"img"


@pytest.mark.asyncio
async def test_station_location_empty_content(load_tool_module, monkeypatch):
    mod = load_tool_module("heavens_above")

    class DummyResp:
        content = b""

    class DummyClient:
        async def get(self, *_args, **_kwargs):
            return DummyResp()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())
    text, artifact = await mod.station_location("天宫")
    assert text == "空间站位置获取失败"
    assert artifact is None


@pytest.mark.asyncio
async def test_get_launches_success(load_tool_module, monkeypatch):
    mod = load_tool_module("rocket")
    launch_time = datetime.now(UTC) + timedelta(hours=1)

    class DummyResp:
        status_code = 200

        def json(self):
            return {
                "pagination": {"total": 1},
                "data": [
                    {
                        "name": "Falcon 9 | Starlink",
                        "site": "LC-39A",
                        "provider": "SpaceX",
                        "launch_date": launch_time.isoformat(),
                    }
                ],
            }

    class DummyClient:
        async def get(self, *args, **kwargs):
            return DummyResp()

    monkeypatch.setattr(mod, "http_client", DummyClient())
    result = await mod.get_launches(days=1)
    assert "未来 1 天共有 1 次发射计划" in result
    assert "Falcon 9" in result


@pytest.mark.asyncio
async def test_get_launches_http_error(load_tool_module, monkeypatch):
    mod = load_tool_module("rocket")

    class DummyResp:
        status_code = 503

    class DummyClient:
        async def get(self, *args, **kwargs):
            return DummyResp()

    monkeypatch.setattr(mod, "http_client", DummyClient())
    result = await mod.get_launches(days=1)
    assert "请求失败: 503" in result
