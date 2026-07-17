"""Configuration-layer exceptions for the LINA kernel."""

from __future__ import annotations


class ConfigError(Exception):
    """Base exception for all configuration-related failures."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when a required configuration file is missing on disk."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Configuration file not found: {path}")


class ConfigValidationError(ConfigError):
    """Raised when configuration values fail schema validation."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        self.errors = errors or []
        detail = f" | Errors: {'; '.join(self.errors)}" if self.errors else ""
        super().__init__(f"{message}{detail}")


class ConfigKeyError(ConfigError):
    """Raised when a required configuration key is absent and has no default."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Missing required configuration key: {key}")