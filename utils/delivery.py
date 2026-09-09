"""Explicit outcomes for sending requested content to a transport."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    """Count delivered content, excluding progress and failure notifications."""

    attempted: int = 0
    sent: int = 0
    errors: tuple[str, ...] = ()

    @property
    def successful(self) -> bool:
        return self.attempted > 0 and self.sent == self.attempted and not self.errors

    def combine(self, other: DeliveryResult) -> DeliveryResult:
        return DeliveryResult(
            attempted=self.attempted + other.attempted,
            sent=self.sent + other.sent,
            errors=self.errors + other.errors,
        )
