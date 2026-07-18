"""Prompt Registry port — versioned, template-driven prompt management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class PromptTemplate:
    key: str
    version: int
    template: str
    description: str = ""
    input_variables: list[str] = field(default_factory=list)
    plugin_name: str | None = None


class PromptRegistryPort(ABC):
    @abstractmethod
    async def get(self, key: str, *, version: int | None = None) -> PromptTemplate | None:
        """Fetch a template by key; latest version if version is None."""

    @abstractmethod
    async def register(self, template: PromptTemplate) -> PromptTemplate:
        """Register a new template version (immutable once registered)."""

    @abstractmethod
    async def render(self, key: str, variables: dict[str, Any], *, version: int | None = None) -> str:
        """Fetch and render a template with the given variables."""

    @abstractmethod
    async def list_versions(self, key: str) -> list[int]: ...

    @abstractmethod
    async def list_by_plugin(self, plugin_name: str) -> list[PromptTemplate]: ...