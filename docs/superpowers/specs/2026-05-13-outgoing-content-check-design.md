# Outgoing Content Check Design

## Goal

Set the Hugging Face mirror endpoint during startup and run model-generated chat text through the existing text risk checker before sending it.

## Current Behavior

`run.ps1` sets `HF_ENDPOINT=https://hf-mirror.com`, but it overwrites any explicit caller value. `run.sh` and the container startup path do not set the mirror.

Incoming user text and images are checked through `utils.message.message_check()` when `EnvConfig.CONTENT_CHECK_ENABLED` is true. Model-generated chat output is not checked before being sent. There are two user-visible model output paths in `plugins/agent/__init__.py`:

1. `choice.pre_response`, used for quick short replies and waiting previews.
2. The final `response["messages"][-1]` returned by `FrontierCognitive.chat_agent()`.

## Target Behavior

Startup scripts default `HF_ENDPOINT` to `https://hf-mirror.com` without overriding an explicit user-provided value. The container image carries the same default.

Before sending user-visible model text, the agent handler checks the text with the existing `TextCheck` detector. `Unsafe` output is replaced with a fixed playful block notice. `Safe`, `Controversial`, disabled checks, empty text, and unavailable detectors continue through unchanged.

## Implementation Shape

Keep the detector ownership in `utils.message`, next to the existing input check:

- Add a fixed `OUTPUT_RISK_BLOCKED_MESSAGE`.
- Add `sanitize_outgoing_text(content)` that returns either the original text or the block notice.
- Add `sanitize_outgoing_message(raw_message)` for final agent message objects.
- Reuse the content extraction rules already used by `send_messages()`.

Use the sanitizer in `plugins/agent/__init__.py` immediately before sending or storing `choice.pre_response` and final agent responses.

## Testing

Add focused tests for:

1. `sanitize_outgoing_text()` replaces `Unsafe` output.
2. `sanitize_outgoing_text()` allows `Controversial` output.
3. `choice.pre_response` is sanitized before send and insert.
4. Final agent response is sanitized before send and insert.
5. `run.sh` exports the default Hugging Face mirror before startup work begins.
6. `run.ps1` sets the same default without overwriting an existing value.
