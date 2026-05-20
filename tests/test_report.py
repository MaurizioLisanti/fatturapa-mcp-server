"""Tests for the generate_invoice_report tool."""

import pytest

from fatturapa_mcp.tools.report import generate_invoice_report
from tests.conftest import MockCtx

_NS_V13 = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3"

# Checksummed-valid Italian P.IVAs (verified via MEF algorithm):
#   "12345678903": s_odd=25, s_even=22, check=3 ✓
#   "98765432103": s_odd=25, s_even=22, check=3 ✓
_PIVA_A = "12345678903"
_PIVA_B = "98765432103"


def _make_xml(
    piva_supplier: str = _PIVA_A,
    piva_customer: str = _PIVA_B,
    total: str = "122.00",
    imponibile: str = "100.00",
    imposta: str = "22.00",
    date_str: str = "2024-01-15",
    include_payment: bool = True,
    numero: str = "2024/001",
) -> str:
    """Build a minimal, report-ready FatturaPA v1.3 XML string."""
    payment_el = (
        "<DatiPagamento><CondizioniPagamento>TP02</CondizioniPagamento>"
        "<DettaglioPagamento><ModalitaPagamento>MP05</ModalitaPagamento>"
        f"<ImportoPagamento>{total}</ImportoPagamento></DettaglioPagamento>"
        "</DatiPagamento>"
        if include_payment
        else ""
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<p:FatturaElettronica xmlns:p="{_NS_V13}" versione="FPR12">'
        "<FatturaElettronicaHeader>"
        "<DatiTrasmissione>"
        f"<IdTrasmittente><IdPaese>IT</IdPaese>"
        f"<IdCodice>{piva_supplier}</IdCodice></IdTrasmittente>"
        "<ProgressivoInvio>00001</ProgressivoInvio>"
        "<FormatoTrasmissione>FPR12</FormatoTrasmissione>"
        "<CodiceDestinatario>AAAAAAA</CodiceDestinatario>"
        "</DatiTrasmissione>"
        "<CedentePrestatore><DatiAnagrafici>"
        f"<IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{piva_supplier}</IdCodice></IdFiscaleIVA>"
        "<Anagrafica><Denominazione>Fornitore Srl</Denominazione></Anagrafica>"
        "<RegimeFiscale>RF01</RegimeFiscale>"
        "</DatiAnagrafici>"
        "<Sede><Indirizzo>Via A 1</Indirizzo><CAP>00100</CAP>"
        "<Comune>Roma</Comune><Nazione>IT</Nazione></Sede>"
        "</CedentePrestatore>"
        "<CessionarioCommittente><DatiAnagrafici>"
        f"<IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{piva_customer}</IdCodice></IdFiscaleIVA>"
        "<Anagrafica><Denominazione>Cliente Srl</Denominazione></Anagrafica>"
        "</DatiAnagrafici>"
        "<Sede><Indirizzo>Via B 2</Indirizzo><CAP>20100</CAP>"
        "<Comune>Milano</Comune><Nazione>IT</Nazione></Sede>"
        "</CessionarioCommittente>"
        "</FatturaElettronicaHeader>"
        "<FatturaElettronicaBody>"
        "<DatiGenerali><DatiGeneraliDocumento>"
        "<TipoDocumento>TD01</TipoDocumento><Divisa>EUR</Divisa>"
        f"<Data>{date_str}</Data><Numero>{numero}</Numero>"
        f"<ImportoTotaleDocumento>{total}</ImportoTotaleDocumento>"
        "</DatiGeneraliDocumento></DatiGenerali>"
        "<DatiBeniServizi>"
        "<DettaglioLinee>"
        "<NumeroLinea>1</NumeroLinea>"
        "<Descrizione>Servizio di test</Descrizione>"
        "<Quantita>1.00</Quantita><PrezzoUnitario>100.00</PrezzoUnitario>"
        f"<PrezzoTotale>{imponibile}</PrezzoTotale>"
        "<AliquotaIVA>22.00</AliquotaIVA>"
        "</DettaglioLinee>"
        "<DatiRiepilogo>"
        "<AliquotaIVA>22.00</AliquotaIVA>"
        f"<ImponibileImporto>{imponibile}</ImponibileImporto>"
        f"<Imposta>{imposta}</Imposta>"
        "<EsigibilitaIVA>I</EsigibilitaIVA>"
        "</DatiRiepilogo>"
        "</DatiBeniServizi>"
        f"{payment_el}"
        "</FatturaElettronicaBody>"
        "</p:FatturaElettronica>"
    )


_XML_A = _make_xml(
    total="122.00", imponibile="100.00", imposta="22.00", numero="2024/001"
)
_XML_B = _make_xml(
    total="244.00", imponibile="200.00", imposta="44.00", numero="2024/002"
)
_XML_INVALID = "<not-valid-xml>"


class TestGenerateInvoiceReportStructure:
    """Verify output structure and metadata."""

    async def test_result_has_all_required_keys(self) -> None:
        """Result contains all twelve required top-level keys."""
        result = await generate_invoice_report([_XML_A])
        for key in (
            "title",
            "generated_at",
            "total_invoices",
            "valid_invoices",
            "invalid_invoices",
            "total_amount",
            "total_vat",
            "currency",
            "suppliers",
            "customers",
            "anomalies_summary",
            "errors",
        ):
            assert key in result

    async def test_default_title(self) -> None:
        """When title is None the default title is used."""
        result = await generate_invoice_report([_XML_A])
        assert result["title"] == "Invoice Report"

    async def test_custom_title(self) -> None:
        """A provided title is reflected in the output."""
        result = await generate_invoice_report([_XML_A], title="Maggio 2024")
        assert result["title"] == "Maggio 2024"

    async def test_generated_at_is_iso8601(self) -> None:
        """generated_at is a non-empty ISO-8601 string starting with the year."""
        result = await generate_invoice_report([])
        assert result["generated_at"].startswith("20")

    async def test_currency_from_invoice(self) -> None:
        """currency is extracted from the invoice (EUR for the fixture)."""
        result = await generate_invoice_report([_XML_A])
        assert result["currency"] == "EUR"


