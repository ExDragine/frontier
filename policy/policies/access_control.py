"""访问控制策略 — 替代 utils.message.message_gateway()。"""

from policy.base import BasePolicy
from policy.decisions import Decision
from policy.snapshots import InputSnapshot, OutputSnapshot


class AccessControlPolicy(BasePolicy):
    name = "access_control"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        if not isinstance(snapshot, InputSnapshot):
            return Decision.allow(reason="not_applicable")

        # 第 1 层：快速放行 — @mention 或 bot 名称前缀
        if snapshot.is_at_bot or snapshot.is_bot_name_prefix:
            return Decision.allow(reason="direct_mention")

        user_id = snapshot.user_id
        group_id = snapshot.group_id
        numeric_user_id = _to_int(user_id)

        # 第 2 层：测试群组 — 不让未点名的群回复
        test_group_ids = self.config.get("test_group_ids", [])
        if group_id is not None and group_id in test_group_ids:
            return Decision.deny("test_group_no_reply", message="现在不太方便回复呢~")

        # 第 3 层：黑名单拦截
        if numeric_user_id in self.config.get("blacklist_persons", []):
            return Decision.deny("user_blacklisted", message="你已被限制使用")
        if group_id is not None and group_id in self.config.get("blacklist_groups", []):
            return Decision.deny("group_blacklisted", message="该群已被限制使用")

        # 第 4 层：白名单校验
        if self.config.get("whitelist_mode"):
            whitelist_persons = self.config.get("whitelist_persons", [])
            whitelist_groups = self.config.get("whitelist_groups", [])
            person_ok = numeric_user_id in whitelist_persons
            group_ok = group_id is not None and group_id in whitelist_groups
            # 私聊（group_id=None）只要通过用户白名单即可
            if group_id is None and not person_ok:
                return Decision.deny("not_whitelisted", message="你暂未开放此功能")
            if group_id is not None and not (person_ok or group_ok):
                return Decision.deny("not_whitelisted", message="该群暂未开放此功能")

        return Decision.allow(reason="passed_access_control")


def _to_int(value: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return hash(value) & 0x7FFFFFFF
