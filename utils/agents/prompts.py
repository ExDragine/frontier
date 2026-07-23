"""Frontier system prompt loading and composition."""

from nonebot import logger

from utils.configs import EnvConfig

from .workspace import PROJECT_ROOT


def load_base_system_prompt(group_id: int | None, wake_word: str | None) -> str:
    toml_prompt = EnvConfig.SYSTEM_PROMPT.strip()
    if not toml_prompt:
        logger.error("❌ env.toml 中未配置 bot.system_prompt")
        return f"You are {EnvConfig.BOT_NAME}, a helpful assistant. [配置错误: system prompt未配置]"

    name = EnvConfig.BOT_NAME
    if wake_word:
        name = wake_word
    elif group_id is not None:
        try:
            from utils.database import GroupSettingsManager, get_engine

            words = GroupSettingsManager(get_engine()).get(group_id, "wake_word")
            if words:
                name = words[0]
        except Exception as exc:
            logger.debug("Wake word injection skipped: %s: %s", type(exc).__name__, exc)

    try:
        return toml_prompt.format(name=name)
    except KeyError as exc:
        logger.error("❌ system prompt 模板变量缺失: %s", exc)
        return f"You are {name}, a helpful assistant. [配置错误: 模板变量缺失]"


def load_prompt_fragment(filename: str, description: str) -> str:
    try:
        return (PROJECT_ROOT / "prompts" / filename).read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("读取%s失败: %s", description, exc)
        return ""


def load_system_prompt(
    group_id: int | None = None,
    wake_word: str | None = None,
    workspace_key: str | None = None,
) -> str:
    """组合基础人设、全局操作规范和渲染规范，注入当前触发的名称。"""
    prompt = load_base_system_prompt(group_id, wake_word)
    prompt_fragments = (
        ("AGENTS.md", "Agent 操作规范"),
        ("rendering.md", "Markdown 渲染规范"),
    )
    for filename, description in prompt_fragments:
        if fragment := load_prompt_fragment(filename, description):
            prompt += f"\n\n{fragment}"
    if workspace_key is not None:
        prompt += (
            "\n\n【当前 Workspace SOUL】"
            f"动态人设文件路径为 `/memory/{workspace_key}/SOUL.md`。"
            "需要持久化稳定人设或长期偏好时，只更新该文件。"
        )
    return prompt
