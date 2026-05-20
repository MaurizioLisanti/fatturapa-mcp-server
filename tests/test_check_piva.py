"""Tests for the check_piva tool."""

from fatturapa_mcp.tools.check_piva import check_piva
from tests.conftest import MockCtx


class TestCheckPiva:
    # ── Valid P.IVA ─────────────────────────────────────────────────────────

    async def test_valid_piva_returns_true(self) -> None:
        # 12345678903 passes the official MEF checksum algorithm
        result = await check_piva("12345678903")
        assert result["valid"] is True
        assert result["reason"] is None

    async def test_valid_piva_normalised_field(self) -> None:
        result = await check_piva("12345678903")
        assert result["piva"] == "12345678903"

    async def test_strips_it_prefix_lowercase(self) -> None:
        result = await check_piva("it12345678903")
        assert result["valid"] is True
        assert result["piva"] == "12345678903"

    async def test_strips_it_prefix_uppercase(self) -> None:
        result = await check_piva("IT12345678903")
        assert result["valid"] is True
        assert result["piva"] == "12345678903"

    async def test_strips_leading_trailing_whitespace(self) -> None:
        result = await check_piva("  12345678903  ")
        assert result["valid"] is True

    # ── Invalid checksum ────────────────────────────────────────────────────

    async def test_invalid_piva_wrong_check_digit(self) -> None:
        result = await check_piva("12345678900")
        assert result["valid"] is False
        assert result["reason"] is not None

    async def test_invalid_piva_reason_mentions_checksum(self) -> None:
        result = await check_piva("12345678900")
        assert result["reason"] is not None
        assert "3" in result["reason"]  # expected digit is 3

    async def test_all_zeros_passes_checksum(self) -> None:
        # Mathematically valid: all zeros make the checksum sum to 0 mod 10.
        # Pure checksum validation does not reject semantically invalid P.IVA.
        result = await check_piva("00000000000")
        assert result["valid"] is True

    # ── Format errors ───────────────────────────────────────────────────────

    async def test_too_short_returns_false(self) -> None:
        result = await check_piva("123")
        assert result["valid"] is False
        assert result["reason"] is not None

    async def test_too_long_returns_false(self) -> None:
        result = await check_piva("123456789012")
        assert result["valid"] is False

    async def test_non_digits_returns_false(self) -> None:
        result = await check_piva("1234567890A")
        assert result["valid"] is False
        assert result["reason"] is not None

    async def test_empty_string_returns_false(self) -> None:
        result = await check_piva("")
        assert result["valid"] is False

    async def test_only_prefix_returns_false(self) -> None:
        result = await check_piva("IT")
        assert result["valid"] is False

    # ── Normalised piva field ───────────────────────────────────────────────

    async def test_piva_field_stripped_on_invalid(self) -> None:
        result = await check_piva("12345678900")
        assert result["piva"] == "12345678900"

    async def test_piva_field_no_it_prefix_after_strip(self) -> None:
        result = await check_piva("IT12345678900")
        assert result["piva"] == "12345678900"


class TestCheckPivaCtxLogging:
    """Verify ctx log calls are emitted with correct structure."""

    async def test_valid_piva_emits_start_and_done(self) -> None:
        """A valid P.IVA produces two info log entries."""
        ctx = MockCtx()
        await check_piva("12345678903", ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2

    async def test_invalid_piva_emits_done_log(self) -> None:
        """An invalid P.IVA still emits a done info log."""
        ctx = MockCtx()
        await check_piva("123", ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2


class TestCheckPivaProgress:
    """Verify progress notifications are emitted in the correct order."""

    async def test_valid_piva_emits_three_steps(self) -> None:
        """Happy path reports steps 1/3, 2/3, 3/3 in order."""
        ctx = MockCtx()
        await check_piva("12345678903", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3), (2, 3), (3, 3)]

    async def test_format_error_emits_only_first_step(self) -> None:
        """Format validation failure stops after step 1."""
        ctx = MockCtx()
        await check_piva("abc", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3)]

    async def test_wrong_length_emits_only_first_step(self) -> None:
        """Wrong length stops after step 1."""
        ctx = MockCtx()
        await check_piva("123", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3)]

    async def test_no_ctx_does_not_raise(self) -> None:
        """Calling without ctx must not raise."""
        result = await check_piva("12345678903", ctx=None)
        assert result["valid"] is True
