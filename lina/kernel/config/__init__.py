"""LINA kernel configuration module.

Public API:
    - get_settings(): cached accessor for the validated global settings.
    - load_settings(): explicit loader (file/env/defaults) without caching.
    - reload_settings(): clears cache and reloads.
    - bootstrap(): ensures required directories exist on disk.
"""

from kernel.config.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigKeyError,
    ConfigValidationError,
)
from kernel.config.loader import ConfigDirectoryInitializer, bootstrap
from kernel.config.schema import (
    APIConfig,
    AuthzConfig,
    ChromaDBConfig,
    DatabaseConfig,
    Environment,
    LinaSettingsSchema,
    LogLevel,
    LoggingConfig,
    OllamaConfig,
    PluginManagerConfig,
)
from kernel.config.settings import get_settings, load_settings, reload_settings

__all__ = [
    "APIConfig",
    "AuthzConfig",
    "ChromaDBConfig",
    "ConfigDirectoryInitializer",
    "ConfigError",
    "ConfigFileNotFoundError",
    "ConfigKeyError",
    "ConfigValidationError",
    "DatabaseConfig",
    "Environment",
    "LinaSettingsSchema",
    "LogLevel",
    "LoggingConfig",
    "OllamaConfig",
    "PluginManagerConfig",
    "bootstrap",
    "get_settings",
    "load_settings",
    "reload_settings",
]