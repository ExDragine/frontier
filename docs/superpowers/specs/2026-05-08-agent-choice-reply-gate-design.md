# AgentChoice Reply Gate Design

## Goal

Change `AgentChoice` from a reasoning-effort router into a lightweight reply gate, while passing the configured `EnvConfig.AGENT_CAPABILITY` directly to the main agent.

## Current Behavior

`plugins/agent/__init__.py` calls `assistant_agent()` with `prompts/agent_choice.md` when `EnvConfig.AGENT_CAPABILITY == "auto"`. The structured result currently selects one of `low`, `medium`, `high`, or `xhigh`, and that selected value is passed to `FrontierCognitive.chat_agent()` as the Responses API `reasoning_effort`.

This means the same prompt is responsible for dynamic thinking-level selection, and there is no late gate for suppressing replies when the latest message is only a closing remark, evaluation, or otherwise useless continuation after a completed exchange.

## Target Behavior

`AgentChoice` should expose `should_reply: bool`.

The agent handler should:

1. Always use `EnvConfig.AGENT_CAPABILITY` as the capability value passed to `FrontierCognitive.chat_agent()`.
2. Use `prompts/agent_choice.md` to classify whether the bot should continue the conversation after the coarse `message_gateway()` allows the message through.
4. If `should_reply` is false, stop the matcher with `common.finish()` before queueing the deep agent request.
5. If `should_reply` is true, continue the existing queue and agent execution flow unchanged.

## Reply Gate Criteria

Return `should_reply = false` when recent context shows the previous user problem has already been answered or completed, and the latest input is only:

- an evaluation such as "对", "不错", "有用", "不对但算了";
- thanks or acknowledgement such as "谢谢", "好", "了解";
- chitchat or reaction with no actionable request;
- a statement that does not add useful information or ask the bot to do anything.

Return `should_reply = true` when the latest input:

- asks a new question;
- requests a change, follow-up, explanation, or action;
- corrects earlier information in a way that needs a response;
- contains quoted text or other textual context that likely needs interpretation;
- explicitly mentions or addresses the bot.

When uncertain, reply.

## Implementation Shape

Keep the change local to:

- `plugins/agent/__init__.py`: update the `AgentChoice` schema, add a pre-queue reply gate, and make `_process_agent_request()` pass `EnvConfig.AGENT_CAPABILITY` directly.
- `prompts/agent_choice.md`: replace capability routing instructions with reply-gate instructions.
- `test/plugins/agent_image_memory_test.py`: add focused tests for capability passthrough and no-reply finish behavior.
- `env.toml.example`: document concrete capability levels instead of `auto`.

No changes are needed in `utils/agents.py` or `utils/agent_queue.py`.

## Testing

Add tests that prove:

1. `_process_agent_request()` passes the configured capability to `chat_agent()` directly and does not use AgentChoice as a reasoning-level router.
2. When `AgentChoice.should_reply` is false, the matcher finishes before queue submission and `chat_agent()` is not called.
