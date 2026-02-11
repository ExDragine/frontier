"""周易占卜工具 - 完整版

支持三种传统起卦方法:
1. 三枚铜钱法 - 最传统准确的起卦方式
2. 时间起卦法 - 根据年月日时起卦
3. 报数起卦法 - 通过数字起卦
"""

import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from langchain.tools import tool
from nonebot import logger

# 周易数据文件路径
ICHING_DATA_DIR = Path(__file__).parent.parent / "data" / "iching"
ICHING_INDEX_PATH = ICHING_DATA_DIR / "index.json"
ICHING_TRIGRAMS_PATH = ICHING_DATA_DIR / "trigrams.json"
ICHING_HEXAGRAMS_DIR = ICHING_DATA_DIR / "hexagrams"


def load_iching_index() -> dict:
    """加载周易索引数据

    Returns:
        dict: 索引数据,包含64卦列表
    """
    try:
        with open(ICHING_INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"周易索引文件不存在: {ICHING_INDEX_PATH}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"周易索引JSON解析失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"加载周易索引失败: {e}", exc_info=e)
        return {}


def load_trigrams_data() -> dict:
    """加载八卦数据

    Returns:
        dict: 八卦数据
    """
    try:
        with open(ICHING_TRIGRAMS_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("trigrams", {})
    except Exception as e:
        logger.error(f"加载八卦数据失败: {e}", exc_info=e)
        return {}


def load_hexagram_detail(filename: str) -> dict:
    """加载指定卦的详细数据

    Args:
        filename: 卦象文件名 (如 "01_qian.json")

    Returns:
        dict: 卦象详细数据
    """
    hexagram_path = ICHING_HEXAGRAMS_DIR / filename
    try:
        with open(hexagram_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"卦象文件不存在: {hexagram_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"卦象JSON解析失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"加载卦象详情失败: {e}", exc_info=e)
        return {}


class IChingReader:
    """周易占卜阅读器"""

    def __init__(self, index_data: dict, trigrams_data: dict):
        """初始化周易阅读器

        Args:
            index_data: 64卦索引数据
            trigrams_data: 八卦数据
        """
        self.index_data = index_data
        self.hexagrams_list = index_data.get("hexagrams", [])
        self.trigrams = trigrams_data

        # 构建上下卦映射表,加速查找
        self._build_lookup_table()

    def _build_lookup_table(self):
        """构建上下卦到卦号的映射表"""
        self.hexagram_lookup = {}
        for hex_info in self.hexagrams_list:
            key = (hex_info["upper"], hex_info["lower"])
            self.hexagram_lookup[key] = hex_info

    def divine_by_coins(self) -> dict:
        """三枚铜钱法起卦

        投掷三枚铜钱六次,生成本卦和变卦
        - 三正面(9) = 老阳(动爻) → 阳变阴
        - 两正一反(8) = 少阴 → 阴不变
        - 两反一正(7) = 少阳 → 阳不变
        - 三反面(6) = 老阴(动爻) → 阴变阳

        Returns:
            dict: 占卜结果,包含original_hexagram, changing_hexagram, changing_lines
        """
        lines = []  # 存储六爻的数值(6,7,8,9)
        changing_lines = []  # 动爻位置(1-6)

        # 投掷6次,从下往上构建六爻
        for position in range(1, 7):
            # 模拟投掷三枚铜钱: 正面=3, 反面=2
            coins = [secrets.choice([2, 3]) for _ in range(3)]
            total = sum(coins)  # 6, 7, 8, 9

            lines.append(total)

            # 6(老阴)和9(老阳)是动爻
            if total in [6, 9]:
                changing_lines.append(position)

        # 生成本卦
        original_hex = self._generate_hexagram_from_lines(lines, False)

        # 如果有动爻,计算变卦
        changing_hex = None
        if changing_lines:
            changing_hex = self._generate_hexagram_from_lines(lines, True)

        return {
            "original_hexagram": original_hex,
            "changing_hexagram": changing_hex,
            "changing_lines": changing_lines,
            "method": "coin",
            "lines_values": lines,  # 保存原始爻值用于显示
        }

    def divine_by_time(
        self, year: int | None = None, month: int | None = None, day: int | None = None, hour: int | None = None
    ) -> dict:
        """时间起卦法

        Args:
            year: 年份(不提供则用当前时间)
            month: 月份(1-12)
            day: 日期(1-31)
            hour: 时辰(1-12, 子时=1, 丑时=2, ..., 亥时=12)

        Returns:
            dict: 占卜结果
        """
        now = datetime.now()
        # 传统命理中，23点之后就是“第二天”了
        is_next_day = now.hour >= 23
        if year is None:
            # 注意：如果是12月31日23:00，年份也可能需要进位，
            # 建议直接用 timedelta 处理日期进位
            target_time = now + timedelta(hours=1) if is_next_day else now
            year = target_time.year
            month = target_time.month
            day = target_time.day
        if month is None:
            month = now.month
        if day is None:
            day = now.day
        if hour is None:
            hour = ((now.hour + 1) // 2 % 12) + 1

        # 参数验证
        if not (1900 <= year <= 2100):
            raise ValueError(f"年份无效: {year}, 应在1900-2100之间")
        if not (1 <= month <= 12):
            raise ValueError(f"月份无效: {month}, 应在1-12之间")
        if not (1 <= day <= 31):
            raise ValueError(f"日期无效: {day}, 应在1-31之间")
        if not (1 <= hour <= 12):
            raise ValueError(f"时辰无效: {hour}, 应在1-12之间")

        # 八卦序数映射: 1=乾, 2=兑, 3=离, 4=震, 5=巽, 6=坎, 7=艮, 8=坤
        trigram_order = ["", "乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

        # 计算上卦、下卦、动爻
        sum_ymd = year + month + day
        upper_num = (sum_ymd % 8) or 8  # 余数0时取8
        lower_num = ((sum_ymd + hour) % 8) or 8
        changing_line = ((sum_ymd + hour) % 6) or 6  # 1-6

        upper_trigram = trigram_order[upper_num]
        lower_trigram = trigram_order[lower_num]

        # 查找对应的卦象
        original_hex = self._find_hexagram_by_trigrams(upper_trigram, lower_trigram)

        # 计算变卦(翻转动爻)
        changing_hex = self._calculate_changing_hexagram_simple(original_hex, [changing_line])

        time_info = f"{year}年{month}月{day}日 {self._hour_to_chinese(hour)}"

        return {
            "original_hexagram": original_hex,
            "changing_hexagram": changing_hex,
            "changing_lines": [changing_line],
            "method": "time",
            "time_info": time_info,
        }

    def divine_by_numbers(self, num1: int | None = None, num2: int | None = None) -> dict:
        """报数起卦法

        Args:
            num1: 第一个数字(1-99999, 不提供则随机)
            num2: 第二个数字(1-99999, 不提供则随机)

        Returns:
            dict: 占卜结果
        """
        # 如果未提供数字,随机生成
        if num1 is None:
            num1 = secrets.randbelow(9999) + 1
        if num2 is None:
            num2 = secrets.randbelow(9999) + 1

        # 参数验证
        if not (1 <= num1 <= 99999):
            raise ValueError(f"数字1超出范围: {num1}, 应在1-99999之间")
        if not (1 <= num2 <= 99999):
            raise ValueError(f"数字2超出范围: {num2}, 应在1-99999之间")

        # 八卦序数映射
        trigram_order = ["", "乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

        upper_num = (num1 % 8) or 8
        lower_num = (num2 % 8) or 8
        changing_line = ((num1 + num2) % 6) or 6

        upper_trigram = trigram_order[upper_num]
        lower_trigram = trigram_order[lower_num]

        original_hex = self._find_hexagram_by_trigrams(upper_trigram, lower_trigram)
        changing_hex = self._calculate_changing_hexagram_simple(original_hex, [changing_line])

        return {
            "original_hexagram": original_hex,
            "changing_hexagram": changing_hex,
            "changing_lines": [changing_line],
            "method": "number",
            "numbers": (num1, num2),
        }

    def _generate_hexagram_from_lines(self, lines: list[int], is_changing: bool) -> dict:
        """根据六爻数值生成卦象

        Args:
            lines: 六个爻的数值(6,7,8,9), 从初爻到上爻
            is_changing: 是否生成变卦

        Returns:
            dict: 卦象数据
        """
        # 将爻值转换为二进制(1=阳, 0=阴)
        binary_lines = []
        for i, value in enumerate(lines):
            position = i + 1
            if is_changing and position in [i + 1 for i, v in enumerate(lines) if v in [6, 9]]:
                # 变卦: 老阳变阴, 老阴变阳
                if value == 9:
                    binary_lines.append(0)  # 阳变阴
                elif value == 6:
                    binary_lines.append(1)  # 阴变阳
                else:
                    # 7和8不变
                    binary_lines.append(1 if value in [7, 9] else 0)
            else:
                # 本卦: 7和9为阳, 6和8为阴
                binary_lines.append(1 if value in [7, 9] else 0)

        # 下三爻(初、二、三爻)组成下卦
        lower_trigram = self._binary_to_trigram(binary_lines[0:3])
        # 上三爻(四、五、上爻)组成上卦
        upper_trigram = self._binary_to_trigram(binary_lines[3:6])

        return self._find_hexagram_by_trigrams(upper_trigram, lower_trigram)

    def _find_hexagram_by_trigrams(self, upper: str, lower: str) -> dict:
        """根据上下卦查找对应的64卦

        Args:
            upper: 上卦名称
            lower: 下卦名称

        Returns:
            dict: 卦象基本信息(从index中)
        """
        key = (upper, lower)
        if key in self.hexagram_lookup:
            hex_info = self.hexagram_lookup[key]
            # 加载详细数据
            detail = load_hexagram_detail(hex_info["file"])
            if detail:
                return detail
            else:
                # 如果详细数据加载失败,返回索引中的基本信息
                return hex_info

        raise ValueError(f"未找到卦象: 上卦{upper}, 下卦{lower}")

    def _calculate_changing_hexagram_simple(self, original_hex: dict, changing_lines: list[int]) -> dict:
        """根据动爻计算变卦(简化版,用于时间和报数起卦)

        Args:
            original_hex: 原卦数据
            changing_lines: 动爻位置列表

        Returns:
            dict: 变卦数据
        """
        # 获取原卦的六爻阴阳
        lines_binary = self._hexagram_to_binary(original_hex)

        # 翻转动爻
        for line_pos in changing_lines:
            idx = line_pos - 1  # 转换为0-5索引
            lines_binary[idx] = 1 - lines_binary[idx]  # 0变1, 1变0

        # 根据新的六爻查找变卦
        new_lower = self._binary_to_trigram(lines_binary[0:3])
        new_upper = self._binary_to_trigram(lines_binary[3:6])

        return self._find_hexagram_by_trigrams(new_upper, new_lower)

    def _hexagram_to_binary(self, hexagram: dict) -> list[int]:
        """将卦象转换为二进制表示

        Args:
            hexagram: 卦象数据

        Returns:
            list[int]: [初爻, 二爻, ..., 上爻], 1为阳0为阴
        """
        lower_trigram_name = hexagram.get("lower_trigram")
        upper_trigram_name = hexagram.get("upper_trigram")

        lower_binary = self.trigrams[lower_trigram_name]["binary"]
        upper_binary = self.trigrams[upper_trigram_name]["binary"]

        return lower_binary + upper_binary

    def _binary_to_trigram(self, binary: list[int]) -> str:
        """从三爻的二进制确定八卦名称

        Args:
            binary: 三个爻的二进制表示 [下爻, 中爻, 上爻]

        Returns:
            str: 八卦名称
        """
        for name, data in self.trigrams.items():
            if data["binary"] == binary:
                return name

        raise ValueError(f"未找到对应的八卦: {binary}")

    def _hour_to_chinese(self, hour: int) -> str:
        """将时辰数字转换为中文

        Args:
            hour: 时辰数字(1-12)

        Returns:
            str: 中文时辰名
        """
        hour_names = [
            "",
            "子时",
            "丑时",
            "寅时",
            "卯时",
            "辰时",
            "巳时",
            "午时",
            "未时",
            "申时",
            "酉时",
            "戌时",
            "亥时",
        ]
        return hour_names[hour] if 1 <= hour <= 12 else f"{hour}时"

    def format_divination_result(
        self,
        original_hex: dict,
        changing_hex: dict | None,
        changing_lines: list[int],
        method: str,
        question: str,
        extra_info: Any = None,
        lines_values: list[int] | None = None,
    ) -> str:
        """格式化占卜结果为清晰的文本输出

        Args:
            original_hex: 本卦数据
            changing_hex: 变卦数据(可选)
            changing_lines: 动爻位置列表
            method: 起卦方法
            question: 占卜问题
            extra_info: 额外信息(时间或数字)
            lines_values: 爻值列表(仅铜钱法使用)

        Returns:
            str: 格式化的占卜结果
        """
        method_names = {"coin": "三枚铜钱法", "time": "时间起卦法", "number": "报数起卦法"}

        result = "☯️ 周易占卜结果\n\n"

        # 问题和方法
        if question:
            result += f"📝 占问: {question}\n"
        result += f"🎲 方法: {method_names.get(method, method)}\n"

        if extra_info:
            if isinstance(extra_info, tuple):
                result += f"🔢 数字: {extra_info[0]}, {extra_info[1]}\n"
            else:
                result += f"⏰ 时间: {extra_info}\n"

        result += "\n" + "━" * 50 + "\n\n"

        # 本卦信息
        result += f"📿 本卦: {original_hex['full_symbol']} 第{original_hex['number']}卦 - {original_hex['name']}卦\n\n"
        result += f"   🎴 卦名: {original_hex['nature']}\n"
        result += f"   🔺 上卦: {original_hex['upper_trigram']} {original_hex['upper_symbol']}\n"
        result += f"   🔻 下卦: {original_hex['lower_trigram']} {original_hex['lower_symbol']}\n"
        result += f"   ⚡ 五行: {original_hex['element']}\n\n"

        # 卦象图形
        result += "   卦象:\n"
        result += self._draw_hexagram_lines(original_hex, changing_lines, lines_values)
        result += "\n"

        # 卦辞
        result += f"📜 卦辞: {original_hex['judgment']['text']}\n"
        result += f"   白话: {original_hex['judgment']['vernacular']}\n\n"

        # 象辞
        result += f"📖 象辞: {original_hex['image']['text']}\n"
        result += f"   白话: {original_hex['image']['vernacular']}\n\n"

        # 动爻信息
        if changing_lines:
            result += "━" * 50 + "\n\n"
            result += f"⚡ 动爻 ({len(changing_lines)}个):\n\n"

            yao_names = ["初", "二", "三", "四", "五", "上"]
            for line_pos in changing_lines:
                if line_pos <= len(original_hex["lines"]):
                    line = original_hex["lines"][line_pos - 1]
                    result += f"   {yao_names[line_pos - 1]}爻动:\n"
                    result += f"      {line['text']}\n"
                    result += f"      {line['vernacular']}\n\n"

        # 变卦信息
        if changing_hex:
            result += "━" * 50 + "\n\n"
            result += (
                f"🔄 变卦: {changing_hex['full_symbol']} 第{changing_hex['number']}卦 - {changing_hex['name']}卦\n\n"
            )
            result += f"   🎴 卦名: {changing_hex['nature']}\n"
            result += f"   ⚡ 五行: {changing_hex['element']}\n\n"

            result += "   卦象:\n"
            result += self._draw_hexagram_lines(changing_hex, [])
            result += "\n"

            result += f"📜 卦辞: {changing_hex['judgment']['text']}\n"
            result += f"   白话: {changing_hex['judgment']['vernacular']}\n\n"

        # 解读提示
        result += "━" * 50 + "\n\n"
        result += "💡 解读提示:\n\n"

        hints = original_hex["interpretation_hints"]
        result += f"🔮 运势: {hints['fortune']}\n"
        result += f"💼 事业: {hints['career']}\n"
        result += f"💕 感情: {hints['relationship']}\n"
        if "health" in hints:
            result += f"🏥 健康: {hints['health']}\n"
        result += f"📝 建议: {hints['advice']}\n\n"

        # 通用解读说明
        result += "━" * 50 + "\n\n"
        result += "📖 占卜说明:\n"
        result += "   • 本卦代表当前状态和主要趋势\n"
        if changing_lines:
            result += "   • 动爻表示变化的关键点,需特别关注\n"
            result += "   • 变卦指示未来发展方向和结果\n"
            result += "   • 综合本卦、动爻、变卦进行解读\n"
        else:
            result += "   • 无动爻表示事态相对稳定\n"
            result += "   • 专注本卦的卦辞和象辞进行解读\n"

        return result

    def _draw_hexagram_lines(
        self, hexagram: dict, changing_lines: list[int], lines_values: list[int] | None = None
    ) -> str:
        """绘制卦象的六爻图形

        Args:
            hexagram: 卦象数据
            changing_lines: 动爻位置(用于标记)
            lines_values: 爻值列表(6,7,8,9), 仅铜钱法使用

        Returns:
            str: ASCII艺术形式的卦象
        """
        # 从卦象符号推断六爻
        lines_binary = self._hexagram_to_binary(hexagram)

        yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
        result = ""

        # 从上往下绘制(显示顺序与计算顺序相反)
        for i in range(5, -1, -1):
            is_yang = lines_binary[i] == 1
            is_changing = (i + 1) in changing_lines

            # 阳爻 ━━━━━  阴爻 ━━ ━━
            if is_yang:
                line_symbol = "━━━━━"
            else:
                line_symbol = "━━ ━━"

            # 标记动爻
            change_marker = " ◯" if is_changing else "  "

            # 如果有爻值,显示爻值类型
            yao_type = ""
            if lines_values and i < len(lines_values):
                value = lines_values[i]
                if value == 9:
                    yao_type = " (老阳)"
                elif value == 6:
                    yao_type = " (老阴)"
                elif value == 7:
                    yao_type = " (少阳)"
                elif value == 8:
                    yao_type = " (少阴)"

            result += f"      {line_symbol}{change_marker}  {yao_names[i]}{yao_type}\n"

        return result


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
async def list_iching_hexagrams(filter_type: str = "all") -> str:
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
                    for h, detail in items:
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
