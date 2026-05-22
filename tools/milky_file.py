from pathlib import Path

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from nonebot import get_bot

from utils.milky_tools import binary_kwargs_from_uri, format_files_info, resolve_group_id, resolve_user_id


def _file_name_from_uri(file_uri: str, file_name: str | None) -> str | None:
    if file_name:
        return file_name
    kwargs = binary_kwargs_from_uri(file_uri)
    if path := kwargs.get("path"):
        return Path(path).name
    return None


@tool(response_format="content")
async def upload_private_file(
    file_uri: str,
    file_name: str | None = None,
    user_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """上传私聊文件。
    Args:
        file_uri: 文件 URI，支持 file://、http(s)://、base64:// 或本地文件路径
        file_name: 文件名；使用 URL/base64 时建议显式提供
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id, error = resolve_user_id(user_id, config)
    if error:
        return error
    kwargs = binary_kwargs_from_uri(file_uri)
    resolved_file_name = _file_name_from_uri(file_uri, file_name)
    if not resolved_file_name:
        return "请提供 file_name。"
    file_id = await get_bot().upload_private_file(user_id=resolved_user_id, **kwargs, file_name=resolved_file_name)
    return f"已上传私聊文件 {resolved_file_name}，file_id={file_id}"


@tool(response_format="content")
async def upload_group_file(
    file_uri: str,
    file_name: str | None = None,
    parent_folder_id: str | None = None,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """上传群文件。
    Args:
        file_uri: 文件 URI，支持 file://、http(s)://、base64:// 或本地文件路径
        file_name: 文件名；使用 URL/base64 时建议显式提供
        parent_folder_id: 可选父文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    kwargs = binary_kwargs_from_uri(file_uri)
    resolved_file_name = _file_name_from_uri(file_uri, file_name)
    if not resolved_file_name:
        return "请提供 file_name。"
    file_id = await get_bot().upload_group_file(
        group_id=resolved_group_id,
        **kwargs,
        file_name=resolved_file_name,
        parent_folder_id=parent_folder_id,
    )
    return f"已上传群 {resolved_group_id} 文件 {resolved_file_name}，file_id={file_id}"


@tool(response_format="content")
async def get_private_file_download_url(
    file_id: str,
    file_hash: str,
    user_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """获取私聊文件下载链接。
    Args:
        file_id: 文件 ID
        file_hash: 文件 TriSHA1 哈希
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id, error = resolve_user_id(user_id, config)
    if error:
        return error
    return await get_bot().get_private_file_download_url(
        user_id=resolved_user_id, file_id=file_id, file_hash=file_hash
    )


@tool(response_format="content")
async def get_group_file_download_url(
    file_id: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """获取群文件下载链接。
    Args:
        file_id: 文件 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    return await get_bot().get_group_file_download_url(group_id=resolved_group_id, file_id=file_id)


@tool(response_format="content")
async def get_group_files(
    parent_folder_id: str | None = None,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """获取群文件列表。
    Args:
        parent_folder_id: 可选父文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    info = await get_bot().get_group_files(group_id=resolved_group_id, parent_folder_id=parent_folder_id)
    return format_files_info(resolved_group_id, info)


@tool(response_format="content")
async def move_group_file(
    file_id: str,
    parent_folder_id: str = "/",
    target_folder_id: str = "/",
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """移动群文件。
    Args:
        file_id: 文件 ID
        parent_folder_id: 文件当前所在文件夹 ID
        target_folder_id: 目标文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().move_group_file(
        group_id=resolved_group_id,
        file_id=file_id,
        parent_folder_id=parent_folder_id,
        target_folder_id=target_folder_id,
    )
    return f"已将群 {resolved_group_id} 文件 {file_id} 从 {parent_folder_id} 移动到 {target_folder_id}"


@tool(response_format="content")
async def rename_group_file(
    file_id: str,
    new_file_name: str,
    parent_folder_id: str = "/",
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """重命名群文件。
    Args:
        file_id: 文件 ID
        new_file_name: 新文件名
        parent_folder_id: 文件所在文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().rename_group_file(
        group_id=resolved_group_id,
        file_id=file_id,
        parent_folder_id=parent_folder_id,
        new_file_name=new_file_name,
    )
    return f"已将群 {resolved_group_id} 文件 {file_id} 重命名为：{new_file_name}"


@tool(response_format="content")
async def delete_group_file(
    file_id: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """删除群文件。
    Args:
        file_id: 文件 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().delete_group_file(group_id=resolved_group_id, file_id=file_id)
    return f"已删除群 {resolved_group_id} 文件 {file_id}"


@tool(response_format="content")
async def create_group_folder(
    folder_name: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """创建群文件夹。
    Args:
        folder_name: 文件夹名
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    folder_id = await get_bot().create_group_folder(group_id=resolved_group_id, folder_name=folder_name)
    return f"已在群 {resolved_group_id} 创建文件夹 {folder_name}，folder_id={folder_id}"


@tool(response_format="content")
async def rename_group_folder(
    folder_id: str,
    new_folder_name: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """重命名群文件夹。
    Args:
        folder_id: 文件夹 ID
        new_folder_name: 新文件夹名
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().rename_group_folder(
        group_id=resolved_group_id,
        folder_id=folder_id,
        new_folder_name=new_folder_name,
    )
    return f"已将群 {resolved_group_id} 文件夹 {folder_id} 重命名为：{new_folder_name}"


@tool(response_format="content")
async def delete_group_folder(
    folder_id: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """删除群文件夹。
    Args:
        folder_id: 文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().delete_group_folder(group_id=resolved_group_id, folder_id=folder_id)
    return f"已删除群 {resolved_group_id} 文件夹 {folder_id}"
