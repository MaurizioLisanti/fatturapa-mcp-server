"""Tests for the extract_invoice_data tool."""

from pathlib import Path

import pytest
from lxml.etree import XMLSyntaxError

from fatturapa_mcp.tools.extract import extract_invoice_data
from tests.conftest import MockCtx

# Minimal valid XML — well-formed but all payload fields absent.
_MINIMAL_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<p:FatturaElettronica"
    ' xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3"'
    ' versione="FPR12">'
    "<FatturaElettronicaHeader/>"
    "<FatturaElettronicaBody/>"
    "</p:FatturaElettronica>"
)

# Supplier identified by Nome+Cognome (no Denominazione); total via DatiRiepilogo.
_XML_NOME_COGNOME = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<p:FatturaElettronica"
    ' xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3"'
    ' versione="FPR12">'
    "<FatturaElettronicaHeader>"
    "<CedentePrestatore><DatiAnagrafici>"
    "<IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>11111111111</IdCodice></IdFiscaleIVA>"
    "<Anagrafica><Nome>Mario</Nome><Cognome>Rossi</Cognome></Anagrafica>"
    "<RegimeFiscale>RF01</RegimeFiscale>"
    "</DatiAnagrafici>"
    "<Sede><Indirizzo>Via X 1</Indirizzo><CAP>00100</CAP>"
    "<Comune>Roma</Comune><Nazione>IT</Nazione></Sede>"
    "</CedentePrestatore>"
    "<CessionarioCommittente><DatiAnagrafici>"
    "<IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>22222222222</IdCodice></IdFiscaleIVA>"
    "<Anagrafica><Denominazione>Cliente Srl</Denominazione></Anagrafica>"
    "</DatiAnagrafici>"
    "<Sede><Indirizzo>Via Y 2</Indirizzo><CAP>20100</CAP>"
    "<Comune>Milano</Comune><Nazione>IT</Nazione></Sede>"
    "</CessionarioCommittente>"
    "</FatturaElettronicaHeader>"
    "<FatturaElettronicaBody>"
    "<DatiGenerali><DatiGeneraliDocumento>"
    "<TipoDocumento>TD01</TipoDocumento><Divisa>EUR</Divisa>"
    "<Data>2024-03-01</Data><Numero>2024/100</Numero>"
    "</DatiGeneraliDocumento></DatiGenerali>"
    "<DatiBeniServizi>"
    "<DatiRiepilogo>"
    "<ImponibileImporto>200.00</ImponibileImporto>"
    "<Imposta>44.00</Imposta>"
    "</DatiRiepilogo>"
    "</DatiBeniServizi>"
    "</FatturaElettronicaBody>"
    "</p:FatturaElettronica>"
)


