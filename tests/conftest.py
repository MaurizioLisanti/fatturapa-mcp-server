"""Pytest fixtures shared across all test modules."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_v13_xml() -> str:
    """Return the content of the valid FatturaPA v1.3 fixture."""
    return (FIXTURES_DIR / "valid_v13.xml").read_text(encoding="utf-8")


@pytest.fixture
def valid_v12_xml() -> str:
    """Return the content of the valid FatturaPA v1.2 fixture."""
    return (FIXTURES_DIR / "valid_v12.xml").read_text(encoding="utf-8")


@pytest.fixture
def invalid_xml() -> str:
    """Return the content of the malformed XML fixture."""
    return (FIXTURES_DIR / "invalid.xml").read_text(encoding="utf-8")


class MockCtx:
    """Minimal MCP Context mock that captures structured log calls for assertions."""

    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.progress: list[tuple[float, float | None]] = []

    async def info(self, message: str) -> None:
        """Capture an info-level log message."""
        self.infos.append(message)

    async def warning(self, message: str) -> None:
        """Capture a warning-level log message."""
        self.warnings.append(message)

    async def error(self, message: str) -> None:
        """Capture an error-level log message."""
        self.errors.append(message)

    async def report_progress(
        self,
        progress: float,
        total: float | None = None,
        message: str | None = None,
    ) -> None:
        """Capture a progress notification."""
        self.progress.append((progress, total))


@pytest.fixture
def mock_ctx() -> MockCtx:
    """Return a fresh MockCtx instance for each test."""
    return MockCtx()
