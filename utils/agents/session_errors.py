"""Session control failures must not be converted into retryable tool errors."""


class CheckpointCapacityExceeded(RuntimeError):
    """The next checkpoint write would exceed the configured storage budget."""


class SessionInterruptedError(RuntimeError):
    """QQ sessions do not support resuming unfinished graph interrupts."""
