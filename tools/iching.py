"""周易占卜工具 - 完整版

支持三种传统起卦方法:
1. 三枚铜钱法 - 最传统准确的起卦方式
2. 时间起卦法 - 根据年月日时起卦
3. 报数起卦法 - 通过数字起卦
"""

from langchain_core.tools import tool
from nonebot import logger

from ._iching_reader import (
    IChingReader,
    load_hexagram_detail,
    load_iching_index,
    load_trigrams_data,
)

__all__ = [
    "IChingReader",
    "get_hexagram_detail",
    "iching_divination",
    "list_iching_hexagrams",
    "load_hexagram_detail",
    "load_iching_index",
    "load_trigrams_data",
]

# ===== 工具函数 =====


@tool(response_format="content")
async def iching_divination(
    method: str = "coin",
    question: str = "",
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    hour: int | None = None,
    num1: int | None = None,
    num2: int | None = None,
) -> str:
    """进行周易占卜

    周易八卦是中国古代的占卜系统,通过64卦象和爻辞提供人生指引。
    适用于决策咨询、事业发展、感情婚姻、健康运势等各类问题。

    Args:
        method (str): 起卦方法,可选值:
            - "coin": 三枚铜钱法(默认,最传统准确)
            - "time": 时间起卦法(根据年月日时起卦)
            - "number": 报数起卦法(通过数字起卦)

        question (str): 占卜的问题(可选,但强烈建议提供以聚焦意念)

        # 以下参数根据method不同而使用:

        # time方法专用参数(不提供则使用当前时间):
        year (int): 年份
        month (int): 月份(1-12)
        day (int): 日期(1-31)
        hour (int): 时辰(1-12, 子时=1, 丑时=2, ..., 亥时=12)

        # number方法专用参数(不提供则随机生成):
        num1 (int): 第一个数字(1-99999)
        num2 (int): 第二个数字(1-99999)

    Returns:
        str: 详细的占卜结果,包含:
            - 起卦方法和参数
            - 本卦(原卦)信息: 卦名、卦象、卦辞、象辞
            - 动爻信息(如有): 爻位、爻辞、解释
            - 变卦信息(如有): 卦名、卦象、卦辞
            - 解读提示: 事业、感情、建议等

    Examples:
        铜钱法占卜: iching_divination("coin", "今年事业发展如何")
        时间起卦: iching_divination("time", "感情运势", year=2026, month=2, day=5, hour=10)
        报数起卦: iching_divination("number", "是否适合跳槽", num1=123, num2=456)
        随机报数: iching_divination("number", "今日运势")  # num1和num2自动随机
    """
    try:
        # 加载周易数据
        index_data = load_iching_index()
        if not index_data:
            return "❌ 周易索引数据加载失败,请检查数据文件"

        trigrams_data = load_trigrams_data()
        if not trigrams_data:
            return "❌ 八卦数据加载失败,请检查数据文件"

        reader = IChingReader(index_data, trigrams_data)

        # 根据不同方法起卦
        if method == "coin":
            result = reader.divine_by_coins()
        elif method == "time":
            result = reader.divine_by_time(year, month, day, hour)
        elif method == "number":
            result = reader.divine_by_numbers(num1, num2)
        else:
            return (
                f"❌ 不支持的起卦方法: {method}\n\n"
                f"✅ 支持的方法:\n"
                f"   • coin - 三枚铜钱法(最传统)\n"
                f"   • time - 时间起卦法\n"
                f"   • number - 报数起卦法"
            )

        # 格式化输出
        formatted_result = reader.format_divination_result(
            original_hex=result["original_hexagram"],
            changing_hex=result.get("changing_hexagram"),
            changing_lines=result.get("changing_lines", []),
            method=method,
            question=question,
            extra_info=result.get("time_info") or result.get("numbers"),
            lines_values=result.get("lines_values"),
        )

        logger.info(
            f"✅ 周易占卜完成: 方法={method}, "
            f"本卦={result['original_hexagram']['name']}, "
            f"问题={question[:20] if question else '无'}..."
        )

        return formatted_result

    except ValueError as e:
        logger.error(f"周易占卜参数错误: {e}")
        return f"❌ 参数错误: {str(e)}"
    except Exception as e:
        logger.error("周易占卜失败", exc_info=e)
        return f"❌ 周易占卜失败: {str(e)}"


