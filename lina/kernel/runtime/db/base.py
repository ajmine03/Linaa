"""SQLAlchemy declarative base and shared column mixins."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base for all LINA ORM models."""


class EntityRecordMixin:
    """Common columns shared by every entity-backed table.

    `data` holds the full JSON-serialized domain entity (source of truth).
    The remaining columns exist purely to support efficient SQL-level
    filtering/sorting without deserializing every row.
    """

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)

    if TYPE_CHECKING:
        def __init__(self, **kwargs: Any) -> None: ...


class EngagementScopedMixin(EntityRecordMixin):
    """Adds an indexed engagement_id column for scoped entities."""

    engagement_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)