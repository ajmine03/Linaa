"""Runtime settings loader combining env vars, YAML, and defaults.

Precedence (highest to lowest):
  1. Environment variables (LINA_*)
  2. YAML config file (config/lina.yaml or path from LINA_CONFIG_FILE)
  3. Schema defaults
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from kernel.config.exceptions import ConfigFileNotFoundError, ConfigValidationError
from kernel.config.schema import LinaSettingsSchema


class _EnvOverrides(BaseSettings):
    """Captures LINA_* environment variables for override merging."""

    model_config = SettingsConfigDict(
        env_prefix="LINA_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str | None = None
    data_directory: str | None = None
    config_file: str | None = None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `override` into `base`, returning a new dict."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigFileNotFoundError(str(path))
    with path.open("r", encoding="utf-8") as fh:
        content = yaml.safe_load(fh) or {}
    if not isinstance(content, dict):
        raise ConfigValidationError(f"Config file {path} must contain a YAML mapping at root.")
    return content


def load_settings(
    config_path: str | Path | None = None,
    *,
    strict: bool = True,
) -> LinaSettingsSchema:
    """Build a validated `LinaSettingsSchema` from file + environment.

    Args:
        config_path: Explicit path to a YAML config file. If None, checks
            LINA_CONFIG_FILE env var, then falls back to ./config/lina.yaml,
            and finally to schema defaults if nothing is found.
        strict: If True, raise on validation errors. If False, log-equivalent
            errors are collected and defaults are used where possible
            (still raises ConfigValidationError — LINA never runs on silently
            invalid config).

    Returns:
        A fully validated LinaSettingsSchema instance.
    """
    env_overrides = _EnvOverrides()

    resolved_path: Path | None = None
    if config_path is not None:
        resolved_path = Path(config_path)
    elif env_overrides.config_file:
        resolved_path = Path(env_overrides.config_file)
    else:
        default_path = Path("./config/lina.yaml")
        if default_path.exists():
            resolved_path = default_path

    file_data: dict[str, Any] = {}
    if resolved_path is not None:
        file_data = _load_yaml(resolved_path)

    env_data: dict[str, Any] = {}
    if env_overrides.environment:
        env_data["environment"] = env_overrides.environment
    if env_overrides.data_directory:
        env_data["data_directory"] = env_overrides.data_directory

    merged = _deep_merge(file_data, env_data)

    try:
        return LinaSettingsSchema.model_validate(merged)
    except Exception as exc:  # noqa: BLE001 - normalized into ConfigValidationError
        raise ConfigValidationError(
            "Failed to validate LINA configuration.", errors=[str(exc)]
        ) from exc


@lru_cache(maxsize=1)
def get_settings() -> LinaSettingsSchema:
    """Cached settings accessor for dependency injection across the app.

    Use `load_settings()` directly in tests to bypass the cache.
    """
    return load_settings()


def reload_settings(config_path: str | Path | None = None) -> LinaSettingsSchema:
    """Clear the settings cache and reload — useful for tests / hot reload."""
    get_settings.cache_clear()
    settings = load_settings(config_path)
    get_settings.cache_clear()
    get_settings.__wrapped__ = None  # type: ignore[attr-defined]
    return settings