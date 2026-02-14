"""塔罗牌占卜工具 - 完整版"""

import json
import random
import secrets
from pathlib import Path

from langchain.tools import tool
from nonebot import logger

# 塔罗牌数据文件路径
TAROT_DATA_PATH = Path(__file__).parent.parent / "data" / "tarot_cards.json"


def load_tarot_data() -> dict:
    """加载塔罗牌数据

    Returns:
        dict: 塔罗牌数据字典，包含大阿卡纳、小阿卡纳和牌阵信息
    """
    try:
        with open(TAROT_DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"塔罗牌数据文件不存在: {TAROT_DATA_PATH}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"塔罗牌数据JSON解析失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"加载塔罗牌数据失败: {e}", exc_info=e)
        return {}


class TarotReader:
    """塔罗牌阅读器"""

    def __init__(self, cards_data: dict):
        """初始化塔罗牌阅读器

        Args:
            cards_data: 塔罗牌数据字典
        """
        self.cards_data = cards_data
        self.all_cards = self._flatten_cards()
        self.spreads = cards_data.get("spreads", {})

    def _flatten_cards(self) -> list[dict]:
        """将78张牌扁平化为列表

        Returns:
            list[dict]: 所有塔罗牌的列表
        """
        cards = []
        # 添加22张大阿卡纳
        cards.extend(self.cards_data.get("major_arcana", []))
        # 添加56张小阿卡纳
        minor = self.cards_data.get("minor_arcana", {})
        for suit in ["wands", "cups", "swords", "pentacles"]:
            cards.extend(minor.get(suit, []))
        return cards

    def draw_cards(self, count: int) -> list[dict]:
        """抽取指定数量的牌(不重复)

        Args:
            count: 需要抽取的牌数量

        Returns:
            list[dict]: 抽取的牌列表，每张牌包含card信息和reversed状态
        """
        if count > len(self.all_cards):
            logger.warning(f"请求抽取{count}张牌，但总共只有{len(self.all_cards)}张，将抽取全部")
            count = len(self.all_cards)

        selected_cards = random.sample(self.all_cards, count)

        # 为每张牌随机确定正逆位(50%概率)
        result = []
        for card in selected_cards:
            is_reversed = secrets.choice([True, False])
            result.append({"card": card, "reversed": is_reversed})
        return result

    def get_spread_info(self, spread_type: str, card_count: int | None = None) -> dict:
        """获取牌阵信息

        Args:
            spread_type: 牌阵类型
            card_count: 自定义牌数（仅用于custom类型）

        Returns:
            dict: 牌阵信息，包含name、description、positions等
        """
        if spread_type in self.spreads:
            return self.spreads[spread_type]
        else:
            # 自定义牌阵
            count = card_count or 1
            positions = [f"位置{i + 1}" for i in range(count)]
            return {
                "name": f"自定义{count}张牌阵",
                "description": f"自由抽取{count}张牌进行解读",
                "positions": positions,
                "interpretation_hint": "观察所有牌面的整体能量和相互关系，从中寻找答案",
            }

    def format_reading(
        self, drawn_cards: list[dict], spread_type: str, question: str, card_count: int | None = None
    ) -> str:
        """格式化占卜结果

        Args:
            drawn_cards: 抽取的牌列表
            spread_type: 牌阵类型
            question: 占卜问题
            card_count: 自定义牌数

        Returns:
            str: 格式化后的占卜结果文本
        """
        spread_info = self.get_spread_info(spread_type, card_count)
        spread_name = spread_info.get("name", spread_type)
        spread_desc = spread_info.get("description", "")
        positions = spread_info.get("positions", [])
        interpretation_hint = spread_info.get("interpretation_hint", "")

        result = "🔮 塔罗占卜结果\n\n"

        if question:
            result += f"📝 问题: {question}\n"

        result += f"🎴 牌阵: {spread_name}"
        if spread_desc:
            result += f"\n💭 说明: {spread_desc}"
        result += "\n"

        result += "\n" + "━" * 50 + "\n\n"

        # 显示抽到的牌
        for idx, item in enumerate(drawn_cards):
            card = item["card"]
            is_reversed = item["reversed"]
            position = positions[idx] if idx < len(positions) else f"位置{idx + 1}"

            card_name = card["name"]
            card_name_en = card.get("name_en", "")
            orientation = "逆位" if is_reversed else "正位"
            keywords = card["keywords_reversed"] if is_reversed else card["keywords_upright"]

            result += f"📍 位置{idx + 1}【{position}】\n"
            result += f"   🃏 {card_name}"
            if card_name_en:
                result += f" ({card_name_en})"
            result += f" - {orientation}\n"

            result += f"   🔑 关键词: {', '.join(keywords)}\n"

            if "element" in card:
                element_name = card["element"]
                result += f"   ⚡ 元素: {element_name}\n"

            result += "\n"

        result += "━" * 50 + "\n\n"

        # 添加解读提示
        if interpretation_hint:
            result += f"💡 解读提示: {interpretation_hint}\n\n"
        else:
            result += "💡 请根据以上牌面和关键词，结合问题背景进行深度解读。\n\n"

        # 添加一些通用的解读建议
        result += "📖 解读建议:\n"
        result += "   • 观察牌面之间的联系和能量流动\n"
        result += "   • 关注正逆位的平衡，寻找需要调整的方向\n"
        result += "   • 将关键词与实际情况结合，找到共鸣点\n"
        if len(drawn_cards) >= 3:
            result += "   • 注意牌阵的整体趋势和转折点\n"

        return result


