# ruff: noqa: S101

import pytest


# ── 普通模式 ens_normal ──


@pytest.mark.asyncio
async def test_ens_normal_scenario_not_found(load_tool_module):
    mod = load_tool_module("ens_normal")
    text, artifact = await mod.ens_normal(scenario="不存在的场景", location="北京")
    assert "未知场景" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_ens_normal_video_path(load_tool_module, monkeypatch):
    """普通场景（风速+北京）→ 字典命中 → 录屏。"""
    mod = load_tool_module("ens_normal")
    captured_url = {}

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        captured_url["url"] = url
        captured_url["duration"] = duration
        return b"fake-video"

    async def fake_screenshot(
        url, *, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        raise AssertionError("不应调用截图")

    monkeypatch.setattr(mod, "record_video", fake_record_video)
    monkeypatch.setattr(mod, "screenshot", fake_screenshot)

    text, artifact = await mod.ens_normal(scenario="风速", location="北京")

    assert "你要的北京现在的风速已返回" == text
    assert "wind" in captured_url["url"]
    assert "level" in captured_url["url"]
    assert "orthographic" in captured_url["url"]
    assert "loc=116.4,39.9" in captured_url["url"]
    assert captured_url.get("duration") == 3
    assert artifact is not None


@pytest.mark.asyncio
async def test_ens_normal_space_mode_plays_video(load_tool_module, monkeypatch):
    """空间天气（极光）→ 默认播放 → 录屏（不再截图）。"""
    mod = load_tool_module("ens_normal")
    captured_url = {}

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        captured_url["url"] = url
        return b"fake-video"

    async def fake_screenshot(
        url, *, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        raise AssertionError("极光现在默认播放，不应截图")

    monkeypatch.setattr(mod, "record_video", fake_record_video)
    monkeypatch.setattr(mod, "screenshot", fake_screenshot)

    text, artifact = await mod.ens_normal(
        scenario="极光",
        location="费尔班克斯",
        lon=-147.72,
        lat=64.86,
    )

    assert "你要的费尔班克斯现在的极光已返回" == text
    assert "anim=off" not in captured_url["url"]  # 不再有 anim=off
    assert artifact is not None


@pytest.mark.asyncio
async def test_ens_normal_explicit_coordinates(load_tool_module, monkeypatch):
    """传入 lon/lat → 跳过字典查找。"""
    mod = load_tool_module("ens_normal")

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        return b"fake-video"

    monkeypatch.setattr(mod, "record_video", fake_record_video)

    text, artifact = await mod.ens_normal(scenario="洋流", location="太平洋", lon=-150.0, lat=0.0)
    assert "洋流" in text
    assert artifact is not None


@pytest.mark.asyncio
async def test_ens_normal_unknown_location(load_tool_module, monkeypatch):
    """未知位置且未传坐标 → 返回错误。"""
    mod = load_tool_module("ens_normal")
    text, artifact = await mod.ens_normal(scenario="风速", location="火星基地")
    assert "获取失败" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_ens_normal_record_video_failure(load_tool_module, monkeypatch):
    """录屏失败 → 返回错误信息。"""
    mod = load_tool_module("ens_normal")

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        raise RuntimeError("浏览器崩溃")

    monkeypatch.setattr(mod, "record_video", fake_record_video)

    text, artifact = await mod.ens_normal(scenario="风速", location="北京")
    assert "获取失败" in text
    assert artifact is None


# ── 专业模式 ens_professional ──


@pytest.mark.asyncio
async def test_ens_professional_video_path(load_tool_module, monkeypatch):
    """数字参数 → 录屏。"""
    mod = load_tool_module("ens_professional")
    captured_url = {}

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        captured_url["url"] = url
        captured_url["duration"] = duration
        return b"fake-video"

    async def fake_screenshot(
        url, *, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        raise AssertionError("不应调用截图")

    monkeypatch.setattr(mod, "record_video", fake_record_video)
    monkeypatch.setattr(mod, "screenshot", fake_screenshot)

    text, artifact = await mod.ens_professional(
        p1=1,
        p2=4,
        p3=1,
        p4=2,
        p5=1,
        p6="116.40",
        p7="39.90",
        p8=300,
        p9="0",
        p10="0",
    )

    assert "你要的(116.4, 39.9)现在的大气数据已返回" == text
    assert "wind" in captured_url["url"]
    assert "isobaric/500hPa" in captured_url["url"]
    assert "overlay=temp" in captured_url["url"]
    assert "116.4" in captured_url["url"]
    assert "39.9" in captured_url["url"]
    assert captured_url.get("duration") == 3
    assert artifact is not None


@pytest.mark.asyncio
async def test_ens_professional_pause_screenshot(load_tool_module, monkeypatch):
    """p10=animoff → 截图。"""
    mod = load_tool_module("ens_professional")
    captured_url = {}

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        raise AssertionError("animoff 不应录屏")

    async def fake_screenshot(
        url, *, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        captured_url["url"] = url
        return b"fake-image"

    monkeypatch.setattr(mod, "record_video", fake_record_video)
    monkeypatch.setattr(mod, "screenshot", fake_screenshot)

    text, artifact = await mod.ens_professional(
        p1=5,
        p2=0,
        p3=1,
        p4=1,
        p5=1,
        p6="0.0",
        p7="60.0",
        p8=300,
        p9="0",
        p10="animoff",
    )

    assert "你要的(0.0, 60.0)现在的空间天气数据已返回" == text
    assert "space" in captured_url["url"]
    assert "anim=off" in captured_url["url"]
    assert artifact is not None


@pytest.mark.asyncio
async def test_ens_professional_bio_fires(load_tool_module, monkeypatch):
    """生物模式 + 火点注释 → URL 包含 annot=fires。"""
    mod = load_tool_module("ens_professional")
    captured_url = {}

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        captured_url["url"] = url
        return b"fake-video"

    monkeypatch.setattr(mod, "record_video", fake_record_video)

    async def fake_screenshot(
        url, *, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        return b"fake"

    monkeypatch.setattr(mod, "screenshot", fake_screenshot)

    await mod.ens_professional(
        p1=6,
        p2=0,
        p3=1,
        p4=0,
        p5=2,
        p6="120.0",
        p7="-15.0",
        p8=80,
        p9="0",
        p10="0",
        bio_annot=1,
    )

    assert "annot=fires" in captured_url["url"]


@pytest.mark.asyncio
async def test_ens_professional_time_parse(load_tool_module, monkeypatch):
    """时间格式转换 YYYYMMDD.HHMM → #YYYY/MM/DD/HHMMZ。"""
    mod = load_tool_module("ens_professional")
    captured_url = {}

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        captured_url["url"] = url
        return b"fake-video"

    monkeypatch.setattr(mod, "record_video", fake_record_video)

    async def fake_screenshot(
        url, *, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        return b"fake"

    monkeypatch.setattr(mod, "screenshot", fake_screenshot)

    await mod.ens_professional(
        p1=1,
        p2=0,
        p3=1,
        p4=0,
        p5=1,
        p6="116.4",
        p7="39.9",
        p8=1850,
        p9="20261001.1200",
        p10="0",
    )

    assert "#2026/10/01/1200Z" in captured_url["url"]


@pytest.mark.asyncio
async def test_ens_professional_failure(load_tool_module, monkeypatch):
    """record_video 失败 → 返回错误信息。"""
    mod = load_tool_module("ens_professional")

    async def fake_record_video(
        url, *, duration, width, height, wait_until, timeout, wait_selector=None, post_wait_ms=0, hard_wait=False, ready_timeout=15000, wait_function=None
    ):
        raise RuntimeError("浏览器超时")

    monkeypatch.setattr(mod, "record_video", fake_record_video)

    text, artifact = await mod.ens_professional(
        p1=1,
        p2=0,
        p3=1,
        p4=0,
        p5=1,
        p6="116.40",
        p7="39.90",
        p8=300,
        p9="0",
        p10="0",
    )

    assert "获取失败" in text
    assert artifact is None


# ── URL 完整性 ──


@pytest.mark.asyncio
async def test_all_scenarios_have_required_keys(load_tool_module):
    """28 个场景的映射表结构完整性。"""
    mod = load_tool_module("ens_normal")
    required_keys = {"mode", "animation", "projection", "zoom"}
    for name, params in mod.SCENARIO_MAP.items():
        missing = required_keys - params.keys()
        assert not missing, f"场景「{name}」缺少必填键: {missing}"
        assert params["mode"] in {"wind", "ocean", "chem", "particulates", "space", "bio"}, (
            f"场景「{name}」mode 无效: {params['mode']}"
        )
