"""Tests for the extract_invoice_data tool."""

import pytest
from lxml.etree import XMLSyntaxError

from fatturapa_mcp.tools.extract import extract_invoice_data

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

    def test_extracts_supplier_name_v13(self, valid_v13_xml: str) -> None:
        """Supplier Denominazione is returned as supplier_name."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["supplier_name"] == "Test Fornitore Srl"

    def test_extracts_supplier_piva_v13(self, valid_v13_xml: str) -> None:
        """Supplier P.IVA is IdPaese+IdCodice concatenated."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["supplier_piva"] == "IT12345678901"

    def test_supplier_tax_code_absent_returns_none(self, valid_v13_xml: str) -> None:
        """supplier_tax_code is None when CodiceFiscale is absent in the fixture."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["supplier_tax_code"] is None

    # ------------------------------------------------------------------
    # Customer fields — v1.3 fixture
    # ------------------------------------------------------------------

    def test_extracts_customer_name_v13(self, valid_v13_xml: str) -> None:
        """Customer Denominazione is returned as customer_name."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["customer_name"] == "Test Cliente Srl"

    def test_extracts_customer_piva_v13(self, valid_v13_xml: str) -> None:
        """Customer P.IVA is IdPaese+IdCodice concatenated."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["customer_piva"] == "IT98765432109"

    # ------------------------------------------------------------------
    # Invoice header fields — v1.3 fixture
    # ------------------------------------------------------------------

    def test_extracts_invoice_number_and_date_v13(self, valid_v13_xml: str) -> None:
        """invoice_number and invoice_date are extracted from DatiGeneraliDocumento."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["invoice_number"] == "2024/001"
        assert result["invoice_date"] == "2024-01-15"

    def test_extracts_document_type_and_currency_v13(self, valid_v13_xml: str) -> None:
        """document_type and currency are extracted correctly."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["document_type"] == "TD01"
        assert result["currency"] == "EUR"

    def test_extracts_total_amount_v13(self, valid_v13_xml: str) -> None:
        """total_amount matches ImportoTotaleDocumento from the v1.3 fixture."""
        result = extract_invoice_data(valid_v13_xml)
        assert result["total_amount"] == pytest.approx(122.0)

    # ------------------------------------------------------------------
    # Line items — v1.3 fixture
    # ------------------------------------------------------------------

    def test_extracts_one_line_item_v13(self, valid_v13_xml: str) -> None:
        """One DettaglioLinee entry is extracted from the v1.3 fixture."""
        result = extract_invoice_data(valid_v13_xml)
        assert len(result["line_items"]) == 1

    def test_line_item_fields_v13(self, valid_v13_xml: str) -> None:
        """Line item fields match the v1.3 fixture values."""
        item = extract_invoice_data(valid_v13_xml)["line_items"][0]
        assert item["line_number"] == 1
        assert item["description"] == "Servizio di test"
        assert item["quantity"] == pytest.approx(1.0)
        assert item["unit_price"] == pytest.approx(100.0)
        assert item["total_price"] == pytest.approx(100.0)
        assert item["vat_rate"] == pytest.approx(22.0)

    # ------------------------------------------------------------------
    # v1.2 fixture
    # ------------------------------------------------------------------

    def test_extracts_basic_fields_from_v12(self, valid_v12_xml: str) -> None:
        """Key fields are extracted from a v1.2 fixture without errors."""
        result = extract_invoice_data(valid_v12_xml)
        assert result["supplier_piva"] == "IT12345678901"
        assert result["invoice_number"] == "2023/042"
        assert result["total_amount"] == pytest.approx(244.0)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_minimal_xml_all_fields_none(self) -> None:
        """All optional fields are None when the XML has no payload elements."""
        result = extract_invoice_data(_MINIMAL_XML)
        assert result["invoice_number"] is None
        assert result["invoice_date"] is None
        assert result["total_amount"] is None
        assert result["supplier_name"] is None
        assert result["supplier_piva"] is None
        assert result["customer_name"] is None
        assert result["customer_piva"] is None
        assert result["line_items"] == []

    def test_nome_cognome_fallback(self) -> None:
        """supplier_name falls back to Nome+Cognome when Denominazione is absent."""
        result = extract_invoice_data(_XML_NOME_COGNOME)
        assert result["supplier_name"] == "Mario Rossi"

    def test_total_from_dati_riepilogo_fallback(self) -> None:
        """total_amount sums ImponibileImporto+Imposta when ImportoTotale is absent."""
        result = extract_invoice_data(_XML_NOME_COGNOME)
        assert result["total_amount"] == pytest.approx(244.0)

    def test_malformed_xml_raises(self, invalid_xml: str) -> None:
        """Malformed XML propagates XMLSyntaxError from lxml."""
        with pytest.raises(XMLSyntaxError):
            extract_invoice_data(invalid_xml)
