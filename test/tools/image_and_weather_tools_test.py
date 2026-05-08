# ruff: noqa: S101

import base64

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
async def test_get_paint_stages_generated_artifact_for_main_agent(load_tool_module, monkeypatch, tmp_path):
    from utils import staged_artifacts

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)
    mod = load_tool_module("paint")

    async def fake_paint(_prompt, _reference_images):
        return b"img"

    monkeypatch.setattr(mod, "paint", fake_paint)
    monkeypatch.setattr(mod.EnvConfig, "PAINT_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_paint("a cat")

    assert artifact.content["raw"] == b"img"
    assert "send_staged_artifact" in text
    artifact_id = text.split('artifact_id="', 1)[1].split('"', 1)[0]
    assert (tmp_path / artifact_id / "manifest.json").is_file()


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
    assert text2.startswith("成功获取FY4B卫星全地球视角云图视频")
    assert "send_staged_artifact" in text2
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

    current = await mod.weather_tool.current("北京")
    future = await mod.weather_tool.forecast("北京", 2)
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
    assert text.startswith("获取成功")
    assert "send_staged_artifact" in text
    assert artifact.content["type"] == "image"
