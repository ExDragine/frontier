"""Limit model-facing hot history without editing checkpoint ancestry."""

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages.utils import count_tokens_approximately

from utils.media import media_block_kind


def messages_contain_media(messages) -> bool:
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        if isinstance(content, list) and any(media_block_kind(block) is not None for block in content):
            return True
    return False


def history_budget(settings, profile, *, reserved_tokens: int = 0) -> int:
    window = (profile or {}).get("max_input_tokens")
    if isinstance(window, int) and window > 0:
        return max(0, min(settings.history_max_tokens, int(window * settings.history_window_fraction), window - reserved_tokens))
    return min(settings.history_max_tokens, 8000)


def recent_complete_turns(messages, max_tokens: int):
    """Retain a suffix of complete human-led turns, never orphan tool results."""
    turns = []
    for message in messages:
        role = message.get("role") if isinstance(message, dict) else getattr(message, "type", None)
        if role in {"user", "human"}:
            turns.append([])
        if turns:
            turns[-1].append(message)
    chosen = []
    remaining = max_tokens
    for turn in reversed(turns):
        tokens = count_tokens_approximately(turn)
        if tokens > remaining:
            break
        chosen.append(turn)
        remaining -= tokens
    return [message for turn in reversed(chosen) for message in turn]


class SessionHistoryMiddleware(AgentMiddleware):
    def __init__(self, lease, profile):
        self.lease = lease
        self.profile = profile

    def _request(self, request):
        messages = request.messages
        cutoff = next((index for index, message in enumerate(messages) if message.id == self.lease.current_id), None)
        if cutoff is None:
            # Deep Agents may have already summarized the current turn. Its
            # compaction protocol owns that representation; do not slice it.
            return request
        current = messages[cutoff:]
        reserved = count_tokens_approximately(current)
        if request.system_message is not None:
            reserved += count_tokens_approximately([request.system_message])
        # Tool schemas and provider accounting vary. Reserve their serialized size
        # conservatively in addition to a margin for the next model response.
        reserved += sum(len(str(getattr(tool, "args", tool))) for tool in request.tools) // 3 + 4096
        budget = history_budget(self.lease.entry.settings, self.profile, reserved_tokens=reserved)
        history = recent_complete_turns(messages[:cutoff], budget)
        self.lease.history_tokens = count_tokens_approximately(history)
        return request.override(messages=[*history, *current])

    def wrap_model_call(self, request, handler):
        return handler(self._request(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._request(request))
