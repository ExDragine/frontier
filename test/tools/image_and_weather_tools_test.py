# ruff: noqa: S101

import base64
from types import SimpleNamespace

import pytest


def _tiny_png_data_url(raw: bytes = b"current-image") -> str:
    return f"data:image/png;base64,{base64.b64encode(raw).decode()}"


@pytest.mark.asyncio
async def test_get_paint_generate_uses_shared_paint_service(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")
    captured = {}

    async def fake_paint(prompt, reference_images):
        captured["prompt"] = prompt
        captured["reference_images"] = reference_images
        return b"img"

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", True, raising=False)
    text, artifact = await mod.get_paint("a cat")

    assert captured == {"prompt": "a cat", "reference_images": []}
    assert "成功生成图片" in text
    assert artifact.content["raw"] == b"img"


@pytest.mark.asyncio
async def test_get_paint_returns_direct_artifact(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")

    async def fake_paint(_prompt, _reference_images):
        return b"img"

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_paint("a cat")

    assert artifact.content["raw"] == b"img"


@pytest.mark.asyncio
async def test_get_paint_edit_uses_images_from_latest_user_message(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")
    captured = {}
    history_image = _tiny_png_data_url(b"history-image")
    current_image = _tiny_png_data_url(b"current-image")
    quoted_image = _tiny_png_data_url(b"quoted-image")
    state = {
        "user_id": "10001",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "old"},
                    {"type": "image_url", "image_url": {"url": history_image}},
                ],
            },
            {
                "role": "assistant",
                "content": "ok",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "把当前和引用图片融合"},
                    {"type": "image_url", "image_url": {"url": quoted_image}},
                    {"type": "image_url", "image_url": {"url": current_image}},
                ],
            },
        ],
    }

    async def fake_paint(prompt, reference_images):
        captured["prompt"] = prompt
        captured["reference_images"] = reference_images
        return b"edited"

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_paint("watercolor style", mode="edit", state=state)

    assert captured["prompt"] == "watercolor style"
    assert captured["reference_images"] == [b"quoted-image", b"current-image"]
    assert b"history-image" not in captured["reference_images"]
    assert "成功编辑图片" in text
    assert artifact.content["raw"] == b"edited"


@pytest.mark.asyncio
async def test_get_paint_edit_without_images_fails_before_service_call(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")

    async def fake_paint(_prompt, _reference_images):
        raise AssertionError("paint should not be called without reference images")

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_paint("watercolor style", mode="edit", state={"user_id": "10001", "messages": []})

    assert "没有可编辑的图片" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_get_paint_respects_disabled_paint_module(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")

    async def fake_paint(_prompt, _reference_images):
        raise AssertionError("paint should not be called while disabled")

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", False, raising=False)

    text, artifact = await mod.get_paint("a cat")

    assert "绘画功能未启用" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_get_paint_rate_limits_by_injected_user_id(load_tool_module, monkeypatch):
    mod = load_tool_module("paint")

    async def fake_paint(_prompt, _reference_images):
        raise AssertionError("paint should not be called while rate limited")

    class DenyLimiter:
        def check(self, user_id, *, now, max_requests, window_seconds):
            assert user_id == "10001"
            assert max_requests == 3
            assert window_seconds == 600
            return mod.PaintRateLimitResult(False, 42)

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod, "paint_rate_limiter", DenyLimiter())
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", True, raising=False)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_RATE_LIMIT_MAX_REQUESTS", 3, raising=False)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_RATE_LIMIT_WINDOW_SECONDS", 600, raising=False)

    text, artifact = await mod.get_paint("a cat", state={"user_id": "10001", "messages": []})

    assert "画得太快了" in text
    assert "42 秒后再试" in text
    assert artifact is None


def test_get_paint_tool_schema_hides_injected_state(load_tool_module):
    mod = load_tool_module("paint")
    args = getattr(mod.get_paint, "args", {})

    assert "prompt" in args
    assert "mode" in args
    assert "state" not in args


@pytest.mark.asyncio
async def test_china_earthquake_tool_returns_plain_text(load_tool_module, monkeypatch):
    mod = load_tool_module("earthquake")

    class FixedDateTime(mod.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 7, 14, 12, tzinfo=tz)

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "message": "",
                "code": 0,
                "data": [
                    {
                        "oriTime": "2026-07-13 07:27:48",
                        "locName": "四川宜宾市高县",
                        "magnitude": 3.8,
                        "focDepth": 5.0,
                    },
                    {
                        "oriTime": "2026-07-13 05:02:08",
                        "locName": "四川宜宾市高县",
                        "magnitude": 3.9,
                        "focDepth": 6.0,
                    },
                ],
            }

    class Client:
        async def get(self, url, *, params):
            assert url == "https://www.cenc.ac.cn/prodlaunch-web-backend/open/data/catalogs"
            assert params == {
                "orderBy": "id",
                "isAsc": "false",
                "startMg": 3,
                "endMg": 10,
                "startTime": "2026-06-14 00:00:00",
                "endTime": "2026-07-14 23:59:59",
                "locationRange": 1,
            }
            return Response()

    monkeypatch.setattr(mod, "datetime", FixedDateTime)
    monkeypatch.setattr(mod, "httpx_client", Client())

    result = await mod.get_china_earthquake()

    assert result == (
        "中国地震台网最近地震信息（2 条）：\n"
        "1. 2026-07-13 07:27:48｜四川宜宾市高县｜M3.8｜深度 5 千米\n"
        "2. 2026-07-13 05:02:08｜四川宜宾市高县｜M3.9｜深度 6 千米"
    )
    assert not hasattr(mod, "get_japan_earthquake")


