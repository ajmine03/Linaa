"""structlog configuration — JSON in production, console-pretty in development."""

from __future__ import annotations

import logging
import sys

import structlog

from kernel.config.schema import Environment, LoggingConfig


def configure_logging(config: LoggingConfig, *, environment: Environment) -> None:
    """Configure structlog + stdlib logging once at process startup.

    Idempotent-ish: safe to call multiple times (e.g. in tests), each call
    fully replaces the prior configuration.
    """
    config.log_directory.mkdir(parents=True, exist_ok=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if config.redact_secrets:
        shared_processors.append(_redact_sensitive_keys)

    if config.json_format or environment == Environment.PRODUCTION:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[config.level.value]
        ),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    file_handler = logging.FileHandler(config.log_directory / "lina.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(config.level.value)


_SENSITIVE_KEYS = frozenset(
    {"password", "secret", "api_key", "token", "authorization", "secret_ref", "credential"}
)


def _redact_sensitive_keys(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict