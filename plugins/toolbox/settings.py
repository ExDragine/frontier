"""Toolbox settings commands and supporting logic."""

from dataclasses import dataclass

from arclet.alconna import Alconna, Args, Arparma, MultiVar, Subcommand
from nonebot import on_command
from nonebot.adapters.milky.event import MessageEvent

from models import get_model_display_name
from utils.alconna import AlconnaQuery, Query, UniMessage, on_alconna
from utils.configs import EnvConfig, get_provider_profile
from utils.database import GroupSettingsManager, get_engine

model_cmd = on_command("model", priority=2, block=True, aliases={"模型", "模型设置"})


settings = on_alconna(
    Alconna(
        "set",
        Subcommand("model", alias={"模型"}, help_text="查看当前模型配置"),
        Subcommand(
            "wake",
            Subcommand(
                "add",
                Args["word", MultiVar(str, "*")],
                alias={"添加"},
                help_text="添加群聊唤醒词",
            ),
            Subcommand(
                "remove",
                Args["word", MultiVar(str, "*")],
                alias={"移除", "删除"},
                help_text="移除群聊唤醒词",
            ),
            Subcommand("clear", alias={"清空"}, help_text="清空群聊唤醒词"),
            alias={"唤醒词"},
            help_text="查看或管理群聊唤醒词",
        ),
    ),
    aliases={"设置"},
    skip_for_unmatch=False,
    auto_send_output=False,
    use_cmd_start=True,
    priority=2,
    block=True,
)


_WAKE_ADD_WORDS_QUERY = AlconnaQuery("wake.add.word")


_WAKE_REMOVE_WORDS_QUERY = AlconnaQuery("wake.remove.word")


@dataclass(frozen=True, slots=True)
class SetMenuItem:
    command: str
    description: str
    group_only: bool = False
    admin_only: bool = False


SET_MENU_ITEMS = (
    SetMenuItem("/set model", "查看当前模型配置（兼容 /model）"),
    SetMenuItem("/set wake", "查看当前群唤醒词", group_only=True),
    SetMenuItem("/set wake add <词>", "添加唤醒词", group_only=True, admin_only=True),
    SetMenuItem("/set wake remove <词>", "移除唤醒词", group_only=True, admin_only=True),
    SetMenuItem("/set wake clear", "清空唤醒词", group_only=True, admin_only=True),
)


SET_WAKE_KEY = "wake_word"


def _model_display_name(model: str, provider: str) -> str:
    try:
        provider_type = str(get_provider_profile(provider).get("type", "")).strip().lower()
    except ValueError:
        provider_type = ""
    return get_model_display_name(provider_type, model)


def _event_group_id(event: MessageEvent) -> int | None:
    if getattr(event.data, "message_scene", None) != "group":
        return None
    group = getattr(event.data, "group", None)
    group_id = getattr(group, "group_id", None)
    return int(group_id) if group_id is not None else None


def _is_group_admin_or_owner(event: MessageEvent) -> bool:
    """检查发送者是否为群主或管理员。"""
    if _event_group_id(event) is None:
        return False
    member = getattr(event.data, "group_member", None)
    return bool(member and member.role in ("admin", "owner"))


def _render_set_menu(event: MessageEvent) -> str:
    is_group = _event_group_id(event) is not None
    is_admin = _is_group_admin_or_owner(event)
    visible_items = [
        item
        for item in SET_MENU_ITEMS
        if (is_group or not item.group_only) and (is_admin or not item.admin_only)
    ]
    lines = [
        f"{'└' if index == len(visible_items) - 1 else '├'} {item.command} — {item.description}"
        for index, item in enumerate(visible_items)
    ]
    return "⚙️ 设置菜单\n" + "\n".join(lines)


def _current_model_summary() -> str:
    models = [
        (
            "对话模型",
            _model_display_name(EnvConfig.ADVAN_MODEL, EnvConfig.ADVAN_MODEL_PROVIDER),
        ),
        (
            "辅助模型",
            _model_display_name(EnvConfig.BASIC_MODEL, EnvConfig.BASIC_MODEL_PROVIDER),
        ),
    ]
    if EnvConfig.PAINT_MODULE_ENABLED:
        models.append(
            (
                "绘图模型",
                _model_display_name(EnvConfig.PAINT_MODEL, EnvConfig.PAINT_MODEL_PROVIDER),
            )
        )
    if EnvConfig.VIDEO_MODULE_ENABLED:
        models.append(
            (
                "视频模型",
                _model_display_name(EnvConfig.VIDEO_MODEL, EnvConfig.VIDEO_MODEL_PROVIDER),
            )
        )

    model_lines = [
        f"{'└' if index == len(models) - 1 else '├'} {label}：{model}"
        for index, (label, model) in enumerate(models)
    ]
    return "🤖 当前模型配置\n" + "\n".join(model_lines)


async def _send_current_model_summary() -> None:
    await UniMessage.text(_current_model_summary()).send()


