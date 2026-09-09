# ruff: noqa: S101
"""Behavior contracts for domain tools with separate validation and rendering."""

import pytest


@pytest.mark.parametrize(
    ("breedable", "groups", "expected"),
    [
        ((1, 1), ("1", "1,2"), "可以在一起孵蛋"),
        ((1, 1), ("1", "2"), "因为蛋组不同"),
        ((2, 1), ("1", "1"), "「甲」不能孵蛋"),
        ((1, 2), ("1", "1"), "「乙」不能孵蛋"),
        ((2, 2), ("1", "1"), "均不能孵蛋"),
    ],
)
async def test_egg_comparison_retains_text_when_rendering_fails(
    load_tool_module, monkeypatch, breedable, groups, expected,
):
    module = load_tool_module("NRCeggs_groups")
    pets = {
        name: {"name": name, "isfudan": can_breed, "danzu": group}
        for name, can_breed, group in zip(("甲", "乙"), breedable, groups, strict=True)
    }

    async def fetch(name):
        return pets[name]

    def render(*args, **kwargs):
        raise RuntimeError("renderer unavailable")

    monkeypatch.setattr(module, "_fetch_pet_by_name", fetch)
    monkeypatch.setattr(module, "_render_html", render)
    text, artifact = await module.get_nrc_eggs_groups("compare", "甲", "乙")
    assert expected in text
    assert artifact is None


async def test_egg_matches_deduplicate_groups_and_preserve_breedable_order(load_tool_module, monkeypatch):
    module = load_tool_module("NRCeggs_groups")
    own_pet = {"name": "自己", "isfudan": 1, "danzu": "1,2"}
    one = {"name": "不能孵", "isfudan": 2, "danzu": "1"}
    two = {"name": "能孵", "isfudan": 1, "danzu": "1,2"}
    rendered = {}

    async def fetch_name(name):
        return own_pet

    async def fetch_group(group):
        return [own_pet, one, two] if group == "1" else [own_pet, two]

    def render(mode, **context):
        rendered.update(context)
        return "<html></html>"

    async def capture(*args, **kwargs):
        return b"eggs"

    monkeypatch.setattr(module, "_fetch_pet_by_name", fetch_name)
    monkeypatch.setattr(module, "_fetch_pets_by_danzu", fetch_group)
    monkeypatch.setattr(module, "_render_html", render)
    monkeypatch.setattr(module, "html_to_image", capture)
    text, artifact = await module.get_nrc_eggs_groups("find_matches", "自己")
    assert "共找到 2 只" in text
    assert [pet["name"] for pet in rendered["matches"]] == ["能孵", "不能孵"]
    assert artifact[0].raw == b"eggs"


async def test_typhoon_partial_render_failure_preserves_order_and_overlay(load_tool_module, monkeypatch):
    module = load_tool_module("typhoon")
    typhoons = [{"name": name, "is_current": 1} for name in ("甲", "乙", "丙")]

    async def fetch():
        return typhoons

    async def overlay(kind):
        return {"label": "雷达", "time": "12:00"}

    async def render(target, layer):
        assert layer["label"] == "雷达"
        if target["name"] == "乙":
            raise RuntimeError("broken card")
        return target["name"].encode()

    monkeypatch.setattr(module, "_fetch_typhoon_data", fetch)
    monkeypatch.setattr(module, "_fetch_latest_overlay", overlay)
    monkeypatch.setattr(module, "_render_single_typhoon", render)
    text, artifact = await module.get_typhoon_info(overlay="radar")
    assert "已叠加雷达 12:00" in text
    assert [segment.raw for segment in artifact] == ["甲".encode(), "丙".encode()]


@pytest.mark.parametrize("parameters", [{"p1": 9}, {"p3": 9}, {"p5": 9}, {"p4": 99}, {"p1": 6, "bio_annot": 9}])
async def test_professional_ens_rejects_invalid_options_before_browser(load_tool_module, parameters):
    from utils.ens_gate import _ens_prefix

    module = load_tool_module("ens_professional")
    token = _ens_prefix.set("vep")
    try:
        text, artifact = await module.run_ens_professional(**parameters)
    finally:
        _ens_prefix.reset(token)
    assert text.startswith("无效")
    assert artifact is None


def test_professional_ens_uses_full_city_catalog(load_tool_module):
    module = load_tool_module("ens_professional")
    lon, lat, name = module._resolve_professional_location("南京市", "0")
    assert name == "南京市"
    assert 118 < lon < 120
    assert 31 < lat < 33


def test_sea_lookup_prefers_exact_global_name_before_fuzzy_coastal_match(load_tool_module, monkeypatch):
    module = load_tool_module("ens_normal")
    monkeypatch.setattr(module, "_COASTAL_SEA_COORDS", {"北海市": (109.0, 21.0)})
    monkeypatch.setattr(module, "_GLOBAL_SEA_COORDS", {"北海": (3.0, 56.0)})
    assert module._resolve_sea_coords("北海") == (3.0, 56.0)
    assert module._resolve_sea_coords("广西北海市近海") == (109.0, 21.0)


async def test_ens_batch_keeps_successful_media_when_another_query_fails(load_tool_module, monkeypatch):
    module = load_tool_module("ens_normal")

    async def execute(scenario, location, time, **kwargs):
        if location == "未知":
            raise ValueError("unknown location")
        return location, location.encode(), location == "北京"

    monkeypatch.setattr(module, "_execute_single_query", execute)
    text, artifact = await module.run_ens_normal(queries=[
        {"scenario": "风速", "location": "北京"},
        {"scenario": "风速", "location": "未知"},
        {"scenario": "风速", "location": "上海"},
    ])
    assert "unknown location" in text
    assert [segment.type for segment in artifact] == ["video", "image"]
    assert [segment.raw for segment in artifact] == ["北京".encode(), "上海".encode()]


@pytest.mark.parametrize("batch", [False, True])
async def test_fire_query_retains_required_visual_even_when_text_only_requested(load_tool_module, monkeypatch, batch):
    module = load_tool_module("ens_normal")

    async def capture(**kwargs):
        return b"fire-map"

    monkeypatch.setattr(module, "record_video", capture)
    query = {"scenario": "活跃火点", "location": "北京"}
    arguments = {"queries": [query]} if batch else query
    text, artifact = await module.run_ens_normal(**arguments, no_video=True)
    assert "活跃火点" in text
    assert artifact[0].raw == b"fire-map"
