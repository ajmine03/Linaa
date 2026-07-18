"""LINA Event Bus — concrete in-process adapter, catalog, and audit bridge."""

from kernel.events.audit_sink import AuditLogSink
from kernel.events.catalog import EventTypes
from kernel.events.in_memory_bus import InMemoryEventBus
from kernel.events.matcher import matches

__all__ = [
    "AuditLogSink",
    "EventTypes",
    "InMemoryEventBus",
    "matches",
]