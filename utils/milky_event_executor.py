"""Milky request reads and writes bound to a trusted event and bot instance."""

import time

from utils.platform_event import InboundEvent


def field(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


class MilkyEventExecutor:
    def __init__(self, bot):
        self.bot = bot

    async def current(self, event: InboundEvent):
        if str(self.bot.self_id) != event.bot_id:
            raise PermissionError("bot_mismatch")
        data = event.data
        if event.kind == "group_invitation":
            # Milky has no invitation lookup API. Only a fresh inbound invitation
            # is evidence; recovered or old invitations must be handled manually.
            return {"state": "pending"} if 0 <= time.time() - event.occurred_at < 60 else None
        if event.kind == "friend_request":
            for filtered in (False, True):
                rows = await self.bot.get_friend_requests(limit=100, is_filtered=filtered)
                for row in rows:
                    if (field(row, "initiator_uid") == data["initiator_uid"]
                            and str(field(row, "target_user_id")) == event.bot_id
                            and field(row, "time") == event.occurred_at
                            and str(field(row, "comment", ""))[:4000] == data.get("comment", "")
                            and str(field(row, "via", ""))[:4000] == data.get("via", "")):
                        return row
            return None
        return await self._group_request(event)

    async def _group_request(self, event):
        data = event.data
        expected_type = "join_request" if event.kind == "group_join_request" else "invited_join_request"
        for filtered in (False, True):
            cursor = None
            for _ in range(3):
                rows, next_cursor = await self.bot.get_group_notifications(
                    start_notification_seq=cursor, is_filtered=filtered, limit=100,
                )
                for row in rows:
                    if (field(row, "notification_seq") == data["notification_seq"]
                            and field(row, "group_id") == event.group_id
                            and field(row, "type") == expected_type
                            and field(row, "initiator_id") == data["initiator_id"]
                            and (event.kind != "group_invited_join_request"
                                 or field(row, "target_user_id") == data["target_user_id"])):
                        return row
                if next_cursor is None or next_cursor == cursor:
                    break
                cursor = next_cursor
        return None

    async def preflight(self, event: InboundEvent, allow_filtered: bool):
        current = await self.current(event)
        if current is None or field(current, "state") != "pending":
            raise ValueError("request_not_pending_or_unverifiable")
        if field(current, "is_filtered", False) and not allow_filtered:
            raise PermissionError("filtered_request")
        if event.kind in {"group_join_request", "group_invited_join_request"}:
            member = await self.bot.get_group_member_info(
                group_id=event.group_id, user_id=int(event.bot_id), no_cache=True,
            )
            if field(member, "role") not in {"admin", "owner"}:
                raise PermissionError("bot_not_group_admin")
        return current

    async def execute(self, event: InboundEvent, action: str, current):
        if action not in {"accept", "reject"} or str(self.bot.self_id) != event.bot_id:
            raise PermissionError("invalid_action_or_bot")
        data = event.data
        if event.kind == "friend_request":
            method = getattr(self.bot, f"{action}_friend_request")
            await method(initiator_uid=data["initiator_uid"], is_filtered=field(current, "is_filtered", False))
        elif event.kind == "group_invitation":
            method = getattr(self.bot, f"{action}_group_invitation")
            await method(group_id=event.group_id, invitation_seq=data["invitation_seq"])
        else:
            method = getattr(self.bot, f"{action}_group_request")
            await method(
                group_id=event.group_id, notification_seq=data["notification_seq"],
                notification_type="join_request" if event.kind == "group_join_request" else "invited_join_request",
                is_filtered=field(current, "is_filtered", False),
            )
