from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot

from utils.milky_tools import (
    binary_kwargs_from_uri,
    format_key_values,
    format_records,
    resolve_group_id,
)


@tool(response_format="content")
async def get_login_info() -> str:
    """获取当前登录 QQ 的基础信息。"""
    info = await get_bot().get_login_info()
    return format_key_values(info, ("uin", "nickname"))


@tool(response_format="content")
async def get_impl_info() -> str:
    """获取当前 Milky 协议端信息。"""
    info = await get_bot().get_impl_info()
    return format_key_values(
        info,
        ("impl_name", "impl_version", "qq_protocol_version", "qq_protocol_type", "milky_version"),
    )


@tool(response_format="content")
async def get_user_profile(user_id: int) -> str:
    """获取用户资料。
    Args:
        user_id: 用户 QQ 号
    """
    profile = await get_bot().get_user_profile(user_id=user_id)
    return format_key_values(profile)


@tool(response_format="content")
async def get_friend_list(no_cache: bool = False) -> str:
    """获取好友列表。
    Args:
        no_cache: 是否强制不使用缓存
    """
    friends = await get_bot().get_friend_list(no_cache=no_cache)
    return format_records("好友列表", friends, ("user_id", "nickname", "remark", "qid", "sex"))


@tool(response_format="content")
async def get_friend_info(user_id: int, no_cache: bool = False) -> str:
    """获取好友信息。
    Args:
        user_id: 好友 QQ 号
        no_cache: 是否强制不使用缓存
    """
    friend = await get_bot().get_friend_info(user_id=user_id, no_cache=no_cache)
    return format_key_values(friend)


@tool(response_format="content")
async def get_group_list(no_cache: bool = False) -> str:
    """获取群列表。
    Args:
        no_cache: 是否强制不使用缓存
    """
    groups = await get_bot().get_group_list(no_cache=no_cache)
    return format_records("群列表", groups, ("group_id", "group_name", "member_count", "max_member_count", "remark"))


@tool(response_format="content")
async def get_group_info(
    group_id: int | None = None,
    no_cache: bool = False,
    config: RunnableConfig = None,
) -> str:
    """获取群信息。
    Args:
        group_id: 可选群号，未传时使用当前群聊
        no_cache: 是否强制不使用缓存
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    group = await get_bot().get_group_info(group_id=resolved_group_id, no_cache=no_cache)
    return format_key_values(group)


@tool(response_format="content")
async def get_group_member_list(
    group_id: int | None = None,
    no_cache: bool = False,
    config: RunnableConfig = None,
) -> str:
    """获取群成员列表。
    Args:
        group_id: 可选群号，未传时使用当前群聊
        no_cache: 是否强制不使用缓存
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    members = await get_bot().get_group_member_list(group_id=resolved_group_id, no_cache=no_cache)
    return format_records(f"群 {resolved_group_id} 成员", members, ("user_id", "nickname", "card", "title", "role"))


@tool(response_format="content")
async def get_group_member_info(
    user_id: int,
    group_id: int | None = None,
    no_cache: bool = False,
    config: RunnableConfig = None,
) -> str:
    """获取群成员信息。
    Args:
        user_id: 成员 QQ 号
        group_id: 可选群号，未传时使用当前群聊
        no_cache: 是否强制不使用缓存
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    member = await get_bot().get_group_member_info(group_id=resolved_group_id, user_id=user_id, no_cache=no_cache)
    return format_key_values(member)


@tool(response_format="content")
async def get_peer_pins() -> str:
    """获取置顶好友和群列表。"""
    pins = await get_bot().get_peer_pins()
    friends = format_records("置顶好友", pins.get("friends", []), ("user_id", "nickname", "remark"))
    groups = format_records("置顶群", pins.get("groups", []), ("group_id", "group_name", "member_count"))
    return f"{friends}\n{groups}"


@tool(response_format="content")
async def set_peer_pin(message_scene: str, peer_id: int, is_pinned: bool = True) -> str:
    """设置或取消置顶好友/群会话。
    Args:
        message_scene: 会话场景，friend、group 或 temp
        peer_id: 好友 QQ 号或群号
        is_pinned: True 置顶，False 取消置顶
    """
    await get_bot().set_peer_pin(message_scene=message_scene, peer_id=peer_id, is_pinned=is_pinned)
    action = "置顶" if is_pinned else "取消"
    return f"已{action} {message_scene} 会话 {peer_id} 的置顶"


@tool(response_format="content")
async def set_avatar(image_uri: str) -> str:
    """设置当前 QQ 账号头像，支持 file://、http(s)://、base64:// 或本地文件路径。
    Args:
        image_uri: 头像图片 URI
    """
    await get_bot().set_avatar(**binary_kwargs_from_uri(image_uri))
    return "已更新当前 QQ 账号头像"


@tool(response_format="content")
async def set_nickname(new_nickname: str) -> str:
    """设置当前 QQ 账号昵称。
    Args:
        new_nickname: 新昵称
    """
    await get_bot().set_nickname(new_nickname=new_nickname)
    return f"已将当前 QQ 账号昵称设置为：{new_nickname}"


@tool(response_format="content")
async def set_bio(new_bio: str) -> str:
    """设置当前 QQ 账号个性签名。
    Args:
        new_bio: 新个性签名
    """
    await get_bot().set_bio(new_bio=new_bio)
    return "已更新当前 QQ 账号个性签名"


@tool(response_format="content")
async def get_custom_face_url_list() -> str:
    """获取自定义表情 URL 列表。"""
    urls = await get_bot().get_custom_face_url_list()
    if not urls:
        return "自定义表情 URL 列表为空。"
    return "自定义表情 URL：\n" + "\n".join(f"- {url}" for url in urls)


@tool(response_format="content")
async def get_cookies(domain: str) -> str:
    """获取指定域名 Cookie。
    Args:
        domain: 域名，例如 qq.com
    """
    return await get_bot().get_cookies(domain=domain)


@tool(response_format="content")
async def get_csrf_token() -> str:
    """获取 CSRF Token。"""
    return await get_bot().get_csrf_token()
