"""Audit sink: subscribes to the Event Bus and persists AuditEntry records.

This bridges the ephemeral Event Bus to durable storage without coupling
the bus itself to a repository implementation. Wired up in kernel/runtime
composition root.
"""

from __future__ import annotations

import structlog

from kernel.entities.enums import EventSeverity
from kernel.entities.event import AuditEntry, EventEnvelope
from kernel.ports.event_bus import EventBusPort
from kernel.ports.repository import Repository

logger = structlog.get_logger(__name__)


class AuditLogSink:
    """Subscribes to '*' on the Event Bus and writes an AuditEntry per event.

    Only events carrying enough context (source + event_type) are recorded;
    the sink never raises — persistence failures are logged, not propagated,
    since audit logging must never crash the event that triggered it.
    """

    def __init__(
        self,
        event_bus: EventBusPort,
        audit_repository: Repository[AuditEntry],
    ) -> None:
        self._event_bus = event_bus
        self._audit_repository = audit_repository
        self._subscription_id: str | None = None

    def start(self) -> None:
        self._subscription_id = self._event_bus.subscribe(
            "*", self._handle_event
        )
        logger.info("audit_sink.started", subscription_id=self._subscription_id)

    def stop(self) -> None:
        if self._subscription_id is not None:
            self._event_bus.unsubscribe(self._subscription_id)
            logger.info("audit_sink.stopped")
            self._subscription_id = None

    async def _handle_event(self, event: EventEnvelope) -> None:
        try:
            entry = AuditEntry(
                engagement_id=event.engagement_id,
                actor=str(event.payload.get("actor", event.source)),
                action=event.event_type,
                target_ref=event.payload.get("target_ref"),
                detail=event.payload,
                severity=event.severity,
            )
            await self._audit_repository.add(entry)
        except Exception:  # noqa: BLE001
            logger.exception(
                "audit_sink.persist_failed",
                event_type=event.event_type,
                source=event.source,
            )

    @staticmethod
    def critical_only_filter(event: EventEnvelope) -> bool:
        """Optional helper for callers wanting a narrower subscription pattern."""
        return event.severity in (EventSeverity.ERROR, EventSeverity.CRITICAL)