class TestGenerateInvoiceReportCounts:
    """Verify invoice counting and totals."""

    async def test_empty_list(self) -> None:
        """Empty xml_contents yields a valid zero-count report."""
        result = await generate_invoice_report([])
        assert result["total_invoices"] == 0
        assert result["valid_invoices"] == 0
        assert result["invalid_invoices"] == 0
        assert result["total_amount"] == pytest.approx(0.0)
        assert result["errors"] == []

    async def test_single_invoice_totals(self) -> None:
        """One invoice: total_amount=122.0, total_vat≈22.0."""
        result = await generate_invoice_report([_XML_A])
        assert result["total_invoices"] == 1
        assert result["valid_invoices"] == 1
        assert result["total_amount"] == pytest.approx(122.0)
        assert result["total_vat"] == pytest.approx(22.0)

    async def test_multiple_invoices_sums(self) -> None:
        """Two invoices: amounts and VAT accumulate correctly."""
        result = await generate_invoice_report([_XML_A, _XML_B])
        assert result["total_invoices"] == 2
        assert result["total_amount"] == pytest.approx(122.0 + 244.0)
        assert result["total_vat"] == pytest.approx(22.0 + 44.0)

    async def test_invalid_invoice_counted(self) -> None:
        """A malformed invoice increments invalid_invoices and populates errors."""
        result = await generate_invoice_report([_XML_A, _XML_INVALID])
        assert result["total_invoices"] == 2
        assert result["valid_invoices"] == 1
        assert result["invalid_invoices"] == 1
        assert len(result["errors"]) == 1

    async def test_all_invalid_invoices(self) -> None:
        """All-invalid batch: valid=0, errors list non-empty, total_amount=0."""
        result = await generate_invoice_report([_XML_INVALID])
        assert result["valid_invoices"] == 0
        assert result["invalid_invoices"] == 1
        assert result["total_amount"] == pytest.approx(0.0)
        assert result["errors"]


class TestGenerateInvoiceReportParties:
    """Verify supplier and customer aggregation."""

    async def test_supplier_appears_in_output(self) -> None:
        """Supplier entry is present with correct name and piva."""
        result = await generate_invoice_report([_XML_A])
        assert len(result["suppliers"]) == 1
        sup = result["suppliers"][0]
        assert sup["piva"] == f"IT{_PIVA_A}"
        assert sup["invoice_count"] == 1

    async def test_same_supplier_aggregated(self) -> None:
        """Two invoices from the same supplier merge into one entry."""
        result = await generate_invoice_report([_XML_A, _XML_B])
        assert len(result["suppliers"]) == 1
        sup = result["suppliers"][0]
        assert sup["invoice_count"] == 2
        assert sup["total_amount"] == pytest.approx(122.0 + 244.0)


class TestGenerateInvoiceReportAnomalies:
    """Verify anomaly aggregation."""

    async def test_clean_invoice_anomaly_summary(self) -> None:
        """Clean invoice: total_anomalies=0, clean_invoices=1."""
        result = await generate_invoice_report([_XML_A])
        summary = result["anomalies_summary"]
        assert summary["total_anomalies"] == 0
        assert summary["clean_invoices"] == 1
        assert summary["by_severity"]["error"] == 0
        assert summary["by_severity"]["warning"] == 0

    async def test_anomaly_detected_and_counted(self) -> None:
        """Invoice with future date contributes FUTURE_DATE to by_code."""
        xml_future = _make_xml(date_str="2099-01-01")
        result = await generate_invoice_report([xml_future])
        summary = result["anomalies_summary"]
        assert summary["total_anomalies"] > 0
        assert "FUTURE_DATE" in summary["by_code"]
        assert summary["clean_invoices"] == 0

    async def test_by_code_aggregates_across_invoices(self) -> None:
        """Two invoices each with a future date produce FUTURE_DATE count of 2."""
        xml_future = _make_xml(date_str="2099-01-01", numero="2024/001")
        xml_future2 = _make_xml(date_str="2099-06-01", numero="2024/002")
        result = await generate_invoice_report([xml_future, xml_future2])
        assert result["anomalies_summary"]["by_code"].get("FUTURE_DATE", 0) == 2


class TestGenerateInvoiceReportCtx:
    """Context logging and progress notifications."""

    async def test_progress_empty_list(self) -> None:
        """Empty list emits a single aggregation step: (1, 1)."""
        ctx = MockCtx()
        await generate_invoice_report([], ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 1)]

    async def test_progress_one_invoice(self) -> None:
        """One invoice emits (1, 2) for parsing and (2, 2) for aggregation."""
        ctx = MockCtx()
        await generate_invoice_report([_XML_A], ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 2), (2, 2)]

    async def test_progress_two_invoices(self) -> None:
        """Two invoices emit steps (1,3), (2,3), (3,3)."""
        ctx = MockCtx()
        await generate_invoice_report([_XML_A, _XML_B], ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 3), (2, 3), (3, 3)]

    async def test_ctx_emits_start_and_done(self) -> None:
        """Two info log entries are emitted: start and done."""
        ctx = MockCtx()
        await generate_invoice_report([_XML_A], ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2

    async def test_no_ctx_does_not_raise(self) -> None:
        """Calling without ctx must not raise."""
        result = await generate_invoice_report([_XML_A], ctx=None)
        assert result["total_invoices"] == 1
