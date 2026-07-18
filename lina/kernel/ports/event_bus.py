"""Event Bus port — internal pub/sub used for decoupled kernel/plugin communication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeAlias

from kernel.entities.event import EventEnvelope

EventHandler: TypeAlias = Callable[[EventEnvelope], Awaitable[None]]


class EventBusPort(ABC):
    """Async publish/subscribe bus. Handlers are invoked concurrently and
    exceptions in one handler must not prevent delivery to others (the
    adapter is responsible for isolating handler failures and logging them).
    """

    @abstractmethod
    async def publish(self, event: EventEnvelope) -> None:
        """Publish an event to all subscribers of its event_type (and wildcard subs)."""

    @abstractmethod
    def subscribe(self, event_type_pattern: str, handler: EventHandler) -> str:
        """Subscribe a handler to an event type or glob pattern (e.g. 'finding.*').

        Returns a subscription ID usable with unsubscribe().
        """

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if it existed."""

    @abstractmethod
    async def replay(
        self, event_type_pattern: str, *, since_correlation_id: str | None = None
    ) -> list[EventEnvelope]:
        """Replay recently buffered events matching a pattern (bounded buffer,
        not a durable event store — for durability, subscribers should persist
        via AuditEntry through the repository port).
        """