"""Tests for the validate_invoice tool."""

from pathlib import Path

import pytest

from fatturapa_mcp.tools.validate import validate_invoice
from tests.conftest import MockCtx

# Well-formed v1.3 XML that fails XSD because the required `versione` attribute
# is absent — used to test structural (non-parse) validation failure.
_V13_MISSING_VERSIONE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<p:FatturaElettronica"
    ' xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3">'
    "<FatturaElettronicaHeader/>"
    "<FatturaElettronicaBody/>"
    "</p:FatturaElettronica>"
)

# Well-formed XML whose namespace is not a recognised FatturaPA namespace.
_UNKNOWN_NAMESPACE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<ns:FatturaElettronica xmlns:ns="http://example.com/unknown" versione="FPR12">'
    "<FatturaElettronicaHeader/>"
    "<FatturaElettronicaBody/>"
    "</ns:FatturaElettronica>"
)


class TestValidateInvoice:
    """Contract tests for validate_invoice."""

    async def test_valid_v13_passes(self, valid_v13_xml: str) -> None:
        """Valid v1.3 invoice returns valid=True with correct version."""
        result = await validate_invoice(valid_v13_xml)
        assert result["valid"] is True
        assert result["version"] == "1.3"
        assert result["errors"] == []

    async def test_valid_v12_passes(self, valid_v12_xml: str) -> None:
        """Valid v1.2 invoice returns valid=True with correct version."""
        result = await validate_invoice(valid_v12_xml)
        assert result["valid"] is True
        assert result["version"] == "1.2"
        assert result["errors"] == []

    async def test_malformed_xml_fails(self, invalid_xml: str) -> None:
        """Malformed (unparseable) XML returns valid=False with a parse error."""
        result = await validate_invoice(invalid_xml)
        assert result["valid"] is False
        assert result["version"] == "unknown"
        assert len(result["errors"]) > 0

    async def test_unknown_namespace_fails(self) -> None:
        """XML with an unrecognised namespace returns valid=False, version unknown."""
        result = await validate_invoice(_UNKNOWN_NAMESPACE)
        assert result["valid"] is False
        assert result["version"] == "unknown"
        assert "Unrecognised FatturaPA namespace" in result["errors"][0]

    async def test_xsd_structural_violation_fails(self) -> None:
        """Well-formed XML violating the XSD (missing versione) returns valid=False."""
        result = await validate_invoice(_V13_MISSING_VERSIONE)
        assert result["valid"] is False
        assert result["version"] == "1.3"
        assert len(result["errors"]) > 0

    async def test_xsd_not_found(
        self, valid_v13_xml: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing XSD file produces a clear error message instead of an exception."""
        import fatturapa_mcp.tools.validate as mod

        monkeypatch.setattr(mod, "_SCHEMAS_DIR", Path("/nonexistent/schemas"))
        result = await validate_invoice(valid_v13_xml)
        assert result["valid"] is False
        assert result["version"] == "1.3"
        assert "XSD schema not found" in result["errors"][0]


class TestValidateInvoiceCtxLogging:
    """Verify ctx log calls are emitted with correct structure."""

    async def test_valid_invoice_emits_start_and_done(self, valid_v13_xml: str) -> None:
        """A valid invoice produces exactly two info log entries."""
        ctx = MockCtx()
        await validate_invoice(valid_v13_xml, ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2
        assert len(ctx.errors) == 0

    async def test_malformed_xml_emits_error_log(self, invalid_xml: str) -> None:
        """A parse error routes the done log to ctx.error."""
        ctx = MockCtx()
        await validate_invoice(invalid_xml, ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.errors) == 1

    async def test_unknown_namespace_emits_error_log(self) -> None:
        """Unknown namespace routes the done log to ctx.error."""
        ctx = MockCtx()
        await validate_invoice(_UNKNOWN_NAMESPACE, ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.errors) == 1

    async def test_missing_xsd_emits_warning_log(
        self, valid_v13_xml: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing XSD file routes the done log to ctx.warning."""
        import fatturapa_mcp.tools.validate as mod

        ctx = MockCtx()
        monkeypatch.setattr(mod, "_SCHEMAS_DIR", Path("/nonexistent/schemas"))
        await validate_invoice(valid_v13_xml, ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.warnings) == 1


class TestValidateInvoiceProgress:
    """Verify progress notifications are emitted in the correct order."""

    async def test_valid_invoice_emits_three_steps(self, valid_v13_xml: str) -> None:
        """Happy path reports steps 1/3, 2/3, 3/3 in order."""
        ctx = MockCtx()
        await validate_invoice(valid_v13_xml, ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3), (2, 3), (3, 3)]

    async def test_malformed_xml_emits_only_first_step(self, invalid_xml: str) -> None:
        """Parse failure stops after step 1 — no further progress reported."""
        ctx = MockCtx()
        await validate_invoice(invalid_xml, ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3)]

    async def test_no_ctx_does_not_raise(self, valid_v13_xml: str) -> None:
        """Calling without ctx must not raise."""
        result = await validate_invoice(valid_v13_xml, ctx=None)
        assert result["valid"] is True
