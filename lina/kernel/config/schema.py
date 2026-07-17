"""Typed configuration schema for LINA, backed by Pydantic v2 models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """SQLite / SQLAlchemy connection configuration."""

    url: str = Field(default="sqlite+aiosqlite:///./data/lina.db")
    echo: bool = Field(default=False)
    pool_pre_ping: bool = Field(default=True)
    connect_timeout_seconds: int = Field(default=30, ge=1, le=300)

    @field_validator("url")
    @classmethod
    def validate_scheme(cls, v: str) -> str:
        if not v.startswith(("sqlite", "sqlite+aiosqlite")):
            raise ValueError("Only SQLite backends are supported in this build.")
        return v


class ChromaDBConfig(BaseModel):
    """Vector store configuration for the Memory Engine / Knowledge Graph."""

    persist_directory: Path = Field(default=Path("./data/chroma"))
    collection_prefix: str = Field(default="lina")
    distance_metric: str = Field(default="cosine")


class OllamaConfig(BaseModel):
    """Local model runtime configuration used by the Model Router."""

    base_url: str = Field(default="http://localhost:11434")
    default_model: str = Field(default="llama3.1:8b")
    reasoning_model: str = Field(default="llama3.1:70b")
    embedding_model: str = Field(default="nomic-embed-text")
    request_timeout_seconds: int = Field(default=120, ge=1, le=1800)
    max_retries: int = Field(default=3, ge=0, le=10)
    keep_alive: str = Field(default="5m")


class AuthzConfig(BaseModel):
    """Authorization framework configuration — engagement scoping guardrails."""

    require_engagement_scope: bool = Field(default=True)
    allow_unscoped_read_only_tools: bool = Field(default=True)
    max_concurrent_engagements: int = Field(default=5, ge=1, le=100)
    audit_log_path: Path = Field(default=Path("./data/audit/audit.log"))


class APIConfig(BaseModel):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])
    api_key_header: str = Field(default="X-LINA-API-Key")
    rate_limit_per_minute: int = Field(default=120, ge=1)


class PluginManagerConfig(BaseModel):
    plugins_directory: Path = Field(default=Path("./plugins"))
    enabled_plugins: list[str] = Field(
        default_factory=lambda: [
            "pentest",
            "coding_agent",
            "osint",
            "bug_bounty",
            "dfir",
            "malware",
            "cloud",
            "active_directory",
            "wireless",
            "mobile",
            "container",
            "blue_team",
        ]
    )
    auto_discover: bool = Field(default=True)
    fail_on_plugin_error: bool = Field(default=False)


class LoggingConfig(BaseModel):
    level: LogLevel = Field(default=LogLevel.INFO)
    json_format: bool = Field(default=True)
    log_directory: Path = Field(default=Path("./data/logs"))
    redact_secrets: bool = Field(default=True)


class LinaSettingsSchema(BaseModel):
    """Root configuration schema for the entire LINA system."""

    environment: Environment = Field(default=Environment.DEVELOPMENT)
    data_directory: Path = Field(default=Path("./data"))
    reports_directory: Path = Field(default=Path("./reports"))

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    authz: AuthzConfig = Field(default_factory=AuthzConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    plugin_manager: PluginManagerConfig = Field(default_factory=PluginManagerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = {"extra": "forbid", "validate_assignment": True}