@tool(response_format="content")
async def tarot_reading(spread_type: str = "three_card", question: str = "", card_count: int = 0) -> str:
    """进行塔罗牌占卜

    适合情感问题、关系咨询、事业发展、决策指引、灵性成长等各类占卜场景。
    支持正逆位解读，返回关键词和解读提示让LLM深度解读。

    Args:
        spread_type (str): 牌阵类型。可选值:
            情感类:
            - "single": 单张牌 (快速洞察)
            - "three_card": 三张牌 (过去-现在-未来)
            - "love_cross": 爱情十字 (5张，深度情感分析)
            - "relationship": 关系牌阵 (7张，全面关系剖析)

            综合分析:
            - "celtic_cross": 凯尔特十字 (10张，最经典全面的牌阵)
            - "horseshoe": 马蹄牌阵 (7张，适合决策)

            专项分析:
            - "spiritual_guidance": 灵性指引 (5张，精神成长)
            - "career_path": 事业发展 (6张，职业规划)
            - "decision_making": 决策指引 (5张，二选一)
            - "year_ahead": 年度展望 (12张，全年趋势)

            自定义:
            - "custom": 自定义牌阵 (需配合card_count参数指定张数，如"十连"用card_count=10)

        question (str): 占卜问题描述 (可选，但建议提供以聚焦能量)

        card_count (int): 自定义抽牌数量 (仅当spread_type="custom"时有效，范围1-78)
            例如: spread_type="custom", card_count=10 表示抽取10张牌

    Returns:
        str: 格式化的占卜结果，包含牌名、正逆位、关键词、解读提示

    Examples:
        单张快速占卜: tarot_reading("single", "今天的运势")
        情感三张牌: tarot_reading("three_card", "我和他的关系发展")
        凯尔特十字: tarot_reading("celtic_cross", "我的人生方向")
        自定义十连: tarot_reading("custom", "感情问题", card_count=10)
    """
    try:
        # 加载塔罗牌数据
        tarot_data = load_tarot_data()
        if not tarot_data:
            return "❌ 塔罗牌数据加载失败，请检查数据文件是否存在"

        # 定义预设牌阵及对应牌数
        predefined_spreads = {
            "single": 1,
            "three_card": 3,
            "love_cross": 5,
            "relationship": 7,
            "celtic_cross": 10,
            "horseshoe": 7,
            "spiritual_guidance": 5,
            "career_path": 6,
            "decision_making": 5,
            "year_ahead": 12,
        }

        # 初始化阅读器
        reader = TarotReader(tarot_data)

        # 检查牌数据是否充足
        if len(reader.all_cards) < 78:
            logger.warning(f"塔罗牌数据不完整，当前仅有 {len(reader.all_cards)} 张牌")

        # 确定抽牌数量
        if spread_type == "custom":
            # 自定义牌阵
            if card_count <= 0:
                return (
                    "❌ 使用自定义牌阵时，请指定card_count参数 (1-78)\n"
                    "例如: tarot_reading('custom', '感情问题', card_count=10)"
                )
            if card_count > 78:
                return f"❌ 抽牌数量不能超过78张，您请求了{card_count}张"
            count = card_count
        elif spread_type in predefined_spreads:
            # 预设牌阵
            count = predefined_spreads[spread_type]
        else:
            # 不支持的牌阵类型
            return (
                f"❌ 不支持的牌阵类型: {spread_type}\n\n"
                f"✅ 支持的牌阵类型:\n"
                f"   情感类: single, three_card, love_cross, relationship\n"
                f"   综合类: celtic_cross, horseshoe\n"
                f"   专项类: spiritual_guidance, career_path, decision_making, year_ahead\n"
                f"   自定义: custom (需指定card_count参数)\n\n"
                f"💡 提示: 对于'十连'等自定义需求，请使用 spread_type='custom', card_count=10"
            )

        # 抽牌
        drawn_cards = reader.draw_cards(count)

        # 格式化结果
        result = reader.format_reading(drawn_cards, spread_type, question, card_count)

        logger.info(
            f"✅ 塔罗占卜完成: 牌阵={spread_type}, 牌数={count}, 问题={question[:30] if question else '无'}..."
        )
        return result

    except Exception as e:
        logger.error("塔罗占卜失败", exc_info=e)
        return f"❌ 塔罗占卜失败: {str(e)}"


@tool(response_format="content")
async def list_tarot_spreads() -> str:
    """列出所有可用的塔罗牌阵及其说明

    Returns:
        str: 所有可用牌阵的详细列表
    """
    try:
        tarot_data = load_tarot_data()
        if not tarot_data:
            return "❌ 无法加载塔罗牌数据"

        spreads = tarot_data.get("spreads", {})

        result = "🎴 塔罗牌阵列表\n\n"
        result += "━" * 50 + "\n\n"

        # 按类别组织牌阵
        categories = {
            "情感关系类": ["single", "three_card", "love_cross", "relationship"],
            "综合分析类": ["celtic_cross", "horseshoe"],
            "专项分析类": ["spiritual_guidance", "career_path", "decision_making", "year_ahead"],
        }

        for category, spread_types in categories.items():
            result += f"📂 {category}\n\n"
            for spread_type in spread_types:
                if spread_type in spreads:
                    spread = spreads[spread_type]
                    name = spread.get("name", spread_type)
                    description = spread.get("description", "")
                    position_count = len(spread.get("positions", []))

                    result += f"   🔹 {spread_type}\n"
                    result += f"      名称: {name} ({position_count}张牌)\n"
                    result += f"      说明: {description}\n\n"

        result += "━" * 50 + "\n\n"
        result += "💡 自定义牌阵:\n"
        result += "   使用 spread_type='custom' 并指定 card_count 参数\n"
        result += "   例如: tarot_reading('custom', '感情问题', card_count=10)\n"

        return result

    except Exception as e:
        logger.error("列出牌阵失败", exc_info=e)
        return f"❌ 列出牌阵失败: {str(e)}"