async def _is_plain_wake(_event, _bot, _state, result: Arparma) -> bool:
    wake = result.query("wake", None)
    return wake is not None and not wake.subcommands


def _group_settings() -> GroupSettingsManager:
    return GroupSettingsManager(get_engine())


async def _set_wake_show(group_id: int) -> str:
    words = _group_settings().get(group_id, SET_WAKE_KEY)
    if not words:
        return f"当前群未设置唤醒词，使用默认唤醒词「{EnvConfig.BOT_NAME}」。"
    return f"当前群唤醒词：{', '.join(words)}"


async def _set_wake_add(group_id: int, word: str) -> str:
    if not word.strip():
        return "⚠️ 唤醒词不能为空。"
    word = word.strip()
    existing = _group_settings().get(group_id, SET_WAKE_KEY)
    if word in existing:
        return f"⚠️ 唤醒词「{word}」已存在。当前唤醒词：{', '.join(existing)}"
    _group_settings().set(group_id, SET_WAKE_KEY, word)
    updated = _group_settings().get(group_id, SET_WAKE_KEY)
    return f"✅ 唤醒词「{word}」已添加。当前唤醒词：{', '.join(updated)}"


async def _set_wake_remove(group_id: int, word: str) -> str:
    word = word.strip()
    if not word:
        return "⚠️ 要移除的唤醒词不能为空。"
    removed = _group_settings().remove(group_id, SET_WAKE_KEY, word)
    if not removed:
        existing = _group_settings().get(group_id, SET_WAKE_KEY)
        if existing:
            return f"⚠️ 未找到唤醒词「{word}」。当前唤醒词：{', '.join(existing)}"
        return f"⚠️ 未找到唤醒词「{word}」，且当前群未设置任何唤醒词。"
    words = _group_settings().get(group_id, SET_WAKE_KEY)
    if words:
        return f"✅ 唤醒词「{word}」已移除。当前唤醒词：{', '.join(words)}"
    return f"✅ 唤醒词「{word}」已移除。将使用默认唤醒词「{EnvConfig.BOT_NAME}」。"


async def _set_wake_clear(group_id: int) -> str:
    count = _group_settings().clear(group_id, SET_WAKE_KEY)
    if count == 0:
        return f"当前群未设置唤醒词，无需清空。使用默认唤醒词「{EnvConfig.BOT_NAME}」。"
    return f"✅ 已清空 {count} 个唤醒词，将使用默认唤醒词「{EnvConfig.BOT_NAME}」。"


@settings.assign("$main")
async def handle_set_menu(event: MessageEvent):
    await UniMessage.text(_render_set_menu(event)).send()


@settings.assign("model")
async def handle_set_model():
    await _send_current_model_summary()


@settings.assign("wake", additional=_is_plain_wake)
async def handle_set_wake_show(event: MessageEvent):
    group_id = _event_group_id(event)
    if group_id is None:
        await UniMessage.text("⚠️ 此命令仅支持群聊。").send()
        return
    await UniMessage.text(await _set_wake_show(group_id)).send()


@settings.assign("wake.add")
async def handle_set_wake_add(
    event: MessageEvent,
    words: Query[tuple[str, ...]] = _WAKE_ADD_WORDS_QUERY,
):
    group_id = _event_group_id(event)
    if group_id is None:
        await UniMessage.text("⚠️ 此命令仅支持群聊。").send()
        return
    if not _is_group_admin_or_owner(event):
        await UniMessage.text("⚠️ 只有群主或管理员才能修改唤醒词。").send()
        return
    word = " ".join(words.result)
    if not word:
        await UniMessage.text("⚠️ 用法：/set wake add <唤醒词>").send()
        return
    await UniMessage.text(await _set_wake_add(group_id, word)).send()


@settings.assign("wake.remove")
async def handle_set_wake_remove(
    event: MessageEvent,
    words: Query[tuple[str, ...]] = _WAKE_REMOVE_WORDS_QUERY,
):
    group_id = _event_group_id(event)
    if group_id is None:
        await UniMessage.text("⚠️ 此命令仅支持群聊。").send()
        return
    if not _is_group_admin_or_owner(event):
        await UniMessage.text("⚠️ 只有群主或管理员才能修改唤醒词。").send()
        return
    word = " ".join(words.result)
    if not word:
        await UniMessage.text("⚠️ 用法：/set wake remove <唤醒词>").send()
        return
    await UniMessage.text(await _set_wake_remove(group_id, word)).send()


@settings.assign("wake.clear")
async def handle_set_wake_clear(event: MessageEvent):
    group_id = _event_group_id(event)
    if group_id is None:
        await UniMessage.text("⚠️ 此命令仅支持群聊。").send()
        return
    if not _is_group_admin_or_owner(event):
        await UniMessage.text("⚠️ 只有群主或管理员才能修改唤醒词。").send()
        return
    await UniMessage.text(await _set_wake_clear(group_id)).send()


@model_cmd.handle()
async def handle_model():
    await _send_current_model_summary()

