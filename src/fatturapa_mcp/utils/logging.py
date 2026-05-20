"""
fatturapa_mcp.utils.logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
JSON structured logger for fatturapa_mcp.

Rules enforced here:
- XML data is NEVER logged — only derived metadata.
- Every log entry must carry a correlation_id for request tracing.
- Log level is controlled by the LOG_LEVEL environment variable.
"""

import json
import logging
import os
import time
import uuid
from typing import Any

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Instance-level attributes present on every LogRecord — used to filter them
# out when serialising extra fields injected by the caller.
_STDLIB_LOG_ATTRS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "taskName",
    }
)


class _JsonFormatter(logging.Formatter):
    """Serialises each LogRecord as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render the log record as a compact JSON object string."""
        entry: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, val in record.__dict__.items():
            if key not in _STDLIB_LOG_ATTRS and not key.startswith("_"):
                entry[key] = val
        return json.dumps(entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for JSON structured output.

    The returned logger emits JSON lines compatible with log aggregation
    pipelines (e.g., CloudWatch, Loki). Caller must inject correlation_id
    via the ``extra`` dict on each log call.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A configured Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(_LOG_LEVEL)
    return logger


def make_correlation_id() -> str:
    """Generate a new UUID4 correlation ID for request tracing.

    Returns:
        A UUID4 string suitable for use as a log correlation_id.
    """
    return str(uuid.uuid4())


def build_log_msg(event: str, **kw: object) -> str:
    """Build a JSON-formatted structured log message string.

    Args:
        event: Log event name (e.g., ``"validate_invoice.start"``).
        **kw: Additional key-value metadata to include in the JSON object.

    Returns:
        A JSON string suitable for passing to ctx.info / ctx.warning / ctx.error.
    """
    return json.dumps({"event": event, **kw}, ensure_ascii=False)


def elapsed_ms(start: float) -> float:
    """Return milliseconds elapsed since *start* (a ``time.monotonic()`` value).

    Args:
        start: Reference time obtained from ``time.monotonic()``.

    Returns:
        Elapsed time in milliseconds, rounded to 2 decimal places.
    """
    return round((time.monotonic() - start) * 1000, 2)


async def ctx_log(
    ctx: Any,  # Any = Context[Any, Any, Any] — FastMCP type params are opaque to tools
    event: str,
    level: str = "info",
    **kw: object,
) -> None:
    """Emit a structured JSON log entry via the MCP context if *ctx* is not None.

    This is a no-op when *ctx* is None, allowing tools to call it unconditionally
    without defensive guards at every call site.

    Args:
        ctx: MCP Context instance, or None (no-op).
        event: Log event identifier (e.g., ``"validate_invoice.start"``).
        level: Log level string — ``"info"``, ``"warning"``, or ``"error"``.
               Defaults to ``"info"``.
        **kw: Metadata fields merged into the JSON message body.
    """
    if ctx is None:
        return
    msg = build_log_msg(event=event, **kw)
    if level == "error":
        await ctx.error(msg)
    elif level == "warning":
        await ctx.warning(msg)
    else:
        await ctx.info(msg)
