"""
fatturapa_mcp.utils.logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
JSON structured logger for fatturapa_mcp.

Rules enforced here:
- XML data is NEVER logged — only derived metadata.
- Every log entry must carry a correlation_id for request tracing.
- Log level is controlled by the LOG_LEVEL environment variable.
"""

import logging
import uuid


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for JSON structured output.

    The returned logger emits JSON lines compatible with log aggregation
    pipelines (e.g., CloudWatch, Loki). Caller must inject correlation_id
    via the `extra` dict on each log call.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A configured Logger instance.
    """
    raise NotImplementedError("Implemented in TASK_scaffold logging utility")


def make_correlation_id() -> str:
    """Generate a new UUID4 correlation ID for request tracing.

    Returns:
        A UUID4 string suitable for use as a log correlation_id.
    """
    return str(uuid.uuid4())
