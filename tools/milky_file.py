import base64
import logging
from pathlib import Path
from typing import cast

from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot

from utils.agent_context import FrontierRuntimeContext
from utils.milky_tools import (
    ToolInputError,
    binary_kwargs_from_uri,
    configurable,
    format_files_info,
    input_error_text,
    require_group_id,
    require_user_id,
)

_DEFAULT_CONFIG = cast(RunnableConfig, None)
_DEFAULT_RUNTIME = cast(ToolRuntime[FrontierRuntimeContext, dict], None)
logger = logging.getLogger(__name__)


def _prepare_upload(file_uri: str, file_name: str | None, config: RunnableConfig) -> tuple[dict[str, str], str | None]:
    settings = configurable(config)
    workspace_dir = settings.get("workspace_dir")
    virtual_roots = settings.get("virtual_roots")
    if not isinstance(virtual_roots, dict):
        virtual_roots = {"/": workspace_dir} if workspace_dir else None
    try:
        kwargs = binary_kwargs_from_uri(file_uri, root_dir=workspace_dir, virtual_roots=virtual_roots)
        if not kwargs or ("path" in kwargs and not Path(kwargs["path"]).is_file()):
            raise ValueError("file source is unavailable")
        if "base64" in kwargs and not base64.b64decode(kwargs["base64"], validate=True):
            raise ValueError("empty file content")
    except (ValueError, OSError) as exc:
        logger.warning("File upload input rejected code=invalid_file_source error_type=%s", type(exc).__name__)
        raise ToolInputError(
            "文件上传未执行（invalid_file_source）：文件不存在、超出当前会话挂载范围，或文件 URI/URL/base64 无效。"
            "请先确认文件已创建，并使用当前工作区路径或 /memory/... 附件路径后再试。"
        ) from None
    resolved_name = file_name or (Path(kwargs["path"]).name if "path" in kwargs else None)
    return kwargs, resolved_name


