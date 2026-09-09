"""Close per-turn QuickJS resources even when the graph is cancelled."""

from langchain_quickjs import CodeInterpreterMiddleware as QuickJSMiddleware


class CodeInterpreterMiddleware(QuickJSMiddleware):
    """Pair public lifecycle hooks without depending on the private registry.

    LangGraph skips after_agent on cancellation/errors. QuickJS otherwise keeps
    its worker alive until GC, which can deadlock during interpreter shutdown.
    Each instance belongs to one request and uses turn-scoped REPL state.
    """

    def __init__(self, **kwargs):
        super().__init__(mode="turn", **kwargs)
        self._cleanup_states = []

    async def abefore_agent(self, state, runtime):
        update = await super().abefore_agent(state, runtime)
        self._cleanup_states.append(({**state, **(update or {})}, runtime))
        return update

    async def aclose(self):
        try:
            for state, runtime in self._cleanup_states:
                # In turn mode this hook only evicts the interpreter slot; it
                # is harmless when normal after_agent already evicted it.
                await super().aafter_agent(state, runtime)
        finally:
            self._cleanup_states.clear()
