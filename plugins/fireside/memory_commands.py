from nonebot import get_driver, on_command, require
from nonebot.adapters.milky.event import MessageEvent

from utils.memory import get_memory_service
from utils.memory_types import MemoryScope

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

memory = get_memory_service()
memory_cmd = on_command("记忆", priority=6, block=True, aliases={"memory", "mem", "记忆库"})

USER_SCOPE_TOKENS = {"个人", "我的", "user", "me"}
GROUP_SCOPE_TOKENS = {"群", "本群", "group", "g"}


def _is_superuser(user_id: str) -> bool:
    superusers = {str(item) for item in getattr(get_driver().config, "superusers", set())}
    return str(user_id) in superusers


def _extract_role(event: MessageEvent) -> tuple[str | None, bool]:
    data = getattr(event, "data", None)
    role_candidates = []

    sender = getattr(data, "sender", None)
    if sender is not None:
        role_candidates.append(sender)

    group = getattr(data, "group", None)
    if group is not None:
        role_candidates.extend([group, getattr(group, "member", None), getattr(group, "sender", None)])

    for candidate in role_candidates:
        if candidate is None:
            continue
        if isinstance(candidate, dict) and "role" in candidate:
            return str(candidate["role"]).lower(), True
        role = getattr(candidate, "role", None)
        if role is not None:
            return str(role).lower(), True
    return None, False


def _can_manage_group_memory(event: MessageEvent) -> bool:
    if _is_superuser(event.get_user_id()):
        return True
    role, role_available = _extract_role(event)
    if not role_available:
        return False
    return role in {"owner", "admin", "administrator"}


def _strip_memory_prefix(text: str) -> str:
    stripped = text.strip()
    for prefix in ("/记忆", "记忆", "/memory", "memory", "/mem", "mem"):
        if stripped.lower().startswith(prefix.lower()):
            return stripped[len(prefix) :].strip()
    return stripped


def _parse_scope(token: str | None) -> MemoryScope | None:
    if token is None:
        return None
    normalized = token.strip().lower()
    if normalized in USER_SCOPE_TOKENS:
        return MemoryScope.USER
    if normalized in GROUP_SCOPE_TOKENS:
        return MemoryScope.GROUP
    return None


def _help_message() -> str:
    return "记忆命令:\n/记忆 查看 [个人|群] [数量]\n/记忆 删除 [个人|群] <memory_id>\n/记忆 清空 [个人|群]"


@memory_cmd.handle()
async def handle_memory_command(event: MessageEvent):
    user_id = event.get_user_id()
    group_id = event.data.group.group_id if event.data.group else None
    text = _strip_memory_prefix(event.get_plaintext())
    if not text:
        await UniMessage.text(_help_message()).send()
        return

    args = text.split()
    action = args[0].lower()

    if action in {"查看", "list", "show"}:
        await handle_memory_list(args=args, user_id=user_id, group_id=group_id)
        return

    if action in {"删除", "delete", "del"}:
        await handle_memory_delete(args=args, event=event, user_id=user_id, group_id=group_id)
        return

    if action in {"清空", "clear"}:
        await handle_memory_clear(args=args, event=event, user_id=user_id, group_id=group_id)
        return

    await UniMessage.text(_help_message()).send()


async def handle_memory_list(args: list[str], user_id: str, group_id: int | None):
    scope = _parse_scope(args[1]) if len(args) > 1 else MemoryScope.USER
    if scope is None:
        scope = MemoryScope.USER
    limit_arg_index = 2 if len(args) > 2 and _parse_scope(args[1]) is not None else 1
    limit = 10
    if len(args) > limit_arg_index:
        try:
            limit = max(1, min(50, int(args[limit_arg_index])))
        except (TypeError, ValueError):
            limit = 10
    if scope == MemoryScope.GROUP and group_id is None:
        await UniMessage.text("当前不在群聊中，无法查看群记忆。").send()
        return
    records = await memory.list_memories(scope=scope, user_id=user_id, group_id=group_id, limit=limit)
    await UniMessage.text(memory.format_memory_list(records)).send()


async def handle_memory_delete(args: list[str], event: MessageEvent, user_id: str, group_id: int | None):
    if len(args) < 2:
        await UniMessage.text("请提供 memory_id。示例: /记忆 删除 <memory_id>").send()
        return
    scope_hint = _parse_scope(args[1]) if len(args) > 1 else None
    if scope_hint is not None and len(args) < 3:
        await UniMessage.text("请提供 memory_id。示例: /记忆 删除 群 <memory_id>").send()
        return
    memory_id = args[2] if scope_hint is not None else args[1]
    if scope_hint == MemoryScope.GROUP and group_id is None:
        await UniMessage.text("当前不在群聊中，无法删除群记忆。").send()
        return
    allow_group_delete = _can_manage_group_memory(event)
    success, message = await memory.soft_delete_memory(
        memory_id=memory_id,
        user_id=user_id,
        group_id=group_id,
        allow_group_delete=allow_group_delete,
        preferred_scope=scope_hint,
    )
    await UniMessage.text(message if success else f"删除失败: {message}").send()


async def handle_memory_clear(args: list[str], event: MessageEvent, user_id: str, group_id: int | None):
    scope = _parse_scope(args[1]) if len(args) > 1 else MemoryScope.USER
    if scope is None:
        scope = MemoryScope.USER
    if scope == MemoryScope.GROUP and group_id is None:
        await UniMessage.text("当前不在群聊中，无法清空群记忆。").send()
        return
    allow_group_delete = _can_manage_group_memory(event)
    count, message = await memory.clear_memories(
        scope=scope,
        user_id=user_id,
        group_id=group_id,
        allow_group_delete=allow_group_delete,
    )
    if scope == MemoryScope.GROUP and not allow_group_delete and count == 0:
        await UniMessage.text("清空失败: 无权限清空群记忆。").send()
        return
    await UniMessage.text(message).send()
