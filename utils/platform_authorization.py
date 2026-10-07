"""Owner authorization for bot-wide relationship changes from chat tools."""

from nonebot import get_driver
from nonebot.adapters.milky import Adapter

from utils.agent_context import FrontierRuntimeContext
from utils.milky_tools import ToolInputError, configurable


def require_bot_owner(config=None, runtime=None):
    context = getattr(runtime, "context", None)
    if isinstance(context, FrontierRuntimeContext):
        if context.conversation is not None and context.conversation.platform != "qq":
            raise ToolInputError("只有机器人超级用户才能管理好友或邀请机器人入群。")
        user_id = context.user_id
    else:
        user_id = configurable(config).get("user_id")
    owners = get_driver().config.superusers
    prefix = Adapter.get_name().split(maxsplit=1)[0].lower()
    if user_id is None or not ({str(user_id), f"{prefix}:{user_id}"} & set(owners)):
        raise ToolInputError("只有机器人超级用户才能管理好友或邀请机器人入群。")
