# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
async def test_solar_flare(load_tool_module, monkeypatch):
    mod = load_tool_module("space_weather")

    class DummyResp:
        def json(self):
            return [
                {"classType": "M1.2", "beginTime": "t1", "activeRegionNum": "1", "link": "u1"},
                {"classType": "X2.0", "beginTime": "t2", "activeRegionNum": "2", "link": "u2"},
            ]

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *_args, **_kwargs):
            return DummyResp()

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *args, **kwargs: DummyClient())
    result = await mod.solar_flare()
    assert "耀斑类型:X2.0" in result


@pytest.mark.asyncio
async def test_realtime_solarwind(load_tool_module, monkeypatch):
    mod = load_tool_module("space_weather")

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    class DummyClient:
        async def get(self, url):
            if "mag-2-hour" in url:
                return DummyResp([["t", "Bt"], ["2026-01-01T00:00Z", 7.5]])
            if "plasma-2-hour" in url:
                return DummyResp([["h"], ["2026-01-01T00:00Z", 450, 6, 100000, 1, 0, 1]])
            return DummyResp([["h"], ["2026-01-01T00:00Z", 4]])

    monkeypatch.setattr(mod, "httpx_client", DummyClient())
    result = await mod.realtime_solarwind()
    assert "速度：450 km/s" in result
    assert "当前Kp: 4" in result


@pytest.mark.asyncio
async def test_soho_realtime_solarwind(load_tool_module, monkeypatch):
    mod = load_tool_module("space_weather")

    class DummyResp:
        content = b"2026 010:12:34:56 420 5 33 45 1 2"

    class DummyClient:
        async def get(self, *_args, **_kwargs):
            return DummyResp()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())
    result = await mod.soho_realtime_solarwind()
    assert "速度：420.0 km/s" in result
    assert "数据来源:https://space.umd.edu/pm/" in result


@pytest.mark.asyncio
async def test_geospace(load_tool_module):
    mod = load_tool_module("space_weather")
    text, artifact = await mod.geospace()
    assert "地磁场" in text
    assert len(artifact.content) == 3


@pytest.mark.asyncio
async def test_noaa_enlil_predict(load_tool_module, monkeypatch):
    mod = load_tool_module("space_weather")

    class DummyResp:
        content = b"<html></html>"

    class DummyClient:
        async def get(self, *_args, **_kwargs):
            return DummyResp()

    class DummySoup:
        def __init__(self, *_args, **_kwargs):
            pass

        def select(self, *_args, **_kwargs):
            return [{"href": "20260101T00/"}, {"href": "20260101T01/"}]

    monkeypatch.setattr(mod, "httpx_client", DummyClient())
    monkeypatch.setattr(mod, "BeautifulSoup", DummySoup)

    text, artifact = await mod.noaa_enlil_predict()
    assert "NOAA Enlil模型" in text
    assert hasattr(artifact.content, "url")


@pytest.mark.asyncio
async def test_solar_image_and_goes_suvi(load_tool_module):
    mod = load_tool_module("space_weather")

    text, artifact = await mod.solar_image("SN")
    assert text == "获取成功"
    assert artifact.content["type"] == "image"

    text2, artifact2 = await mod.solar_image("BAD")
    assert "查无此图" in text2
    assert artifact2 is None

    text3, artifact3 = await mod.goes_suvi("304")
    assert text3 == "获取成功"
    assert artifact3.content["type"] == "image"

    text4, artifact4 = await mod.goes_suvi("094")
    assert "查无此图" in text4
    assert artifact4 is None


@pytest.mark.asyncio
async def test_sunspot(load_tool_module, monkeypatch):
    mod = load_tool_module("space_weather")

    class DummyResp:
        def __init__(self, content=None, payload=None):
            self.content = content
            self._payload = payload or {}

        def json(self):
            return self._payload

    class DummyClient:
        async def get(self, url, **_kwargs):
            if url == "https://img.local/aso.jpg":
                return DummyResp(content=b"aso")
            return DummyResp(content=b"soho")

        async def post(self, *_args, **_kwargs):
            return DummyResp(payload={"msg": "https://img.local/aso.jpg"})

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    text, artifact = await mod.sunspot("SOHO")
    assert text == "获取成功"
    assert artifact.content["raw"] == b"soho"

    text2, artifact2 = await mod.sunspot("ASO-S")
    assert text2 == "获取成功"
    assert artifact2.content["raw"] == b"aso"


@pytest.mark.asyncio
async def test_swpc_page(load_tool_module, monkeypatch):
    mod = load_tool_module("space_weather")

    class DummyElement:
        async def screenshot(self):
            return b"swpc"

    class DummyPage:
        async def goto(self, *_args, **_kwargs):
            return None

        async def wait_for_timeout(self, *_args, **_kwargs):
            return None

        async def query_selector(self, *_args, **_kwargs):
            return DummyElement()

    class DummyBrowser:
        async def new_page(self):
            return DummyPage()

        async def close(self):
            return None

    class DummyChromium:
        async def launch(self):
            return DummyBrowser()

    class DummyPlaywright:
        chromium = DummyChromium()

    class DummyCtx:
        async def __aenter__(self):
            return DummyPlaywright()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(mod, "async_playwright", lambda: DummyCtx())

    text, artifact = await mod.swpc_page()
    assert text == "获取成功"
    assert artifact.content["raw"] == b"swpc"


@pytest.mark.asyncio
async def test_planets_weather(load_tool_module):
    mod = load_tool_module("space_weather")
    text, artifact = await mod.planets_weather("火星")
    assert "火星天气" in text
    assert artifact is not None

    text2, artifact2 = await mod.planets_weather("开普勒")
    assert "太阳系" in text2
    assert artifact2 is None
