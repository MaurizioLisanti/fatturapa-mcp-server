"""Tests for the check_piva tool."""

from fatturapa_mcp.tools.check_piva import check_piva


class TestCheckPiva:
    # ── Valid P.IVA ─────────────────────────────────────────────────────────

    def test_valid_piva_returns_true(self) -> None:
        # 12345678903 passes the official MEF checksum algorithm
        result = check_piva("12345678903")
        assert result["valid"] is True
        assert result["reason"] is None

    def test_valid_piva_normalised_field(self) -> None:
        result = check_piva("12345678903")
        assert result["piva"] == "12345678903"

    def test_strips_it_prefix_lowercase(self) -> None:
        result = check_piva("it12345678903")
        assert result["valid"] is True
        assert result["piva"] == "12345678903"

    def test_strips_it_prefix_uppercase(self) -> None:
        result = check_piva("IT12345678903")
        assert result["valid"] is True
        assert result["piva"] == "12345678903"

    def test_strips_leading_trailing_whitespace(self) -> None:
        result = check_piva("  12345678903  ")
        assert result["valid"] is True

    # ── Invalid checksum ────────────────────────────────────────────────────

    def test_invalid_piva_wrong_check_digit(self) -> None:
        result = check_piva("12345678900")
        assert result["valid"] is False
        assert result["reason"] is not None

    def test_invalid_piva_reason_mentions_checksum(self) -> None:
        result = check_piva("12345678900")
        assert result["reason"] is not None
        assert "3" in result["reason"]  # expected digit is 3

    def test_all_zeros_passes_checksum(self) -> None:
        # Mathematically valid: all zeros make the checksum sum to 0 mod 10.
        # Pure checksum validation does not reject semantically invalid P.IVA.
        result = check_piva("00000000000")
        assert result["valid"] is True

    # ── Format errors ───────────────────────────────────────────────────────

    def test_too_short_returns_false(self) -> None:
        result = check_piva("123")
        assert result["valid"] is False
        assert result["reason"] is not None

    def test_too_long_returns_false(self) -> None:
        result = check_piva("123456789012")
        assert result["valid"] is False

    def test_non_digits_returns_false(self) -> None:
        result = check_piva("1234567890A")
        assert result["valid"] is False
        assert result["reason"] is not None

    def test_empty_string_returns_false(self) -> None:
        result = check_piva("")
        assert result["valid"] is False

    def test_only_prefix_returns_false(self) -> None:
        result = check_piva("IT")
        assert result["valid"] is False

    # ── Normalised piva field ───────────────────────────────────────────────

    def test_piva_field_stripped_on_invalid(self) -> None:
        result = check_piva("12345678900")
        assert result["piva"] == "12345678900"

    def test_piva_field_no_it_prefix_after_strip(self) -> None:
        result = check_piva("IT12345678900")
        assert result["piva"] == "12345678900"