class TestExtractInvoiceData:
    """Contract tests for extract_invoice_data."""

    # ------------------------------------------------------------------
    # Supplier fields — v1.3 fixture
    # ------------------------------------------------------------------

    async def test_extracts_supplier_name_v13(self, valid_v13_xml: str) -> None:
        """Supplier Denominazione is returned as supplier_name."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["supplier_name"] == "Test Fornitore Srl"

    async def test_extracts_supplier_piva_v13(self, valid_v13_xml: str) -> None:
        """Supplier P.IVA is IdPaese+IdCodice concatenated."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["supplier_piva"] == "IT12345678901"

    async def test_supplier_tax_code_absent_returns_none(
        self, valid_v13_xml: str
    ) -> None:
        """supplier_tax_code is None when CodiceFiscale is absent in the fixture."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["supplier_tax_code"] is None

    # ------------------------------------------------------------------
    # Customer fields — v1.3 fixture
    # ------------------------------------------------------------------

    async def test_extracts_customer_name_v13(self, valid_v13_xml: str) -> None:
        """Customer Denominazione is returned as customer_name."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["customer_name"] == "Test Cliente Srl"

    async def test_extracts_customer_piva_v13(self, valid_v13_xml: str) -> None:
        """Customer P.IVA is IdPaese+IdCodice concatenated."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["customer_piva"] == "IT98765432109"

    # ------------------------------------------------------------------
    # Invoice header fields — v1.3 fixture
    # ------------------------------------------------------------------

    async def test_extracts_invoice_number_and_date_v13(
        self, valid_v13_xml: str
    ) -> None:
        """invoice_number and invoice_date are extracted from DatiGeneraliDocumento."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["invoice_number"] == "2024/001"
        assert result["invoice_date"] == "2024-01-15"

    async def test_extracts_document_type_and_currency_v13(
        self, valid_v13_xml: str
    ) -> None:
        """document_type and currency are extracted correctly."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["document_type"] == "TD01"
        assert result["currency"] == "EUR"

    async def test_extracts_total_amount_v13(self, valid_v13_xml: str) -> None:
        """total_amount matches ImportoTotaleDocumento from the v1.3 fixture."""
        result = await extract_invoice_data(valid_v13_xml)
        assert result["total_amount"] == pytest.approx(122.0)

    # ------------------------------------------------------------------
    # Line items — v1.3 fixture
    # ------------------------------------------------------------------

    async def test_extracts_one_line_item_v13(self, valid_v13_xml: str) -> None:
        """One DettaglioLinee entry is extracted from the v1.3 fixture."""
        result = await extract_invoice_data(valid_v13_xml)
        assert len(result["line_items"]) == 1

    async def test_line_item_fields_v13(self, valid_v13_xml: str) -> None:
        """Line item fields match the v1.3 fixture values."""
        item = (await extract_invoice_data(valid_v13_xml))["line_items"][0]
        assert item["line_number"] == 1
        assert item["description"] == "Servizio di test"
        assert item["quantity"] == pytest.approx(1.0)
        assert item["unit_price"] == pytest.approx(100.0)
        assert item["total_price"] == pytest.approx(100.0)
        assert item["vat_rate"] == pytest.approx(22.0)

    # ------------------------------------------------------------------
    # v1.2 fixture
    # ------------------------------------------------------------------

    async def test_extracts_basic_fields_from_v12(self, valid_v12_xml: str) -> None:
        """Key fields are extracted from a v1.2 fixture without errors."""
        result = await extract_invoice_data(valid_v12_xml)
        assert result["supplier_piva"] == "IT12345678901"
        assert result["invoice_number"] == "2023/042"
        assert result["total_amount"] == pytest.approx(244.0)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    async def test_minimal_xml_all_fields_none(self) -> None:
        """All optional fields are None when the XML has no payload elements."""
        result = await extract_invoice_data(_MINIMAL_XML)
        assert result["invoice_number"] is None
        assert result["invoice_date"] is None
        assert result["total_amount"] is None
        assert result["supplier_name"] is None
        assert result["supplier_piva"] is None
        assert result["customer_name"] is None
        assert result["customer_piva"] is None
        assert result["line_items"] == []

    async def test_nome_cognome_fallback(self) -> None:
        """supplier_name falls back to Nome+Cognome when Denominazione is absent."""
        result = await extract_invoice_data(_XML_NOME_COGNOME)
        assert result["supplier_name"] == "Mario Rossi"

    async def test_total_from_dati_riepilogo_fallback(self) -> None:
        """total_amount sums ImponibileImporto+Imposta when ImportoTotale is absent."""
        result = await extract_invoice_data(_XML_NOME_COGNOME)
        assert result["total_amount"] == pytest.approx(244.0)

    async def test_malformed_xml_raises(self, invalid_xml: str) -> None:
        """Malformed XML propagates XMLSyntaxError from lxml."""
        with pytest.raises(XMLSyntaxError):
            await extract_invoice_data(invalid_xml)


class TestExtractInvoiceDataCtxLogging:
    """Verify ctx log calls are emitted with correct structure."""

    async def test_emits_start_and_done(self, valid_v13_xml: str) -> None:
        """A successful extraction produces exactly two info log entries."""
        ctx = MockCtx()
        await extract_invoice_data(valid_v13_xml, ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2
        assert len(ctx.errors) == 0


class TestExtractInvoiceDataFilePath:
    """Tests for the file_path / roots-check integration."""

    async def test_file_path_reads_and_extracts(
        self, valid_v13_xml: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Providing a file_path within allowed roots reads and extracts data."""
        invoice = tmp_path / "invoice.xml"
        invoice.write_text(valid_v13_xml, encoding="utf-8")
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(tmp_path))
        result = await extract_invoice_data(file_path=str(invoice))
        assert result["invoice_number"] == "2024/001"

    async def test_file_path_outside_roots_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A file_path outside the allowed roots raises PermissionError."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside" / "inv.xml"
        outside.parent.mkdir()
        outside.write_text("<x/>", encoding="utf-8")
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(allowed))
        with pytest.raises(PermissionError):
            await extract_invoice_data(file_path=str(outside))

    async def test_neither_xml_nor_file_path_raises(self) -> None:
        """Passing neither xml_content nor file_path raises ValueError."""
        with pytest.raises(ValueError):
            await extract_invoice_data()


class TestExtractInvoiceDataProgress:
    """Verify progress notifications are emitted in the correct order."""

    async def test_happy_path_emits_three_steps(self, valid_v13_xml: str) -> None:
        """Happy path reports steps 1/3, 2/3, 3/3 in order."""
        ctx = MockCtx()
        await extract_invoice_data(valid_v13_xml, ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3), (2, 3), (3, 3)]

    async def test_no_ctx_does_not_raise(self, valid_v13_xml: str) -> None:
        """Calling without ctx must not raise."""
        result = await extract_invoice_data(valid_v13_xml, ctx=None)
        assert result["invoice_number"] == "2024/001"
