"""Tests for the lookup_sdi_error tool."""

import pytest

from fatturapa_mcp.tools.sdi_errors import lookup_sdi_error
from tests.conftest import MockCtx


class TestLookupSdiError:
    async def test_known_code_returns_all_keys(self) -> None:
        result = await lookup_sdi_error("00001")
        assert result["code"] == "00001"
        assert len(result["description"]) > 0
        assert len(result["category"]) > 0
        assert len(result["resolution"]) > 0

    async def test_struttura_code_00001(self) -> None:
        result = await lookup_sdi_error("00001")
        assert result["category"] == "STRUTTURA"

    async def test_struttura_code_00002(self) -> None:
        result = await lookup_sdi_error("00002")
        assert result["category"] == "STRUTTURA"

    async def test_contenuto_code_00101(self) -> None:
        result = await lookup_sdi_error("00101")
        assert result["category"] == "CONTENUTO"

    async def test_firma_code_00200(self) -> None:
        result = await lookup_sdi_error("00200")
        assert result["category"] == "FIRMA"

    async def test_firma_code_00202_scaduto(self) -> None:
        result = await lookup_sdi_error("00202")
        assert result["category"] == "FIRMA"
        assert "scadut" in result["description"].lower()

    async def test_recapito_code_00300(self) -> None:
        result = await lookup_sdi_error("00300")
        assert result["category"] == "RECAPITO"

    async def test_duplicato_code_00115(self) -> None:
        result = await lookup_sdi_error("00115")
        assert result["category"] == "CONTENUTO"
        assert "duplicat" in result["description"].lower()

    async def test_result_code_matches_input(self) -> None:
        for code in ("00001", "00103", "00201", "00304"):
            result = await lookup_sdi_error(code)
            assert result["code"] == code

    async def test_unknown_code_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown SDI error code"):
            await lookup_sdi_error("UNKNOWN")

    async def test_unknown_numeric_code_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown SDI error code"):
            await lookup_sdi_error("99999")

    async def test_empty_string_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            await lookup_sdi_error("")


class TestLookupSdiErrorCtxLogging:
    """Verify ctx log calls are emitted with correct structure."""

    async def test_known_code_emits_start_and_done(self) -> None:
        """A known code produces a start info and a done info log."""
        ctx = MockCtx()
        await lookup_sdi_error("00001", ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2

    async def test_unknown_code_emits_warning(self) -> None:
        """An unknown code routes the done log to ctx.warning before raising."""
        ctx = MockCtx()
        with pytest.raises(ValueError):
            await lookup_sdi_error("99999", ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.warnings) == 1


class TestLookupSdiErrorProgress:
    """Verify progress notifications are emitted in the correct order."""

    async def test_known_code_emits_three_steps(self) -> None:
        """Happy path reports steps 1/3, 2/3, 3/3 in order."""
        ctx = MockCtx()
        await lookup_sdi_error("00001", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3), (2, 3), (3, 3)]

    async def test_unknown_code_emits_only_first_step(self) -> None:
        """Unknown code stops after step 1 — lookup fails before step 2."""
        ctx = MockCtx()
        with pytest.raises(ValueError):
            await lookup_sdi_error("99999", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3)]

    async def test_no_ctx_does_not_raise(self) -> None:
        """Calling without ctx must not raise."""
        result = await lookup_sdi_error("00001", ctx=None)
        assert result["code"] == "00001"
