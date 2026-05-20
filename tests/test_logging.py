"""Tests for the logging utility module."""

import json
import logging
import uuid

from fatturapa_mcp.utils.logging import (
    build_log_msg,
    ctx_log,
    elapsed_ms,
    get_logger,
    make_correlation_id,
)
from tests.conftest import MockCtx


class TestMakeCorrelationId:
    """Tests for the make_correlation_id helper."""

    def test_returns_string(self) -> None:
        """make_correlation_id should return a string."""
        result = make_correlation_id()
        assert isinstance(result, str)

    def test_returns_valid_uuid4(self) -> None:
        """Returned value must be parseable as a UUID."""
        result = make_correlation_id()
        parsed = uuid.UUID(result)
        assert parsed.version == 4

    def test_each_call_returns_unique_id(self) -> None:
        """Each invocation must produce a distinct correlation ID."""
        assert make_correlation_id() != make_correlation_id()


class TestGetLogger:
    """Tests for get_logger."""

    def test_returns_logger_instance(self) -> None:
        """get_logger should return a logging.Logger."""
        logger = get_logger(__name__)
        assert isinstance(logger, logging.Logger)

    def test_logger_name_matches(self) -> None:
        """Returned logger name matches the argument."""
        logger = get_logger("fatturapa_mcp.test")
        assert logger.name == "fatturapa_mcp.test"

    def test_logger_has_handler(self) -> None:
        """Logger must have at least one handler attached."""
        logger = get_logger("fatturapa_mcp.test_handler")
        assert len(logger.handlers) >= 1

    def test_json_formatter_emits_json(self) -> None:
        """Handler formatter must produce parseable JSON."""
        logger = get_logger("fatturapa_mcp.test_fmt")
        handler = logger.handlers[0]
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        assert handler.formatter is not None
        output = handler.formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "hello"
        assert parsed["level"] == "INFO"

    def test_extra_fields_appear_in_json(self) -> None:
        """Extra fields injected via LogRecord.__dict__ are serialised into JSON."""
        logger = get_logger("fatturapa_mcp.test_extra")
        handler = logger.handlers[0]
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="msg",
            args=(),
            exc_info=None,
        )
        record.__dict__["correlation_id"] = "abc-123"
        assert handler.formatter is not None
        parsed = json.loads(handler.formatter.format(record))
        assert parsed["correlation_id"] == "abc-123"


class TestBuildLogMsg:
    """Tests for build_log_msg."""

    def test_returns_valid_json(self) -> None:
        """build_log_msg always returns parseable JSON."""
        msg = build_log_msg("test.event", key="value")
        parsed = json.loads(msg)
        assert parsed["event"] == "test.event"
        assert parsed["key"] == "value"

    def test_no_extra_fields(self) -> None:
        """build_log_msg with only event produces a single-key JSON object."""
        parsed = json.loads(build_log_msg("solo"))
        assert parsed == {"event": "solo"}


class TestElapsedMs:
    """Tests for elapsed_ms."""

    def test_returns_float(self) -> None:
        """elapsed_ms must return a float."""
        import time

        start = time.monotonic()
        result = elapsed_ms(start)
        assert isinstance(result, float)

    def test_non_negative(self) -> None:
        """Elapsed time must be >= 0."""
        import time

        start = time.monotonic()
        assert elapsed_ms(start) >= 0.0


class TestCtxLog:
    """Tests for ctx_log."""

    async def test_noop_when_ctx_none(self) -> None:
        """ctx_log is a no-op when ctx is None — no exception raised."""
        await ctx_log(None, "test.event", key="val")

    async def test_info_level(self) -> None:
        """Default level routes to ctx.info."""
        ctx = MockCtx()
        await ctx_log(ctx, "test.start", foo=1)
        assert len(ctx.infos) == 1
        parsed = json.loads(ctx.infos[0])
        assert parsed["event"] == "test.start"
        assert parsed["foo"] == 1

    async def test_warning_level(self) -> None:
        """level='warning' routes to ctx.warning."""
        ctx = MockCtx()
        await ctx_log(ctx, "test.warn", level="warning", x=2)
        assert len(ctx.warnings) == 1
        parsed = json.loads(ctx.warnings[0])
        assert parsed["event"] == "test.warn"

    async def test_error_level(self) -> None:
        """level='error' routes to ctx.error."""
        ctx = MockCtx()
        await ctx_log(ctx, "test.err", level="error")
        assert len(ctx.errors) == 1

    async def test_unknown_level_falls_back_to_info(self) -> None:
        """Any unrecognised level string falls back to ctx.info."""
        ctx = MockCtx()
        await ctx_log(ctx, "test.fallback", level="debug")
        assert len(ctx.infos) == 1
        assert len(ctx.warnings) == 0
        assert len(ctx.errors) == 0