@tool(response_format="content")
@input_error_text
async def upload_private_file(
    file_uri: str,
    file_name: str | None = None,
    user_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """上传私聊文件。
    Args:
        file_uri: 已存在的工作区虚拟路径或 /memory/... 附件路径，也支持 file://、http(s)://、base64://
        file_name: 文件名；使用 URL/base64 时建议显式提供
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id = require_user_id(user_id, config)
    kwargs, resolved_file_name = _prepare_upload(file_uri, file_name, config)
    if not resolved_file_name:
        return "请提供 file_name。"
    file_id = await get_bot().upload_private_file(user_id=resolved_user_id, **kwargs, file_name=resolved_file_name)
    return f"已上传私聊文件 {resolved_file_name}，file_id={file_id}"


@tool(response_format="content")
@input_error_text
async def upload_group_file(
    file_uri: str,
    file_name: str | None = None,
    parent_folder_id: str | None = None,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """上传群文件。
    Args:
        file_uri: 已存在的工作区虚拟路径或 /memory/... 附件路径，也支持 file://、http(s)://、base64://
        file_name: 文件名；使用 URL/base64 时建议显式提供
        parent_folder_id: 可选父文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    kwargs, resolved_file_name = _prepare_upload(file_uri, file_name, config)
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
@input_error_text
async def get_private_file_download_url(
    file_id: str,
    file_hash: str,
    user_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
    is_self_send: bool = False,
) -> str:
    """获取私聊文件下载链接。
    Args:
        file_id: 文件 ID
        file_hash: 文件 TriSHA1 哈希
        is_self_send: 文件是否由机器人自己发送，下载本人发出的私聊文件时为 true
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id = require_user_id(user_id, config)
    return await get_bot().get_private_file_download_url(
        user_id=resolved_user_id, file_id=file_id, file_hash=file_hash, is_self_send=is_self_send
    )


@tool(response_format="content")
@input_error_text
async def persist_group_file(
    file_id: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
) -> str:
    """将群临时文件转存为永久文件。仅允许目标群的群主或管理员操作，需要 Milky 1.3。

    Args:
        file_id: 已存在的群临时文件 ID
        group_id: 可选目标群号，默认当前群
    """
    from .milky_group import require_admin_group

    resolved_group_id = require_admin_group(group_id, config, runtime)
    await get_bot().persist_group_file(group_id=resolved_group_id, file_id=file_id)
    return f"已将群 {resolved_group_id} 文件 {file_id} 转存为永久文件"


@tool(response_format="content")
@input_error_text
async def get_group_file_download_url(
    file_id: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """获取群文件下载链接。
    Args:
        file_id: 文件 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    return await get_bot().get_group_file_download_url(group_id=resolved_group_id, file_id=file_id)


@tool(response_format="content")
@input_error_text
async def get_group_files(
    parent_folder_id: str | None = None,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """获取群文件列表。
    Args:
        parent_folder_id: 可选父文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    info = await get_bot().get_group_files(group_id=resolved_group_id, parent_folder_id=parent_folder_id)
    return format_files_info(resolved_group_id, info)


@tool(response_format="content")
@input_error_text
async def move_group_file(
    file_id: str,
    parent_folder_id: str = "/",
    target_folder_id: str = "/",
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """移动群文件。
    Args:
        file_id: 文件 ID
        parent_folder_id: 文件当前所在文件夹 ID
        target_folder_id: 目标文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    await get_bot().move_group_file(
        group_id=resolved_group_id,
        file_id=file_id,
        parent_folder_id=parent_folder_id,
        target_folder_id=target_folder_id,
    )
    return f"已将群 {resolved_group_id} 文件 {file_id} 从 {parent_folder_id} 移动到 {target_folder_id}"


@tool(response_format="content")
@input_error_text
async def rename_group_file(
    file_id: str,
    new_file_name: str,
    parent_folder_id: str = "/",
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """重命名群文件。
    Args:
        file_id: 文件 ID
        new_file_name: 新文件名
        parent_folder_id: 文件所在文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    await get_bot().rename_group_file(
        group_id=resolved_group_id,
        file_id=file_id,
        parent_folder_id=parent_folder_id,
        new_file_name=new_file_name,
    )
    return f"已将群 {resolved_group_id} 文件 {file_id} 重命名为：{new_file_name}"


@tool(response_format="content")
@input_error_text
async def delete_group_file(
    file_id: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """删除群文件。
    Args:
        file_id: 文件 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    await get_bot().delete_group_file(group_id=resolved_group_id, file_id=file_id)
    return f"已删除群 {resolved_group_id} 文件 {file_id}"


@tool(response_format="content")
@input_error_text
async def create_group_folder(
    folder_name: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """创建群文件夹。
    Args:
        folder_name: 文件夹名
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    folder_id = await get_bot().create_group_folder(group_id=resolved_group_id, folder_name=folder_name)
    return f"已在群 {resolved_group_id} 创建文件夹 {folder_name}，folder_id={folder_id}"


@tool(response_format="content")
@input_error_text
async def rename_group_folder(
    folder_id: str,
    new_folder_name: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """重命名群文件夹。
    Args:
        folder_id: 文件夹 ID
        new_folder_name: 新文件夹名
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    await get_bot().rename_group_folder(
        group_id=resolved_group_id,
        folder_id=folder_id,
        new_folder_name=new_folder_name,
    )
    return f"已将群 {resolved_group_id} 文件夹 {folder_id} 重命名为：{new_folder_name}"


@tool(response_format="content")
@input_error_text
async def delete_group_folder(
    folder_id: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """删除群文件夹。
    Args:
        folder_id: 文件夹 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    await get_bot().delete_group_folder(group_id=resolved_group_id, folder_id=folder_id)
    return f"已删除群 {resolved_group_id} 文件夹 {folder_id}"
