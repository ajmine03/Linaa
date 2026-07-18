"""LINA kernel runtime — composition root, persistence adapters, DI container."""

from kernel.runtime.container import Container, build_container
from kernel.runtime.logging_setup import configure_logging
from kernel.runtime.unit_of_work import SQLAlchemyUnitOfWork

__all__ = [
    "Container",
    "SQLAlchemyUnitOfWork",
    "build_container",
    "configure_logging",
]