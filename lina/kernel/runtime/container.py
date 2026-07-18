"""Composition root: wires config, logging, database, event bus, and audit sink
into a single Container object used by the API layer, CLI, and tests alike.

Later modules (plugin_manager, model_router, memory_engine, knowledge_graph,
authz, agent_runtime, workflow_engine, mcp) extend this container with
additional attributes as they're implemented — this module only wires what
exists today.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from kernel.config.loader import bootstrap
from kernel.config.schema import LinaSettingsSchema
from kernel.config.settings import load_settings
from kernel.events.audit_sink import AuditLogSink
from kernel.events.in_memory_bus import InMemoryEventBus
from kernel.ports.event_bus import EventBusPort
from kernel.runtime.db.session import create_engine, create_session_factory, dispose_engine, init_db
from kernel.runtime.logging_setup import configure_logging
from kernel.runtime.repositories.factory import audit_entry_repository
from kernel.runtime.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class Container:
    """Holds every wired singleton/service needed to run LINA."""

    settings: LinaSettingsSchema
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    event_bus: EventBusPort
    audit_sink: AuditLogSink

    def unit_of_work(self) -> SQLAlchemyUnitOfWork:
        """Factory for a fresh transactional Unit of Work."""
        return SQLAlchemyUnitOfWork(self.session_factory)

    async def shutdown(self) -> None:
        self.audit_sink.stop()
        await dispose_engine(self.engine)
        logger.info("container.shutdown_complete")


async def build_container(config_path: str | None = None) -> Container:
    """Build and fully initialize the LINA composition root.

    Order matters: settings -> directories -> logging -> db engine/tables ->
    event bus -> audit sink (needs its own session for persistence, so it
    uses a dedicated one-off session via the repository factory bound to a
    short-lived session per audit write — see AuditLogSink implementation,
    which persists through the injected repository abstraction).
    """
    settings = load_settings(config_path)
    bootstrap(settings)
    configure_logging(settings.logging, environment=settings.environment)

    logger.info(
        "container.building",
        environment=settings.environment.value,
        database_url=settings.database.url,
    )

    engine = create_engine(settings.database)
    await init_db(engine)
    session_factory = create_session_factory(engine)

    event_bus = InMemoryEventBus()

    # Audit sink gets its own dedicated long-lived session for simplicity;
    # a production-hardened variant would open one short session per event.
    audit_session = session_factory()
    audit_repo = audit_entry_repository(audit_session)
    audit_sink = AuditLogSink(event_bus, audit_repo)
    audit_sink.start()

    container = Container(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        event_bus=event_bus,
        audit_sink=audit_sink,
    )

    logger.info("container.build_complete")
    return container