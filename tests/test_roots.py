"""Tests for the roots path-guard utility."""

import os
from pathlib import Path

import pytest

from fatturapa_mcp.utils.roots import (
    ensure_path_allowed,
    get_allowed_roots,
    is_path_allowed,
    is_unrestricted_mode,
)


# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from the developer's own environment variables."""
    monkeypatch.delenv("FATTURAPA_ALLOWED_ROOTS", raising=False)
    monkeypatch.delenv("FATTURAPA_ALLOW_ALL_PATHS", raising=False)


# is_path_allowed
# ---------------------------------------------------------------------------


class TestIsPathAllowed:
    """Contract tests for is_path_allowed."""

    def test_path_inside_allowed_root_returns_true(self, tmp_path: Path) -> None:
        """A file nested under an allowed root is permitted."""
        target = tmp_path / "invoices" / "inv001.xml"
        target.parent.mkdir()
        target.touch()
        assert is_path_allowed(target, [tmp_path]) is True

    def test_path_outside_allowed_root_returns_false(self, tmp_path: Path) -> None:
        """A file outside every allowed root is denied."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside" / "evil.xml"
        outside.parent.mkdir()
        outside.touch()
        assert is_path_allowed(outside, [allowed]) is False

    def test_path_traversal_attempt_returns_false(self, tmp_path: Path) -> None:
        """A ``..`` escape that leaves the root resolves to a denied path."""
        allowed = tmp_path / "safe"
        allowed.mkdir()
        escape = allowed / ".." / "other.xml"
        # resolves to tmp_path / other.xml — outside `allowed`
        assert is_path_allowed(escape, [allowed]) is False

    def test_empty_roots_denies_any_path(self, tmp_path: Path) -> None:
        """With no roots configured the guard fails closed."""
        assert is_path_allowed(tmp_path / "anything.xml", []) is False

    def test_relative_path_is_resolved_before_check(self, tmp_path: Path) -> None:
        """A relative path is resolved to absolute before comparison."""
        target = tmp_path / "file.xml"
        target.touch()
        # is_relative_to works on resolved absolute paths
        assert is_path_allowed(str(target), [tmp_path]) is True

    def test_multiple_roots_matches_second(self, tmp_path: Path) -> None:
        """A path under the second root in a list is still permitted."""
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        root1.mkdir()
        root2.mkdir()
        target = root2 / "doc.xml"
        target.touch()
        assert is_path_allowed(target, [root1, root2]) is True

    def test_multiple_roots_no_match_returns_false(self, tmp_path: Path) -> None:
        """A path matching none of the roots is denied."""
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        other = tmp_path / "other"
        root1.mkdir()
        root2.mkdir()
        other.mkdir()
        target = other / "doc.xml"
        target.touch()
        assert is_path_allowed(target, [root1, root2]) is False

    def test_path_exactly_at_root_boundary_is_permitted(self, tmp_path: Path) -> None:
        """The root directory itself is within the allowed area."""
        assert is_path_allowed(tmp_path, [tmp_path]) is True

    def test_string_path_accepted(self, tmp_path: Path) -> None:
        """A plain str is accepted as well as a Path object."""
        assert is_path_allowed(str(tmp_path), [tmp_path]) is True


# ---------------------------------------------------------------------------
# get_allowed_roots
# ---------------------------------------------------------------------------


class TestGetAllowedRoots:
    """Tests for get_allowed_roots environment loading."""

    def test_empty_env_returns_empty_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unset env variable returns an empty list (open mode)."""
        monkeypatch.delenv("FATTURAPA_ALLOWED_ROOTS", raising=False)
        assert get_allowed_roots() == []

    def test_blank_env_returns_empty_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Whitespace-only value returns an empty list."""
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", "   ")
        assert get_allowed_roots() == []

    def test_single_path_parsed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A single path is returned as a one-element list."""
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(tmp_path))
        result = get_allowed_roots()
        assert result == [tmp_path]

    def test_multiple_paths_parsed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Multiple paths separated by os.pathsep are all returned."""
        p1 = tmp_path / "a"
        p2 = tmp_path / "b"
        joined = os.pathsep.join([str(p1), str(p2)])
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", joined)
        result = get_allowed_roots()
        assert result == [p1, p2]

    def test_whitespace_around_paths_stripped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Leading/trailing whitespace around each path entry is ignored."""
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", f"  {tmp_path}  ")
        result = get_allowed_roots()
        assert result == [tmp_path]


class TestUnrestrictedMode:
    """The escape hatch must be explicit, and only accept explicit values."""

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
    def test_recognised_truthy_values_enable_open_mode(
        self, value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Documented opt-in values switch the guard off."""
        monkeypatch.setenv("FATTURAPA_ALLOW_ALL_PATHS", value)
        assert is_unrestricted_mode() is True

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "maybe", " "])
    def test_other_values_leave_guard_active(
        self, value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Anything else keeps the guard on — no accidental opt-out."""
        monkeypatch.setenv("FATTURAPA_ALLOW_ALL_PATHS", value)
        assert is_unrestricted_mode() is False

    def test_open_mode_permits_path_outside_roots(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With the opt-in set, an unlisted path is readable again."""
        monkeypatch.setenv("FATTURAPA_ALLOW_ALL_PATHS", "1")
        assert is_path_allowed(tmp_path / "anything.xml", []) is True


class TestEnsurePathAllowed:
    """The raising wrapper must explain which of the two failures occurred."""

    def test_allows_path_inside_configured_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A path inside a configured root does not raise."""
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(tmp_path))
        target = tmp_path / "invoice.xml"
        target.touch()
        ensure_path_allowed(target)

    def test_unconfigured_server_explains_how_to_configure(
        self, tmp_path: Path
    ) -> None:
        """With no roots set, the error names the variable to set."""
        with pytest.raises(PermissionError, match="FATTURAPA_ALLOWED_ROOTS"):
            ensure_path_allowed(tmp_path / "invoice.xml")

    def test_path_outside_roots_reports_a_different_cause(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With roots set, the error says the path is outside them."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(allowed))
        with pytest.raises(PermissionError, match="outside the allowed roots"):
            ensure_path_allowed(tmp_path / "elsewhere.xml")

    def test_traversal_out_of_root_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ../ escape from an allowed root is refused after resolution."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(allowed))
        with pytest.raises(PermissionError):
            ensure_path_allowed(allowed / ".." / "secret.xml")
