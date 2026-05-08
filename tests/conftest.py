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
