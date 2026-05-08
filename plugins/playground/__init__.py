from nonebot import on_notice
from nonebot.adapters.milky.bot import Bot
from nonebot.adapters.milky.event import FriendNudgeEvent, GroupNudgeEvent

event = on_notice(priority=0, block=True)


@event.handle()
async def handle_message(bot: Bot, event: FriendNudgeEvent | GroupNudgeEvent):
    if isinstance(event, FriendNudgeEvent):
        await bot.send_friend_nudge(user_id=int(event.get_user_id()))
    elif isinstance(event, GroupNudgeEvent):
        await bot.send_group_nudge(group_id=event.data.group_id, user_id=int(event.get_user_id()))
