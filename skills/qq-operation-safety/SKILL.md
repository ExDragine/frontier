---
name: qq-operation-safety
description: Use before QQ platform writes, moderation, announcements, file operations, reminders, scheduled tasks, or sending generated media.
---

# QQ operation safety

Resolve the current target from runtime context and the latest message metadata. Never infer a different group or user from stale history.

- Private chat: use private/friend tools and the current user ID. Do not call group administration or group-file tools.
- Group chat: use the current group ID. Resolve a referenced member from the relevant message's user ID.
- Destructive friend operations and high-risk moderation require an explicitly authorized administrator.
- Before muting, removing, or changing an administrator, verify both the caller's role and that the target is not the owner or an equally privileged administrator.
- Announcements, uploads, reminders, scheduled tasks, browser operations, and media generation require clear user intent.
- Report success only after the tool confirms it. If a tool returns an error or cooldown, state that result plainly.

Never expose API keys, tokens, cookies, private URLs, or unrelated user data in tool arguments or replies.
