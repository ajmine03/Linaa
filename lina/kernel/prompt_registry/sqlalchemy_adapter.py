"""Concrete PromptRegistryPort implementation backed by SQLite via SQLAlchemy."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kernel.ports.prompt_registry import PromptRegistryPort, PromptTemplate
from kernel.prompt_registry.db.models import PromptTemplateRecord
from kernel.prompt_registry.renderer import TemplateRenderer

logger = structlog.get_logger(__name__)


def _record_to_template(record: PromptTemplateRecord) -> PromptTemplate:
    return PromptTemplate(
        key=record.key,
        version=record.version,
        template=record.template,
        description=record.description,
        input_variables=record.input_variables(),
        plugin_name=record.plugin_name,
    )


class SQLAlchemyPromptRegistry(PromptRegistryPort):
    def __init__(self, session: AsyncSession, *, renderer: TemplateRenderer | None = None) -> None:
        self._session = session
        self._renderer = renderer or TemplateRenderer()

    async def get(self, key: str, *, version: int | None = None) -> PromptTemplate | None:
        if version is not None:
            stmt = select(PromptTemplateRecord).where(
                PromptTemplateRecord.key == key, PromptTemplateRecord.version == version
            )
        else:
            stmt = (
                select(PromptTemplateRecord)
                .where(PromptTemplateRecord.key == key)
                .order_by(PromptTemplateRecord.version.desc())
                .limit(1)
            )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return _record_to_template(record) if record else None

    async def register(self, template: PromptTemplate) -> PromptTemplate:
        latest = await self.get(template.key)
        next_version = (latest.version + 1) if latest else 1

        if template.version != next_version:
            logger.info(
                "prompt_registry.version_auto_corrected",
                key=template.key,
                requested_version=template.version,
                assigned_version=next_version,
            )

        record = PromptTemplateRecord(
            id=str(uuid.uuid4()),
            key=template.key,
            version=next_version,
            template=template.template,
            description=template.description,
            input_variables_json=json.dumps(template.input_variables),
            plugin_name=template.plugin_name,
            created_at=datetime.now(UTC),
        )
        self._session.add(record)
        await self._session.flush()

        logger.info(
            "prompt_registry.registered", key=template.key, version=next_version,
            plugin_name=template.plugin_name,
        )
        return _record_to_template(record)

    async def render(
        self, key: str, variables: dict[str, object], *, version: int | None = None
    ) -> str:
        template = await self.get(key, version=version)
        if template is None:
            raise ValueError(f"Prompt template '{key}' (version={version}) not found.")
        return self._renderer.render(template, variables)

    async def list_versions(self, key: str) -> list[int]:
        stmt = (
            select(PromptTemplateRecord.version)
            .where(PromptTemplateRecord.key == key)
            .order_by(PromptTemplateRecord.version.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_plugin(self, plugin_name: str) -> list[PromptTemplate]:
        # Latest version per key for this plugin
        subq = (
            select(
                PromptTemplateRecord.key,
                func.max(PromptTemplateRecord.version).label("max_version"),
            )
            .where(PromptTemplateRecord.plugin_name == plugin_name)
            .group_by(PromptTemplateRecord.key)
            .subquery()
        )
        stmt = select(PromptTemplateRecord).join(
            subq,
            (PromptTemplateRecord.key == subq.c.key)
            & (PromptTemplateRecord.version == subq.c.max_version),
        )
        result = await self._session.execute(stmt)
        return [_record_to_template(r) for r in result.scalars().all()]