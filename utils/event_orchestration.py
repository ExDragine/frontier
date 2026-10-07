"""Request inbox processing; models propose and a separate executor writes."""

import asyncio
import time

from utils.agents.event_agent import propose_event_action
from utils.agents.runtime import run_serialized
from utils.event_policy import EventConfig, allowed_actions
from utils.milky_event_executor import MilkyEventExecutor, field
from utils.platform_event import InboundEvent


class EventOrchestrator:
    def __init__(self, store, config, bot_lookup, propose=propose_event_action):
        self.store = store
        self.config = config
        self.bot_lookup = bot_lookup
        self.propose = propose

    async def ingest(self, event: InboundEvent):
        cfg: EventConfig = self.config()
        if not cfg.enabled:
            return False
        rule = cfg.rule_for(event.kind, event.group_id)
        if rule.mode == "ignore":
            return False
        status = "recorded" if rule.mode == "record" else "pending"
        return await self.store.put(event, status, cfg.ttl_seconds, cfg.max_pending)

    async def process(self, row):
        event = InboundEvent.model_validate_json(row["payload"])
        scope = f"event:{event.bot_id}:{event.group_id or event.data.get('initiator_uid')}"
        started = False

        async def run():
            nonlocal started
            started = True
            await self._process(event, row)

        try:
            await run_serialized(scope, run, timeout=self.config().timeout_seconds + 5)
        except TimeoutError:
            if not started:
                await self.store.finish(event.key, "deferred", "queue_wait_timeout")

    async def _propose(self, event, rule, choices):
        if rule.mode == "rule":
            return rule.action
        if choices == ("defer",):
            return "defer"
        return await self.propose(event, rule, choices)

    async def _process(self, event, row):
        cfg = self.config()
        policy = cfg.model_dump_json()
        rule = cfg.rule_for(event.kind, event.group_id)
        action = "defer"
        writing = False
        try:
            async with asyncio.timeout(cfg.timeout_seconds):
                if not cfg.enabled or rule.mode in {"ignore", "record"}:
                    await self.store.finish(event.key, "deferred", "policy_disabled")
                    return
                if row["expires"] <= time.time():
                    await self.store.finish(event.key, "expired")
                    return
                choices = allowed_actions(rule, event.data)
                action = await self._propose(event, rule, choices)
                if action not in choices:
                    action = "defer"
                if rule.mode == "shadow" or action == "defer":
                    await self.store.finish(
                        event.key, "shadow" if rule.mode == "shadow" else "deferred",
                        "evaluation_only" if rule.mode == "shadow" else "no_authorized_action", action, policy,
                    )
                    return
                executor = MilkyEventExecutor(self.bot_lookup(event.bot_id))
                current = await executor.preflight(event, rule.allow_filtered)
                if self.config().model_dump_json() != policy:
                    await self.store.finish(event.key, "deferred", "policy_changed", action, policy)
                    return
                if not await self.store.begin_action(event.key, action, policy):
                    return
                writing = True
                if self.config().model_dump_json() != policy or row["expires"] <= time.time():
                    await self.store.finish(event.key, "deferred", "policy_changed_or_expired_before_write", action, policy)
                    return
                await executor.execute(event, action, current)
                await self.store.finish(event.key, "succeeded", "platform_confirmed", action, policy)
        except asyncio.CancelledError:
            # The durable executing marker is recovered as unknown if shutdown
            # interrupts this final write as well. Never retry the platform call.
            await self.store.finish(event.key, "unknown" if writing else "deferred", "cancelled", action, policy)
            raise
        except Exception as error:  # noqa: BLE001 - inbox failures must not stop workers
            await self.store.finish(
                event.key, "unknown" if writing else "deferred", type(error).__name__, action, policy,
            )

    async def reconcile(self, row):
        """Read-only recovery; never repeat an uncertain platform operation."""
        event = InboundEvent.model_validate_json(row["payload"])
        if event.kind == "group_invitation":
            return  # No remote lookup exists; an operator must inspect it.
        try:
            current = await MilkyEventExecutor(self.bot_lookup(event.bot_id)).current(event)
            state = field(current, "state")
            if state in {"accepted", "rejected", "ignored"}:
                expected = "accepted" if row["proposal"] == "accept" else "rejected"
                await self.store.finish(
                    event.key, "resolved", "remote_" + state + ("_matches" if state == expected else "_differs"),
                    row["proposal"], row["policy"],
                )
        except Exception:  # noqa: BLE001 - offline/missing state remains unknown
            return