@pytest.mark.asyncio
async def test_usgs_significant_earthquakes_returns_plain_text(load_tool_module, monkeypatch):
    mod = load_tool_module("earthquake")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "properties": {
                            "mag": 6.3,
                            "place": "southeast of the Loyalty Islands",
                            "time": 0,
                            "sig": 611,
                            "alert": "green",
                            "tsunami": 0,
                        },
                        "geometry": {"coordinates": [171.5, -22.8, 10]},
                    },
                    {
                        "properties": {
                            "mag": 7.5,
                            "place": "20 km ESE of Yumare, Venezuela",
                            "time": 1000,
                            "sig": 2646,
                            "alert": "red",
                            "tsunami": 1,
                        },
                        "geometry": {"coordinates": [-68.5, 10.5, 7.55]},
                    },
                ],
            }

    class Client:
        async def get(self, url):
            assert url == mod.USGS_SIGNIFICANT_MONTH_URL
            return Response()

    monkeypatch.setattr(mod, "httpx_client", Client())

    result = await mod.get_usgs_significant_earthquakes()

    assert result == (
        "USGS 过去一个月重大地震（2 条，时间均为北京时间）：\n"
        "1. 1970-01-01 08:00:01｜20 km ESE of Yumare, Venezuela｜M7.5｜深度 7.55 千米｜"
        "显著性 2646｜PAGER 红色｜海啸标记：有\n"
        "2. 1970-01-01 08:00:00｜southeast of the Loyalty Islands｜M6.3｜深度 10 千米｜"
        "显著性 611｜PAGER 绿色｜海啸标记：无"
    )


def test_available_china_radar_areas(load_tool_module):
    mod = load_tool_module("radar")

    result = mod.get_available_china_radar_areas()

    assert result.startswith(f"可用雷达地区（{len(mod.areas)} 个）：")
    assert "全国及分区：全国、华北、东北、华东、华中、华南、西南、西北" in result
    assert "省、市及雷达站：" in result
    assert all(area in result for area in mod.areas)


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

    class FakeUniMessage:
        @staticmethod
        def image(**kwargs):
            return SimpleNamespace(content={"type": "image", **kwargs})

        @staticmethod
        def video(**kwargs):
            return SimpleNamespace(content={"type": "video", **kwargs})

    class DummyResp:
        content = b"video"

        def raise_for_status(self):
            return None

    class DummyClient:
        async def get(self, *_args, **_kwargs):
            return DummyResp()

    monkeypatch.setattr(mod, "UniMessage", FakeUniMessage)
    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    image_text, image_artifact = await mod.get_fy4b_satellite_image("china")
    assert image_text == "成功获取FY4B 中国区域真彩色云图"
    assert image_artifact.content == {
        "type": "image",
        "url": "https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_REGC_GCLR.JPG",
    }

    sandwich_text, sandwich_artifact = await mod.get_fy4b_satellite_image("sandwich")
    assert sandwich_text == "成功获取FY4B 全盘三明治云图"
    assert sandwich_artifact.content == {
        "type": "image",
        "url": "https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/SWCI/FY4B_DISK_SWCI.JPG",
    }

    text, artifact = await mod.get_fy4b_cloud_map("china", "72h")
    assert text == "成功获取china地区的卫星云图动画（最近72小时）"
    assert artifact.content["type"] == "video"

    text2, artifact2 = await mod.get_fy4b_geos_cloud_map("MOS", "24h")
    assert text2.startswith("成功获取FY4B卫星全地球视角云图视频")
    assert artifact2.content["type"] == "video"

    assert await mod.get_fy4b_geos_cloud_map("BAD", "24h") is None

    text3, artifact3 = await mod.get_himawari_satellite_image()
    assert "成功获取Himawari静止气象卫星最新可见光合成图像" in text3
    assert artifact3.content["type"] == "image"


@pytest.mark.asyncio
async def test_weather_tools(load_tool_module, monkeypatch):
    mod = load_tool_module("weather")

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
    assert text.startswith("获取成功")
    assert artifact.content["type"] == "image"
