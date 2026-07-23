"""Signal-LLM gate for browser capture tools."""

from nonebot import logger
from pydantic import BaseModel, Field


class BrowserCaptureIntent(BaseModel):
    """Signal LLM 对用户消息的截图/录屏意图判断结果。"""

    screenshot: bool = Field(
        description="用户是否要求查看某个网页的可视化外观（截图/拍照/快照/看看长啥样/打开看看等）"
    )
    recording: bool = Field(description="用户是否要求录制网页视频（录屏/录制/录视频等）")


async def detect_browser_capture_intent(user_text: str | None) -> set[str]:
    """仅在用户明确要求查看网页外观时暴露截图或录屏工具。"""
    if not user_text:
        return set()
    from utils.signal_llm import signal_structured

    try:
        result: BrowserCaptureIntent = await signal_structured(
            system_prompt=(
                '判断用户消息是否明确表达了"想看到某个网页的可视化外观"的意图。\n\n'
                "以下情况 screenshot 应为 True：\n"
                "- 明确说截图、拍照、快照、截屏、screenshot\n"
                '- "来张XX看看"、"打开XX看看"、"看看XX长啥样"、"XX首页什么样的"\n'
                '- "帮我打开XX网站"、"访问XX页面"并带有查看意图\n\n'
                "以下情况 recording 应为 True：\n"
                "- 明确说录屏、录制、录视频、record/recording\n"
                '- "把XX录下来"、"录一段XX"\n\n'
                "以下情况应返回 False：\n"
                '- 用户只是提到"截图"但不是要求截图（如"你看这个截图"、"截图里的内容"）\n'
                "- 普通问答、搜索、查数据、天气等不涉及网页外观的请求\n"
                '- 模糊回应如"好"、"可以"、"行"\n'
                "- 台风、雷达图、云图、卫星云图、天气图等气象数据可视化请求——这些是数据产品，不是网页截图\n"
                '- "叠加雷达""叠加云图""看看雷达""看看云图"等台风工具内的图层叠加选项'
            ),
            user_prompt=user_text,
            schema=BrowserCaptureIntent,
        )
    except Exception:
        logger.warning("Signal LLM 截图/录屏意图检测失败，默认不暴露工具")
        return set()

    tools: set[str] = set()
    if result.screenshot:
        tools.add("webpage_screenshot")
    if result.recording:
        tools.add("webpage_recording")
    return tools
