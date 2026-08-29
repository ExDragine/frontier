---
name: qq-operation-safety
description: Use before QQ platform writes, moderation, announcements, file operations, reminders, scheduled tasks, or sending generated media.
---

# QQ operation safety

Resolve the current target from runtime context and the latest message metadata. Never infer a different group or user from stale history.

- Private chat: use private/friend tools and the current user ID. Do not call group administration or group-file tools.
- Group chat: use the current group ID. Resolve a referenced member from the relevant message's user ID.
- Deleting or blocking a friend is destructive and requires an explicit instruction from an authorized administrator. Lower-risk changes to the bot's own nickname, signature, or avatar may proceed when intent is clear.
- Muting or removing a member, changing administrators, and enabling group-wide mute are high-risk moderation operations. Verify the caller's current role and confirm the target is not the owner or an equally privileged administrator.
- Changing a group name or avatar, publishing an announcement, or setting an essence message is lower risk and may proceed when the user's intent is explicit and the tool's permission check passes.
- Announcements, uploads, reminders, scheduled tasks, browser operations, and media generation require clear user intent.
- Report success only after the tool confirms it. If a tool returns an error or cooldown, state that result plainly.

Never expose API keys, tokens, cookies, private URLs, or unrelated user data in tool arguments or replies.
