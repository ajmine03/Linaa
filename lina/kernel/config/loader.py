"""Filesystem bootstrap: ensures required LINA directories exist and are writable."""

from __future__ import annotations

import stat
from pathlib import Path

import structlog

from kernel.config.schema import LinaSettingsSchema

logger = structlog.get_logger(__name__)


class ConfigDirectoryInitializer:
    """Creates and validates the on-disk directory layout required by LINA."""

    def __init__(self, settings: LinaSettingsSchema) -> None:
        self._settings = settings

    def required_directories(self) -> list[Path]:
        return [
            self._settings.data_directory,
            self._settings.reports_directory,
            self._settings.chromadb.persist_directory,
            self._settings.logging.log_directory,
            self._settings.authz.audit_log_path.parent,
            self._settings.plugin_manager.plugins_directory,
        ]

    def initialize(self) -> None:
        for directory in self.required_directories():
            self._ensure_directory(directory)
        logger.info(
            "config.directories_initialized",
            count=len(self.required_directories()),
        )

    @staticmethod
    def _ensure_directory(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        mode = path.stat().st_mode
        if not (mode & stat.S_IWUSR):
            raise PermissionError(f"Directory is not writable: {path}")


def bootstrap(settings: LinaSettingsSchema) -> LinaSettingsSchema:
    """Convenience entrypoint: initialize directories and return settings unchanged."""
    ConfigDirectoryInitializer(settings).initialize()
    return settings