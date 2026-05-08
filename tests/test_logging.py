"""Tests for the logging utility module."""

import uuid

import pytest

from fatturapa_mcp.utils.logging import get_logger, make_correlation_id


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


class TestGetLoggerSkeleton:
    """Skeleton: verify get_logger raises NotImplementedError until implemented."""

    def test_raises_not_implemented(self) -> None:
        """Skeleton: get_logger raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            get_logger(__name__)
