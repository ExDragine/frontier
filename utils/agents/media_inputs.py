"""Apply media capabilities and budgets after filesystem blob rehydration."""

from langchain.agents.middleware import AgentMiddleware

from utils.media_budget import InlineMediaBudget

from .inputs import filter_messages_for_model_capabilities


class MediaInputMiddleware(AgentMiddleware):
    def __init__(self, model: str, *, role=None, max_images: int, max_bytes: int):
        self.model = model
        self.role = role
        self.max_images = max(0, max_images)
        self.max_bytes = max(0, max_bytes)

    def _request(self, request):
        messages = filter_messages_for_model_capabilities(request.messages, self.model, role=self.role)
        # Prefer the latest explicit reads and current input over older history.
        # Preserve messages, tool IDs and ordering in the request and checkpoint.
        views = [{"content": message.content} for message in messages]
        budget = InlineMediaBudget(self.max_bytes, self.max_images)
        bounded = budget.history(views)
        return request.override(messages=[
            message.model_copy(update={"content": view["content"]})
            for message, view in zip(messages, bounded, strict=True)
        ])

    def wrap_model_call(self, request, handler):
        return handler(self._request(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._request(request))
