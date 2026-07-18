"""SQLAlchemy ORM table backing the Prompt Registry."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from kernel.runtime.db.base import Base


class PromptTemplateRecord(Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (Index("ix_prompt_key_version", "key", "version", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer)
    template: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(512), default="")
    input_variables_json: Mapped[str] = mapped_column(Text, default="[]")
    plugin_name: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def input_variables(self) -> list[str]:
        return json.loads(self.input_variables_json) if self.input_variables_json else []