# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
async def test_tarot_reading_invalid_spread(load_tool_module):
    mod = load_tool_module("tarot")
    result = await mod.tarot_reading("unknown_spread", "test")
    assert "不支持的牌阵类型" in result


@pytest.mark.asyncio
async def test_tarot_reading_custom_without_count(load_tool_module):
    mod = load_tool_module("tarot")
    result = await mod.tarot_reading("custom", "test", card_count=0)
    assert "请指定card_count参数" in result


@pytest.mark.asyncio
async def test_tarot_reading_success(load_tool_module):
    mod = load_tool_module("tarot")
    result = await mod.tarot_reading("single", "今天运势如何")
    assert "塔罗占卜结果" in result
    assert "问题: 今天运势如何" in result


@pytest.mark.asyncio
async def test_list_tarot_spreads(load_tool_module):
    mod = load_tool_module("tarot")
    result = await mod.list_tarot_spreads()
    assert "塔罗牌阵列表" in result
    assert "single" in result


@pytest.mark.asyncio
async def test_iching_divination_invalid_method(load_tool_module):
    mod = load_tool_module("iching")
    result = await mod.iching_divination("bad_method", "test")
    assert "不支持的起卦方法" in result


@pytest.mark.asyncio
async def test_iching_divination_number_success(load_tool_module):
    mod = load_tool_module("iching")
    result = await mod.iching_divination("number", "今天运势", num1=123, num2=456)
    assert "周易占卜结果" in result
    assert "今天运势" in result


@pytest.mark.asyncio
async def test_list_iching_hexagrams(load_tool_module):
    mod = load_tool_module("iching")
    result_all = await mod.list_iching_hexagrams("all")
    result_eight = await mod.list_iching_hexagrams("eight")
    assert "周易64卦总览" in result_all
    assert "周易八纯卦" in result_eight


@pytest.mark.asyncio
async def test_get_hexagram_detail(load_tool_module):
    mod = load_tool_module("iching")
    result = await mod.get_hexagram_detail("1")
    assert "第1卦" in result
    assert "乾卦" in result