@tool(response_format="content")
async def list_iching_hexagrams(filter_type: str = "all") -> str:  # noqa: C901
    """列出周易64卦的信息

    Args:
        filter_type (str): 筛选类型
            - "all": 全部64卦(默认)
            - "eight": 八纯卦(乾坤震巽坎离艮兑)
            - "element": 按五行分类显示

    Returns:
        str: 64卦列表及简要说明
    """
    try:
        index_data = load_iching_index()
        if not index_data:
            return "❌ 无法加载周易索引数据"

        hexagrams = index_data.get("hexagrams", [])

        if filter_type == "eight":
            # 八纯卦(上下卦相同)
            result = "☯️ 周易八纯卦\n\n"
            result += "━" * 50 + "\n\n"

            eight_pure = [h for h in hexagrams if h["upper"] == h["lower"]]
            for h in eight_pure:
                # 加载详细信息
                detail = load_hexagram_detail(h["file"])
                if detail:
                    result += f"{h['symbol']} {h['number']}.{h['name']}卦 ({h['nature']})\n"
                    result += f"   五行: {detail.get('element', '未知')}\n"
                    if "judgment" in detail:
                        result += f"   卦辞: {detail['judgment']['vernacular']}\n"
                    result += "\n"

        elif filter_type == "element":
            # 按五行分类
            result = "☯️ 64卦五行分类\n\n"
            result += "━" * 50 + "\n\n"

            elements = {"金": [], "木": [], "水": [], "火": [], "土": []}
            for h in hexagrams:
                detail = load_hexagram_detail(h["file"])
                if detail and "element" in detail:
                    element = detail["element"]
                    if element in elements:
                        elements[element].append((h, detail))

            for element, items in elements.items():
                if items:
                    result += f"🔸 {element}行 ({len(items)}卦)\n"
                    for h, _detail in items:
                        result += f"   {h['symbol']} {h['number']}.{h['name']}\n"
                    result += "\n"

        else:  # all
            result = "☯️ 周易64卦总览\n\n"
            result += "━" * 50 + "\n\n"

            # 每行8卦
            for i in range(0, 64, 8):
                line_hexagrams = hexagrams[i : i + 8]
                result += "  ".join([f"{h['symbol']}{h['number']:02d}.{h['name']}" for h in line_hexagrams]) + "\n"

            result += "\n" + "━" * 50 + "\n\n"
            result += "💡 提示:\n"
            result += "   • 使用 filter_type='eight' 查看八纯卦详情\n"
            result += "   • 使用 filter_type='element' 按五行分类查看\n"

        return result

    except Exception as e:
        logger.error("列出卦象失败", exc_info=e)
        return f"❌ 列出卦象失败: {str(e)}"


@tool(response_format="content")
async def get_hexagram_detail(hexagram_name: str) -> str:
    """获取指定卦的详细信息

    Args:
        hexagram_name (str): 卦名,如"乾"、"坤"、"屯"等,或卦号(1-64)

    Returns:
        str: 该卦的完整信息
    """
    try:
        index_data = load_iching_index()
        if not index_data:
            return "❌ 无法加载周易索引数据"

        hexagrams = index_data.get("hexagrams", [])
        hex_info = None

        # 查找卦象
        for h in hexagrams:
            if h["name"] == hexagram_name or str(h["number"]) == str(hexagram_name):
                hex_info = h
                break

        if not hex_info:
            return f"❌ 未找到卦象: {hexagram_name}"

        # 加载详细信息
        hexagram = load_hexagram_detail(hex_info["file"])
        if not hexagram:
            return f"❌ 无法加载卦象详情: {hexagram_name}"

        # 详细展示
        result = f"☯️ {hexagram['full_symbol']} 第{hexagram['number']}卦 - {hexagram['name']}卦\n\n"
        result += f"🎴 别名: {hexagram['nature']}\n"
        result += f"🔺 上卦: {hexagram['upper_trigram']} {hexagram['upper_symbol']}\n"
        result += f"🔻 下卦: {hexagram['lower_trigram']} {hexagram['lower_symbol']}\n"
        result += f"⚡ 五行: {hexagram['element']}\n\n"

        result += "━" * 50 + "\n\n"

        result += "📜 卦辞:\n"
        result += f"   {hexagram['judgment']['text']}\n"
        result += f"   白话: {hexagram['judgment']['vernacular']}\n\n"

        result += "📖 象辞:\n"
        result += f"   {hexagram['image']['text']}\n"
        result += f"   白话: {hexagram['image']['vernacular']}\n\n"

        result += "━" * 50 + "\n\n"

        result += "📍 六爻爻辞:\n"
        for line in hexagram["lines"]:
            result += f"   {line['position']}. {line['text']}\n"
            result += f"      {line['vernacular']}\n"

        result += "\n" + "━" * 50 + "\n\n"

        result += "💡 解读提示:\n"
        hints = hexagram["interpretation_hints"]
        result += f"   🔮 运势: {hints['fortune']}\n"
        result += f"   💼 事业: {hints['career']}\n"
        result += f"   💕 感情: {hints['relationship']}\n"
        if "health" in hints:
            result += f"   🏥 健康: {hints['health']}\n"
        result += f"   📝 建议: {hints['advice']}\n"

        return result

    except Exception as e:
        logger.error(f"获取卦象详情失败: {hexagram_name}", exc_info=e)
        return f"❌ 获取卦象详情失败: {str(e)}"
