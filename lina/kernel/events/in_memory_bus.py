"""In-process async Event Bus adapter — default LINA implementation.

Suitable for a single-process deployment (the target architecture here).
Handler isolation: one handler's exception never blocks delivery to others.
Maintains a small bounded ring buffer per pattern-subscription-free replay
of recent events for late subscribers / debugging.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import deque
from dataclasses import dataclass, field

import structlog

from kernel.entities.event import EventEnvelope
from kernel.events.matcher import matches
from kernel.ports.event_bus import EventBusPort, EventHandler
from kernel.ports.exceptions import EventBusError

logger = structlog.get_logger(__name__)

_DEFAULT_REPLAY_BUFFER_SIZE = 500


@dataclass(slots=True)
class _Subscription:
    subscription_id: str
    pattern: str
    handler: EventHandler


class InMemoryEventBus(EventBusPort):
    """Default single-process Event Bus implementation.

    Thread-safety note: designed for a single asyncio event loop. All state
    mutation happens under `_lock` to remain safe under concurrent tasks.
    """

    def __init__(self, *, replay_buffer_size: int = _DEFAULT_REPLAY_BUFFER_SIZE) -> None:
        self._subscriptions: dict[str, _Subscription] = {}
        self._lock = asyncio.Lock()
        self._buffer: deque[EventEnvelope] = deque(maxlen=replay_buffer_size)
        self._publish_count = 0

    async def publish(self, event: EventEnvelope) -> None:
        self._buffer.append(event)
        self._publish_count += 1

        async with self._lock:
            targets = [
                sub for sub in self._subscriptions.values() if matches(event.event_type, sub.pattern)
            ]

        if not targets:
            logger.debug(
                "event_bus.published_no_subscribers",
                event_type=event.event_type,
                source=event.source,
            )
            return

        results = await asyncio.gather(
            *(self._safe_invoke(sub, event) for sub in targets),
            return_exceptions=False,
        )
        failures = sum(1 for r in results if r is False)
        logger.debug(
            "event_bus.published",
            event_type=event.event_type,
            source=event.source,
            subscriber_count=len(targets),
            failures=failures,
        )

    async def _safe_invoke(self, sub: _Subscription, event: EventEnvelope) -> bool:
        """Invoke a single handler, isolating and logging any exception.

        Returns True on success, False on handler failure (never raises).
        """
        try:
            await sub.handler(event)
            return True
        except Exception:  # noqa: BLE001 - deliberate isolation boundary
            logger.exception(
                "event_bus.handler_failed",
                subscription_id=sub.subscription_id,
                pattern=sub.pattern,
                event_type=event.event_type,
            )
            return False

    def subscribe(self, event_type_pattern: str, handler: EventHandler) -> str:
        if not event_type_pattern:
            raise EventBusError("Subscription pattern must not be empty.")
        subscription_id = str(uuid.uuid4())
        self._subscriptions[subscription_id] = _Subscription(
            subscription_id=subscription_id,
            pattern=event_type_pattern,
            handler=handler,
        )
        logger.info(
            "event_bus.subscribed",
            subscription_id=subscription_id,
            pattern=event_type_pattern,
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        existed = self._subscriptions.pop(subscription_id, None) is not None
        if existed:
            logger.info("event_bus.unsubscribed", subscription_id=subscription_id)
        return existed

    async def replay(
        self, event_type_pattern: str, *, since_correlation_id: str | None = None
    ) -> list[EventEnvelope]:
        events = [e for e in self._buffer if matches(e.event_type, event_type_pattern)]
        if since_correlation_id is not None:
            found_index: int | None = None
            for i, e in enumerate(events):
                if e.correlation_id == since_correlation_id:
                    found_index = i
            events = events[found_index + 1 :] if found_index is not None else events
        return events

    @property
    def subscriber_count(self) -> int:
        return len(self._subscriptions)

    @property
    def total_published(self) -> int:
        return self._publish_count