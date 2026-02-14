# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
async def test_get_paint_success_and_failure(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")

    class DummyResp:
        content = b"img"

    monkeypatch.setattr(mod.httpx, "get", lambda *args, **kwargs: DummyResp())
    text, artifact = await mod.get_paint("a cat")
    assert "成功生成图片" in text
    assert artifact.content["raw"] == b"img"

    def broken_get(*_args, **_kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(mod.httpx, "get", broken_get)
    text2, artifact2 = await mod.get_paint("a cat")
    assert "图片生成失败" in text2
    assert artifact2 is None


@pytest.mark.asyncio
async def test_earthquake_tools(load_tool_module, monkeypatch):
    mod = load_tool_module("earthquake")

    async def cn_img():
        return b"cn"

    async def jp_img():
        return b"jp"

    monkeypatch.setattr(mod, "cenc_eq_list_img", cn_img)
    monkeypatch.setattr(mod, "jma_eq_list_img", jp_img)

    text_cn, art_cn = await mod.get_china_earthquake()
    text_jp, art_jp = await mod.get_japan_earthquake()

    assert "中国地震" in text_cn
    assert art_cn.content["raw"] == b"cn"
    assert "日本地震" in text_jp
    assert art_jp.content["raw"] == b"jp"


@pytest.mark.asyncio
async def test_radar_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("radar")

    async def ok(_area):
        return "https://img/radar.png"

    monkeypatch.setattr(mod, "china_static_radar", ok)
    text, artifact = await mod.get_static_china_radar("北京")
    assert "成功获取" in text
    assert artifact.content["url"] == "https://img/radar.png"

    async def none_url(_area):
        return None

    monkeypatch.setattr(mod, "china_static_radar", none_url)
    text2, artifact2 = await mod.get_static_china_radar("未知地区")
    assert "找不到" in text2
    assert artifact2 is None


@pytest.mark.asyncio
async def test_satellite_tools(load_tool_module, monkeypatch):
    mod = load_tool_module("satellite")

    class DummyResp:
        content = b"video"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(mod.httpx, "get", lambda *args, **kwargs: DummyResp())
    text, artifact = await mod.get_fy4b_cloud_map("china", "3h")
    assert "成功获取" in text
    assert artifact.content["type"] == "video"

    class DummyAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *_args, **_kwargs):
            return DummyResp()

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda **kwargs: DummyAsyncClient())
    text2, artifact2 = await mod.get_fy4b_geos_cloud_map("MOS", "24h")
    assert "成功获取FY4B卫星全地球视角云图视频" == text2
    assert artifact2.content["type"] == "video"

    assert await mod.get_fy4b_geos_cloud_map("BAD", "24h") is None

    text3, artifact3 = await mod.get_himawari_satellite_image()
    assert "成功获取Himawari静止气象卫星最新可见光合成图像" in text3
    assert artifact3.content["type"] == "image"


@pytest.mark.asyncio
async def test_weather_tools(load_tool_module, monkeypatch):
    mod = load_tool_module("weather")

    async def fake_geocode(_city):
        return 39.9, 116.4

    async def fake_fetch_json(url, _client, **_kwargs):
        if "current_weather=true" in url:
            return {"current_weather": {"temperature": 25, "windspeed": 3}}
        return {"daily": {"temperature_2m_max": [30, 31], "temperature_2m_min": [20, 21]}}

    monkeypatch.setattr(mod, "geocode", fake_geocode)
    monkeypatch.setattr(mod, "fetch_json", fake_fetch_json)

    current = await mod.get_current_weather("北京")
    future = await mod.get_future_weather("北京", 2)
    assert "北京 25℃" in current
    assert "第1天: 高30℃ 低20℃" in future

    class MarsResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"descriptions": ["cold", "windy"]}

    class MarsClient:
        async def get(self, *_args, **_kwargs):
            return MarsResp()

    monkeypatch.setattr(mod, "httpx_client", MarsClient())
    mars = await mod.mars_weather()
    assert "火星天气" in mars

    text, artifact = await mod.get_wind_map("wind_shear")
    assert text == "获取成功"
    assert artifact.content["type"] == "image"
