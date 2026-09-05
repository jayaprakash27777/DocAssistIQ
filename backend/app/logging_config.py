"""DocAssistIQ Backend — Structured Logging Configuration.

Configures `structlog` to produce:
  - Human-readable console output during development (colours, aligned keys)
  - Machine-readable JSON output in all other environments (stdout, one JSON
    object per line — compatible with log aggregators such as Loki, Datadog,
    CloudWatch)

Every log record automatically includes:
  - `timestamp`  — ISO-8601 UTC
  - `level`      — DEBUG / INFO / WARNING / ERROR / CRITICAL
  - `logger`     — dotted module path
  - `request_id` — correlation ID from the current ContextVar
  - `event`      — the human message

Safe-logging rules enforced at this layer:
  - stdlib logging is also routed through structlog so third-party
    libraries (SQLAlchemy, uvicorn) share the same pipeline.
  - Sensitive field names in log records are detected and redacted.
    The check is intentionally conservative; the source code must
    not pass sensitive values as structured fields.

Usage:
    from app.logging_config import configure_logging
    configure_logging(level="INFO", json_output=True)

    import structlog
    log = structlog.get_logger(__name__)
    log.info("patient record retrieved", patient_id=pid)
"""

import logging
import sys

import structlog

from app.middleware.request_id import get_request_id

# Fields whose values should be redacted if they appear in log records.
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "secret_key",
        "authorization",
        "api_key",
        "cookie",
        "set_cookie",
    }
)


def _redact_sensitive(
    _logger: object,
    _method: str,
    event_dict: dict,
) -> dict:
    """Structlog processor: redact sensitive keys before output."""
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict


def _inject_request_id(
    _logger: object,
    _method: str,
    event_dict: dict,
) -> dict:
    """Structlog processor: attach the current request ID to every record."""
    event_dict["request_id"] = get_request_id()
    return event_dict


def configure_logging(*, level: str = "INFO", json_output: bool = False) -> None:
    """Configure structlog + stdlib logging for the application.

    Call once at application startup (inside ``create_app``).

    Args:
        level:       Logging level string e.g. "DEBUG", "INFO".
        json_output: If True, emit JSON lines. If False, pretty console output.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _inject_request_id,
        _redact_sensitive,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        # Production: JSON lines to stdout
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: human-readable with colours
        renderer = structlog.dev.ConsoleRenderer(colors=True)  # type: ignore[assignment]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level <= logging.DEBUG else logging.WARNING
    )
