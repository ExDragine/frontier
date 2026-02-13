# ruff: noqa: S101

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


def test_comet_tool_info_and_list(load_tool_module):
    mod = load_tool_module("comet")

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    class DummyClient:
        def get(self, url, params):
            if "comet.api" in url:
                return DummyResp({"object": {"fullname": "C/2023 A3", "current_mag": 2.3}})
            return DummyResp({"objects": [{"fullname": "C/2023 A3"}, {"fullname": "1P/Halley"}]})

    tool = mod.CometTool(DummyClient())
    assert "C/2023 A3" in tool.info("A3")
    assert "1P/Halley" in tool.list()


def test_comet_tool_error(load_tool_module):
    mod = load_tool_module("comet")

    class BadClient:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("network down")

    tool = mod.CometTool(BadClient())
    assert "失败" in tool.info("A3")
    assert "失败" in tool.list()


@pytest.mark.asyncio
async def test_station_location(load_tool_module, monkeypatch):
    mod = load_tool_module("heavens_above")

    class DummyResp:
        content = b"img"

    monkeypatch.setattr(mod.httpx, "get", lambda *args, **kwargs: DummyResp())
    text, artifact = await mod.station_location("国际空间站")
    assert text == "空间站位置获取成功"
    assert artifact.content["raw"] == b"img"


@pytest.mark.asyncio
async def test_station_location_empty_content(load_tool_module, monkeypatch):
    mod = load_tool_module("heavens_above")

    class DummyResp:
        content = b""

    monkeypatch.setattr(mod.httpx, "get", lambda *args, **kwargs: DummyResp())
    text, artifact = await mod.station_location("天宫")
    assert text == "空间站位置获取失败"
    assert artifact is None


@pytest.mark.asyncio
async def test_get_launches_success(load_tool_module, monkeypatch):
    mod = load_tool_module("rocket")

    class DummyResp:
        status_code = 200

        def json(self):
            return {
                "count": 1,
                "results": [
                    {
                        "name": "Falcon 9 | Starlink",
                        "pad": {"location": {"country_code": "US"}},
                        "launch_service_provider": {"name": "SpaceX"},
                        "net": "2030-01-01T00:00:00+00:00",
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
